import os
import sys
from pathlib import Path

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("错误: 未设置 DEEPSEEK_API_KEY 环境变量", file=sys.stderr)
    sys.exit(1)
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-flash"
DEEPSEEK_MODEL_PRO = "deepseek-v4-pro"

_default_blog_dir = Path.home() / "Documents" / "myBlog" / "src" / "content" / "weekly"
BLOG_CONTENT_DIR = Path(os.environ.get("BLOG_CONTENT_DIR", str(_default_blog_dir)))

# 验证路径不超出预期范围（防环境变量投毒）
if "BLOG_CONTENT_DIR" in os.environ:
    resolved = BLOG_CONTENT_DIR.resolve()
    home = Path.home()
    if not str(resolved).startswith(str(home)):
        print(f"错误: BLOG_CONTENT_DIR 必须在用户目录下: {resolved}", file=sys.stderr)
        sys.exit(1)
