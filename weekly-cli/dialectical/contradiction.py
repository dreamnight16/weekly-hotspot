"""Phase 2: Contradiction Identification — the second stage of dialectical epistemology.

从现象把握到矛盾识别：识别具体矛盾、利益结构、阶级立场.
"""
from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt

CONTRADICTION_PROMPT = load_prompt("dialectical/contradiction")


def build_contradiction_context(events: list[dict]) -> str:
    """Format selected events for contradiction prompt injection.

    Provides richer context than Phase 1, including materialContent
    for dialectical analysis of interest structures and class positions.
    """
    if not events:
        return ""

    lines = []
    for i, e in enumerate(events):
        lines.append(f"[事件 {i+1}]")
        lines.append(f"  ID: {e.get('id', f'evt-{i+1}')}")
        lines.append(f"  标题: {e.get('title', '(无标题)')}")
        summary = e.get("summary")
        if summary is not None:
            lines.append(f"  概述: {str(summary)[:300]}")
        material = e.get("materialContent")
        if material is not None:
            lines.append(f"  物质内容: {str(material)[:500]}")
        lines.append("")
    return "\n".join(lines)


def identify_contradictions(
    client: DeepSeekClient,
    events: list[dict],
) -> dict:
    """Execute Phase 2: Contradiction Identification.

    Loads the dialectical/contradiction prompt, formats event context,
    calls the LLM, and returns structured contradiction analysis.

    Returns a dict matching the contradiction analysis schema:
    - phaseSummary: overall contradiction summary for this phase
    - events: list of events with contradiction analysis fields
    - overallContradictionLandscape: macro-level contradiction pattern
    - interestStructures: list of interest group analyses
    - classPositions: list of class position analyses
    - nineDimScores: dialectic scoring across 9 dimensions
    - competingHypotheses: alternative explanatory hypotheses
    """
    if not events:
        return {
            "phaseSummary": "无事件可供矛盾分析",
            "events": [],
            "overallContradictionLandscape": "",
            "interestStructures": [],
            "classPositions": [],
            "nineDimScores": {},
            "competingHypotheses": [],
        }

    events_text = build_contradiction_context(events)
    prompt = CONTRADICTION_PROMPT.format(
        event_count=len(events),
        events_text=events_text,
    )

    try:
        result = client.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是一个唯物辩证法研究者。你的任务是矛盾识别——"
                        "从现象把握的结果出发，提取每个事件背后的矛盾结构、"
                        "利益格局和阶级立场。用朴实中文写作，不堆砌术语，"
                        "不贴标签。严格按JSON格式输出。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=16384,
        )
    except Exception as e:
        from config import get_logger as _gl
        _gl("contradiction").warning("identify_contradictions: chat_json failed: %s", e)
        return {"phaseSummary": "LLM调用失败", "events": [], "overallContradictionLandscape": ""}

    # ── Defensive: ensure events list is valid ──
    events_list = result.get("events")
    if events_list is None:
        result["events"] = []
    elif not isinstance(events_list, list):
        result["events"] = []

    # ── Defensive: sanitize event entries, add defaults for missing fields ──
    if isinstance(result.get("events"), list):
        sanitized = []
        for i, e in enumerate(result["events"]):
            if not isinstance(e, dict):
                continue
            sanitized_e = dict(e)
            if "id" not in sanitized_e:
                sanitized_e["id"] = f"evt-{i+1}"
            if "title" not in sanitized_e:
                sanitized_e["title"] = "(无标题)"
            if "isDirectExpression" not in sanitized_e:
                sanitized_e["isDirectExpression"] = True
            sanitized.append(sanitized_e)
        result["events"] = sanitized

    # ── Defensive: ensure other top-level fields exist ──
    if result.get("interestStructures") is None:
        result["interestStructures"] = []
    if result.get("classPositions") is None:
        result["classPositions"] = []
    if result.get("nineDimScores") is None:
        result["nineDimScores"] = {}
    if result.get("competingHypotheses") is None:
        result["competingHypotheses"] = []

    return result
