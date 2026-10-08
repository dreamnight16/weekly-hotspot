"""Tests for the claim typing and hedging engine."""
import pytest

from evidence.claims import (
    apply_review_verdicts,
    classify_claim,
    extract_claims,
    hedge_statement,
    initial_decision,
    render_claims_for_review,
    split_sentences,
    stricter_decision,
    supporting_source_ids,
)
from schema import SourceRecord


class TestClassifyClaim:
    def test_unhedged_motive_is_high_risk_hypothesis(self):
        """The central failure this layer exists to catch."""
        ctype, risk = classify_claim("车企希望通过主动通报控制舆论，避免大规模召回和赔偿")
        assert ctype == "HYPOTHESIS"
        assert risk == "high"

    def test_hedged_motive_is_medium_risk(self):
        ctype, risk = classify_claim("车企可能希望通过主动通报降低后续召回成本")
        assert ctype == "HYPOTHESIS"
        assert risk == "medium"

    def test_attributed_statement_is_not_a_fact_claim(self):
        ctype, risk = classify_claim("车企通报称不存在实际使用中的同类故障")
        assert ctype == "ATTRIBUTED"
        assert risk == "medium"

    def test_open_question_is_unknown(self):
        assert classify_claim("是否存在批量性设计缺陷")[0] == "UNKNOWN"
        assert classify_claim("事故原因是否与设计有关？")[0] == "UNKNOWN"

    def test_invalid_defaults_to_unknown(self):
        assert classify_claim("")[0] == "UNKNOWN"

    @pytest.mark.parametrize(
        "text",
        [
            "节省召回成本达数亿元",
            "成本高达 3.5 亿元",
            "涨幅达 20%",
        ],
    )
    def test_specific_figures_are_inferences(self, text):
        assert classify_claim(text) == ("INFERENCE", "high")

    def test_hedged_figure_is_medium(self):
        assert classify_claim("具体节省召回成本可能达数亿元") == ("INFERENCE", "medium")

    @pytest.mark.parametrize(
        "text", ["过去数十年间该行业持续扩张", "他是亿万富翁", "该企业发布了召回公告"]
    )
    def test_no_false_positive_on_non_figures(self, text):
        assert classify_claim(text)[1] in ("low", "medium")

    def test_unhedged_legal_finding_is_high_risk(self):
        assert classify_claim("该行为已构成欺诈") == ("INFERENCE", "high")

    def test_hedged_legal_prediction_is_not_high_risk(self):
        ctype, risk = classify_claim("该选手可能面临过失杀人指控")
        assert (ctype, risk) == ("INFERENCE", "medium")

    def test_value_judgment(self):
        assert classify_claim("企业应当公开测试条件")[0] == "VALUE_JUDGMENT"

    def test_unknown_marker(self):
        assert classify_claim("事故原因不明")[0] == "UNKNOWN"


class TestHedgeStatement:
    def test_inserts_conditional_before_motive_verb(self):
        out = hedge_statement("车企希望通过主动通报控制舆论，避免大规模召回和赔偿")
        assert out.startswith("车企可能希望")
        assert "希望通过主动通报控制舆论" in out

    def test_does_not_double_hedge(self):
        out = hedge_statement("车企可能希望通过主动通报避免召回")
        assert "可能可能" not in out

    def test_hedges_multiple_clauses(self):
        out = hedge_statement("车企希望通过通报控制舆论，试图避免召回")
        assert out.count("可能") == 2

    def test_empty_input(self):
        assert hedge_statement("") == ""

    def test_hedged_output_is_no_longer_high_risk(self):
        original = "车企希望通过主动通报控制舆论，避免大规模召回和赔偿"
        assert classify_claim(hedge_statement(original))[1] != "high"


class TestSplitSentences:
    def test_splits_chinese_sentences(self):
        parts = split_sentences("第一句。第二句！第三句？")
        assert len(parts) == 3

    def test_handles_empty(self):
        assert split_sentences("") == []


class TestSupportingSources:
    def test_returns_sources_sharing_content(self):
        sources = [
            SourceRecord(
                sourceId="s1",
                content="监管部门通报称已就制动踏板问题组织调查并开展检验。",
            )
        ]
        ids = supporting_source_ids("监管部门就制动踏板问题组织调查", sources)
        assert ids == ["s1"]

    def test_unrelated_source_does_not_support(self):
        sources = [SourceRecord(sourceId="s1", content="今天天气晴朗适合出行。")]
        assert supporting_source_ids("监管部门就制动踏板问题组织调查", sources) == []

    def test_short_claim_yields_no_match(self):
        assert supporting_source_ids("事故", [SourceRecord(sourceId="s1", content="事故")]) == []


class TestInitialDecision:
    def test_unhedged_motive_is_rewritten_not_removed(self):
        """A hypothesis must be repaired, not deleted: the analysis is the product."""
        decision, _ = initial_decision("HYPOTHESIS", "high", "UNVERIFIED", [])
        assert decision == "REWRITE"

    def test_unsourced_ordinary_fact_is_qualified(self):
        decision, reason = initial_decision("FACT", "low", "UNVERIFIED", [])
        assert decision == "QUALIFY"
        assert "待核实" in reason

    def test_unsourced_high_risk_inference_is_removed(self):
        decision, _ = initial_decision("INFERENCE", "high", "UNVERIFIED", [])
        assert decision == "REMOVE"

    def test_unknown_is_kept(self):
        assert initial_decision("UNKNOWN", "low", "UNVERIFIED", [])[0] == "KEEP"


class TestStricterDecision:
    def test_remove_beats_keep(self):
        assert stricter_decision("KEEP", "REMOVE") == "REMOVE"

    def test_keep_cannot_lower_rewrite(self):
        assert stricter_decision("REWRITE", "KEEP") == "REWRITE"

    def test_symmetric(self):
        assert stricter_decision("KEEP", "KEEP") == "KEEP"


class TestExtractClaims:
    def test_extracts_from_nested_paths(self):
        analysis = {
            "materialContent": "车企希望通过主动通报控制舆论。",
            "unityOfOpposites": {"struggle": "双方在价格上对立。"},
        }
        claims = extract_claims(analysis, event_id="e1")
        paths = {c.path for c in claims}
        assert "materialContent" in paths
        assert "unityOfOpposites.struggle" in paths

    def test_records_event_id_and_ids_are_unique(self):
        analysis = {"materialContent": "第一句。第二句。"}
        claims = extract_claims(analysis, event_id="e1", claim_prefix="c")
        assert all(c.eventId == "e1" for c in claims)
        assert len({c.claimId for c in claims}) == len(claims)

    def test_empty_analysis_yields_nothing(self):
        assert extract_claims({}, event_id="e1") == []


class TestApplyReviewVerdicts:
    def _claims(self):
        return extract_claims(
            {"materialContent": "该企业发布了召回公告。"}, event_id="e1"
        )

    def test_review_can_escalate(self):
        claims = self._claims()
        applied = apply_review_verdicts(
            claims,
            [{"claimId": claims[0].claimId, "verdict": "REMOVE", "reason": "无来源"}],
        )
        assert applied == 1
        assert claims[0].publicationDecision == "REMOVE"

    def test_review_cannot_downgrade_below_deterministic_floor(self):
        claims = extract_claims(
            {"materialContent": "车企希望通过主动通报控制舆论。"}, event_id="e1"
        )
        assert claims[0].publicationDecision == "REWRITE"
        apply_review_verdicts(claims, [{"claimId": claims[0].claimId, "verdict": "KEEP"}])
        assert claims[0].publicationDecision == "REWRITE"

    def test_revised_statement_is_captured(self):
        claims = self._claims()
        apply_review_verdicts(
            claims,
            [{
                "claimId": claims[0].claimId,
                "verdict": "REWRITE",
                "revisedStatement": "改写后的表述",
            }],
        )
        assert claims[0].revisedStatement == "改写后的表述"

    def test_unmatched_review_is_ignored(self):
        claims = self._claims()
        assert apply_review_verdicts(claims, [{"claimId": "nope", "verdict": "REMOVE"}]) == 0

    def test_matches_by_statement_when_id_absent(self):
        claims = self._claims()
        apply_review_verdicts(
            claims, [{"statement": claims[0].statement, "verdict": "QUALIFY"}]
        )
        assert claims[0].publicationDecision == "QUALIFY"


class TestRenderClaimsForReview:
    def test_renders_ids_and_types(self):
        claims = extract_claims({"materialContent": "该企业发布了召回公告。"}, event_id="e1")
        text = render_claims_for_review(claims)
        assert claims[0].claimId in text
        assert "claimId=" in text

    def test_empty_returns_placeholder(self):
        assert "未抽取到断言" in render_claims_for_review([])
