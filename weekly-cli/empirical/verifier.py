"""Empirical Layer: Evidence Verifier.

Grades sources using the Admiralty grading system (A-F reliability, 1-6 credibility),
checks independent corroboration, and generates Analysis of Competing Hypotheses (ACH)
matrices for core explanatory propositions.

Gracefully degrades: returns None on ANY failure so the pipeline continues.
"""
import json

from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt

VERIFIER_PROMPT = load_prompt("empirical/verifier")

KEY_FIELDS = (
    "verificationSummary",
    "sourceGrades",
    "verificationResults",
    "corroborationMatrix",
    "achResults",
    "informationGaps",
)


def format_event_for_verifier(event: dict) -> str:
    """Serialize an event dict to a JSON string for the verifier prompt.

    Uses ensure_ascii=False to preserve Chinese characters and
    limited indentation to keep prompt size manageable.
    Truncates overly long fields to prevent prompt overflow.
    """
    try:
        # Make a shallow copy to avoid mutating the original
        safe = {}
        for k, v in event.items():
            if isinstance(v, str) and len(v) > 3000:
                safe[k] = v[:3000] + "...(truncated)"
            elif isinstance(v, list) and len(v) > 50:
                safe[k] = v[:50]
            else:
                safe[k] = v
        return json.dumps(safe, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        # Fallback: convert to string representation
        return json.dumps(
            {k: str(v)[:1000] for k, v in event.items()},
            ensure_ascii=False,
            indent=2,
        )


def _has_minimal_event_content(event: dict | None) -> bool:
    """Check that the event has enough content for verification.

    Needs at least a title and either a summary, evidence list, or
    dialectical summary to be worth verifying.
    """
    if not event or not isinstance(event, dict):
        return False
    title = event.get("title")
    if not title or not isinstance(title, str) or not title.strip():
        return False
    if event.get("summary"):
        return True
    if event.get("evidence") and isinstance(event.get("evidence"), list) and len(event["evidence"]) > 0:
        return True
    if event.get("dialecticalSummary"):
        return True
    return False


def _sanitize_list_field(result: dict, field: str) -> None:
    """Ensure a field in result is a list, replacing non-lists with empty list."""
    val = result.get(field)
    if val is None or not isinstance(val, list):
        result[field] = []


def verify_evidence(
    client: DeepSeekClient | None,
    event: dict,
) -> dict | None:
    """Run evidence verification against a single event.

    Performs three operations:
    1. Source grading using the Admiralty scale (reliability A-F, credibility 1-6)
    2. Independent corroboration check (cross-validation across sources)
    3. Analysis of Competing Hypotheses (ACH) matrix generation

    Args:
        client: A DeepSeekClient instance (uses empirical model for lighter load).
        event: A dict representing a single event with title, summary, evidence,
               timeline, dialecticalSummary, and related fields.

    Returns:
        A dict with verificationSummary, sourceGrades, verificationResults,
        corroborationMatrix, achResults, and informationGaps,
        or None on ANY failure (graceful degradation).
    """
    if client is None:
        return None

    if not _has_minimal_event_content(event):
        return None

    event_json = format_event_for_verifier(event)

    prompt = VERIFIER_PROMPT.format(
        event_count=1,
        dialectical_output=event_json,
    )

    try:
        result = client.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是一个证据审查员（Evidence Reviewer）。你的任务是对"
                        "事件分析进行证据质量审查——来源分级、交叉验证、竞争性"
                        "假设分析。严格按JSON格式输出。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=8192,
        )
    except Exception:
        # Graceful degradation: any LLM call failure returns None
        return None

    # ── Defensive: validate response structure ──
    if not isinstance(result, dict):
        return None

    # Ensure all expected fields exist and are lists where appropriate
    if result.get("verificationSummary") is None:
        result["verificationSummary"] = ""

    for field in (
        "sourceGrades",
        "verificationResults",
        "corroborationMatrix",
        "achResults",
        "informationGaps",
    ):
        _sanitize_list_field(result, field)

    return result
