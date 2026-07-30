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
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from chinese_scraper_utils import DeepSeekClient

from scraper.cache import load_cache
from scraper.sources import scrape_all
from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL_DIALECTICAL,
    DEEPSEEK_MODEL_EMPIRICAL,
    BLOG_CONTENT_DIR,
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
from narrative.article import generate_article
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
    except Exception:
        return None


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="每周热点深度分析 — AI 驱动的五阶段唯物辩证法分析工具",
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


def _v2_quality_gate(event: dict) -> bool:
    """Quality gate for v2 dialectical unfolding results.

    Checks that the event has meaningful dialectical content:
    - dialecticalConfidence is not LOW
    - at least one dialectical law has substantive content
    - the event has a title
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


def _parallel_analyze(
    dialectical_client: DeepSeekClient,
    empirical_client: DeepSeekClient,
    events: list[dict],
    log: logging.Logger,
) -> list[dict]:
    """Phase 3: parallel per-event dialectical unfolding + adversarial review.

    Each event is searched (DDG+Bing), then analyzed via unfold_dialectics
    with the dialectical (pro) model, and adversarially reviewed with the
    empirical (flash) model.  Up to 3 workers run in parallel.
    """

    def _analyze_one(idx: int, event: dict) -> tuple[int, dict | None]:
        log.info("  搜索 (%d): %s", idx, event.get("title", "(无标题)"))
        search_results = search_event(event.get("title", ""), max_results=10)
        log.info("    (%d) 找到 %d 条结果", idx, len(search_results))

        try:
            unfolding = unfold_dialectics(
                dialectical_client, event, search_results, idx=idx,
            )
        except Exception as exc:
            log.warning("    (%d) unfold_dialectics 失败: %s，跳过", idx, exc)
            return (idx, None)

        if unfolding is None:
            log.warning("    (%d) unfold_dialectics 返回 None，跳过", idx)
            return (idx, None)

        # Run adversarial review with empirical model (graceful degradation)
        adversary = safe_call(adversarial_review, empirical_client, unfolding)
        if adversary is not None:
            unfolding["adversarialReview"] = adversary

        # Extract the primary event from the unfolding result
        unfolded_events = unfolding.get("events", [])
        if unfolded_events and isinstance(unfolded_events, list):
            analyzed = dict(unfolded_events[0])
        else:
            analyzed = dict(event)

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
        log.critical("  Phase 3: 没有事件通过分析，退出。")
        sys.exit(1)

    quality = [e for e in analyzed if _v2_quality_gate(e)]
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


# =============================================================================
# Main pipeline
# =============================================================================


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    setup_logging(verbose=args.verbose)
    logger.info("Run %s started", RUN_ID)

    phase_start: dict[str, float] = {}

    def _phase_begin(name: str) -> None:
        phase_start[name] = time.time()

    def _phase_done(name: str) -> None:
        elapsed = time.time() - phase_start.get(name, time.time())
        logger.info("[%s] 耗时 %.1fs", name, elapsed)

    # ---- Model clients ----
    dialectical_client = DeepSeekClient(
        DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_DIALECTICAL, thinking=True,
    )
    empirical_client = DeepSeekClient(
        DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_EMPIRICAL,
    )

    # =====================================================================
    # Phase 0: Scrape
    # =====================================================================
    _phase_begin("Phase 0")
    raw_events, _from_cache = _scrape_or_load_cache(args)
    _phase_done("Phase 0")

    # =====================================================================
    # Phase 1: Phenomenon Grasping
    # =====================================================================
    _phase_begin("Phase 1")
    logger.info("[Phase 1] 现象把握（辩证层）...")
    p1_dialectical = grasp_phenomena(dialectical_client, raw_events)
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

    selected = p1_merged.get("selectedEvents", [])
    if not selected:
        logger.critical("Phase 1: 无入选事件，退出。")
        if args.dry_run:
            total_cost = float(dialectical_client.total_cost + empirical_client.total_cost)
            logger.info("Dry run complete. 预估费用 $%.4f", total_cost)
        sys.exit(1)

    # =====================================================================
    # Phase 2: Contradiction Identification
    # =====================================================================
    _phase_begin("Phase 2")
    logger.info("[Phase 2] 矛盾识别（辩证层）...")
    p2_dialectical = identify_contradictions(dialectical_client, selected)
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

    p2_events = p2_merged.get("events", [])
    if not p2_events:
        logger.critical("Phase 2: 无事件通过矛盾识别，退出。")
        if args.dry_run:
            total_cost = float(dialectical_client.total_cost + empirical_client.total_cost)
            logger.info("Dry run complete. 预估费用 $%.4f", total_cost)
        sys.exit(1)

    # Cap events for analysis
    p2_events = p2_events[:args.max_events]

    # =====================================================================
    # Phase 3: Dialectical Unfolding (parallel per-event)
    # =====================================================================
    _phase_begin("Phase 3")
    logger.info("[Phase 3] 辩证展开（并行逐事件分析）...")
    quality_events = _parallel_analyze(
        dialectical_client, empirical_client, p2_events, logger,
    )
    _phase_done("Phase 3")

    if not quality_events:
        logger.critical("质量筛选后没有事件留存，退出。")
        if args.dry_run:
            total_cost = float(dialectical_client.total_cost + empirical_client.total_cost)
            logger.info("Dry run complete. 预估费用 $%.4f", total_cost)
        sys.exit(1)

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
    # Dry-run: report cost and exit
    # =====================================================================
    total_cost = float(dialectical_client.total_cost + empirical_client.total_cost)

    if args.dry_run:
        logger.info(
            "Dry run complete. 共 %d 个质量事件，预估费用 $%.4f",
            len(quality_events), total_cost,
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
        try:
            issue_events.append(SelectedEvent(
                id=e.get("id", f"evt-{len(issue_events)+1}"),
                title=e.get("title", "(无标题)"),
                summary=e.get("summary", ""),
                materialContent=e.get("materialContent", ""),
                isDirectExpression=e.get("isDirectExpression", False),
            ))
        except Exception:
            issue_events.append(SelectedEvent(
                id=f"evt-{len(issue_events)+1}",
                title=e.get("title", "(无标题)"),
                summary=e.get("summary", ""),
            ))

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
        phase3=None,  # per-event analysis lives in the quality_events dicts
        phase4=HistoricalPositioning(**{
            k: v for k, v in p4_final.items()
            if k in HistoricalPositioning.model_fields
        }) if p4_final else None,
        phase5=PracticeOrientation(**{
            k: v for k, v in p5_final.items()
            if k in PracticeOrientation.model_fields
        }) if p5_final else None,
        evidenceTrace=EvidenceTrace(),
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
        ),
    )

    # ---- JSON output ----
    BLOG_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = BLOG_CONTENT_DIR / f"{week_id}.json"
    json_payload = {
        "id": issue.id,
        "weekStart": issue.weekStart,
        "weekEnd": issue.weekEnd,
        "events": quality_events,  # full v2 event dicts with analysis
        "phase1": p1_merged,
        "phase2": p2_merged,
        "phase4": p4_final,
        "phase5": p5_final,
        "evidenceTrace": issue.evidenceTrace.model_dump(),
        "metadata": issue.metadata.model_dump(),
    }
    json_path.write_text(
        json.dumps(json_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # ---- Markdown article output ----
    blog_root = BLOG_CONTENT_DIR.parent  # src/content
    posts_dir = blog_root / "posts" / week_id
    posts_dir.mkdir(parents=True, exist_ok=True)
    article_path = posts_dir / "index.md"
    md = generate_article(issue, blog_root)
    article_path.write_text(md, encoding="utf-8")

    logger.info("输出 JSON: %s", json_path)
    logger.info("输出文章: %s", article_path)
    logger.info("共 %d 个质量事件", len(quality_events))
    logger.info("API 费用: $%.4f", total_cost)


# Backward compatibility alias for tests
parse_args = _parse_args


if __name__ == "__main__":
    main()
