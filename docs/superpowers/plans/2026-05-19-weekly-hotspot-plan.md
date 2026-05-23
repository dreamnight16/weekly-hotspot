# 每周热点深度梳理 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建「每周热点深度梳理」功能，包含 Python CLI（DeepSeek API 驱动的事件筛选与梳理）和 Astro/React 前端（溯源报告风格的时间线/关系网/证据展示）

**Architecture:** Python CLI 通过 DeepSeek API 分三阶段处理（政审→评分筛选→逐事件梳理），输出结构化 JSON 到 Blog 的 Astro content collection。前端全静态构建，React islands 负责交互式可视化。

**Tech Stack:** Python 3 + openai SDK (DeepSeek), Astro 4 + React 18 + TypeScript + Tailwind CSS, react-force-graph-2d

**Repos involved:**
- `C:\Users\DreamNight\Documents\01My\funny\weekly-cli\` — Python CLI
- `C:\Users\DreamNight\Documents\01My\myBlog\` — Blog 前端

---

## File Map

```
weekly-cli/                          # Python CLI (新项目)
  config.py                          # API key from env, paths
  schema.py                          # Pydantic models
  client.py                          # DeepSeek OpenAI-compatible wrapper
  censor.py                          # Phase 0: 政审过滤
  scorer.py                          # Phase 1: 评分筛选
  analyzer.py                        # Phase 2: 逐事件深度梳理
  main.py                            # 编排三阶段 + 输出 JSON
  requirements.txt                   # openai, pydantic
  test_censor.py                     # 政审测试
  test_scorer.py                     # 评分测试
  test_analyzer.py                   # 梳理测试
  test_schema.py                     # Schema 验证测试

myBlog/
  src/content/config.ts              # [修改] 添加 weekly collection
  src/pages/weekly/
    index.astro                      # 往期列表页
    [id].astro                       # 当期详情页
  src/components/weekly/
    ScoreBadge.tsx                   # 评分徽章
    TimelineView.tsx                 # 垂直时间线
    GraphView.tsx                    # 力导向关系网
    EvidenceView.tsx                 # 证据表格 + 真伪标签
    EventCard.tsx                    # 事件卡片 + Tab 切换
```

---

## Part A: Python CLI

### Task 1: 项目脚手架

**Files:**
- Create: `weekly-cli/requirements.txt`
- Create: `weekly-cli/config.py`

- [ ] **Step 1: 创建 requirements.txt**

```text
openai>=1.0.0
pydantic>=2.0.0
```

- [ ] **Step 2: 安装依赖**

```bash
cd weekly-cli && pip install -r requirements.txt
```

- [ ] **Step 3: 创建 config.py**

```python
import os
from pathlib import Path

DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

BLOG_CONTENT_DIR = Path(os.environ.get(
    "BLOG_CONTENT_DIR",
    r"C:\Users\DreamNight\Documents\01My\myBlog\src\content\weekly"
))
```

- [ ] **Step 4: 验证 — 运行 Python 检查导入**

```bash
cd weekly-cli && python -c "from config import DEEPSEEK_MODEL, BLOG_CONTENT_DIR; print('OK')"
```
Expected: `OK`

---

### Task 2: 数据模型

**Files:**
- Create: `weekly-cli/schema.py`
- Create: `weekly-cli/test_schema.py`

- [ ] **Step 1: 编写 model 和 validation test**

`test_schema.py`:
```python
import json
from schema import WeeklyIssue, Event, TimelineNode, EvidenceNode, Edge

SAMPLE_EVENT = {
    "id": "evt-1",
    "title": "测试事件",
    "impactScore": 4,
    "infoGainScore": 3,
    "summary": "这是一个测试事件的概述。",
    "timeline": [
        {
            "id": "tl-1",
            "time": "2026-05-18T10:00:00+08:00",
            "title": "首次报道",
            "description": "媒体首次报道此事。",
            "evidenceRefs": ["ev-1"]
        }
    ],
    "evidence": [
        {
            "id": "ev-1",
            "sourceType": "官媒",
            "sourceName": "人民日报",
            "sourceUrl": "https://example.com/news/1",
            "content": "相关报道内容摘要。",
            "authenticity": "真实",
            "aiReason": "来源权威，多方交叉验证一致。"
        }
    ],
    "edges": [
        {
            "from": "tl-1",
            "to": "ev-1",
            "type": "关联",
            "description": "该报道为时间线节点的信息来源。"
        }
    ]
}

SAMPLE_ISSUE = {
    "id": "2026-W21",
    "weekStart": "2026-05-18",
    "weekEnd": "2026-05-24",
    "events": [SAMPLE_EVENT]
}


def test_event_validation():
    event = Event(**SAMPLE_EVENT)
    assert event.impactScore == 4
    assert event.timeline[0].title == "首次报道"
    assert event.evidence[0].authenticity == "真实"


def test_weekly_issue_validation():
    issue = WeeklyIssue(**SAMPLE_ISSUE)
    assert issue.id == "2026-W21"
    assert len(issue.events) == 1


def test_invalid_score_rejected():
    try:
        Event(**{**SAMPLE_EVENT, "impactScore": 6})
        assert False, "Should have raised ValidationError"
    except Exception:
        pass


def test_invalid_authenticity_rejected():
    try:
        bad_evidence = {**SAMPLE_EVENT["evidence"][0], "authenticity": "不确定"}
        bad_event = {**SAMPLE_EVENT, "evidence": [bad_evidence]}
        Event(**bad_event)
        assert False, "Should have raised ValidationError"
    except Exception:
        pass


def test_json_roundtrip():
    issue = WeeklyIssue(**SAMPLE_ISSUE)
    json_str = issue.model_dump_json(indent=2, ensure_ascii=False)
    parsed = WeeklyIssue(**json.loads(json_str))
    assert parsed.id == issue.id
    assert len(parsed.events) == 1
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd weekly-cli && python -m pytest test_schema.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'schema'`

- [ ] **Step 3: 实现 schema.py**

```python
from typing import Literal, Optional
from pydantic import BaseModel, Field


class TimelineNode(BaseModel):
    id: str
    time: str
    title: str
    description: str
    evidenceRefs: list[str] = Field(default_factory=list)


class EvidenceNode(BaseModel):
    id: str
    sourceType: Literal["官媒", "社交平台", "一手材料", "其他"]
    sourceName: str
    sourceUrl: Optional[str] = None
    content: str
    authenticity: Literal["真实", "存疑", "不实", "待验证"]
    aiReason: str


class Edge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    type: Literal["因果", "关联", "反驳"]
    description: str

    model_config = {"populate_by_name": True}


class Event(BaseModel):
    id: str
    title: str
    impactScore: int = Field(ge=1, le=5)
    infoGainScore: int = Field(ge=1, le=5)
    summary: str
    timeline: list[TimelineNode] = Field(default_factory=list)
    evidence: list[EvidenceNode] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)


class WeeklyIssue(BaseModel):
    id: str
    weekStart: str
    weekEnd: str
    events: list[Event] = Field(default_factory=list)
```

- [ ] **Step 4: Run tests — verify pass**

```bash
cd weekly-cli && python -m pytest test_schema.py -v
```
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add weekly-cli/schema.py weekly-cli/test_schema.py weekly-cli/requirements.txt weekly-cli/config.py
git commit -m "feat: add data models and project scaffold for weekly hotspot CLI"
```

---

### Task 3: DeepSeek API Client

**Files:**
- Create: `weekly-cli/client.py`
- Create: `weekly-cli/test_client.py`

- [ ] **Step 1: 编写 client test**

`test_client.py`:
```python
import os
import json
import pytest
from client import DeepSeekClient

@pytest.fixture
def client():
    api_key = os.environ.get("DEEPSEEK_API_KEY", "test-key")
    return DeepSeekClient(api_key)


def test_client_initialization(client):
    assert client.model == "deepseek-chat"
    assert client.base_url == "https://api.deepseek.com"


def test_chat_returns_valid_json():
    """Integration test — requires DEEPSEEK_API_KEY env var"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY not set")

    client = DeepSeekClient(api_key)
    result = client.chat_json([
        {"role": "system", "content": "你是一个JSON输出助手。请始终以有效的JSON格式回复。"},
        {"role": "user", "content": '返回 {"answer": 42}'}
    ])
    assert result["answer"] == 42
```

- [ ] **Step 2: Run test — fails on import**

```bash
cd weekly-cli && python -m pytest test_client.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'client'`

- [ ] **Step 3: 实现 client.py**

```python
import json
import re
from openai import OpenAI


class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-chat"):
        self.base_url = base_url
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat_json(self, messages: list[dict], temperature: float = 0.3, max_tokens: int = 8192) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()

        # 移除可能的 markdown 代码块包裹
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*\n", "", raw)
            raw = re.sub(r"\n```\s*$", "", raw)

        return json.loads(raw)
```

- [ ] **Step 4: Run unit test**

```bash
cd weekly-cli && python -m pytest test_client.py::test_client_initialization -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add weekly-cli/client.py weekly-cli/test_client.py
git commit -m "feat: add DeepSeek API client wrapper with JSON mode"
```

---

### Task 4: Phase 0 — 政审过滤

**Files:**
- Create: `weekly-cli/censor.py`
- Create: `weekly-cli/test_censor.py`

- [ ] **Step 1: 编写 censor test**

`test_censor.py`:
```python
import os
import pytest
from client import DeepSeekClient
from censor import censor_events


CENSOR_SYSTEM_PROMPT = """你是一个内容审核助手。请识别并排除以下类型的事件：
- 纯政治敏感话题
- 可能违反中国内容审查政策的事件
- 不适合在个人技术博客公开发表的内容
- 涉及领导人、领土主权、民族宗教等高度敏感领域

只返回通过审查的事件列表。不要解释审核原因。"""


@pytest.fixture
def client():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY not set")
    return DeepSeekClient(api_key)


def test_censor_filters_political(client):
    events = [
        {"title": "某地举行科技创新大赛", "summary": "当地举办了青少年科技创新比赛"},
        {"title": "某政治敏感事件", "summary": "涉及政治敏感内容"},
    ]
    result = censor_events(client, events)
    assert len(result) <= 2
    # 政治敏感事件应被过滤
    titles = [e["title"] for e in result]
    assert "某政治敏感事件" not in titles


def test_censor_preserves_normal_events(client):
    events = [
        {"title": "AI技术新突破", "summary": "某公司发布新一代大模型"},
        {"title": "世界杯预选赛结果", "summary": "中国队晋级下一轮"},
    ]
    result = censor_events(client, events)
    assert len(result) == 2
```

- [ ] **Step 2: Run test — fails on import**

```bash
cd weekly-cli && python -m pytest test_censor.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 censor.py**

```python
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
```

- [ ] **Step 4: Run test**

```bash
cd weekly-cli && python -m pytest test_censor.py -v
```
Expected: 2 PASS (requires DEEPSEEK_API_KEY)

- [ ] **Step 5: Commit**

```bash
git add weekly-cli/censor.py weekly-cli/test_censor.py
git commit -m "feat: add Phase 0 political review filter"
```

---

### Task 5: Phase 1 — 评分与筛选

**Files:**
- Create: `weekly-cli/scorer.py`
- Create: `weekly-cli/test_scorer.py`

- [ ] **Step 1: 编写 scorer test**

`test_scorer.py`:
```python
import os
import pytest
from client import DeepSeekClient
from scorer import score_and_select


@pytest.fixture
def client():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY not set")
    return DeepSeekClient(api_key)


def test_scorer_returns_top_events(client):
    events = [
        {"title": "事件A", "summary": "某科技公司发布革命性产品，影响全球供应链。"},
        {"title": "事件B", "summary": "某地天气变化。"},
        {"title": "事件C", "summary": "国际空间站发现新粒子，物理学界震动。"},
    ]
    result = score_and_select(client, events, top_n=2)
    assert len(result) == 2
    for e in result:
        assert "impactScore" in e
        assert "infoGainScore" in e
        assert 1 <= e["impactScore"] <= 5
        assert 1 <= e["infoGainScore"] <= 5


def test_scorer_respects_top_n(client):
    events = [
        {"title": f"事件{i}", "summary": f"描述{i}"} for i in range(10)
    ]
    result = score_and_select(client, events, top_n=5)
    assert len(result) <= 5
```

- [ ] **Step 2: Run test — fails**

```bash
cd weekly-cli && python -m pytest test_scorer.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 scorer.py**

```python
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
```

- [ ] **Step 4: Run test**

```bash
cd weekly-cli && python -m pytest test_scorer.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add weekly-cli/scorer.py weekly-cli/test_scorer.py
git commit -m "feat: add Phase 1 scoring and selection"
```

---

### Task 6: Phase 2 — 逐事件深度梳理

**Files:**
- Create: `weekly-cli/analyzer.py`
- Create: `weekly-cli/test_analyzer.py`

- [ ] **Step 1: 编写 analyzer test**

`test_analyzer.py`:
```python
import os
import pytest
from client import DeepSeekClient
from analyzer import analyze_event
from schema import Event


EVENT_INPUT = {
    "title": "AI大模型价格战",
    "summary": "多家科技公司大幅下调大模型API价格，引发行业震动。",
    "impactScore": 5,
    "infoGainScore": 4,
}


@pytest.fixture
def client():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY not set")
    return DeepSeekClient(api_key)


def test_analyze_event_returns_valid_structure(client):
    result = analyze_event(client, EVENT_INPUT)
    event = Event(**result)
    assert len(event.timeline) >= 3
    assert len(event.evidence) >= 2
    for e in event.evidence:
        assert e.authenticity in ("真实", "存疑", "不实", "待验证")
    for edge in event.edges:
        assert edge.type in ("因果", "关联", "反驳")


def test_analyze_event_timeline_has_dates(client):
    result = analyze_event(client, EVENT_INPUT)
    for node in result["timeline"]:
        assert "T" in node["time"]  # ISO datetime contains T
        assert len(node["title"]) > 0
```

- [ ] **Step 2: Run test — fails**

```bash
cd weekly-cli && python -m pytest test_analyzer.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 analyzer.py**

```python
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
```

- [ ] **Step 4: Run test**

```bash
cd weekly-cli && python -m pytest test_analyzer.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add weekly-cli/analyzer.py weekly-cli/test_analyzer.py
git commit -m "feat: add Phase 2 per-event deep analysis"
```

---

### Task 7: 编排器 & JSON 输出

**Files:**
- Create: `weekly-cli/main.py`

- [ ] **Step 1: 实现 main.py**

```python
import json
import sys
from datetime import datetime, timedelta
from config import DEEPSEEK_API_KEY, BLOG_CONTENT_DIR
from client import DeepSeekClient
from censor import censor_events
from scorer import score_and_select
from analyzer import analyze_event
from schema import WeeklyIssue


def get_week_id() -> str:
    today = datetime.now()
    iso = today.isocalendar()
    return f"{today.year}-W{iso.week:02d}"


def get_week_range() -> tuple[str, str]:
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


def fetch_weekly_hotspots(client: DeepSeekClient) -> list[dict]:
    """让 DeepSeek 联网搜索本周热点事件列表"""
    result = client.chat_json([
        {"role": "system", "content": "你是一个新闻聚合助手。请搜索并列出本周（过去7天内）的热点新闻事件。对每个事件提供标题和一句话摘要。重点关注科技、社会、经济、国际领域。返回至少20个事件。返回格式：{\"events\": [{\"title\": \"...\", \"summary\": \"...\"}]}"},
        {"role": "user", "content": "请列出本周的热点事件，至少20个。重点关注有实际影响的事件，排除纯娱乐八卦。"},
    ])
    return result.get("events", [])


def main():
    client = DeepSeekClient(DEEPSEEK_API_KEY)

    print("[Phase 0] 获取本周热点候选...")
    raw_events = fetch_weekly_hotspots(client)
    print(f"  获取到 {len(raw_events)} 个候选事件")

    print("[Phase 0] 政审过滤...")
    passed = censor_events(client, raw_events)
    print(f"  通过审查: {len(passed)} 个")

    print("[Phase 1] AI 评分筛选...")
    selected = score_and_select(client, passed, top_n=8)
    print(f"  入选: {len(selected)} 个")

    print("[Phase 2] 逐事件深度梳理...")
    analyzed_events = []
    for i, event in enumerate(selected):
        print(f"  分析 ({i+1}/{len(selected)}): {event['title']}")
        try:
            result = analyze_event(client, event, idx=i + 1)
            analyzed_events.append(result)
        except Exception as e:
            print(f"    分析失败: {e}，重试一次...")
            try:
                result = analyze_event(client, event, idx=i + 1)
                analyzed_events.append(result)
            except Exception as e2:
                print(f"    重试仍失败: {e2}，跳过此事件")

    week_id = get_week_id()
    week_start, week_end = get_week_range()

    issue = WeeklyIssue(
        id=week_id,
        weekStart=week_start,
        weekEnd=week_end,
        events=analyzed_events,
    )

    BLOG_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = BLOG_CONTENT_DIR / f"{week_id}.json"
    output_path.write_text(issue.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n输出: {output_path}")
    print(f"共 {len(analyzed_events)} 个事件")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 创建一个 sample JSON 用于前端开发**

`weekly-cli/sample_weekly.json`:
```json
{
  "id": "2026-W21",
  "weekStart": "2026-05-18",
  "weekEnd": "2026-05-24",
  "events": [
    {
      "id": "evt-1",
      "title": "AI大模型价格战全面爆发",
      "impactScore": 5,
      "infoGainScore": 4,
      "summary": "本周多家科技巨头宣布大幅下调大模型API调用价格，降幅最高达97%。字节跳动、阿里云、百度智能云相继跟进，标志着国内AI大模型从技术竞争转向价格竞争。此举将大幅降低AI应用开发门槛，但也引发了对中小模型厂商生存空间的担忧。",
      "timeline": [
        {
          "id": "tl-1-1",
          "time": "2026-05-15T10:00:00+08:00",
          "title": "字节豆包率先降价",
          "description": "字节跳动宣布豆包大模型API价格下调至每百万token 0.8元，降幅达97%。",
          "evidenceRefs": ["ev-1-1"]
        },
        {
          "id": "tl-1-2",
          "time": "2026-05-15T18:00:00+08:00",
          "title": "阿里云跟进出价",
          "description": "阿里云通义千问系列模型宣布降价，最高降幅达95%。",
          "evidenceRefs": ["ev-1-2"]
        },
        {
          "id": "tl-1-3",
          "time": "2026-05-16T09:00:00+08:00",
          "title": "百度文心加入战局",
          "description": "百度智能云宣布文心大模型API价格全面下调。",
          "evidenceRefs": ["ev-1-3"]
        },
        {
          "id": "tl-1-4",
          "time": "2026-05-17T14:00:00+08:00",
          "title": "行业分析师发布影响评估",
          "description": "多家研究机构发布报告，认为价格战将加速AI应用落地，但短期压缩行业利润。",
          "evidenceRefs": ["ev-1-4"]
        },
        {
          "id": "tl-1-5",
          "time": "2026-05-18T08:00:00+08:00",
          "title": "中小厂商回应生存担忧",
          "description": "多家AI创业公司表示将通过差异化策略应对价格战，专注垂直场景。",
          "evidenceRefs": ["ev-1-5"]
        }
      ],
      "evidence": [
        {
          "id": "ev-1-1",
          "sourceType": "官媒",
          "sourceName": "字节跳动官方公告",
          "sourceUrl": null,
          "content": "字节跳动宣布豆包大模型价格调整公告，pro-32k版本降至0.8元/百万token。",
          "authenticity": "真实",
          "aiReason": "官方公告，多家媒体交叉验证确认。"
        },
        {
          "id": "ev-1-2",
          "sourceType": "官媒",
          "sourceName": "阿里云官方公众号",
          "sourceUrl": null,
          "content": "阿里云宣布通义千问价格调整，Qwen-Long版本降至0.5元/百万token。",
          "authenticity": "真实",
          "aiReason": "官方渠道发布，价格数据可在官网查询。"
        },
        {
          "id": "ev-1-3",
          "sourceType": "社交平台",
          "sourceName": "微博@百度AI",
          "sourceUrl": null,
          "content": "百度智能云宣布文心大模型API价格下调，降幅最高90%。",
          "authenticity": "真实",
          "aiReason": "百度官方微博账号发布，与旗下产品页信息一致。"
        },
        {
          "id": "ev-1-4",
          "sourceType": "其他",
          "sourceName": "IDC中国",
          "sourceUrl": null,
          "content": "IDC报告指出价格战将推动2026年中国AI应用市场规模增长40%。",
          "authenticity": "存疑",
          "aiReason": "研究报告存在，但40%增长率是基于预测模型，实际数据待验证。"
        },
        {
          "id": "ev-1-5",
          "sourceType": "社交平台",
          "sourceName": "即刻App",
          "sourceUrl": null,
          "content": "多位AI创业者表示将通过垂直场景定制化避开价格战，聚焦金融、医疗等赛道。",
          "authenticity": "待验证",
          "aiReason": "社交媒体个人言论，缺乏正式声明或合同佐证。"
        }
      ],
      "edges": [
        {
          "from": "tl-1-1",
          "to": "tl-1-2",
          "type": "因果",
          "description": "字节率先降价触发阿里云在数小时内跟进。"
        },
        {
          "from": "tl-1-2",
          "to": "tl-1-3",
          "type": "因果",
          "description": "字节和阿里相继降价后，百度被迫加入价格战。"
        },
        {
          "from": "tl-1-3",
          "to": "tl-1-4",
          "type": "关联",
          "description": "三大厂商降价后，分析师开始评估行业影响。"
        },
        {
          "from": "tl-1-4",
          "to": "tl-1-5",
          "type": "关联",
          "description": "行业影响评估引发中小厂商的公开回应。"
        },
        {
          "from": "ev-1-5",
          "to": "tl-1-5",
          "type": "反驳",
          "description": "创业者声称的差异化策略尚缺乏实际业绩支撑，其可行性存疑。"
        }
      ]
    }
  ]
}
```

- [ ] **Step 3: Copy sample to blog for frontend dev**

```bash
cp weekly-cli/sample_weekly.json "C:\Users\DreamNight\Documents\01My\myBlog\src\content\weekly\2026-W21.json"
```

- [ ] **Step 4: Commit**

```bash
git add weekly-cli/main.py weekly-cli/sample_weekly.json
git commit -m "feat: add orchestrator and sample weekly data"
```

---

## Part B: Blog 前端

### Task 8: 注册 Content Collection

**Files:**
- Modify: `myBlog/src/content/config.ts`

- [ ] **Step 1: 添加 weekly collection schema**

在 `config.ts` 中添加（在 `friendsCollection` 定义之后，`export const collections` 之前）：

```typescript
const weeklyCollection = defineCollection({
  type: 'data',
  schema: z.object({
    id: z.string(),
    weekStart: z.string(),
    weekEnd: z.string(),
    events: z.array(z.object({
      id: z.string(),
      title: z.string(),
      impactScore: z.number().min(1).max(5),
      infoGainScore: z.number().min(1).max(5),
      summary: z.string(),
      timeline: z.array(z.object({
        id: z.string(),
        time: z.string(),
        title: z.string(),
        description: z.string(),
        evidenceRefs: z.array(z.string()),
      })),
      evidence: z.array(z.object({
        id: z.string(),
        sourceType: z.enum(["官媒", "社交平台", "一手材料", "其他"]),
        sourceName: z.string(),
        sourceUrl: z.string().nullable(),
        content: z.string(),
        authenticity: z.enum(["真实", "存疑", "不实", "待验证"]),
        aiReason: z.string(),
      })),
      edges: z.array(z.object({
        from: z.string(),
        to: z.string(),
        type: z.enum(["因果", "关联", "反驳"]),
        description: z.string(),
      })),
    })),
  }),
})
```

然后更新 `export const collections`：

```typescript
export const collections = {
  posts: postsCollection,
  projects: projectsCollection,
  spec: specCollection,
  friends: friendsCollection,
  weekly: weeklyCollection,
}
```

- [ ] **Step 2: 验证 Astro 类型检查**

```bash
cd C:\Users\DreamNight\Documents\01My\myBlog && npx astro check
```
Expected: No type errors

- [ ] **Step 3: Commit**

```bash
git add src/content/config.ts src/content/weekly/2026-W21.json
git commit -m "feat: add weekly content collection"
```

---

### Task 9: 列表页 `/weekly/`

**Files:**
- Create: `myBlog/src/pages/weekly/index.astro`

- [ ] **Step 1: 创建列表页**

```astro
---
import { getCollection } from 'astro:content'
import PageLayout from '@/layouts/PageLayout.astro'

const issues = await getCollection('weekly')
issues.sort((a, b) => b.data.weekStart.localeCompare(a.data.weekStart))
---

<PageLayout title="每周热点 · 深度梳理" description="AI驱动的热点事件分析与证据链梳理">
  <div class="max-w-3xl mx-auto px-4 py-12">
    <header class="mb-12">
      <h1 class="text-2xl font-bold tracking-wide text-[var(--text-primary)]">
        每周热点 · 深度梳理
      </h1>
      <p class="mt-2 text-sm text-[var(--text-secondary)] tracking-wide">
        AI 筛选有价值的热点事件，梳理时间线、证据链与关系网。
      </p>
    </header>

    <div class="grid gap-6">
      {
        issues.map((issue) => (
          <a
            href={`/weekly/${issue.data.id}`}
            class="block p-6 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
          >
            <div class="flex items-baseline justify-between">
              <h2 class="text-lg font-semibold text-[var(--text-primary)]">
                {issue.data.id.replace('W', ' 第 ')} 周
              </h2>
              <span class="text-xs text-[var(--text-secondary)] font-mono tabular-nums">
                {issue.data.weekStart} — {issue.data.weekEnd}
              </span>
            </div>
            <p class="mt-2 text-sm text-[var(--text-secondary)]">
              {issue.data.events.length} 个事件 · {
                issue.data.events.reduce((sum, e) => sum + e.timeline.length, 0)
              } 个时间节点 · {
                issue.data.events.reduce((sum, e) => sum + e.evidence.length, 0)
              } 条证据
            </p>
          </a>
        ))
      }
    </div>
  </div>
</PageLayout>
```

- [ ] **Step 2: 验证构建**

```bash
cd C:\Users\DreamNight\Documents\01My\myBlog && npx astro build
```
Expected: 构建成功，`/weekly/` 页面可访问

- [ ] **Step 3: Commit**

```bash
git add src/pages/weekly/index.astro
git commit -m "feat: add weekly list page"
```

---

### Task 10: 详情页 `/weekly/[id]`

**Files:**
- Create: `myBlog/src/pages/weekly/[id].astro`

- [ ] **Step 1: 创建详情页**

```astro
---
import { getCollection } from 'astro:content'
import PageLayout from '@/layouts/PageLayout.astro'
import EventCard from '@/components/weekly/EventCard'

export async function getStaticPaths() {
  const issues = await getCollection('weekly')
  return issues.map((issue) => ({
    params: { id: issue.data.id },
    props: { issue: issue.data },
  }))
}

const { id } = Astro.params
const { issue } = Astro.props
---

<PageLayout title={`${id} · 每周热点`} description={`${id} 热点事件深度梳理`}>
  <div class="max-w-4xl mx-auto px-4 py-12">
    <header class="mb-10">
      <p class="text-xs text-[var(--text-secondary)] font-mono tabular-nums tracking-wide">
        {issue.weekStart} — {issue.weekEnd}
      </p>
      <h1 class="mt-1 text-2xl font-bold tracking-wider text-[var(--text-primary)]">
        本周深度 · {issue.id.replace('W', ' 第 ')} 周
      </h1>
      <p class="mt-2 text-sm text-[var(--text-secondary)]">
        {issue.events.length} 个精选事件
      </p>
    </header>

    <div class="space-y-12">
      {issue.events.map((event, i) => (
        <EventCard event={event} index={i} client:load />
      ))}
    </div>
  </div>
</PageLayout>
```

- [ ] **Step 2: 验证构建**

```bash
cd C:\Users\DreamNight\Documents\01My\myBlog && npx astro build
```
Expected: 构建成功，`/weekly/2026-W21/` 页面生成

- [ ] **Step 3: Commit** (先暂存，等 Task 11-14 组件实现后一起验证)

---

### Task 11: ScoreBadge 组件

**Files:**
- Create: `myBlog/src/components/weekly/ScoreBadge.tsx`

- [ ] **Step 1: 创建 ScoreBadge**

```tsx
interface ScoreBadgeProps {
  label: string
  score: number
}

export default function ScoreBadge({ label, score }: ScoreBadgeProps) {
  const pct = (score / 5) * 100

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-[var(--text-secondary)] tracking-wide uppercase">
        {label}
      </span>
      <span className="text-sm font-bold tabular-nums text-[var(--text-primary)]">
        {score.toFixed(1)}
      </span>
      <div className="w-12 h-1 rounded-full bg-[var(--border-primary)] overflow-hidden">
        <div
          className="h-full rounded-full bg-[var(--accent)] transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit** (随 EventCard 一起)

---

### Task 12: TimelineView 组件

**Files:**
- Create: `myBlog/src/components/weekly/TimelineView.tsx`

- [ ] **Step 1: 创建 TimelineView**

```tsx
import { useState } from 'react'

interface TimelineNode {
  id: string
  time: string
  title: string
  description: string
  evidenceRefs: string[]
}

interface Props {
  nodes: TimelineNode[]
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

function hasEvidence(node: TimelineNode): boolean {
  return node.evidenceRefs.length > 0
}

export default function TimelineView({ nodes }: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  const toggle = (id: string) => {
    const next = new Set(expanded)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setExpanded(next)
  }

  const sorted = [...nodes].sort((a, b) => a.time.localeCompare(b.time))

  return (
    <div className="relative pl-6">
      <div className="absolute left-[7px] top-2 bottom-2 w-px bg-[var(--border-primary)]" />

      <div className="space-y-0">
        {sorted.map((node, i) => {
          const isOpen = expanded.has(node.id)
          const isFirst = i === 0
          return (
            <div key={node.id} className="relative pb-5 last:pb-0">
              <span
                className={`absolute left-[-20px] top-1.5 w-[15px] h-[15px] rounded-full border-2 border-[var(--border-primary)] bg-[var(--bg-primary)] ${
                  isFirst ? 'ring-2 ring-[var(--accent)] border-[var(--accent)]' : ''
                } ${hasEvidence(node) ? '' : 'bg-[var(--bg-secondary)]'}`}
              />

              <button
                onClick={() => toggle(node.id)}
                className="w-full text-left group"
              >
                <time className="text-xs font-mono tabular-nums text-[var(--text-secondary)] tracking-tight">
                  {formatTime(node.time)}
                </time>
                <h5 className="mt-0.5 text-sm font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent)] transition-colors">
                  {node.title}
                </h5>
              </button>

              {isOpen && (
                <div className="mt-2 ml-0 text-sm text-[var(--text-secondary)] leading-relaxed">
                  {node.description}
                  {node.evidenceRefs.length > 0 && (
                    <span className="ml-2 text-xs text-[var(--accent)] font-mono tabular-nums">
                      [{node.evidenceRefs.length} 条证据]
                    </span>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit** (随 EventCard 一起)

---

### Task 13: GraphView 组件

**Files:**
- Create: `myBlog/src/components/weekly/GraphView.tsx`

- [ ] **Step 1: 安装 react-force-graph-2d**

```bash
cd C:\Users\DreamNight\Documents\01My\myBlog && pnpm add react-force-graph-2d
```

- [ ] **Step 2: 创建 GraphView**

```tsx
import { useMemo } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import type { TimelineNode, EvidenceNode, Edge } from './EventCard'

interface GraphNode {
  id: string
  label: string
  group: 'timeline' | 'evidence'
  nodeData: TimelineNode | EvidenceNode
}

interface GraphLink {
  source: string
  target: string
  type: string
  description: string
}

interface Props {
  timeline: TimelineNode[]
  evidence: EvidenceNode[]
  edges: Edge[]
}

const EDGE_COLORS: Record<string, string> = {
  '因果': '#ef4444',
  '关联': '#6b7280',
  '反驳': '#f59e0b',
}

const EDGE_DASH: Record<string, number[]> = {
  '因果': [],
  '关联': [4, 4],
  '反驳': [2, 2],
}

const AUTH_COLORS: Record<string, string> = {
  '真实': '#22c55e',
  '存疑': '#eab308',
  '不实': '#ef4444',
  '待验证': '#9ca3af',
}

export default function GraphView({ timeline, evidence, edges }: Props) {
  const { nodes, links } = useMemo(() => {
    const nodes: GraphNode[] = [
      ...timeline.map((t) => ({
        id: t.id,
        label: t.title,
        group: 'timeline' as const,
        nodeData: t,
      })),
      ...evidence.map((e) => ({
        id: e.id,
        label: e.sourceName,
        group: 'evidence' as const,
        nodeData: e,
      })),
    ]

    const links: GraphLink[] = edges.map((e) => ({
      source: e.from,
      target: e.to,
      type: e.type,
      description: e.description,
    }))

    return { nodes, links }
  }, [timeline, evidence, edges])

  const width = typeof window !== 'undefined' ? Math.min(window.innerWidth - 64, 800) : 800

  return (
    <div className="border border-[var(--border-primary)] rounded-lg overflow-hidden bg-[var(--bg-secondary)]">
      <ForceGraph2D
        graphData={{ nodes, links }}
        width={width}
        height={500}
        nodeLabel={(n: GraphNode) => n.label}
        nodeColor={(n: GraphNode) =>
          n.group === 'evidence'
            ? AUTH_COLORS[(n.nodeData as EvidenceNode).authenticity] || '#9ca3af'
            : 'var(--accent)'
        }
        nodeRelSize={6}
        linkColor={(l: GraphLink) => EDGE_COLORS[l.type] || '#6b7280'}
        linkLineDash={(l: GraphLink) => EDGE_DASH[l.type] || []}
        linkDirectionalArrowLength={6}
        linkDirectionalArrowRelPos={1}
        linkLabel={(l: GraphLink) => `${l.type} · ${l.description}`}
        backgroundColor="transparent"
        linkWidth={1.5}
      />
    </div>
  )
}
```

- [ ] **Step 3: Commit** (随 EventCard 一起)

---

### Task 14: EvidenceView 组件

**Files:**
- Create: `myBlog/src/components/weekly/EvidenceView.tsx`

- [ ] **Step 1: 创建 EvidenceView**

```tsx
import type { EvidenceNode } from './EventCard'

interface Props {
  evidence: EvidenceNode[]
}

const AUTH_STYLES: Record<string, string> = {
  '真实': 'border-emerald-500/40 bg-emerald-50 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-950/30 dark:text-emerald-400',
  '存疑': 'border-amber-500/40 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-950/30 dark:text-amber-400',
  '不实': 'border-red-500/40 bg-red-50 text-red-800 dark:border-red-500/30 dark:bg-red-950/30 dark:text-red-400',
  '待验证': 'border-dashed border-gray-400/40 bg-gray-50 text-gray-600 dark:border-gray-500/30 dark:bg-gray-950/30 dark:text-gray-400',
}

export default function EvidenceView({ evidence }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[var(--border-primary)] text-left">
            <th className="py-2 pr-4 text-xs font-medium text-[var(--text-secondary)] tracking-wide w-16">
              判定
            </th>
            <th className="py-2 pr-4 text-xs font-medium text-[var(--text-secondary)] tracking-wide w-16">
              来源类型
            </th>
            <th className="py-2 pr-4 text-xs font-medium text-[var(--text-secondary)] tracking-wide">
              来源
            </th>
            <th className="py-2 text-xs font-medium text-[var(--text-secondary)] tracking-wide">
              内容
            </th>
          </tr>
        </thead>
        <tbody>
          {evidence.map((e) => (
            <tr key={e.id} className="border-b border-[var(--border-primary)] last:border-0">
              <td className="py-3 pr-4">
                <span className={`inline-block px-2 py-0.5 text-xs rounded border ${AUTH_STYLES[e.authenticity]}`}>
                  {e.authenticity}
                </span>
              </td>
              <td className="py-3 pr-4 text-xs text-[var(--text-secondary)] tabular-nums">
                {e.sourceType}
              </td>
              <td className="py-3 pr-4">
                <div className="text-xs font-medium text-[var(--text-primary)]">
                  {e.sourceName}
                </div>
                <div className="mt-0.5 text-xs text-[var(--text-secondary)] leading-relaxed max-w-xs">
                  {e.aiReason}
                </div>
              </td>
              <td className="py-3 text-xs text-[var(--text-primary)] leading-relaxed">
                {e.content}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 2: Commit** (随 EventCard 一起)

---

### Task 15: EventCard 组件（整合）

**Files:**
- Create: `myBlog/src/components/weekly/EventCard.tsx`

- [ ] **Step 1: 创建 EventCard 类型定义和组件**

```tsx
import { useState } from 'react'
import ScoreBadge from './ScoreBadge'
import TimelineView from './TimelineView'
import GraphView from './GraphView'
import EvidenceView from './EvidenceView'

export interface TimelineNode {
  id: string
  time: string
  title: string
  description: string
  evidenceRefs: string[]
}

export interface EvidenceNode {
  id: string
  sourceType: '官媒' | '社交平台' | '一手材料' | '其他'
  sourceName: string
  sourceUrl: string | null
  content: string
  authenticity: '真实' | '存疑' | '不实' | '待验证'
  aiReason: string
}

export interface Edge {
  from: string
  to: string
  type: '因果' | '关联' | '反驳'
  description: string
}

interface Event {
  id: string
  title: string
  impactScore: number
  infoGainScore: number
  summary: string
  timeline: TimelineNode[]
  evidence: EvidenceNode[]
  edges: Edge[]
}

interface Props {
  event: Event
  index: number
}

type Tab = 'timeline' | 'graph' | 'evidence'

const TAB_LABELS: Record<Tab, string> = {
  timeline: '时间线',
  graph: '关系网',
  evidence: '证据',
}

export default function EventCard({ event, index }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('timeline')

  return (
    <section className="border border-[var(--border-primary)] rounded-lg bg-[var(--bg-primary)]">
      <div className="p-6 pb-4">
        <div className="flex items-start justify-between gap-6">
          <div className="flex-1">
            <span className="text-xs text-[var(--text-secondary)] font-mono tabular-nums tracking-wide">
              # {index + 1}
            </span>
            <h2 className="mt-1 text-lg font-bold text-[var(--text-primary)] tracking-wide">
              {event.title}
            </h2>
          </div>
          <div className="flex gap-5 shrink-0">
            <ScoreBadge label="影响" score={event.impactScore} />
            <ScoreBadge label="增量" score={event.infoGainScore} />
          </div>
        </div>

        <p className="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed">
          {event.summary}
        </p>

        <div className="mt-4 flex gap-1 border-b border-[var(--border-primary)]">
          {(Object.keys(TAB_LABELS) as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-2 text-xs tracking-wide transition-colors border-b-2 -mb-px ${
                activeTab === tab
                  ? 'border-[var(--accent)] text-[var(--accent)] font-semibold'
                  : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
            >
              {TAB_LABELS[tab]}
              {tab === 'timeline' && (
                <span className="ml-1 text-[10px] tabular-nums">({event.timeline.length})</span>
              )}
              {tab === 'evidence' && (
                <span className="ml-1 text-[10px] tabular-nums">({event.evidence.length})</span>
              )}
              {tab === 'graph' && (
                <span className="ml-1 text-[10px] tabular-nums">({event.edges.length})</span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6 pt-4">
        {activeTab === 'timeline' && <TimelineView nodes={event.timeline} />}
        {activeTab === 'graph' && (
          <GraphView
            timeline={event.timeline}
            evidence={event.evidence}
            edges={event.edges}
          />
        )}
        {activeTab === 'evidence' && <EvidenceView evidence={event.evidence} />}
      </div>
    </section>
  )
}
```

- [ ] **Step 2: 更新 [id].astro 使用 client:load**

确认 `myBlog/src/pages/weekly/[id].astro` 中 EventCard 使用 `client:load`（Task 10 已设置）

- [ ] **Step 3: 验证完整构建**

```bash
cd C:\Users\DreamNight\Documents\01My\myBlog && npx astro check && npx astro build
```
Expected: 类型检查通过，构建成功

- [ ] **Step 4: 启动 dev server 验证**

```bash
cd C:\Users\DreamNight\Documents\01My\myBlog && npx astro dev
```
访问 `http://localhost:4321/weekly/` 和 `http://localhost:4321/weekly/2026-W21`

- [ ] **Step 5: Commit**

```bash
git add src/components/weekly/ src/pages/weekly/
git commit -m "feat: add weekly detail page with timeline, graph, and evidence views"
```

---

### Task 16: 导航入口

**Files:**
- Modify: `myBlog/src/config.json`

- [ ] **Step 1: 在 blog 导航菜单中添加入口**

```json
{
  "name": "热点",
  "link": "/weekly",
  "icon": "icon-compass"
}
```

插入到 menus 数组中合适位置。

- [ ] **Step 2: Commit**

```bash
git add src/config.json
git commit -m "feat: add weekly hotspot nav entry"
```

---

### Task 17: CLI 集成脚本（可选便利脚本）

**Files:**
- Create: `myBlog/scripts/generate-weekly.sh`

- [ ] **Step 1: 创建快捷运行脚本**

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLI_DIR="$SCRIPT_DIR/../../funny/weekly-cli"
BLOG_DIR="$SCRIPT_DIR/.."

export BLOG_CONTENT_DIR="$BLOG_DIR/src/content/weekly"
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"

if [ -z "$DEEPSEEK_API_KEY" ]; then
  echo "Error: DEEPSEEK_API_KEY is not set"
  exit 1
fi

cd "$CLI_DIR"
python main.py

echo "Done. Run 'pnpm build' to deploy."
```

无需 commit，纯本地便利脚本。

---

## Self-Review Summary

**Spec coverage:**
- AI Pipeline 三阶段 → Tasks 4, 5, 6
- 编排器 + JSON 输出 → Task 7
- Content collection → Task 8
- 列表页 → Task 9
- 详情页 → Task 10
- ScoreBadge → Task 11
- TimelineView → Task 12
- GraphView → Task 13
- EvidenceView → Task 14
- EventCard + Tab 切换 → Task 15
- 导航入口 → Task 16

**Placeholder check:** 无占位符，全部完成代码填充。

**Type consistency:**
- `Edge` 在 schema.py 中使用 `from_`/`alias="from"` 处理保留字，在 GraphView 中使用 `edge.from`/`edge.to` — 一致
- Event/timeline/evidence 类型在组件 TypeScript 和 Python Pydantic 中字段名一致
- `authenticity` 枚举值：Python `Literal["真实", "存疑", "不实", "待验证"]` → TS 同
- `sourceType` 枚举：Python `Literal["官媒", "社交平台", "一手材料", "其他"]` → TS 同
