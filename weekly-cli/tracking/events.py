"""Event tracking: stable identity, clustering, and cross-week revision.

A hot topic is a headline; an event is a thing that happened.  "尊界刹车踏板
断裂" and "尊界回应制动踏板问题" are one event observed twice, not two events.
Giving each observation a title-independent id is what makes it possible to say
later that a judgment changed, and why.

Clustering is rule-based by design.  Calling a model to decide whether two
headlines describe one event would add an API call per topic and make the
grouping non-reproducible between runs.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Iterable, Optional

from chinese_scraper_utils import stable_id

from config import get_logger
from evidence.claims import split_sentences
from evidence.collector import extract_entities
from evidence.sources import content_similarity

logger = get_logger("tracking.events")

# Titles describing the same event often share an entity but not much else, so
# entity identity is the primary key and text similarity is the fallback.
ENTITY_MATCH_RE = re.compile(r"[\s·・]+")

# Chinese headlines lead with the actor, so the first two characters are a
# usable actor key.  "尊界刹车踏板断裂" and "尊界回应制动踏板问题" share the
# actor 尊界 but little else, which is precisely why actor identity has to
# carry the clustering rather than whole-title similarity.
ACTOR_KEY_LEN = 2
_CJK_RE = re.compile(r"[^\w\u4e00-\u9fff]")
_BRACKET_RE = re.compile(r"[【\[（(](?P<name>[^】\]）)]{2,12})[】\]）)]")


def _clean(title: str) -> str:
    return _CJK_RE.sub("", title or "")


def actor_key(title: str) -> str:
    """Leading actor span of a headline, used as the clustering primary key."""
    bracketed = _BRACKET_RE.search(title or "")
    if bracketed:
        return _clean(bracketed.group("name"))[:6].lower()
    return _clean(title)[:ACTOR_KEY_LEN].lower()


def content_bigrams(title: str) -> set[str]:
    """Content bigrams of a headline with its actor prefix removed."""
    body = _clean(title)[ACTOR_KEY_LEN:]
    if len(body) < 2:
        return set()
    return {body[i : i + 2] for i in range(len(body) - 1)}


def same_event(title_a: str, title_b: str) -> bool:
    """Conservative test for whether two headlines describe one event.

    Splitting one event into two records is a missed connection; merging two
    events into one invents a relationship that does not exist.  The second
    error is worse, so the rule requires both a shared actor *and* a shared
    content bigram rather than similarity of the titles overall.
    """
    if not title_a or not title_b:
        return False
    if _clean(title_a) == _clean(title_b):
        return True
    if actor_key(title_a) != actor_key(title_b):
        return False
    return bool(content_bigrams(title_a) & content_bigrams(title_b))


def _topic_token(titles: list[str]) -> str:
    """The bigram shared by most titles — the cluster's stable topic marker."""
    counts: dict[str, int] = {}
    for title in titles:
        for gram in content_bigrams(title):
            counts[gram] = counts.get(gram, 0) + 1
    if not counts:
        return _clean(titles[0])[:8] if titles else "unknown"
    # Deterministic: highest count, then lexicographic.
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]

REVERSAL_MARKERS: tuple[str, ...] = (
    "反转", "辟谣", "不实", "澄清", "否认", "撤回", "更正", "致歉", "道歉",
    "立案", "处罚", "通报批评", "撤销",
)


def normalize_entity(entity: str) -> str:
    """Normalize an entity string into a clustering key."""
    return ENTITY_MATCH_RE.sub("", (entity or "").strip().lower())


def event_id_for(actor: str, topic: str = "") -> str:
    """Stable, title-independent event id derived from the actor and topic.

    Keyed on actor + topic token rather than on the exact headline, so the
    same event keeps its id when the headline is rephrased between weeks.
    """
    a = normalize_entity(actor) or "unknown"
    t = normalize_entity(topic)
    return f"evt-{stable_id('dianalyze-event', a, t)}"


def assign_event_identity(
    raw_events: list[dict],
    *,
    observed_at: Optional[str] = None,
    known_event_ids: Optional[set[str]] = None,
    known_actors: Optional[set[str]] = None,
) -> list[dict]:
    """Cluster raw topics into events and stamp each with a stable identity.

    Adds `eventId`, `topicAliases`, `sourcePlatform`, `firstSeenAt`,
    `lastSeenAt`, and `eventStatus` to each event dict.  Events already known
    from earlier weeks are marked 持续发展 rather than 新发生.
    """
    today = observed_at or date.today().isoformat()
    known = known_event_ids or set()
    known_actors = known_actors or set()

    # Greedy clustering: a headline joins the first cluster it matches, else
    # starts one.  Deterministic given the same input ordering.
    clusters: list[dict] = []
    for raw in raw_events:
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("title") or "").strip()
        if not title:
            continue

        target = None
        for cluster in clusters:
            if any(same_event(title, t) for t in cluster["titles"]):
                target = cluster
                break
        if target is None:
            target = {
                "titles": [],
                "actors": [],
                "sourcePlatforms": [],
                "firstSeenAt": today,
                "lastSeenAt": today,
                "representative": raw,
            }
            clusters.append(target)

        target["titles"].append(title)
        actor = actor_key(title)
        if actor and actor not in target["actors"]:
            target["actors"].append(actor)
        platform = str(raw.get("sourcePlatform") or "").strip()
        if platform and platform not in target["sourcePlatforms"]:
            target["sourcePlatforms"].append(platform)
        # Keep the longest summary as the representative: heat blurbs vary and
        # the longest one usually carries the most context.
        if len(str(raw.get("summary") or "")) > len(
            str(target["representative"].get("summary") or "")
        ):
            target["representative"] = raw

    clustered: list[dict] = []
    for cluster in clusters:
        titles = list(dict.fromkeys(cluster["titles"]))
        actor = cluster["actors"][0] if cluster["actors"] else ""
        event_id = event_id_for(actor, _topic_token(titles))
        rep = dict(cluster["representative"])
        rep["eventId"] = event_id
        rep["id"] = rep.get("id") or event_id
        rep["actorKey"] = actor
        rep["topicAliases"] = titles
        rep["sourcePlatform"] = ", ".join(cluster["sourcePlatforms"]) or rep.get(
            "sourcePlatform"
        )
        rep["firstSeenAt"] = cluster["firstSeenAt"]
        rep["lastSeenAt"] = cluster["lastSeenAt"]
        rep["eventStatus"] = (
            "持续发展" if (event_id in known or actor in known_actors) else "新发生"
        )
        rep["clusterSize"] = len(titles)
        clustered.append(rep)

    merged = len(raw_events) - len(clustered)
    if merged > 0:
        logger.info(
            "[tracking] %d 条话题聚类为 %d 个事件（合并 %d 条同事件重复报道）",
            len(raw_events), len(clustered), merged,
        )
    return clustered


def detect_reversals(dossier, prior_dossier) -> list[str]:
    """Detect that a story has turned since we last looked at it.

    A turn is signalled by new disagreement between sources, or by language in
    the new material that only appears once a story has been corrected,
    retracted, or acted on.
    """
    if prior_dossier is None:
        return []

    notes: list[str] = []
    prior_conflicts = set(getattr(prior_dossier, "conflicts", []) or [])
    for conflict in getattr(dossier, "conflicts", []) or []:
        if conflict not in prior_conflicts:
            notes.append(f"来源间出现新的分歧：{conflict}")

    prior_urls = {getattr(s, "url", "") for s in getattr(prior_dossier, "sources", [])}
    for src in getattr(dossier, "sources", []):
        if getattr(src, "url", "") in prior_urls:
            continue
        body = f"{getattr(src, 'title', '')} {getattr(src, 'content', '')}"
        if any(marker in body for marker in REVERSAL_MARKERS):
            notes.append(
                f"新增来源含反转/处置信号：{getattr(src, 'title', '') or getattr(src, 'url', '')}"
            )
    return notes


def event_status_from(dossier, prior_dossier, reversals: Iterable[str]) -> str:
    """Classify the event's current stage."""
    if any(True for _ in reversals):
        return "出现反转"
    if prior_dossier is None:
        return "新发生"
    if not getattr(dossier, "sources", None):
        return "待观察"
    return "持续发展"


def track_changes(
    dossiers: list,
    history: dict,
) -> tuple[list[dict], list[str]]:
    """Annotate dossiers with cross-week status and collect revision notes.

    Returns (annotations, notes) where each annotation records what changed for
    one event.  The notes feed the article so a corrected judgment is visible
    rather than silently overwriting the previous week's.
    """
    annotations: list[dict] = []
    notes: list[str] = []

    for dossier in dossiers:
        event_id = getattr(dossier, "eventId", "")
        prior = history.get(event_id)
        reversals = detect_reversals(dossier, prior)
        status = event_status_from(dossier, prior, reversals)
        annotation = {
            "eventId": event_id,
            "title": getattr(dossier, "title", ""),
            "eventStatus": status,
            "firstSeenAt": getattr(prior, "retrievedAt", "") or getattr(dossier, "retrievedAt", ""),
            "lastSeenAt": getattr(dossier, "retrievedAt", ""),
            "reversals": reversals,
            "isNew": prior is None,
        }
        annotations.append(annotation)
        if prior is not None and reversals:
            notes.append(
                f"《{getattr(dossier, 'title', '')}》自上次观察后出现变化："
                + "；".join(reversals)
            )

    return annotations, notes


def claims_changed(prior_claims: Iterable, current_claims: Iterable) -> list[dict]:
    """Compare claims at the same path across runs to record judgment revisions."""
    prior_by_path = {
        getattr(c, "path", ""): c for c in prior_claims if getattr(c, "path", "")
    }
    changes: list[dict] = []
    for claim in current_claims:
        path = getattr(claim, "path", "")
        old = prior_by_path.get(path)
        if old is None:
            continue
        old_text = getattr(old, "statement", "")
        new_text = getattr(claim, "statement", "")
        if old_text and new_text and content_similarity(old_text, new_text) < 0.6:
            changes.append(
                {
                    "path": path,
                    "before": old_text,
                    "after": new_text,
                    "reason": "本期材料与上期不一致，判断已更新",
                }
            )
    return changes


def summarize_story_line(annotations: list[dict]) -> str:
    """Render a one-line trajectory per tracked event for the article."""
    if not annotations:
        return ""
    lines = []
    for a in annotations:
        label = a.get("eventStatus", "")
        line = f"- {a.get('title', '')}：{label}"
        if a.get("reversals"):
            line += f"（{'；'.join(a['reversals'])}）"
        lines.append(line)
    return "\n".join(lines)


def marker_scan(text: str) -> bool:
    """True when a passage contains reversal/action language."""
    return any(m in s for s in split_sentences(text) for m in REVERSAL_MARKERS)
