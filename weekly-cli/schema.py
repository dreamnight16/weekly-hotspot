from typing import Literal, Optional, Self
from pydantic import BaseModel, Field, model_validator


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


# ---- Output models ----


class ClassAnalysis(BaseModel):
    classNature: str = ""
    contradiction: str = ""
    historicalContext: str = ""


class TimelineNode(BaseModel):
    id: str
    time: str
    title: str
    description: str
    evidenceRefs: list[str] = Field(default_factory=list)


class EvidenceNode(BaseModel):
    id: str
    sourceType: Literal["官媒", "社交平台", "一手材料", "其他"]
    sourceName: str
    sourceUrl: Optional[str] = None
    content: str
    authenticity: Literal["真实", "存疑", "不实", "待验证"]
    aiReason: str
    classBias: Literal["无产阶级立场", "资产阶级立场", "小资产阶级立场", "帝国主义话语", "待判断"] = "待判断"


class Edge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    type: Literal["因果", "关联", "矛盾"]
    description: str

    model_config = {"populate_by_name": True}


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

    @model_validator(mode="after")
    def _validate_synthesis_refs(self) -> Self:
        for i, theme in enumerate(self.crossCuttingThemes):
            if not theme.relatedEventIds:
                raise ValueError(f"crossCuttingThemes[{i}].relatedEventIds must not be empty")

        for i, trend in enumerate(self.trends):
            if not trend.evidenceEventIds:
                raise ValueError(f"trends[{i}].evidenceEventIds must not be empty")

        for i, c in enumerate(self.contradictionsInMotion):
            if not c.eventsInvolved:
                raise ValueError(f"contradictionsInMotion[{i}].eventsInvolved must not be empty")

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

    @model_validator(mode="after")
    def _validate_cross_ids(self) -> Self:
        timeline_ids = {t.id for t in self.timeline}
        evidence_ids = {e.id for e in self.evidence}
        valid_refs = timeline_ids | evidence_ids

        for i, edge in enumerate(self.edges):
            if edge.from_ not in valid_refs:
                raise ValueError(f"Edge[{i}].from='{edge.from_}' does not reference any timeline/evidence id")
            if edge.to not in valid_refs:
                raise ValueError(f"Edge[{i}].to='{edge.to}' does not reference any timeline/evidence id")

        for i, node in enumerate(self.timeline):
            for j, ref in enumerate(node.evidenceRefs):
                if ref not in evidence_ids:
                    raise ValueError(f"Timeline[{i}].evidenceRefs[{j}]='{ref}' does not reference any evidence id")

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

        for i, theme in enumerate(self.synthesis.crossCuttingThemes):
            for j, eid in enumerate(theme.relatedEventIds):
                if eid not in event_ids:
                    raise ValueError(f"synthesis.crossCuttingThemes[{i}].relatedEventIds[{j}]='{eid}' does not match any event id")

        for i, trend in enumerate(self.synthesis.trends):
            for j, eid in enumerate(trend.evidenceEventIds):
                if eid not in event_ids:
                    raise ValueError(f"synthesis.trends[{i}].evidenceEventIds[{j}]='{eid}' does not match any event id")

        for i, c in enumerate(self.synthesis.contradictionsInMotion):
            for j, eid in enumerate(c.eventsInvolved):
                if eid not in event_ids:
                    raise ValueError(f"synthesis.contradictionsInMotion[{i}].eventsInvolved[{j}]='{eid}' does not match any event id")

        return self
