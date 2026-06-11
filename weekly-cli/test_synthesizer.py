"""Tests for synthesizer.py — Phase 4 cross-event synthesis."""
import os
import pytest
from unittest.mock import MagicMock
from chinese_scraper_utils import DeepSeekClient
from synthesizer import synthesize_events
from schema import WeeklySynthesis


SAMPLE_SYNTHESIS = {
    "weeklyNarrative": "本周多个事件从不同侧面反映了资本在科技、劳动、金融三个领域的集中化趋势。",
    "crossCuttingThemes": [
        {
            "name": "平台资本对劳动者的成本转嫁",
            "description": "多个事件显示平台企业通过调整抽成、定价等机制将运营成本转嫁给劳动者",
            "relatedEventIds": ["evt-1", "evt-2"],
            "significance": "揭示了数字资本主义下'灵活用工'模式的结构性矛盾",
        }
    ],
    "trends": [
        {
            "name": "政府监管力度加大",
            "description": "本周多个事件显示监管部门对科技公司的介入在增加",
            "direction": "上升",
            "evidenceEventIds": ["evt-1", "evt-3"],
        }
    ],
    "contradictionsInMotion": [
        {
            "contradiction": "资本积累与劳动者权益保护之间的矛盾",
            "opposingForces": "平台资本追求利润最大化的动力 与 劳动者通过政策和集体行动争取权益",
            "eventsInvolved": ["evt-1", "evt-2"],
            "currentState": "对抗激化",
            "outlook": "短期内矛盾将继续激化，但政策介入可能在一定程度上缓解极端对抗",
        }
    ],
    "globalAssessment": "本周核心矛盾运动处于积累期，多个领域的量变在向质变逼近。",
    "dataGaps": ["缺乏事件二中企业内部决策的具体信息"],
}


@pytest.fixture
def events():
    return [
        {
            "id": "evt-1",
            "title": "测试事件一",
            "impactScore": 5,
            "infoGainScore": 4,
            "summary": "事件一概述",
            "classAnalysis": {
                "classNature": "资本扩张",
                "contradiction": "劳资矛盾",
                "historicalContext": "数字经济发展期",
            },
            "dialecticalSummary": "事件一辩证总结",
            "timeline": [{"id": "tl-1-1"}, {"id": "tl-1-2"}, {"id": "tl-1-3"}],
            "evidence": [
                {"authenticity": "真实"},
                {"authenticity": "存疑"},
            ],
        },
        {
            "id": "evt-2",
            "title": "测试事件二",
            "impactScore": 3,
            "infoGainScore": 3,
            "summary": "事件二概述",
            "classAnalysis": {
                "classNature": "金融资本流动",
                "contradiction": "跨国资本与本土政策",
                "historicalContext": "全球加息周期",
            },
            "dialecticalSummary": "事件二辩证总结",
            "timeline": [{"id": "tl-2-1"}, {"id": "tl-2-2"}, {"id": "tl-2-3"}],
            "evidence": [
                {"authenticity": "真实"},
                {"authenticity": "待验证"},
            ],
        },
    ]


def test_synthesis_schema_valid():
    syn = WeeklySynthesis(**SAMPLE_SYNTHESIS)
    assert len(syn.weeklyNarrative) > 20
    assert len(syn.crossCuttingThemes) == 1
    assert syn.trends[0].direction == "上升"
    assert syn.contradictionsInMotion[0].currentState == "对抗激化"


def test_synthesize_events_with_mock(events):
    mock_client = MagicMock()
    mock_client.chat_json.return_value = SAMPLE_SYNTHESIS
    result = synthesize_events(mock_client, events)
    syn = WeeklySynthesis(**result)
    assert len(syn.crossCuttingThemes) == 1
    assert len(syn.trends) == 1
    assert len(syn.contradictionsInMotion) == 1


def test_synthesize_events_real(events):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY not set")
    client = DeepSeekClient(api_key, model="deepseek-v4-flash")
    result = synthesize_events(client, events)
    syn = WeeklySynthesis(**result)
    assert len(syn.weeklyNarrative) > 50
    assert len(syn.globalAssessment) > 0
