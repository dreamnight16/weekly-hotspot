"""Empirical Layer: 9-Dimension Event Scorer.

Calibrates event scores across nine dimensions (D1-D9) with per-dimension
confidence ratings. Each dimension is scored 1-10 via a structured LLM prompt.

Gracefully degrades: returns None on ANY failure so the pipeline continues.
"""
import json
import math

from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt

SCORER_PROMPT = load_prompt("empirical/scorer")

DIMENSION_NAMES = {
    "D1": "影响力规模",
    "D2": "影响范围",
    "D3": "传播速度",
    "D4": "新颖程度",
    "D5": "连锁反应潜能",
    "D6": "行动者显著度",
    "D7": "不确定性",
    "D8": "极性",
    "D9": "持久性",
}

VALID_CONFIDENCE_VALUES = {"高", "中", "低"}


def format_event_for_scorer(event: dict) -> str:
    """Serialize an event dict to a JSON string for the scorer prompt.

    Uses ensure_ascii=False to preserve Chinese characters.
    Truncates overly long string values to prevent prompt overflow.
    """
    try:
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
        return json.dumps(
            {k: str(v)[:1000] for k, v in event.items()},
            ensure_ascii=False,
            indent=2,
        )


def _has_minimal_scoring_content(event: dict | None) -> bool:
    """Check that the event has enough content for scoring.

    Needs at least a title and either a summary or dialecticalSummary.
    """
    if not event or not isinstance(event, dict):
        return False
    title = event.get("title")
    if not title or not isinstance(title, str) or not title.strip():
        return False
    if event.get("summary"):
        return True
    if event.get("dialecticalSummary"):
        return True
    return False


def _validate_dimension_score(score) -> bool:
    """Check that a dimension score is a valid integer 1-10."""
    if score is None:
        return False
    if not isinstance(score, (int, float)):
        return False
    if isinstance(score, float) and not score.is_integer():
        return False
    return 1 <= score <= 10


def _sanitize_dimension(dim: dict, idx: int) -> dict:
    """Sanitize a single dimension dict, applying defaults and clamping.

    Returns a new dict (immutable pattern).
    """
    sanitized = {
        "id": dim.get("id") if dim.get("id") else f"D{idx + 1}",
        "name": dim.get("name") if dim.get("name") else DIMENSION_NAMES.get(f"D{idx + 1}", ""),
        "score": 5,
        "confidence": "低",
        "rationale": dim.get("rationale") if dim.get("rationale") else "",
    }

    # Validate and clamp score
    raw_score = dim.get("score")
    if _validate_dimension_score(raw_score):
        sanitized["score"] = int(raw_score)
    elif isinstance(raw_score, (int, float)):
        # Clamp out-of-range numeric values
        sanitized["score"] = max(1, min(10, int(raw_score)))

    # Validate confidence
    raw_confidence = dim.get("confidence")
    if raw_confidence in VALID_CONFIDENCE_VALUES:
        sanitized["confidence"] = raw_confidence

    return sanitized


def _compute_composite_score(dimensions: list[dict]) -> float:
    """Compute the arithmetic mean of all dimension scores."""
    if not dimensions:
        return 0.0
    scores = [d["score"] for d in dimensions]
    return round(sum(scores) / len(scores), 2)


def score_event(
    client: DeepSeekClient | None,
    event: dict,
) -> dict | None:
    """Calibrate 9-dimension event scores (D1-D9).

    Each dimension is scored 1-10 with per-dimension confidence
    (高/中/低). Returns a composite score as the arithmetic mean.

    Args:
        client: A DeepSeekClient instance (uses empirical model).
        event: A dict representing a single event with at minimum title
               and either summary or dialecticalSummary.

    Returns:
        A dict with eventId, eventTitle, scoringSummary, dimensions (list of 9),
        compositeScore, overallConfidence, and informationSufficiency,
        or None on ANY failure (graceful degradation).
    """
    if client is None:
        return None

    if not _has_minimal_scoring_content(event):
        return None

    event_json = format_event_for_scorer(event)

    prompt = SCORER_PROMPT.format(
        event_json=event_json,
    )

    try:
        result = client.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是一个事件评分校准员。你的任务是对单一事件进行"
                        "九维度定量评分。严格按JSON格式输出。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=4096,
        )
    except Exception:
        return None

    if not isinstance(result, dict):
        return None

    # ── Apply defaults for missing top-level fields ──
    result.setdefault("eventId", event.get("id", ""))
    result.setdefault("eventTitle", event.get("title", ""))
    result.setdefault("scoringSummary", "")
    result.setdefault("overallConfidence", "低")
    result.setdefault("informationSufficiency", "不足")

    # ── Sanitize dimensions ──
    dimensions = result.get("dimensions")
    if not isinstance(dimensions, list):
        result["dimensions"] = []
        result["compositeScore"] = 0.0
        return result

    sanitized_dims = []
    for i, dim in enumerate(dimensions):
        if not isinstance(dim, dict):
            dim = {}
        sanitized_dims.append(_sanitize_dimension(dim, i))

    result["dimensions"] = sanitized_dims

    # Compute composite score
    result["compositeScore"] = _compute_composite_score(sanitized_dims)

    return result
