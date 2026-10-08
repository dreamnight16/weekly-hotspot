"""Evidence layer: claim typing, risk classification, and deterministic hedging.

This module is where "an incentive exists" is stopped from silently becoming
"the actor intended this".  It is deliberately rule-based rather than
model-based: the publication gate must be predictable and regression-testable,
and a model asked to police its own output is just another uncontrolled
generator.

The rules below are heuristics with an explicit, documented bias.  When unsure
they classify *upward* in risk, because the cost of over-hedging an inference
is a weaker sentence, while the cost of under-hedging one is a false accusation.
"""

from __future__ import annotations

import re
from typing import Iterable, Iterator

from config import get_logger
# Re-exported so callers can reach the vocabulary through the evidence package.
from schema import (  # noqa: F401
    CLAIM_TYPES,
    PUBLICATION_DECISIONS,
    VERIFICATION_STATUSES,
)

logger = get_logger("evidence.claims")

# ── Marker vocabularies ──────────────────────────────────────────────────────
# Attributing an intention to an actor.  This is the single most dangerous
# claim class in the pipeline: it reads as fact but can almost never be sourced.
MOTIVE_MARKERS: tuple[str, ...] = (
    "试图", "意图", "旨在", "为了", "希望", "企图", "想要",
    "意在", "谋求", "蓄意", "故意", "刻意", "有意",
)

# Explicit uncertainty.  Its presence downgrades a motive attribution from
# "stated as fact" to "stated as hypothesis".
HEDGE_MARKERS: tuple[str, ...] = (
    "可能", "或许", "大概", "也许", "疑似", "据称", "据传", "推测",
    "尚不确定", "无法确认", "有待", "不排除", "是否存在",
)

LEGAL_MARKERS: tuple[str, ...] = (
    "违法", "犯罪", "触犯", "构成", "欺诈", "侵权", "渎职",
    "过失", "定罪", "量刑", "承担法律责任",
)

CAUSAL_MARKERS: tuple[str, ...] = (
    "导致", "使得", "引发", "造成", "促使", "归因于", "因为", "因而", "从而",
)

ATTRIBUTION_MARKERS: tuple[str, ...] = (
    "称", "表示", "声明", "通报", "回应", "宣布", "指出", "透露",
    "否认", "承认", "公告", "发布", "回应称",
)

UNKNOWN_MARKERS: tuple[str, ...] = (
    "未知", "不明", "尚无定论", "无法确定", "缺乏证据", "信息不足",
    "有待核实", "待核实", "不得而知", "没有公开", "未披露",
)

VALUE_MARKERS: tuple[str, ...] = (
    "应当", "应该", "必须", "不应", "不能", "值得", "需要公开", "有责任",
)

# A specific quantity attached to a claim is a factual assertion in disguise.
_NUMERIC_RE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:亿元|万元|亿|万|元|美元|%|％|个百分点|倍|辆|人|家|次|吨)"
    r"|(?:数|上|近|约|超|逾|几|数[十百千万])(?:十|百|千)?(?:万|亿)"
    r"|(?:十|百|千)?(?:万|亿)(?:元|美元|吨|人|家|辆|次)"
)

# An open question is an UNKNOWN, not an assertion.  "是否存在批量性设计缺陷"
# states no fact at all, and treating it as one inverts its meaning.
_QUESTION_RE = re.compile(r"[？?]|是否|能否|有无|究竟")

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？；!?;\n])")
_CLAUSE_SPLIT_RE = re.compile(r"(?<=[，,、])")

# A claim is considered supported by a source when a meaningful share of the
# claim's character bigrams appear in that source's text.  The threshold is an
# initial experimental parameter, not a measured constant.
SUPPORT_OVERLAP_THRESHOLD = 0.10
_MIN_BIGRAMS = 4

_STOP_BIGRAMS = frozenset(
    {
        "这个", "那个", "以及", "并且", "但是", "因此", "所以", "如果",
        "就是", "在这", "一个", "可以", "没有", "他们", "我们", "什么",
    }
)


def _has_marker(text: str, markers: Iterable[str]) -> bool:
    return any(m in text for m in markers)


def _is_hedged(text: str) -> bool:
    return _has_marker(text, HEDGE_MARKERS)


def split_sentences(text: str) -> list[str]:
    """Split Chinese prose into sentences, keeping the terminating punctuation."""
    if not text:
        return []
    parts = [p.strip() for p in _SENTENCE_SPLIT_RE.split(text)]
    return [p for p in parts if p]


def classify_claim(text: str) -> tuple[str, str]:
    """Classify a statement as (claim_type, risk_level).

    Order matters.  Undecidability and explicit attribution are checked before
    motive and causal reading, because a sentence that says "the company says X"
    is a claim *about a statement*, which is a far weaker and far safer
    assertion than a claim about the world.
    """
    t = (text or "").strip()
    if not t:
        return "UNKNOWN", "low"

    if _has_marker(t, UNKNOWN_MARKERS) or _QUESTION_RE.search(t):
        return "UNKNOWN", "low"

    is_attributed = _has_marker(t, ATTRIBUTION_MARKERS)
    is_motive = _has_marker(t, MOTIVE_MARKERS)
    is_legal = _has_marker(t, LEGAL_MARKERS)
    is_causal = _has_marker(t, CAUSAL_MARKERS)
    hedged = _is_hedged(t)

    # Motive attribution stated as fact — the failure this layer exists to stop.
    if is_motive and not hedged:
        return "HYPOTHESIS", "high"
    if is_motive and hedged:
        return "HYPOTHESIS", "medium"

    # Legal characterisation is high risk unless it is reporting someone else's
    # finding rather than making the finding.  A hedged legal *prediction*
    # ("may face charges") is not the same speech act as a legal *verdict*
    # ("this constituted fraud"), so the hedge still downgrades it.
    if is_legal and not is_attributed:
        return "INFERENCE", "medium" if hedged else "high"

    if is_attributed:
        return "ATTRIBUTED", "medium"

    if _has_marker(t, VALUE_MARKERS):
        return "VALUE_JUDGMENT", "low"

    # A specific figure attached to a claim is a factual assertion in disguise.
    # Hedging the verb ("may save hundreds of millions") does not make the
    # number itself sourced, so it still outranks a plain causal reading.
    if _NUMERIC_RE.search(t) and not is_attributed:
        return "INFERENCE", "medium" if hedged else "high"

    if is_causal:
        return "INFERENCE", "low" if hedged else "medium"

    # A statement that hedges itself is presenting an inference, not a fact —
    # even with no causal or motive marker.  Reading it as FACT would let the
    # gate delete a legitimate hedged reading, which is the mirror-image
    # failure of publishing an unhedged one.
    if hedged:
        return "INFERENCE", "low"

    return "FACT", "low"


def hedge_statement(text: str) -> str:
    """Downgrade an unhedged motive clause to an explicitly conditional one.

    Inserting "可能" before the motive verb is deliberate: it keeps the
    analysis (the reader still sees the hypothesis) while removing the
    assertion of fact.  Deleting the clause instead would satisfy the gate and
    lose the insight, which is its own failure mode.
    """
    if not text:
        return text

    def _repl(match: re.Match[str]) -> str:
        start = match.start()
        window = text[max(0, start - 6) : start]
        if _is_hedged(window):
            return match.group(0)
        return f"可能{match.group(0)}"

    pattern = "|".join(re.escape(m) for m in MOTIVE_MARKERS)
    hedged_text = re.sub(pattern, _repl, text)

    # Strip an accidental double hedge such as "可能可能试图".
    hedged_text = re.sub(r"(可能){2,}", "可能", hedged_text)
    return hedged_text


def _bigrams(text: str) -> set[str]:
    compact = re.sub(r"[\s\W_]+", "", text or "")
    if len(compact) < 2:
        return set()
    grams = {compact[i : i + 2] for i in range(len(compact) - 1)}
    return {g for g in grams if g not in _STOP_BIGRAMS}


def supporting_source_ids(
    statement: str,
    sources: Iterable,
    threshold: float = SUPPORT_OVERLAP_THRESHOLD,
) -> list[str]:
    """Return ids of sources that plausibly support *statement*.

    A source proves only what it actually says, so relatedness is not enough:
    the source text must share a meaningful share of the claim's content
    bigrams.  Absence of support is the normal, expected outcome for
    inferences, and yields an empty list rather than a convenient guess.
    """
    grams = _bigrams(statement)
    if len(grams) < _MIN_BIGRAMS:
        return []
    ids: list[str] = []
    for src in sources:
        body = f"{getattr(src, 'title', '')} {getattr(src, 'content', '')} {getattr(src, 'snippet', '')}"
        src_grams = _bigrams(body)
        if not src_grams:
            continue
        if len(grams & src_grams) / len(grams) >= threshold:
            ids.append(getattr(src, "sourceId", ""))
    return [i for i in ids if i]


# =============================================================================
# Claim extraction: turning analysis prose into addressable, typed assertions
# =============================================================================
# Each extracted claim records the field it came from, so a revision directive
# can rewrite or delete exactly that sentence.  Without an address, a critique
# is just an opinion about the article; with one, it is an edit.

EVENT_CLAIM_PATHS: tuple[str, ...] = (
    "materialContent",
    "phaseSummary",
    "unityOfOpposites.identity",
    "unityOfOpposites.struggle",
    "unityOfOpposites.particularity",
    "unityOfOpposites.universality",
    "quantityQuality.quantitativeDirection",
    "quantityQuality.measure",
    "quantityQuality.newQuality",
    "quantityQuality.oldQualityNegated",
    "negationOfNegation.oldThing",
    "negationOfNegation.firstNegation",
    "negationOfNegation.internalNegation",
    "negationOfNegation.stageCharacteristics",
    "dataValidation.result",
)

EVENT_CLAIM_LISTS: tuple[str, ...] = ("dataValidation.issues",)


def get_path(obj: object, path: str) -> object:
    """Read a dotted path from nested dicts, returning None when absent."""
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def verification_status(claim_type: str, evidence_ids: list[str], sources: Iterable) -> str:
    """Derive how well supported a claim is, given the sources behind it."""
    if not evidence_ids:
        return "UNVERIFIED"
    kinds = {
        getattr(s, "kind", "")
        for s in sources
        if getattr(s, "sourceId", "") in set(evidence_ids)
    }
    independent = kinds & {"PRIMARY", "INDEPENDENT"}
    if len(evidence_ids) >= 2 and independent:
        return "CORROBORATED"
    if evidence_ids:
        return "SINGLE_SOURCE"
    return "UNVERIFIED"


def initial_decision(
    claim_type: str, risk: str, status: str, evidence_ids: list[str]
) -> tuple[str, str]:
    """Assign the first-pass publication decision and its reason.

    This encodes the pipeline's central rule: an inference about intent is not
    disqualified by the absence of evidence — it is disqualified from being
    stated as fact.  Hence REWRITE rather than REMOVE for motive attributions,
    and REMOVE only for assertions that cannot stand in any form.
    """
    supported = bool(evidence_ids)

    if claim_type == "UNKNOWN":
        return "KEEP", "开放问题；保留并列出所需证据"
    if claim_type == "VALUE_JUDGMENT":
        return "KEEP", "价值判断；须注明所依据的规范原则"
    # An unsourced ordinary fact is qualified, not deleted.  Deleting every
    # unsourced sentence would gut an analysis whenever retrieval is thin,
    # which is its own failure: it trades a possible overstatement for a
    # certain loss of substance.  Traceability is enforced at the publication
    # gate, where it can downgrade the whole issue instead of shredding it.
    if claim_type == "FACT" and not supported:
        return "QUALIFY", "事实陈述未见来源支持，须标注为待核实"
    if claim_type == "ATTRIBUTED" and not supported:
        return "QUALIFY", "归属陈述未见来源，须标注为待核实"
    if claim_type == "HYPOTHESIS":
        if risk == "high":
            return "REWRITE", "未加限定的动机归因，须改写为有条件的假说"
        return "KEEP", "已限定为假说"
    if claim_type == "INFERENCE":
        if risk == "high" and not supported:
            return "REMOVE", "高风险推断（具体数额或定性认定）且无证据支持"
        if supported:
            return ("KEEP", "推断有来源支持") if status == "CORROBORATED" else (
                "QUALIFY", "推断仅有单一来源支持"
            )
        return "QUALIFY", "推断无直接来源支持，须降低确定性"
    # FACT
    if not supported:
        return "QUALIFY", "事实陈述未见来源支持"
    return ("KEEP", "事实陈述有来源支持") if status != "SINGLE_SOURCE" else (
        "QUALIFY", "事实陈述仅单一来源支持"
    )


# Severity ordering for combining a deterministic decision with a model's
# review.  The stricter verdict always wins: a model may escalate a concern,
# but it cannot talk the deterministic layer out of one it already found.
_DECISION_SEVERITY: dict[str, int] = {
    "KEEP": 0,
    "UNREVIEWED": 1,
    "RESEARCH": 2,
    "QUALIFY": 3,
    "REWRITE": 4,
    "REMOVE": 5,
}


def render_claims_for_review(claims: Iterable) -> str:
    """Render the claim list a reviewer is asked to adjudicate."""
    claim_list = list(claims or [])
    if not claim_list:
        return "（未抽取到断言）"
    lines = ["## 待审查断言清单", ""]
    for claim in claim_list:
        lines.append(
            f"- claimId={claim.claimId} | 类型={claim.type}"
            f" | 路径={claim.path} | 现有证据={claim.evidenceIds or '无'}"
            f" | 初步判定={claim.publicationDecision}"
        )
        lines.append(f"  {claim.statement}")
        if claim.reason:
            lines.append(f"  系统理由：{claim.reason}")
    return "\n".join(lines)


def stricter_decision(a: str, b: str) -> str:
    """Return whichever decision is more conservative."""
    return a if _DECISION_SEVERITY.get(a, 1) >= _DECISION_SEVERITY.get(b, 1) else b


def _match_claim(claims: list, review: dict):
    """Locate the claim a review refers to, by id, statement, or prefix."""
    claim_id = str(review.get("claimId") or review.get("targetClaimId") or "").strip()
    for claim in claims:
        if claim_id and claim.claimId == claim_id:
            return claim
    statement = str(
        review.get("statement") or review.get("targetClaim") or ""
    ).strip()
    if not statement:
        return None
    for claim in claims:
        if claim.statement.strip() == statement:
            return claim
    for claim in claims:
        head = statement[:16]
        if head and (head in claim.statement or claim.statement[:16] in statement):
            return claim
    return None


def apply_review_verdicts(claims: list, reviews: Iterable) -> int:
    """Fold model review verdicts into the claim set.  Returns how many applied.

    Only ever escalates: the deterministic classification is the floor, and a
    reviewer that disagrees downward cannot lower it.
    """
    applied = 0
    claim_list = list(claims)
    for review in reviews or []:
        if not isinstance(review, dict):
            continue
        target = _match_claim(claim_list, review)
        if target is None:
            continue
        verdict = str(review.get("verdict") or "KEEP").strip().upper()
        if verdict not in PUBLICATION_DECISIONS:
            continue
        merged = stricter_decision(target.publicationDecision, verdict)
        if merged != target.publicationDecision:
            target.publicationDecision = merged
            applied += 1
        revised = review.get("revisedStatement")
        if isinstance(revised, str) and revised.strip():
            target.revisedStatement = revised.strip()
        reason = review.get("reason")
        if isinstance(reason, str) and reason.strip():
            target.reason = f"{target.reason}；复核：{reason.strip()}"
    return applied


def extract_claims(
    analysis: dict,
    *,
    event_id: str,
    sources: Iterable = (),
    claim_prefix: str = "claim",
    text_paths: Iterable[str] = EVENT_CLAIM_PATHS,
    list_paths: Iterable[str] = EVENT_CLAIM_LISTS,
) -> list:
    """Extract typed, addressable claims from one event's analysis tree."""
    from schema import ClaimRecord  # local import keeps schema import-light

    source_list = list(sources)
    claims: list = []
    counter = 0

    def _add(path: str, sentence: str) -> None:
        nonlocal counter
        counter += 1
        claim_type, risk = classify_claim(sentence)
        ev_ids = supporting_source_ids(sentence, source_list)
        status = verification_status(claim_type, ev_ids, source_list)
        decision, reason = initial_decision(claim_type, risk, status, ev_ids)
        claims.append(
            ClaimRecord(
                claimId=f"{claim_prefix}-{counter:03d}",
                eventId=event_id,
                statement=sentence.strip(),
                type=claim_type,
                path=path,
                evidenceIds=ev_ids,
                verificationStatus=status,
                publicationDecision=decision,
                riskLevel=risk,
                reason=reason,
            )
        )

    for path in text_paths:
        value = get_path(analysis, path)
        if isinstance(value, str) and value.strip():
            for sentence in split_sentences(value):
                _add(path, sentence)

    for path in list_paths:
        value = get_path(analysis, path)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    _add(path, item)

    return claims
