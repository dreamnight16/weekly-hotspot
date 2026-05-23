import os
import pytest
from chinese_scraper_utils import DeepSeekClient
from censor import censor_events


@pytest.fixture
def client():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY not set")
    return DeepSeekClient(api_key)


def test_censor_filters_political(client):
    events = [
        {"title": "某地举行科技创新大赛", "summary": "当地举办了青少年科技创新比赛"},
        {"title": "某政治敏感事件", "summary": "涉及政治敏感内容"},
    ]
    result = censor_events(client, events)
    assert len(result) <= 2
    titles = [e["title"] for e in result]
    assert "某政治敏感事件" not in titles


def test_censor_preserves_normal_events(client):
    events = [
        {"title": "AI技术新突破", "summary": "某公司发布新一代大模型"},
        {"title": "世界杯预选赛结果", "summary": "中国队晋级下一轮"},
    ]
    result = censor_events(client, events)
    assert len(result) == 2
