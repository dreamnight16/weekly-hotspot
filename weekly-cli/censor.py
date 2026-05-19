from client import DeepSeekClient


CENSOR_PROMPT = """你是一个内容审核助手。以下是本周热点事件候选列表。请识别并排除以下类型的事件：
- 纯政治敏感话题（涉及领导人、领土主权、民族宗教等）
- 可能违反内容审查政策的事件
- 不适合在个人技术博客公开发表的内容

返回通过审查的事件列表。**不要解释审核原因，不要提及被排除的事件。**
返回格式：{"passed": [{"title": "...", "summary": "..."}]}"""


def censor_events(client: DeepSeekClient, events: list[dict]) -> list[dict]:
    events_text = "\n".join(f"- {e['title']}: {e['summary']}" for e in events)
    result = client.chat_json([
        {"role": "system", "content": CENSOR_PROMPT},
        {"role": "user", "content": f"请审核以下事件：\n{events_text}"},
    ])
    return result.get("passed", events)
