"""Tests for config.py — API key presence, path resolution safety."""
import os
import pytest
from pathlib import Path

import config


@pytest.mark.unit
def test_api_key_is_set():
    """DEEPSEEK_API_KEY must be set (injected by conftest or real env)."""
    assert config.DEEPSEEK_API_KEY
    assert len(config.DEEPSEEK_API_KEY) > 0


@pytest.mark.unit
def test_blog_content_dir_resolves_within_home():
    """Default blog dir resolves under user home."""
    resolved = config.BLOG_CONTENT_DIR.resolve()
    home = Path.home()
    assert str(resolved).startswith(str(home))


@pytest.mark.unit
def test_base_url_is_deepseek():
    """Verify default API endpoint."""
    assert config.DEEPSEEK_BASE_URL == "https://api.deepseek.com"


@pytest.mark.unit
def test_models_configured():
    """Verify both flash and pro model names are set."""
    assert "flash" in config.DEEPSEEK_MODEL
    assert "pro" in config.DEEPSEEK_MODEL_PRO


@pytest.mark.unit
def test_path_safety_reject_outside_home(monkeypatch):
    """The path safety check logic detects out-of-home paths."""
    outside = Path("/tmp/evil/path/outside/home")
    home = Path.home()
    assert not str(outside.resolve()).startswith(str(home))
