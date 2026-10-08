"""Tests for source capture, provenance, and independence detection."""
from evidence.sources import (
    build_source_record,
    classify_source_kind,
    content_fingerprint,
    content_similarity,
    dedupe_by_url,
    mark_republications,
    normalize_url,
    parse_page,
)


class TestNormalizeUrl:
    def test_strips_scheme_www_and_trailing_slash(self):
        assert normalize_url("HTTPS://WWW.Example.com/a/") == "example.com/a"

    def test_empty(self):
        assert normalize_url("") == ""


class TestContentFingerprint:
    def test_ignores_whitespace(self):
        assert content_fingerprint("a b c") == content_fingerprint("abc")

    def test_differs_for_different_text(self):
        assert content_fingerprint("abc") != content_fingerprint("abd")

    def test_empty(self):
        assert content_fingerprint("") != ""


class TestContentSimilarity:
    def test_identical_is_one(self):
        assert content_similarity("同样的报道内容", "同样的报道内容") == 1.0

    def test_unrelated_is_low(self):
        assert content_similarity("制动踏板断裂事故", "今天天气很好") < 0.2

    def test_empty_returns_zero(self):
        assert content_similarity("", "abc") == 0.0


class TestParsePage:
    def test_extracts_visible_text(self):
        html = "<html><body><p>第一段</p><p>第二段</p></body></html>"
        text, _, _ = parse_page(html)
        assert "第一段" in text
        assert "第二段" in text

    def test_strips_script_and_style(self):
        html = "<body><script>var x=1;</script><style>.a{}</style><p>正文</p></body>"
        text, _, _ = parse_page(html)
        assert "var x" not in text
        assert ".a{" not in text
        assert "正文" in text

    def test_extracts_published_time_meta(self):
        html = (
            '<head><meta property="article:published_time" content="2026-10-11T08:00:00Z">'
            "</head><body><p>正文</p></body>"
        )
        _, _, published = parse_page(html)
        assert published == "2026-10-11T08:00:00Z"

    def test_extracts_title(self):
        html = "<html><head><title>测试标题</title></head><body><p>x</p></body></html>"
        _, title, _ = parse_page(html)
        assert title == "测试标题"

    def test_malformed_html_does_not_raise(self):
        text, _, _ = parse_page("<p>未闭合<b>标签")
        assert "未闭合" in text


class TestClassifySourceKind:
    def test_government_domain_is_primary(self):
        assert classify_source_kind("https://www.samr.gov.cn/x") == "PRIMARY"

    def test_aggregator_is_republished(self):
        assert classify_source_kind("https://www.sohu.com/a/1") == "REPUBLISHED"

    def test_unknown_domain(self):
        assert classify_source_kind("https://example.com/a") == "UNKNOWN"

    def test_empty(self):
        assert classify_source_kind("") == "UNKNOWN"


class TestBuildSourceRecord:
    def test_uses_snippet_when_no_content(self):
        rec = build_source_record(url="https://e.com/a", snippet="摘要")
        assert rec.fetchStatus == "snippet-only"
        assert rec.contentFingerprint

    def test_fetched_content_sets_status(self):
        rec = build_source_record(
            url="https://e.com/a", content="正文", fetch_status="ok"
        )
        assert rec.fetchStatus == "ok"
        assert rec.content == "正文"

    def test_source_id_is_stable_for_same_url(self):
        a = build_source_record(url="https://e.com/a", snippet="x")
        b = build_source_record(url="https://e.com/a", snippet="y")
        assert a.sourceId == b.sourceId


class TestMarkRepublications:
    def test_identical_content_is_marked_republished(self):
        """Five copies of one wire story are one witness, not five."""
        body = "监管部门今日发布通报，就相关产品问题说明情况并启动调查程序。"
        records = [
            build_source_record(url=f"https://site{i}.com/a", content=body)
            for i in range(4)
        ]
        marked = mark_republications(records)
        assert marked == 3
        assert records[0].kind != "REPUBLISHED"
        assert all(r.kind == "REPUBLISHED" for r in records[1:])

    def test_distinct_content_is_not_marked(self):
        records = [
            build_source_record(url="https://a.com/1", content="监管部门发布通报，启动调查程序。"),
            build_source_record(url="https://b.com/2", content="企业回应称产品符合国家标准要求。"),
        ]
        assert mark_republications(records) == 0

    def test_primary_source_keeps_its_kind(self):
        body = "监管部门发布通报。"
        records = [
            build_source_record(url="https://samr.gov.cn/a", content=body),
            build_source_record(url="https://site.com/a", content=body),
        ]
        mark_republications(records)
        assert records[0].kind == "PRIMARY"


class TestDedupeByUrl:
    def test_keeps_richest_record(self):
        records = [
            build_source_record(url="https://e.com/a", snippet="短"),
            build_source_record(url="https://e.com/a/", content="长内容" * 10),
        ]
        out = dedupe_by_url(records)
        assert len(out) == 1
        assert out[0].content

    def test_drops_records_without_url(self):
        assert dedupe_by_url([build_source_record(url="")]) == []
