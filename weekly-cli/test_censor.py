import os
import pytest
from unittest.mock import MagicMock

from chinese_scraper_utils import DeepSeekClient
from censor import censor_events


@pytest.fixture
def client():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY not set")
    return DeepSeekClient(api_key)


@pytest.mark.integration
def test_censor_filters_political(client):
    events = [
        {"title": "某地举行科技创新大赛", "summary": "当地举办了青少年科技创新比赛"},
        {"title": "某政治敏感事件", "summary": "涉及政治敏感内容"},
    ]
    result = censor_events(client, events)
    assert len(result) <= 2
    titles = [e["title"] for e in result]
    assert "某政治敏感事件" not in titles


@pytest.mark.integration
def test_censor_preserves_normal_events(client):
    events = [
        {"title": "AI技术新突破", "summary": "某公司发布新一代大模型"},
        {"title": "世界杯预选赛结果", "summary": "中国队晋级下一轮"},
    ]
    result = censor_events(client, events)
    assert len(result) == 2


@pytest.mark.unit
def test_censor_empty_events():
    result = censor_events(None, [])
    assert result == []


@pytest.mark.unit
def test_censor_with_mock():
    mock_client = MagicMock()
    mock_client.chat_json.return_value = {
        "passed": [
            {"title": "事件A", "summary": "描述A"},
        ]
    }
    events = [
        {"title": "事件A", "summary": "描述A"},
        {"title": "事件B", "summary": "描述B"},
    ]
    result = censor_events(mock_client, events)
    assert len(result) == 1
    assert result[0]["title"] == "事件A"
