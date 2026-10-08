import logging
import os
import sys
import uuid
from pathlib import Path

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-flash"
DEEPSEEK_MODEL_PRO = "deepseek-v4-pro"

# v2 dialectical/empirical routing
DEEPSEEK_MODEL_DIALECTICAL = "deepseek-v4-pro"   # thinking=True for dialectical layers
DEEPSEEK_MODEL_EMPIRICAL = "deepseek-v4-flash"    # lighter model for empirical layers

MODEL_ROUTING = {
    "dialectical": DEEPSEEK_MODEL_DIALECTICAL,
    "empirical": DEEPSEEK_MODEL_EMPIRICAL,
}

_default_blog_dir = Path.home() / "Documents" / "Blog-mizuki" / "src" / "content" / "weekly"
BLOG_CONTENT_DIR = Path(os.environ.get("BLOG_CONTENT_DIR", str(_default_blog_dir)))

# 验证路径不超出预期范围（防环境变量投毒）
if "BLOG_CONTENT_DIR" in os.environ:
    resolved = BLOG_CONTENT_DIR.resolve()
    home = Path.home()
    if not str(resolved).startswith(str(home)):
        print(f"错误: BLOG_CONTENT_DIR 必须在用户目录下: {resolved}", file=sys.stderr)
        sys.exit(1)

# 独立站（格物）的数据输出目录；缺省与 BLOG_CONTENT_DIR 相同以保持向后兼容。
# 文章仍写入 BLOG_CONTENT_DIR 同级的 posts/ 下，保持"文章在博客、数据在格物"。
WEB_DATA_DIR = Path(os.environ.get("WEB_DATA_DIR", str(BLOG_CONTENT_DIR)))

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
