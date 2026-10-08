# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — 采用 DreamNight Design Language (DNDL v1.0)

- **品牌统一重设计**：按 DNDL v1.0（实现版本 1.1.0）重做界面。
  `tokens.css` / `materials.css` / `motion.css` / `LICENSE` 以确定版本逐字节引入，
  另附 `VERSION` 记录来源仓库与 commit，五个文件保持同级关系；未就地改动任何品牌数值。
- **几何与排版**：默认直角、大面积品牌实色块、Display 级排版取代装饰性容器堆叠。
- **可读性**：色块正文统一使用 `--dn-text-on-color`，浅色底次要小字使用 `--dn-text-secondary`；
  按 WCAG 实测逐项核验对比度，不以元素级 opacity 淡化文字。
- **无障碍**：交互目标取 `--dn-target-min`；焦点可见；支持 `prefers-reduced-motion`、
  关闭透明与 `forced-colors` 回退；状态不再只靠颜色传达。
- **信息架构**：页面结构与导航按产品真实内容重做（非仅换色）。


### Added — 格物 v3 证据层与分析闭环

- **证据前置**：新增 `evidence/` 模块（sources / claims / collector / store）。
  Phase 0.5 在任何分析之前为每个候选事件建立事实档案：多维查询扩展、正文抓取、
  来源指纹、转载识别。分析阶段改为读取证据档案，而非标题与热搜排名。
- **断言类型化**：`FACT` / `ATTRIBUTED` / `INFERENCE` / `HYPOTHESIS` /
  `VALUE_JUDGMENT` / `UNKNOWN`，配合 `UNVERIFIED` / `SINGLE_SOURCE` /
  `CORROBORATED` / `CONTRADICTED` 验证状态。
- **确定性发布门禁**：`publication_gate()` 返回 ALLOW / DEGRADE / BLOCK，
  检查悬空证据引用、未修正的高风险断言与证据充分性。另有正文级安全网
  `sanitize_narrative()`。
- **验证闭环**：verifier 与 adversary 改为输出结构化处置
  （`KEEP`/`QUALIFY`/`REWRITE`/`REMOVE`/`RESEARCH`），
  `narrative/revision.py` 将其确定性地应用到分析文本，最多两轮。
- **事件追踪**：`tracking/events.py` 提供稳定 `eventId`、事件聚类、
  跨周状态（新发生/持续发展/出现反转/基本结束/待观察）与判断修订记录。
- **内容回归评测**：`evaluation/` 含 66 个案例（62 个取自历史真实产出）
  与五项指标，已接入 CI。

### Changed

- 文章生成改为由**已验证断言清单**驱动的 LLM 叙事，输入为断言账本而非原始分析输出；
  生成后经 `scan_text_risk` 复核，异常时回退模板渲染。
- `phase3` 不再硬编码为 `None`。此前 Phase 3 的全部成果（含对抗审查）
  从未进入 Markdown 文章。
- 三大规律可按 `applicable=false` 省略；`currentPhase` 与 `direction`
  新增 `证据不足` 取值。
- 矛盾分析新增 `principalContradictionUncertain`、`potentialContradictions`、
  `commonInterests`，利益结构新增 `relationshipType`（现实对抗/潜在差异/共同利益）。
- `SourceGrade` 缺省值由 `C3` 改为 `UNVERIFIED/6`：未评估不再伪装成已评估。
- `_fuzzy_fix_enum` 改为大小写不敏感。
- 事件聚类在抓取阶段完成，`sourcePlatform` 随抓取结果透传。

### Fixed

- 对抗审查结论不再被丢弃：`requiredCorrection` 类的意见现在会真正改写正文。
- 数值分歧检测改为在剥离数字后比较句子，"30% vs 70%" 一类冲突可被识别。

### Added — 格物 v2

- 格物 v2 五阶段辩证认识运动 pipeline: Phase 1 现象把握 (phenomenon grasping), Phase 2 矛盾识别 (contradiction identification), Phase 3 辩证展开 (dialectical unfolding) with adversarial review, Phase 4 历史定位 (historical positioning) with cross-event synthesis, Phase 5 实践导向 (practice orientation) — judgment, scenarios, signals, calibration
- Empirical layer: verifier, scorer, and quantitative modules, causal loop diagrams, hidden connections, and scenario planning
- Model routing, dual-layer merger, and v2 quality gates
- Complete Pydantic v2 data models for 格物 v2
- Dialectical layer and empirical layer prompt templates for all 5 phases
- 30 new tests covering utils, quality, cache, and quantitative modules

### Changed

- Renamed project to 格物 (Dianalyze); completed migration from v1 to gewu v2 (old v1 code removed)
- Extracted scraper and cache into a `scraper/` module
- Switched chinese-scraper-utils to a git install for thinking-mode support

### Fixed

- Added defensive AI-output sanitization layer to prevent pipeline crashes
- Coerced LLM integer IDs to strings and float credibility to int in grasping; float-to-int coercion for numeric schema fields plus probability string parsing
- Wrapped dialectical-phase `chat_json` calls in try-except for graceful LLM failure; increased all phase `max_tokens` to 32k to prevent JSON truncation

## [v0.3.1] - 2026-06-05

### Security

- Sanitized LLM inputs: strip control characters from search results before prompt injection
- Pinned chinese-scraper-utils to an exact version (`==0.2.6`)
- Added a bandit security-scan step to CI
- Removed the fake test-key fallback in the client fixture

### Added

- Community health files: CODE_OF_CONDUCT.md, SECURITY.md, CONTRIBUTING.md, .editorconfig
- Issue and PR templates under `.github/`
- Multi-language READMEs (English, 简体中文, 繁體中文, 日本語)
- `pyproject.toml` with project metadata

### Changed

- Pointed weekly output to Blog-mizuki instead of myBlog

### Fixed

- Removed the deprecated license classifier (PEP 639)
- Corrected the CI branch to `master`

### Removed

- PyPI publish job on tag push (added and subsequently reverted within this release)

## [v0.3.0] - 2026-05-24

### Added

- Typed pipeline models: `RawEvent`, `CensoredEvent`, `ScoredEvent` Pydantic models
- Offline mock tests for the analyzer (no API key required)
- CI workflow running pytest on Python 3.11 / 3.12 / 3.13

### Fixed

- Test assertion bug: corrected Literal value in analyzer test (`"反驳"` → `"矛盾"`)

## [v0.1.1] - 2026-05-24

### Security

- Fixed 9 issues from the code audit: search results wrapped in XML boundaries with an anti-injection guard in the analyzer; `BLOG_CONTENT_DIR` path validation (home-dir check, removed hardcoded username); exponential-backoff retry (replacing fixed 3s); `max_length` constraints on all schema fields

### Added

- MIT LICENSE
- Related-projects section to the README

### Changed

- Migrated to chinese-scraper-utils v0.2.1 — use library APIs for scraping and search
- Switched to the cn-scraper-utils DeepSeekClient and replaced hardcoded UA strings with `random_ua()`

### Fixed

- Censor review now defaults to an empty list on failure instead of passing everything through
- JSON parsing failure falls back and retries; a clear error is raised after two failures
- Missing API key now fails fast at startup
- Added a 3-second wait between retries
- Hacker News scraping switched to 5-thread concurrency
- README test badge count

### Removed

- Superpowers skill-generated docs and Claude-generated files

## [v0.1.0] - 2026-05-20

### Added

- Weekly hotspot CLI scaffold: data models and project structure
- DeepSeek API client wrapper with JSON mode
- Phase 0 political review filter, Phase 1 scoring and selection, Phase 2 per-event deep analysis
- Orchestrator and sample weekly data
- Real Weibo/Zhihu scraping to replace AI-hallucinated content
- DuckDuckGo web search before AI analysis
- Quality gate to filter out events with thin evidence
- International news source, compliance filter, and source-bias awareness
- README, .gitignore, and weekly CI workflow

### Changed

- Refactored to the MLM-MZT analytical framework — class analysis, dialectical scoring, contradiction edges
- Rewrote prompts to avoid template-filling and demand concrete dialectical analysis
- Auto-inject the JSON instruction into the system prompt for DeepSeek compatibility

### Fixed

- Replaced evidence hallucination with real scraped data
- JSON serialization now uses `by_alias=True` and correct sample `from_` keys
- Enforced enum-only values in the analyzer prompt
- Populated `classAnalysis` and `dialecticalSummary` in sample data
- Escaped Chinese quotes in sample JSON; quoted YAML keys and enforced LF line endings

[Unreleased]: https://github.com/dreamnight16/weekly-hotspot/compare/v0.3.1...HEAD
[v0.3.1]: https://github.com/dreamnight16/weekly-hotspot/compare/v0.3.0...v0.3.1
[v0.3.0]: https://github.com/dreamnight16/weekly-hotspot/compare/v0.1.1...v0.3.0
[v0.1.1]: https://github.com/dreamnight16/weekly-hotspot/compare/v0.1.0...v0.1.1
[v0.1.0]: https://github.com/dreamnight16/weekly-hotspot/releases/tag/v0.1.0
