"""Tests for main.py — helpers, retry, quality gate, week utils."""
from unittest.mock import patch, MagicMock

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
