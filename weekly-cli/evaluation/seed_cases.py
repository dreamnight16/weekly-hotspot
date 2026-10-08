"""Seed evaluation cases from previously produced weekly reports.

Run: uv run python weekly-cli/evaluation/seed_cases.py

The seed set is built from real output rather than from invented examples,
because the failures worth regressing on are the ones the pipeline actually
committed.  Annotations (which assertions are forbidden, which analysis must
survive) are curated by hand and preserved across re-seeding.

Re-seeding is safe: an existing case file is never overwritten unless
--force is passed, so hand-written annotations are not lost.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CASES_DIR = Path(__file__).parent / "cases"
DEFAULT_DATA_DIR = Path(__file__).parents[2] / "web" / "src" / "data" / "weekly"

ANALYSIS_KEYS = ("materialContent", "phaseSummary")
NESTED_KEYS = (
    "unityOfOpposites",
    "quantityQuality",
    "negationOfNegation",
    "dataValidation",
)

# Category assignment is keyword-based and deliberately coarse: it exists to
# keep the case set balanced, not to be a classifier.
CATEGORY_HINTS = (
    ("企业安全事件", ("刹车", "踏板", "召回", "缺陷", "断裂", "事故", "伤亡", "爆炸")),
    ("劳动争议", ("加班", "工资", "裁员", "劳动", "员工", "欠薪", "工伤")),
    ("公共政策", ("政策", "监管", "低保", "禁渔", "调休", "收费", "医保")),
    ("科研成果", ("论文", "研究", "芯片", "算力", "AI", "人工智能", "技术")),
    ("经济数据", ("价格", "汇率", "存款", "利润", "营收", "市场", "股价")),
    ("国际事件", ("日本", "美国", "英国", "欧盟", "墨西哥", "苏格兰", "全球")),
)

# Cases whose analysis demonstrably overstated its evidence.  These assertions
# must not survive revision verbatim.
CURATED: dict[str, dict] = {
    "尊界": {
        "forbiddenAssertions": [
            "希望通过主动通报控制舆论，避免大规模召回和赔偿",
        ],
        "mustPreserve": ["刹车踏板", "召回"],
        "notes": (
            "2026-W41 实际产出。Phase 1 在仅有标题与热搜排名的情况下，"
            "生成了确定语气的动机归因，并给出 B3 信源等级；"
            "Phase 2 进一步量化为『可能达数亿元』。对抗审查已识别该问题，"
            "但其结论当时未进入文章。"
        ),
    },
}


def categorize(title: str) -> str:
    for label, hints in CATEGORY_HINTS:
        if any(h in title for h in hints):
            return label
    return "其他"


def extract_analysis(event: dict) -> dict:
    analysis: dict = {}
    for key in ANALYSIS_KEYS:
        if isinstance(event.get(key), str) and event[key].strip():
            analysis[key] = event[key]
    for key in NESTED_KEYS:
        value = event.get(key)
        if isinstance(value, dict) and any(value.values()):
            analysis[key] = value
    return analysis


def sources_for(event: dict) -> list[dict]:
    url = event.get("sourceUrl")
    if not url:
        return []
    return [
        {
            "sourceId": f"src-{abs(hash(url)) % 10**8:08d}",
            "url": url,
            "title": event.get("title", ""),
            "kind": "UNKNOWN",
            "content": event.get("summary", ""),
            "snippet": event.get("summary", ""),
        }
    ]


def build_case(week_id: str, index: int, event: dict) -> dict | None:
    analysis = extract_analysis(event)
    if not analysis:
        return None
    title = str(event.get("title") or "")
    case_id = f"{week_id}-e{index:02d}"

    curated = next(
        (payload for key, payload in CURATED.items() if key in title), {}
    )
    case = {
        "caseId": case_id,
        "title": title,
        "week": week_id,
        "category": categorize(title),
        "analysis": analysis,
        "sources": sources_for(event),
        "forbiddenAssertions": curated.get("forbiddenAssertions", []),
        "mustPreserve": curated.get("mustPreserve", []),
    }
    if curated.get("notes"):
        case["notes"] = curated["notes"]
    return case


def main() -> None:
    parser = argparse.ArgumentParser(description="从历史周报生成评测案例")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--force", action="store_true", help="覆盖已有案例")
    args = parser.parse_args()

    CASES_DIR.mkdir(parents=True, exist_ok=True)
    created = skipped = 0

    for path in sorted(args.data_dir.glob("*.json")):
        week_id = path.stem
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for index, event in enumerate(payload.get("events") or []):
            if not isinstance(event, dict):
                continue
            case = build_case(week_id, index, event)
            if case is None:
                continue
            out = CASES_DIR / f"{case['caseId']}.json"
            if out.exists() and not args.force:
                skipped += 1
                continue
            out.write_text(
                json.dumps(case, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            created += 1

    print(f"生成 {created} 个案例，保留已有 {skipped} 个 → {CASES_DIR}")


if __name__ == "__main__":
    main()
