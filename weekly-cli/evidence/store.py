"""Evidence layer: dossier persistence and cross-run reuse.

Dossiers are cached so a re-run on an event with no new information does not
repeat retrieval.  Reuse is keyed on source fingerprints rather than on the
event id alone: if a page changed under us, the cached dossier is stale and
must be rebuilt, not silently reused.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from config import get_logger

logger = get_logger("evidence.store")

CACHE_DIR = Path.home() / ".cache" / "weekly-hotspot" / "dossiers"


def _dossier_path(week_id: str) -> Path:
    return CACHE_DIR / f"{week_id}.json"


def save_dossiers(dossiers: Iterable, week_id: str) -> Optional[Path]:
    """Persist dossiers for a week.  Returns the path, or None on failure."""
    payload = [d.model_dump() for d in dossiers]
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _dossier_path(week_id)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info("[evidence] 已缓存 %d 份证据档案: %s", len(payload), path)
        return path
    except (OSError, TypeError, ValueError) as exc:
        logger.warning("[evidence] 证据档案缓存失败: %s", exc)
        return None


def load_dossiers(week_id: str) -> list:
    """Load cached dossiers for a week, or an empty list."""
    from schema import EvidenceDossier

    path = _dossier_path(week_id)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("[evidence] 证据档案读取失败: %s", exc)
        return []
    out = []
    for item in raw if isinstance(raw, list) else []:
        try:
            out.append(EvidenceDossier(**item))
        except Exception as exc:  # a corrupt entry must not sink the rest
            logger.warning("[evidence] 跳过损坏的档案: %s", exc)
    return out


def load_recent_dossiers(week_ids: Iterable[str]) -> dict[str, object]:
    """Map eventId -> most recent dossier across the given weeks (oldest first)."""
    history: dict[str, object] = {}
    for week_id in week_ids:
        for dossier in load_dossiers(week_id):
            if getattr(dossier, "eventId", ""):
                history[dossier.eventId] = dossier
    return history


def fingerprint_set(dossier) -> set[str]:
    """Set of source content fingerprints in a dossier."""
    return {
        getattr(s, "contentFingerprint", "")
        for s in getattr(dossier, "sources", [])
        if getattr(s, "contentFingerprint", "")
    }


def has_new_information(old, new) -> bool:
    """True when *new* carries source fingerprints absent from *old*.

    Events with nothing new can skip the expensive analysis stages, which is
    the main cost control on a weekly re-run.
    """
    if old is None:
        return True
    return bool(fingerprint_set(new) - fingerprint_set(old))
