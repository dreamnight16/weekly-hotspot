from typing import Any, Literal, Optional, Self
from pydantic import BaseModel, Field, model_validator

from config import get_logger

_logger = get_logger("schema")


# ---- Pipeline intermediate models ----

class RawEvent(BaseModel):
    """Phase 0 输出：原始抓取事件"""
    title: str
    summary: str


class CensoredEvent(BaseModel):
    """Phase 1 输出：通过政审的事件"""
    title: str
    summary: str


class ScoredEvent(BaseModel):
    """Phase 2 输出：评分后入选的事件"""
    title: str
    summary: str
    impactScore: int = Field(ge=1, le=5)
    infoGainScore: int = Field(ge=1, le=5)


# ---- Enum value fixup maps ----

# Maps known AI mistakes to correct enum values
_CURRENT_STATE_FIXUPS: dict[str, str] = {
    "外部对抗激化，内部隐性积累": "对抗激化",
}
_DIRECTION_FIXUPS: dict[str, str] = {
    "隐性积累": "缓和",  # AI confuses currentState enum for direction
}
_AUTHENTICITY_FIXUPS: dict[str, str] = {}
_SOURCE_TYPE_FIXUPS: dict[str, str] = {}
_CLASS_BIAS_FIXUPS: dict[str, str] = {}
_TYPE_FIXUPS: dict[str, str] = {}


def _fuzzy_fix_enum(value: str, valid_values: frozenset[str], fixups: dict[str, str], default: str) -> str:
    """Try to map a non-enum value to a valid one.  Strips whitespace first."""
    if not isinstance(value, str):
        return default
    v = value.strip()
    if v in valid_values:
        return v
    if v in fixups:
        return fixups[v]
    # Substring match: if the valid value appears anywhere in the AI output, use it
    for valid in valid_values:
        if valid in v:
            _logger.warning("  [sanitize] enum fixup: %r -> %r (substring match)", v, valid)
            return valid
    _logger.warning("  [sanitize] enum default: %r -> %r (no match in %s)", v, default, sorted(valid_values))
    return default


# ---- Output models ----


class ClassAnalysis(BaseModel):
    classNature: str = ""
    contradiction: str = ""
    historicalContext: str = ""


class TimelineNode(BaseModel):
    id: str
    time: str = ""  # default for AI that omits this field
    title: str
    description: str
    evidenceRefs: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("time"):
                data["time"] = "未知"
                _logger.debug("  [sanitize] timeline node %s missing 'time', set to '未知'", data.get("id", "?"))
        return data


class EvidenceNode(BaseModel):
    id: str
    sourceType: Literal["官媒", "社交平台", "一手材料", "其他"]
    sourceName: str
    sourceUrl: Optional[str] = None
    content: str
    authenticity: Literal["真实", "存疑", "不实", "待验证"]
    aiReason: str
    classBias: Literal["无产阶级立场", "资产阶级立场", "小资产阶级立场", "帝国主义话语", "待判断"] = "待判断"

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        # Fix classBias: AI often writes explanation text instead of enum value
        if "classBias" in data:
            valid = frozenset({"无产阶级立场", "资产阶级立场", "小资产阶级立场", "帝国主义话语", "待判断"})
            data["classBias"] = _fuzzy_fix_enum(
                str(data["classBias"]), valid, _CLASS_BIAS_FIXUPS, "待判断"
            )
        # Fix sourceType
        if "sourceType" in data:
            valid_st = frozenset({"官媒", "社交平台", "一手材料", "其他"})
            data["sourceType"] = _fuzzy_fix_enum(
                str(data["sourceType"]), valid_st, _SOURCE_TYPE_FIXUPS, "其他"
            )
        # Fix authenticity
        if "authenticity" in data:
            valid_auth = frozenset({"真实", "存疑", "不实", "待验证"})
            data["authenticity"] = _fuzzy_fix_enum(
                str(data["authenticity"]), valid_auth, _AUTHENTICITY_FIXUPS, "待验证"
            )
        return data


class Edge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    type: Literal["因果", "关联", "矛盾"]
    description: str

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def _sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "type" in data:
            valid_types = frozenset({"因果", "关联", "矛盾"})
            data["type"] = _fuzzy_fix_enum(
                str(data["type"]), valid_types, _TYPE_FIXUPS, "关联"
            )
        return data


# ---- Phase 4: Synthesis models ----


class CrossCuttingTheme(BaseModel):
    name: str = Field(max_length=80)
    description: str = Field(max_length=500)
    relatedEventIds: list[str] = Field(default_factory=list)
    significance: str = Field(max_length=500)


class IdentifiedTrend(BaseModel):
    name: str = Field(max_length=80)
    description: str = Field(max_length=500)
    direction: Literal["上升", "下降", "转型", "激化", "缓和"]
    evidenceEventIds: list[str] = Field(default_factory=list)


class ContradictionInMotion(BaseModel):
    contradiction: str = Field(max_length=300)
    opposingForces: str = Field(max_length=500)
    eventsInvolved: list[str] = Field(default_factory=list)
    currentState: Literal["对抗激化", "暂时缓和", "向新形态转化", "隐性积累"]
    outlook: str = Field(max_length=500)


class WeeklySynthesis(BaseModel):
    weeklyNarrative: str = Field(max_length=2000)
    crossCuttingThemes: list[CrossCuttingTheme] = Field(default_factory=list, max_length=5)
    trends: list[IdentifiedTrend] = Field(default_factory=list, max_length=5)
    contradictionsInMotion: list[ContradictionInMotion] = Field(default_factory=list, max_length=5)
    globalAssessment: str = Field(default="", max_length=1000)
    dataGaps: list[str] = Field(default_factory=list, max_length=5)

    @model_validator(mode="before")
    @classmethod
    def _sanitize_synthesis(cls, data: Any) -> Any:
        """Fix common AI-generated enum errors in synthesis output."""
        if not isinstance(data, dict):
            return data

        # Fix direction enum in trends
        valid_directions = frozenset({"上升", "下降", "转型", "激化", "缓和"})
        for i, trend in enumerate(data.get("trends", []) or []):
            if isinstance(trend, dict) and "direction" in trend:
                trend["direction"] = _fuzzy_fix_enum(
                    str(trend["direction"]), valid_directions, _DIRECTION_FIXUPS, "转型"
                )

        # Fix currentState enum in contradictionsInMotion
        valid_states = frozenset({"对抗激化", "暂时缓和", "向新形态转化", "隐性积累"})
        for i, c in enumerate(data.get("contradictionsInMotion", []) or []):
            if isinstance(c, dict) and "currentState" in c:
                c["currentState"] = _fuzzy_fix_enum(
                    str(c["currentState"]), valid_states, _CURRENT_STATE_FIXUPS, "隐性积累"
                )

        return data

    @model_validator(mode="after")
    def _validate_synthesis_refs(self) -> Self:
        # Drop items with empty required refs (AI often generates hollow items)
        self.crossCuttingThemes = [t for t in self.crossCuttingThemes if t.relatedEventIds]
        self.trends = [t for t in self.trends if t.evidenceEventIds]
        self.contradictionsInMotion = [c for c in self.contradictionsInMotion if c.eventsInvolved]

        return self


class Event(BaseModel):
    id: str = Field(max_length=100)
    title: str = Field(max_length=500)
    impactScore: int = Field(ge=1, le=5)
    infoGainScore: int = Field(ge=1, le=5)
    summary: str = Field(max_length=5000)
    classAnalysis: ClassAnalysis = Field(default_factory=ClassAnalysis)
    dialecticalSummary: str = Field(default="", max_length=200)
    timeline: list[TimelineNode] = Field(default_factory=list, max_length=50)
    evidence: list[EvidenceNode] = Field(default_factory=list, max_length=100)
    edges: list[Edge] = Field(default_factory=list, max_length=200)

    @model_validator(mode="before")
    @classmethod
    def _sanitize_event(cls, data: Any) -> Any:
        """Fix common AI-generated data issues before strict validation."""
        if not isinstance(data, dict):
            return data

        # Clamp scores to valid range
        for field in ("impactScore", "infoGainScore"):
            if field in data and isinstance(data[field], (int, float)):
                val = data[field]
                if val < 1:
                    _logger.warning("  [sanitize] evt %s %s=%s clamped to 1", data.get("id", "?"), field, val)
                    data[field] = 1
                elif val > 5:
                    _logger.warning("  [sanitize] evt %s %s=%s clamped to 5", data.get("id", "?"), field, val)
                    data[field] = 5

        # Ensure dialecticalSummary is a string and not too long
        if "dialecticalSummary" in data and not isinstance(data.get("dialecticalSummary"), str):
            data["dialecticalSummary"] = str(data.get("dialecticalSummary", ""))

        # Ensure classAnalysis has all required sub-fields
        if "classAnalysis" in data:
            if not isinstance(data["classAnalysis"], dict):
                data["classAnalysis"] = {}
            for sub in ("classNature", "contradiction", "historicalContext"):
                data["classAnalysis"].setdefault(sub, "")

        # Fix edge cross-references: drop edges whose from/to don't match any
        # known timeline/evidence id
        timeline_data = data.get("timeline", [])
        evidence_data = data.get("evidence", [])
        valid_ids = set()
        for t in timeline_data:
            if isinstance(t, dict) and "id" in t:
                valid_ids.add(t["id"])
        for e in evidence_data:
            if isinstance(e, dict) and "id" in e:
                valid_ids.add(e["id"])

        edges = data.get("edges", [])
        fixed_edges = []
        for i, edge in enumerate(edges or []):
            if not isinstance(edge, dict):
                continue
            from_id = edge.get("from", "")
            to_id = edge.get("to", "")
            from_ok = from_id in valid_ids
            to_ok = to_id in valid_ids
            if from_ok and to_ok:
                fixed_edges.append(edge)
            else:
                missing = []
                if not from_ok:
                    missing.append(f"from='{from_id}'")
                if not to_ok:
                    missing.append(f"to='{to_id}'")
                _logger.warning(
                    "  [sanitize] evt %s: drop Edge[%d] (%s) — reference(s) %s not found in timeline/evidence",
                    data.get("id", "?"), i, edge.get("description", "")[:40], ", ".join(missing),
                )
        if len(fixed_edges) < len(edges):
            data["edges"] = fixed_edges

        # Fix timeline evidenceRefs: drop references to non-existent evidence
        if evidence_data and timeline_data:
            ev_ids = {e["id"] for e in evidence_data if isinstance(e, dict) and "id" in e}
            for i, t in enumerate(timeline_data):
                if not isinstance(t, dict):
                    continue
                refs = t.get("evidenceRefs", [])
                if refs:
                    clean_refs = [r for r in refs if r in ev_ids]
                    if len(clean_refs) < len(refs):
                        dropped = set(refs) - set(clean_refs)
                        _logger.warning(
                            "  [sanitize] evt %s timeline[%d]: drop invalid evidenceRefs %s",
                            data.get("id", "?"), i, sorted(dropped),
                        )
                    t["evidenceRefs"] = clean_refs

        return data

    @model_validator(mode="after")
    def _validate_cross_ids(self) -> Self:
        timeline_ids = {t.id for t in self.timeline}
        evidence_ids = {e.id for e in self.evidence}
        valid_refs = timeline_ids | evidence_ids

        invalid_edges = []
        for i, edge in enumerate(self.edges):
            if edge.from_ not in valid_refs or edge.to not in valid_refs:
                invalid_edges.append(i)

        if invalid_edges:
            _logger.error(
                "Edge cross-ref validation failed for %s: edges %s still have invalid refs after sanitization",
                self.id, invalid_edges,
            )
            self.edges = [e for i, e in enumerate(self.edges) if i not in invalid_edges]

        for node in self.timeline:
            clean_refs = [r for r in node.evidenceRefs if r in evidence_ids]
            if len(clean_refs) != len(node.evidenceRefs):
                _logger.warning(
                    "Timeline %s evidenceRefs stripped: %s -> %s",
                    node.id, node.evidenceRefs, clean_refs,
                )
                node.evidenceRefs = clean_refs

        return self


class WeeklyIssue(BaseModel):
    id: str
    weekStart: str
    weekEnd: str
    events: list[Event] = Field(default_factory=list)
    synthesis: WeeklySynthesis | None = Field(default=None)

    @model_validator(mode="after")
    def _validate_synthesis_event_ids(self) -> Self:
        if self.synthesis is None:
            return self

        event_ids = {e.id for e in self.events}

        # Sanitize crossCuttingThemes: drop invalid event id references
        for theme in self.synthesis.crossCuttingThemes:
            clean_refs = [eid for eid in theme.relatedEventIds if eid in event_ids]
            if len(clean_refs) != len(theme.relatedEventIds):
                _logger.warning(
                    "  [sanitize] synthesis theme '%s': dropped invalid event refs %s",
                    theme.name,
                    sorted(set(theme.relatedEventIds) - set(clean_refs)),
                )
                theme.relatedEventIds = clean_refs

        # Sanitize trends
        for trend in self.synthesis.trends:
            clean_refs = [eid for eid in trend.evidenceEventIds if eid in event_ids]
            if len(clean_refs) != len(trend.evidenceEventIds):
                _logger.warning(
                    "  [sanitize] synthesis trend '%s': dropped invalid event refs %s",
                    trend.name,
                    sorted(set(trend.evidenceEventIds) - set(clean_refs)),
                )
                trend.evidenceEventIds = clean_refs

        # Sanitize contradictionsInMotion
        for c in self.synthesis.contradictionsInMotion:
            clean_refs = [eid for eid in c.eventsInvolved if eid in event_ids]
            if len(clean_refs) != len(c.eventsInvolved):
                _logger.warning(
                    "  [sanitize] synthesis contradiction: dropped invalid event refs %s",
                    sorted(set(c.eventsInvolved) - set(clean_refs)),
                )
                c.eventsInvolved = clean_refs

        return self
