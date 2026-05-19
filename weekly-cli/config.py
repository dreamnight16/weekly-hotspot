import os
from pathlib import Path

DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

BLOG_CONTENT_DIR = Path(os.environ.get(
    "BLOG_CONTENT_DIR",
    r"C:\Users\DreamNight\Documents\01My\myBlog\src\content\weekly"
))
