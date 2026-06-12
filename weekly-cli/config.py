import logging
import os
import sys
import uuid
from pathlib import Path

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("错误: 未设置 DEEPSEEK_API_KEY 环境变量", file=sys.stderr)
    sys.exit(1)
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-flash"
DEEPSEEK_MODEL_PRO = "deepseek-v4-pro"

_default_blog_dir = Path.home() / "Documents" / "Blog-mizuki" / "src" / "content" / "weekly"
BLOG_CONTENT_DIR = Path(os.environ.get("BLOG_CONTENT_DIR", str(_default_blog_dir)))

# 验证路径不超出预期范围（防环境变量投毒）
if "BLOG_CONTENT_DIR" in os.environ:
    resolved = BLOG_CONTENT_DIR.resolve()
    home = Path.home()
    if not str(resolved).startswith(str(home)):
        print(f"错误: BLOG_CONTENT_DIR 必须在用户目录下: {resolved}", file=sys.stderr)
        sys.exit(1)

RUN_ID = uuid.uuid4().hex[:12]


def setup_logging(verbose: bool = False) -> None:
    """Configure structured logging to stdout."""
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "[%(levelname)s] %(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    ))
    root = logging.getLogger("weekly")
    root.setLevel(level)
    root.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under the 'weekly' namespace."""
    return logging.getLogger(f"weekly.{name}")
