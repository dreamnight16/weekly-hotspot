"""Evidence layer: source capture, provenance, and independence.

The point of this module is to make the difference between *five reports* and
*five copies of one report* mechanically visible.  A syndicated wire story
appearing on five outlets fingerprints identically, so identical content is
recorded as REPUBLISHED and never counted as five independent witnesses.

Page text is extracted with the standard library rather than a scraping
dependency: the pipeline must keep running when an optional package is absent,
and a predictable extractor is easier to regression-test than a clever one.
"""

from __future__ import annotations

import hashlib
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Iterable, Optional

from config import get_logger

logger = get_logger("evidence.sources")

USER_AGENT = (
    "Mozilla/5.0 (compatible; Dianalyze/3.0; +https://github.com/dreamnight16/weekly-hotspot)"
)
FETCH_TIMEOUT = 12
MAX_PAGE_BYTES = 600_000
MAX_TEXT_CHARS = 6000

# Domains that publish the thing itself rather than reporting on it.  This is a
# prior, not a verdict: content-fingerprint republication detection below can
# and does override it.
_PRIMARY_HINTS = (
    "gov.cn", "samr.gov.cn", "court.gov.cn", "spp.gov.cn", "stats.gov.cn",
    "sec.gov", "hkexnews.hk", "sse.com.cn", "szse.cn", "cninfo.com.cn",
    "who.int", "iso.org", "doi.org", "arxiv.org", "nature.com", "science.org",
)
_REPUBLISHER_HINTS = (
    "sohu.com", "163.com", "sina.com.cn", "qq.com", "toutiao.com",
    "baijiahao.baidu.com", "ifeng.com", "zhihu.com", "weibo.com",
    "360doc.com", "toutiao", "bilibili.com", "douyin.com",
)

_META_TIME_KEYS = (
    "article:published_time", "og:published_time", "publishdate",
    "pubdate", "date", "weibo: article:create_at", "parsely-pub-date",
)
_META_SITE_KEYS = ("og:site_name", "application-name", "publisher", "author")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_url(url: str) -> str:
    """Normalize a URL for identity comparison (drop scheme/trailing slash)."""
    u = (url or "").strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def content_fingerprint(text: str) -> str:
    """Stable fingerprint of retrieved content, for change and duplicate detection."""
    normalized = re.sub(r"\s+", "", text or "")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]


def _shingles(text: str, n: int = 4) -> set[str]:
    compact = re.sub(r"\s+", "", text or "")
    if len(compact) < n:
        return {compact} if compact else set()
    return {compact[i : i + n] for i in range(len(compact) - n + 1)}


def content_similarity(a: str, b: str) -> float:
    """Jaccard similarity over character shingles, for syndication detection."""
    sa, sb = _shingles(a), _shingles(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


class _PageParser(HTMLParser):
    """Collect visible text and a few meta tags from a page."""

    _SKIP = frozenset(
        {"script", "style", "noscript", "svg", "head", "nav", "footer", "form", "iframe"}
    )
    _BLOCK = frozenset(
        {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6",
         "section", "article", "blockquote", "table"}
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag in self._SKIP:
            self._skip_depth += 1
        elif tag in self._BLOCK:
            self._parts.append("\n")
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            attr = {k.lower(): (v or "") for k, v in attrs}
            key = (attr.get("property") or attr.get("name") or "").lower()
            val = attr.get("content", "").strip()
            if key and val and key not in self.meta:
                self.meta[key] = val

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag == "meta":
            self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag in self._BLOCK:
            self._parts.append("\n")
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
            return
        if not self._skip_depth:
            self._parts.append(data)

    def text(self) -> str:
        raw = "".join(self._parts)
        lines = [re.sub(r"[ \t\xa0]+", " ", ln).strip() for ln in raw.split("\n")]
        return "\n".join(ln for ln in lines if ln)


def parse_page(html: str) -> tuple[str, str, str]:
    """Return (text, page_title, published_at) extracted from raw HTML."""
    parser = _PageParser()
    try:
        parser.feed(html)
    except Exception as exc:  # malformed markup must not abort collection
        logger.debug("parse_page: feed failed: %s", exc)
    text = parser.text()[:MAX_TEXT_CHARS]
    published = ""
    for key in _META_TIME_KEYS:
        if parser.meta.get(key):
            published = parser.meta[key]
            break
    return text, parser.title.strip(), published


def fetch_page(url: str, timeout: int = FETCH_TIMEOUT) -> tuple[str, str]:
    """Fetch a URL and return (extracted_text, status).

    Status is one of "ok", "fetched-no-text", "http-error", "network-error".
    Never raises: collection degrades to snippet-only rather than aborting.
    """
    if not url or not url.startswith(("http://", "https://")):
        return "", "invalid-url"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        # Scheme is restricted to http/https by the guard above.
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
            raw = resp.read(MAX_PAGE_BYTES)
            charset = resp.headers.get_content_charset() or "utf-8"
    except Exception as exc:
        logger.debug("fetch_page failed for %s: %s", url, exc)
        return "", "network-error"
    try:
        html = raw.decode(charset, errors="replace")
    except (LookupError, UnicodeDecodeError):
        html = raw.decode("utf-8", errors="replace")
    text, _, _ = parse_page(html)
    return (text, "ok") if text.strip() else ("", "fetched-no-text")


def classify_source_kind(url: str, publisher: str = "") -> str:
    """Best-effort prior on whether a source originates or repeats information."""
    haystack = f"{normalize_url(url)} {publisher}".lower()
    if not haystack.strip():
        return "UNKNOWN"
    if any(h in haystack for h in _PRIMARY_HINTS):
        return "PRIMARY"
    if any(h in haystack for h in _REPUBLISHER_HINTS):
        return "REPUBLISHED"
    return "UNKNOWN"


def build_source_record(
    *,
    url: str,
    title: str = "",
    snippet: str = "",
    publisher: str = "",
    published_at: str = "",
    content: str = "",
    fetch_status: str = "snippet-only",
    source_id: str = "",
) -> "SourceRecord":
    """Assemble a SourceRecord from a search hit, optionally enriched by a fetch."""
    from schema import SourceRecord  # local import keeps schema free of network code

    body = content or snippet or ""
    return SourceRecord(
        sourceId=source_id or content_fingerprint(normalize_url(url))[:16],
        url=url,
        title=title,
        publisher=publisher,
        publishedAt=published_at or None,
        retrievedAt=_now_iso(),
        snippet=snippet[:1000],
        content=content,
        contentFingerprint=content_fingerprint(body) if body else "",
        kind=classify_source_kind(url, publisher),
        fetchStatus=fetch_status,
    )


def mark_republications(records: list["SourceRecord"], threshold: float = 0.7) -> int:
    """Reclassify near-identical records as REPUBLISHED.  Returns how many.

    This is the mechanism that stops five copies of one announcement from
    reading as five corroborating witnesses.
    """
    marked = 0
    kept: list = []
    for rec in records:
        body = rec.content or rec.snippet
        duplicate_of = None
        for prior in kept:
            if not body or not (prior.content or prior.snippet):
                continue
            if content_similarity(body, prior.content or prior.snippet) >= threshold:
                duplicate_of = prior
                break
        if duplicate_of is not None:
            if rec.kind != "PRIMARY":
                rec.kind = "REPUBLISHED"
                marked += 1
            if not rec.publisher:
                rec.publisher = duplicate_of.publisher
        kept.append(rec)
    return marked


def dedupe_by_url(records: Iterable["SourceRecord"]) -> list["SourceRecord"]:
    """Drop records sharing a normalized URL, keeping the richest one."""
    best: dict[str, object] = {}
    for rec in records:
        key = normalize_url(rec.url)
        if not key:
            continue
        prior = best.get(key)
        if prior is None or len(rec.content) > len(getattr(prior, "content", "")):
            best[key] = rec
    return list(best.values())
