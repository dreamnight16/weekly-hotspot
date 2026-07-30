"""Test Empirical Layer: Adversarial Review (Devil's Advocate)."""
import json
import pytest
from unittest.mock import MagicMock

from empirical.adversary import adversarial_review, format_dialectical_output


class TestFormatDialecticalOutput:
    def test_formats_unfolding_result(self):
        unfolding_result = {
            "phaseSummary": "辩证展开总述",
            "unityOfOpposites": {
                "identity": "同一性分析",
                "struggle": "斗争性分析",
                "particularity": "特殊性分析",
                "universality": "普遍性分析",
            },
            "quantityQuality": {
                "currentPhase": "量变积累",
                "quantitativeDirection": "上升趋势",
                "measure": "度量关节线",
                "newQuality": "新质量",
                "oldQualityNegated": "旧质量",
            },
            "negationOfNegation": {
                "oldThing": "旧事物",
                "firstNegation": "第一次否定",
                "internalNegation": "内部否定",
                "direction": "螺旋上升",
                "stageCharacteristics": "当前阶段",
            },
        }
        text = format_dialectical_output(unfolding_result)
        assert "辩证展开总述" in text
        assert "同一性分析" in text
        assert "量变积累" in text
        assert "螺旋上升" in text

    def test_handles_empty_result(self):
        text = format_dialectical_output({})
        assert text is not None
        assert isinstance(text, str)

    def test_json_serializable(self):
        """Verify the formatted output is valid JSON serializable."""
        result = {"key": "value", "nested": {"a": 1}}
        text = format_dialectical_output(result)
        # Should not raise
        parsed = json.loads(json.dumps({"text": text}))
        assert "text" in parsed


class TestAdversarialReview:
    def test_returns_none_on_none_client(self):
        """Test graceful degradation when client is None."""
        result = adversarial_review(client=None, unfolding_result={"test": True})
        assert result is None

    def test_returns_none_on_empty_unfolding(self):
        """Test graceful degradation with empty unfolding result."""
        mock_client = MagicMock()
        result = adversarial_review(mock_client, unfolding_result={})
        assert result is None

    def test_returns_none_on_client_error(self):
        """Test graceful degradation when LLM call raises an exception."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = RuntimeError("API timeout")
        result = adversarial_review(
            mock_client,
            unfolding_result={"phaseSummary": "test", "unityOfOpposites": {"identity": "x", "struggle": "y", "particularity": "z", "universality": "w"}}
        )
        assert result is None

    def test_returns_none_on_invalid_json_response(self):
        """Test graceful degradation when LLM returns invalid JSON."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = json.JSONDecodeError("bad json", "{", 0)
        result = adversarial_review(
            mock_client,
            unfolding_result={"phaseSummary": "test"}
        )
        assert result is None

    def test_calls_chat_json_with_correct_prompt(self):
        """Test that the LLM is called with formatted adversarial prompt."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "adversarySummary": "整体评估",
            "challenges": [
                {
                    "challengeId": "da-1",
                    "targetClaim": "目标断言",
                    "claimLocation": "quantityQuality",
                    "weaknessType": "证据链最薄",
                    "weaknessExplanation": "解释",
                    "counterEvidence": [
                        {
                            "evidenceType": "被忽略的事实",
                            "description": "证据描述",
                            "sourceHint": "来源提示",
                            "impact": "显著削弱",
                        }
                    ],
                    "conflictingLogicalSteps": [],
                    "alternativeInterpretations": [],
                    "resilienceAssessment": {
                        "resilience": "弱",
                        "requiredCorrection": "修正",
                        "conditionsForOriginalToStand": "条件",
                    },
                }
            ],
            "noWeakClaimsFound": False,
            "noWeakClaimsRationale": "",
        }
        unfolding_result = {
            "phaseSummary": "辩证总述",
            "events": [{"id": "evt-1", "title": "测试事件", "summary": "概述"}],
            "dialecticalConfidence": "MEDIUM",
            "unityOfOpposites": {
                "identity": "同一性", "struggle": "斗争性",
                "particularity": "特殊性", "universality": "普遍性",
            },
            "quantityQuality": {
                "currentPhase": "量变积累", "quantitativeDirection": "趋势",
                "measure": "度量", "newQuality": "新质", "oldQualityNegated": "旧质",
            },
            "negationOfNegation": {
                "oldThing": "旧事物", "firstNegation": "第一次否定",
                "internalNegation": "内部否定", "direction": "螺旋上升",
                "stageCharacteristics": "特征",
            },
        }
        result = adversarial_review(mock_client, unfolding_result)

        # Verify chat_json was called
        mock_client.chat_json.assert_called_once()
        call_args = mock_client.chat_json.call_args[0][0]  # messages
        user_content = call_args[1]["content"]
        assert "辩证总述" in user_content
        assert "同一性" in user_content
        assert "量变积累" in user_content

        # Verify result structure
        assert result is not None
        assert "adversarySummary" in result
        assert "challenges" in result
        assert len(result["challenges"]) == 1
        assert result["challenges"][0]["challengeId"] == "da-1"

    def test_handles_no_weak_claims_found(self):
        """Test when adversary finds no weak claims."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "adversarySummary": "分析扎实，无明显弱断言",
            "challenges": [],
            "noWeakClaimsFound": True,
            "noWeakClaimsRationale": "各断言均有充分证据支撑",
        }
        result = adversarial_review(
            mock_client,
            unfolding_result={
                "phaseSummary": "test",
                "unityOfOpposites": {"identity": "x", "struggle": "y", "particularity": "z", "universality": "w"},
            }
        )
        assert result is not None
        assert result["noWeakClaimsFound"] is True
        assert result["challenges"] == []

    def test_defaults_applied_to_missing_fields(self):
        """Test defaults applied when LLM omits fields from response."""
        mock_client = MagicMock()
        mock_client.chat_json.return_value = {
            "adversarySummary": "评估",
            # challenges missing
            # noWeakClaimsFound missing
        }
        result = adversarial_review(
            mock_client,
            unfolding_result={
                "phaseSummary": "test",
                "unityOfOpposites": {"identity": "x", "struggle": "y", "particularity": "z", "universality": "w"},
            }
        )
        assert result is not None
        assert "challenges" in result
        assert result["challenges"] == []
        assert "noWeakClaimsFound" in result
        assert result["noWeakClaimsFound"] is False

    def test_graceful_degradation_on_type_error(self):
        """Test graceful degradation when chat_json call fails with TypeError."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = TypeError("unexpected keyword argument")
        result = adversarial_review(
            mock_client,
            unfolding_result={"phaseSummary": "test"}
        )
        assert result is None

    def test_graceful_degradation_on_connection_error(self):
        """Test graceful degradation on connection errors."""
        mock_client = MagicMock()
        mock_client.chat_json.side_effect = ConnectionError("Connection refused")
        result = adversarial_review(
            mock_client,
            unfolding_result={"phaseSummary": "test"}
        )
        assert result is None

    @pytest.mark.integration
    def test_adversarial_review_integration(self):
        """Integration test: requires DEEPSEEK_API_KEY.

        Tests the full pipeline: unfolding -> adversarial review.
        """
        import os

        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key or "dummy" in api_key.lower() or "pytest" in api_key.lower():
            pytest.skip("DEEPSEEK_API_KEY not set or is a dummy key")
        from chinese_scraper_utils import DeepSeekClient
        from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL_DIALECTICAL, DEEPSEEK_MODEL_EMPIRICAL
        from dialectical.unfolding import unfold_dialectics

        # Use dialectical model for unfolding
        dialectical_client = DeepSeekClient(
            DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_DIALECTICAL, thinking=True
        )
        event = {
            "id": "evt-1",
            "title": "AI行业价格战持续升温",
            "materialContent": "资本通过低价策略抢占市场份额，小企业面临生存压力",
            "summary": "多家AI公司宣布大幅下调服务价格，部分降价幅度超过90%",
        }
        search_results = [
            {
                "title": "AI价格战愈演愈烈",
                "url": "https://example.com/ai-price-war",
                "snippet": "多家企业加入价格战",
            }
        ]

        # Step 1: Unfolding
        unfolding_result = unfold_dialectics(
            dialectical_client, event, search_results, idx=1
        )
        assert "unityOfOpposites" in unfolding_result
        assert "quantityQuality" in unfolding_result
        assert "negationOfNegation" in unfolding_result

        # Step 2: Adversarial review with a different client instance
        empirical_client = DeepSeekClient(
            DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL_EMPIRICAL, thinking=False
        )
        adversary_result = adversarial_review(empirical_client, unfolding_result)
        assert adversary_result is not None, "Adversarial review should return a result"
        assert "adversarySummary" in adversary_result
        assert "challenges" in adversary_result
        assert isinstance(adversary_result["challenges"], list)
        assert "noWeakClaimsFound" in adversary_result
