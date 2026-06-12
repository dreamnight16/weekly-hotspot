"""Tests for search.py — title similarity, Bing search, merge logic."""
from unittest.mock import patch, MagicMock

import pytest
from search import _title_similar, _search_bing, search_event


@pytest.mark.unit
def test_title_similar_exact():
    assert _title_similar("AI大模型价格战", "AI大模型价格战") is True


@pytest.mark.unit
def test_title_similar_partial():
    assert _title_similar("AI 大模型价格战", "大模型 AI 价格战") is True


@pytest.mark.unit
def test_title_similar_different():
    assert _title_similar("AI大模型", "世界杯预选赛") is False


@pytest.mark.unit
def test_title_similar_empty():
    assert _title_similar("", "something") is False
    assert _title_similar("something", "") is False
    assert _title_similar("", "") is False


@pytest.mark.unit
def test_search_bing_no_key(monkeypatch):
    monkeypatch.delenv("BING_API_KEY", raising=False)
    # Reload module level constant
    import search
    monkeypatch.setattr(search, "BING_API_KEY", "")
    result = _search_bing("test query")
    assert result == []


@pytest.mark.unit
def test_search_event_with_mock():
    """Mock both DDG and Bing to test merge + dedup logic."""
    with patch("search._search_ddg") as mock_ddg, patch("search._search_bing") as mock_bing, patch("search.BING_API_KEY", "fake-key"):
        mock_ddg.return_value = [
            MagicMock(title="结果A", url="https://a.com/1", snippet="摘要A"),
        ]
        mock_bing.return_value = [
            {"title": "结果A", "url": "https://a.com/1", "snippet": "摘要A"},  # URL dup
            {"title": "结果B", "url": "https://b.com/2", "snippet": "摘要B"},
        ]
        result = search_event("test query", max_results=5)
        assert len(result) >= 1
        # No duplicate URLs
        urls = [r["url"].rstrip("/").lower() for r in result]
        assert len(set(urls)) == len(urls)


@pytest.mark.unit
def test_search_event_ddg_only():
    """Only DDG available (no Bing key)."""
    with patch("search._search_ddg") as mock_ddg, patch("search.BING_API_KEY", ""):
        mock_ddg.return_value = [
            MagicMock(title="结果", url="https://x.com", snippet="s"),
        ]
        result = search_event("test")
        assert len(result) == 1
