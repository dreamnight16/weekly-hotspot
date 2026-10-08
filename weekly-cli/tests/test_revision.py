"""Tests for the revision applier -- the step that makes verification binding."""
from evidence.claims import extract_claims
from narrative.revision import apply_revisions, revise_statement, summarise_records
from schema import ClaimRecord


class TestReviseStatement:
    def test_keep_is_unchanged(self):
        claim = ClaimRecord(statement="原文", publicationDecision="KEEP")
        assert revise_statement(claim) == "原文"

    def test_remove_returns_none(self):
        claim = ClaimRecord(statement="原文", publicationDecision="REMOVE")
        assert revise_statement(claim) is None

    def test_rewrite_hedges_motive(self):
        claim = ClaimRecord(
            statement="车企希望通过主动通报控制舆论",
            publicationDecision="REWRITE",
        )
        assert revise_statement(claim) == "车企可能希望通过主动通报控制舆论"

    def test_rewrite_prefers_reviewer_text(self):
        claim = ClaimRecord(
            statement="原文",
            publicationDecision="REWRITE",
            revisedStatement="审查员改写后的表述",
        )
        assert revise_statement(claim) == "审查员改写后的表述"

    def test_qualify_appends_marker(self):
        claim = ClaimRecord(statement="某事实。", publicationDecision="QUALIFY")
        assert "尚无直接证据支持" in revise_statement(claim)

    def test_qualify_attributed_uses_attribution_marker(self):
        claim = ClaimRecord(
            statement="企业称产品合格。", type="ATTRIBUTED", publicationDecision="QUALIFY"
        )
        assert "待独立来源核实" in revise_statement(claim)

    def test_research_leaves_text(self):
        claim = ClaimRecord(statement="原文", publicationDecision="RESEARCH")
        assert revise_statement(claim) == "原文"


class TestApplyRevisions:
    def test_rewrites_motive_in_place(self):
        original = "车企希望通过主动通报控制舆论，避免大规模召回和赔偿"
        analysis = {"materialContent": f"前言。{original}。后语。"}
        claims = extract_claims(analysis, event_id="e1")
        revised, records = apply_revisions(analysis, claims, round_no=1)
        assert original not in revised["materialContent"]
        assert "可能希望" in revised["materialContent"]
        assert any(r.action == "REWRITE" for r in records)

    def test_removes_banned_sentence(self):
        analysis = {"materialContent": "保留这句。删除这句。"}
        claims = [ClaimRecord(
            claimId="c1", statement="删除这句。", path="materialContent",
            publicationDecision="REMOVE",
        )]
        revised, records = apply_revisions(analysis, claims)
        assert "删除这句" not in revised["materialContent"]
        assert "保留这句" in revised["materialContent"]
        assert records[0].action == "REMOVE"

    def test_handles_nested_path(self):
        analysis = {"unityOfOpposites": {"struggle": "车企希望通过通报淡化问题。"}}
        claims = extract_claims(analysis, event_id="e1")
        revised, _ = apply_revisions(analysis, claims)
        assert "可能希望" in revised["unityOfOpposites"]["struggle"]

    def test_handles_list_path(self):
        analysis = {"dataValidation": {"issues": ["企业希望通过掩盖问题。"]}}
        claims = extract_claims(analysis, event_id="e1")
        revised, records = apply_revisions(analysis, claims)
        assert records
        assert "可能希望" in revised["dataValidation"]["issues"][0]

    def test_unmatched_path_is_skipped(self):
        analysis = {"materialContent": "原文。"}
        claims = [ClaimRecord(
            claimId="c1", statement="不存在的句子。", path="nowhere",
            publicationDecision="REMOVE",
        )]
        revised, records = apply_revisions(analysis, claims)
        assert records == []
        assert revised["materialContent"] == "原文。"

    def test_records_capture_before_and_after(self):
        analysis = {"materialContent": "车企希望通过通报避免召回。"}
        claims = extract_claims(analysis, event_id="e1")
        _, records = apply_revisions(analysis, claims)
        assert records[0].before and records[0].after
        assert records[0].round == 1

    def test_keep_and_unreviewed_produce_no_records(self):
        analysis = {"materialContent": "普通陈述。"}
        claims = extract_claims(analysis, event_id="e1")
        claims[0].publicationDecision = "KEEP"
        _, records = apply_revisions(analysis, claims)
        assert records == []

    def test_research_is_recorded_without_editing(self):
        analysis = {"materialContent": "需要补充检索的断言。"}
        claims = [ClaimRecord(
            claimId="c1", statement="需要补充检索的断言。", path="materialContent",
            publicationDecision="RESEARCH",
        )]
        revised, records = apply_revisions(analysis, claims)
        assert revised["materialContent"] == "需要补充检索的断言。"
        assert records[0].action == "RESEARCH"


class TestSummariseRecords:
    def test_counts_by_action(self):
        from schema import RevisionRecord

        records = [
            RevisionRecord(action="REMOVE"),
            RevisionRecord(action="REMOVE"),
            RevisionRecord(action="KEEP"),
        ]
        out = summarise_records(records)
        assert out["REMOVE"] == 2 and out["KEEP"] == 1

    def test_empty(self):
        assert summarise_records([]) == {}
