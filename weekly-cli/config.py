import os
import sys
from pathlib import Path

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("错误: 未设置 DEEPSEEK_API_KEY 环境变量", file=sys.stderr)
    sys.exit(1)
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

BLOG_CONTENT_DIR = Path(os.environ.get(
    "BLOG_CONTENT_DIR",
    r"C:\Users\DreamNight\Documents\01My\myBlog\src\content\weekly"
))
