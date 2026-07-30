"""抓取缓存 — 抓取全失败时回退上次数据，避免流水线中断。"""
import json
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "weekly-hotspot"
CACHE_FILE = CACHE_DIR / "last_raw_events.json"


def save_cache(events: list[dict]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(events, ensure_ascii=False), encoding="utf-8")


def load_cache() -> list[dict] | None:
    if not CACHE_FILE.exists():
        return None
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
