# Contributing to Weekly Hotspot Analysis

Thanks for your interest in contributing!

## Getting Started

```bash
git clone https://github.com/sixtdreanight/weekly-hotspot.git
cd weekly-hotspot
pip install -r weekly-cli/requirements.txt
cp .env.example .env  # configure DEEPSEEK_API_KEY
pytest
```

## Development Workflow

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Run `pytest` to verify all tests pass
4. Add tests for new functionality
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

The pipeline has 4 stages:

```
Search (stage 0) → Censor (stage 1) → Analyze (stage 2) → Score (stage 3)
```

Each stage should pass typed Pydantic models, not raw dicts.

## Code Style

- Full type hints on all public functions
- Use Pydantic models for pipeline data
- Functions under 50 lines; files under 800 lines
- Follow PEP 8

## Pull Request Checklist

- [ ] All tests pass (`pytest`)
- [ ] Type hints added for new public APIs
- [ ] New tests added for new behavior
- [ ] Pipeline stage interfaces documented
- [ ] `.gitignore` updated if new secrets/output files added

## Questions?

Open a [discussion](https://github.com/sixtdreanight/weekly-hotspot/discussions).

[conv]: https://www.conventionalcommits.org/
