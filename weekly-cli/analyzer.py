from client import DeepSeekClient


ANALYZER_PROMPT = """你是一个调查记者。请基于以下**真实搜索结果**对热点事件进行深度梳理。

## 事件
标题：{title}
概述：{summary}

## 搜索结果（来自搜索引擎的真实网页）
{search_results}

## 任务

### 1. 时间线（5-10个节点）
从搜索结果中提取关键时间节点，按时间顺序排列。每个节点包含：
- id: "tl-{idx}-序号"
- time: ISO 时间（如 2026-05-18T14:00:00+08:00），必须从搜索结果中提取
- title: 节点标题
- description: 详细描述（基于搜索结果，不要编造）
- evidenceRefs: ["ev-{idx}-对应证据序号"]

**重要：只构建搜索结果中能找到信息的时间节点。如果搜索结果信息不足，节点可以少于5个。**

### 2. 证据收集与标注
从搜索结果中提取证据，每条证据必须有对应的来源网页：
- id: "ev-{idx}-序号"
- sourceType: "官媒" | "社交平台" | "一手材料" | "其他"
- sourceName: 来源名称（网站名或媒体名）
- sourceUrl: **必须填入搜索结果中真实的 URL**
- content: 证据摘要（基于搜索结果，不要编造）
- authenticity: "真实" | "存疑" | "不实" | "待验证"
- aiReason: 判断理由（基于来源可信度，一句话）

### 3. 节点间关系
标注节点之间的关联：
- from / to: 节点 id
- type: "因果" | "关联" | "反驳"
- description: 一句话说明

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
      "sourceUrl": "https://...",
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
}}

**如果搜索结果太少或质量太低，宁可少输出节点和证据，也不要编造。**"""


def build_search_results_text(results: list[dict]) -> str:
    if not results:
        return "（无搜索结果，请基于事件标题和概述进行最小化分析，只输出你能确认的信息。）"

    lines = []
    for i, r in enumerate(results):
        lines.append(f"[{i+1}] 标题: {r['title']}")
        lines.append(f"    URL: {r['url']}")
        lines.append(f"    摘要: {r['snippet']}")
        lines.append("")
    return "\n".join(lines)


def analyze_event(
    client: DeepSeekClient,
    event: dict,
    search_results: list[dict],
    idx: int = 1,
) -> dict:
    prompt = ANALYZER_PROMPT.format(
        title=event["title"],
        summary=event["summary"],
        search_results=build_search_results_text(search_results),
        impactScore=event["impactScore"],
        infoGainScore=event["infoGainScore"],
        idx=idx,
    )
    result = client.chat_json([
        {"role": "system", "content": "你是一个调查记者，擅长深度分析事件。请严格基于提供的搜索结果进行分析，不要编造任何信息。请严格按照要求的JSON格式输出。"},
        {"role": "user", "content": prompt},
    ], max_tokens=16384)
    return result
