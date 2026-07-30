**Language:** [English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md)

# Dianalyze — Dialectical Weekly Deep Analysis

[![Tests](https://img.shields.io/badge/tests-70%20unit%20%2B%209%20integration-green)](https://github.com/sixtdreanight/weekly-hotspot/actions)
[![Coverage](https://img.shields.io/badge/coverage-82%25-brightgreen)](https://github.com/sixtdreanight/weekly-hotspot/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)

Dialectical weekly news analysis powered by AI. Uses dialectical materialism and historical materialism as core methodology, supported by modern analytical techniques (evidence verification, quantitative data, scenario planning). Output: structured JSON + Markdown article. Rendered on blog.

## Architecture

```
Weibo / Zhihu / Hacker News (real-time scrape)
  ↓ Fetch trending topics + deduplication
[Phase 0] Scrape & Cache
  ↓ Fall back to cache if all sources fail
[Phase 1] Censorship Filter (MLM relevance)
  ↓ Exclude entertainment / politically sensitive content
[Phase 2] AI Scoring & Selection
  ↓ Event impact × Information novelty → top 5-8
[Phase 3] Per-event Deep Analysis (parallel, 3 workers)
  ↓ DuckDuckGo + Bing search → Timeline + Evidence + Edges
[Phase 4] Cross-event Synthesis
  ↓ Themes + Trends + Contradictions in motion
Output → JSON + Markdown article → Blog-mizuki repo
```

## Project Structure

```
weekly-cli/          # Python CLI pipeline
  main.py            # Orchestrator: 5-phase pipeline driver
  config.py           # Environment variable config + path safety
  schema.py           # Pydantic v2 data models (14 models)
  censor.py           # Phase 1: Censorship filter
  scorer.py           # Phase 2: Scoring & selection
  analyzer.py         # Phase 3: Per-event deep analysis
  search.py           # Parallel DuckDuckGo + Bing search with dedup
  synthesizer.py      # Phase 4: Cross-event synthesis
  article.py          # Markdown article generator
  cache.py            # Scrape cache fallback
  test_*.py           # Unit & integration tests (80%+ coverage)
prompts/              # Externalized LLM prompt templates

## Usage

### Manual

```bash
export DEEPSEEK_API_KEY=sk-your-key
export BLOG_CONTENT_DIR=/path/to/Blog-mizuki/src/content/weekly
cd weekly-cli && pip install -r requirements.txt && python main.py
```

### Automated (GitHub Actions)

Runs every Monday 00:00 UTC. Results pushed to Blog-mizuki repo.

Required GitHub Secrets:
- `DEEPSEEK_API_KEY` — DeepSeek API key
- `BLOG_PAT` — Personal Access Token with write access to Blog-mizuki repo

## Tech Stack

- **AI**: DeepSeek API (deepseek-chat)
- **Backend**: Python 3 + openai SDK + Pydantic
- **Frontend**: Astro 4 + React 18 + TypeScript + Tailwind CSS
- **Visualization**: react-force-graph-2d (D3-force)

## Related

- [chinese-scraper-utils](https://github.com/sixtdreanight/chinese-scraper-utils) — Shared utilities used by this project
- [Blog-mizuki](https://github.com/sixtdreanight/Blog-mizuki) — Weekly reports published at dreamnight.net.cn

---

<div align="center">

**Language / 语言 / 言語**

[**English**](README.md) | [**简体中文**](README.zh-CN.md) | [**繁體中文**](README.zh-Hant.md) | [**日本語**](README.ja.md)

</div>
