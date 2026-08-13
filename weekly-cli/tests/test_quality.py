"""Test quality gate functions using mock objects."""
import pytest
from types import SimpleNamespace
from quality import is_quality_event, is_quality_issue

CONTENT_OK = "这是一段足够长的辩证内容文本，用来满足质量门控的最低长度要求"


def _make_event(confidence="HIGH", title="测试事件", content=CONTENT_OK):
    return {
        "dialecticalConfidence": confidence,
        "title": title,
        "unityOfOpposites": {"对立面": content},
        "quantityQuality": {},
        "negationOfNegation": {},
    }


class TestIsQualityEvent:
    def test_valid_event_passes(self):
        assert is_quality_event(_make_event()) is True

    def test_low_confidence_rejected(self):
        assert is_quality_event(_make_event(confidence="LOW")) is False

    def test_no_dialectical_content_rejected(self):
        event = _make_event()
        event["unityOfOpposites"] = {}
        event["quantityQuality"] = {}
        event["negationOfNegation"] = {}
        assert is_quality_event(event) is False

    def test_short_dialectical_content_rejected(self):
        assert is_quality_event(_make_event(content="短")) is False

    def test_missing_title_rejected(self):
        assert is_quality_event(_make_event(title="")) is False


class TestIsQualityIssue:
    def _issue(self, events=None, phase1=True, phase2=True):
        issue = SimpleNamespace()
        issue.events = events or []
        issue.phase1 = SimpleNamespace() if phase1 else None
        issue.phase2 = SimpleNamespace() if phase2 else None
        return issue

    def test_valid(self):
        assert is_quality_issue(self._issue(events=[SimpleNamespace()])) is True

    def test_no_events(self):
        assert is_quality_issue(self._issue(events=[])) is False

    def test_no_phase1(self):
        assert is_quality_issue(self._issue(events=[SimpleNamespace()], phase1=False)) is False

    def test_no_phase2(self):
        assert is_quality_issue(self._issue(events=[SimpleNamespace()], phase2=False)) is False
