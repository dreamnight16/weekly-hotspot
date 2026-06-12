from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt

SCORER_PROMPT = load_prompt("scorer")


def score_and_select(client: DeepSeekClient, events: list[dict], top_n: int = 8) -> list[dict]:
    if len(events) <= top_n:
        top_n = len(events)
    events_text = "\n".join(f"- {e['title']}: {e['summary']}" for e in events)
    result = client.chat_json([
        {"role": "system", "content": SCORER_PROMPT},
        {"role": "user", "content": f"以下 {len(events)} 个事件，选出最有辩证分析价值的前 {top_n} 个，按价值降序排列。要给出具体理由，不要套评分模板：\n{events_text}"},
    ])
    return result.get("events", [])
