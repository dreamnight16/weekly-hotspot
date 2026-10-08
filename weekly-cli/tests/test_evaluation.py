"""Tests for the content regression harness."""
import json

import pytest

from evaluation.metrics import (
    analysis_retention,
    evidence_coverage,
    interception_rate,
    summarize,
    unfounded_attribution_rate,
    unsupported_fact_rate,
)
from evaluation.runner import format_report, load_cases, run_all, run_case
from schema import ClaimRecord


def _claim(**kwargs):
    base = {"claimId": "c1", "statement": "x", "type": "FACT"}
    base.update(kwargs)
    return ClaimRecord(**base)


class TestUnsupportedFactRate:
    def test_all_unsourced(self):
        assert unsupported_fact_rate([_claim(), _claim(claimId="c2")]) == 1.0

    def test_all_sourced(self):
        claims = [_claim(evidenceIds=["s1"]), _claim(claimId="c2", evidenceIds=["s2"])]
        assert unsupported_fact_rate(claims) == 0.0

    def test_inferences_are_excluded(self):
        """An inference legitimately has no source; counting it would punish correctness."""
        assert unsupported_fact_rate([_claim(type="INFERENCE")]) == 0.0

    def test_no_factual_claims(self):
        assert unsupported_fact_rate([]) == 0.0


class TestUnfoundedAttributionRate:
    def test_unrepaired_attribution_counts(self):
        claim = _claim(
            type="HYPOTHESIS", riskLevel="high", publicationDecision="UNREVIEWED"
        )
        assert unfounded_attribution_rate([claim]) == 1.0

    def test_repaired_attribution_does_not_count(self):
        claim = _claim(
            type="HYPOTHESIS", riskLevel="high", publicationDecision="REWRITE"
        )
        assert unfounded_attribution_rate([claim]) == 0.0

    def test_empty(self):
        assert unfounded_attribution_rate([]) == 0.0


class TestEvidenceCoverage:
    def test_no_high_risk_claims_is_full_coverage(self):
        assert evidence_coverage([]) == 1.0

    def test_partial(self):
        claims = [
            _claim(riskLevel="high", evidenceIds=["s1"]),
            _claim(claimId="c2", riskLevel="high"),
        ]
        assert evidence_coverage(claims) == 0.5


class TestInterceptionAndRetention:
    def test_interception_rate(self):
        assert interception_rate(4, 3) == 0.75

    def test_interception_zero_detected(self):
        assert interception_rate(0, 0) == 0.0

    def test_retention_full(self):
        assert analysis_retention("abcd", "abcd", []) == 1.0

    def test_retention_partial(self):
        assert analysis_retention("abcd", "ab", []) == 0.5

    def test_retention_empty_before(self):
        assert analysis_retention("", "x", []) == 1.0

    def test_retention_clamped(self):
        assert analysis_retention("ab", "abcdef", []) == 1.0


class TestSummarize:
    def test_empty(self):
        assert summarize([]) == {"cases": 0}

    def test_aggregates(self):
        results = [
            {"caseId": "a", "unsupported_fact_rate": 0.0},
            {"caseId": "b", "unsupported_fact_rate": 1.0},
        ]
        out = summarize(results)
        assert out["cases"] == 2
        assert out["unsupported_fact_rate"] == 0.5


class TestRunCase:
    def _case(self, **kwargs):
        case = {
            "caseId": "test-1",
            "title": "测试",
            "analysis": {"materialContent": "车企希望通过主动通报控制舆论，避免召回。"},
            "sources": [],
            "forbiddenAssertions": ["希望通过主动通报控制舆论，避免召回"],
            "mustPreserve": [],
        }
        case.update(kwargs)
        return case

    def test_repaired_case_has_no_violations(self):
        result = run_case(self._case())
        assert result["violations"] == []
        assert result["high_risk_after"] == 0

    def test_unrepaired_case_is_flagged(self):
        """Without revision the forbidden assertion survives and must be caught."""
        case = self._case(mustPreserve=["不存在的短语"])
        result = run_case(case)
        assert any("应当保留" in v for v in result["violations"])

    def test_hedged_occurrence_is_not_a_violation(self):
        case = self._case()
        result = run_case(case)
        assert not any("确定语气" in v for v in result["violations"])


class TestLoadCases:
    def test_loads_repo_cases(self):
        cases = load_cases()
        assert len(cases) > 0
        assert all("caseId" in c for c in cases)

    def test_skips_invalid_files(self, tmp_path):
        (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
        (tmp_path / "nocase.json").write_text(json.dumps({"x": 1}), encoding="utf-8")
        good = {"caseId": "ok", "analysis": {}}
        (tmp_path / "good.json").write_text(json.dumps(good), encoding="utf-8")
        cases = load_cases(tmp_path)
        assert [c["caseId"] for c in cases] == ["ok"]

    def test_missing_dir_returns_empty(self, tmp_path):
        assert load_cases(tmp_path / "nope") == []


class TestRunAll:
    def test_repo_case_set_passes(self):
        """The seeded real-world cases are the regression gate."""
        report = run_all()
        assert report["cases"] > 0
        assert report["failed_cases"] == [], format_report(report)

    def test_motive_attribution_rate_is_zero(self):
        report = run_all()
        assert report["unfounded_attribution_rate"] == 0.0

    def test_analysis_is_not_gutted(self):
        """Guards the mirror-image failure: a gate that deletes everything."""
        report = run_all()
        assert report["analysis_retention"] > 0.9


class TestFormatReport:
    def test_renders_metrics(self):
        text = format_report(run_all())
        assert "错误动机归因率" in text
        assert "有效分析保留率" in text
