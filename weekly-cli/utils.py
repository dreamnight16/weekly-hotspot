"""Shared utility functions used across the pipeline."""
import random
import time
from datetime import datetime, timedelta


def get_week_id() -> str:
    today = datetime.now()
    iso = today.isocalendar()
    return f"{today.year}-W{iso.week:02d}"


def get_week_range() -> tuple[str, str]:
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


def retry_call(fn, *args, phase: str = "", max_retries: int = 2, **kwargs):
    """带退避重试的调用封装。"""
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt + random.uniform(0, 1)
                from config import get_logger
                logger = get_logger("utils")
                logger.warning("  [%s] 失败: %s，%.0fs 后重试...", phase, e, wait)
                time.sleep(wait)
            else:
                raise


def section_label(n: int) -> str:
    """数字转中文序号。"""
    labels = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    if n < len(labels):
        return labels[n]
    return str(n)
