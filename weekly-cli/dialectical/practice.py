"""Phase 5: Practice Orientation — the fifth and final stage of dialectical epistemology.

Translate the full dialectical analysis into practice guidance:
  - Overall judgment of the situation
  - Three scenario projections (baseline, alternative, wildcard)
  - Practice significance for action
  - Signals to watch for monitoring
  - Last week calibration for iterative improvement
"""
from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt

PRACTICE_PROMPT = load_prompt("dialectical/practice")


def build_practice_context(positioning_result: dict) -> str:
    """Build XML event blocks from positioning result for prompt injection.

    Formats each event's id, title, summary, materialContent, impact/infoGain
    scores, plus the per-event historical materialism positioning analysis
    (productiveForces, productionRelations, etc.) for practice orientation.
    Returns a no-information empty string when events are empty.
    """
    events = positioning_result.get("events", [])
    if not events or not isinstance(events, list):
        return ""

    # Include phaseSummary from positioning as context preamble
    phase_summary = positioning_result.get("phaseSummary", "")

    lines = []
    if phase_summary:
        lines.append(f"[历史定位摘要] {phase_summary}")
        lines.append("")

    for i, e in enumerate(events):
        if not isinstance(e, dict):
            continue
        lines.append(f"[事件 {i+1}]")
        lines.append(f"  ID: {e.get('id', f'evt-{i+1}')}")
        lines.append(f"  标题: {e.get('title', '(无标题)')}")

        summary = e.get("summary")
        if summary is not None:
            lines.append(f"  概述: {str(summary)[:300]}")

        material = e.get("materialContent")
        if material is not None:
            lines.append(f"  物质内容: {str(material)[:500]}")

        impact = e.get("impactScore")
        if impact is not None:
            lines.append(f"  影响度评分: {impact}")

        infogain = e.get("infoGainScore")
        if infogain is not None:
            lines.append(f"  信息增益评分: {infogain}")

        # Include per-event historical materialism positioning analysis
        fields = [
            ("productiveForces", "生产力"),
            ("productionRelations", "生产关系"),
            ("baseStructure", "经济基础"),
            ("superstructure", "上层建筑"),
            ("classForceComparison", "阶级力量对比"),
            ("historicalPosition", "历史方位"),
        ]
        for key, label in fields:
            val = e.get(key)
            if val is not None:
                lines.append(f"  {label}: {str(val)[:300]}")

        lines.append("")
    return "\n".join(lines)


def orient_practice(
    client: DeepSeekClient,
    positioning_result: dict,
) -> dict:
    """Execute Phase 5: Practice Orientation.

    Loads the dialectical/practice prompt, formats context from the
    positioning result, calls the LLM, and returns structured practice
    orientation.

    Returns a dict matching the PracticeOrientation schema:
    - overallJudgment: overall judgment of the current situation
    - scenarios: list of scenario dicts (baseline, alternative, wildcard)
    - practiceSignificance: significance for action
    - signalsToWatch: list of signal monitoring dicts
    - lastWeekCalibration: dict with calibration info

    When positioning_result has no valid events or client is None,
    returns a default structure.
    """
    events = positioning_result.get("events", [])
    if not events or not isinstance(events, list):
        return {
            "overallJudgment": "无事件可供实践导向分析",
            "scenarios": [],
            "practiceSignificance": "",
            "signalsToWatch": [],
            "lastWeekCalibration": {
                "predictionSummary": "",
                "actualOutcome": "",
                "calibrationNote": "",
                "accuracyScore": None,
            },
        }

    # Filter out non-dict events
    valid_events = [e for e in events if isinstance(e, dict)]
    if not valid_events:
        return {
            "overallJudgment": "无事件可供实践导向分析",
            "scenarios": [],
            "practiceSignificance": "",
            "signalsToWatch": [],
            "lastWeekCalibration": {
                "predictionSummary": "",
                "actualOutcome": "",
                "calibrationNote": "",
                "accuracyScore": None,
            },
        }

    event_count = len(valid_events)
    events_text = build_practice_context(positioning_result)

    prompt = PRACTICE_PROMPT.format(
        event_count=event_count,
        events_text=events_text,
    )

    result = client.chat_json(
        [
            {
                "role": "system",
                "content": (
                    "你是一个唯物辩证法研究者。你的任务是实践导向——"
                    "将辩证分析转化为对实践的指导，包括情景推演、"
                    "信号监测和校准。用朴实中文写作，不堆砌术语，"
                    "不贴标签。严格按JSON格式输出。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=16384,
    )

    # ── Defensive: ensure top-level string fields ──
    if result.get("overallJudgment") is None:
        result["overallJudgment"] = ""
    if result.get("practiceSignificance") is None:
        result["practiceSignificance"] = ""

    # ── Defensive: ensure scenarios list ──
    scenarios = result.get("scenarios")
    if scenarios is None:
        result["scenarios"] = []
    elif not isinstance(scenarios, list):
        result["scenarios"] = []

    # ── Defensive: enrich each scenario with defaults ──
    if isinstance(result.get("scenarios"), list):
        sanitized = []
        for s in result["scenarios"]:
            if not isinstance(s, dict):
                continue
            sanitized_s = dict(s)
            if "scenarioId" not in sanitized_s:
                sanitized_s["scenarioId"] = f"sc-{len(sanitized) + 1}"
            if "keyAssumptions" not in sanitized_s or sanitized_s.get("keyAssumptions") is None:
                sanitized_s["keyAssumptions"] = []
            elif not isinstance(sanitized_s["keyAssumptions"], list):
                sanitized_s["keyAssumptions"] = []
            if "earlySignals" not in sanitized_s or sanitized_s.get("earlySignals") is None:
                sanitized_s["earlySignals"] = []
            elif not isinstance(sanitized_s["earlySignals"], list):
                sanitized_s["earlySignals"] = []
            if "relatedEventIds" not in sanitized_s or sanitized_s.get("relatedEventIds") is None:
                sanitized_s["relatedEventIds"] = []
            elif not isinstance(sanitized_s["relatedEventIds"], list):
                sanitized_s["relatedEventIds"] = []
            sanitized.append(sanitized_s)
        result["scenarios"] = sanitized

    # ── Defensive: ensure signalsToWatch list ──
    signals = result.get("signalsToWatch")
    if signals is None:
        result["signalsToWatch"] = []
    elif not isinstance(signals, list):
        result["signalsToWatch"] = []

    # ── Defensive: enrich each signal with defaults ──
    if isinstance(result.get("signalsToWatch"), list):
        sanitized_signals = []
        for sig in result["signalsToWatch"]:
            if not isinstance(sig, dict):
                continue
            sanitized_sig = dict(sig)
            if "priority" not in sanitized_sig or sanitized_sig.get("priority") is None:
                sanitized_sig["priority"] = 3
            sanitized_signals.append(sanitized_sig)
        result["signalsToWatch"] = sanitized_signals

    # ── Defensive: ensure lastWeekCalibration dict ──
    calibration = result.get("lastWeekCalibration")
    if calibration is None or not isinstance(calibration, dict):
        result["lastWeekCalibration"] = {
            "predictionSummary": "",
            "actualOutcome": "",
            "calibrationNote": "",
            "accuracyScore": None,
        }

    return result
