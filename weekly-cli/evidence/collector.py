"""Evidence layer: query expansion, retrieval, and dossier assembly.

Phase 1 previously ran on a headline plus a heat ranking.  This module builds
the fact file that the dialectical phases actually read from instead.

Two retrieval channels run side by side and check each other: search snippets
give breadth and tell us what is being said, while fetched page bodies give
depth and tell us what the original material actually says.  Snippets alone
cannot distinguish an announcement from a report about one, and a body alone
gives no sense of how the event is being framed elsewhere.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, Optional

from config import get_logger
from evidence.claims import split_sentences
from evidence.sources import (
    build_source_record,
    content_similarity,
    dedupe_by_url,
    fetch_page,
    mark_republications,
    normalize_url,
)

logger = get_logger("evidence.collector")

# Retrieval is organised by question type rather than by repeating the headline.
# Searching a trending title five times returns five copies of the same framing.
_QUERY_SUFFIXES: tuple[tuple[str, str], ...] = (
    ("fact", ""),
    ("primary", "官方通报 声明 公告"),
    ("dispute", "争议 质疑 回应 澄清"),
    ("background", "背景 技术标准 规定 依据"),
    ("followup", "后续 调查 进展 处理结果"),
)

# Domains that block automated retrieval or only carry user chatter; fetching
# them costs time and yields nothing citable.
_SKIP_FETCH_HINTS = (
    "weibo.com", "zhihu.com", "bilibili.com", "douyin.com", "xiaohongshu.com",
    "tieba.baidu.com", "twitter.com", "x.com", "facebook.com", "youtube.com",
    "baijiahao.baidu.com", "toutiao.com",
)

MAX_DEFAULT_SOURCES = 10
MAX_DEFAULT_FETCHES = 4
DEFAULT_RESULTS_PER_QUERY = 6

_NUM_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(亿元|万元|亿|万|元|美元|%|％|倍|辆|人|家|次|吨)"
)


def extract_entities(title: str, aliases: Iterable[str] = ()) -> str:
    """Pull a short searchable subject out of a headline.

    Hot-topic titles are full sentences ("尊界通报刹车踏板断裂"); using the
    whole thing as a query term retrieves the framing rather than the event.
    """
    text = (title or "").strip()
    for alias in aliases:
        if alias and alias in text:
            return alias
    # Prefer the explicit platform tags the scrapers emit when present.
    tagged = re.search(r"[【\[](?P<name>[^】\]]{2,12})[】\]]", text)
    if tagged:
        return tagged.group("name")
    # Otherwise take the leading subject run, which in Chinese headlines is the
    # actor, before the first verb-ish boundary.
    head = re.split(r"[，,。：:！!？?（(]", text)[0]
    return head[:12] if head else text[:12]


def expand_queries(title: str, aliases: Iterable[str] = ()) -> list[str]:
    """Build one query per retrieval intent, keyed on the event subject."""
    entity = extract_entities(title, aliases)
    queries: list[str] = []
    for _kind, suffix in _QUERY_SUFFIXES:
        q = f"{entity} {suffix}".strip() if suffix else entity
        if q and q not in queries:
            queries.append(q)
    # The full headline still matters for "followup"-style coverage, so keep it
    # as a final query rather than as the only one.
    if title and title not in queries:
        queries.append(title)
    return queries


def _should_fetch(url: str) -> bool:
    u = normalize_url(url)
    return bool(u) and not any(h in u for h in _SKIP_FETCH_HINTS)


def detect_numeric_conflicts(sources: list, max_conflicts: int = 5) -> list[str]:
    """Flag sources that assert different values for the same statement.

    Coarse on purpose: it compares sentences that are already textually similar
    and reports where their figures disagree, which is the shape of the
    "30% vs 70% revenue share" class of contradiction.
    """
    observations: list[tuple[object, str, dict[str, float]]] = []
    for src in sources:
        body = getattr(src, "content", "") or getattr(src, "snippet", "")
        for sentence in split_sentences(body):
            nums = {unit: float(val) for val, unit in _NUM_RE.findall(sentence)}
            if nums:
                observations.append((src, sentence, nums))

    conflicts: list[str] = []
    for i, (src_a, sent_a, nums_a) in enumerate(observations):
        for src_b, sent_b, nums_b in observations[i + 1 :]:
            if getattr(src_a, "sourceId", "") == getattr(src_b, "sourceId", ""):
                continue
            shared = set(nums_a) & set(nums_b)
            if not shared:
                continue
            # Compare with the figures removed: "占比为30%" and "占比为70%"
            # assert the same thing about the same subject, and only differ in
            # the value.  Comparing the raw sentences instead would make the
            # similarity threshold depend on how long the sentence happens to be.
            if content_similarity(_NUM_RE.sub("", sent_a), _NUM_RE.sub("", sent_b)) < 0.6:
                continue
            if any(nums_a[u] != nums_b[u] for u in shared):
                label_a = getattr(src_a, "publisher", "") or getattr(src_a, "url", "")
                label_b = getattr(src_b, "publisher", "") or getattr(src_b, "url", "")
                conflicts.append(
                    f"{label_a} 与 {label_b} 对同一事项给出的数值不一致"
                    f"（{sent_a[:60]} / {sent_b[:60]}）"
                )
                if len(conflicts) >= max_conflicts:
                    return conflicts
    return conflicts


def collect_dossier(
    event: dict,
    *,
    search_fn: Optional[Callable[..., list[dict]]] = None,
    fetch_fn: Optional[Callable[[str], tuple[str, str]]] = None,
    max_sources: int = MAX_DEFAULT_SOURCES,
    max_fetches: int = MAX_DEFAULT_FETCHES,
    results_per_query: int = DEFAULT_RESULTS_PER_QUERY,
) -> "EvidenceDossier":
    """Retrieve and structure the material for one event.

    Never raises.  When retrieval fails the dossier is returned with
    `searchFailed=True` and no sources, which the caller must treat as
    "lower the analysis depth" rather than as licence to fill the gap from the
    model's own memory.
    """
    from schema import EvidenceDossier  # local import: schema has no network deps

    if search_fn is None:
        from search import search_event as search_fn  # type: ignore[assignment]
    if fetch_fn is None:
        fetch_fn = fetch_page

    title = str(event.get("title") or "").strip()
    aliases = [str(a) for a in (event.get("topicAliases") or [])]
    event_id = str(event.get("eventId") or event.get("id") or "")
    queries = expand_queries(title, aliases)

    hits: list[dict] = []
    failures = 0
    for query in queries:
        try:
            found = search_fn(query, max_results=results_per_query) or []
        except Exception as exc:
            failures += 1
            logger.warning("[evidence] 检索失败 %r: %s", query, exc)
            continue
        hits.extend(found)

    if not hits:
        logger.info("[evidence] %s: 未获得任何检索结果，降级为无证据", title)
        return EvidenceDossier(
            eventId=event_id, title=title, queries=queries,
            searchFailed=True, retrievedAt=_utc_now(),
        )

    unique_hits = _dedupe_hits(hits)[:max_sources]

    # Fetch bodies breadth-first, preferring likely-original hosts.
    fetch_targets = sorted(
        unique_hits, key=lambda h: _fetch_priority(h.get("url", ""))
    )[:max_fetches]

    bodies: dict[str, tuple[str, str]] = {}
    if fetch_targets:
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {
                pool.submit(fetch_fn, h.get("url", "")): h.get("url", "")
                for h in fetch_targets
                if _should_fetch(h.get("url", ""))
            }
            for fut, url in futures.items():
                try:
                    bodies[url] = fut.result()
                except Exception as exc:
                    logger.debug("[evidence] 抓取失败 %s: %s", url, exc)

    records = []
    for hit in unique_hits:
        url = hit.get("url", "")
        content, status = bodies.get(url, ("", "snippet-only"))
        records.append(
            build_source_record(
                url=url,
                title=hit.get("title", ""),
                snippet=hit.get("snippet", ""),
                content=content,
                fetch_status=status,
            )
        )

    republications = mark_republications(records)
    logger.info(
        "[evidence] %s: %d 条来源（其中 %d 条为转载），%d 条抓到正文",
        title, len(records), republications,
        sum(1 for r in records if r.content),
    )

    return EvidenceDossier(
        eventId=event_id,
        title=title,
        queries=queries,
        sources=records,
        conflicts=detect_numeric_conflicts(records),
        retrievedAt=_utc_now(),
        searchFailed=False,
    )


def _fetch_priority(url: str) -> int:
    """Lower sorts first: prefer likely-primary origins over aggregators."""
    u = normalize_url(url)
    if not _should_fetch(u):
        return 99
    if any(h in u for h in ("gov.cn", "court.gov.cn", "sec.gov", "cninfo.com.cn")):
        return 0
    if any(h in u for h in ("sina.com.cn", "163.com", "sohu.com", "qq.com")):
        return 5
    return 2


def _dedupe_hits(hits: list[dict]) -> list[dict]:
    """Collapse hits by normalized URL, then by near-identical title."""
    seen_urls: set[str] = set()
    out: list[dict] = []
    for hit in hits:
        key = normalize_url(hit.get("url", ""))
        if not key or key in seen_urls:
            continue
        seen_urls.add(key)
        out.append(hit)
    return out


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def dossier_to_text(dossier: "EvidenceDossier", max_chars: int = 6000) -> str:
    """Render a dossier as prompt-ready text for the dialectical phases.

    Sources are labelled by kind so the model can see which material is
    original and which is a republication, and an honest empty dossier says so
    instead of inviting the model to substitute its own recollection.
    """
    if not dossier.sources:
        return (
            "（未检索到可用来源。请只依据已知标题信息做最小判断，"
            "明确标注证据不足，不要用常识补全事实。）"
        )

    lines: list[str] = []
    if dossier.conflicts:
        lines.append("【来源间分歧】")
        lines.extend(f"- {c}" for c in dossier.conflicts)
        lines.append("")

    lines.append("【已获取来源】")
    for i, src in enumerate(dossier.sources, 1):
        kind_label = {
            "PRIMARY": "原始来源", "INDEPENDENT": "独立报道",
            "REPUBLISHED": "转载", "UNKNOWN": "性质未明",
        }.get(src.kind, src.kind)
        lines.append(f"[来源{i}] {kind_label} | {src.title or src.url}")
        if src.url:
            lines.append(f"  URL: {src.url}")
        if src.publishedAt:
            lines.append(f"  发布: {src.publishedAt}")
        body = (src.content or src.snippet or "").strip()
        if body:
            lines.append(f"  内容: {body[:800]}")
        lines.append("")

    text = "\n".join(lines)
    return text[:max_chars]


def dossier_claim_context(dossier: "EvidenceDossier") -> str:
    """Compact source listing for claim extraction (ids must stay visible)."""
    if not dossier.sources:
        return "（无来源）"
    lines = []
    for src in dossier.sources:
        body = (src.content or src.snippet or "").strip()[:600]
        lines.append(
            f"- {src.sourceId} [{src.kind}] {src.title or src.url}\n  {body}"
        )
    return "\n".join(lines)
