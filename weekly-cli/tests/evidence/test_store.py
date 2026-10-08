"""Tests for dossier persistence and reuse."""
import json

import pytest

from evidence import store
from schema import EvidenceDossier, SourceRecord


@pytest.fixture
def tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "CACHE_DIR", tmp_path)
    return tmp_path


def _dossier(event_id="e1", fingerprint="abc"):
    return EvidenceDossier(
        eventId=event_id,
        title="事件",
        sources=[SourceRecord(sourceId="s1", contentFingerprint=fingerprint)],
    )


class TestSaveLoad:
    def test_round_trip(self, tmp_cache):
        path = store.save_dossiers([_dossier()], "2026-W41")
        assert path is not None and path.exists()
        loaded = store.load_dossiers("2026-W41")
        assert len(loaded) == 1
        assert loaded[0].eventId == "e1"

    def test_load_missing_returns_empty(self, tmp_cache):
        assert store.load_dossiers("1999-W01") == []

    def test_corrupt_file_returns_empty(self, tmp_cache):
        store.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (store.CACHE_DIR / "2026-W41.json").write_text("{not json", encoding="utf-8")
        assert store.load_dossiers("2026-W41") == []

    def test_partial_corruption_skips_bad_entry(self, tmp_cache):
        store.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        payload = [_dossier().model_dump(), {"eventId": "e2", "sources": "not-a-list"}]
        (store.CACHE_DIR / "2026-W41.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        loaded = store.load_dossiers("2026-W41")
        assert [d.eventId for d in loaded] == ["e1"]


class TestHistory:
    def test_load_recent_maps_by_event_id(self, tmp_cache):
        store.save_dossiers([_dossier("e1", "f1")], "2026-W40")
        store.save_dossiers([_dossier("e2", "f2")], "2026-W41")
        history = store.load_recent_dossiers(["2026-W40", "2026-W41"])
        assert set(history) == {"e1", "e2"}

    def test_later_week_wins(self, tmp_cache):
        store.save_dossiers([_dossier("e1", "old")], "2026-W40")
        store.save_dossiers([_dossier("e1", "new")], "2026-W41")
        history = store.load_recent_dossiers(["2026-W40", "2026-W41"])
        assert store.fingerprint_set(history["e1"]) == {"new"}


class TestHasNewInformation:
    def test_none_history_means_new(self):
        assert store.has_new_information(None, _dossier()) is True

    def test_same_fingerprints_means_nothing_new(self):
        assert store.has_new_information(_dossier("e1", "x"), _dossier("e1", "x")) is False

    def test_new_fingerprint_is_new_information(self):
        assert store.has_new_information(_dossier("e1", "x"), _dossier("e1", "y")) is True

    def test_fingerprint_set_skips_empty(self):
        empty = EvidenceDossier(eventId="e1", sources=[SourceRecord(sourceId="s1")])
        assert store.fingerprint_set(empty) == set()
