"""Tests for event clustering, stable identity, and cross-week revision."""
from schema import EvidenceDossier, SourceRecord
from tracking.events import (
    actor_key,
    assign_event_identity,
    claims_changed,
    detect_reversals,
    event_id_for,
    event_status_from,
    same_event,
    summarize_story_line,
    track_changes,
)


class TestActorKey:
    def test_leading_characters(self):
        assert actor_key("尊界刹车踏板断裂") == "尊界"

    def test_bracketed_tag_wins(self):
        assert actor_key("【尊界汽车】发布通报") == "尊界汽车"

    def test_case_folded(self):
        assert actor_key("ABC事件") == actor_key("abc事件")


class TestSameEvent:
    def test_same_event_across_rephrasings(self):
        """The three titles the user cited as one event observed three times."""
        assert same_event("尊界刹车踏板断裂", "尊界回应制动踏板问题")
        assert same_event("尊界刹车踏板断裂", "尊界免费升级踏板结构")

    def test_same_actor_different_event_is_not_merged(self):
        """Merging two events invents a relationship; the rule stays conservative."""
        assert not same_event("小米汽车定价策略", "小米机器人发布会")

    def test_different_actor(self):
        assert not same_event("尊界刹车踏板断裂", "烟草局人士称细烟带动女性烟民")

    def test_identical_titles(self):
        assert same_event("同一标题", "同一标题")

    def test_empty(self):
        assert not same_event("", "x")


class TestAssignEventIdentity:
    def test_clusters_rephrasings_into_one_event(self):
        raw = [
            {"title": "尊界刹车踏板断裂", "summary": "a", "sourcePlatform": "微博热搜"},
            {"title": "尊界回应制动踏板问题", "summary": "b", "sourcePlatform": "微博热搜"},
            {"title": "尊界免费升级踏板结构", "summary": "c", "sourcePlatform": "知乎热榜"},
        ]
        events = assign_event_identity(raw, observed_at="2026-10-11")
        assert len(events) == 1
        assert len(events[0]["topicAliases"]) == 3
        assert events[0]["eventStatus"] == "新发生"

    def test_id_is_stable_across_weeks(self):
        raw = [
            {"title": "尊界刹车踏板断裂", "summary": "a"},
            {"title": "尊界回应制动踏板问题", "summary": "b"},
        ]
        first = assign_event_identity(raw, observed_at="2026-10-11")
        second = assign_event_identity(raw, observed_at="2026-10-18")
        assert first[0]["eventId"] == second[0]["eventId"]

    def test_known_event_becomes_ongoing(self):
        raw = [{"title": "尊界刹车踏板断裂", "summary": "a"}]
        first = assign_event_identity(raw, observed_at="2026-10-11")
        known = {first[0]["eventId"]}
        second = assign_event_identity(raw, observed_at="2026-10-18", known_event_ids=known)
        assert second[0]["eventStatus"] == "持续发展"

    def test_unrelated_topics_stay_separate(self):
        raw = [
            {"title": "尊界刹车踏板断裂", "summary": "a"},
            {"title": "烟草局人士称细烟带动女性烟民", "summary": "b"},
        ]
        assert len(assign_event_identity(raw)) == 2

    def test_skips_blank_titles(self):
        assert assign_event_identity([{"title": "  "}, {"title": "有效标题"}]) != []

    def test_tolerates_non_dict_entries(self):
        events = assign_event_identity(["not a dict", {"title": "有效标题"}])
        assert len(events) == 1

    def test_platform_is_recorded(self):
        raw = [{"title": "尊界刹车踏板断裂", "summary": "a", "sourcePlatform": "微博热搜"}]
        assert "微博热搜" in assign_event_identity(raw)[0]["sourcePlatform"]


class TestEventIdFor:
    def test_stable_for_same_inputs(self):
        assert event_id_for("尊界", "踏板") == event_id_for("尊界", "踏板")

    def test_differs_by_topic(self):
        assert event_id_for("尊界", "踏板") != event_id_for("尊界", "座椅")


def _dossier(event_id="e1", title="尊界刹车踏板断裂", urls=(), conflicts=()):
    return EvidenceDossier(
        eventId=event_id,
        title=title,
        conflicts=list(conflicts),
        sources=[SourceRecord(sourceId=f"s{i}", url=u) for i, u in enumerate(urls)],
    )


class TestDetectReversals:
    def test_no_prior_means_no_reversal(self):
        assert detect_reversals(_dossier(), None) == []

    def test_new_conflict_is_a_reversal(self):
        prior = _dossier(conflicts=[])
        current = _dossier(conflicts=["甲与乙数值不一致"])
        notes = detect_reversals(current, prior)
        assert any("分歧" in n for n in notes)

    def test_repeated_conflict_is_not_new(self):
        prior = _dossier(conflicts=["甲与乙数值不一致"])
        current = _dossier(conflicts=["甲与乙数值不一致"])
        assert detect_reversals(current, prior) == []

    def test_retraction_language_in_new_source(self):
        current = _dossier(urls=["https://new.com/1"])
        current.sources[0].title = "官方辟谣：相关说法不实"
        notes = detect_reversals(current, _dossier(urls=["https://old.com/1"]))
        assert any("反转" in n for n in notes)

    def test_known_url_is_not_new(self):
        prior = _dossier(urls=["https://same.com/1"])
        current = _dossier(urls=["https://same.com/1"])
        current.sources[0].title = "官方辟谣"
        assert detect_reversals(current, prior) == []


class TestEventStatus:
    def test_reversal_wins(self):
        assert event_status_from(_dossier(), _dossier(), ["x"]) == "出现反转"

    def test_first_sighting(self):
        assert event_status_from(_dossier(), None, []) == "新发生"

    def test_no_sources_is_pending(self):
        empty = EvidenceDossier(eventId="e1", title="t")
        assert event_status_from(empty, _dossier(), []) == "待观察"

    def test_ongoing(self):
        dossier = _dossier(urls=["https://a.com/1"])
        assert event_status_from(dossier, dossier, []) == "持续发展"


class TestTrackChanges:
    def test_annotations_and_notes(self):
        current = _dossier(event_id="e1")
        history = {}
        annotations, notes = track_changes([current], history)
        assert annotations[0]["isNew"] is True
        assert notes == []

    def test_reversal_produces_note(self):
        prior = _dossier(conflicts=[])
        current = _dossier(conflicts=["甲与乙数值不一致"])
        annotations, notes = track_changes([current], {"e1": prior})
        assert notes and "变化" in notes[0]
        assert annotations[0]["eventStatus"] == "出现反转"


class TestClaimsChanged:
    def test_detects_material_change(self):
        from evidence.claims import extract_claims

        prior = extract_claims({"materialContent": "该企业发布了召回公告。"}, event_id="e1")
        current = extract_claims({"materialContent": "该企业撤回了此前的召回公告。"}, event_id="e1")
        assert claims_changed(prior, current)

    def test_unchanged_yields_nothing(self):
        from evidence.claims import extract_claims

        claims = extract_claims({"materialContent": "该企业发布了召回公告。"}, event_id="e1")
        assert claims_changed(claims, claims) == []


class TestSummarizeStoryLine:
    def test_renders_status(self):
        line = summarize_story_line([{"title": "事件", "eventStatus": "出现反转"}])
        assert "事件" in line and "出现反转" in line

    def test_empty(self):
        assert summarize_story_line([]) == ""
