import os
import pytest
from chinese_scraper_utils import DeepSeekClient
from scorer import score_and_select


@pytest.fixture
def client():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY not set")
    return DeepSeekClient(api_key)


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


def test_scorer_respects_top_n(client):
    events = [{"title": f"事件{i}", "summary": f"描述{i}"} for i in range(10)]
    result = score_and_select(client, events, top_n=5)
    assert len(result) <= 5
