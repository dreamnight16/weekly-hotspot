"""Empirical Layer: Quantitative Context.

Provides GDELT statistics, sentiment baseline extraction, and change-point
detection to anchor dialectical analysis with quantitative data.

This module is a STUB for post-MVP integration. Real GDELT API calls,
sentiment time-series analysis, and change-point detection (PELT via
Harbinger or statistical outlier detection) will be added later.

All functions return None on failure — graceful degradation is the
default contract.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("weekly.empirical.quantitative")

DEFAULT_STUB = {
    "gdelt": {
        "totalArticles": 0,
        "avgTone": 0.0,
        "numEvents": 0,
        "note": "stub: real GDELT API integration is post-MVP",
    },
    "sentiment": {
        "baseline": 0.0,
        "trend": "未知",
        "volatility": "未知",
        "note": "stub: sentiment time-series analysis not yet implemented",
    },
    "changePoints": [],
    "status": "stub",
}


def quantitative_context(
    event_title: str,
    *,
    dialectical_context: dict | None = None,
) -> dict | None:
    """Fetch quantitative context for an event.

    In the stub implementation, returns a minimal dict with placeholder
    values. Real GDELT API integration, sentiment baseline extraction,
    and change-point detection (PELT or simple statistical outlier)
    will be added post-MVP.

    Args:
        event_title: The title of the event to query quantitative data for.
        dialectical_context: Optional dict with dialectical analysis
            results to contextualize the quantitative data.

    Returns:
        A dict with gdelt, sentiment, and changePoints keys, or None on
        ANY failure (graceful degradation).
    """
    if not event_title or not isinstance(event_title, str) or not event_title.strip():
        logger.debug("quantitative_context: empty or invalid event_title")
        return None

    try:
        result = dict(DEFAULT_STUB)  # shallow copy is sufficient for stub

        if dialectical_context:
            result["dialecticalContext"] = {
                k: v
                for k, v in dialectical_context.items()
                if isinstance(v, (str, int, float, bool, list, dict, type(None)))
            }

        logger.info(
            "quantitative_context: returning stub for event=%r", event_title
        )
        return result
    except Exception:
        logger.exception("quantitative_context: unexpected error")
        return None
