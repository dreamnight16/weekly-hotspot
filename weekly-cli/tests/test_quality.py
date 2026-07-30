"""Test quality gate functions using mock objects."""
import pytest
from types import SimpleNamespace
from quality import is_quality_event, is_quality_issue

SUMMARY_OK = "这是一段足够长的辩证总结文字，必须要超过三十个字符才能通过质量门控的检查"


def _make_event(timeline_count=3, evidence_list=None, summary=SUMMARY_OK):
    ev = SimpleNamespace()
    ev.timeline = [SimpleNamespace(id=f"t{i}") for i in range(timeline_count)]
    ev.evidence = evidence_list or []
    ev.dialecticalSummary = summary
    return ev


def _make_evidence(authenticity="真实"):
    e = SimpleNamespace()
    e.authenticity = authenticity
    return e


class TestIsQualityEvent:
    def test_valid_event_passes(self):
        event = _make_event(3, [_make_evidence("真实"), _make_evidence("存疑")])
        assert is_quality_event(event) is True

    def test_too_few_timeline(self):
        event = _make_event(1, [_make_evidence("真实"), _make_evidence("真实")])
        assert is_quality_event(event) is False

    def test_too_few_evidence(self):
        event = _make_event(3, [_make_evidence("真实")])
        assert is_quality_event(event) is False

    def test_no_verified_evidence(self):
        event = _make_event(3, [_make_evidence("不实"), _make_evidence("不实")])
        assert is_quality_event(event) is False

    def test_summary_too_short(self):
        event = _make_event(3, [_make_evidence("真实"), _make_evidence("真实")], summary="太短")
        assert is_quality_event(event) is False


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
