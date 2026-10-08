"""Phase 1: Phenomenon Grasping — the first stage of dialectical epistemology.

From perceptual concreteness: 去粗取精、去伪存真、由此及彼、由表及里.
"""
from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt

GRASPING_PROMPT = load_prompt("dialectical/grasping")


def build_events_text(events: list[dict], dossiers: dict | None = None) -> str:
    """Format events plus their retrieved evidence for prompt injection.

    The evidence block is the point: without it this stage sees a headline and
    a heat ranking, and any "material content" it produces is invention.
    """
    from evidence.collector import dossier_to_text

    lines = []
    for i, e in enumerate(events):
        lines.append(f"[{i+1}] {e.get('title', '(无标题)')}")
        summary = e.get("summary")
        if summary is not None:
            lines.append(f"    概述: {str(summary)[:400]}")
        if e.get("eventStatus"):
            lines.append(f"    事件状态: {e.get('eventStatus')}")
        aliases = e.get("topicAliases") or []
        if len(aliases) > 1:
            lines.append(f"    同一事件的其他标题: {'；'.join(aliases[1:4])}")

        dossier = _lookup_dossier(e, dossiers)
        if dossier is not None:
            lines.append("    【已检索证据材料】")
            block = dossier_to_text(dossier)
            lines.extend(f"    {ln}" for ln in block.splitlines() if ln.strip())
        else:
            lines.append("    （未检索到证据材料——只能依据标题做最小判断，必须标注证据不足）")
    return "\n".join(lines)


def _lookup_dossier(event: dict, dossiers: dict | None):
    if not dossiers:
        return None
    key = str(event.get("eventId") or event.get("id") or "")
    return dossiers.get(key)


def grasp_phenomena(
    client: DeepSeekClient,
    events: list[dict],
    dossiers: dict | None = None,
) -> dict:
    """Execute Phase 1: Phenomenon Grasping.

    Returns a dict matching PhenomenonGrasping schema fields:
    - selectedEvents: events with dialectical analysis value
    - excludedEvents: events excluded with specific reasons
    - sourceQualityReport: overall source quality assessment
    """
    if not events:
        return {
            "selectedEvents": [],
            "excludedEvents": [],
            "sourceQualityReport": "无事件可供分析",
        }

    events_text = build_events_text(events, dossiers)
    prompt = GRASPING_PROMPT.format(
        event_count=len(events),
        events_text=events_text,
    )

    try:
        result = client.chat_json([
            {
                "role": "system",
                "content": (
                    "你是一个唯物辩证法研究者。你的任务是现象把握——"
                    "认识运动的第一个阶段。用朴实中文写作，不堆砌术语，"
                    "不贴标签。严格按JSON格式输出。"
                ),
        },
        {"role": "user", "content": prompt},
                ], max_tokens=32768)
    except Exception as e:
        from config import get_logger as _gl
        _gl("grasping").warning("grasp_phenomena: chat_json failed: %s", e)
        return {"selectedEvents": [], "excludedEvents": [], "sourceQualityReport": "LLM调用失败"}

    # Ensure selectedEvents have required fields and are a valid list
    selected = result.get("selectedEvents")
    if selected is None:
        result["selectedEvents"] = []
        return result
    if not isinstance(selected, list):
        result["selectedEvents"] = []
        return result
    sanitized = []
    for i, e in enumerate(selected):
        if not isinstance(e, dict):
            continue
        sanitized_e = dict(e)
        # Force id to string (LLM often returns integers)
        raw_id = sanitized_e.get("id", f"evt-{i+1}")
        sanitized_e["id"] = str(raw_id) if not isinstance(raw_id, str) else raw_id
        if "sourceGrade" not in sanitized_e:
            # Never invent a grade.  A source we did not retrieve is not "C3,
            # basic reliability, possibly true" — it is ungraded.  Defaulting
            # to a middle grade made an absent assessment look like a made one.
            sanitized_e["sourceGrade"] = {
                "reliability": "UNVERIFIED",
                "credibility": 6,
                "rationale": "未检索到来源，未作可靠性评定",
            }
        sanitized.append(sanitized_e)
    result = {**result, "selectedEvents": sanitized}

    # Also sanitize excludedEvents — LLM may return integer IDs here too
    excluded = result.get("excludedEvents")
    if isinstance(excluded, list):
        clean_excluded = []
        for e in excluded:
            if not isinstance(e, dict):
                continue
            ce = dict(e)
            raw_id = ce.get("id", "")
            ce["id"] = str(raw_id) if not isinstance(raw_id, str) else raw_id
            clean_excluded.append(ce)
        result["excludedEvents"] = clean_excluded
    elif excluded is None:
        result["excludedEvents"] = []

    return result
