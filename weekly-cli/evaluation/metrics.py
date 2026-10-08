"""Content-level evaluation metrics for 格物 (Dianalyze).

Unit test coverage says the code does what it was written to do.  It says
nothing about whether the *output* is factually grounded, and the pipeline's
characteristic failures are content failures: an unsupported motive stated as
fact, a single wire story counted as three witnesses, a framework imposed on an
event that does not support it.

These metrics measure the output.  They are computed deterministically so a
regression in prompt wording cannot hide behind a different retrieval run.
"""

from __future__ import annotations

from typing import Iterable


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def unsupported_fact_rate(claims: Iterable) -> float:
    """Share of factual claims that carry no supporting source.

    Factual assertions are FACT and ATTRIBUTED.  Inferences are excluded: an
    inference legitimately has no source, and counting it here would make the
    metric punish correct behaviour.
    """
    factual = [c for c in claims if getattr(c, "type", "") in ("FACT", "ATTRIBUTED")]
    unsupported = [c for c in factual if not getattr(c, "evidenceIds", None)]
    return _rate(len(unsupported), len(factual))


def unfounded_attribution_rate(claims: Iterable) -> float:
    """Share of motive attributions that are asserted rather than hypothesised.

    The numerator counts assertions that still read as fact.  A hedged motive
    ("the firm may have...") is the correct output and is not counted.
    """
    motives = [
        c
        for c in claims
        if "动机" in getattr(c, "reason", "")
        or getattr(c, "type", "") == "HYPOTHESIS"
    ]
    asserted = [
        c
        for c in motives
        if getattr(c, "riskLevel", "") == "high"
        and getattr(c, "publicationDecision", "") not in ("REWRITE", "REMOVE")
    ]
    return _rate(len(asserted), len(motives))


def evidence_coverage(claims: Iterable) -> float:
    """Share of high-risk claims that cite at least one source."""
    risky = [c for c in claims if getattr(c, "riskLevel", "") == "high"]
    if not risky:
        return 1.0
    covered = [c for c in risky if getattr(c, "evidenceIds", None)]
    return _rate(len(covered), len(risky))


def interception_rate(detected: int, intercepted: int) -> float:
    """Share of detected serious defects that were actually removed or hedged."""
    return _rate(intercepted, detected)


def analysis_retention(before: str, after: str, removed_markers: Iterable[str]) -> float:
    """Share of non-defective text preserved through revision.

    Guards the mirror-image failure: a gate so aggressive it deletes good
    analysis passes every safety metric while destroying the product.
    """
    total = len(before or "")
    if not total:
        return 1.0
    return max(0.0, min(1.0, len(after or "") / total))


def summarize(results: list[dict]) -> dict:
    """Aggregate per-case results into a report."""
    if not results:
        return {"cases": 0}
    keys = (
        "unsupported_fact_rate",
        "unfounded_attribution_rate",
        "evidence_coverage",
        "interception_rate",
        "analysis_retention",
    )
    summary: dict = {"cases": len(results)}
    for key in keys:
        values = [r[key] for r in results if key in r]
        summary[key] = round(sum(values) / len(values), 4) if values else 0.0
    summary["failed_cases"] = [
        r["caseId"] for r in results if r.get("violations")
    ]
    return summary
