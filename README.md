**Language:** [English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md)

# Weekly Hotspot Analysis

[![Tests](https://img.shields.io/badge/tests-7%20passed%20%2B%207%20integration-green)](https://github.com/sixtdreanight/weekly-hotspot/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)

Grabs trending news every Monday, runs each story through DeepSeek for filtering, scoring, and deep analysis. Output: timelines, evidence chains, and relationship graphs as structured JSON. Rendered on the blog.

## Architecture

```
DeepSeek API (web search)
  ↓ Fetch weekly hot topic candidates
[Phase 0] Censorship filter
  ↓ Exclude sensitive content
[Phase 1] AI scoring & selection
  ↓ Event impact × Information novelty → top 5-8
[Phase 2] Per-event deep analysis
  ↓ Timeline + Evidence + Cause/Correlation/Contradiction
Output JSON → myBlog content collection
  ↓ Astro static build
Investigative report style pages
```

## Project Structure

```
weekly-cli/         # Python CLI
  main.py           # Orchestrator: fetch → censor → score → analyze → output
  config.py         # Environment variable config
  schema.py         # Pydantic data models
  client.py         # DeepSeek API wrapper
  censor.py         # Phase 0: Censorship filter
  scorer.py         # Phase 1: Scoring & selection
  analyzer.py       # Phase 2: Per-event deep analysis
  test_*.py         # Tests
docs/               # Design docs & implementation plans
```

## Usage

### Manual

```bash
export DEEPSEEK_API_KEY=sk-your-key
export BLOG_CONTENT_DIR=/path/to/myBlog/src/content/weekly
cd weekly-cli && pip install -r requirements.txt && python main.py
```

### Automated (GitHub Actions)

Runs every Monday 00:00 UTC. Results pushed to myBlog repo.

Required GitHub Secrets:
- `DEEPSEEK_API_KEY` — DeepSeek API key
- `BLOG_PAT` — Personal Access Token with write access to myBlog repo

## Tech Stack

- **AI**: DeepSeek API (deepseek-chat)
- **Backend**: Python 3 + openai SDK + Pydantic
- **Frontend**: Astro 4 + React 18 + TypeScript + Tailwind CSS
- **Visualization**: react-force-graph-2d (D3-force)

## Related

- [chinese-scraper-utils](https://github.com/sixtdreanight/chinese-scraper-utils) — Shared utilities used by this project
- [myBlog](https://github.com/sixtdreanight/myBlog) — Weekly reports published at dreamnight.net.cn

---

<div align="center">

**Language / 语言 / 言語**

[**English**](README.md) | [**简体中文**](README.zh-CN.md) | [**繁體中文**](README.zh-Hant.md) | [**日本語**](README.ja.md)

</div>
