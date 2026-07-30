"""Phase 1: Phenomenon Grasping — the first stage of dialectical epistemology.

From perceptual concreteness: 去粗取精、去伪存真、由此及彼、由表及里.
"""
from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt

GRASPING_PROMPT = load_prompt("dialectical/grasping")


def build_events_text(events: list[dict]) -> str:
    """Format raw events for prompt injection."""
    lines = []
    for i, e in enumerate(events):
        lines.append(f"[{i+1}] {e.get('title', '(无标题)')}")
        summary = e.get("summary")
        if summary is not None:
            lines.append(f"    {str(summary)[:200]}")
    return "\n".join(lines)


def grasp_phenomena(
    client: DeepSeekClient,
    events: list[dict],
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

    events_text = build_events_text(events)
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
            sanitized_e["sourceGrade"] = {
                "reliability": "C",
                "credibility": 3,
                "rationale": "未提供来源评估",
            }
        sanitized.append(sanitized_e)
    result = {**result, "selectedEvents": sanitized}

    return result
