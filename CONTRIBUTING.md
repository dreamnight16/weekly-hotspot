# Contributing to Weekly Hotspot Analysis

Thanks for your interest in contributing!

## Getting Started

```bash
git clone https://github.com/dreamnight16/weekly-hotspot.git
cd weekly-hotspot
pip install -r weekly-cli/requirements.txt
export DEEPSEEK_API_KEY=sk-your-key
# Run unit tests (no API key needed for these)
pytest weekly-cli/ -v -m "unit"
# Run with coverage (minimum 80% required)
pytest weekly-cli/ -m "unit" --cov=weekly-cli --cov-fail-under=80
```

## Development Workflow

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Run `pytest -m "unit" --cov=weekly-cli --cov-fail-under=80` to verify
4. Add tests for new functionality (mark with `@pytest.mark.unit` or `@pytest.mark.integration`)
5. Commit using [Conventional Commits][conv] format
6. Push and open a pull request

## Commit Convention

```
feat: add CensoredEvent typed pipeline stage
fix: prevent search result injection in LLM prompt
refactor: replace raw dicts with Pydantic models
test: add offline mock tests for analyzer
docs: update pipeline architecture diagram
```

Types: `feat` `fix` `refactor` `test` `docs` `chore` `perf` `ci`

## Architecture

The pipeline has 5 stages:

```
Phase 0: Scrape (Weibo/Zhihu/HN) → dedup + cache
Phase 1: Censor (MLM relevance filter)
Phase 2: Score (impact × info gain → top N)
Phase 3: Analyze (DDG+Bing search → timeline + evidence + edges, parallel)
Phase 4: Synthesize (cross-event themes, trends, contradictions)
```

Output models (14 Pydantic v2 models) are defined in `schema.py`.
LLM prompts are externalized in `prompts/*.json`.

## Code Style

- Full type hints on all public functions
- Use Pydantic models for pipeline data
- Functions under 50 lines; files under 800 lines
- Follow PEP 8
- Use `logging` module, not `print()`

## Pull Request Checklist

- [ ] All unit tests pass (`pytest -m "unit"`)
- [ ] Coverage ≥ 80% (`--cov-fail-under=80`)
- [ ] Type hints added for new public APIs
- [ ] New tests added for new behavior
- [ ] Prompt changes reflected in `prompts/*.json`
- [ ] `.gitignore` updated if new secrets/output files added

## Questions?

Open a [discussion](https://github.com/dreamnight16/weekly-hotspot/discussions).

[conv]: https://www.conventionalcommits.org/
