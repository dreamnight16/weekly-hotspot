"""Test quantitative module (post-MVP stub)."""
import pytest
from empirical.quantitative import quantitative_context


class TestQuantitativeContext:
    def test_returns_dict_for_valid_title(self):
        result = quantitative_context("测试事件标题")
        assert isinstance(result, dict)
        assert result["status"] == "stub"
        assert "gdelt" in result
        assert "sentiment" in result
        assert "changePoints" in result

    def test_returns_none_for_empty_title(self):
        assert quantitative_context("") is None

    def test_returns_none_for_none_title(self):
        assert quantitative_context(None) is None

    def test_returns_none_for_whitespace_only(self):
        assert quantitative_context("   ") is None

    def test_not_a_string(self):
        assert quantitative_context(123) is None

    def test_includes_dialectical_context(self):
        result = quantitative_context("事件", dialectical_context={"phase": "phase3", "confidence": "HIGH"})
        assert "dialecticalContext" in result
        assert result["dialecticalContext"]["phase"] == "phase3"
