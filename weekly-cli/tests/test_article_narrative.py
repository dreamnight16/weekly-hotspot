"""Tests for the constrained LLM narrative path."""
from unittest.mock import MagicMock

import pytest

from narrative.article import (
    assemble_article,
    build_article_context,
    build_claim_ledger,
    gate_note,
    generate_narrative_article,
)
from schema import (
    EvidenceDossier,
    IssueMetadata,
    PhenomenonGrasping,
    PublicationGate,
    SelectedEvent,
    SourceRecord,
    WeeklyIssue,
)


def _issue(**kwargs):
    event = SelectedEvent(
        id="e1", title="尊界通报刹车踏板断裂", summary="车企发布说明",
        sourceUrl="https://example.com/a", materialContent="召回成本压力",
    )
    defaults = dict(
        id="2026-W41",
        weekStart="2026-10-05",
        weekEnd="2026-10-11",
        events=[event],
        phase1=PhenomenonGrasping(phaseSummary="本周总述"),
        metadata=IssueMetadata(
            modelVersions={"dialectical": "m"},
            analysisDate="2026-10-12",
            evidenceCutoff="2026-10-12T00:00:00+00:00",
            promptVersion="abcdef123456",
        ),
    )
    defaults.update(kwargs)
    return WeeklyIssue(**defaults)


class TestBuildClaimLedger:
    def test_empty_ledger_forbids_all_assertions(self):
        text = build_claim_ledger({})
        assert "不得作出任何分析性断言" in text

    def test_renders_type_and_decision(self):
        from evidence.claims import extract_claims

        claims = extract_claims(
            {"materialContent": "车企希望通过主动通报控制舆论。"}, event_id="e1"
        )
        text = build_claim_ledger({"e1": claims})
        assert "假说" in text
        assert "须按改写后的表述写" in text

    def test_event_without_claims_is_labelled(self):
        assert "未抽取到断言" in build_claim_ledger({"e1": []})


class TestGateNote:
    def test_none_gate(self):
        assert gate_note(None) == ""

    def test_degrade_note_forbids_conclusions(self):
        note = gate_note(PublicationGate(decision="DEGRADE"))
        assert "降级发布" in note
        assert "不要给出确定性的分析结论" in note

    def test_block_note_restricts_to_facts(self):
        note = gate_note(PublicationGate(decision="BLOCK"))
        assert "不得作出任何分析性结论" in note

    def test_allow_note(self):
        assert "正常发布" in gate_note(PublicationGate(decision="ALLOW"))


class TestBuildArticleContext:
    def test_includes_events_and_ledger(self):
        context = build_article_context(_issue(), {"e1": []})
        assert "尊界通报刹车踏板断裂" in context
        assert "断言清单" in context

    def test_includes_sources_and_conflicts(self):
        dossier = EvidenceDossier(
            eventId="e1",
            title="尊界",
            conflicts=["甲与乙数值不一致"],
            sources=[SourceRecord(sourceId="s1", title="通报", content="内容")],
        )
        context = build_article_context(_issue(), {"e1": []}, [dossier])
        assert "s1" in context
        assert "甲与乙数值不一致" in context

    def test_includes_revision_log(self):
        from schema import RevisionRecord

        issue = _issue(revisionLog=[RevisionRecord(path="materialContent", action="REWRITE", reason="未加限定")])
        context = build_article_context(issue, {"e1": []})
        assert "已修订的判断" in context
        assert "REWRITE" in context

    def test_includes_story_notes(self):
        context = build_article_context(
            _issue(), {"e1": []}, story_notes=["《事件》出现反转"]
        )
        assert "必须说明为什么改变" in context
        assert "出现反转" in context

    def test_no_story_notes_section_when_empty(self):
        assert "事件追踪" not in build_article_context(_issue(), {"e1": []})


class TestGenerateNarrativeArticle:
    def test_returns_body_on_success(self):
        client = MagicMock()
        client.chat.return_value = "## 一、现象\n\n正文内容。"
        body = generate_narrative_article(client, _issue(), "context")
        assert body.startswith("## 一、现象")

    def test_strips_stray_frontmatter(self):
        client = MagicMock()
        client.chat.return_value = "---\ntitle: x\n---\n\n## 正文"
        body = generate_narrative_article(client, _issue(), "context")
        assert body == "## 正文"

    def test_returns_none_on_client_failure(self):
        client = MagicMock()
        client.chat.side_effect = RuntimeError("api down")
        assert generate_narrative_article(client, _issue(), "context") is None

    def test_returns_none_on_empty_response(self):
        client = MagicMock()
        client.chat.return_value = "   "
        assert generate_narrative_article(client, _issue(), "context") is None


class TestAssembleArticle:
    def test_wraps_body_with_frontmatter(self):
        markdown = assemble_article(_issue(), "## 正文内容")
        assert markdown.startswith("---")
        assert "## 正文内容" in markdown
        assert "格物" in markdown

    def test_discloses_provenance(self):
        markdown = assemble_article(_issue(), "正文")
        assert "分析日期" in markdown
        assert "提示词版本" in markdown
        assert "证据截止" in markdown

    def test_degrades_are_announced_to_the_reader(self):
        issue = _issue(publicationGate=PublicationGate(decision="DEGRADE"))
        markdown = assemble_article(issue, "正文")
        assert "降级发布" in markdown

    def test_blocked_issue_says_so(self):
        issue = _issue(publicationGate=PublicationGate(decision="BLOCK"))
        markdown = assemble_article(issue, "正文")
        assert "停止发布" in markdown

    def test_allowed_issue_has_no_warning(self):
        issue = _issue(publicationGate=PublicationGate(decision="ALLOW"))
        markdown = assemble_article(issue, "正文")
        assert "降级发布" not in markdown
        assert "停止发布" not in markdown
