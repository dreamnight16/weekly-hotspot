"""Tests for main.py — helpers, retry, quality gate, week utils."""
import json
from unittest.mock import patch

import pytest
from utils import get_week_id, get_week_range, retry_call
from main import parse_args, main


# ---- Week utility tests ----

@pytest.mark.unit
def test_get_week_id():
    wid = get_week_id()
    assert "-W" in wid
    parts = wid.split("-W")
    assert len(parts) == 2
    assert 2020 <= int(parts[0]) <= 2100
    assert 1 <= int(parts[1]) <= 53


@pytest.mark.unit
def test_get_week_range():
    start, end = get_week_range()
    assert "-" in start
    assert "-" in end
    from datetime import datetime
    s = datetime.strptime(start, "%Y-%m-%d")
    assert s.weekday() == 0  # Monday


# ---- Retry tests ----

@pytest.mark.unit
def testretry_call_success():
    calls = []

    def fn():
        calls.append(1)
        return "ok"

    result = retry_call(fn, phase="test", max_retries=2)
    assert result == "ok"
    assert len(calls) == 1


@pytest.mark.unit
def testretry_call_retry_then_succeed():
    call_count = {"n": 0}

    def flaky():
        call_count["n"] += 1
        if call_count["n"] < 2:
            raise ValueError("transient error")
        return "recovered"

    result = retry_call(flaky, phase="test", max_retries=3)
    assert result == "recovered"
    assert call_count["n"] == 2


@pytest.mark.unit
def testretry_call_all_fail():
    def always_fail():
        raise RuntimeError("persistent error")

    with pytest.raises(RuntimeError, match="persistent error"):
        retry_call(always_fail, phase="test", max_retries=2)


# ---- CLI argument tests ----

@pytest.mark.unit
def test_parse_args_defaults():
    args = parse_args([])
    assert args.dry_run is False
    assert args.verbose is False
    assert args.skip_scrape is False
    assert args.max_events == 8


@pytest.mark.unit
def test_parse_args_flags():
    args = parse_args(["--dry-run", "--verbose", "--skip-scrape", "--max-events", "5"])
    assert args.dry_run is True
    assert args.verbose is True
    assert args.skip_scrape is True
    assert args.max_events == 5


@pytest.mark.unit
def test_parse_args_short_flags():
    args = parse_args(["-v", "--dry-run"])
    assert args.verbose is True
    assert args.dry_run is True


# ---- Minimal main() dry-run test ----

@pytest.mark.unit
def test_main_dry_run_exits_cleanly_without_scraping():
    """main() with --dry-run --skip-scrape exits without error when no data."""
    with patch("main.load_cache") as mock_load:
        mock_load.return_value = None
        with pytest.raises(SystemExit) as exc:
            main(["--dry-run", "--skip-scrape"])
        assert exc.value.code == 1  # exits because no cache + no scrape


@pytest.mark.unit
@pytest.mark.parametrize("missing_sdk", [False, True])
def test_main_writes_evidence_report_without_model(tmp_path, monkeypatch, missing_sdk):
    """Collection and report output do not require a model key."""
    import main as main_module

    output_dir = tmp_path / "weekly"
    monkeypatch.setattr(main_module, "DEEPSEEK_API_KEY", "test-key" if missing_sdk else "")
    monkeypatch.setattr(main_module, "BLOG_CONTENT_DIR", output_dir)
    events = [{
        "title": "测试素材",
        "summary": "公开来源摘要",
        "sourceUrl": "https://example.com/source",
    }]

    with patch.object(main_module, "scrape_all", return_value=events), \
         patch.object(main_module, "DeepSeekClient", side_effect=ImportError("openai")):
        main_module.main([])

    json_files = list(output_dir.glob("*.json"))
    assert len(json_files) == 1
    payload = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert payload["metadata"]["modelVersions"] == {}
    assert payload["events"][0]["sourceUrl"] == "https://example.com/source"
    article = (tmp_path / "posts" / json_files[0].stem / "index.md").read_text(encoding="utf-8")
    assert "未进行模型分析" in article
    assert "https://example.com/source" in article


@pytest.mark.unit
@pytest.mark.parametrize("model_url", [None, "https://example.com/model-made-up"])
def test_model_stage_preserves_scraper_source_url(model_url):
    """Model-shaped events inherit provenance when the model omits it."""
    import main as main_module

    events = main_module._carry_source_urls(
        [{"id": "evt-1", "title": "测试素材", "summary": "改写后的摘要", "sourceUrl": model_url}],
        [{
            "id": "evt-1",
            "title": "测试素材",
            "summary": "原始摘要",
            "sourceUrl": "https://example.com/source",
        }],
    )

    assert events[0]["sourceUrl"] == "https://example.com/source"


@pytest.mark.unit
def test_evidence_report_keeps_cost_of_completed_model_calls(tmp_path, monkeypatch):
    import main as main_module

    monkeypatch.setattr(main_module, "BLOG_CONTENT_DIR", tmp_path / "weekly")
    main_module._write_evidence_report(
        [{"title": "测试素材"}], False, False, total_cost=0.25,
    )
    output = next((tmp_path / "weekly").glob("*.json"))
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["metadata"]["totalApiCost"] == 0.25
