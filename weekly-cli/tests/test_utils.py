"""Test utility functions (prevents 0% coverage on utils.py)."""
import pytest
from datetime import datetime
from utils import get_week_id, get_week_range, section_label, retry_call, is_quality


class TestGetWeekId:
    def test_returns_valid_format(self):
        wid = get_week_id()
        assert "-W" in wid
        year, week = wid.split("-W")
        assert 2020 <= int(year) <= 2100
        assert 1 <= int(week) <= 53


class TestGetWeekRange:
    def test_returns_7_day_range(self):
        start, end = get_week_range()
        s = datetime.strptime(start, "%Y-%m-%d")
        e = datetime.strptime(end, "%Y-%m-%d")
        assert (e - s).days == 6
        assert s.weekday() == 0  # Monday
        assert e.weekday() == 6  # Sunday


class TestSectionLabel:
    def test_chinese_labels(self):
        assert section_label(1) == "一"
        assert section_label(5) == "五"
        assert section_label(10) == "十"

    def test_fallback_to_number(self):
        assert section_label(11) == "11"
        assert section_label(0) == "零"


class TestRetryCall:
    def test_success_first_try(self):
        def ok(): return 42
        assert retry_call(ok, phase="test") == 42

    def test_retries_then_succeeds(self):
        calls = [0]
        def fail_then_ok():
            calls[0] += 1
            if calls[0] < 2:
                raise ValueError("fail")
            return "ok"
        assert retry_call(fail_then_ok, phase="test", max_retries=2) == "ok"

    def test_exhausts_retries(self):
        def always_fail(): raise RuntimeError("nope")
        with pytest.raises(RuntimeError):
            retry_call(always_fail, phase="test", max_retries=2)


class TestIsQuality:
    def test_quality_event_minimal(self):
        event = {
            "timeline": [{"id": "1"}, {"id": "2"}, {"id": "3"}],
            "evidence": [
                {"authenticity": "真实"}, {"authenticity": "存疑"}
            ],
            "dialecticalSummary": "这是一个足够长的辩证总结——至少有三十个字以上才能通过质量检查"
        }
        assert is_quality(event) is True

    def test_too_few_timeline(self):
        event = {"timeline": [{"id": "1"}], "evidence": [{"authenticity": "真实"}, {"authenticity": "真实"}], "dialecticalSummary": "x" * 30}
        assert is_quality(event) is False

    def test_too_few_evidence(self):
        event = {"timeline": [{"id": "1"}, {"id": "2"}, {"id": "3"}], "evidence": [], "dialecticalSummary": "x" * 30}
        assert is_quality(event) is False

    def test_no_verified_evidence(self):
        event = {
            "timeline": [{"id": "1"}, {"id": "2"}, {"id": "3"}],
            "evidence": [{"authenticity": "不实"}, {"authenticity": "不实"}],
            "dialecticalSummary": "x" * 30
        }
        assert is_quality(event) is False

    def test_short_summary(self):
        event = {
            "timeline": [{"id": "1"}, {"id": "2"}, {"id": "3"}],
            "evidence": [{"authenticity": "真实"}, {"authenticity": "真实"}],
            "dialecticalSummary": "太短"
        }
        assert is_quality(event) is False
