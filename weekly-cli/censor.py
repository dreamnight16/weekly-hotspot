"""
MLM Relevance Filter — 基于阶级相关性筛选，不套标签。
"""
from chinese_scraper_utils import DeepSeekClient


FILTER_PROMPT = """你是一个马列毛主义者。审查以下热点话题是否有分析价值。

对每个话题，自问：这件事是否涉及具体的阶级利益、社会矛盾或生产关系变化？
- 能指出具体的利益主体、冲突形态、矛盾关联 → 保留
- 纯消费娱乐、个人猎奇、与阶级社会无关 → 排除

不要拿"劳资矛盾""资产阶级""阶级斗争"这些标签去套。你要判断的是：这件事背后有没有真实的、物质的阶级内容？

**合规注意**：以下类型的事件必须排除，不得出现在面向中国读者的个人博客中：
- 涉及中国领土主权争议、分裂主义的内容
- 涉及被中国政府依法禁止的组织及其活动
- 可能被理解为煽动颠覆国家政权的内容
- 注意：正常的阶级分析、社会矛盾讨论、经济政策批评不属于上述范畴，不应排除

**国际信源**：部分话题来自国际媒体，其报道框架本身具有特定的阶级立场（如西方媒体的帝国主义话语、冷战思维）。审查时只看事件本身的阶级内容，不受信源立场影响。

返回格式：{"passed": [{"title": "...", "summary": "..."}]}"""


def censor_events(client: DeepSeekClient, events: list[dict]) -> list[dict]:
    if not events:
        return []
    events_text = "\n".join(f"- {e['title']}: {e['summary']}" for e in events)
    result = client.chat_json([
        {"role": "system", "content": FILTER_PROMPT},
        {"role": "user", "content": f"以下话题来自国内外多个平台。哪些有具体的阶级分析价值？注意排除违反中国互联网法规的内容，同时不被国际媒体的报道框架带偏。一个一个判断：\n{events_text}"},
    ])
    return result.get("passed", [])
