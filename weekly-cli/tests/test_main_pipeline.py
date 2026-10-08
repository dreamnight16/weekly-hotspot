"""Tests for the v3 orchestration helpers in main.py."""
from unittest.mock import MagicMock

import main
from schema import DialecticalUnfolding, EvidenceDossier, SourceRecord


class TestPromptSetVersion:
    def test_is_stable(self):
        assert main._prompt_set_version() == main._prompt_set_version()

    def test_is_a_short_hex_digest(self):
        value = main._prompt_set_version()
        assert len(value) == 12
        int(value, 16)


class TestRecentWeekIds:
    def test_returns_requested_count(self):
        assert len(main._recent_week_ids(4)) == 4

    def test_is_oldest_first(self):
        weeks = main._recent_week_ids(3)
        assert weeks == sorted(weeks)

    def test_format(self):
        assert all("-W" in w for w in main._recent_week_ids(1))


class TestBuildPhase3:
    def test_none_for_no_events(self):
        assert main._build_phase3([]) is None

    def test_selects_highest_confidence(self):
        events = [
            {"dialecticalConfidence": "LOW", "phaseSummary": "low"},
            {"dialecticalConfidence": "HIGH", "phaseSummary": "high"},
        ]
        phase = main._build_phase3(events)
        assert isinstance(phase, DialecticalUnfolding)
        assert phase.phaseSummary == "high"

    def test_survives_malformed_event(self):
        """A bad event must not sink the whole phase."""
        phase = main._build_phase3([{"dialecticalConfidence": "HIGH", "unityOfOpposites": "not-a-dict"}])
        assert phase is None or isinstance(phase, DialecticalUnfolding)

    def test_renders_adversarial_review(self):
        """Phase 3 was previously pinned to None, dropping this from the article."""
        from narrative.article import _render_phase3

        events = [{
            "dialecticalConfidence": "HIGH",
            "adversarialReview": {
                "originalClaim": "原主张",
                "critique": "批判内容在此",
                "confidence": "MEDIUM",
            },
        }]
        phase = main._build_phase3(events)
        assert "批判内容在此" in _render_phase3(phase)


class TestFactsOnlyPhase1:
    def test_strips_material_content(self):
        payload = {
            "selectedEvents": [
                {"title": "事件", "summary": "概述", "materialContent": "车企希望通过通报控制舆论。"}
            ]
        }
        out = main._facts_only_phase1(payload, None)
        assert out["selectedEvents"][0]["materialContent"] == ""
        assert out["selectedEvents"][0]["title"] == "事件"

    def test_notes_the_block(self):
        gate = MagicMock(blockingClaims=["问题一"])
        out = main._facts_only_phase1({"selectedEvents": []}, gate)
        assert "仅发布事实" in out["sourceQualityReport"]
        assert "问题一" in out["sourceQualityReport"]

    def test_does_not_mutate_input(self):
        payload = {"selectedEvents": [{"title": "t", "materialContent": "x"}]}
        main._facts_only_phase1(payload, None)
        assert payload["selectedEvents"][0]["materialContent"] == "x"


class TestVerifyAndReviseEvent:
    def test_applies_deterministic_revision_without_client(self):
        analysis = {"materialContent": "车企希望通过主动通报控制舆论，避免召回。"}
        revised, claims, records = main._verify_and_revise_event(
            event_analysis=analysis,
            dossier=None,
            event_id="e1",
            round_no=1,
            empirical_client=None,
            log=main.logger,
        )
        assert "可能希望" in revised["materialContent"]
        assert claims and records

    def test_merges_reviewer_verdict(self):
        analysis = {"title": "事件", "summary": "概述", "materialContent": "该企业发布了召回公告。"}
        client = MagicMock()
        client.chat_json.return_value = {
            "verificationSummary": "s",
            "claimReviews": [
                {
                    "claimId": "e1-r1-001",
                    "verdict": "REMOVE",
                    "reason": "无来源",
                }
            ],
        }
        _revised, claims, _records = main._verify_and_revise_event(
            event_analysis=analysis,
            dossier=None,
            event_id="e1",
            round_no=1,
            empirical_client=client,
            log=main.logger,
        )
        assert claims[0].publicationDecision == "REMOVE"

    def test_uses_dossier_sources_as_evidence(self):
        dossier = EvidenceDossier(
            eventId="e1",
            title="t",
            sources=[
                SourceRecord(
                    sourceId="s1",
                    kind="INDEPENDENT",
                    content="该企业发布了召回公告，说明相关情况。",
                )
            ],
        )
        analysis = {"materialContent": "该企业发布了召回公告。"}
        _revised, claims, _ = main._verify_and_revise_event(
            event_analysis=analysis,
            dossier=dossier,
            event_id="e1",
            round_no=1,
            empirical_client=None,
            log=main.logger,
        )
        assert "s1" in claims[0].evidenceIds


class TestClusterEvents:
    def test_clusters_and_marks_new(self):
        raw = [
            {"title": "尊界刹车踏板断裂", "summary": "a"},
            {"title": "尊界回应制动踏板问题", "summary": "b"},
        ]
        events = main._cluster_events(raw, main.logger)
        assert len(events) == 1
        assert events[0]["eventStatus"] in ("新发生", "持续发展")

    def test_empty_input(self):
        assert main._cluster_events([], main.logger) == []
