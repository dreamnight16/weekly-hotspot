"""Phase 4: Historical Positioning — the fourth stage of dialectical epistemology.

Position each event within the historical materialism framework:
  - Per-event: productive forces, production relations, base, superstructure,
    class force comparison, historical position.
  - Cross-event: epoch themes, contradiction landscape, system archetypes,
    hidden connections, historical analogies.
"""
from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt

POSITIONING_PROMPT = load_prompt("dialectical/positioning")


def build_positioning_context(events: list[dict]) -> str:
    """Build XML event blocks for prompt injection.

    Formats each event's id, title, summary, materialContent, and scores
    for historical materialism positioning analysis. Returns a no-information
    empty string when events is empty.
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
        impact = e.get("impactScore")
        if impact is not None:
            lines.append(f"  影响度评分: {impact}")
        infogain = e.get("infoGainScore")
        if infogain is not None:
            lines.append(f"  信息增益评分: {infogain}")
        lines.append("")
    return "\n".join(lines)


def position_historically(
    client: DeepSeekClient,
    events: list[dict],
) -> dict:
    """Execute Phase 4: Historical Positioning.

    Loads the dialectical/positioning prompt, formats event context,
    calls the LLM, and returns structured historical materialism analysis.

    Returns a dict matching the HistoricalPositioning schema:
    - phaseSummary: overall historical positioning summary
    - events: list of events with per-event analysis fields
      (productiveForces, productionRelations, baseStructure,
       superstructure, classForceComparison, historicalPosition)
    - crossCuttingSynthesis: cross-event synthesis string
    - epochThemes: list of epoch theme dicts
    - systemArchetypes: list of system archetype dicts
    - hiddenConnections: list of hidden connection dicts
    - historicalAnalogies: list of historical analogy dicts

    When events is empty or client is None, returns a default structure.
    """
    if not events:
        return {
            "phaseSummary": "无事件可供历史定位",
            "events": [],
            "crossCuttingSynthesis": "",
            "epochThemes": [],
            "systemArchetypes": [],
            "hiddenConnections": [],
            "historicalAnalogies": [],
        }

    events_text = build_positioning_context(events)
    prompt = POSITIONING_PROMPT.format(
        event_count=len(events),
        events_text=events_text,
    )

    try:
        result = client.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是一个唯物辩证法研究者。你的任务是历史定位——"
                        "在辩证展开的基础上，将每个事件置于历史唯物主义的"
                        "框架中定位，并进行跨事件的综合。用朴实中文写作，"
                        "不堆砌术语，不贴标签。严格按JSON格式输出。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=16384,
        )
    except Exception as e:
        from config import get_logger as _gl
        _gl("positioning").warning("position_historically: chat_json failed: %s", e)
        return {"phaseSummary": "LLM调用失败", "events": [], "crossCuttingSynthesis": {}, "historicalAnalogies": []}

    # ── Defensive: ensure events list is valid ──
    events_list = result.get("events")
    if events_list is None:
        result["events"] = []
    elif not isinstance(events_list, list):
        result["events"] = []

    # ── Defensive: enrich each event with per-positioning defaults ──
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
            # Per-event historical materialism positioning defaults
            if "productiveForces" not in sanitized_e:
                sanitized_e["productiveForces"] = ""
            if "productionRelations" not in sanitized_e:
                sanitized_e["productionRelations"] = ""
            if "baseStructure" not in sanitized_e:
                sanitized_e["baseStructure"] = ""
            if "superstructure" not in sanitized_e:
                sanitized_e["superstructure"] = ""
            if "classForceComparison" not in sanitized_e:
                sanitized_e["classForceComparison"] = ""
            if "historicalPosition" not in sanitized_e:
                sanitized_e["historicalPosition"] = ""
            sanitized.append(sanitized_e)
        result["events"] = sanitized

    # ── Defensive: ensure cross-event synthesis fields exist ──
    if result.get("crossCuttingSynthesis") is None:
        result["crossCuttingSynthesis"] = ""
    if result.get("epochThemes") is None:
        result["epochThemes"] = []
    elif not isinstance(result["epochThemes"], list):
        result["epochThemes"] = []
    if result.get("systemArchetypes") is None:
        result["systemArchetypes"] = []
    elif not isinstance(result["systemArchetypes"], list):
        result["systemArchetypes"] = []
    if result.get("hiddenConnections") is None:
        result["hiddenConnections"] = []
    elif not isinstance(result["hiddenConnections"], list):
        result["hiddenConnections"] = []
    if result.get("historicalAnalogies") is None:
        result["historicalAnalogies"] = []
    elif not isinstance(result["historicalAnalogies"], list):
        result["historicalAnalogies"] = []
    if result.get("phaseSummary") is None:
        result["phaseSummary"] = ""

    return result
