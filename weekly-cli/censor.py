"""
MLM Relevance Filter — 马列毛主义相关性筛选。
不是政审，而是滤除纯娱乐八卦，保留有阶级/社会/政治/经济意义的事件。
"""
from client import DeepSeekClient


FILTER_PROMPT = """你是一个以马列毛主义为指导的分析师。请筛选以下热点事件。

保留标准（满足任一即可）：
- 涉及阶级斗争、劳资矛盾、工农权益、生产关系变化
- 涉及国际关系、帝国主义扩张、霸权主义、殖民主义残留
- 涉及经济基础变化（产业政策、所有制调整、分配制度）
- 涉及社会主要矛盾与人民群众切身利益
- 涉及科技发展对生产力/生产关系的辩证作用
- 涉及意识形态斗争、文化领导权、上层建筑变革
- 涉及民族解放运动、第三世界发展、反帝反殖斗争

排除标准：
- 纯娱乐八卦、明星私生活、饭圈争端
- 纯商业广告、消费主义营销
- 与人民群众利益无关的个人猎奇

返回通过筛选的事件列表。
返回格式：{"passed": [{"title": "...", "summary": "..."}]}"""


def censor_events(client: DeepSeekClient, events: list[dict]) -> list[dict]:
    if not events:
        return []
    events_text = "\n".join(f"- {e['title']}: {e['summary']}" for e in events)
    result = client.chat_json([
        {"role": "system", "content": FILTER_PROMPT},
        {"role": "user", "content": f"请基于马列毛主义相关性筛选以下事件：\n{events_text}"},
    ])
    return result.get("passed", events)
