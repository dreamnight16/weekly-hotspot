"""Quality gates for 格物 (Dianalyze).

Two distinct gates live here and they are not interchangeable:

`is_quality_event` filters Phase 3 output for *analytical substance*.  It has
always asked only whether the dialectical analysis is filled in, which means a
framework can satisfy it completely while resting on no evidence at all.

`publication_gate` is the publish-time decision.  It is deterministic on
purpose: a gate implemented as another model call is just another uncontrolled
generator, and the thing it is supposed to catch would flow straight through it.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional

from config import get_logger

logger = get_logger("quality")

ALLOW = "ALLOW"
DEGRADE = "DEGRADE"
BLOCK = "BLOCK"


def is_quality_event(event: dict) -> bool:
    """Quality gate for a single dialectically-analyzed event (Phase 3).

    An event must have:
    - dialecticalConfidence that is not LOW
    - substantive dialectical content (at least one of unityOfOpposites /
      quantityQuality / negationOfNegation contributes a >= 10-char string)
    - a title
    """
    confidence = event.get("dialecticalConfidence", "LOW")
    if confidence == "LOW":
        return False

    uoo = event.get("unityOfOpposites", {})
    qq = event.get("quantityQuality", {})
    non_ = event.get("negationOfNegation", {})

    has_dialectical_content = any([
        isinstance(uoo, dict) and any(
            v for v in uoo.values() if isinstance(v, str) and len(v) >= 10
        ),
        isinstance(qq, dict) and any(
            v for v in qq.values() if isinstance(v, str) and len(v) >= 10
        ),
        isinstance(non_, dict) and any(
            v for v in non_.values() if isinstance(v, str) and len(v) >= 10
        ),
    ])

    if not has_dialectical_content:
        return False

    if not event.get("title"):
        return False

    return True


def is_quality_issue(issue) -> bool:
    """Quality gate for a complete WeeklyIssue.

    A WeeklyIssue must have:
    - At least one event
    - Both phase1 and phase2 present
    """
    events = getattr(issue, "events", [])
    if not events:
        return False
    if getattr(issue, "phase1", None) is None:
        return False
    if getattr(issue, "phase2", None) is None:
        return False
    return True


# =============================================================================
# Publication gate
# =============================================================================

# Below this many distinct-origin sources, key facts are treated as unconfirmed.
MIN_INDEPENDENT_SOURCES = 1


def assess_evidence(dossier) -> tuple[str, list[str]]:
    """Classify how well an event's fact base supports deep analysis.

    Returns (status, reasons) where status is "sufficient", "thin", or "absent".
    """
    if dossier is None:
        return "absent", ["未建立证据档案"]

    reasons: list[str] = []
    if getattr(dossier, "searchFailed", False):
        return "absent", ["检索失败，未获得任何来源"]

    sources = list(getattr(dossier, "sources", []) or [])
    if not sources:
        return "absent", ["无来源"]

    independent = getattr(dossier, "independent_count", 0)
    if independent < MIN_INDEPENDENT_SOURCES:
        return "thin", [
            f"仅有转载来源（{len(sources)} 条），无原始或独立来源"
        ]

    # Disagreement among sources is a downgrade: we cannot state a fact that
    # our own material contradicts.
    if getattr(dossier, "conflicts", None):
        return "thin", [f"来源间存在 {len(dossier.conflicts)} 处数值分歧"]

    # Absence of a primary document is worth disclosing but is not itself a
    # defect: plenty of real events are known only through independent
    # reporting, and demanding a primary for every one would block publication
    # of everything the authorities never wrote down.
    if not getattr(dossier, "has_primary", False):
        reasons.append("缺少原始来源，关键结论以独立报道为准")

    return "sufficient", reasons


def validate_claim_references(claims: Iterable, dossiers: Iterable) -> list[str]:
    """Check every cited evidence id actually exists in the dossiers.

    A citation that resolves to nothing is worse than no citation: it looks
    like traceability while providing none.
    """
    known: set[str] = set()
    for dossier in dossiers or []:
        for src in getattr(dossier, "sources", []) or []:
            known.add(getattr(src, "sourceId", ""))

    dangling: list[str] = []
    for claim in claims or []:
        for ev_id in getattr(claim, "evidenceIds", []) or []:
            if ev_id and ev_id not in known:
                dangling.append(
                    f"{getattr(claim, 'claimId', '?')} 引用了不存在的证据 {ev_id}"
                )
    return dangling


def scan_residual_risk(analysis_by_event: dict) -> list:
    """Re-extract claims from the *revised* text and return any still high-risk.

    This is what makes the revision loop verifiable rather than aspirational:
    it checks the text that is actually about to be published, not the
    directives that were supposed to change it.
    """
    from evidence.claims import extract_claims

    residual: list = []
    for event_id, analysis in (analysis_by_event or {}).items():
        try:
            claims = extract_claims(
                analysis, event_id=event_id, sources=[], claim_prefix="post"
            )
        except Exception as exc:
            logger.warning("[gate] 复核断言失败 %s: %s", event_id, exc)
            continue
        residual.extend(c for c in claims if getattr(c, "riskLevel", "") == "high")
    return residual


# Markdown decoration stripped before classifying a sentence.  A bullet and
# a bold marker do not change whether a claim asserts a motive as fact.
_MD_PREFIX_RE = re.compile(r"^[\s>#*\-\d.、]+")

MIN_CLASSIFIABLE_CHARS = 10


def scan_text_risk(text: str) -> list:
    """Sentence-level risk scan of arbitrary prose, such as a written article.

    Applied to the generated narrative this is the check that the writer
    honoured the ledger; the ledger governs what it was *told* it could say,
    and this governs what it actually said.
    """
    from evidence.claims import classify_claim, split_sentences
    from schema import ClaimRecord

    risky: list = []
    for i, raw in enumerate(split_sentences(text or "")):
        stripped = _MD_PREFIX_RE.sub("", raw).strip()
        if len(stripped) < MIN_CLASSIFIABLE_CHARS:
            continue
        claim_type, risk = classify_claim(stripped)
        if risk != "high":
            continue
        risky.append(
            ClaimRecord(
                claimId=f"text-{i:03d}",
                statement=raw.strip(),
                type=claim_type,
                riskLevel=risk,
                reason="正文中出现未加限定的高风险断言",
            )
        )
    return risky


def sanitize_narrative(text: str) -> tuple[str, list[str]]:
    """Downgrade high-risk sentences in generated prose.

    Sentences are hedged rather than deleted: the analysis is the point of the
    article, and dropping it would trade a false certainty for a silent loss of
    substance.  Only the certainty changes.
    """
    from evidence.claims import hedge_statement

    out = text or ""
    notes: list[str] = []
    for claim in scan_text_risk(out):
        original = claim.statement
        if not original or original not in out:
            continue
        replacement = hedge_statement(original)
        if replacement.strip() == original.strip():
            replacement = original + "（此为推断，尚无直接证据支持）"
        out = out.replace(original, replacement, 1)
        notes.append(f"正文高风险断言已降低确定性：{original[:40]}")
    return out, notes


def publication_gate(
    *,
    dossiers: Iterable = (),
    claims: Iterable = (),
    analysis_by_event: Optional[dict] = None,
    report_only: bool = False,
) -> "PublicationGate":
    """Decide whether this issue may be published, degraded, or blocked.

    BLOCK  — a serious defect survives into the text: an unfixed unfounded
             motive attribution, a dangling evidence citation, or a critical
             fact explicitly contradicted by sources.
    DEGRADE— the event matters but its fact base is thin.  Publish facts,
             disputes, and open questions only, with no confident conclusion.
    ALLOW  — key facts are traceable, inferences are labelled, nothing serious
             is unresolved.
    """
    from schema import PublicationGate

    dossier_list = list(dossiers or [])
    claim_list = list(claims or [])
    blocking: list[str] = []
    degraded: list[str] = []

    # 1. Untraceable citations are a hard defect.
    for problem in validate_claim_references(claim_list, dossier_list):
        blocking.append(problem)

    # 2. Unfixed high-risk assertions in the publishable text.
    residual = scan_residual_risk(analysis_by_event or {})
    for claim in residual:
        blocking.append(
            f"未修正的高风险断言（{claim.type}）：{claim.statement[:40]}"
        )

    # 3. Unsupported factual claims that no rule managed to remove.
    for claim in claim_list:
        if getattr(claim, "type", "") in ("FACT", "ATTRIBUTED") and not getattr(
            claim, "evidenceIds", None
        ):
            degraded.append(
                f"{getattr(claim, 'claimId', '?')} 无来源支持："
                f"{getattr(claim, 'statement', '')[:40]}"
            )

    # 4. Evidence sufficiency across the selected events.
    statuses = [assess_evidence(d) for d in dossier_list]
    absent = sum(1 for status, _ in statuses if status == "absent")
    thin = sum(1 for status, _ in statuses if status == "thin")
    notes: list[str] = []
    for status, reasons in statuses:
        if status == "sufficient":
            notes.extend(reasons)
        else:
            degraded.extend(reasons)

    if blocking:
        decision = BLOCK
    elif not dossier_list:
        # Nothing was retrieved at all: there is no basis on which to publish
        # confident conclusions, even if no individual rule fired.
        decision = DEGRADE
    elif degraded:
        # Covers unsupported factual claims as well as thin or absent evidence.
        decision = DEGRADE
    else:
        decision = ALLOW

    if report_only and decision == BLOCK:
        # Used when the caller has already exhausted its revision rounds: the
        # issue is published in degraded form rather than silently dropped.
        decision = DEGRADE
        blocking.append("修订轮次用尽，降级为事实与争议摘要")

    gate = PublicationGate(
        decision=decision,
        reasons=list(dict.fromkeys(notes + degraded + blocking)),
        blockingClaims=blocking,
        degradedClaims=degraded,
    )
    logger.info(
        "[gate] 发布判定: %s（阻断项 %d，降级项 %d）",
        gate.decision, len(blocking), len(degraded),
    )
    return gate
