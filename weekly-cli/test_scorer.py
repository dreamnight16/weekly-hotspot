import os
import pytest
from unittest.mock import MagicMock

from chinese_scraper_utils import DeepSeekClient
from scorer import score_and_select


@pytest.fixture
def client():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY not set")
    return DeepSeekClient(api_key)


@pytest.mark.integration
def test_scorer_returns_top_events(client):
    events = [
        {"title": "事件A", "summary": "某科技公司发布革命性产品，影响全球供应链。"},
        {"title": "事件B", "summary": "某地天气变化。"},
        {"title": "事件C", "summary": "国际空间站发现新粒子，物理学界震动。"},
    ]
    result = score_and_select(client, events, top_n=2)
    assert len(result) == 2
    for e in result:
        assert "impactScore" in e
        assert "infoGainScore" in e
        assert 1 <= e["impactScore"] <= 5
        assert 1 <= e["infoGainScore"] <= 5


@pytest.mark.integration
def test_scorer_respects_top_n(client):
    events = [{"title": f"事件{i}", "summary": f"描述{i}"} for i in range(10)]
    result = score_and_select(client, events, top_n=5)
    assert len(result) <= 5


@pytest.mark.unit
def test_scorer_fewer_events_than_top_n():
    mock_client = MagicMock()
    mock_client.chat_json.return_value = {"events": [{"title": "A", "impactScore": 4, "infoGainScore": 3, "summary": "desc"}]}
    events = [{"title": "A", "summary": "desc"}]
    result = score_and_select(mock_client, events, top_n=8)
    assert len(result) == 1


@pytest.mark.unit
def test_scorer_with_mock_client():
    mock_client = MagicMock()
    mock_client.chat_json.return_value = {
        "events": [
            {"title": "事件1", "impactScore": 5, "infoGainScore": 4, "summary": "概述1"},
            {"title": "事件2", "impactScore": 3, "infoGainScore": 2, "summary": "概述2"},
        ]
    }
    events = [
        {"title": "事件1", "summary": "概述1"},
        {"title": "事件2", "summary": "概述2"},
        {"title": "事件3", "summary": "概述3"},
    ]
    result = score_and_select(mock_client, events, top_n=2)
    assert len(result) == 2
    assert result[0]["impactScore"] == 5
