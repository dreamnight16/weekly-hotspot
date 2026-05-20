"""
MLM Relevance Filter — 基于阶级相关性筛选，不套标签。
"""
from client import DeepSeekClient


FILTER_PROMPT = """你是一个马列毛主义者。审查以下热点话题是否有分析价值。

对每个话题，自问：这件事是否涉及具体的阶级利益、社会矛盾或生产关系变化？
- 能指出具体的利益主体、冲突形态、矛盾关联 → 保留
- 纯消费娱乐、个人猎奇、与阶级社会无关 → 排除

不要拿"劳资矛盾""资产阶级""阶级斗争"这些标签去套。你要判断的是：这件事背后有没有真实的、物质的阶级内容？

返回格式：{"passed": [{"title": "...", "summary": "..."}]}"""


def censor_events(client: DeepSeekClient, events: list[dict]) -> list[dict]:
    if not events:
        return []
    events_text = "\n".join(f"- {e['title']}: {e['summary']}" for e in events)
    result = client.chat_json([
        {"role": "system", "content": FILTER_PROMPT},
        {"role": "user", "content": f"以下话题中，哪些有具体的阶级分析价值？不要套标签，一个一个判断：\n{events_text}"},
    ])
    return result.get("passed", events)
