import os
import pytest
from chinese_scraper_utils import DeepSeekClient
from analyzer import analyze_event
from schema import Event


EVENT_INPUT = {
    "title": "AI大模型价格战",
    "summary": "多家科技公司大幅下调大模型API价格，引发行业震动。",
    "impactScore": 5,
    "infoGainScore": 4,
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
        assert edge.type in ("因果", "关联", "反驳")


def test_analyze_event_timeline_has_dates(client):
    result = analyze_event(client, EVENT_INPUT, [])
    for node in result["timeline"]:
        assert "T" in node["time"]
        assert len(node["title"]) > 0
