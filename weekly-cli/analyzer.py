from client import DeepSeekClient


ANALYZER_PROMPT = """你是一个以马列毛主义为理论基石的现代分析师。请基于以下**真实搜索结果**对热点事件进行阶级分析与事件梳理。

## 事件
标题：{title}
概述：{summary}

## 搜索结果（来自搜索引擎的真实网页）
{search_results}

## 分析任务

### 0. 阶级分析（classAnalysis）
用马列毛主义视角分析该事件的阶级本质：
- classNature: 该事件反映了哪个阶级/阶层的利益诉求？
- contradiction: 事件揭示了什么主要矛盾？（如：劳资矛盾、帝国主义与第三世界的矛盾、生产力与生产关系的矛盾）
- historicalContext: 从历史唯物主义角度，该事件在历史进程中的位置

### 1. 时间线（5-10个节点）
从搜索结果中提取关键时间节点，按时间顺序排列。每个节点包含：
- id: "tl-{idx}-序号"
- time: ISO 时间，必须从搜索结果中提取
- title: 节点标题
- description: 基于搜索结果描述，点明该节点的阶级/矛盾意义
- evidenceRefs: ["ev-{idx}-对应证据序号"]

### 2. 证据收集与标注
从搜索结果中提取证据：
- id: "ev-{idx}-序号"
- sourceType: "官媒" | "社交平台" | "一手材料" | "其他"
- sourceName: 来源名称
- sourceUrl: **必须填入真实 URL**
- content: 证据摘要
- authenticity: "真实" | "存疑" | "不实" | "待验证"
- aiReason: 判断理由
- classBias: 该来源的阶级立场 — "无产阶级立场" | "资产阶级立场" | "小资产阶级立场" | "帝国主义话语" | "待判断"

### 3. 节点间关系
- from / to: 节点 id
- type: "因果" | "关联" | "矛盾"
- description: 一句话说明，须体现辩证关系

### 4. 辩证总结（dialecticalSummary）
100字以内，用辩证唯物主义视角概括该事件的历史意义、矛盾运动和可能的发展方向。

返回格式：
{{
  "id": "evt-{idx}",
  "title": "{title}",
  "impactScore": {impactScore},
  "infoGainScore": {infoGainScore},
  "summary": "{summary}",
  "classAnalysis": {{
    "classNature": "...",
    "contradiction": "...",
    "historicalContext": "..."
  }},
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
      "sourceName": "来源名称",
      "sourceUrl": "https://...",
      "content": "证据摘要",
      "authenticity": "真实",
      "aiReason": "判断理由",
      "classBias": "无产阶级立场"
    }}
  ],
  "edges": [
    {{
      "from": "tl-{idx}-1",
      "to": "tl-{idx}-2",
      "type": "因果",
      "description": "辩证关系说明"
    }}
  ],
  "dialecticalSummary": "..."
}}

**核心原则：**
- 一切分析基于真实搜索结果，不编造
- 阶级分析必须具体，不要空谈理论概念
- 关系类型用"矛盾"替代"反驳"，体现辩证唯物主义
- 如果搜索结果不足，宁缺毋滥"""


def build_search_results_text(results: list[dict]) -> str:
    if not results:
        return "（无搜索结果，请基于事件标题和概述进行最小化分析。标注缺乏信息来源。）"

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
        {"role": "system", "content": "你是一个以马列毛主义为理论基石的分析师。请严格基于提供的搜索结果进行分析。阶级分析要具体、辩证、历史唯物。不要编造任何信息。严格按照JSON格式输出。"},
        {"role": "user", "content": prompt},
    ], max_tokens=16384)
    return result
