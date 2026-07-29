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
    """Edge.from referencing nonexistent id is sanitized (dropped)."""
    bad = {**SAMPLE_EVENT, "edges": [{"from": "tl-nonexistent", "to": "ev-1", "type": "关联", "description": "bad"}]}
    event = Event(**bad)
    # Edge with invalid from should be dropped, only valid edges remain
    assert len(event.edges) == 0, f"Expected 0 edges after sanitization, got {len(event.edges)}"


@pytest.mark.unit
def test_cross_id_invalid_edge_to():
    """Edge.to referencing nonexistent id is sanitized (dropped)."""
    bad = {**SAMPLE_EVENT, "edges": [{"from": "tl-1", "to": "ev-nonexistent", "type": "关联", "description": "bad"}]}
    event = Event(**bad)
    assert len(event.edges) == 0


@pytest.mark.unit
def test_cross_id_invalid_evidence_ref():
    """Timeline evidenceRefs to nonexistent evidence are cleaned."""
    bad_timeline = {
        **SAMPLE_EVENT["timeline"][0],
        "evidenceRefs": ["ev-nonexistent"],
    }
    bad = {**SAMPLE_EVENT, "timeline": [bad_timeline]}
    event = Event(**bad)
    # Invalid evidence ref should be removed
    assert event.timeline[0].evidenceRefs == []


@pytest.mark.unit
def test_cross_id_invalid_synthesis_event_id():
    """WeeklyIssue with synthesis referencing nonexistent event id is sanitized."""
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
    issue = WeeklyIssue(
        id="2026-W99",
        weekStart="2026-01-01",
        weekEnd="2026-01-07",
        events=[event],
        synthesis=syn,
    )
    # Invalid event ref should be dropped from the theme
    assert issue.synthesis is not None
    assert issue.synthesis.crossCuttingThemes[0].relatedEventIds == []


@pytest.mark.unit
def test_cross_id_invalid_trend_event_id():
    """Trend evidenceEventIds with bad ref is sanitized."""
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
    issue = WeeklyIssue(
        id="2026-W99",
        weekStart="2026-01-01",
        weekEnd="2026-01-07",
        events=[event],
        synthesis=syn,
    )
    assert issue.synthesis is not None
    assert issue.synthesis.trends[0].evidenceEventIds == []


@pytest.mark.unit
def test_cross_id_invalid_contradiction_ids():
    """Contradiction eventsInvolved with bad ref is sanitized."""
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
    issue = WeeklyIssue(
        id="2026-W99",
        weekStart="2026-01-01",
        weekEnd="2026-01-07",
        events=[event],
        synthesis=syn,
    )
    assert issue.synthesis is not None
    assert issue.synthesis.contradictionsInMotion[0].eventsInvolved == []


@pytest.mark.unit
def test_synthesis_empty_refs_dropped():
    """Synthesis items with empty relatedEventIds are silently dropped."""
    syn = WeeklySynthesis(
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
    assert len(syn.crossCuttingThemes) == 0


# ---- Sanitization tests (mode='before' validators) ----

@pytest.mark.unit
def test_sanitize_score_clamped():
    """Scores > 5 are clamped to 5."""
    event = Event(**{**SAMPLE_EVENT, "impactScore": 6, "infoGainScore": 0})
    assert event.impactScore == 5
    assert event.infoGainScore == 1  # clamped up


@pytest.mark.unit
def test_sanitize_missing_timeline_time():
    """Timeline node missing 'time' gets default '未知'."""
    bad_event = {**SAMPLE_EVENT}
    bad_event["timeline"] = [{
        "id": "tl-1",
        "title": "No time node",
        "description": "Missing time field",
        "evidenceRefs": ["ev-1"],
    }]
    event = Event(**bad_event)
    assert event.timeline[0].time == "未知"


@pytest.mark.unit
def test_sanitize_class_analysis_defaults():
    """ClassAnalysis with missing sub-fields gets empty defaults."""
    bad_event = {**SAMPLE_EVENT}
    bad_event["classAnalysis"] = {}
    event = Event(**bad_event)
    assert event.classAnalysis.classNature == ""
    assert event.classAnalysis.contradiction == ""
    assert event.classAnalysis.historicalContext == ""


@pytest.mark.unit
def test_sanitize_class_analysis_not_dict():
    """ClassAnalysis that is not a dict becomes default."""
    bad_event = {**SAMPLE_EVENT}
    bad_event["classAnalysis"] = "not a dict"
    event = Event(**bad_event)
    assert event.classAnalysis.classNature == ""
    assert event.classAnalysis.contradiction == ""


@pytest.mark.unit
def test_sanitize_evidence_enum_fixup():
    """Evidence with wrong enum values gets fuzzy fixed."""
    bad_event = {**SAMPLE_EVENT}
    bad_event["evidence"] = [{
        "id": "ev-1",
        "sourceType": "blog",  # not a valid value
        "sourceName": "测试",
        "content": "内容",
        "authenticity": "不确定",  # not a valid value
        "aiReason": "理由",
        "classBias": "工人阶级立场",  # not a valid value, but "无产阶级立场" is a substring? No
    }]
    event = Event(**bad_event)
    # sourceType falls back to "其他", authenticity to "待验证", classBias to "待判断"
    assert event.evidence[0].sourceType == "其他"
    assert event.evidence[0].authenticity == "待验证"
    assert event.evidence[0].classBias == "待判断"


@pytest.mark.unit
def test_sanitize_synthesis_direction_fixup():
    """Synthesis direction with wrong enum gets fixed."""
    syn = WeeklySynthesis(
        weeklyNarrative="测试",
        crossCuttingThemes=[],
        trends=[{
            "name": "趋势", "description": "描述",
            "direction": "隐性积累",  # AI confuses with currentState enum
            "evidenceEventIds": ["evt-1"],  # need at least one ref to survive
        }],
        contradictionsInMotion=[],
        globalAssessment="评估",
    )
    # "隐性积累" is in _DIRECTION_FIXUPS -> "缓和"
    assert syn.trends[0].direction == "缓和"


@pytest.mark.unit
def test_sanitize_synthesis_current_state_fixup():
    """Synthesis currentState with concatenated values gets fixed."""
    syn = WeeklySynthesis(
        weeklyNarrative="测试",
        crossCuttingThemes=[],
        trends=[],
        contradictionsInMotion=[{
            "contradiction": "矛盾", "opposingForces": "双方",
            "eventsInvolved": ["evt-1"],  # need at least one ref to survive
            "currentState": "外部对抗激化，内部隐性积累",  # known AI mistake
            "outlook": "走向",
        }],
        globalAssessment="评估",
    )
    # substring "对抗激化" matches
    assert syn.contradictionsInMotion[0].currentState == "对抗激化"


@pytest.mark.unit
def test_sanitize_synthesis_current_state_substring():
    """Synthesis currentState fixup via substring match."""
    syn = WeeklySynthesis(
        weeklyNarrative="测试",
        crossCuttingThemes=[],
        trends=[],
        contradictionsInMotion=[{
            "contradiction": "矛盾", "opposingForces": "双方",
            "eventsInvolved": ["evt-1"],  # need at least one ref to survive
            "currentState": "当前处于向新形态转化过程中",  # substring match
            "outlook": "走向",
        }],
        globalAssessment="评估",
    )
    assert syn.contradictionsInMotion[0].currentState == "向新形态转化"


@pytest.mark.unit
def test_sanitize_dialectical_summary_not_string():
    """dialecticalSummary that's not a string gets converted."""
    bad_event = {**SAMPLE_EVENT, "dialecticalSummary": 12345}
    event = Event(**bad_event)
    assert isinstance(event.dialecticalSummary, str)
    assert "12345" in event.dialecticalSummary
