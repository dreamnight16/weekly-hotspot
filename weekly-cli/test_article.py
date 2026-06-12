"""Tests for article.py — markdown generation, date formatting, labels."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from utils import section_label
from article import (
    _format_date_range,
    _tagline,
    _event_block,
    _synthesis_narrative,
    _diff_section,
    generate_article,
    load_last_week,
)
from schema import WeeklyIssue, WeeklySynthesis, Event
from conftest import SAMPLE_EVENT_DICT


@pytest.mark.unit
def test_format_date_range():
    result = _format_date_range("2026-05-18", "2026-05-24")
    assert "5月18日" in result
    assert "5月24日" in result
    assert "周" in result


@pytest.mark.unit
def test_format_date_range_invalid():
    result = _format_date_range("bad-date", "also-bad")
    assert result == "bad-date — also-bad"


@pytest.mark.unit
def test_tagline_empty():
    result = _tagline([])
    assert result is not None


@pytest.mark.unit
def test_tagline_high_impact():
    events = [
        {"impactScore": 5},
        {"impactScore": 4},
        {"impactScore": 5},
    ]
    result = _tagline(events)
    assert "密集" in result


@pytest.mark.unit
def test_tagline_low_impact():
    events = [
        {"impactScore": 1},
        {"impactScore": 2},
    ]
    result = _tagline(events)
    assert "相对平静" in result


@pytest.mark.unit
def testsection_label():
    assert section_label(1) == "一"
    assert section_label(2) == "二"
    assert section_label(10) == "十"
    assert section_label(0) == "零"


@pytest.mark.unit
def testsection_label_overflow():
    result = section_label(11)
    assert result == "11"


@pytest.mark.unit
def test_event_block_minimal(sample_event):
    result = _event_block(sample_event, 1)
    assert "## 1. 测试事件" in result
    assert "该事件体现了" in result
    assert "## 1. 测试事件" in result


@pytest.mark.unit
def test_event_block_full(sample_event):
    """Event block with all sections populated."""
    result = _event_block(sample_event, 2)
    assert "## 2. 测试事件" in result
    assert "谁得了什么、谁失了什么？" in result
    assert "矛盾在哪？" in result
    assert "这件事从哪来、往哪去？" in result
    assert "一句话" in result
    assert "怎么发展的" in result
    assert "信源" in result
    assert "脉络" in result


@pytest.mark.unit
def test_load_last_week_none(tmp_path):
    result = load_last_week(tmp_path, "2026-W01")
    assert result is None


@pytest.mark.unit
def test_synthesis_narrative(sample_synthesis):
    result = _synthesis_narrative(sample_synthesis, ["事件一", "事件二"])
    assert "这周发生了什么" in result
    assert "不止一件事" in result
    assert "风向在变" in result
    assert "底层的矛盾在怎么动" in result
    assert "总的来看" in result
    assert "还没看清楚的地方" in result


@pytest.mark.unit
def test_diff_section_new_and_continuing():
    this_syn = {
        "crossCuttingThemes": [
            {"name": "新主题"},
            {"name": "旧主题"},
        ]
    }
    last_week = {
        "events": [],
        "synthesis": {
            "weeklyNarrative": "上周综述",
            "crossCuttingThemes": [
                {"name": "旧主题"},
                {"name": "无关主题"},
            ]
        }
    }
    result = _diff_section(this_syn, last_week)
    assert "新出现的" in result
    assert "新主题" in result
    assert "在延续的" in result
    assert "旧主题" in result


@pytest.mark.unit
def test_diff_section_no_last_synthesis():
    this_syn = {"crossCuttingThemes": [{"name": "主题A"}]}
    last_week = {
        "events": [
            {"title": "旧事件"},
        ],
        "synthesis": None,
    }
    result = _diff_section(this_syn, last_week)
    assert "上周回顾" in result
    assert "旧事件" in result


@pytest.mark.unit
def test_generate_article_minimal(tmp_path, sample_event, sample_synthesis):
    """Generate article with 2 events + synthesis, verify structure."""
    event1 = Event(**sample_event)
    event2 = Event(
        id="evt-2",
        title="事件二",
        impactScore=3,
        infoGainScore=3,
        summary="事件二概述",
        classAnalysis={"classNature": "金融资本流动", "contradiction": "跨国资本与本土政策", "historicalContext": "全球加息周期"},
        dialecticalSummary="事件二辩证总结超过三十个字符的辩证总结确保通过质量门控",
        timeline=[
            {"id": "tl-2-1", "time": "2026-01-04T00:00:00", "title": "节点", "description": "描述", "evidenceRefs": ["ev-2-1"]},
            {"id": "tl-2-2", "time": "2026-01-05T00:00:00", "title": "节点B", "description": "描述B", "evidenceRefs": ["ev-2-1"]},
            {"id": "tl-2-3", "time": "2026-01-06T00:00:00", "title": "节点C", "description": "描述C", "evidenceRefs": ["ev-2-1"]},
        ],
        evidence=[
            {"id": "ev-2-1", "sourceType": "官媒", "sourceName": "央视", "content": "证据", "authenticity": "真实", "aiReason": "官方", "classBias": "待判断"},
            {"id": "ev-2-2", "sourceType": "其他", "sourceName": "分析", "content": "证据B", "authenticity": "存疑", "aiReason": "待核实", "classBias": "待判断"},
        ],
        edges=[
            {"from": "tl-2-1", "to": "tl-2-2", "type": "因果", "description": "关联"},
        ],
    )
    syn = WeeklySynthesis(**sample_synthesis)
    issue = WeeklyIssue(
        id="2026-W21",
        weekStart="2026-05-18",
        weekEnd="2026-05-24",
        events=[event1, event2],
        synthesis=syn,
    )
    weekly_dir = tmp_path / "src" / "content" / "weekly"
    weekly_dir.mkdir(parents=True, exist_ok=True)
    (weekly_dir / "2026-W20.json").write_text(
        json.dumps({
            "id": "2026-W20",
            "weekStart": "2026-05-11",
            "weekEnd": "2026-05-17",
            "events": [sample_event],
            "synthesis": sample_synthesis,
        }),
        encoding="utf-8",
    )

    result = generate_article(issue, tmp_path)
    assert "2026-W21" in result
    assert "title: 每周热点分析 2026-W21" in result
    assert "published: 2026-05-24" in result
    assert "category: 周刊" in result
    assert "测试事件" in result
    assert "weekly-hotspot" in result


@pytest.mark.unit
def test_generate_article_without_synthesis(tmp_path, sample_event):
    """Generate article without synthesis section."""
    event = Event(**sample_event)
    issue = WeeklyIssue(
        id="2026-W21",
        weekStart="2026-05-18",
        weekEnd="2026-05-24",
        events=[event],
        synthesis=None,
    )
    result = generate_article(issue, tmp_path)
    assert "2026-W21" in result
    assert "逐件看" in result
    # No synthesis sections
    assert "这周发生了什么" not in result
