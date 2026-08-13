# 格物 — 辩证周报分析系统 v2

> **状态**: 已确认
> **日期**: 2026-07-30
> **项目名**: 格物（取"格物致知"——探究事物原理，穷究矛盾本质）
> **仓库**: `dreamnight16/gewu`（从 `weekly-hotspot` 更名）
> **目标**: 以唯物辩证法和历史唯物主义为绝对核心方法论，辅以现代分析手段，全量重构

---

## 一、重构目标

### 当前系统的问题

| # | 缺陷 | 根因 |
|---|------|------|
| 1 | 评分仅 2 维（impact × info_gain） | 缺少辩证矛盾的评估维度 |
| 2 | 单次 LLM 生成，输出套公式 | 无批判、无 refine、无对抗挑战 |
| 3 | 零证据验证 | 每个断言都是未检查的 LLM 自评 |
| 4 | 无定量数据锚点 | 纯文本悬浮分析，脱离可测量现实 |
| 5 | 无对抗性压力测试 | 每个结论都是没有经过挑战的第一反应 |

### 重构后的核心原则

- **唯物辩证法为绝对核心**：整个分析流水线由辩证法的认识运动驱动，从感性具体到理性抽象再到理性具体，最后回归实践
- **历史唯物主义为宏观定位框架**：每个事件都在生产力-生产关系、经济基础-上层建筑的坐标系中定位
- **现代分析手段为辅助工具**：9维评分、证据验证、多轮对抗、定量数据、因果循环图、情景分析等服务于辩证分析，不替代辩证分析
- **不确定性必须诚实**：区分"有证据支撑的判断"和"有辩证价值但证据不足的推论"
- **实践指向**：分析最终必须回答"这对我理解当下社会有什么帮助"，并给出下周可观测的具体信号

---

## 二、方法论体系

### 唯物辩证法三个基本规律在系统中的作用

| 规律 | 在系统中的作用 | 对应阶段 |
|------|---------------|---------|
| **对立统一规律** | 每个事件的分析核心——识别矛盾双方、它们的物质利益、对抗的具体形态、同一性与斗争性、矛盾的特殊性与普遍性 | 阶段二矛盾识别 + 阶段三展开 |
| **量变质变规律** | 判断事件性质——是量变积累还是质的飞跃？矛盾发展到了什么阶段？度的边界在哪里？ | 阶段三展开 |
| **否定之否定规律** | 把握运动方向——旧事物被否定、新事物在旧事物内部成长、螺旋上升或暂时倒退 | 阶段三展开 + 阶段五实践指向 |

### 历史唯物主义宏观定位框架

| 范畴 | 分析内容 | 对应阶段 |
|------|---------|---------|
| **生产力-生产关系** | 事件反映的是生产力发展还是生产关系调整？二者之间的矛盾如何表现？ | 阶段四历史定位 |
| **经济基础-上层建筑** | 事件属于经济基础还是上层建筑？二者作用与反作用如何？ | 阶段四历史定位 |
| **阶级分析** | 各方的物质利益位置、阶级力量对比的变化 | 贯穿阶段二、三、四 |
| **社会存在决定社会意识** | 各方立场和言论的背后物质基础 | 阶段二矛盾识别 + 阶段三展开 |

### 辩证认识运动路线

```
感性具体 ──→ 理性抽象 ──→ 理性具体 ──→ 实践

  阶段一        阶段二        阶段三、四       阶段五
 现象把握      矛盾识别      辩证展开         实践指向
                             历史定位
```

---

## 三、系统架构

### 双层结构设计

每个阶段都按**辩证层（核心）+ 实证层（辅助）→ 阶段末尾合并**的双层结构组织：

```
┌──────────────────────────────────────────────┐
│                 阶段 N                       │
│                                              │
│  ┌─────────────┐      ┌──────────────┐       │
│  │  辩证分析层   │      │  实证检验层    │       │
│  │  (核心,必跑)  │      │  (辅助,可降级) │       │
│  │              │      │              │       │
│  │ 辩证提示词    │      │ 现代方法工具   │       │
│  │ 唯物辩证法逻辑 │      │ 证据/数据/对抗  │       │
│  │ 历史唯物框架  │      │ 校准/验证/补充  │       │
│  └──────┬───────┘      └──────┬───────┘       │
│         │                     │               │
│         └──────┬──────────────┘               │
│                ▼                              │
│         ┌──────────┐                          │
│         │  合并器   │                          │
│         │          │                          │
│         │ 标注不一致 │                          │
│         │ 统一输出   │                          │
│         └──────────┘                          │
└──────────────────────────────────────────────┘
```

### 五阶段流水线

```
[Phase 0] 抓取 (Weibo/Zhihu/HN + 缓存)
  │
  ▼
[Phase 1] 现象把握 (感性认识阶段)
  ├── 辩证层: 物质内容初判 + 去伪存真
  │   问题: 这件事背后有没有真实的物质利益关系？
  │   不是简单排除"娱乐八卦"——如果暴露了具体阶级利益格局就有价值
  │   区分本质的直接表现 vs 本质的歪曲反映
  ├── 实证层: 来源可信度分级(Admiralty简化) + GDELT基线 + 舆情基线
  └── 合并: PhenomenonGrasping — 筛选后事件集 + 来源质量 + 定量基线
  │
  ▼
[Phase 2] 矛盾识别 (理性认识·抽象)
  ├── 辩证层: 提取矛盾结构
  │   ① 主要矛盾——对立统一的具体形态，不能笼统说"劳资矛盾"
  │   ② 矛盾的主要方面——谁占支配地位？矛盾的性质由谁决定？
  │   ③ 物质利益格局——谁在推动什么、谁在抵抗什么、谁得到什么、谁失去什么
  ├── 实证层: 9维评分校准 + 竞争假设(ACH) + 关键实体重要性查询
  └── 合并: ContradictionIdentification — 矛盾结构 + 利益格局 + 替代解释对比
  │
  ▼
[Phase 3] 辩证展开 (理性认识·具体)
  ├── 辩证层: 三个基本规律的逐一展开
  │   ① 对立统一展开: 同一性(相互依存/转化条件) + 斗争性(对抗烈度) + 特殊性与普遍性
  │   ② 量变质变判断: 量变还是质变？度在哪里？积累方向？新质是什么？
  │   ③ 否定之否定: 旧事物→否定→新事物→自我否定→螺旋上升？阶段性特征？
  ├── 实证层: 多轮对抗分析 + 因果循环图(CLD) + 变点检测 + 定量数据
  └── 合并: DialecticalUnfolding — 三规律逐条展开 + 对抗挑战 + 反馈结构 + 数据验证
  │
  ▼
[Phase 4] 历史定位 + 跨事件综合 (理性认识·具体)
  ├── 辩证层: 历史唯物主义定位 + 跨事件综合
  │   ① 生产力-生产关系: 新技术/新组织 vs 所有制/分配方式变化
  │   ② 经济基础-上层建筑: 属于哪一层？二者作用与反作用？
  │   ③ 阶级力量对比: 谁的力量在增强？谁的在削弱？
  │   ④ 历史方位: 在更长时段中处于什么位置？量变节点还是转折点？
  │   ⑤ 跨事件综合: 时代主题 + 矛盾总景观 + 事件间相互加强/抵消
  ├── 实证层: 系统原型匹配 + 非显见关联 + 历史类比检索
  └── 合并: HistoricalPositioning — 历史定位 + 跨事件综合 + 系统原型 + 非显见关联
  │
  ▼
[Phase 5] 实践指向 (理性回归实践)
  ├── 辩证层: 矛盾运动总判断 + 实践意义 + 可观测信号
  ├── 实证层: 情景规划(3情景) + 上周校准回溯 + 不确定性诚实标注
  └── 合并: PracticeOrientation — 总判断 + 情景 + 信号 + 校准
  │
  ▼
[输出] JSON + Markdown 文章 (按五阶段结构组织)
```

---

## 四、数据模型

### 顶层结构

```
WeeklyIssue
├── id: str                         # e.g. "2026-W31"
├── weekStart: str                  # "2026-07-27"
├── weekEnd: str                    # "2026-08-02"
├── phase1: PhenomenonGrasping
├── phase2: ContradictionIdentification
├── phase3: DialecticalUnfolding
├── phase4: HistoricalPositioning
├── phase5: PracticeOrientation
├── evidenceTrace: EvidenceTrace    # 全链证据溯源
└── metadata: IssueMetadata
```

### 阶段一：PhenomenonGrasping

```
PhenomenonGrasping
├── phaseSummary: str               # "本周抓取 X 个事件，通过物质内容初判筛选后保留 Y 个"
├── selectedEvents: list[SelectedEvent]
│   ├── id: str
│   ├── title: str
│   ├── summary: str
│   ├── sourceUrl: str | None
│   ├── materialContent: str        # 物质内容初判：这件事背后有没有真实的物质利益关系？
│   ├── isDirectExpression: bool    # 是本质的直接表现还是歪曲反映？
│   └── sourceGrade: SourceGrade
│       ├── reliability: "A"|"B"|"C"|"D"|"E"|"F"  # Admiralty 简化
│       ├── credibility: 1|2|3|4|5|6
│       └── rationale: str
├── excludedEvents: list[ExcludedEvent]
│   ├── title: str
│   ├── reason: str                 # 为什么排除——必须有具体的物质内容判断
│   └── category: str               # 纯消费娱乐 | 缺乏物质利益关系 | 信息不足无法判断
├── gdeltBaseline: GDELTBaseline | None  # GDELT 本周事件统计基线
│   ├── totalEventsThisWeek: int
│   ├── toneAvg: float
│   └── topThemes: list[str]
└── sourceQualityReport: str        # 来源质量总评
```

### 阶段二：ContradictionIdentification

```
ContradictionIdentification
├── phaseSummary: str               # "从 Y 个事件中识别出 Z 个具有明确矛盾结构的"
├── events: list[EventContradiction]
│   ├── eventId: str
│   ├── primaryContradiction: str              # 主要矛盾的具体形态（不能笼统）
│   │   # 例："平台企业通过调整抽成机制将政府社保政策的合规成本转嫁给骑手"
│   ├── opposingParties: tuple[str, str]       # 矛盾双方
│   ├── principalAspect: str                   # 矛盾的主要方面 + 判断依据
│   ├── secondaryContradictions: list[str]     # 次要矛盾
│   ├── interestStructure: InterestStructure
│   │   ├── whoBenefits: str                  # 谁得到了什么
│   │   ├── whoLoses: str                     # 谁失去了什么
│   │   ├── pushingForces: str                # 谁在推动什么
│   │   └── resistingForces: str              # 谁在抵抗什么
│   ├── classPositions: list[ClassPosition]    # 各方的阶级立场（基于物质利益，不贴标签）
│   │   ├── party: str
│   │   ├── materialBasis: str                # 物质利益基础
│   │   └── classStance: str
│   ├── nineDimCalibration: NineDimScores      # 9维评分校准
│   │   ├── magnitude: tuple[int, float]       # (score, confidence)
│   │   ├── scope: tuple[int, float]
│   │   ├── velocity: tuple[int, float]
│   │   ├── novelty: tuple[int, float]
│   │   ├── cascadePotential: tuple[int, float]
│   │   ├── actorProminence: tuple[int, float]
│   │   ├── uncertainty: tuple[int, float]
│   │   ├── polarity: tuple[int, float]
│   │   └── durability: tuple[int, float]
│   └── competingHypotheses: list[CompetingHypothesis]  # ACH 竞争假设
│       ├── hypothesis: str
│       ├── evidenceFor: list[str]
│       ├── evidenceAgainst: list[str]
│       └── likelihood: str                     # 相对辩证解释的可能性
└── overallContradictionLandscape: str          # 全周矛盾格局总览
```

### 阶段三：DialecticalUnfolding

```
DialecticalUnfolding
├── phaseSummary: str
├── events: list[EventDialectical]
│   ├── eventId: str
│   ├── unityOfOpposites: UnityOfOpposites
│   │   ├── identity: str              # 同一性——对立双方在什么条件下相互依存、相互转化？
│   │   ├── struggle: str              # 斗争性——对抗的具体形态和烈度
│   │   ├── particularity: str         # 矛盾的特殊性——与其他同类矛盾的特殊区别
│   │   └── universality: str          # 矛盾的普遍性——揭示的普遍规律
│   ├── quantityQuality: QuantityQuality
│   │   ├── currentPhase: str          # "量变积累" | "质的飞跃" | "量变中的局部质变"
│   │   ├── quantitativeDirection: str # 量的积累方向
│   │   ├── measure: str               # 度——量变达到什么程度会发生质变
│   │   ├── newQuality: str | None     # 如果正在质变——新质是什么
│   │   └── oldQualityNegated: str     # 被否定的旧质
│   ├── negationOfNegation: NegationOfNegation
│   │   ├── oldThing: str              # 旧事物
│   │   ├── firstNegation: str         # 第一次否定：旧事物被什么否定
│   │   ├── internalNegation: str      # 新事物内部孕育的自我否定因素
│   │   ├── direction: str             # "螺旋上升" | "暂时倒退" | "停滞"
│   │   └── stageCharacteristics: str  # 发展阶段性特征
│   ├── dialecticalSummary: str        # 三规律的辩证总结（<200字）
│   ├── adversarialReview: AdversarialReview
│   │   ├── challenged: bool
│   │   ├── challenges: list[str]      # 对抗审查提出的挑战
│   │   ├── survived: bool
│   │   └── revised: str | None        # 经挑战后的修正
│   ├── causalLoopDiagram: CausalLoopDiagram | None
│   │   ├── nodes: list[CLDNode]
│   │   └── loops: list[CLDLoop]       # R1/R2 (reinforcing), B1/B2 (balancing)
│   └── dataValidation: DataValidation
│       ├── changePointDetected: bool
│       ├── sentimentTimeSeries: list[SentimentPoint]
│       └── economicIndicators: list[EconomicIndicator]
└── dialecticalConfidence: str         # 总体辩证法分析的置信度
```

### 阶段四：HistoricalPositioning

```
HistoricalPositioning
├── phaseSummary: str
├── events: list[EventHistorical]
│   ├── eventId: str
│   ├── productiveForces: str              # 生产力维度分析
│   ├── productionRelations: str           # 生产关系维度分析
│   ├── baseStructure: str                 # 经济基础定位
│   ├── superstructure: str                # 上层建筑定位
│   ├── classForceComparison: str          # 阶级力量对比变化
│   └── historicalPosition: str            # 历史方位——在更长时段中的位置
├── crossCuttingSynthesis: CrossCuttingSynthesis
│   ├── epochThemes: list[EpochTheme]      # 贯穿事件的时代主题
│   │   ├── name: str
│   │   ├── description: str
│   │   ├── eventIds: list[str]
│   │   └── dialecticalSignificance: str
│   ├── contradictionLandscape: str        # 矛盾运动总景观——事件间如何相互影响
│   ├── systemArchetypes: list[SystemArchetype]  # 匹配的系统原型
│   │   ├── archetype: str                 # FixesThatFail | LimitsToGrowth | ShiftingTheBurden | TragedyOfCommons
│   │   ├── description: str
│   │   └── leveragePoint: str             # 系统的杠杆点
│   └── hiddenConnections: list[HiddenConnection]  # 非显见关联
│       ├── eventIdA: str
│       ├── eventIdB: str
│       ├── connectionType: str            # "因果链" | "共享结构驱动" | "潜在联盟动态"
│       └── reasoning: str
└── historicalAnalogies: list[HistoricalAnalogy]
    ├── analogousEvent: str
    ├── similarity: str
    ├── difference: str
    └── lesson: str
```

### 阶段五：PracticeOrientation

```
PracticeOrientation
├── overallJudgment: str                   # 本周矛盾运动总判断
├── scenarios: list[Scenario]              # 3 情景
│   ├── type: "baseline"|"alternative"|"wildcard"
│   ├── description: str
│   ├── probability: str                   # 概率区间 (e.g. "55-80%")
│   ├── conditions: str                    # 此情景发生的条件
│   ├── leadingIndicators: list[str]       # 先行指标
│   └── implications: str
├── practiceSignificance: str              # 对读者理解当下社会的帮助
├── signalsToWatch: list[WatchSignal]
│   ├── signal: str                        # 可观测的具体信号
│   ├── ifObserved: str                    # 如果出现则说明什么
│   ├── ifNotObserved: str                 # 如果不出现则说明什么
│   └── deadline: str | None               # 预期观测时间窗口
└── lastWeekCalibration: LastWeekCalibration | None
    ├── correctJudgments: list[str]
    ├── incorrectJudgments: list[str]
    ├── brierScore: float | None
    ├── calibrationNotes: str
    └── adjustmentsForThisWeek: str
```

### 元数据与证据溯源

```
IssueMetadata
├── modelVersions: dict[str, str]       # 每个阶段使用的模型
├── verificationPasses: int             # 证据验证总次数
├── empiricalDegradations: list[str]    # 实证层哪些服务降级了
├── totalApiCost: float
├── runDuration: float
└── runId: str

EvidenceTrace
├── claims: list[TracedClaim]
│   ├── claimId: str
│   ├── claim: str
│   ├── phase: str                      # 来自哪个阶段
│   ├── confidence: "HIGH"|"MEDIUM"|"LOW"
│   ├── sources: list[TracedSource]
│   │   ├── sourceName: str
│   │   ├── sourceUrl: str | None
│   │   ├── reliability: str            # Admiralty A-F
│   │   └── credibility: int            # 1-6
│   ├── independentCorroborations: int  # 独立交叉验证数量
│   └── verificationMethod: str
└── totalVerifiedClaims: int
```

---

## 五、代码架构

### 目录结构

```
weekly-cli/
├── main.py                  # 五阶段编排器
├── config.py                # 环境变量、模型配置、路径配置
├── schema.py                # Pydantic v2 完整数据模型（所有 phase 模型）
├── merger.py                # 每阶段末尾的双层合并逻辑 + 不一致标注
├── retry.py                 # 退避重试 + 容错
├── quality.py               # 质量门控

├── dialectical/             # === 辩证分析层（核心，不可跳过）===
│   ├── __init__.py
│   ├── grasping.py          # Phase 1: 现象把握
│   ├── contradiction.py     # Phase 2: 矛盾识别
│   ├── unfolding.py         # Phase 3: 辩证展开
│   ├── positioning.py       # Phase 4: 历史定位 + 跨事件综合
│   └── practice.py          # Phase 5: 实践指向

├── empirical/               # === 实证检验层（辅助，可降级）===
│   ├── __init__.py
│   ├── verifier.py          # 证据验证：来源分级 + 交叉验证 + ACH
│   ├── scorer.py            # 9维评分：校准辩证判断
│   ├── adversary.py         # 多轮对抗审查：Devil's Advocate + 辩证综合
│   ├── quantitative.py      # GDELT + 情感分析 + 变点检测
│   ├── causal.py            # 因果循环图 + 系统原型匹配
│   ├── connections.py       # 非显见关联 + PESTLE 交互矩阵
│   └── scenarios.py         # GBN 3 情景规划 + 先行指标

├── scraper/                 # === 数据抓取 ===
│   ├── __init__.py
│   ├── sources.py           # Weibo + Zhihu + HN 抓取
│   └── cache.py             # 缓存回退

├── narrative/               # === 叙事生成 ===
│   ├── __init__.py
│   └── article.py           # 按五阶段结构生成 Markdown 文章

├── prompts/                 # === 外部化提示词 ===
│   ├── __init__.py          # load_prompt 工具函数
│   ├── dialectical/
│   │   ├── grasping.json    # 阶段一：物质内容初判
│   │   ├── contradiction.json # 阶段二：矛盾识别
│   │   ├── unfolding.json   # 阶段三：三规律展开
│   │   ├── positioning.json # 阶段四：历史定位
│   │   └── practice.json    # 阶段五：实践指向
│   └── empirical/
│       ├── verifier.json    # 证据验证
│       ├── adversary.json   # 对抗审查
│       └── quantitative.json # 定量数据
│   └── narrative/
│       └── article.json     # 叙事提示词

└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_schema.py
    ├── dialectical/
    │   ├── test_grasping.py
    │   ├── test_contradiction.py
    │   ├── test_unfolding.py
    │   ├── test_positioning.py
    │   └── test_practice.py
    ├── empirical/
    │   ├── test_verifier.py
    │   ├── test_scorer.py
    │   ├── test_adversary.py
    │   └── test_quantitative.py
    └── test_merger.py
```

### 模块接口规范

每个辩证模块遵循统一接口：

```python
def analyze_<phase>(client: DeepSeekClient, input: PhaseInput) -> PhaseOutput:
    """执行该阶段的辩证分析。"""
```

每个实证模块遵循统一接口：

```python
def verify_<phase>(dialectical_output: PhaseOutput, context: dict) -> EmpiricalOutput | None:
    """对辩证分析进行实证检验。失败时返回 None（可降级）。"""
```

合并器接口：

```python
def merge(dialectical: PhaseOutput, empirical: EmpiricalOutput | None) -> MergedOutput:
    """合并辩证层和实证层的输出，标注不一致处。"""
```

### 关键设计约束

| 约束 | 说明 |
|------|------|
| **辩证层不可跳过** | 即使 LLM 调用失败，辩证层骨架不能省略——降级时标注"本段因技术原因简化" |
| **实证层可降级** | 任一部分失败不影响流水线继续，只标注"实证数据缺失" |
| **每阶段末尾强制合并** | 合并器显式标注辩证层与实证层的不一致 |
| **证据溯源贯穿全链** | 每个分析断言记录其证据来源、分级和交叉验证状态 |
| **负向风格指令贯穿所有提示词** | 禁止辩证术语堆砌、禁止标签化、禁止跳过辩证推理直接给结论 |
| **枚举值验证 + sanitize** | 所有枚举字段有模糊修正，AI 输出做 clamp 和清理 |

### 合并器设计细节

合并器（`merger.py`）在每个阶段末尾运行，将辩证层和实证层输出合并为统一结果。合并规则：

1. **实证层确认辩证判断**：直接合并，标注 `empiricalVerified: true`
2. **实证层质疑辩证判断**：两者均保留在合并输出中，显式标注分歧——"辩证分析认为 X，但实证检验发现 Y"
3. **实证层缺失（降级）**：只输出辩证层结果，标注 `empiricalDegraded: true`
4. **实证层发现辩证层遗漏的内容**：追加到合并输出，标注 `empiricalSupplemental`

> 合并器不解决分歧，只标注分歧——判断是读者的任务。

### 模型路由策略

| 任务类型 | 模型 | 原因 |
|---------|------|------|
| 辩证分析层（所有阶段） | deepseek-v4-pro (thinking=true) | 需要最强的辩证推理能力 |
| 实证检验层（9维评分） | deepseek-v4-flash | 轻量提取任务 |
| 实证检验层（对抗审查） | deepseek-v4-pro (thinking=true) | 需要强批判性推理 |
| 实证检验层（定量数据解读） | deepseek-v4-flash | 描述性任务 |
| 叙事生成 | deepseek-v4-pro (thinking=false) | 需要高质量中文写作 |

---

## 六、提示词体系

### 提示词设计原则

每个辩证提示词的五要素：

1. **方法论定位**：本阶段在认识运动中的位置
2. **辩证方法**：本阶段应用的辩证范畴和规律
3. **分析要求**：从辩证角度切入的具体分析要求
4. **负向风格指令**：禁止套话、标签、跳过推理
5. **输出格式**：结构化 JSON schema

### 负向风格指令（贯穿所有提示词）

```
❌ 禁止堆砌辩证术语（剥削、压迫、辩证法、阶级斗争、矛盾运动等词汇不能作为空洞修饰语使用——每次使用必须有具体指向）
❌ 禁止贴阶级标签（不能说"这体现了资产阶级立场"——必须说清楚在什么具体条件下谁得到了什么、谁失去了什么）
❌ 禁止跳过辩证推理直接给结论（不能说"这是劳资矛盾的体现"——必须从具体事实出发，一步一步展示矛盾如何形成）
❌ 禁止空洞的"反映了""揭示了""体现了"（这些词后面必须有具体的、可验证的内容）
❌ 禁止 balance-both-sides（不能"一方面...另一方面..."摇摆不定——必须分析后给出清晰的判断）
❌ 禁止用理论脑补缺失的证据（证据不足时如实说证据不足，不要用哲学语言填充）
```

### 提示词文件清单

| 文件 | 对应模块 | 核心指令 |
|------|---------|---------|
| `prompts/dialectical/grasping.json` | `dialectical/grasping.py` | 物质内容初判、去伪存真 |
| `prompts/dialectical/contradiction.json` | `dialectical/contradiction.py` | 提取矛盾结构、利益格局 |
| `prompts/dialectical/unfolding.json` | `dialectical/unfolding.py` | 三规律逐条展开 |
| `prompts/dialectical/positioning.json` | `dialectical/positioning.py` | 历史唯物主义定位 + 跨事件综合 |
| `prompts/dialectical/practice.json` | `dialectical/practice.py` | 实践指向、信号生成 |
| `prompts/empirical/verifier.json` | `empirical/verifier.py` | 证据分级、交叉验证、ACH |
| `prompts/empirical/adversary.json` | `empirical/adversary.py` | Devil's Advocate 对抗审查 |
| `prompts/empirical/quantitative.json` | `empirical/quantitative.py` | 定量数据解读 |
| `prompts/narrative/article.json` | `narrative/article.py` | 按五阶段组织叙事 |

---

## 七、输出格式

### JSON 输出

完整结构化数据（包含所有阶段的输出、证据溯源和元数据），写到 `BLOG_CONTENT_DIR/{weekId}.json`。

JSON 格式严格遵循 Pydantic 模型的 schema，所有字段完整输出，证据溯源全链可追溯。

### Markdown 文章输出

写到 `BLOG_CONTENT_DIR/../posts/{weekId}/index.md`。文章按五阶段认识运动组织：

```
---
title: 辩证周报 2026-WXX
published: YYYY-MM-DD
description: 本周 X 个事件的辩证分析，核心矛盾是...
category: 辩证周报
tags: [...]
---

# 辩证周报 2026-WXX

> 日期范围 | 本周 X 个事件

## 一、现象
（本周看到了什么——仍是感性阶段）
- 入选事件速览（每个 1-2 句）
- 排除了什么及原因
- 来源质量

## 二、矛盾
（从现象到本质的第一次飞跃）
- 逐事件矛盾识别
  - 主要矛盾
  - 矛盾的主要方面
  - 物质利益格局
- **与替代解释的对比**（实证层 ACH 的发现）

## 三、展开
（辩证法的核心——三规律逐事件展开）
- 逐事件分析：
  - 对立统一：同一性 → 斗争性 → 特殊性
  - 量变质变：阶段 → 方向 → 度
  - 否定之否定：轨迹 → 方向
- **对抗审查的发现**（实证层）
- **数据的印证与质疑**（实证层）

## 四、定位
（从具体事件上升到历史高度）
- 本周的时代主题
- 矛盾运动总景观
- 生产力-生产关系、经济基础-上层建筑
- 阶级力量对比
- **隐藏的关联**（实证层）
- **历史类似事件**（实证层）

## 五、方向
（回归实践）
- 总的判断
- 三种情景（Baseline / Alternative / Wildcard）
  - 每种有概率区间 + 条件 + 先行指标
- 下周关注的具体信号
- **上周判断的校准**（实证层）

---

*本文由 [格物](https://github.com/dreamnight16/gewu)
分析系统自动生成，以唯物辩证法和历史唯物主义为方法论核心。*
*所有判断均标注证据来源、置信度和不确定性。*
*[查看完整证据溯源](link-to-json)*
```

### 关键输出设计约束

- 确认事实与辩证判断在排版上区分（确认事实用正常字体，辩证判断用缩进斜体 + 置信度标签）
- 每个分析断言至少有一个可追溯的证据来源
- 不确定性用 [HIGH] / [MEDIUM] / [LOW] 标签显式标注

---

## 八、测试策略

### 测试层级

| 层级 | 范围 | 工具 |
|------|------|------|
| 单元测试 | 每个模块函数的独立测试 | pytest |
| 集成测试 | 辩证层 + 实证层 + 合并 → 完整阶段 | pytest + DEEPSEEK_API_KEY |
| 端到端测试 | 完整五阶段流水线 | pytest + 样本输出验证 |
| Schema 测试 | Pydantic 模型验证、枚举 sanitize | pytest (单元级) |

### 测试覆盖率目标

- 辩证层：≥ 85%
- 实证层：≥ 80%（可降级的部分可以稍低）
- Schema：100%（模型验证逻辑全覆盖）
- 合并器：100%（不一致标注逻辑必须全覆盖）

### Pytest 标记

```python
@pytest.mark.unit       # 不需要 API key
@pytest.mark.integration # 需要 DEEPSEEK_API_KEY
@pytest.mark.slow       # 完整 E2E 测试，CI 中按需运行
```

---

## 九、迁移策略

### 与当前系统的关系

| 旧组件 | 迁移方式 |
|--------|---------|
| `schema.py` | 全量重写为五阶段 Pydantic 模型 |
| `main.py` | 全量重写为五阶段编排器 |
| `censor.py` | 废弃 → 替换为 `dialectical/grasping.py` |
| `scorer.py` | 废弃 → 评分逻辑移入 `empirical/scorer.py` |
| `analyzer.py` | 拆分为 `dialectical/unfolding.py` + `empirical/adversary.py` |
| `synthesizer.py` | 合并入 `dialectical/positioning.py` |
| `article.py` | 重写为 `narrative/article.py`（五阶段叙事结构） |
| `search.py` | 保留，作为实证层的数据来源之一 |
| `cache.py` | 保留，几乎不变 |
| `config.py` | 扩展模型配置和路由策略 |
| `utils.py` | 保留并扩展 |
| `prompts/` | 全量重写（按五阶段 + 双层结构重新设计） |

### 兼容性

- GitHub Actions 工作流保留结构，只更新依赖和执行命令
- Blog-mizuki 端渲染逻辑需要适配新的 JSON schema（文章结构变化）
- 旧版 JSON 输出不向前兼容——视为全新系统

---

## 十、风险与缓解

| 风险 | 缓解 |
|------|------|
| 五阶段 LLM 调用过多导致成本大幅上升 | 实证层用 flash 模型降低成本；对抗审查仅在置信度低时触发 |
| 辩证提示词过于复杂导致 LLM 不遵循 | 每个提示词分多步分解执行（先回答子问题再合成），结构化 JSON schema 约束输出 |
| 实证层服务（GDELT、情感分析）不稳定 | 每个实证模块有独立异常处理，失败返回 None 不阻断流水线 |
| 首次实现时辩证分析质量不如预期 | 用 sample_weekly.json 做 A/B 对比测试，与旧版输出直接比较 |

---

## 附录 A：术语对照

| 中文 | 对应代码/模块名 |
|------|----------------|
| 现象把握 | `PhenomenonGrasping` / `dialectical/grasping.py` |
| 矛盾识别 | `ContradictionIdentification` / `dialectical/contradiction.py` |
| 辩证展开 | `DialecticalUnfolding` / `dialectical/unfolding.py` |
| 历史定位 | `HistoricalPositioning` / `dialectical/positioning.py` |
| 实践指向 | `PracticeOrientation` / `dialectical/practice.py` |
| 对立统一 | `UnityOfOpposites` |
| 量变质变 | `QuantityQuality` |
| 否定之否定 | `NegationOfNegation` |
| 物质利益格局 | `InterestStructure` |
| 阶级力量对比 | `ClassForceComparison` |
| 证据溯源 | `EvidenceTrace` |
| 冲突验证 | `AdversarialReview` |
| 因果循环图 | `CausalLoopDiagram` |
| 系统原型 | `SystemArchetype` |

## 附录 B：与旧系统的关键差异

| 维度 | 旧系统 v1 | 新系统 v2 |
|------|----------|----------|
| 核心方法论 | MLM 阶级分析（一个视角） | 唯物辩证法 + 历史唯物主义（整个认识路线） |
| 流水线组织 | 按任务类型（抓取→过滤→评分→分析→综合） | 按认识运动（现象→矛盾→展开→定位→实践） |
| 评分模型 | 2 维（impact × info_gain） | 9 维 + 辩证矛盾判断（辩证为主，评分为辅） |
| LLM 调用 | 单次生成 | 多轮（生成→对抗→综合→精炼→打磨） |
| 证据处理 | AI 自评（无外部验证） | Admiralty 来源分级 + 独立交叉验证 + ACH |
| 定量数据 | 无 | GDELT + 情感时序 + 变点检测 |
| 输出结构 | 固定模板 | 按五阶段认识运动组织 |
| 不确定性 | 不标注 | [HIGH]/[MEDIUM]/[LOW] 显式标注 |
| 校准机制 | 无 | 每周回溯 + 校准评分 |
