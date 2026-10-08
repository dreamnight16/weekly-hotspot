"""Tests for query expansion, conflict detection, and dossier assembly."""
from evidence.collector import (
    collect_dossier,
    detect_numeric_conflicts,
    dossier_claim_context,
    dossier_to_text,
    expand_queries,
    extract_entities,
)
from schema import SourceRecord


class TestExtractEntities:
    def test_uses_bracketed_tag(self):
        assert extract_entities("【尊界】刹车踏板断裂") == "尊界"

    def test_uses_alias_when_present(self):
        assert extract_entities("尊界通报刹车踏板断裂", ["尊界"]) == "尊界"

    def test_falls_back_to_leading_subject(self):
        assert extract_entities("尊界通报刹车踏板断裂").startswith("尊界")

    def test_empty(self):
        assert extract_entities("") == ""


class TestExpandQueries:
    def test_produces_multiple_intents(self):
        queries = expand_queries("尊界通报刹车踏板断裂")
        assert len(queries) >= 4

    def test_queries_cover_primary_and_dispute(self):
        joined = " ".join(expand_queries("尊界通报刹车踏板断裂"))
        assert "官方" in joined
        assert "争议" in joined
        assert "后续" in joined

    def test_queries_are_unique(self):
        queries = expand_queries("某事件")
        assert len(queries) == len(set(queries))


class TestDetectNumericConflicts:
    def test_detects_disagreeing_figures(self):
        sources = [
            SourceRecord(sourceId="s1", publisher="甲报", content="图书销售营收占比为30%。"),
            SourceRecord(sourceId="s2", publisher="乙报", content="图书销售营收占比为70%。"),
        ]
        conflicts = detect_numeric_conflicts(sources)
        assert len(conflicts) == 1
        assert "甲报" in conflicts[0]

    def test_agreement_is_not_a_conflict(self):
        sources = [
            SourceRecord(sourceId="s1", content="图书销售营收占比为30%。"),
            SourceRecord(sourceId="s2", content="图书销售营收占比为30%。"),
        ]
        assert detect_numeric_conflicts(sources) == []

    def test_unrelated_sentences_are_not_compared(self):
        sources = [
            SourceRecord(sourceId="s1", content="成本为30元。"),
            SourceRecord(sourceId="s2", content="涨幅为70%。"),
        ]
        assert detect_numeric_conflicts(sources) == []

    def test_respects_max_conflicts(self):
        sources = [
            SourceRecord(sourceId=f"s{i}", content=f"占比为{i}0%。") for i in range(1, 6)
        ]
        assert len(detect_numeric_conflicts(sources, max_conflicts=2)) <= 2


def _fake_search(queries_seen):
    def _search(query, max_results=10):
        queries_seen.append(query)
        return [
            {"title": f"{query} 报道", "url": f"https://news.example.com/{len(queries_seen)}", "snippet": "摘要内容"}
        ]
    return _search


class TestCollectDossier:
    def test_builds_dossier_from_injected_search(self):
        seen = []
        dossier = collect_dossier(
            {"title": "尊界通报刹车踏板断裂", "eventId": "e1"},
            search_fn=_fake_search(seen),
            fetch_fn=lambda url: ("", "network-error"),
            max_fetches=0,
        )
        assert dossier.eventId == "e1"
        assert dossier.searchFailed is False
        assert len(dossier.sources) >= 1
        assert len(seen) == len(dossier.queries)

    def test_search_failure_marks_dossier_unusable(self):
        def _boom(query, max_results=10):
            raise RuntimeError("network down")

        dossier = collect_dossier(
            {"title": "事件", "eventId": "e1"}, search_fn=_boom, max_fetches=0
        )
        assert dossier.searchFailed is True
        assert dossier.sources == []

    def test_empty_results_marks_search_failed(self):
        dossier = collect_dossier(
            {"title": "事件", "eventId": "e1"},
            search_fn=lambda q, max_results=10: [],
            max_fetches=0,
        )
        assert dossier.searchFailed is True

    def test_fetches_page_content(self):
        dossier = collect_dossier(
            {"title": "事件", "eventId": "e1"},
            search_fn=_fake_search([]),
            fetch_fn=lambda url: ("抓取到的正文内容", "ok"),
            max_fetches=2,
        )
        assert any(s.content for s in dossier.sources)

    def test_fetch_exception_does_not_abort(self):
        def _boom(url):
            raise RuntimeError("fetch failed")

        dossier = collect_dossier(
            {"title": "事件", "eventId": "e1"},
            search_fn=_fake_search([]),
            fetch_fn=_boom,
            max_fetches=2,
        )
        assert dossier.sources

    def test_respects_max_sources(self):
        dossier = collect_dossier(
            {"title": "事件", "eventId": "e1"},
            search_fn=_fake_search([]),
            max_fetches=0,
            max_sources=2,
        )
        assert len(dossier.sources) <= 2


class TestDossierRendering:
    def test_absent_evidence_is_stated_explicitly(self):
        from schema import EvidenceDossier

        text = dossier_to_text(EvidenceDossier(eventId="e1"))
        assert "未检索到可用来源" in text

    def test_labels_source_kind(self):
        from schema import EvidenceDossier

        dossier = EvidenceDossier(
            eventId="e1",
            sources=[SourceRecord(sourceId="s1", kind="PRIMARY", title="通报", url="https://gov.cn/a")],
        )
        assert "原始来源" in dossier_to_text(dossier)

    def test_marks_republished(self):
        from schema import EvidenceDossier

        dossier = EvidenceDossier(
            eventId="e1",
            sources=[SourceRecord(sourceId="s1", kind="REPUBLISHED", url="https://a.com/1")],
        )
        assert "转载" in dossier_to_text(dossier)

    def test_claim_context_includes_source_ids(self):
        from schema import EvidenceDossier

        dossier = EvidenceDossier(
            eventId="e1", sources=[SourceRecord(sourceId="s1", content="内容")]
        )
        assert "s1" in dossier_claim_context(dossier)

    def test_empty_claim_context(self):
        from schema import EvidenceDossier

        assert "无来源" in dossier_claim_context(EvidenceDossier(eventId="e1"))
