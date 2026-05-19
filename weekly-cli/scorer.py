from client import DeepSeekClient


SCORER_PROMPT = """你是一个资深新闻编辑。以下是本周通过初审的热点事件列表。

请为每个事件按两个维度评分（1-5分，整数）：
- **事件影响（impactScore）**：影响范围、是否产生连锁反应、改变了什么。这是最重要的维度。
- **信息增量（infoGainScore）**：是否带来新认知、不是旧闻翻新

评分后，按「事件影响」降序排列，选出最有价值的前 N 个事件。
对每个入选事件写一段 200 字以内的概述。

返回格式：
{"events": [{"title": "...", "impactScore": 4, "infoGainScore": 3, "summary": "概述..."}]}"""


def score_and_select(client: DeepSeekClient, events: list[dict], top_n: int = 8) -> list[dict]:
    if len(events) <= top_n:
        top_n = len(events)
    events_text = "\n".join(f"- {e['title']}: {e['summary']}" for e in events)
    result = client.chat_json([
        {"role": "system", "content": SCORER_PROMPT},
        {"role": "user", "content": f"请为以下 {len(events)} 个事件评分，选出前 {top_n} 个：\n{events_text}"},
    ])
    return result.get("events", [])
