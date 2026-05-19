from client import DeepSeekClient


ANALYZER_PROMPT = """你是一个调查记者和分析师。请对以下热点事件进行深度梳理。

事件：{title}
背景：{summary}

请完成以下三项分析：

### 1. 时间线（5-10个节点）
关键节点按时间顺序排列。每个节点包含：ISO时间、标题、详细描述、关联证据ID列表。
时间必须精确到小时级别（如 2026-05-18T14:00:00+08:00）。

### 2. 证据收集与标注
对每条证据标注：
- sourceType: "官媒" | "社交平台" | "一手材料" | "其他"
- sourceName: 来源名称
- sourceUrl: 来源链接（可为null）
- content: 证据摘要
- authenticity: "真实" | "存疑" | "不实" | "待验证"
- aiReason: 判断理由（一句话）

### 3. 节点间关系
标注节点之间的关联类型：
- "因果"：一个节点导致另一个
- "关联"：两个节点主题相关但非因果
- "反驳"：一个节点的信息推翻另一个

每条关系包含 from, to, type, description（一句话）。

返回格式：
{{
  "id": "evt-{idx}",
  "title": "{title}",
  "impactScore": {impactScore},
  "infoGainScore": {infoGainScore},
  "summary": "{summary}",
  "timeline": [
    {{
      "id": "tl-{idx}-1",
      "time": "ISO时间",
      "title": "节点标题",
      "description": "详细描述",
      "evidenceRefs": ["ev-{idx}-1"]
    }}
  ],
  "evidence": [
    {{
      "id": "ev-{idx}-1",
      "sourceType": "官媒",
      "sourceName": "来源",
      "sourceUrl": null,
      "content": "摘要",
      "authenticity": "真实",
      "aiReason": "判断理由"
    }}
  ],
  "edges": [
    {{
      "from": "tl-{idx}-1",
      "to": "tl-{idx}-2",
      "type": "因果",
      "description": "一句话说明"
    }}
  ]
}}"""


def analyze_event(client: DeepSeekClient, event: dict, idx: int = 1) -> dict:
    prompt = ANALYZER_PROMPT.format(
        title=event["title"],
        summary=event["summary"],
        impactScore=event["impactScore"],
        infoGainScore=event["infoGainScore"],
        idx=idx,
    )
    result = client.chat_json([
        {"role": "system", "content": "你是一个调查记者，擅长深度分析事件。请严格按照要求的JSON格式输出。"},
        {"role": "user", "content": prompt},
    ], max_tokens=16384)
    return result
