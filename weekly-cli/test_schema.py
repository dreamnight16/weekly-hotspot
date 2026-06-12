import json
import pytest
from schema import WeeklyIssue, WeeklySynthesis, Event, ClassAnalysis

SAMPLE_EVENT: dict = {
    "id": "evt-1",
    "title": "测试事件",
    "impactScore": 4,
    "infoGainScore": 3,
    "summary": "这是一个测试事件的概述。",
    "classAnalysis": {
        "classNature": "资本扩张",
        "contradiction": "劳资矛盾",
        "historicalContext": "全球化退潮期",
    },
    "dialecticalSummary": "该事件体现了资本在追求利润过程中与劳动者的矛盾激化。",
    "timeline": [
        {
            "id": "tl-1",
            "time": "2026-05-18T10:00:00+08:00",
            "title": "首次报道",
            "description": "媒体首次报道此事。",
            "evidenceRefs": ["ev-1"],
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
            "aiReason": "来源权威，多方交叉验证一致。",
            "classBias": "无产阶级立场",
        }
    ],
    "edges": [
        {
            "from": "tl-1",
            "to": "ev-1",
            "type": "关联",
            "description": "该报道为时间线节点的信息来源。",
        }
    ],
}

SAMPLE_ISSUE = {
    "id": "2026-W21",
    "weekStart": "2026-05-18",
    "weekEnd": "2026-05-24",
    "events": [SAMPLE_EVENT],
}


@pytest.mark.unit
def test_event_validation():
    event = Event(**SAMPLE_EVENT)
    assert event.impactScore == 4
    assert event.timeline[0].title == "首次报道"
    assert event.evidence[0].authenticity == "真实"
    assert event.classAnalysis.contradiction == "劳资矛盾"
    assert len(event.dialecticalSummary) > 0


@pytest.mark.unit
def test_weekly_issue_validation():
    issue = WeeklyIssue(**SAMPLE_ISSUE)
    assert issue.id == "2026-W21"
    assert len(issue.events) == 1


@pytest.mark.unit
def test_invalid_score_rejected():
    try:
        Event(**{**SAMPLE_EVENT, "impactScore": 6})
        assert False, "Should have raised ValidationError"
    except Exception:
        pass


@pytest.mark.unit
def test_invalid_authenticity_rejected():
    try:
        bad_evidence = {
            **SAMPLE_EVENT["evidence"][0],
            "authenticity": "不确定",
        }
        bad_event = {**SAMPLE_EVENT, "evidence": [bad_evidence]}
        Event(**bad_event)
        assert False, "Should have raised ValidationError"
    except Exception:
        pass


@pytest.mark.unit
def test_json_roundtrip():
    issue = WeeklyIssue(**SAMPLE_ISSUE)
    json_str = issue.model_dump_json(indent=2, ensure_ascii=False, by_alias=True)
    parsed = WeeklyIssue(**json.loads(json_str))
    assert parsed.id == issue.id
    assert len(parsed.events) == 1
    # Edge alias: "from" in JSON maps to from_ in model
    assert parsed.events[0].edges[0].from_ == "tl-1"


@pytest.mark.unit
def test_class_analysis_default():
    ca = ClassAnalysis()
    assert ca.classNature == ""
    assert ca.contradiction == ""


@pytest.mark.unit
def test_weekly_issue_with_synthesis():
    syn = WeeklySynthesis(
        weeklyNarrative="本周多个事件反映了科技资本集中化趋势。",
        crossCuttingThemes=[],
        trends=[],
        contradictionsInMotion=[],
        globalAssessment="本周核心矛盾处于积累阶段。",
        dataGaps=["缺乏内部决策信息"],
    )
    issue = WeeklyIssue(
        id="2026-W24",
        weekStart="2026-06-08",
        weekEnd="2026-06-14",
        events=[Event(**SAMPLE_EVENT)],
        synthesis=syn,
    )
    json_str = issue.model_dump_json(indent=2, ensure_ascii=False, by_alias=True)
    parsed = WeeklyIssue(**json.loads(json_str))
    assert parsed.synthesis is not None
    assert len(parsed.synthesis.weeklyNarrative) > 10
    assert parsed.synthesis.globalAssessment == "本周核心矛盾处于积累阶段。"


@pytest.mark.unit
def test_weekly_issue_without_synthesis():
    """旧 JSON 不含 synthesis 字段也能解析。"""
    issue = WeeklyIssue(**SAMPLE_ISSUE)
    assert issue.synthesis is None


# ---- Cross-ID validation tests ----

@pytest.mark.unit
def test_cross_id_valid_event():
    """Valid event with consistent cross-references passes."""
    event = Event(**SAMPLE_EVENT)
    assert event.edges[0].from_ == "tl-1"


@pytest.mark.unit
def test_cross_id_invalid_edge_from():
    """Edge.from referencing nonexistent id raises ValueError."""
    bad = {**SAMPLE_EVENT, "edges": [{"from": "tl-nonexistent", "to": "ev-1", "type": "关联", "description": "bad"}]}
    with pytest.raises(ValueError, match="does not reference"):
        Event(**bad)


@pytest.mark.unit
def test_cross_id_invalid_edge_to():
    """Edge.to referencing nonexistent id raises ValueError."""
    bad = {**SAMPLE_EVENT, "edges": [{"from": "tl-1", "to": "ev-nonexistent", "type": "关联", "description": "bad"}]}
    with pytest.raises(ValueError, match="does not reference"):
        Event(**bad)


@pytest.mark.unit
def test_cross_id_invalid_evidence_ref():
    """Timeline evidenceRefs referencing nonexistent evidence raises ValueError."""
    bad_timeline = {
        **SAMPLE_EVENT["timeline"][0],
        "evidenceRefs": ["ev-nonexistent"],
    }
    bad = {**SAMPLE_EVENT, "timeline": [bad_timeline]}
    with pytest.raises(ValueError, match="does not reference"):
        Event(**bad)


@pytest.mark.unit
def test_cross_id_invalid_synthesis_event_id():
    """WeeklyIssue with synthesis referencing nonexistent event id raises."""
    event = Event(**SAMPLE_EVENT)
    syn = WeeklySynthesis(
        weeklyNarrative="测试",
        crossCuttingThemes=[{
            "name": "主题", "description": "描述",
            "relatedEventIds": ["evt-nonexistent"],
            "significance": "意义",
        }],
        trends=[],
        contradictionsInMotion=[],
        globalAssessment="评估",
        dataGaps=[],
    )
    with pytest.raises(ValueError, match="does not match any event id"):
        WeeklyIssue(
            id="2026-W99",
            weekStart="2026-01-01",
            weekEnd="2026-01-07",
            events=[event],
            synthesis=syn,
        )


@pytest.mark.unit
def test_cross_id_invalid_trend_event_id():
    """Trend evidenceEventIds with bad ref raises."""
    event = Event(**SAMPLE_EVENT)
    syn = WeeklySynthesis(
        weeklyNarrative="测试",
        crossCuttingThemes=[],
        trends=[{
            "name": "趋势", "description": "描述",
            "direction": "上升",
            "evidenceEventIds": ["evt-nonexistent"],
        }],
        contradictionsInMotion=[],
        globalAssessment="评估",
        dataGaps=[],
    )
    with pytest.raises(ValueError, match="does not match any event id"):
        WeeklyIssue(
            id="2026-W99",
            weekStart="2026-01-01",
            weekEnd="2026-01-07",
            events=[event],
            synthesis=syn,
        )


@pytest.mark.unit
def test_cross_id_invalid_contradiction_ids():
    """Contradiction eventsInvolved with bad ref raises."""
    event = Event(**SAMPLE_EVENT)
    syn = WeeklySynthesis(
        weeklyNarrative="测试",
        crossCuttingThemes=[],
        trends=[],
        contradictionsInMotion=[{
            "contradiction": "矛盾", "opposingForces": "双方",
            "eventsInvolved": ["evt-nonexistent"],
            "currentState": "对抗激化", "outlook": "走向",
        }],
        globalAssessment="评估",
        dataGaps=[],
    )
    with pytest.raises(ValueError, match="does not match any event id"):
        WeeklyIssue(
            id="2026-W99",
            weekStart="2026-01-01",
            weekEnd="2026-01-07",
            events=[event],
            synthesis=syn,
        )


@pytest.mark.unit
def test_synthesis_empty_refs_rejected():
    """Synthesis with empty relatedEventIds raises."""
    with pytest.raises(ValueError, match="relatedEventIds must not be empty"):
        WeeklySynthesis(
            weeklyNarrative="测试",
            crossCuttingThemes=[{
                "name": "主题", "description": "描述",
                "relatedEventIds": [],
                "significance": "意义",
            }],
            trends=[],
            contradictionsInMotion=[],
            globalAssessment="评估",
        )
