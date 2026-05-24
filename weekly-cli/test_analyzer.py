import os
import json
import pytest
from unittest.mock import MagicMock, patch
from chinese_scraper_utils import DeepSeekClient
from analyzer import analyze_event
from schema import Event


EVENT_INPUT = {
    "title": "AI大模型价格战",
    "summary": "多家科技公司大幅下调大模型API价格，引发行业震动。",
    "impactScore": 5,
    "infoGainScore": 4,
}

SAMPLE_ANALYZER_OUTPUT = {
    "id": "ai-price-war",
    "title": "AI大模型价格战",
    "summary": "多家科技公司大幅下调大模型API价格，引发行业震动。",
    "impactScore": 5,
    "infoGainScore": 4,
    "classAnalysis": {
        "classNature": "科技资本的垄断竞争延伸到定价层面",
        "contradiction": "大厂通过低价策略挤压中小模型厂商的生存空间",
        "historicalContext": "AI基础设施从技术竞赛转向价格竞赛",
    },
    "dialecticalSummary": "价格战的背后是云厂商通过API绑定生态的战略，中小厂商面临被挤出市场的风险",
    "timeline": [
        {"id": "t1", "time": "2026-01-15T00:00:00", "title": "DeepSeek率先降价", "description": "DeepSeek大幅下调API价格", "evidenceRefs": ["e1"]},
        {"id": "t2", "time": "2026-02-01T00:00:00", "title": "阿里云跟进", "description": "阿里云宣布降价", "evidenceRefs": ["e2"]},
        {"id": "t3", "time": "2026-03-10T00:00:00", "title": "价格战白热化", "description": "多家厂商参与价格竞争", "evidenceRefs": ["e3"]},
    ],
    "evidence": [
        {"id": "e1", "sourceType": "官媒", "sourceName": "新华社", "content": "DeepSeek宣布大幅下调API价格", "authenticity": "真实", "aiReason": "直接公告", "classBias": "待判断"},
        {"id": "e2", "sourceType": "社交平台", "sourceName": "微博", "content": "阿里云跟进降价措施", "authenticity": "真实", "aiReason": "官方发布", "classBias": "待判断"},
        {"id": "e3", "sourceType": "其他", "sourceName": "即刻App", "content": "大模型价格战趋势分析", "authenticity": "存疑", "aiReason": "第三方分析", "classBias": "待判断"},
    ],
    "edges": [
        {"from": "t1", "to": "t2", "type": "因果", "description": "DeepSeek降价引发连锁反应"},
        {"from": "t2", "to": "t3", "type": "关联", "description": "竞争加剧导致行业洗牌"},
    ],
}


@pytest.fixture
def client():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY not set")
    return DeepSeekClient(api_key)


def test_analyze_event_returns_valid_structure(client):
    result = analyze_event(client, EVENT_INPUT, [])
    event = Event(**result)
    assert len(event.timeline) >= 3
    assert len(event.evidence) >= 2
    for e in event.evidence:
        assert e.authenticity in ("真实", "存疑", "不实", "待验证")
    for edge in event.edges:
        assert edge.type in ("因果", "关联", "矛盾")


def test_analyze_event_timeline_has_dates(client):
    result = analyze_event(client, EVENT_INPUT, [])
    for node in result["timeline"]:
        assert "T" in node["time"]
        assert len(node["title"]) > 0


# ---- Offline tests with mocked DeepSeekClient ----

def test_analyze_event_offline_validates_schema():
    """Test that sample output passes Pydantic validation."""
    event = Event(**SAMPLE_ANALYZER_OUTPUT)
    assert event.timeline[0].title == "DeepSeek率先降价"
    assert len(event.evidence) == 3
    assert event.edges[0].type == "因果"
    assert event.edges[1].type == "关联"


def test_analyze_event_offline_with_mock_client():
    """Test analyze_event with mocked client returns valid structure."""
    mock_client = MagicMock()
    mock_client.chat_json.return_value = SAMPLE_ANALYZER_OUTPUT

    result = analyze_event(mock_client, EVENT_INPUT, [], idx=1)

    event = Event(**result)
    assert len(event.timeline) >= 3
    assert len(event.evidence) >= 2
    for edge in event.edges:
        assert edge.type in ("因果", "关联", "矛盾")
