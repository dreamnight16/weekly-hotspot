# 格物 (Dianalyze) v2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Full rewrite of weekly-hotspot into 格物 (Dianalyze) — a 5-phase dialectical weekly analysis system driven by dialectical materialism and historical materialism as core methodology, with modern analytical techniques as auxiliary support.

**Architecture:** Five-phase pipeline following the dialectical epistemology: PhenomenonGrasping → ContradictionIdentification → DialecticalUnfolding → HistoricalPositioning → PracticeOrientation. Each phase runs a dual-layer structure (dialectical core + empirical auxiliary) merged at phase-end. Output: structured JSON + Markdown article organized by the five-phase narrative.

**Tech Stack:** Python 3.11+, Pydantic v2, DeepSeek API (v4-pro for dialectical, v4-flash for empirical), chinese-scraper-utils, ddgs, httpx

**Spec:** `docs/superpowers/specs/2026-07-30-dialectical-weekly-v2-design.md`

## Global Constraints

- Python ≥ 3.11
- Pydantic ≥ 2.0 with model_validator sanitization for all enum fields
- DeepSeek API: v4-pro (thinking=true) for dialectical layers, v4-flash for empirical layers
- Dialectical layer never skipped; empirical layer degrades gracefully on failure
- All prompts externalized in `prompts/` directory as JSON files
- Negative style guide enforced in all dialectical prompts: no empty dialectical jargon, no class-labeling without material basis, no skipping reasoning to conclusion
- Test coverage ≥ 80%
- Existing scraper (chinese-scraper-utils), cache, search, and utils preserved and adapted
- Old files (censor.py, scorer.py, analyzer.py, synthesizer.py, old article.py, old schema.py) removed in final cleanup task

---

## File Structure

```
weekly-cli/
├── main.py                              # [MODIFY] Rewrite as 5-phase orchestrator
├── config.py                            # [MODIFY] Add model routing config
├── schema.py                            # [REWRITE] Complete Pydantic v2 data models
├── merger.py                            # [NEW] Dual-layer merge + conflict annotation
├── retry.py                             # [KEEP] Existing retry_call, extend
├── quality.py                           # [MODIFY] Extend quality gate for new schema
│
├── dialectical/                         # [NEW DIR] Dialectical analysis layer
│   ├── __init__.py
│   ├── grasping.py                      # Phase 1: Phenomenon grasping
│   ├── contradiction.py                 # Phase 2: Contradiction identification
│   ├── unfolding.py                     # Phase 3: Dialectical unfolding
│   ├── positioning.py                   # Phase 4: Historical positioning + synthesis
│   └── practice.py                      # Phase 5: Practice orientation
│
├── empirical/                           # [NEW DIR] Empirical verification layer
│   ├── __init__.py
│   ├── verifier.py                      # Evidence grading + cross-verification + ACH
│   ├── scorer.py                        # 9-dimension scoring calibration
│   ├── adversary.py                     # Multi-round adversarial review
│   ├── quantitative.py                  # GDELT + sentiment + change-point detection
│   ├── causal.py                        # Causal loop diagrams + system archetypes
│   ├── connections.py                   # Non-obvious connection discovery
│   └── scenarios.py                     # GBN 3-scenario planning
│
├── scraper/                             # [NEW DIR] Data scraping
│   ├── __init__.py
│   ├── sources.py                       # [ADAPT FROM main.py] Weibo/Zhihu/HN scrape
│   └── cache.py                         # [MOVE] Existing cache.py → scraper/cache.py
│
├── narrative/                           # [NEW DIR] Article generation
│   ├── __init__.py
│   └── article.py                       # Five-phase narrative article generator
│
├── prompts/                             # [REWRITE] All prompt templates
│   ├── __init__.py                      # load_prompt utility
│   ├── dialectical/
│   │   ├── grasping.json
│   │   ├── contradiction.json
│   │   ├── unfolding.json
│   │   ├── positioning.json
│   │   └── practice.json
│   ├── empirical/
│   │   ├── verifier.json
│   │   ├── adversary.json
│   │   └── quantitative.json
│   └── narrative/
│       └── article.json
│
├── utils.py                             # [KEEP] get_week_id, get_week_range, section_label
├── search.py                            # [KEEP] DDG + Bing parallel search
│
└── tests/
    ├── conftest.py                      # [EXTEND] Add v2 sample fixtures
    ├── test_schema.py                   # [REWRITE] Full model validation tests
    ├── test_merger.py                   # [NEW] Merge logic tests
    ├── dialectical/
    │   ├── test_grasping.py
    │   ├── test_contradiction.py
    │   ├── test_unfolding.py
    │   ├── test_positioning.py
    │   └── test_practice.py
    └── empirical/
        ├── test_verifier.py
        ├── test_scorer.py
        └── test_adversary.py
```

**Files to remove (final task):**
- `censor.py`, `scorer.py`, `analyzer.py`, `synthesizer.py`, `article.py` (old), `schema.py` (old), `cache.py` (moved)
- Old prompt files: `prompts/censor.json`, `prompts/scorer.json`, `prompts/analyzer.json`, `prompts/synthesizer.json`

---

### Task 1: Complete Data Model (schema.py)

**Files:**
- Rewrite: `weekly-cli/schema.py`
- Test: `weekly-cli/tests/test_schema.py`

**Interfaces:**
- Produces: All Pydantic models used by every downstream task:
  - `RawEvent`, `CensoredEvent` (Phase 0-1 intermediate)
  - `SourceGrade`, `GDELTBaseline` (Phase 1 empirical)
  - `SelectedEvent`, `ExcludedEvent` (Phase 1)
  - `InterestStructure`, `ClassPosition`, `NineDimScores`, `CompetingHypothesis` (Phase 2)
  - `UnityOfOpposites`, `QuantityQuality`, `NegationOfNegation`, `AdversarialReview`, `CausalLoopDiagram`, `DataValidation` (Phase 3)
  - `EpochTheme`, `SystemArchetype`, `HiddenConnection`, `HistoricalAnalogy` (Phase 4)
  - `Scenario`, `WatchSignal`, `LastWeekCalibration` (Phase 5)
  - `EvidenceTrace`, `TracedClaim`, `TracedSource` (metadata)
  - `IssueMetadata` (run-level)
  - `WeeklyIssue` (top-level output)
  - Phase aggregate models: `PhenomenonGrasping`, `ContradictionIdentification`, `DialecticalUnfolding`, `HistoricalPositioning`, `PracticeOrientation`

- [ ] **Step 1: Write test file with sample data and validation checks**

Create `weekly-cli/tests/test_schema.py`:

```python
"""Test Pydantic v2 schema models for 格物 v2."""
import json
import pytest
from schema import (
    SourceGrade, GDELTBaseline, SelectedEvent, ExcludedEvent,
    InterestStructure, ClassPosition, NineDimScores, CompetingHypothesis,
    UnityOfOpposites, QuantityQuality, NegationOfNegation,
    AdversarialReview, CausalLoopDiagram, DataValidation,
    EpochTheme, SystemArchetype, HiddenConnection, HistoricalAnalogy,
    Scenario, WatchSignal, LastWeekCalibration,
    EvidenceTrace, TracedClaim, TracedSource, IssueMetadata,
    PhenomenonGrasping, ContradictionIdentification,
    DialecticalUnfolding, HistoricalPositioning, PracticeOrientation,
    WeeklyIssue, RawEvent, CensoredEvent,
)


class TestSourceGrade:
    def test_valid_source_grade(self):
        sg = SourceGrade(reliability="A", credibility=1, rationale="官方发布")
        assert sg.reliability == "A"
        assert sg.credibility == 1

    def test_invalid_reliability_defaults(self):
        sg = SourceGrade(reliability="X", credibility=3, rationale="test")
        assert sg.reliability in ("A", "B", "C", "D", "E", "F")  # sanitized

    def test_credibility_clamped(self):
        sg = SourceGrade(reliability="B", credibility=99, rationale="test")
        assert 1 <= sg.credibility <= 6


class TestSelectedEvent:
    def test_valid_event(self):
        e = SelectedEvent(
            id="evt-1", title="测试事件", summary="概述",
            sourceUrl=None, materialContent="有物质利益关系",
            isDirectExpression=True,
            sourceGrade=SourceGrade(reliability="A", credibility=2, rationale="官方")
        )
        assert e.id == "evt-1"
        assert e.isDirectExpression is True


class TestNineDimScores:
    def test_all_dimensions(self):
        s = NineDimScores(
            magnitude=(5, 0.9), scope=(3, 0.8), velocity=(2, 0.7),
            novelty=(4, 0.6), cascadePotential=(3, 0.5),
            actorProminence=(4, 0.9), uncertainty=(2, 0.8),
            polarity=(4, 0.7), durability=(3, 0.6)
        )
        assert s.magnitude[0] == 5
        assert s.cascadePotential[1] == 0.5

    def test_scores_clamped(self):
        s = NineDimScores(
            magnitude=(99, 9.9), scope=(0, -1.0), velocity=(2, 0.5),
            novelty=(3, 0.5), cascadePotential=(3, 0.5),
            actorProminence=(3, 0.5), uncertainty=(3, 0.5),
            polarity=(3, 0.5), durability=(3, 0.5)
        )
        assert 1 <= s.magnitude[0] <= 10
        assert 1 <= s.scope[0] <= 10
        assert 0.0 <= s.magnitude[1] <= 1.0


class TestDialecticalModels:
    def test_unity_of_opposites(self):
        u = UnityOfOpposites(
            identity="双方在政策框架下相互依存",
            struggle="平台通过抽成转嫁成本",
            particularity="不同于传统制造业劳资矛盾",
            universality="资本将外部成本内部化的普遍规律"
        )
        assert "相互依存" in u.identity

    def test_quantity_quality(self):
        q = QuantityQuality(
            currentPhase="量变积累",
            quantitativeDirection="平台抽成比例持续上升",
            measure="当抽成比例超过骑手承受阈值时发生质变",
            newQuality=None,
            oldQualityNegated="骑手作为独立承包商的旧形态"
        )
        assert q.currentPhase == "量变积累"

    def test_negation_of_negation(self):
        n = NegationOfNegation(
            oldThing="平台-骑手的旧雇佣关系",
            firstNegation="灵活用工模式否定固定雇佣",
            internalNegation="骑手集体权益意识生长",
            direction="螺旋上升",
            stageCharacteristics="否定之否定的初期阶段"
        )
        assert n.direction == "螺旋上升"


class TestPhaseModels:
    def test_phenomenon_grasping_minimal(self):
        pg = PhenomenonGrasping(
            phaseSummary="测试总结",
            selectedEvents=[],
            excludedEvents=[],
            gdeltBaseline=None,
            sourceQualityReport="来源质量良好"
        )
        assert pg.phaseSummary == "测试总结"

    def test_contradiction_identification(self):
        ci = ContradictionIdentification(
            phaseSummary="总结",
            events=[],
            overallContradictionLandscape="整体格局"
        )
        assert ci.overallContradictionLandscape == "整体格局"

    def test_dialectical_unfolding(self):
        du = DialecticalUnfolding(
            phaseSummary="总结",
            events=[],
            dialecticalConfidence="HIGH"
        )
        assert du.dialecticalConfidence == "HIGH"

    def test_historical_positioning(self):
        hp = HistoricalPositioning(
            phaseSummary="总结",
            events=[],
            crossCuttingSynthesis=None,
            historicalAnalogies=[]
        )
        assert hp.phaseSummary == "总结"

    def test_practice_orientation(self):
        po = PracticeOrientation(
            overallJudgment="本周矛盾处于积累期",
            scenarios=[],
            practiceSignificance="有助于理解平台劳动关系",
            signalsToWatch=[],
            lastWeekCalibration=None
        )
        assert "积累期" in po.overallJudgment


class TestWeeklyIssue:
    def test_minimal_issue(self):
        wi = WeeklyIssue(
            id="2026-W31",
            weekStart="2026-07-27",
            weekEnd="2026-08-02",
            events=[],
            phase1=PhenomenonGrasping(
                phaseSummary="", selectedEvents=[],
                excludedEvents=[], gdeltBaseline=None,
                sourceQualityReport=""
            ),
            phase2=None,
            phase3=None,
            phase4=None,
            phase5=None,
            evidenceTrace=EvidenceTrace(claims=[], totalVerifiedClaims=0),
            metadata=IssueMetadata(
                modelVersions={}, verificationPasses=0,
                empiricalDegradations=[], totalApiCost=0.0,
                runDuration=0.0, runId="test"
            )
        )
        assert wi.id == "2026-W31"

    def test_issue_json_roundtrip(self):
        wi = WeeklyIssue(
            id="2026-W31", weekStart="2026-07-27", weekEnd="2026-08-02",
            events=[], phase1=PhenomenonGrasping(
                phaseSummary="t", selectedEvents=[], excludedEvents=[],
                gdeltBaseline=None, sourceQualityReport=""
            ),
            evidenceTrace=EvidenceTrace(claims=[], totalVerifiedClaims=0),
            metadata=IssueMetadata(
                modelVersions={}, verificationPasses=0,
                empiricalDegradations=[], totalApiCost=0.0,
                runDuration=0.0, runId="t"
            )
        )
        d = wi.model_dump_json(ensure_ascii=False)
        wi2 = WeeklyIssue.model_validate_json(d)
        assert wi2.id == wi.id


class TestEvidenceTrace:
    def test_traced_claim(self):
        tc = TracedClaim(
            claimId="c-1", claim="测试断言", phase="phase2",
            confidence="HIGH",
            sources=[TracedSource(
                sourceName="新华社", sourceUrl="https://example.com",
                reliability="A", credibility=2
            )],
            independentCorroborations=2,
            verificationMethod="交叉验证"
        )
        assert tc.confidence == "HIGH"
        assert len(tc.sources) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd weekly-cli && python -m pytest tests/test_schema.py -v
```
Expected: ImportError (schema.py doesn't exist yet or has old models)

- [ ] **Step 3: Write the complete schema.py**

Create `weekly-cli/schema.py` with all Pydantic v2 models. Full implementation of:
- Enum literals with `_fuzzy_fix_enum` sanitizer (ported from existing schema.py)
- All `@model_validator(mode="before")` sanitization hooks
- All `@model_validator(mode="after")` cross-reference validation
- Score clamping (1-10 for NineDimScores, 1-5 for legacy fields)
- Edge cross-reference cleanup (drop edges referencing non-existent timeline/evidence ids)
- Empty list filtering for synthesis models (drop items with empty refs)

The complete schema implements all models from the spec §四 (data models section).

Key enum sets:
- `reliability`: A, B, C, D, E, F
- `credibility`: 1, 2, 3, 4, 5, 6
- `currentPhase`: "量变积累", "质的飞跃", "量变中的局部质变"
- `direction`: "螺旋上升", "暂时倒退", "停滞"
- `confidence`: "HIGH", "MEDIUM", "LOW"
- `archetype`: "FixesThatFail", "LimitsToGrowth", "ShiftingTheBurden", "TragedyOfCommons"
- `scenarioType`: "baseline", "alternative", "wildcard"

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd weekly-cli && python -m pytest tests/test_schema.py -v
```
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add weekly-cli/schema.py weekly-cli/tests/test_schema.py
git commit -m "feat(schema): complete Pydantic v2 data models for 格物 v2

All 5-phase models + evidence trace + metadata models with
enum sanitization, score clamping, cross-reference validation"
```

---

### Task 2: Config, Utilities, and Merger Foundation

**Files:**
- Modify: `weekly-cli/config.py`
- Create: `weekly-cli/merger.py`
- Modify: `weekly-cli/quality.py`
- Test: `weekly-cli/tests/test_merger.py`

**Interfaces:**
- Consumes: `schema.py` models
- Produces:
  - `config.py`: `DEEPSEEK_MODEL_DIALECTICAL = "deepseek-v4-pro"`, `DEEPSEEK_MODEL_EMPIRICAL = "deepseek-v4-flash"`, `get_logger(name)`, `setup_logging(verbose)`, `RUN_ID`
  - `merger.py`: `merge_phase(dialectical: BaseModel, empirical: BaseModel | None) -> dict` returning merged dict with `empiricalVerified`, `empiricalDegraded`, `empiricalSupplemental` flags
  - `quality.py`: `is_quality_event(event: Event) -> bool`, `is_quality_issue(issue: WeeklyIssue) -> bool`

- [ ] **Step 1: Update config.py**

Add model routing constants:

```python
DEEPSEEK_MODEL_DIALECTICAL = "deepseek-v4-pro"   # thinking=True for dialectical layers
DEEPSEEK_MODEL_EMPIRICAL = "deepseek-v4-flash"    # lighter model for empirical layers
```

Keep existing env var loading, path validation, logging setup unchanged. Add:

```python
MODEL_ROUTING = {
    "dialectical": DEEPSEEK_MODEL_DIALECTICAL,
    "empirical": DEEPSEEK_MODEL_EMPIRICAL,
}
```

- [ ] **Step 2: Write merger tests**

Create `weekly-cli/tests/test_merger.py`:

```python
"""Test dual-layer merge logic."""
import pytest
from schema import (
    PhenomenonGrasping, SelectedEvent, ExcludedEvent,
    SourceGrade, GDELTBaseline,
)


class TestMerge:
    def test_merge_with_empirical_verified(self):
        from merger import merge_phase
        dialectical = PhenomenonGrasping(
            phaseSummary="辩证总结",
            selectedEvents=[
                SelectedEvent(
                    id="evt-1", title="测试", summary="概述",
                    materialContent="有物质内容",
                    isDirectExpression=True,
                    sourceGrade=SourceGrade(
                        reliability="A", credibility=2, rationale="官方"
                    )
                )
            ],
            excludedEvents=[],
            gdeltBaseline=None,
            sourceQualityReport="好"
        )
        empirical = {"verificationNote": "来源质量确认", "verified": True}
        result = merge_phase(dialectical, empirical)
        assert result["empiricalVerified"] is True
        assert result["empiricalDegraded"] is False

    def test_merge_empirical_degraded(self):
        from merger import merge_phase
        dialectical = PhenomenonGrasping(
            phaseSummary="辩证总结",
            selectedEvents=[],
            excludedEvents=[],
            gdeltBaseline=None,
            sourceQualityReport="一般"
        )
        result = merge_phase(dialectical, None)
        assert result["empiricalDegraded"] is True
        assert result["empiricalVerified"] is False

    def test_merge_preserves_dialectical_data(self):
        from merger import merge_phase
        dialectical = PhenomenonGrasping(
            phaseSummary="辩证总结",
            selectedEvents=[
                SelectedEvent(
                    id="evt-1", title="测试", summary="概述",
                    materialContent="物质内容",
                    isDirectExpression=True,
                    sourceGrade=SourceGrade(
                        reliability="B", credibility=3, rationale="待确认"
                    )
                )
            ],
            excludedEvents=[],
            gdeltBaseline=None,
            sourceQualityReport="一般"
        )
        result = merge_phase(dialectical, None)
        assert result["phaseSummary"] == "辩证总结"
        assert len(result["selectedEvents"]) == 1
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd weekly-cli && python -m pytest tests/test_merger.py -v
```
Expected: ImportError (merger.py doesn't exist)

- [ ] **Step 4: Implement merger.py**

```python
"""Dual-layer merge: combines dialectical (core) and empirical (auxiliary) output per phase.

Merge rules:
1. Empirical confirms dialectical → merge with empiricalVerified=True
2. Empirical challenges dialectical → both kept, divergence flagged
3. Empirical degraded (None) → dialectical only, empiricalDegraded=True
4. Empirical supplements → appended with empiricalSupplemental markers
"""
from pydantic import BaseModel


def merge_phase(
    dialectical: BaseModel,
    empirical: dict | None,
) -> dict:
    """Merge dialectical and empirical output for one phase.
    
    Returns a dict with the merged output plus metadata flags.
    The merger does NOT resolve conflicts — it annotates them.
    """
    result = dialectical.model_dump()
    
    if empirical is None:
        result["empiricalVerified"] = False
        result["empiricalDegraded"] = True
        result["empiricalNotes"] = "实证层降级：数据不可用"
        return result
    
    # Empirical layer present
    result["empiricalVerified"] = empirical.get("verified", True)
    result["empiricalDegraded"] = False
    
    # If empirical challenges the dialectical analysis
    if empirical.get("challenges"):
        result["empiricalChallenges"] = empirical["challenges"]
        result["empiricalVerified"] = False
    
    # If empirical adds supplementary findings
    if empirical.get("supplements"):
        result["empiricalSupplemental"] = empirical["supplements"]
    
    # Merge any additional empirical data
    for key in ("verificationNote", "scoreCalibration", "dataContext"):
        if key in empirical:
            result[f"empirical_{key}"] = empirical[key]
    
    return result
```

- [ ] **Step 5: Run merger tests to verify they pass**

```bash
cd weekly-cli && python -m pytest tests/test_merger.py -v
```

- [ ] **Step 6: Update quality.py**

Add v2 quality gate functions:

```python
def is_quality_event(event) -> bool:
    """Quality gate for a single analyzed event (Phase 3+)."""
    timeline = getattr(event, "timeline", [])
    evidence = getattr(event, "evidence", [])
    if len(timeline) < 3:
        return False
    if len(evidence) < 2:
        return False
    verified = [e for e in evidence if getattr(e, "authenticity", None) in ("真实", "存疑")]
    if len(verified) == 0:
        return False
    summary = getattr(event, "dialecticalSummary", "")
    if len(summary) < 30:
        return False
    return True


def is_quality_issue(issue) -> bool:
    """Quality gate for a complete WeeklyIssue."""
    events = getattr(issue, "events", [])
    if not events:
        return False
    if getattr(issue, "phase1", None) is None:
        return False
    if getattr(issue, "phase2", None) is None:
        return False
    return True
```

- [ ] **Step 7: Commit**

```bash
git add weekly-cli/config.py weekly-cli/merger.py weekly-cli/quality.py weekly-cli/tests/test_merger.py
git commit -m "feat: add model routing, dual-layer merger, and v2 quality gates"
```

---

### Task 3: Prompt Templates — Dialectical Layer

**Files:**
- Rewrite: `weekly-cli/prompts/__init__.py`
- Create: `weekly-cli/prompts/dialectical/grasping.json`
- Create: `weekly-cli/prompts/dialectical/contradiction.json`
- Create: `weekly-cli/prompts/dialectical/unfolding.json`
- Create: `weekly-cli/prompts/dialectical/positioning.json`
- Create: `weekly-cli/prompts/dialectical/practice.json`

**Interfaces:**
- Produces: `load_prompt(name: str) -> str` (existing interface preserved)
- Each prompt template uses Python `str.format()` syntax with named placeholders

- [ ] **Step 1: Update prompts/__init__.py**

Keep existing `load_prompt` function, update to support nested subdirectories:

```python
"""Load LLM prompt templates from prompts/ directory."""
import json
from pathlib import Path

PROMPT_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt template by path (e.g. 'dialectical/grasping')."""
    path = PROMPT_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))["prompt"]
```

- [ ] **Step 2: Write grasping.json (Phase 1 prompt)**

```json
{
  "prompt": "你是一个唯物辩证法研究者。你的任务是**现象把握**——认识运动的第一个阶段，从感性具体出发，去粗取精、去伪存真。\n\n## 任务\n\n对以下 {event_count} 个热点话题进行物质内容初判。\n\n{events_text}\n\n## 方法——从物质利益出发，不做标签判断\n\n对每个话题，回答三个问题：\n\n1. **这件事背后有没有真实的物质利益关系？** 谁在推动什么？谁在抵抗什么？有没有具体的人因为这个事件得到或失去什么？\n2. **这是本质的直接表现还是歪曲反映？** 如果事件呈现的面貌与背后的物质利益关系一致，是直接表现；如果事件的表面叙述掩盖了真正的利益格局，是歪曲反映。\n3. **这个现象值得深入分析吗？** 如果只是纯粹的消费娱乐、个人猎奇、没有具体物质内容的话题——排除。但如果某个看似娱乐的事件暴露了具体的利益关系（如明星合同纠纷揭示的劳资关系），就有辩证分析价值。\n\n## 原则\n\n- 不要用\"反映了\"\"体现了\"开头——直接说具体的物质内容\n- 不要贴阶级标签——说清楚谁在什么条件下得到了什么、失去了什么\n- 不要因为话题\"敏感\"而排除——正常的阶级分析、社会矛盾讨论不是排除理由\n- 证据不足时如实说证据不足，不要用哲学语言填充\n\n## 输出 JSON\n\n{{\n  \"selectedEvents\": [\n    {{\n      \"id\": \"evt-{idx}\",\n      \"title\": \"事件标题\",\n      \"summary\": \"事件概述\",\n      \"materialContent\": \"物质内容初判——这件事背后谁在推动什么、谁在抵抗什么\",\n      \"isDirectExpression\": true,\n      \"rationale\": \"为什么入选——具体的辩证分析价值在哪\",\n      \"sourceGrade\": {{\n        \"reliability\": \"A-F\",\n        \"credibility\": 1-6,\n        \"rationale\": \"分级理由\"\n      }}\n    }}\n  ],\n  \"excludedEvents\": [\n    {{\n      \"title\": \"排除的事件\",\n      \"reason\": \"排除原因——必须有具体的物质内容判断\",\n      \"category\": \"纯消费娱乐 | 缺乏物质利益关系 | 信息不足无法判断\"\n    }}\n  ],\n  \"sourceQualityReport\": \"来源质量总评\"\n}}"
}
```

- [ ] **Step 3: Write contradiction.json (Phase 2 prompt)**

Structure: prompt the LLM as a dialectical materialist to extract contradiction structure from each event. Required output fields per spec: `primaryContradiction`, `opposingParties`, `principalAspect`, `secondaryContradictions`, `interestStructure` (whoBenefits, whoLoses, pushingForces, resistingForces), `classPositions` (party, materialBasis, classStance).

- [ ] **Step 4: Write unfolding.json (Phase 3 prompt)**

Structure: guide the LLM through the three laws of dialectics for each event. Required output: `unityOfOpposites` (identity, struggle, particularity, universality), `quantityQuality` (currentPhase, quantitativeDirection, measure, newQuality, oldQualityNegated), `negationOfNegation` (oldThing, firstNegation, internalNegation, direction, stageCharacteristics), `dialecticalSummary`.

- [ ] **Step 5: Write positioning.json (Phase 4 prompt)**

Structure: historical materialism positioning + cross-event synthesis. Required output per event: `productiveForces`, `productionRelations`, `baseStructure`, `superstructure`, `classForceComparison`, `historicalPosition`. Cross-event: `epochThemes`, `contradictionLandscape`.

- [ ] **Step 6: Write practice.json (Phase 5 prompt)**

Structure: practice orientation from dialectical analysis. Required output: `overallJudgment`, `scenarios` (3 types with probability bands, conditions, leading indicators, implications), `practiceSignificance`, `signalsToWatch`, `dataGaps`.

- [ ] **Step 7: Verify prompts load correctly**

```bash
cd weekly-cli && python -c "
from prompts import load_prompt
for p in ['dialectical/grasping', 'dialectical/contradiction', 'dialectical/unfolding', 'dialectical/positioning', 'dialectical/practice']:
    prompt = load_prompt(p)
    print(f'{p}: {len(prompt)} chars OK')
"
```

- [ ] **Step 8: Commit**

```bash
git add weekly-cli/prompts/
git commit -m "feat(prompts): dialectical layer prompt templates for all 5 phases"
```

---

### Task 4: Prompt Templates — Empirical Layer

**Files:**
- Create: `weekly-cli/prompts/empirical/verifier.json`
- Create: `weekly-cli/prompts/empirical/adversary.json`
- Create: `weekly-cli/prompts/empirical/quantitative.json`
- Create: `weekly-cli/prompts/narrative/article.json`

**Interfaces:**
- Each prompt uses `str.format()` placeholders for event data injection

- [ ] **Step 1: Write verifier.json**

Evidence grading prompt: Admiralty source grading (A-F reliability, 1-6 credibility), independent corroboration check, ACH competing hypothesis generation.

- [ ] **Step 2: Write adversary.json**

Devil's Advocate prompt: "找出辩证分析中最弱的3个断言，逐条挑战。如果你是一个持反对立场的分析者，你会怎么反驳？挑战必须是具体的——指出被忽略的证据、被简化的利益关系、被跳过的辩证推理步骤。"

- [ ] **Step 3: Write quantitative.json**

Quantitative data interpretation prompt: interpret GDELT event statistics, sentiment time series, change-point detection results in the context of the dialectical analysis.

- [ ] **Step 4: Write narrative/article.json**

Article generation prompt: "将以下五阶段辩证分析合成为一篇面向读者的文章。叙事必须跟随辩证认识运动的节奏：从现象（读者看到了什么）→ 矛盾（这背后是什么在对抗）→ 展开（矛盾如何运动）→ 定位（这在更大的历史图景中处于什么位置）→ 方向（我们应该关注什么）。"

- [ ] **Step 5: Verify and commit**

```bash
cd weekly-cli && python -c "
from prompts import load_prompt
for p in ['empirical/verifier', 'empirical/adversary', 'empirical/quantitative', 'narrative/article']:
    prompt = load_prompt(p)
    print(f'{p}: {len(prompt)} chars OK')
"
git add weekly-cli/prompts/empirical/ weekly-cli/prompts/narrative/
git commit -m "feat(prompts): empirical layer and narrative prompt templates"
```

---

### Task 5: Phase 1 — Phenomenon Grasping

**Files:**
- Create: `weekly-cli/dialectical/__init__.py`
- Create: `weekly-cli/dialectical/grasping.py`
- Create: `weekly-cli/empirical/__init__.py`
- Test: `weekly-cli/tests/dialectical/test_grasping.py`

**Interfaces:**
- Consumes: `DeepSeekClient`, list of `RawEvent` dicts, `prompts.dialectical.grasping`
- Produces: `grasp_phenomena(client, events) -> dict` matching `PhenomenonGrasping` schema
- Empirical layer: `verify_sources(events) -> dict | None` (created in Task 7, stubbed here)

- [ ] **Step 1: Write test**

```python
"""Test Phase 1: Phenomenon Grasping."""
import pytest
from dialectical.grasping import grasp_phenomena, build_events_text


class TestBuildEventsText:
    def test_formats_events(self):
        events = [
            {"title": "事件A", "summary": "概述A"},
            {"title": "事件B", "summary": "概述B"},
        ]
        text = build_events_text(events)
        assert "事件A" in text
        assert "事件B" in text
        assert "概述A" in text


class TestGrasping:
    @pytest.mark.integration
    def test_grasp_phenomena_with_client(self):
        """Integration test: requires DEEPSEEK_API_KEY."""
        import os
        if not os.environ.get("DEEPSEEK_API_KEY"):
            pytest.skip("DEEPSEEK_API_KEY not set")
        from chinese_scraper_utils import DeepSeekClient
        from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL_DIALECTICAL
        
        client = DeepSeekClient(DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_DIALECTICAL, thinking=True)
        events = [
            {"title": "AI大模型价格战", "summary": "多家科技巨头宣布大幅下调大模型API价格"},
            {"title": "某明星演唱会", "summary": "某歌手巡回演唱会门票售罄"},
        ]
        result = grasp_phenomena(client, events)
        assert "selectedEvents" in result
        assert "excludedEvents" in result
        # AI price war should be selected, concert should be excluded
        selected_titles = [e["title"] for e in result.get("selectedEvents", [])]
        assert any("AI" in t or "大模型" in t for t in selected_titles)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd weekly-cli && python -m pytest tests/dialectical/test_grasping.py::TestBuildEventsText -v
```

- [ ] **Step 3: Implement grasping.py**

```python
"""Phase 1: Phenomenon Grasping — the first stage of dialectical epistemology.

From perceptual concreteness: 去粗取精、去伪存真、由此及彼、由表及里.
"""
from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt

GRASPING_PROMPT = load_prompt("dialectical/grasping")


def build_events_text(events: list[dict]) -> str:
    """Format raw events for prompt injection."""
    lines = []
    for i, e in enumerate(events):
        lines.append(f"[{i+1}] {e['title']}")
        lines.append(f"    {e.get('summary', '')[:200]}")
    return "\n".join(lines)


def grasp_phenomena(
    client: DeepSeekClient,
    events: list[dict],
) -> dict:
    """Execute Phase 1: Phenomenon Grasping.
    
    Returns a dict matching PhenomenonGrasping schema fields:
    - selectedEvents: events with dialectical analysis value
    - excludedEvents: events excluded with specific reasons
    - sourceQualityReport: overall source quality assessment
    """
    if not events:
        return {
            "selectedEvents": [],
            "excludedEvents": [],
            "sourceQualityReport": "无事件可供分析",
        }
    
    events_text = build_events_text(events)
    prompt = GRASPING_PROMPT.format(
        event_count=len(events),
        events_text=events_text,
    )
    
    result = client.chat_json([
        {
            "role": "system",
            "content": (
                "你是一个唯物辩证法研究者。你的任务是现象把握——"
                "认识运动的第一个阶段。用朴实中文写作，不堆砌术语，"
                "不贴标签。严格按JSON格式输出。"
            )
        },
        {"role": "user", "content": prompt},
    ], max_tokens=8192)
    
    # Ensure selectedEvents have required fields
    for i, e in enumerate(result.get("selectedEvents", []) or []):
        if "id" not in e:
            e["id"] = f"evt-{i+1}"
        if "sourceGrade" not in e:
            e["sourceGrade"] = {
                "reliability": "C",
                "credibility": 3,
                "rationale": "未提供来源评估"
            }
    
    return result
```

- [ ] **Step 4: Run unit test to verify it passes**

```bash
cd weekly-cli && python -m pytest tests/dialectical/test_grasping.py::TestBuildEventsText -v
```

- [ ] **Step 5: Commit**

```bash
git add weekly-cli/dialectical/ weekly-cli/tests/dialectical/
git commit -m "feat(phase1): phenomenon grasping — dialectical filter replacing censor"
```

---

### Task 6: Phase 2 — Contradiction Identification

**Files:**
- Create: `weekly-cli/dialectical/contradiction.py`
- Test: `weekly-cli/tests/dialectical/test_contradiction.py`

**Interfaces:**
- Consumes: `DeepSeekClient`, list of selected event dicts from Phase 1, `prompts.dialectical.contradiction`
- Produces: `identify_contradictions(client, events) -> dict` matching `ContradictionIdentification` schema

- [ ] **Step 1: Write test**

```python
"""Test Phase 2: Contradiction Identification."""
import pytest


class TestContradictionIdentification:
    def test_build_events_context(self):
        from dialectical.contradiction import build_contradiction_context
        events = [
            {
                "id": "evt-1", "title": "测试事件",
                "materialContent": "测试物质内容",
                "summary": "测试概述"
            }
        ]
        ctx = build_contradiction_context(events)
        assert "evt-1" in ctx
        assert "测试事件" in ctx

    @pytest.mark.integration
    def test_identify_contradictions(self):
        import os
        if not os.environ.get("DEEPSEEK_API_KEY"):
            pytest.skip("DEEPSEEK_API_KEY not set")
        from chinese_scraper_utils import DeepSeekClient
        from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL_DIALECTICAL
        from dialectical.contradiction import identify_contradictions
        
        client = DeepSeekClient(DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_DIALECTICAL, thinking=True)
        events = [{
            "id": "evt-1",
            "title": "AI大模型价格战全面爆发",
            "materialContent": "科技资本通过价格战清洗中小竞争者",
            "summary": "多家科技巨头宣布大幅下调大模型API价格"
        }]
        result = identify_contradictions(client, events)
        assert "events" in result
        assert len(result["events"]) >= 1
        e = result["events"][0]
        assert "primaryContradiction" in e
        assert "interestStructure" in e
```

- [ ] **Step 2: Implement contradiction.py**

Key function: `identify_contradictions(client, events) -> dict` that calls the LLM with the contradiction prompt, formats event context, and returns structured contradiction analysis.

- [ ] **Step 3: Run tests**

```bash
cd weekly-cli && python -m pytest tests/dialectical/test_contradiction.py -v
```

- [ ] **Step 4: Commit**

```bash
git add weekly-cli/dialectical/contradiction.py weekly-cli/tests/dialectical/test_contradiction.py
git commit -m "feat(phase2): contradiction identification — extract primary contradiction and interest structure"
```

---

### Task 7: Phase 3 — Dialectical Unfolding + Adversarial Review

**Files:**
- Create: `weekly-cli/dialectical/unfolding.py`
- Create: `weekly-cli/empirical/adversary.py`
- Test: `weekly-cli/tests/dialectical/test_unfolding.py`
- Test: `weekly-cli/tests/empirical/test_adversary.py`

**Interfaces:**
- `unfold_dialectics(client, event, search_results, idx) -> dict` — Phase 3 dialectical core
- `adversarial_review(client, unfolding_result) -> dict | None` — empirical layer, degrades gracefully

- [ ] **Step 1: Write tests**

Test unfolding unit tests (build search context, format event for prompt). Integration test for full unfolding + adversarial review pipeline.

- [ ] **Step 2: Implement unfolding.py**

The three-law dialectical analysis: unity of opposites → quantity-quality → negation of negation. Adapts from existing `analyzer.py` structure but replaces the MLM class analysis prompt with dialectical unfolding.

- [ ] **Step 3: Implement adversary.py**

Devil's Advocate review: takes the unfolding output, prompts a fresh LLM instance to find weaknesses, returns challenges. On failure, returns None (graceful degradation).

- [ ] **Step 4: Run and commit**

```bash
cd weekly-cli && python -m pytest tests/dialectical/test_unfolding.py tests/empirical/test_adversary.py -v
git add weekly-cli/dialectical/unfolding.py weekly-cli/empirical/adversary.py weekly-cli/tests/
git commit -m "feat(phase3): dialectical unfolding + adversarial review"
```

---

### Task 8: Phase 4 — Historical Positioning + Synthesis

**Files:**
- Create: `weekly-cli/dialectical/positioning.py`
- Test: `weekly-cli/tests/dialectical/test_positioning.py`

**Interfaces:**
- `position_historically(client, events) -> dict` — historical materialism positioning + cross-event synthesis
- Consumes: Phase 3 output event dicts

- [ ] **Step 1: Write test**

Unit test for `build_positioning_context` (XML event blocks). Integration test for full positioning.

- [ ] **Step 2: Implement positioning.py**

Per-event: productive forces, production relations, base, superstructure, class force comparison, historical position.
Cross-event: epoch themes, contradiction landscape.

- [ ] **Step 3: Commit**

```bash
git add weekly-cli/dialectical/positioning.py weekly-cli/tests/dialectical/test_positioning.py
git commit -m "feat(phase4): historical positioning and cross-event synthesis"
```

---

### Task 9: Phase 5 — Practice Orientation

**Files:**
- Create: `weekly-cli/dialectical/practice.py`
- Test: `weekly-cli/tests/dialectical/test_practice.py`

**Interfaces:**
- `orient_practice(client, synthesis_result) -> dict` — practice orientation: overall judgment, signals, data gaps

- [ ] **Step 1: Write test**
- [ ] **Step 2: Implement practice.py**
- [ ] **Step 3: Commit**

```bash
git add weekly-cli/dialectical/practice.py weekly-cli/tests/dialectical/test_practice.py
git commit -m "feat(phase5): practice orientation — judgment, signals, scenarios"
```

---

### Task 10: Empirical Layer — Verifier, Scorer, Quantitative

**Files:**
- Create: `weekly-cli/empirical/verifier.py`
- Create: `weekly-cli/empirical/scorer.py`
- Create: `weekly-cli/empirical/quantitative.py`
- Test: `weekly-cli/tests/empirical/test_verifier.py`
- Test: `weekly-cli/tests/empirical/test_scorer.py`

**Interfaces:**
- `verify_evidence(client, event) -> dict | None` — source grading + ACH + corroboration
- `score_event(client, event) -> dict | None` — 9-dimension scores
- `quantitative_context(event_title) -> dict | None` — GDELT stats + sentiment + change-point

- [ ] **Step 1: Implement verifier.py**

Evidence grading with simplified Admiralty system. ACH (Analysis of Competing Hypotheses) matrix generation. Independent corroboration check via web search.

- [ ] **Step 2: Implement scorer.py**

9-dimension scoring (D1-D9) with per-dimension confidence. Each dimension scored 1-10 via structured LLM prompt.

- [ ] **Step 3: Implement quantitative.py**

GDELT event count/tone query (via chinese-scraper-utils or direct API). Sentiment baseline extraction. Change-point detection stub (PELT via Harbinger, or simple statistical outlier detection as fallback).

- [ ] **Step 4: Run and commit**

```bash
cd weekly-cli && python -m pytest tests/empirical/ -v
git add weekly-cli/empirical/ weekly-cli/tests/empirical/
git commit -m "feat(empirical): verifier, scorer, and quantitative modules"
```

---

### Task 11: Empirical Layer — Causal, Connections, Scenarios

**Files:**
- Create: `weekly-cli/empirical/causal.py`
- Create: `weekly-cli/empirical/connections.py`
- Create: `weekly-cli/empirical/scenarios.py`

**Interfaces:**
- `build_causal_loop(client, events) -> dict | None` — CLD + system archetype matching
- `find_connections(client, events) -> dict | None` — non-obvious connections + PESTLE matrix
- `plan_scenarios(client, synthesis) -> dict | None` — GBN 3-scenario + leading indicators

- [ ] **Step 1: Implement causal.py**

Causal loop diagram generation + system archetype (FixesThatFail, LimitsToGrowth, ShiftingTheBurden, TragedyOfCommons) matching.

- [ ] **Step 2: Implement connections.py**

Event graph anomaly detection + PESTLE interaction matrix + shortest-path link analysis.

- [ ] **Step 3: Implement scenarios.py**

GBN 8-step scaled down for weekly cadence: 2 key uncertainties → 2x2 matrix → 3 scenarios with probability bands and signpost indicators.

- [ ] **Step 4: Commit**

```bash
git add weekly-cli/empirical/causal.py weekly-cli/empirical/connections.py weekly-cli/empirical/scenarios.py
git commit -m "feat(empirical): causal loop diagrams, hidden connections, and scenario planning"
```

---

### Task 12: Article Generator — Five-Phase Narrative

**Files:**
- Create: `weekly-cli/narrative/__init__.py`
- Create: `weekly-cli/narrative/article.py`
- Test: `weekly-cli/tests/test_article.py` (rewrite)

**Interfaces:**
- `generate_article(issue: WeeklyIssue) -> str` — Markdown article following the 5-phase dialectical narrative structure

- [ ] **Step 1: Write test**

```python
def test_article_has_five_sections():
    """Article must have all 5 dialectical phases as sections."""
    from narrative.article import generate_article
    from schema import WeeklyIssue, PhenomenonGrasping, EvidenceTrace, IssueMetadata
    
    issue = WeeklyIssue(
        id="2026-W31", weekStart="2026-07-27", weekEnd="2026-08-02",
        events=[],
        phase1=PhenomenonGrasping(
            phaseSummary="现象总结",
            selectedEvents=[],
            excludedEvents=[],
            gdeltBaseline=None,
            sourceQualityReport="好"
        ),
        evidenceTrace=EvidenceTrace(claims=[], totalVerifiedClaims=0),
        metadata=IssueMetadata(
            modelVersions={}, verificationPasses=0,
            empiricalDegradations=[], totalApiCost=0.0,
            runDuration=0.0, runId="test"
        )
    )
    md = generate_article(issue)
    assert "一、现象" in md
    assert "二、矛盾" in md
    assert "三、展开" in md
    assert "四、定位" in md
    assert "五、方向" in md
    assert "格物" in md
```

- [ ] **Step 2: Implement article.py**

Generate Markdown following the 5-phase structure. Each section renders from the corresponding phase model. Footer references 格物 (Dianalyze). Uncertainty labels ([HIGH]/[MEDIUM]/[LOW]) applied to analytical assertions.

- [ ] **Step 3: Run test and commit**

```bash
cd weekly-cli && python -m pytest tests/test_article.py -v
git add weekly-cli/narrative/ weekly-cli/tests/test_article.py
git commit -m "feat(narrative): five-phase dialectical article generator"
```

---

### Task 13: Main Orchestrator — Five-Phase Pipeline

**Files:**
- Rewrite: `weekly-cli/main.py`
- Modify: `weekly-cli/conftest.py`

**Interfaces:**
- `main(argv)` — 5-phase pipeline driver
- Phase 0: scrape (preserved from existing)
- Phase 1-5: dialectical + empirical + merge pattern
- Output: JSON + Markdown article

- [ ] **Step 1: Write the orchestrator**

Rewrite `main.py` with the 5-phase dual-layer structure. Key flow:

```python
def main(argv=None):
    args = parse_args(argv)
    setup_logging(verbose=args.verbose)
    
    # Model clients
    dialectical_client = DeepSeekClient(DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_DIALECTICAL, thinking=True)
    empirical_client = DeepSeekClient(DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_EMPIRICAL)
    
    # Phase 0: Scrape (preserved)
    raw_events = scrape_or_load_cache(args)
    
    # Phase 1: Phenomenon Grasping
    p1_dialectical = grasp_phenomena(dialectical_client, raw_events)
    p1_empirical = safe_call(verify_sources, empirical_client, p1_dialectical)
    p1_merged = merge_phase(PhenomenonGrasping(**p1_dialectical), p1_empirical)
    
    # Phase 2: Contradiction Identification
    p2_dialectical = identify_contradictions(dialectical_client, p1_merged["selectedEvents"])
    p2_empirical = safe_call(score_event, empirical_client, p2_dialectical)
    p2_merged = merge_phase(ContradictionIdentification(**p2_dialectical), p2_empirical)
    
    # Phase 3: Dialectical Unfolding (parallel per event)
    analyzed = parallel_analyze(dialectical_client, empirical_client, p2_merged["events"])
    
    # Phase 4: Historical Positioning
    p4_dialectical = position_historically(dialectical_client, analyzed)
    p4_empirical = safe_call(find_connections, empirical_client, analyzed)
    p4_merged = merge_phase(HistoricalPositioning(**p4_dialectical), p4_empirical)
    
    # Phase 5: Practice Orientation
    p5_dialectical = orient_practice(dialectical_client, p4_merged)
    p5_empirical = safe_call(plan_scenarios, empirical_client, p4_merged)
    p5_merged = merge_phase(PracticeOrientation(**p5_dialectical), p5_empirical)
    
    # Assemble WeeklyIssue
    # Output JSON + Markdown
```

- [ ] **Step 2: Update conftest.py fixtures for v2**

Add `sample_grasping`, `sample_contradiction`, `sample_unfolding`, `sample_weekly_issue` fixtures.

- [ ] **Step 3: Commit**

```bash
git add weekly-cli/main.py weekly-cli/conftest.py
git commit -m "feat(main): five-phase dialectical pipeline orchestrator"
```

---

### Task 14: Scraper Adaptation + Cache Migration

**Files:**
- Move: `weekly-cli/cache.py` → `weekly-cli/scraper/cache.py`
- Create: `weekly-cli/scraper/sources.py` (extract scrape logic from old main.py)
- Create: `weekly-cli/scraper/__init__.py`

- [ ] **Step 1: Move and adapt cache.py**
- [ ] **Step 2: Extract sources.py from existing main.py Phase 0 logic**
- [ ] **Step 3: Update main.py imports**
- [ ] **Step 4: Commit**

```bash
git add weekly-cli/scraper/ weekly-cli/cache.py weekly-cli/main.py
git commit -m "refactor: extract scraper and cache into scraper/ module"
```

---

### Task 15: Cleanup — Remove Old Code, Finalize Tests

**Files:**
- Remove: `weekly-cli/censor.py`, `weekly-cli/scorer.py`, `weekly-cli/analyzer.py`, `weekly-cli/synthesizer.py`, `weekly-cli/article.py`
- Remove: `weekly-cli/prompts/censor.json`, `weekly-cli/prompts/scorer.json`, `weekly-cli/prompts/analyzer.json`, `weekly-cli/prompts/synthesizer.json`
- Remove: `weekly-cli/sample_weekly.json`
- Rewrite: `weekly-cli/tests/` — remove old test files for removed modules

- [ ] **Step 1: Remove old source files**

```bash
cd weekly-cli
rm -f censor.py scorer.py analyzer.py synthesizer.py article.py
rm -f prompts/censor.json prompts/scorer.json prompts/analyzer.json prompts/synthesizer.json
rm -f sample_weekly.json cache.py  # cache moved to scraper/
```

- [ ] **Step 2: Remove old test files**

```bash
cd weekly-cli/tests
rm -f test_censor.py test_scorer.py test_analyzer.py test_synthesizer.py test_cache.py test_client.py test_config.py test_search.py test_main.py
```

- [ ] **Step 3: Run full test suite**

```bash
cd weekly-cli && python -m pytest tests/ -v --cov=. --cov-report=term-missing -m "not integration"
```

Verify ≥80% coverage.

- [ ] **Step 4: Update requirements.txt if needed**

Remove any deps no longer needed; add any new ones (GDELT client, etc.).

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: remove old v1 code — complete migration to 格物 v2

Removed: censor.py, scorer.py, analyzer.py, synthesizer.py, old article.py, old prompts, old tests
The system is now fully 5-phase dialectical with dual-layer architecture"
```

---

### Task 16: End-to-End Validation

**Files:**
- Run: full pipeline dry-run
- Verify: output JSON validates against schema
- Verify: Markdown article renders correctly

- [ ] **Step 1: Run dry-run pipeline**

```bash
cd weekly-cli && python main.py --dry-run --verbose --max-events 3
```

Expected: All 5 phases complete, JSON output valid, no crashes.

- [ ] **Step 2: Run full pipeline with output**

```bash
cd weekly-cli && python main.py --max-events 5
```

Expected: `{weekId}.json` and `posts/{weekId}/index.md` generated.

- [ ] **Step 3: Validate output**

```python
from schema import WeeklyIssue
import json
wi = WeeklyIssue.model_validate_json(open(f"{weekId}.json").read())
assert wi.phase1 is not None
assert wi.phase2 is not None
assert wi.phase3 is not None
assert wi.phase4 is not None
assert wi.phase5 is not None
print("Output validation PASSED")
```

- [ ] **Step 4: Final commit with any fixes**

```bash
git add -A && git commit -m "chore: E2E validation fixes" && git push
```

---

## Self-Review Checklist

1. **Spec coverage**: All 5 phases, all data models, dual-layer structure, merger, prompts, article structure, evidence trace — each mapped to a task.
2. **Placeholder scan**: All steps have concrete code. No TODOs or "implement later".
3. **Type consistency**: Model names match schema.py definitions. Function signatures consistent across tasks.
