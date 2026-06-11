"""Phase 4: Cross-event synthesis — 跨事件综合梳理，找出全周矛盾运动的脉络。"""
from chinese_scraper_utils import DeepSeekClient


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


SYNTHESIZER_PROMPT = """你是一个马列毛主义者。以下是本周经深度分析后的 {event_count} 个社会事件。你的任务是对它们进行**跨事件综合梳理**——不是重复单个事件的分析，而是找出事件之间的联系、贯穿全周的趋势、矛盾运动的总图景。

## 本周事件

{events_context}

## 分析方法——找事件之间的物质联系

**跨事件主题**不是把相似事件贴标签。你要找的是：
- 不同事件是否源于同一个深层矛盾的不同表现？
- 一个事件的变化是否改变了其他事件的条件？
- 多个事件是否指向同一股社会力量的运动方向？

**趋势识别**要回答：
- 在具体利益格局中，力量对比发生了怎样的变化？
- 哪些矛盾在激化、哪些在缓和、哪些在转化形态？
- 哪些是短期波动、哪些是结构变化的征兆？

**矛盾运动**要找的是全周层面的运动：
- 本周最核心的矛盾对抗是什么？如何贯穿多个事件？
- 不同矛盾之间是相互激化还是相互抵消？
- 从全周看，矛盾走向对抗升级、暂时稳定、还是质变的前夜？

**数据诚实**：事件之间真实联系不明确时，如实说信息不足。不要强行制造联系。如果本周缺乏贯穿性主线，weeklyNarrative 可以写"本周事件较为离散"并说明原因。

## 原则

- 每条判断必须有事件分析为据，标注涉及的 event id
- 不要堆砌"辩证""矛盾""斗争"等空话
- 用朴实中文，说清楚谁在什么条件下如何
- 注意：事件来自国内外不同平台，报道框架各有立场。穿透框架看物质内容

## 输出 JSON 格式

{{
  "weeklyNarrative": "200-300字。串联全周事件的运动脉络。让人读完知道这周发生了什么层面的变化。",
  "crossCuttingThemes": [
    {{
      "name": "主题标签，如'科技资本集中化'",
      "description": "主题的具体内容，涉及哪些利益",
      "relatedEventIds": ["evt-1", "evt-3"],
      "significance": "该主题揭示了什么深层矛盾或趋势"
    }}
  ],
  "trends": [
    {{
      "name": "趋势名称",
      "description": "趋势内容",
      "direction": "【只填枚举值】上升 / 下降 / 转型 / 激化 / 缓和",
      "evidenceEventIds": ["evt-1", "evt-2"]
    }}
  ],
  "contradictionsInMotion": [
    {{
      "contradiction": "矛盾表述",
      "opposingForces": "对立双方及其物质利益",
      "eventsInvolved": ["evt-1", "evt-4"],
      "currentState": "【只填枚举值】对抗激化 / 暂时缓和 / 向新形态转化 / 隐性积累",
      "outlook": "矛盾的可能走向"
    }}
  ],
  "globalAssessment": "本周总体判断。核心矛盾运动处在什么阶段，值得关注什么。",
  "dataGaps": ["因信息不足未能判断的方面"]
}}"""


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
