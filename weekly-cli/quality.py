"""Quality gate functions for 格物 v2 dialectical analysis pipeline.

Quality gates validate that analysis output meets minimum thresholds
before being accepted into the final WeeklyIssue.
"""


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
