"""Phase 4: Cross-event synthesis — 跨事件综合梳理，找出全周矛盾运动的脉络。"""
from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt


def _build_events_context(events: list[dict]) -> str:
    """将分析后的事件浓缩为 XML 块，送入 synthesis prompt。"""
    blocks = []
    for e in events:
        ca = e.get("classAnalysis", {})
        evidence = e.get("evidence", [])
        real = sum(1 for ev in evidence if ev.get("authenticity") == "真实")
        dubious = sum(1 for ev in evidence if ev.get("authenticity") == "存疑")
        blocks.append(
            f"<event_{e['id']}>\n"
            f"  <title>{e['title']}</title>\n"
            f"  <impactScore>{e['impactScore']}</impactScore>\n"
            f"  <infoGainScore>{e['infoGainScore']}</infoGainScore>\n"
            f"  <classNature>{ca.get('classNature', '')}</classNature>\n"
            f"  <contradiction>{ca.get('contradiction', '')}</contradiction>\n"
            f"  <historicalContext>{ca.get('historicalContext', '')}</historicalContext>\n"
            f"  <dialecticalSummary>{e.get('dialecticalSummary', '')}</dialecticalSummary>\n"
            f"  <timelineNodes>{len(e.get('timeline', []))}</timelineNodes>\n"
            f"  <evidenceSummary>真实{real}条 存疑{dubious}条</evidenceSummary>\n"
            f"</event_{e['id']}>"
        )
    return "\n".join(blocks)


SYNTHESIZER_PROMPT = load_prompt("synthesizer")


def synthesize_events(
    client: DeepSeekClient,
    events: list[dict],
) -> dict:
    """Phase 4: Cross-event synthesis. 返回 dict 匹配 WeeklySynthesis schema。"""
    context = _build_events_context(events)
    prompt = SYNTHESIZER_PROMPT.format(
        event_count=len(events),
        events_context=context,
    )
    result = client.chat_json([
        {"role": "system", "content": "你是一个马列毛主义者。基于事件分析结果进行综合梳理。严格按 JSON 格式输出。"},
        {"role": "user", "content": prompt},
    ], max_tokens=8192)
    return result
