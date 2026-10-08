#!/usr/bin/env python3
"""Dianalyze v2 — Five-Phase Dialectical Pipeline Orchestrator.

Phase 0: Scrape raw events from Weibo, Zhihu, HackerNews
Phase 1: Phenomenon Grasping (dialectical + empirical source verification)
Phase 2: Contradiction Identification (dialectical + empirical scoring)
Phase 3: Dialectical Unfolding (parallel per-event + adversarial review)
Phase 4: Historical Positioning (dialectical + empirical connections + causal loops)
Phase 5: Practice Orientation (dialectical + empirical scenario planning)

Output: WeeklyIssue JSON + five-phase Markdown article
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from chinese_scraper_utils import DeepSeekClient

from scraper.cache import load_cache
from scraper.sources import scrape_all
from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL_DIALECTICAL,
    DEEPSEEK_MODEL_EMPIRICAL,
    BLOG_CONTENT_DIR,
    WEB_DATA_DIR,
    setup_logging,
    get_logger,
    RUN_ID,
)
from dialectical.grasping import grasp_phenomena
from dialectical.contradiction import identify_contradictions
from dialectical.unfolding import unfold_dialectics
from dialectical.positioning import position_historically
from dialectical.practice import orient_practice
from empirical.adversary import adversarial_review
from empirical.causal import build_causal_loop
from empirical.connections import find_connections
from empirical.scenarios import plan_scenarios
from empirical.scorer import score_event
from empirical.verifier import verify_evidence
from merger import merge_phase
from narrative.article import (
    assemble_article,
    build_article_context,
    generate_article,
    generate_narrative_article,
)
from narrative.revision import apply_revisions, summarise_records
from quality import is_quality_event, publication_gate, sanitize_narrative, scan_text_risk
from evidence.claims import extract_claims
from evidence.collector import collect_dossier, dossier_to_text
from evidence.store import has_new_information, load_recent_dossiers, save_dossiers
from schema import (
    WeeklyIssue,
    PhenomenonGrasping,
    ContradictionIdentification,
    HistoricalPositioning,
    PracticeOrientation,
    SelectedEvent,
    EvidenceTrace,
    IssueMetadata,
)
from search import search_event
from tracking.events import assign_event_identity, track_changes
from utils import get_week_id, get_week_range

logger = get_logger("pipeline")


# =============================================================================
# Utility helpers
# =============================================================================


def safe_call(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Call *fn* and return its result; return None on ANY exception.

    This is the empirical-layer safety wrapper: when the empirical model
    fails we degrade gracefully and let the dialectical layer carry the
    phase alone.
    """
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        logger.warning(
            "[empirical] %s 失败: %s",
            getattr(fn, "__name__", repr(fn)), exc,
        )
        return None


_SOURCE_URL_RE = re.compile(r"(?:^|\n)来源:\s*(https?://\S+)")


def _source_url(event: dict) -> str:
    """Read a source URL from the explicit field or the scraper summary."""
    explicit = str(event.get("sourceUrl") or "").strip()
    if explicit:
        return explicit
    summary = str(event.get("summary") or "")
    match = _SOURCE_URL_RE.search(summary)
    return match.group(1).strip() if match else ""


def _carry_source_urls(events: list[dict], raw_events: list[dict]) -> list[dict]:
    """Preserve scraper provenance when a model returns a new event shape."""
    by_id = {
        str(event.get("id")): _source_url(event)
        for event in raw_events
        if event.get("id") and _source_url(event)
    }
    by_title = {
        str(event.get("title", "")).strip(): _source_url(event)
        for event in raw_events
        if str(event.get("title", "")).strip() and _source_url(event)
    }
    carried: list[dict] = []
    for event in events:
        item = dict(event)
        item["sourceUrl"] = (
            by_id.get(str(item.get("id")), "")
            or by_title.get(str(item.get("title", "")).strip(), "")
            or _source_url(item)
        ) or None
        carried.append(item)
    return carried


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="每周热点证据收集，支持可选的五阶段模型分析",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="运行流水线但不写入输出文件",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="启用 DEBUG 级别日志",
    )
    parser.add_argument(
        "--skip-scrape", action="store_true",
        help="跳过 Phase 0 抓取，仅用缓存（用于重复测试）",
    )
    parser.add_argument(
        "--max-events", type=int, default=8,
        help="最大入选事件数（默认 8）",
    )
    parser.add_argument(
        "--max-dossiers", type=int, default=8,
        help="最多为多少个事件建立证据档案（默认 8，控制检索与费用）",
    )
    parser.add_argument(
        "--max-page-fetches", type=int, default=4,
        help="每个事件最多抓取几篇原文（默认 4；0 表示只用检索摘要）",
    )
    parser.add_argument(
        "--max-revision-rounds", type=int, default=2,
        help="断言修订最多几轮（默认 2；超出后降级发布而不是无限自省）",
    )
    return parser.parse_args(argv)


# =============================================================================
# Phase 0: Scrape
# =============================================================================


def _scrape_or_load_cache(args: argparse.Namespace) -> tuple[list[dict], bool]:
    """Phase 0: scrape real hot topics or fall back to cache.

    Returns (events_list, from_cache).
    """
    raw_events: list[dict] = []

    if args.skip_scrape:
        logger.info("[Phase 0] --skip-scrape: 跳过抓取")
    else:
        raw_events = scrape_all()

    if not raw_events:
        cached = load_cache()
        if cached:
            logger.info("  抓取全失败，使用缓存数据（%d 个话题）", len(cached))
            return cached, True
        logger.critical("  抓取失败且无缓存，退出。请检查网络。")
        sys.exit(1)

    return raw_events, False


# =============================================================================
# Phase 3 helpers: parallel analysis + quality gate
# =============================================================================


def _parallel_analyze(
    dialectical_client: DeepSeekClient,
    events: list[dict],
    log: logging.Logger,
    dossiers: dict | None = None,
) -> list[dict]:
    """Phase 3: parallel per-event dialectical unfolding.

    Each event is analyzed against the evidence dossier already gathered in
    Phase 0.5 rather than against a fresh search, so every phase reasons over
    one shared evidence set.  Adversarial review is not run here: it belongs
    after claim extraction, where its verdicts can be bound to assertions and
    actually applied.
    """

    def _analyze_one(idx: int, event: dict) -> tuple[int, dict | None]:
        event_id = str(event.get("eventId") or event.get("id") or "")
        dossier = (dossiers or {}).get(event_id)
        dossier_text = None
        if dossier is not None:
            dossier_text = dossier_to_text(dossier, max_chars=4000)
            log.info(
                "  (%d) 分析: %s（依据 %d 条来源）",
                idx, event.get("title", "(无标题)"), len(dossier.sources),
            )
        else:
            log.info("  (%d) 分析: %s（无证据档案）", idx, event.get("title", "(无标题)"))

        try:
            unfolding = unfold_dialectics(
                dialectical_client, event, [], idx=idx, dossier_text=dossier_text,
            )
        except Exception as exc:
            log.warning("    (%d) unfold_dialectics 失败: %s，跳过", idx, exc)
            return (idx, None)

        if unfolding is None:
            log.warning("    (%d) unfold_dialectics 返回 None，跳过", idx)
            return (idx, None)

        # Extract the primary event from the unfolding result
        unfolded_events = unfolding.get("events", [])
        if unfolded_events and isinstance(unfolded_events, list):
            analyzed = {**event, **dict(unfolded_events[0])}
        else:
            analyzed = dict(event)

        analyzed["sourceUrl"] = event.get("sourceUrl") or analyzed.get("sourceUrl")

        # Merge top-level dialectical analysis into the event dict
        for key in (
            "unityOfOpposites", "quantityQuality", "negationOfNegation",
            "dialecticalConfidence", "adversarialReview",
            "causalLoopDiagram", "dataValidation", "phaseSummary",
        ):
            if key in unfolding:
                analyzed[key] = unfolding[key]

        log.info("    (%d) 分析完成", idx)
        return (idx, analyzed)

    results_map: dict[int, dict] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(_analyze_one, i + 1, event): i + 1
            for i, event in enumerate(events)
        }
        for fut in as_completed(futures):
            idx, result = fut.result()
            if result is not None:
                results_map[idx] = result

    analyzed = [results_map[i] for i in sorted(results_map)]

    if not analyzed:
        log.warning("  Phase 3: 没有事件通过分析")
        return []

    quality = [e for e in analyzed if is_quality_event(e)]
    dropped = len(analyzed) - len(quality)
    if dropped > 0:
        log.info("  质量筛选: 剔除了 %d 个证据不足或内容空洞的事件", dropped)
    log.info("  最终入选: %d 个", len(quality))

    return quality


# =============================================================================
# Phase empirical helpers
# =============================================================================


def _empirical_verify_events(
    client: DeepSeekClient,
    events: list[dict],
    max_calls: int = 3,
) -> dict | None:
    """Run verify_evidence on selected events (up to max_calls)."""
    results: list[dict] = []
    for event in events[:max_calls]:
        r = safe_call(verify_evidence, client, event)
        if r is not None:
            results.append(r)
    if not results:
        return None
    combined = dict(results[0])
    combined["verified"] = True
    if len(results) > 1:
        combined["supplements"] = results[1:]
    return combined


def _empirical_score_events(
    client: DeepSeekClient,
    events: list[dict],
    max_calls: int = 5,
) -> dict | None:
    """Run score_event on events (up to max_calls)."""
    results: list[dict] = []
    for event in events[:max_calls]:
        r = safe_call(score_event, client, event)
        if r is not None:
            results.append(r)
    if not results:
        return None
    combined = dict(results[0])
    combined["verified"] = True
    if len(results) > 1:
        combined["supplements"] = results[1:]
    return combined


def _combine_empirical(*results: dict | None) -> dict | None:
    """Combine multiple empirical results into a single dict for merge_phase."""
    non_none = [r for r in results if r is not None and isinstance(r, dict)]
    if not non_none:
        return None
    combined: dict[str, Any] = {"verified": True}
    for r in non_none:
        for key in ("verificationNote", "scoreCalibration", "dataContext",
                     "challenges", "supplements", "causalSummary",
                     "connectionSummary", "scenarioSummary"):
            if key in r:
                existing = combined.get(key)
                if existing is None:
                    combined[key] = r[key]
                elif isinstance(existing, list) and isinstance(r[key], list):
                    combined[key] = existing + r[key]
    return combined


def _prompt_set_version() -> str:
    """Fingerprint the prompt templates so an issue records the wording used.

    Without this, comparing two weeks of output cannot distinguish a change in
    the world from a change in the instructions.
    """
    import hashlib

    from prompts import PROMPT_DIR

    digest = hashlib.sha256()
    for path in sorted(PROMPT_DIR.rglob("*.json")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def _recent_week_ids(count: int = 4) -> list[str]:
    """Week ids for the preceding weeks, oldest first, for cross-week matching."""
    from datetime import datetime, timedelta

    today = datetime.now()
    ids: list[str] = []
    for back in range(1, count + 1):
        day = today - timedelta(weeks=back)
        iso = day.isocalendar()
        ids.append(f"{iso.year}-W{iso.week:02d}")
    return list(reversed(ids))


def _cluster_events(raw_events: list[dict], log: logging.Logger) -> list[dict]:
    """Phase 0: collapse hot topics into events with stable identities."""
    from tracking.events import actor_key

    prior = load_recent_dossiers(_recent_week_ids(4))
    known_actors = {
        actor_key(getattr(d, "title", "")) for d in prior.values()
    }
    known_actors.discard("")
    events = assign_event_identity(
        raw_events,
        known_event_ids=set(prior),
        known_actors=known_actors,
    )
    continuing = sum(1 for e in events if e.get("eventStatus") == "持续发展")
    log.info(
        "  聚类为 %d 个事件（其中 %d 个为上期持续追踪）", len(events), continuing
    )
    return events


def _collect_dossiers(
    events: list[dict],
    *,
    max_dossiers: int,
    max_page_fetches: int,
    log: logging.Logger,
) -> dict[str, Any]:
    """Phase 0.5: build the evidence file for each candidate event.

    Runs before any analysis so the dialectical phases read from retrieved
    material rather than from a headline and a heat ranking.
    """
    dossiers: dict[str, Any] = {}
    targets = events[:max_dossiers]
    if not targets:
        return dossiers

    log.info("[Phase 0.5] 证据建档（%d 个事件）...", len(targets))
    for i, event in enumerate(targets, 1):
        title = str(event.get("title") or "")
        log.info("  (%d/%d) 检索: %s", i, len(targets), title)
        try:
            dossier = collect_dossier(event, max_fetches=max_page_fetches)
        except Exception as exc:
            log.warning("  (%d) 建档失败: %s", i, exc)
            continue
        dossiers[dossier.eventId] = dossier
        log.info(
            "    → %d 条来源（独立来源 %d，正文 %d）",
            len(dossier.sources),
            dossier.independent_count,
            sum(1 for s in dossier.sources if s.content),
        )
    return dossiers


def _build_phase3(quality_events: list[dict]) -> Any:
    """Bridge the per-event analyses into the single unfolding the template takes.

    The highest-confidence event represents the phase; every event's full
    analysis remains in the JSON payload.  Rendering the phase at all is the
    point -- it was previously pinned to None, so adversarial review and the
    dialectical findings never reached the Markdown.
    """
    from schema import DialecticalUnfolding

    if not quality_events:
        return None
    rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    primary = min(
        quality_events,
        key=lambda e: rank.get(str(e.get("dialecticalConfidence", "LOW")), 3),
    )
    fields = {
        k: v for k, v in primary.items() if k in DialecticalUnfolding.model_fields
    }
    try:
        return DialecticalUnfolding(**fields)
    except Exception as exc:
        logger.warning("  phase3 构建失败: %s", exc)
        return None


def _facts_only_phase1(p1_merged: dict, gate: Any) -> dict:
    """Strip analysis from Phase 1 when publication was blocked.

    What remains is what the block permits: the facts, their sources, and the
    unresolved problems.
    """
    payload = dict(p1_merged)
    selected = []
    for event in payload.get("selectedEvents", []) or []:
        item = dict(event)
        # The material-content field is where unsupported motives were stated,
        # so it is exactly the field that must not survive a block.
        item["materialContent"] = ""
        selected.append(item)
    payload["selectedEvents"] = selected
    note = "本期因存在未解决的证据问题，仅发布事实与争议，不发布分析结论。"
    if gate is not None and gate.blockingClaims:
        note += " 主要问题：" + "；".join(gate.blockingClaims[:3])
    payload["sourceQualityReport"] = note
    return payload


def _verify_and_revise_event(
    *,
    event_analysis: dict,
    dossier: Any,
    event_id: str,
    round_no: int,
    empirical_client: DeepSeekClient | None,
    log: logging.Logger,
) -> tuple[dict, list, list]:
    """Extract claims, collect reviewer verdicts, and apply the revisions.

    Returns (revised_analysis, claims, revision_records).  One application per
    round: applying twice would double-hedge a sentence into nonsense.
    """
    sources = list(getattr(dossier, "sources", []) or [])
    claims = extract_claims(
        event_analysis,
        event_id=event_id,
        sources=sources,
        claim_prefix=f"{event_id}-r{round_no}",
    )

    if empirical_client is not None:
        verifier = safe_call(verify_evidence, empirical_client, event_analysis, claims)
        if isinstance(verifier, dict):
            reviews = verifier.get("claimReviews") or []
            if reviews:
                log.info("    verifier 审查 %d 条断言", len(reviews))
            from evidence.claims import apply_review_verdicts

            apply_review_verdicts(claims, reviews)

        adversary = safe_call(adversarial_review, empirical_client, event_analysis, claims)
        if isinstance(adversary, dict):
            challenges = adversary.get("challenges") or []
            if challenges:
                log.info("    adversary 提出 %d 项挑战", len(challenges))
            from evidence.claims import apply_review_verdicts

            apply_review_verdicts(claims, challenges)

    revised, records = apply_revisions(event_analysis, claims, round_no=round_no)
    if records:
        log.info("    已修订断言: %s", summarise_records(records))
    return revised, claims, records


def _build_evidence_only_issue(
    raw_events: list[dict],
    from_cache: bool,
) -> WeeklyIssue:
    """Build a readable source report without calling a model provider."""
    events: list[SelectedEvent] = []
    for index, raw in enumerate(raw_events):
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("title") or "(无标题)").strip()
        summary = str(raw.get("summary") or "").strip()
        source_url = _source_url(raw)
        if source_url:
            summary = re.sub(
                rf"\s*来源:\s*{re.escape(source_url)}\s*$", "", summary,
            ).strip()
        events.append(SelectedEvent(
            id=str(raw.get("id") or f"raw-{index + 1}"),
            title=title,
            summary=summary,
            sourceUrl=source_url or None,
        ))

    cache_note = "本期数据来自上次成功抓取的缓存。" if from_cache else "本期数据来自本次抓取。"
    phase1 = PhenomenonGrasping(
        phaseSummary=(
            f"{cache_note} 共整理 {len(events)} 条公开热点素材。"
            "本报告保留标题、摘要和来源，未生成模型分析结论。"
        ),
        selectedEvents=events,
        sourceQualityReport="以下内容是来源素材的整理，不代表独立核验或事实判断。",
    )
    week_start, week_end = get_week_range()
    return WeeklyIssue(
        id=get_week_id(),
        weekStart=week_start,
        weekEnd=week_end,
        events=events,
        phase1=phase1,
        evidenceTrace=EvidenceTrace(),
        metadata=IssueMetadata(
            modelVersions={},
            totalApiCost=0.0,
            runDuration=0.0,
            runId=RUN_ID,
        ),
    )


def _write_outputs(
    issue: WeeklyIssue,
    events_payload: list[dict],
    phase_payloads: dict[str, Any] | None = None,
    article_body: str | None = None,
) -> None:
    """Write the JSON and Markdown forms of an issue.

    `article_body` is the narrative section.  When it is absent the
    deterministic five-phase rendering is used instead, so a failed narrative
    degrades to a weaker article rather than to no article.
    """
    phase_payloads = phase_payloads or {}
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_path = WEB_DATA_DIR / f"{issue.id}.json"
    json_payload = {
        "id": issue.id,
        "weekStart": issue.weekStart,
        "weekEnd": issue.weekEnd,
        "events": events_payload,
        "phase1": phase_payloads.get("phase1", issue.phase1.model_dump()),
        "phase2": phase_payloads.get(
            "phase2", issue.phase2.model_dump() if issue.phase2 else None,
        ),
        "phase4": phase_payloads.get(
            "phase4", issue.phase4.model_dump() if issue.phase4 else None,
        ),
        "phase5": phase_payloads.get(
            "phase5", issue.phase5.model_dump() if issue.phase5 else None,
        ),
        "evidenceTrace": issue.evidenceTrace.model_dump(),
        "metadata": issue.metadata.model_dump(),
        "evidence": [d.model_dump() for d in issue.evidence],
        "revisionLog": [r.model_dump() for r in issue.revisionLog],
        "publicationGate": issue.publicationGate.model_dump()
        if issue.publicationGate
        else None,
    }
    json_path.write_text(
        json.dumps(json_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    blog_root = BLOG_CONTENT_DIR.parent
    posts_dir = blog_root / "posts" / issue.id
    posts_dir.mkdir(parents=True, exist_ok=True)
    article_path = posts_dir / "index.md"
    if article_body:
        markdown = assemble_article(issue, article_body)
    else:
        markdown = generate_article(issue, blog_root)
    article_path.write_text(markdown, encoding="utf-8")
    logger.info("输出 JSON: %s", json_path)
    logger.info("输出文章: %s", article_path)
    logger.info("共 %d 个素材事件", len(events_payload))


# =============================================================================
# Main pipeline
# =============================================================================


def _write_evidence_report(
    raw_events: list[dict],
    from_cache: bool,
    dry_run: bool,
    *,
    total_cost: float = 0.0,
) -> None:
    issue = _build_evidence_only_issue(raw_events, from_cache)
    issue.metadata.totalApiCost = total_cost
    if dry_run:
        logger.info("Evidence-only dry run complete. 共 %d 个素材", len(issue.events))
        return
    _write_outputs(issue, [event.model_dump() for event in issue.events])


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    setup_logging(verbose=args.verbose)
    logger.info("Run %s started", RUN_ID)

    from datetime import date as _date

    analysis_date = _date.today().isoformat()
    prompt_version = _prompt_set_version()
    logger.info("  prompt set %s", prompt_version)

    phase_start: dict[str, float] = {}

    def _phase_begin(name: str) -> None:
        phase_start[name] = time.time()

    def _phase_done(name: str) -> None:
        elapsed = time.time() - phase_start.get(name, time.time())
        logger.info("[%s] 耗时 %.1fs", name, elapsed)

    # =====================================================================
    # Phase 0: Scrape
    # =====================================================================
    _phase_begin("Phase 0")
    raw_events, from_cache = _scrape_or_load_cache(args)
    events = _cluster_events(raw_events, logger)
    _phase_done("Phase 0")

    if not DEEPSEEK_API_KEY:
        logger.info("未配置模型服务，输出证据整理报告")
        _write_evidence_report(events, from_cache, args.dry_run)
        return

    # ---- Model clients ----
    try:
        dialectical_client = DeepSeekClient(
            DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_DIALECTICAL, thinking=True,
        )
        empirical_client = DeepSeekClient(
            DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_EMPIRICAL,
        )
    except ImportError:
        logger.warning("模型 SDK 未安装，输出证据整理报告")
        _write_evidence_report(events, from_cache, args.dry_run)
        return

    # =====================================================================
    # Phase 0.5: Evidence dossiers (before any analysis)
    # =====================================================================
    _phase_begin("Phase 0.5")
    dossiers = _collect_dossiers(
        events,
        max_dossiers=args.max_dossiers,
        max_page_fetches=args.max_page_fetches,
        log=logger,
    )
    _phase_done("Phase 0.5")
    evidence_cutoff = max(
        (getattr(d, "retrievedAt", "") for d in dossiers.values()), default=""
    )

    # =====================================================================
    # Phase 1: Phenomenon Grasping
    # =====================================================================
    _phase_begin("Phase 1")
    logger.info("[Phase 1] 现象把握（辩证层）...")
    p1_dialectical = grasp_phenomena(dialectical_client, events, dossiers)
    selected_count = len(p1_dialectical.get("selectedEvents", []))
    logger.info("  入选 %d 个事件，排除 %d 个",
                selected_count,
                len(p1_dialectical.get("excludedEvents", [])))

    logger.info("[Phase 1] 信源验证（实证层）...")
    p1_empirical = _empirical_verify_events(
        empirical_client, p1_dialectical.get("selectedEvents", []),
    )
    if p1_empirical is None:
        logger.info("  实证层降级：验证不可用")

    p1_model = PhenomenonGrasping(**p1_dialectical)
    p1_merged = merge_phase(p1_model, p1_empirical)
    _phase_done("Phase 1")

    selected = _carry_source_urls(
        p1_merged.get("selectedEvents", []), raw_events,
    )
    p1_merged["selectedEvents"] = selected
    if not selected:
        logger.warning("Phase 1 未返回事件，降级为证据整理报告")
        _write_evidence_report(
            raw_events, from_cache, args.dry_run,
            total_cost=float(dialectical_client.total_cost + empirical_client.total_cost),
        )
        return

    # =====================================================================
    # Phase 2: Contradiction Identification
    # =====================================================================
    _phase_begin("Phase 2")
    logger.info("[Phase 2] 矛盾识别（辩证层）...")
    p2_dialectical = identify_contradictions(dialectical_client, selected, dossiers)
    p2_event_count = len(p2_dialectical.get("events", []))
    logger.info("  分析 %d 个事件", p2_event_count)

    logger.info("[Phase 2] 九维评分（实证层）...")
    p2_empirical = _empirical_score_events(
        empirical_client, p2_dialectical.get("events", []),
    )
    if p2_empirical is None:
        logger.info("  实证层降级：评分不可用")

    p2_model = ContradictionIdentification(**p2_dialectical)
    p2_merged = merge_phase(p2_model, p2_empirical)
    _phase_done("Phase 2")

    p2_events = _carry_source_urls(p2_merged.get("events", []), selected)
    p2_merged["events"] = p2_events
    if not p2_events:
        logger.warning("Phase 2 未返回事件，降级为证据整理报告")
        _write_evidence_report(
            raw_events, from_cache, args.dry_run,
            total_cost=float(dialectical_client.total_cost + empirical_client.total_cost),
        )
        return

    # Cap events for analysis
    p2_events = p2_events[:args.max_events]

    # =====================================================================
    # Phase 3: Dialectical Unfolding (parallel per-event)
    # =====================================================================
    _phase_begin("Phase 3")
    logger.info("[Phase 3] 辩证展开（并行逐事件分析）...")
    quality_events = _parallel_analyze(
        dialectical_client, p2_events, logger, dossiers,
    )
    _phase_done("Phase 3")

    # =====================================================================
    # Phase 3.5: Claim extraction, verification, and revision
    # =====================================================================
    _phase_begin("Phase 3.5")
    logger.info("[Phase 3.5] 断言抽取与修订（最多 %d 轮）...", args.max_revision_rounds)
    claims_by_event: dict[str, list] = {}
    revision_log: list = []
    # Later rounds only revisit events that still carry a high-risk assertion,
    # which keeps a second pass cheap instead of re-verifying everything.
    retry_ids: set[str] | None = None
    for round_no in range(1, args.max_revision_rounds + 1):
        for event in quality_events:
            event_id = str(event.get("eventId") or event.get("id") or "")
            if retry_ids is not None and event_id not in retry_ids:
                continue
            revised, claims, records = _verify_and_revise_event(
                event_analysis=event,
                dossier=dossiers.get(event_id),
                event_id=event_id,
                round_no=round_no,
                empirical_client=empirical_client,
                log=logger,
            )
            event.clear()
            event.update(revised)
            claims_by_event[event_id] = claims
            revision_log.extend(records)

        residual = scan_residual_risk({
            str(e.get("eventId") or e.get("id") or ""): e for e in quality_events
        })
        if not residual:
            logger.info("  第 %d 轮后无残留高风险断言", round_no)
            break
        retry_ids = {str(getattr(c, "eventId", "")) for c in residual}
        logger.info(
            "  第 %d 轮后仍有 %d 条高风险断言（涉及 %d 个事件）",
            round_no, len(residual), len(retry_ids),
        )
    else:
        logger.warning("  修订轮次用尽，仍有高风险断言残留，将触发降级发布")
    _phase_done("Phase 3.5")

    if not quality_events:
        logger.warning("质量筛选后没有事件留存，降级为证据整理报告")
        _write_evidence_report(
            raw_events, from_cache, args.dry_run,
            total_cost=float(dialectical_client.total_cost + empirical_client.total_cost),
        )
        return

    # =====================================================================
    # Phase 4: Historical Positioning (skip if < 2 quality events)
    # =====================================================================
    p4_final: dict | None = None
    if len(quality_events) >= 2:
        _phase_begin("Phase 4")
        logger.info("[Phase 4] 历史定位（辩证层）...")
        p4_dialectical = position_historically(dialectical_client, quality_events)
        logger.info("  定位完成")

        logger.info("[Phase 4] 关联发现 + 因果回路（实证层）...")
        p4_emp_conn = safe_call(find_connections, empirical_client, quality_events)
        p4_emp_causal = safe_call(build_causal_loop, empirical_client, quality_events)
        p4_empirical = _combine_empirical(p4_emp_conn, p4_emp_causal)
        if p4_empirical is None:
            logger.info("  实证层降级：关联与因果分析不可用")

        p4_model = HistoricalPositioning(**p4_dialectical)
        p4_final = merge_phase(p4_model, p4_empirical)
        _phase_done("Phase 4")
    else:
        logger.info("[Phase 4] 事件不足 2 个，跳过历史定位")

    # =====================================================================
    # Phase 5: Practice Orientation (skip if < 2 quality events)
    # =====================================================================
    p5_final: dict | None = None
    if p4_final and len(quality_events) >= 2:
        _phase_begin("Phase 5")
        logger.info("[Phase 5] 实践导向（辩证层）...")
        p5_dialectical = orient_practice(dialectical_client, p4_final)
        logger.info("  实践导向完成")

        logger.info("[Phase 5] 情景规划（实证层）...")
        # Adapt p4_final for plan_scenarios: it expects weeklyNarrative
        synthesis_input = dict(p4_final)
        if "weeklyNarrative" not in synthesis_input:
            synthesis_input["weeklyNarrative"] = (
                synthesis_input.get("crossCuttingSynthesis", "")
                or synthesis_input.get("phaseSummary", "")
            )
        p5_empirical = safe_call(plan_scenarios, empirical_client, synthesis_input)
        if p5_empirical is None:
            logger.info("  实证层降级：情景规划不可用")

        p5_model = PracticeOrientation(**p5_dialectical)
        p5_final = merge_phase(p5_model, p5_empirical)
        _phase_done("Phase 5")
    else:
        logger.info("[Phase 5] 事件不足 2 个，跳过实践导向")

    # =====================================================================
    # Phase 6: Publication gate (deterministic)
    # =====================================================================
    _phase_begin("Phase 6")
    logger.info("[Phase 6] 发布门禁...")
    analyses = {
        str(e.get("eventId") or e.get("id") or ""): e for e in quality_events
    }
    all_claims = [c for claims in claims_by_event.values() for c in claims]
    gate = publication_gate(
        dossiers=list(dossiers.values()),
        claims=all_claims,
        analysis_by_event=analyses,
    )
    _phase_done("Phase 6")

    if gate.decision == "BLOCK":
        logger.error(
            "[Phase 6] 发布被阻止，仅输出事实与争议：%s",
            "；".join(gate.blockingClaims[:3]),
        )

    # =====================================================================
    # Cross-week tracking
    # =====================================================================
    annotations, tracking_notes = track_changes(
        list(dossiers.values()), load_recent_dossiers(_recent_week_ids(4))
    )
    if tracking_notes:
        logger.info("[tracking] 检出 %d 处事件变化", len(tracking_notes))

    # =====================================================================
    # Dry-run: report cost and exit
    # =====================================================================
    total_cost = float(dialectical_client.total_cost + empirical_client.total_cost)

    if args.dry_run:
        logger.info(
            "Dry run complete. 共 %d 个质量事件，发布判定 %s，预估费用 $%.4f",
            len(quality_events), gate.decision, total_cost,
        )
        return

    # =====================================================================
    # Assemble output
    # =====================================================================
    week_id = get_week_id()
    week_start, week_end = get_week_range()

    # Build SelectedEvent instances for the WeeklyIssue events list
    issue_events: list[SelectedEvent] = []
    for e in quality_events:
        identity = {
            "id": str(e.get("id") or f"evt-{len(issue_events)+1}"),
            "title": e.get("title", "(无标题)"),
            "summary": e.get("summary", ""),
            "sourceUrl": e.get("sourceUrl"),
            "materialContent": e.get("materialContent", ""),
            "isDirectExpression": e.get("isDirectExpression", False),
            "eventId": e.get("eventId"),
            "topicAliases": e.get("topicAliases") or [],
            "sourcePlatform": e.get("sourcePlatform"),
            "firstSeenAt": e.get("firstSeenAt"),
            "lastSeenAt": e.get("lastSeenAt"),
            "eventStatus": e.get("eventStatus"),
        }
        try:
            issue_events.append(SelectedEvent(**identity))
        except Exception:
            identity.pop("eventId", None)
            issue_events.append(SelectedEvent(**identity))

    issue = WeeklyIssue(
        id=week_id,
        weekStart=week_start,
        weekEnd=week_end,
        events=issue_events,
        phase1=PhenomenonGrasping(**{
            k: v for k, v in p1_merged.items()
            if k in PhenomenonGrasping.model_fields
        }),
        phase2=ContradictionIdentification(**{
            k: v for k, v in p2_merged.items()
            if k in ContradictionIdentification.model_fields
        }),
        # The template renderer takes a single unfolding; the complete per-event
        # set lives in the JSON `events` payload.  Previously this was hardcoded
        # to None, which silently dropped every Phase 3 finding -- including the
        # adversarial review -- from the Markdown entirely.
        phase3=_build_phase3(quality_events),
        phase4=HistoricalPositioning(**{
            k: v for k, v in p4_final.items()
            if k in HistoricalPositioning.model_fields
        }) if p4_final else None,
        phase5=PracticeOrientation(**{
            k: v for k, v in p5_final.items()
            if k in PracticeOrientation.model_fields
        }) if p5_final else None,
        evidenceTrace=EvidenceTrace(),
        evidence=list(dossiers.values()),
        revisionLog=revision_log,
        publicationGate=gate,
        metadata=IssueMetadata(
            runId=RUN_ID,
            totalApiCost=total_cost,
            runDuration=time.time() - phase_start.get("Phase 0", time.time()),
            empiricalDegradations=[
                f"Phase {i}" for i, merged in
                [(1, p1_merged), (2, p2_merged), (4, p4_final), (5, p5_final)]
                if merged and merged.get("empiricalDegraded")
            ],
            modelVersions={
                "dialectical": DEEPSEEK_MODEL_DIALECTICAL,
                "empirical": DEEPSEEK_MODEL_EMPIRICAL,
            },
            analysisDate=analysis_date,
            evidenceCutoff=evidence_cutoff,
            promptVersion=prompt_version,
        ),
    )

    # ---- Evidence dossiers are cached before publication so a re-run on an
    # event with no new information can skip retrieval entirely.
    save_dossiers(list(dossiers.values()), week_id)

    # ---- Publication gate: BLOCK publishes facts and disputes only.
    if gate.decision == "BLOCK":
        logger.warning("[Phase 6] 分析结论不予发布，改为事实与争议通报")
        _write_outputs(
            issue,
            quality_events,
            phase_payloads={
                "phase1": _facts_only_phase1(p1_merged, gate),
                "phase2": None,
                "phase4": None,
                "phase5": None,
            },
        )
        logger.info("API 费用: $%.4f", total_cost)
        return

    # ---- Article: LLM narrative over the validated claims, else the template.
    article_body: str | None = None
    if gate.decision != "BLOCK":
        context = build_article_context(
            issue, claims_by_event, list(dossiers.values()), gate,
            story_notes=tracking_notes,
        )
        article_body = generate_narrative_article(
            dialectical_client, issue, context, gate=gate,
        )
        if article_body:
            article_body, notes = sanitize_narrative(article_body)
            remaining = scan_text_risk(article_body) if notes else []
            if remaining:
                logger.warning(
                    "  正文仍残留 %d 条高风险断言，回退为模板渲染", len(remaining)
                )
                article_body = None
            elif notes:
                logger.info("  正文安全网修正 %d 处表述", len(notes))
        else:
            logger.info("  叙事生成不可用，使用模板渲染")

    _write_outputs(
        issue,
        quality_events,
        phase_payloads={
            "phase1": p1_merged,
            "phase2": p2_merged,
            "phase4": p4_final,
            "phase5": p5_final,
        },
        article_body=article_body,
    )
    logger.info("API 费用: $%.4f", total_cost)


# Backward compatibility alias for tests
parse_args = _parse_args


if __name__ == "__main__":
    main()
