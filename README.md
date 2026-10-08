**Language:** [English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md)

# Dianalyze — Weekly Hotspot Evidence And Analysis

[![Tests](https://img.shields.io/badge/tests-70%20unit%20%2B%209%20integration-green)](https://github.com/dreamnight16/weekly-hotspot/actions)
[![Coverage](https://img.shields.io/badge/coverage-82%25-brightgreen)](https://github.com/dreamnight16/weekly-hotspot/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)

Collects weekly hotspot material and can optionally add structured analysis. The evidence-only path produces JSON and Markdown from fetched or cached source items without requiring a model provider. When analysis is enabled, the existing methodology adds verification, quantitative context, and scenario planning.

## Architecture

```
Weibo / Zhihu / Hacker News (real-time scrape)
  ↓ Fetch trending topics + deduplication
[Phase 0] Scrape & Cache
  ↓ Fall back to cache if all sources fail
[Phase 1] Optional relevance filter
  ↓ Exclude entertainment / politically sensitive content
[Phase 2] Optional scoring & selection
  ↓ Event impact × Information novelty → top 5-8
[Phase 3] Optional per-event analysis (parallel, 3 workers)
  ↓ DuckDuckGo + Bing search → Timeline + Evidence + Edges
[Phase 4] Cross-event Synthesis
  ↓ Themes + Trends + Contradictions in motion
Output → JSON + Markdown article → Blog-mizuki repo
```

## Project Structure

```
weekly-cli/            # Python CLI pipeline
  main.py              # Orchestrator: phases 0-6
  config.py            # Environment config + path safety
  schema.py            # Pydantic v2 models (phases, claims, evidence)
  merger.py            # Dual-layer (dialectical + empirical) merge
  quality.py           # Publication gate: ALLOW / DEGRADE / BLOCK
  search.py            # DuckDuckGo + Bing search with dedup

  scraper/             # Hot-topic scraping (Weibo / Zhihu / HN)
  evidence/            # Fact layer, runs BEFORE analysis
    sources.py         #   Source records, page fetch, republication detection
    claims.py          #   Claim typing, risk classification, hedging
    collector.py       #   Query expansion, retrieval, dossier assembly
    store.py           #   Dossier cache keyed on content fingerprints
  dialectical/         # Five-phase dialectical epistemology
    grasping.py contradiction.py unfolding.py positioning.py practice.py
  empirical/           # Verification, adversarial review, causal, scenarios
    verifier.py adversary.py causal.py connections.py scenarios.py scorer.py
  narrative/
    article.py         #   LLM narrative over the validated claim ledger
    revision.py        #   Applies KEEP/QUALIFY/REWRITE/REMOVE to the analysis
  tracking/events.py   # Stable event ids, clustering, cross-week revision

  evaluation/          # Content regression evaluation (runs in CI)
    cases/             #   Fixed case set mined from real weekly output
    runner.py metrics.py seed_cases.py

  prompts/             # Externalized LLM prompt templates
  tests/               # Unit tests for every module
```

### The evidence chain

格物 is built around one closed loop rather than a single pass:

```
现实事实 → 理论解释 → 竞争性假设 → 经验检验 → 判断修正 → 新的现实事实
```

Concretely: retrieval happens **before** analysis (Phase 0.5), every key
assertion carries a type and a verification status, an inference about
intent may be published only as a hypothesis, reviewer verdicts are applied
to the text rather than merely reported, and a deterministic gate decides
whether the result may be published at all. See
[docs/dianalyze-v3-evidence-layer.md](docs/dianalyze-v3-evidence-layer.md).

## Usage

### Manual

```bash
# Optional: enables the analysis phases
export DEEPSEEK_API_KEY=sk-your-key
export BLOG_CONTENT_DIR=/path/to/Blog-mizuki/src/content/weekly
cd weekly-cli && pip install -r requirements.txt && python main.py
```

### Automated (GitHub Actions)

Runs every Monday 00:00 UTC. Results pushed to Blog-mizuki repo.

Optional GitHub Secrets:
- `DEEPSEEK_API_KEY` — enables generated analysis; collection and evidence-only reports do not require it
- `pip install -r requirements-llm.txt` — optional model-analysis dependencies
- `BLOG_PAT` — Personal Access Token with write access to Blog-mizuki repo

## Tech Stack

- **Optional analysis**: DeepSeek API (deepseek-chat)
- **Backend**: Python 3 + Pydantic; OpenAI SDK is optional for model analysis
- **Frontend**: Astro 4 + React 18 + TypeScript + Tailwind CSS
- **Visualization**: react-force-graph-2d (D3-force)

## Related

- [chinese-scraper-utils](https://github.com/dreamnight16/chinese-scraper-utils) — Shared utilities used by this project
- [Blog-mizuki](https://github.com/dreamnight16/Blog-mizuki) — Weekly reports published at dreamnight.net.cn

---

<div align="center">

**Language / 语言 / 言語**

[**English**](README.md) | [**简体中文**](README.zh-CN.md) | [**繁體中文**](README.zh-Hant.md) | [**日本語**](README.ja.md)

</div>
