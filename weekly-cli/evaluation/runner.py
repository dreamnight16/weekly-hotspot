"""Evaluation runner: replays fixed cases through the evidence pipeline.

Runs offline and deterministically.  Retrieval is not exercised here on
purpose: comparing prompt versions against different search results would
measure the search engine, not the prompts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Support direct invocation by putting the package root on the path, mirroring
# what pytest's conftest does for the test suite.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import get_logger
from evidence.claims import extract_claims
from evaluation.metrics import (
    analysis_retention,
    evidence_coverage,
    interception_rate,
    summarize,
    unfounded_attribution_rate,
    unsupported_fact_rate,
)
from narrative.revision import apply_revisions

logger = get_logger("evaluation.runner")

CASES_DIR = Path(__file__).parent / "cases"


def load_cases(cases_dir: Path | None = None) -> list[dict]:
    """Load every case file, sorted by id for reproducible ordering."""
    directory = cases_dir or CASES_DIR
    cases: list[dict] = []
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("[eval] 跳过无法解析的案例 %s: %s", path.name, exc)
            continue
        if isinstance(data, dict) and "caseId" in data:
            cases.append(data)
    return cases


def _serialize(analysis: dict) -> str:
    return json.dumps(analysis, ensure_ascii=False, sort_keys=True)


def run_case(case: dict) -> dict:
    """Replay one case and measure the outcome."""
    from schema import SourceRecord

    case_id = case.get("caseId", "unknown")
    analysis = dict(case.get("analysis") or {})
    sources = [
        SourceRecord(**s)
        for s in case.get("sources", [])
        if isinstance(s, dict)
    ]
    forbidden = [s for s in case.get("forbiddenAssertions", []) if s]
    must_preserve = [s for s in case.get("mustPreserve", []) if s]

    before_text = _serialize(analysis)
    before_claims = extract_claims(analysis, event_id=case_id, sources=sources)

    detected = [c for c in before_claims if c.riskLevel == "high"]
    revised, records = apply_revisions(analysis, before_claims, round_no=1)
    after_text = _serialize(revised)
    after_claims = extract_claims(revised, event_id=case_id, sources=sources)

    violations: list[str] = []

    # 1. Assertions the case declares must not survive *as assertions*.  The
    #    phrase may legitimately remain inside a hedged sentence -- that is the
    #    intended repair -- so the check classifies the containing sentence
    #    rather than testing for the substring.
    from evidence.claims import classify_claim, split_sentences

    for phrase in forbidden:
        if phrase not in after_text:
            continue
        for sentence in split_sentences(after_text):
            if phrase not in sentence:
                continue
            _type, risk = classify_claim(sentence)
            if risk == "high":
                violations.append(f"禁止断言仍以确定语气存在：{phrase[:40]}")
                break

    # 2. No high-risk assertion may remain unhedged.
    residual = [c for c in after_claims if c.riskLevel == "high"]
    for claim in residual:
        violations.append(f"残留高风险断言：{claim.statement[:40]}")

    # 3. Valuable analysis must not be lost (over-conservatism check).
    for phrase in must_preserve:
        if phrase not in after_text:
            violations.append(f"应当保留的分析被删除：{phrase[:40]}")

    intercepted = sum(
        1
        for c in detected
        if c.publicationDecision in ("REMOVE", "REWRITE", "QUALIFY")
    )

    return {
        "caseId": case_id,
        "title": case.get("title", ""),
        "category": case.get("category", ""),
        "claims": len(before_claims),
        "high_risk_before": len(detected),
        "high_risk_after": len(residual),
        "revisions": {r.action: 1 for r in records},
        "unsupported_fact_rate": round(unsupported_fact_rate(after_claims), 4),
        "unfounded_attribution_rate": round(
            unfounded_attribution_rate(after_claims), 4
        ),
        "evidence_coverage": round(evidence_coverage(after_claims), 4),
        "interception_rate": round(interception_rate(len(detected), intercepted), 4),
        "analysis_retention": round(
            analysis_retention(
                before_text, after_text, [c.statement for c in before_claims]
            ),
            4,
        ),
        "violations": violations,
    }


def run_all(cases_dir: Path | None = None) -> dict:
    """Replay every case and return the aggregate report."""
    cases = load_cases(cases_dir)
    results = [run_case(case) for case in cases]
    report = summarize(results)
    report["results"] = results
    return report


def main() -> int:
    """Run the evaluation and return a process exit code."""
    import argparse

    parser = argparse.ArgumentParser(description="格物内容回归评测")
    parser.add_argument("--cases-dir", type=Path, default=None)
    parser.add_argument(
        "--allow-violations", action="store_true",
        help="只报告不失败（用于建立基线时）",
    )
    args = parser.parse_args()

    report = run_all(args.cases_dir)
    print(format_report(report))
    if report.get("failed_cases") and not args.allow_violations:
        return 1
    return 0


def format_report(report: dict) -> str:
    """Render the report as readable text for CI logs."""
    lines = [
        "格物 内容回归评测",
        f"案例数: {report.get('cases', 0)}",
        "",
        f"无依据事实断言率   {report.get('unsupported_fact_rate', 0):.3f}",
        f"错误动机归因率     {report.get('unfounded_attribution_rate', 0):.3f}",
        f"关键断言证据覆盖率 {report.get('evidence_coverage', 0):.3f}",
        f"严重错误拦截率     {report.get('interception_rate', 0):.3f}",
        f"有效分析保留率     {report.get('analysis_retention', 0):.3f}",
    ]
    failed = report.get("failed_cases") or []
    if failed:
        lines.append("")
        lines.append(f"未通过案例（{len(failed)}）:")
        for result in report.get("results", []):
            if result.get("caseId") in failed:
                lines.append(f"  - {result['caseId']}")
                for violation in result["violations"]:
                    lines.append(f"      {violation}")
    else:
        lines.append("")
        lines.append("全部案例通过。")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
