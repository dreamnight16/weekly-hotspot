"""Quality gate functions for 格物 v2 dialectical analysis pipeline.

Quality gates validate that analysis output meets minimum thresholds
before being accepted into the final WeeklyIssue.
"""


def is_quality_event(event) -> bool:
    """Quality gate for a single analyzed event (Phase 3+).

    An event must have:
    - At least 3 timeline entries
    - At least 2 evidence items
    - At least 1 verified or suspect evidence item
    - A dialecticalSummary of at least 30 characters
    """
    timeline = getattr(event, "timeline", [])
    evidence = getattr(event, "evidence", [])
    if len(timeline) < 3:
        return False
    if len(evidence) < 2:
        return False
    verified = [e for e in evidence if getattr(e, "authenticity", None) in ("真实", "存疑")]
    if len(verified) == 0:
        return False
    summary = getattr(event, "dialecticalSummary", "")
    if len(summary) < 30:
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
