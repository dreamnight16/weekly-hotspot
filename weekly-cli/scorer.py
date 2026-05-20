from client import DeepSeekClient


SCORER_PROMPT = """你是一个马列毛主义者。评估以下事件的分析价值，选出最值得深入分析的事件。

不要机械套用评分等级。先真正理解每个事件的阶级内容和矛盾形态，然后按分析价值排序。

一个事件的分析价值取决于：
- 它是否揭示了具体的矛盾运动（不是笼统的"劳资矛盾"，而是矛盾在特定条件下的具体展开）
- 它是否暴露了被日常话语掩盖的阶级利益关系
- 它是否提供了理解当前社会变化的新素材
- 它是否有足够的真实信息支撑分析——只有热度没有实质内容的事件应该筛掉

对入选事件，用一段话直接点出其核心矛盾和阶级意义。不要写"该事件反映了..."这类引语——直接说矛盾是什么、涉及谁的利益。

按分析价值降序排列，每个事件给 impactScore 和 infoGainScore（1-5 整数）。

返回格式：
{"events": [{"title": "...", "impactScore": 4, "infoGainScore": 3, "summary": "概述..."}]}"""


def score_and_select(client: DeepSeekClient, events: list[dict], top_n: int = 8) -> list[dict]:
    if len(events) <= top_n:
        top_n = len(events)
    events_text = "\n".join(f"- {e['title']}: {e['summary']}" for e in events)
    result = client.chat_json([
        {"role": "system", "content": SCORER_PROMPT},
        {"role": "user", "content": f"以下 {len(events)} 个事件，选出最有辩证分析价值的前 {top_n} 个，按价值降序排列。要给出具体理由，不要套评分模板：\n{events_text}"},
    ])
    return result.get("events", [])
