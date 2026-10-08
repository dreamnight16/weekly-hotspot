"""Narrative layer: applying revision directives to the analysis.

The pipeline previously produced adversarial reviews that nothing consumed: an
adversary could correctly identify an unsupported motive attribution and the
sentence still shipped verbatim.  This module closes that loop by turning each
directive into a concrete edit of the analysis text.

Applying edits is deliberately deterministic.  Asking a model to apply its own
critique introduces a second uncontrolled generation step between the finding
and the fix, which is exactly where a correction gets quietly dropped.
"""

from __future__ import annotations

from typing import Iterable

from config import get_logger
from evidence.claims import get_path, hedge_statement

logger = get_logger("narrative.revision")

# Suffix appended to a claim that is kept but downgraded.  Kept short so it
# reads as an epistemic marker rather than as an editorial apology.
QUALIFY_SUFFIX = "（此为推断，尚无直接证据支持）"
ATTRIBUTED_QUALIFY_SUFFIX = "（该说法尚待独立来源核实）"


def _set_path(obj: dict, path: str, value: object) -> bool:
    """Assign a dotted path inside nested dicts.  Returns True on success."""
    parts = path.split(".")
    cur = obj
    for part in parts[:-1]:
        if not isinstance(cur, dict) or part not in cur:
            return False
        cur = cur[part]
    if not isinstance(cur, dict):
        return False
    cur[parts[-1]] = value
    return True


def _replace_in_list(analysis: dict, path: str, old: str, new: str | None) -> bool:
    """Apply a replacement to a string item of a list field."""
    value = get_path(analysis, path)
    if not isinstance(value, list):
        return False
    changed = False
    for i, item in enumerate(value):
        if isinstance(item, str) and old in item:
            if new is None:
                value.pop(i)
            else:
                value[i] = item.replace(old, new, 1)
            changed = True
            break
    return changed


def revise_statement(claim) -> str | None:
    """Compute the replacement text for one claim, or None to delete it.

    REWRITE means "the premise does not support this form of words", which for
    a motive attribution means adding the conditional rather than dropping the
    hypothesis.  Deleting it would satisfy the gate and lose the analysis.
    """
    decision = getattr(claim, "publicationDecision", "UNREVIEWED")
    statement = getattr(claim, "statement", "") or ""

    if decision == "KEEP":
        return statement
    if decision == "REMOVE":
        return None
    if decision == "REWRITE":
        # A reviewer-supplied rewrite is used verbatim when present: it is a
        # considered replacement, not a mechanical hedge.
        supplied = getattr(claim, "revisedStatement", None)
        if supplied and supplied.strip():
            return supplied.strip()
        rewritten = hedge_statement(statement)
        if rewritten.strip() == statement.strip():
            rewritten = statement + QUALIFY_SUFFIX
        return rewritten
    if decision == "QUALIFY":
        supplied = getattr(claim, "revisedStatement", None)
        if supplied and supplied.strip():
            return supplied.strip()
        # Low-risk unsourced statements are flagged in the claim ledger, which
        # the writer reads and the gate counts, rather than annotated inline.
        # Marking every such sentence in place buries the article in
        # parentheticals while adding no information the ledger does not carry.
        if getattr(claim, "riskLevel", "") == "low":
            return statement
        if getattr(claim, "type", "") == "ATTRIBUTED":
            return statement + ATTRIBUTED_QUALIFY_SUFFIX
        return statement + QUALIFY_SUFFIX
    # RESEARCH leaves the text in place; the gap is recorded, not papered over.
    return statement


def apply_revisions(
    analysis: dict,
    claims: Iterable,
    *,
    round_no: int = 1,
) -> tuple[dict, list]:
    """Apply every non-KEEP directive to *analysis* in place.

    Returns the mutated analysis and the RevisionRecords describing what
    actually changed, so a judgment change is auditable after the fact.
    """
    from schema import RevisionRecord

    records: list = []
    for claim in claims:
        decision = getattr(claim, "publicationDecision", "UNREVIEWED")
        if decision in ("KEEP", "UNREVIEWED", "RESEARCH"):
            if decision == "RESEARCH":
                records.append(
                    RevisionRecord(
                        claimId=getattr(claim, "claimId", ""),
                        eventId=getattr(claim, "eventId", ""),
                        path=getattr(claim, "path", ""),
                        action="RESEARCH",
                        before=getattr(claim, "statement", ""),
                        after=getattr(claim, "statement", ""),
                        reason="证据不足，需补充检索",
                        round=round_no,
                    )
                )
            continue

        statement = getattr(claim, "statement", "") or ""
        path = getattr(claim, "path", "") or ""
        replacement = revise_statement(claim)
        if replacement is not None and replacement.strip() == statement.strip():
            # Decision recorded on the claim, text deliberately unchanged.
            continue
        before_field = get_path(analysis, path)

        applied = False
        if isinstance(before_field, str) and statement in before_field:
            new_field = (
                before_field.replace(statement, replacement, 1)
                if replacement is not None
                else before_field.replace(statement, "", 1)
            )
            applied = _set_path(analysis, path, new_field)
        else:
            applied = _replace_in_list(analysis, path, statement, replacement)

        if not applied:
            logger.debug(
                "revision not applied (path %r not found): %s", path, statement[:40]
            )
            continue

        records.append(
            RevisionRecord(
                claimId=getattr(claim, "claimId", ""),
                eventId=getattr(claim, "eventId", ""),
                path=path,
                action=decision,
                before=statement,
                after=replacement or "",
                reason=getattr(claim, "reason", ""),
                round=round_no,
            )
        )

    return analysis, records


def summarise_records(records: Iterable) -> dict[str, int]:
    """Count applied revisions by action, for logs and the quality report."""
    counts: dict[str, int] = {}
    for rec in records:
        action = getattr(rec, "action", "UNKNOWN")
        counts[action] = counts.get(action, 0) + 1
    return counts
