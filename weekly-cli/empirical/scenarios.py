"""Empirical Layer: GBN Scenario Planning & Leading Indicators.

Implements a scaled-down GBN (Global Business Network) 8-step scenario
planning process for weekly cadence: identifies 2 key uncertainties,
constructs a 2x2 scenario matrix, generates 3 scenarios (baseline,
alternative, wildcard) with probability bands, and produces signpost
indicators for monitoring.

Gracefully degrades: returns None on ANY failure so the pipeline continues.
"""
import json
import logging

from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt

logger = logging.getLogger("weekly.empirical.scenarios")

SCENARIOS_PROMPT = load_prompt("empirical/scenarios")

VALID_SCENARIO_TYPES = frozenset({"baseline", "alternative", "wildcard"})


def _serialize_synthesis(synthesis: dict) -> str:
    """Serialize synthesis dict to a JSON string for the prompt."""
    try:
        safe = {}
        for k, v in synthesis.items():
            if isinstance(v, str) and len(v) > 3000:
                safe[k] = v[:3000] + "...(truncated)"
            elif isinstance(v, list) and len(v) > 50:
                safe[k] = v[:50]
            else:
                safe[k] = v
        return json.dumps(safe, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return json.dumps(
            {k: str(v)[:1000] for k, v in synthesis.items()},
            ensure_ascii=False,
            indent=2,
        )


def _has_minimal_synthesis_content(synthesis: dict) -> bool:
    """Check that the synthesis has enough content for scenario planning.

    Needs at least a weeklyNarrative or crossCuttingThemes.
    """
    if not synthesis or not isinstance(synthesis, dict):
        return False
    if synthesis.get("weeklyNarrative"):
        return True
    themes = synthesis.get("crossCuttingThemes")
    if isinstance(themes, list) and len(themes) > 0:
        return True
    return False


def _sanitize_scenario_type(raw: str) -> str:
    """Normalize a scenario type to a valid value."""
    if not isinstance(raw, str):
        return "baseline"
    v = raw.strip().lower()
    if v in VALID_SCENARIO_TYPES:
        return v
    # Map common AI deviations
    fixups = {
        "base": "baseline",
        "baseline": "baseline",
        "alt": "alternative",
        "alternate": "alternative",
        "wild card": "wildcard",
        "wild-card": "wildcard",
        "wildcard": "wildcard",
        "黑天鹅": "wildcard",
        "基准": "baseline",
        "替代": "alternative",
    }
    if v in fixups:
        return fixups[v]
    return "baseline"


def _clamp_probability(raw) -> float:
    """Clamp a probability value to [0.0, 1.0]."""
    if not isinstance(raw, (int, float)):
        return 0.5
    return max(0.0, min(1.0, float(raw)))


def _sanitize_scenario(scenario: dict) -> dict:
    """Sanitize a single scenario dict with defaults."""
    scenario_type = _sanitize_scenario_type(scenario.get("scenarioType"))

    # Assign default probability bands based on type if missing/invalid
    prob = _clamp_probability(scenario.get("probability"))
    if prob == 0.5 and scenario_type == "baseline":
        prob = 0.45
    elif prob == 0.5 and scenario_type == "alternative":
        prob = 0.3
    elif prob == 0.5 and scenario_type == "wildcard":
        prob = 0.1

    return {
        "scenarioId": scenario.get("scenarioId") or "",
        "title": scenario.get("title") or "",
        "description": scenario.get("description") or "",
        "scenarioType": scenario_type,
        "probability": prob,
        "keyAssumptions": (
            scenario["keyAssumptions"]
            if isinstance(scenario.get("keyAssumptions"), list)
            else []
        ),
        "earlySignals": (
            scenario["earlySignals"]
            if isinstance(scenario.get("earlySignals"), list)
            else []
        ),
        "implications": scenario.get("implications") or "",
        "relatedEventIds": (
            scenario["relatedEventIds"]
            if isinstance(scenario.get("relatedEventIds"), list)
            else []
        ),
    }


def _sanitize_indicator(indicator: dict) -> dict:
    """Sanitize a leading indicator dict with defaults."""
    raw_priority = indicator.get("priority")
    sanitized_priority = 3
    if isinstance(raw_priority, (int, float)):
        sanitized_priority = max(1, min(5, int(raw_priority)))

    raw_trend = indicator.get("trend")
    valid_trends = {"上升", "稳定", "下降"}
    sanitized_trend = "稳定" if raw_trend in valid_trends else "稳定"

    return {
        "signalName": indicator.get("signalName") or "",
        "description": indicator.get("description") or "",
        "indicator": indicator.get("indicator") or "",
        "currentValue": indicator.get("currentValue") or "",
        "threshold": indicator.get("threshold") or "",
        "trend": sanitized_trend,
        "priority": sanitized_priority,
        "relatedScenarioIds": (
            indicator["relatedScenarioIds"]
            if isinstance(indicator.get("relatedScenarioIds"), list)
            else []
        ),
    }


def plan_scenarios(
    client: DeepSeekClient | None,
    synthesis: dict,
) -> dict | None:
    """Generate 3-scenario GBN planning from weekly synthesis.

    Implements a scaled-down GBN method:
      1. Identify predetermined elements and key uncertainties
      2. Build 2x2 uncertainty matrix
      3. Generate 3 scenarios: baseline (40-60%), alternative (20-35%),
         wildcard (5-15%)
      4. Produce leading indicators for monitoring

    Args:
        client: A DeepSeekClient instance (empirical model).
        synthesis: A dict with weeklyNarrative, crossCuttingThemes, trends,
                   contradictionsInMotion, and globalAssessment.

    Returns:
        A dict with scenarioSummary, predeterminedElements, keyUncertainties,
        scenarios, and leadingIndicators keys,
        or None on ANY failure (graceful degradation).
    """
    if client is None:
        return None

    if not _has_minimal_synthesis_content(synthesis):
        return None

    synthesis_json = _serialize_synthesis(synthesis)

    prompt = SCENARIOS_PROMPT.format(
        synthesis_json=synthesis_json,
    )

    try:
        result = client.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是一个情景规划专家。你的任务是基于周度热点综合研判，"
                        "使用GBN方法生成三情景规划。严格按JSON格式输出。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=8192,
        )
    except Exception:
        return None

    # ── Defensive: validate response structure ──
    if not isinstance(result, dict):
        return None

    result.setdefault("scenarioSummary", "")

    # -- Sanitize predeterminedElements --
    pred = result.get("predeterminedElements")
    if not isinstance(pred, list):
        result["predeterminedElements"] = []
    else:
        cleaned_pred = []
        for p in pred:
            if not isinstance(p, dict):
                continue
            cleaned_pred.append({
                "element": p.get("element") or "",
                "description": p.get("description") or "",
                "evidenceEventIds": (
                    p["evidenceEventIds"]
                    if isinstance(p.get("evidenceEventIds"), list)
                    else []
                ),
            })
        result["predeterminedElements"] = cleaned_pred

    # -- Sanitize keyUncertainties --
    uncertainties = result.get("keyUncertainties")
    if not isinstance(uncertainties, list):
        result["keyUncertainties"] = []
    else:
        cleaned_uncertainties = []
        for u in uncertainties:
            if not isinstance(u, dict):
                continue
            cleaned_uncertainties.append({
                "axis": u.get("axis") or "",
                "polarityA": u.get("polarityA") or "",
                "polarityB": u.get("polarityB") or "",
                "rationale": u.get("rationale") or "",
            })
        result["keyUncertainties"] = cleaned_uncertainties

    # -- Sanitize scenarios --
    scenarios = result.get("scenarios")
    if not isinstance(scenarios, list):
        result["scenarios"] = []
    else:
        result["scenarios"] = [
            _sanitize_scenario(s) if isinstance(s, dict) else _sanitize_scenario({})
            for s in scenarios
        ]

    # -- Sanitize leadingIndicators --
    indicators = result.get("leadingIndicators")
    if not isinstance(indicators, list):
        result["leadingIndicators"] = []
    else:
        result["leadingIndicators"] = [
            _sanitize_indicator(ind) if isinstance(ind, dict) else _sanitize_indicator({})
            for ind in indicators
        ]

    return result
