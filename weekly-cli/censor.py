"""
MLM Relevance Filter — 基于阶级相关性筛选，不套标签。
"""
from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt

FILTER_PROMPT = load_prompt("censor")


def censor_events(client: DeepSeekClient, events: list[dict]) -> list[dict]:
    if not events:
        return []
    events_text = "\n".join(f"- {e['title']}: {e['summary']}" for e in events)
    result = client.chat_json([
        {"role": "system", "content": FILTER_PROMPT},
        {"role": "user", "content": f"以下话题来自国内外多个平台。哪些有具体的阶级分析价值？注意排除违反中国互联网法规的内容，同时不被国际媒体的报道框架带偏。一个一个判断：\n{events_text}"},
    ])
    return result.get("passed", [])
