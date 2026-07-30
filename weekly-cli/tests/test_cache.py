"""Test scraper cache (moved from old test_cache.py, adapted for v2)."""
import json
import tempfile
from pathlib import Path
import pytest
from scraper.cache import save_cache, load_cache


class TestCache:
    @pytest.fixture(autouse=True)
    def setup_cache_dir(self, monkeypatch):
        tmp = Path(tempfile.mkdtemp())
        monkeypatch.setattr("scraper.cache.CACHE_DIR", tmp)
        monkeypatch.setattr("scraper.cache.CACHE_FILE", tmp / "last_raw_events.json")
        yield

    def test_save_and_load(self):
        events = [{"title": "事件1", "summary": "概述1"}, {"title": "事件2", "summary": "概述2"}]
        save_cache(events)
        loaded = load_cache()
        assert loaded is not None
        assert len(loaded) == 2
        assert loaded[0]["title"] == "事件1"

    def test_load_nonexistent(self, monkeypatch):
        tmp = Path(tempfile.mkdtemp())
        monkeypatch.setattr("scraper.cache.CACHE_FILE", tmp / "nonexistent.json")
        assert load_cache() is None

    def test_load_corrupted(self, monkeypatch):
        import scraper.cache
        tmp = Path(tempfile.mkdtemp())
        junk = tmp / "junk.json"
        junk.write_text("not valid json", encoding="utf-8")
        monkeypatch.setattr(scraper.cache, "CACHE_FILE", junk)
        assert load_cache() is None
