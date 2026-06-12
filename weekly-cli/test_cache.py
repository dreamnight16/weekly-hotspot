"""Tests for cache.py — save/load/corruption/clean."""
import json
import pytest
from cache import save_cache, load_cache, CACHE_DIR, CACHE_FILE


@pytest.mark.unit
def test_save_and_load(tmp_path, monkeypatch):
    monkeypatch.setattr("cache.CACHE_DIR", tmp_path)
    monkeypatch.setattr("cache.CACHE_FILE", tmp_path / "last_raw_events.json")

    events = [{"title": "test", "summary": "desc"}]
    save_cache(events)
    loaded = load_cache()
    assert loaded == events


@pytest.mark.unit
def test_load_cache_nonexistent():
    # CACHE_FILE does not exist by default in clean env
    # Just verify load_cache doesn't crash when file is absent
    import cache
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        import pathlib
        cache_file = pathlib.Path(td) / "nonexistent.json"
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(cache, "CACHE_FILE", cache_file)
        result = load_cache()
        monkeypatch.undo()
        assert result is None


@pytest.mark.unit
def test_load_cache_corrupted(tmp_path, monkeypatch):
    monkeypatch.setattr("cache.CACHE_DIR", tmp_path)
    monkeypatch.setattr("cache.CACHE_FILE", tmp_path / "last_raw_events.json")

    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "last_raw_events.json").write_text("not valid json", encoding="utf-8")
    result = load_cache()
    assert result is None


@pytest.mark.unit
def test_save_creates_dir(tmp_path, monkeypatch):
    subdir = tmp_path / "nested" / "cache"
    monkeypatch.setattr("cache.CACHE_DIR", subdir)
    monkeypatch.setattr("cache.CACHE_FILE", subdir / "last_raw_events.json")

    events = [{"title": "deep"}]
    save_cache(events)
    assert subdir.exists()
    assert (subdir / "last_raw_events.json").exists()
