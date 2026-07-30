"""Empirical Layer: Causal Loop Diagrams & System Archetype Matching.

Builds causal loop diagrams (CLD) from event data and matches system
archetypes (FixesThatFail, LimitsToGrowth, ShiftingTheBurden,
TragedyOfCommons) using an LLM-based analysis.

Gracefully degrades: returns None on ANY failure so the pipeline continues.
"""
import json
import logging

from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt

logger = logging.getLogger("weekly.empirical.causal")

CAUSAL_PROMPT = load_prompt("empirical/causal")

# Valid system archetype types (must match schema.ArchetypeType enum values)
VALID_ARCHETYPES = frozenset({
    "FixesThatFail",
    "LimitsToGrowth",
    "ShiftingTheBurden",
    "TragedyOfCommons",
})


def _serialize_events(events: list[dict]) -> str:
    """Serialize events list to a JSON string for the prompt.

    Uses ensure_ascii=False to preserve Chinese characters.
    Truncates overly long fields to keep prompt size manageable.
    """
    try:
        safe_events = []
        for event in events:
            safe = {}
            for k, v in event.items():
                if isinstance(v, str) and len(v) > 2000:
                    safe[k] = v[:2000] + "...(truncated)"
                elif isinstance(v, list) and len(v) > 30:
                    safe[k] = v[:30]
                else:
                    safe[k] = v
            safe_events.append(safe)
        return json.dumps(safe_events, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return json.dumps(
            [{k: str(v)[:500] for k, v in e.items()} for e in events],
            ensure_ascii=False,
            indent=2,
        )


def _has_minimal_event_data(events: list[dict]) -> bool:
    """Check that the events list has enough content for causal analysis.

    Needs at least 2 events with titles to build meaningful causal links.
    """
    if not events or not isinstance(events, list):
        return False
    if len(events) < 2:
        return False
    return all(
        isinstance(e, dict) and e.get("title") and isinstance(e["title"], str) and e["title"].strip()
        for e in events
    )


def _sanitize_archetype_type(raw: str) -> str:
    """Normalize an archetype type string to a valid value.

    Tries exact match first, then fixup map for common AI variants,
    then substring match, falling back to 'LimitsToGrowth'.
    """
    if not isinstance(raw, str):
        return "LimitsToGrowth"
    v = raw.strip()
    if v in VALID_ARCHETYPES:
        return v
    # Common AI deviations
    fixups = {
        "fixes that fail": "FixesThatFail",
        "fixesthatfail": "FixesThatFail",
        "limits to growth": "LimitsToGrowth",
        "limitstogrowth": "LimitsToGrowth",
        "shifting the burden": "ShiftingTheBurden",
        "shiftingtheburden": "ShiftingTheBurden",
        "tragedy of commons": "TragedyOfCommons",
        "tragedyofcommons": "TragedyOfCommons",
        "tragedy of the commons": "TragedyOfCommons",
    }
    lower = v.lower()
    if lower in fixups:
        return fixups[lower]
    # Substring match
    for valid in sorted(VALID_ARCHETYPES, key=len, reverse=True):
        if valid.lower() in lower:
            return valid
    logger.warning("  [sanitize] unknown archetype type %r, defaulting to LimitsToGrowth", raw)
    return "LimitsToGrowth"


def _sanitize_archetype(arch: dict) -> dict:
    """Sanitize a single system archetype dict with defaults."""
    return {
        "archetypeType": _sanitize_archetype_type(arch.get("archetypeType")),
        "patternName": arch.get("patternName") or "",
        "description": arch.get("description") or "",
        "matchingRationale": arch.get("matchingRationale") or "",
        "currentStage": arch.get("currentStage") or "形成期",
        "structuralFeatures": arch.get("structuralFeatures") or "",
        "relatedEventIds": (
            arch["relatedEventIds"]
            if isinstance(arch.get("relatedEventIds"), list)
            else []
        ),
    }


def _sanitize_feedback_loop(loop: dict, loop_type: str) -> dict:
    """Sanitize a feedback loop dict with defaults."""
    return {
        "loopName": loop.get("loopName") or "",
        "description": loop.get("description") or "",
        "involvedNodes": (
            loop["involvedNodes"]
            if isinstance(loop.get("involvedNodes"), list)
            else []
        ),
        "strength": loop.get("strength", "中") if loop.get("strength") in ("强", "中", "弱") else "中",
        "relatedEventIds": (
            loop["relatedEventIds"]
            if isinstance(loop.get("relatedEventIds"), list)
            else []
        ),
    }


def _sanitize_leverage_point(lp: dict) -> dict:
    """Sanitize a leverage point dict with defaults."""
    return {
        "nodeName": lp.get("nodeName") or "",
        "interventionDescription": lp.get("interventionDescription") or "",
        "expectedImpact": lp.get("expectedImpact") or "",
        "difficulty": lp.get("difficulty", "中") if lp.get("difficulty") in ("高", "中", "低") else "中",
    }


def build_causal_loop(
    client: DeepSeekClient | None,
    events: list[dict],
) -> dict | None:
    """Build a causal loop diagram and match system archetypes from event data.

    Analyzes a list of events to produce:
      1. Causal Loop Diagram (CLD) with positive/negative feedback loops
      2. System archetype matching (FixesThatFail, LimitsToGrowth, etc.)
      3. Key leverage points for intervention

    Args:
        client: A DeepSeekClient instance (empirical model).
        events: A list of event dicts, each with at minimum a 'title' field.
                At least 2 events are needed for meaningful causal analysis.

    Returns:
        A dict with causalSummary, causalLoopDiagram, systemArchetypes keys,
        or None on ANY failure (graceful degradation).
    """
    if client is None:
        return None

    if not _has_minimal_event_data(events):
        return None

    events_json = _serialize_events(events)

    prompt = CAUSAL_PROMPT.format(
        event_count=len(events),
        events_json=events_json,
    )

    try:
        result = client.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是一个系统思维分析师。你的任务是根据事件数据构建因果回路图"
                        "和匹配系统基模。严格按JSON格式输出。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=8192,
        )
    except Exception:
        # Graceful degradation: any LLM call failure returns None
        return None

    # ── Defensive: validate response structure ──
    if not isinstance(result, dict):
        return None

    result.setdefault("causalSummary", "")

    # -- Sanitize causalLoopDiagram --
    cld = result.get("causalLoopDiagram")
    if not isinstance(cld, dict):
        result["causalLoopDiagram"] = {
            "nodes": [],
            "positiveFeedbackLoops": [],
            "negativeFeedbackLoops": [],
            "keyLeveragePoints": [],
        }
    else:
        if not isinstance(cld.get("nodes"), list):
            cld["nodes"] = []
        # Sanitize feedback loops
        cleaned_positive = []
        for loop in cld.get("positiveFeedbackLoops") or []:
            if isinstance(loop, dict):
                cleaned_positive.append(_sanitize_feedback_loop(loop, "positive"))
        cld["positiveFeedbackLoops"] = cleaned_positive

        cleaned_negative = []
        for loop in cld.get("negativeFeedbackLoops") or []:
            if isinstance(loop, dict):
                cleaned_negative.append(_sanitize_feedback_loop(loop, "negative"))
        cld["negativeFeedbackLoops"] = cleaned_negative

        # Sanitize leverage points
        cleaned_lps = []
        for lp in cld.get("keyLeveragePoints") or []:
            if isinstance(lp, dict):
                cleaned_lps.append(_sanitize_leverage_point(lp))
        cld["keyLeveragePoints"] = cleaned_lps

    # -- Sanitize systemArchetypes --
    archetypes = result.get("systemArchetypes")
    if not isinstance(archetypes, list):
        result["systemArchetypes"] = []
    else:
        result["systemArchetypes"] = [
            _sanitize_archetype(a) if isinstance(a, dict) else _sanitize_archetype({})
            for a in archetypes
        ]

    return result
