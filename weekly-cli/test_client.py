import os
import pytest
from chinese_scraper_utils import DeepSeekClient


@pytest.fixture
def client():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY not set")
    return DeepSeekClient(api_key)


def test_client_initialization(client):
    assert client.model == "deepseek-chat"
    assert client.base_url == "https://api.deepseek.com"


def test_chat_returns_valid_json():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY not set")
    client = DeepSeekClient(api_key)
    result = client.chat_json([
        {"role": "system", "content": "你是一个JSON输出助手。请始终以有效的JSON格式回复。"},
        {"role": "user", "content": '返回 {"answer": 42}'}
    ])
    assert result["answer"] == 42
