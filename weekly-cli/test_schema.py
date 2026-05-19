import json
from schema import WeeklyIssue, Event, TimelineNode, EvidenceNode, Edge

SAMPLE_EVENT = {
    "id": "evt-1",
    "title": "测试事件",
    "impactScore": 4,
    "infoGainScore": 3,
    "summary": "这是一个测试事件的概述。",
    "timeline": [
        {
            "id": "tl-1",
            "time": "2026-05-18T10:00:00+08:00",
            "title": "首次报道",
            "description": "媒体首次报道此事。",
            "evidenceRefs": ["ev-1"]
        }
    ],
    "evidence": [
        {
            "id": "ev-1",
            "sourceType": "官媒",
            "sourceName": "人民日报",
            "sourceUrl": "https://example.com/news/1",
            "content": "相关报道内容摘要。",
            "authenticity": "真实",
            "aiReason": "来源权威，多方交叉验证一致。"
        }
    ],
    "edges": [
        {
            "from": "tl-1",
            "to": "ev-1",
            "type": "关联",
            "description": "该报道为时间线节点的信息来源。"
        }
    ]
}

SAMPLE_ISSUE = {
    "id": "2026-W21",
    "weekStart": "2026-05-18",
    "weekEnd": "2026-05-24",
    "events": [SAMPLE_EVENT]
}


def test_event_validation():
    event = Event(**SAMPLE_EVENT)
    assert event.impactScore == 4
    assert event.timeline[0].title == "首次报道"
    assert event.evidence[0].authenticity == "真实"


def test_weekly_issue_validation():
    issue = WeeklyIssue(**SAMPLE_ISSUE)
    assert issue.id == "2026-W21"
    assert len(issue.events) == 1


def test_invalid_score_rejected():
    try:
        Event(**{**SAMPLE_EVENT, "impactScore": 6})
        assert False, "Should have raised ValidationError"
    except Exception:
        pass


def test_invalid_authenticity_rejected():
    try:
        bad_evidence = {**SAMPLE_EVENT["evidence"][0], "authenticity": "不确定"}
        bad_event = {**SAMPLE_EVENT, "evidence": [bad_evidence]}
        Event(**bad_event)
        assert False, "Should have raised ValidationError"
    except Exception:
        pass


def test_json_roundtrip():
    issue = WeeklyIssue(**SAMPLE_ISSUE)
    json_str = issue.model_dump_json(indent=2, ensure_ascii=False)
    parsed = WeeklyIssue(**json.loads(json_str))
    assert parsed.id == issue.id
    assert len(parsed.events) == 1
