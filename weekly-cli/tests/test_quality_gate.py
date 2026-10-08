"""Tests for the deterministic publication gate and the narrative safety net."""
from quality import (
    assess_evidence,
    publication_gate,
    sanitize_narrative,
    scan_text_risk,
    validate_claim_references,
)
from schema import ClaimRecord, EvidenceDossier, SourceRecord


def _dossier(kind="INDEPENDENT", source_id="s1", conflicts=None, failed=False):
    return EvidenceDossier(
        eventId="e1",
        title="事件",
        searchFailed=failed,
        conflicts=conflicts or [],
        sources=[SourceRecord(sourceId=source_id, kind=kind, content="内容")],
    )


class TestAssessEvidence:
    def test_none_dossier_is_absent(self):
        assert assess_evidence(None)[0] == "absent"

    def test_search_failure_is_absent(self):
        assert assess_evidence(_dossier(failed=True))[0] == "absent"

    def test_no_sources_is_absent(self):
        assert assess_evidence(EvidenceDossier(eventId="e1"))[0] == "absent"

    def test_only_republications_is_thin(self):
        status, reasons = assess_evidence(_dossier(kind="REPUBLISHED"))
        assert status == "thin"
        assert "转载" in reasons[0]

    def test_conflicts_make_it_thin(self):
        assert assess_evidence(_dossier(conflicts=["甲与乙不一致"]))[0] == "thin"

    def test_independent_source_is_sufficient(self):
        status, notes = assess_evidence(_dossier())
        assert status == "sufficient"
        assert any("原始来源" in n for n in notes)

    def test_primary_source_is_sufficient(self):
        assert assess_evidence(_dossier(kind="PRIMARY"))[0] == "sufficient"


class TestValidateClaimReferences:
    def test_dangling_reference_is_reported(self):
        claims = [ClaimRecord(claimId="c1", evidenceIds=["missing"])]
        assert validate_claim_references(claims, [_dossier()])

    def test_valid_reference_passes(self):
        claims = [ClaimRecord(claimId="c1", evidenceIds=["s1"])]
        assert validate_claim_references(claims, [_dossier()]) == []

    def test_no_claims(self):
        assert validate_claim_references([], [_dossier()]) == []


class TestScanResidualRisk:
    def test_flags_unhedged_motive(self):
        from quality import scan_residual_risk

        residual = scan_residual_risk({
            "e1": {"materialContent": "车企希望通过主动通报控制舆论，避免召回。"}
        })
        assert len(residual) == 1
        assert residual[0].riskLevel == "high"

    def test_hedged_motive_is_not_residual(self):
        from quality import scan_residual_risk

        residual = scan_residual_risk({
            "e1": {"materialContent": "车企可能希望通过主动通报控制舆论。"}
        })
        assert residual == []

    def test_empty_input(self):
        from quality import scan_residual_risk

        assert scan_residual_risk({}) == []


class TestPublicationGate:
    def test_sourced_facts_allow(self):
        gate = publication_gate(
            dossiers=[_dossier()],
            claims=[ClaimRecord(claimId="c1", type="FACT", statement="x", evidenceIds=["s1"])],
        )
        assert gate.decision == "ALLOW"

    def test_unsourced_fact_degrades(self):
        gate = publication_gate(
            dossiers=[_dossier()],
            claims=[ClaimRecord(claimId="c1", type="FACT", statement="x", evidenceIds=[])],
        )
        assert gate.decision == "DEGRADE"

    def test_only_republications_degrades(self):
        gate = publication_gate(dossiers=[_dossier(kind="REPUBLISHED")], claims=[])
        assert gate.decision == "DEGRADE"

    def test_dangling_citation_blocks(self):
        gate = publication_gate(
            dossiers=[_dossier()],
            claims=[ClaimRecord(claimId="c1", type="FACT", statement="x", evidenceIds=["nope"])],
        )
        assert gate.decision == "BLOCK"

    def test_unfixed_motive_attribution_blocks(self):
        """The acceptance criterion for round 1, enforced at the gate."""
        gate = publication_gate(
            dossiers=[_dossier()],
            claims=[],
            analysis_by_event={
                "e1": {"materialContent": "车企希望通过主动通报控制舆论，避免大规模召回和赔偿。"}
            },
        )
        assert gate.decision == "BLOCK"
        assert gate.blockingClaims

    def test_no_dossiers_at_all_degrades(self):
        assert publication_gate(dossiers=[], claims=[]).decision == "DEGRADE"

    def test_repeated_reasons_are_deduplicated(self):
        gate = publication_gate(dossiers=[_dossier(failed=True)], claims=[])
        assert len(gate.reasons) == len(set(gate.reasons))


class TestScanTextRisk:
    def test_flags_motive_in_prose(self):
        text = "本周尊界通报了踏板问题。\n- 车企希望通过主动通报控制舆论，避免召回。"
        risky = scan_text_risk(text)
        assert len(risky) == 1

    def test_ignores_headings(self):
        assert scan_text_risk("## 一、现象") == []

    def test_ignores_short_fragments(self):
        assert scan_text_risk("短句。") == []

    def test_hedged_prose_is_clean(self):
        assert scan_text_risk("车企可能希望通过主动通报控制舆论。") == []


class TestSanitizeNarrative:
    def test_hedges_risk_sentence(self):
        text = "车企希望通过主动通报控制舆论，避免大规模召回。"
        clean, notes = sanitize_narrative(text)
        assert "可能希望" in clean
        assert notes

    def test_clean_text_is_untouched(self):
        text = "本周收录了三个事件。"
        clean, notes = sanitize_narrative(text)
        assert clean == text and notes == []

    def test_empty_input(self):
        assert sanitize_narrative("") == ("", [])
