"""Evidence layer for 格物 (Dianalyze).

Builds the fact file that deep analysis reads from, so the dialectical phases
start from retrieved material instead of from a headline and a heat ranking.
"""

from evidence.claims import (
    CLAIM_TYPES,
    classify_claim,
    extract_claims,
    hedge_statement,
    initial_decision,
    split_sentences,
    supporting_source_ids,
    verification_status,
)
from evidence.collector import (
    collect_dossier,
    detect_numeric_conflicts,
    dossier_claim_context,
    dossier_to_text,
    expand_queries,
    extract_entities,
)
from evidence.sources import (
    build_source_record,
    classify_source_kind,
    content_fingerprint,
    content_similarity,
    dedupe_by_url,
    fetch_page,
    mark_republications,
    normalize_url,
    parse_page,
)
from evidence.store import load_dossiers, save_dossiers

__all__ = [
    "CLAIM_TYPES",
    "classify_claim",
    "extract_claims",
    "hedge_statement",
    "initial_decision",
    "split_sentences",
    "supporting_source_ids",
    "verification_status",
    "collect_dossier",
    "detect_numeric_conflicts",
    "dossier_claim_context",
    "dossier_to_text",
    "expand_queries",
    "extract_entities",
    "build_source_record",
    "classify_source_kind",
    "content_fingerprint",
    "content_similarity",
    "dedupe_by_url",
    "fetch_page",
    "mark_republications",
    "normalize_url",
    "parse_page",
    "load_dossiers",
    "save_dossiers",
]
