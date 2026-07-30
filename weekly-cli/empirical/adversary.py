"""Empirical Layer: Devil's Advocate Adversarial Review.

Takes the dialectical unfolding output and subjects it to adversarial
scrutiny from a fresh LLM instance. Identifies the three weakest claims
and proposes concrete challenges based on evidence and logic gaps.

Gracefully degrades: returns None on ANY failure so the pipeline continues.
"""
import json
from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt

ADVERSARY_PROMPT = load_prompt("empirical/adversary")


def format_dialectical_output(unfolding_result: dict) -> str:
    """Serialize the unfolding result to a JSON string for the adversary prompt.

    Uses ensure_ascii=False to preserve Chinese characters and
    limited indentation to keep prompt size manageable.
    """
    try:
        return json.dumps(unfolding_result, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        # Fallback: convert to string representation
        return json.dumps(
            {k: str(v)[:1000] for k, v in unfolding_result.items()},
            ensure_ascii=False,
            indent=2,
        )


def _has_minimal_dialectical_content(unfolding_result: dict) -> bool:
    """Check that the unfolding result has enough content for adversarial review.

    The adversary needs at least a phaseSummary or unityOfOpposites to work with.
    """
    if not unfolding_result:
        return False
    if unfolding_result.get("phaseSummary"):
        return True
    uoo = unfolding_result.get("unityOfOpposites")
    if isinstance(uoo, dict) and any(uoo.values()):
        return True
    return False


def adversarial_review(
    client: DeepSeekClient,
    unfolding_result: dict,
) -> dict | None:
    """Run Devil's Advocate review against the dialectical unfolding output.

    Loads the empirical/adversary prompt, sends the full unfolding output
    for critique, and returns structured challenges.

    The adversary is called with a fresh LLM instance (different model or
    separate context) to avoid the dialectical analysis biasing the review.

    Args:
        client: A DeepSeekClient instance (should differ from the
                dialectical client to avoid bias).
        unfolding_result: The full output from unfold_dialectics().

    Returns:
        A dict with adversarySummary, challenges, and noWeakClaimsFound,
        or None on ANY failure (graceful degradation).
    """
    if client is None:
        return None

    if not _has_minimal_dialectical_content(unfolding_result):
        return None

    dialectical_output = format_dialectical_output(unfolding_result)

    # Count events in the unfolding result
    events = unfolding_result.get("events", [])
    event_count = len(events) if isinstance(events, list) else 0
    if event_count == 0:
        event_count = 1  # Assume at least one event was analyzed

    prompt = ADVERSARY_PROMPT.format(
        event_count=event_count,
        dialectical_output=dialectical_output,
    )

    try:
        result = client.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是一个魔鬼代言人（Devil's Advocate）。你的任务不是"
                        "否定辩证分析，而是从反面检验其强度。你的武器不是立场，"
                        "是逻辑和证据——找出辩证分析中最弱的断言，逐条提出具体的、"
                        "有证据支撑的挑战。严格按JSON格式输出。"
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

    if result.get("challenges") is None:
        result["challenges"] = []
    elif not isinstance(result["challenges"], list):
        result["challenges"] = []

    if result.get("noWeakClaimsFound") is None:
        result["noWeakClaimsFound"] = False

    if result.get("adversarySummary") is None:
        result["adversarySummary"] = ""

    if result.get("noWeakClaimsRationale") is None:
        result["noWeakClaimsRationale"] = ""

    return result
