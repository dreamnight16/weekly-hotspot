# 格物 (Dianalyze) v3 — 证据层与分析闭环

本文说明 v3 在 v2 五阶段辩证框架之外增加的证据管理、验证闭环与发布控制。
五阶段认识方法、双模型路由、merger、GitHub Actions 与 Blog-mizuki 发布方式均保持不变。

## 一、v2 的真实数据流（以及它为什么不足以支撑深层分析）

```
Phase 0  抓取      → 标题 + "热搜第N名 · 热度 X" + URL
Phase 1  现象把握  → 只看到标题与热度（无检索）→ 产出 materialContent + sourceGrade
Phase 2  矛盾识别  → 输入是 Phase 1 的产物（仍无检索）
Phase 3  辩证展开  → 唯一检索环节，检索词 = 热点标题本身
Phase 4/5          → 汇总
发布               → narrative/article.py 纯模板渲染
```

三个实测问题：

1. **事实基础是标题加热度。** 微博摘要的内容就是排名与热度数字，Phase 1/2 不检索、不抓正文。
2. **框架被强制填满。** `unityOfOpposites` 四字段、`currentPhase`、`direction` 均为必填，
   提示词虽写了"证据不足时如实说明"，但输出结构里没有承载"证据不足"的位置。
   提示词说不许脑补，schema 要求必须脑补。
3. **验证不约束结论。** 对抗审查发现了问题，但 `main.py` 将 `phase3` 硬编码为 `None`，
   `_render_phase3` 因此从不执行；`requiredCorrection` 没有任何消费者。
   实测 2026-W41：文章里那句无证据的动机归因一字未改地发布了。

## 二、v3 数据流

```
Phase 0    抓取 + 事件聚类（稳定 eventId、topicAliases、firstSeenAt/lastSeenAt、eventStatus）
Phase 0.5  证据建档 evidence/  → 多维查询扩展 + 正文抓取 → SourceRecord[] → EvidenceDossier
Phase 1    现象把握（读证据档案；无来源时信源等级为 UNVERIFIED）
Phase 2    矛盾识别（允许无可确认的主要矛盾、共同利益、潜在矛盾）
Phase 3    辩证展开（复用同一份证据档案；三大规律可按 applicable=false 省略）
Phase 3.5  断言抽取 → 确定性分类 → verifier/adversary 复核 → 应用修订（最多 2 轮）
Phase 4/5  历史定位与实践导向
Phase 6    发布门禁（ALLOW / DEGRADE / BLOCK）+ 由已验证断言驱动的文章生成
```

## 三、核心模块

### `evidence/sources.py` — 来源与独立性

- 正文抽取使用标准库 `html.parser`，不引入抓取依赖；解析失败降级为仅用摘要。
- `contentFingerprint` 记录正文指纹，用于发现网页变化与内容重复。
- `mark_republications()` 把内容近似（字符 shingle Jaccard ≥ 0.7）的来源标记为
  `REPUBLISHED`：**五家媒体转发同一份通稿，只能算一个证据来源。**

### `evidence/claims.py` — 断言类型与风险分级

六种断言类型：`FACT` / `ATTRIBUTED` / `INFERENCE` / `HYPOTHESIS` / `VALUE_JUDGMENT` / `UNKNOWN`。

确定性规则（可回归测试，不依赖模型）：

| 规则 | 判定 |
|---|---|
| 动机动词（希望/试图/旨在/为了…）且无限定 | `HYPOTHESIS` / 高风险 |
| 同上但已有"可能/或许/据称" | `HYPOTHESIS` / 中风险 |
| 违法定性且非归属陈述，无限定 | `INFERENCE` / 高风险 |
| 具体数额（含"数亿元"等中文数量）且非归属陈述 | `INFERENCE` / 中或高风险 |
| 疑问句或"是否/未知/不明" | `UNKNOWN` |
| 显式带限定语 | `INFERENCE` |

**结构性激励不等于实际意图。** 分类器会在风险不明时向上归类：多限定一句的代价是
语气变弱，少限定一句的代价是把推测当事实发布。

`supporting_source_ids()` 实现"来源只能证明它实际支持的命题"：只有来源文本与断言
共享足够多的内容 bigram 才算支持。推断没有来源是正常结果，返回空列表而不是顺手猜一个。

### `narrative/revision.py` — 让验证真正生效

`KEEP` / `QUALIFY` / `REWRITE` / `REMOVE` / `RESEARCH` 五种处置直接改写分析文本。

- `REWRITE` 对动机归因采用**插入限定语**而非删除：
  "车企希望通过主动通报控制舆论" → "车企**可能**希望通过主动通报控制舆论"。
  分析得以保留，只有确定性改变。
- 删除会同时消灭错误与洞见，因此 `REMOVE` 只保留给确实无法成立的断言。
- 应用是确定性的。让模型自己应用自己的批评，等于在"发现问题"和"修复问题"之间
  再插入一个不可控的生成环节。

### `quality.py` — 发布门禁

门禁是确定性代码，不是又一次模型调用。

- **BLOCK**：存在未修正的高风险断言、悬空的证据引用（引用了不存在的 sourceId）、
  或来源明确互相矛盾。
- **DEGRADE**：证据基础薄弱（只有转载来源、来源间有分歧、或存在无来源支持的事实断言）。
  只发布事实、争议与待核实问题。
- **ALLOW**：关键事实可追溯，推断已标识，无未解决的严重问题。

`scan_text_risk()` / `sanitize_narrative()` 对**生成后的正文**再做一次句级风险扫描，
这是"写作者被要求不要夸大"与"写作者确实没有夸大"之间的区别。

### `tracking/events.py` — 事件身份与跨周修订

- 同一事件的不同标题聚为一个事件：以**标题前两字的施动者**为主键，
  再要求共享至少一个内容 bigram。两个事件误合并会凭空造出关系，比漏合并更糟，
  因此规则偏保守。
- `eventId` 由施动者 + 主题 token 派生，标题改写后仍然稳定。
- `detect_reversals()` 识别来源间新分歧与"辟谣/撤回/立案"类反转信号。
- 判断变化写入 `revisionLog`，并在文章中以"必须说明为什么改变"的形式呈现，
  而不是静默覆盖历史文章。

### `evaluation/` — 内容回归评测

66 个案例，其中 62 个由 `seed_cases.py` 从历史周报的真实产出中抽取，
4 个为针对性构造。指标：

| 指标 | 含义 |
|---|---|
| 无依据事实断言率 | FACT/ATTRIBUTED 中无来源支持的比例 |
| 错误动机归因率 | 未加限定的动机归因占比（**当前 0.000**） |
| 关键断言证据覆盖率 | 高风险断言中至少有一个来源的比例 |
| 严重错误拦截率 | 被检出并被改写的严重缺陷占比 |
| 有效分析保留率 | 修订后保留的文本比例（**当前 0.998**，防过度保守） |

评测在 CI 中执行且不需要 API key：检索不参与评测，否则比较提示词版本时
测到的会是搜索引擎的差异。

## 四、成本控制

分级计算，不让所有热点走完整流程：

- 只有 Phase 2 入选事件（≤ `--max-dossiers`，默认 8）建立证据档案。
- 查询扩展固定 5 条（事实 / 原始声明 / 争议 / 背景 / 后续）。
- 每个事件最多抓取 `--max-page-fetches`（默认 4）篇正文，优先政府、法院、企业公告域名。
- 证据档案按源码指纹缓存在 `~/.cache/weekly-hotspot/dossiers/`；
  没有新信息的事件可跳过重复检索。
- 修订最多 `--max-revision-rounds`（默认 2）轮，且第二轮只重访仍有高风险断言的事件。

## 五、命令行

```bash
uv run python weekly-cli/main.py                    # 完整流水线
uv run python weekly-cli/main.py --dry-run          # 不写文件，只报告费用与判定
uv run python weekly-cli/main.py --max-page-fetches 0   # 只用检索摘要，不抓正文
uv run python weekly-cli/evaluation/runner.py       # 内容回归评测（CI 门禁）
uv run python weekly-cli/evaluation/seed_cases.py   # 从历史周报补充案例
```

## 六、兼容性

schema 变更为**纯增量**，并保留旧的默认值语义之外的唯一两处有意变更：

1. `SourceGrade.reliability` 的缺省值由 `"C"` 改为 `"UNVERIFIED"`，
   `credibility` 由 `3` 改为 `6`。未评估不再伪装成已评估。
2. 摘要注入长度由 200 字符提高到 400 字符。

其余新增字段（`eventId`、`topicAliases`、`evidence`、`revisionLog`、
`publicationGate` 等）均为可选，旧数据仍可解析。前端实际消费的
`events[].title` 与 `events[].summary` 未变。
