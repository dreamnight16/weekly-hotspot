"""Empirical Layer: Non-obvious Connection Discovery & PESTLE Matrix.

Finds hidden connections between events, builds PESTLE interaction matrices,
and performs shortest-path link analysis to reveal the underlying event graph
structure.

Gracefully degrades: returns None on ANY failure so the pipeline continues.
"""
import json
import logging

from chinese_scraper_utils import DeepSeekClient
from prompts import load_prompt

logger = logging.getLogger("weekly.empirical.connections")

CONNECTIONS_PROMPT = load_prompt("empirical/connections")

VALID_DIMENSIONS = frozenset({"P", "E", "S", "T", "L", "E"})

CONFIDENCE_VALUES = frozenset({"可验证", "推测性", "理论性"})

STRENGTH_VALUES = frozenset({"强", "中", "弱"})

PESTLE_LABELS = {
    "P": "Political",
    "E": "Economic",
    "S": "Social",
    "T": "Technological",
    "L": "Legal",
    "E": "Environmental",
}


def _serialize_events(events: list[dict]) -> str:
    """Serialize events list to a JSON string for the prompt."""
    try:
        safe_events = []
        for event in events:
            safe = {}
            for k, v in event.items():
                if isinstance(v, str) and len(v) > 2000:
                    safe[k] = v[:2000] + "...(truncated)"
                elif isinstance(v, list) and len(v) > 30:
                    safe[k] = v[:30]
                else:
                    safe[k] = v
            safe_events.append(safe)
        return json.dumps(safe_events, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return json.dumps(
            [{k: str(v)[:500] for k, v in e.items()} for e in events],
            ensure_ascii=False,
            indent=2,
        )


def _has_minimal_event_data(events: list[dict]) -> bool:
    """Check that the events list has enough content for connection analysis."""
    if not events or not isinstance(events, list):
        return False
    if len(events) < 2:
        return False
    return all(
        isinstance(e, dict) and e.get("title") and isinstance(e["title"], str) and e["title"].strip()
        for e in events
    )


def _sanitize_pestle_dimension(raw: str) -> str:
    """Normalize a PESTLE dimension string to a valid single-letter code."""
    if not isinstance(raw, str):
        return "P"
    v = raw.strip().upper()
    if v in VALID_DIMENSIONS:
        return v
    # Map full names to codes
    full_to_code = {
        "POLITICAL": "P", "POLITIC": "P",
        "ECONOMIC": "E", "ECONOMY": "E",
        "SOCIAL": "S",
        "TECHNOLOGICAL": "T", "TECHNOLOGY": "T", "TECH": "T",
        "LEGAL": "L", "LAW": "L",
        "ENVIRONMENTAL": "E", "ENVIRONMENT": "E", "ECOLOGICAL": "E",
    }
    if v in full_to_code:
        return full_to_code[v]
    return "P"


def _sanitize_connection(conn: dict) -> dict:
    """Sanitize a single connection dict with defaults."""
    raw_confidence = conn.get("confidence")
    sanitized_confidence = "推测性"
    if raw_confidence in CONFIDENCE_VALUES:
        sanitized_confidence = raw_confidence

    return {
        "connectionName": conn.get("connectionName") or "",
        "entityA": conn.get("entityA") or "",
        "entityB": conn.get("entityB") or "",
        "connectionMechanism": conn.get("connectionMechanism") or "",
        "mediatingVariables": (
            conn["mediatingVariables"]
            if isinstance(conn.get("mediatingVariables"), list)
            else []
        ),
        "significance": conn.get("significance") or "",
        "confidence": sanitized_confidence,
        "relatedEventIds": (
            conn["relatedEventIds"]
            if isinstance(conn.get("relatedEventIds"), list)
            else []
        ),
    }


def _sanitize_shortest_path(sp: dict) -> dict:
    """Sanitize a shortest path link dict with defaults."""
    raw_strength = sp.get("pathStrength")
    sanitized_strength = "中" if raw_strength in STRENGTH_VALUES else "中"

    return {
        "sourceEventId": sp.get("sourceEventId") or "",
        "targetEventId": sp.get("targetEventId") or "",
        "pathDescription": sp.get("pathDescription") or "",
        "intermediateNodes": (
            sp["intermediateNodes"]
            if isinstance(sp.get("intermediateNodes"), list)
            else []
        ),
        "pathStrength": sanitized_strength,
        "networkSignificance": sp.get("networkSignificance") or "",
    }


def _sanitize_central_event(ce: dict) -> dict:
    """Sanitize a central event dict with defaults."""
    return {
        "eventId": ce.get("eventId") or "",
        "centralityRank": (
            int(ce["centralityRank"])
            if isinstance(ce.get("centralityRank"), (int, float))
            else 0
        ),
        "rationale": ce.get("rationale") or "",
        "connectedEventIds": (
            ce["connectedEventIds"]
            if isinstance(ce.get("connectedEventIds"), list)
            else []
        ),
    }


def find_connections(
    client: DeepSeekClient | None,
    events: list[dict],
) -> dict | None:
    """Discover non-obvious connections between events and build PESTLE matrix.

    Performs three analyses:
      1. Non-obvious connection discovery (hidden links between events)
      2. PESTLE interaction matrix (Political, Economic, Social, Technological,
         Legal, Environmental dimensions)
      3. Shortest-path link analysis (event graph centrality and paths)

    Args:
        client: A DeepSeekClient instance (empirical model).
        events: A list of event dicts, each with at minimum a 'title' field.

    Returns:
        A dict with connectionSummary, connections, pestleMatrix,
        shortestPathLinks, and centralEvents keys,
        or None on ANY failure (graceful degradation).
    """
    if client is None:
        return None

    if not _has_minimal_event_data(events):
        return None

    events_json = _serialize_events(events)

    prompt = CONNECTIONS_PROMPT.format(
        event_count=len(events),
        events_json=events_json,
    )

    try:
        result = client.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是一个关联分析专家。你的任务是发现事件之间的非显性关联、"
                        "生成PESTLE交互矩阵、分析事件网络结构。严格按JSON格式输出。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=8192,
        )
    except Exception:
        return None

    # ── Defensive: validate response structure ──
    if not isinstance(result, dict):
        return None

    result.setdefault("connectionSummary", "")

    # -- Sanitize connections --
    connections = result.get("connections")
    if not isinstance(connections, list):
        result["connections"] = []
    else:
        result["connections"] = [
            _sanitize_connection(c) if isinstance(c, dict) else _sanitize_connection({})
            for c in connections
        ]

    # -- Sanitize pestleMatrix --
    pm = result.get("pestleMatrix")
    if not isinstance(pm, dict):
        result["pestleMatrix"] = {
            "dominantDimension": "",
            "dominantRationale": "",
            "dimensionInteractions": [],
            "eventImpacts": [],
        }
    else:
        pm.setdefault("dominantDimension", "")
        pm.setdefault("dominantRationale", "")

        # Sanitize dimensionInteractions
        interactions = pm.get("dimensionInteractions")
        if not isinstance(interactions, list):
            pm["dimensionInteractions"] = []
        else:
            cleaned_interactions = []
            for di in interactions:
                if not isinstance(di, dict):
                    continue
                cleaned_interactions.append({
                    "fromDimension": _sanitize_pestle_dimension(di.get("fromDimension")),
                    "toDimension": _sanitize_pestle_dimension(di.get("toDimension")),
                    "interactionDescription": di.get("interactionDescription") or "",
                    "exampleEventIds": (
                        di["exampleEventIds"]
                        if isinstance(di.get("exampleEventIds"), list)
                        else []
                    ),
                })
            pm["dimensionInteractions"] = cleaned_interactions

        # Sanitize eventImpacts
        impacts = pm.get("eventImpacts")
        if not isinstance(impacts, list):
            pm["eventImpacts"] = []
        else:
            cleaned_impacts = []
            for imp in impacts:
                if not isinstance(imp, dict):
                    continue
                cleaned_impacts.append({
                    "eventId": imp.get("eventId") or "",
                    "eventTitle": imp.get("eventTitle") or "",
                    "politicalImpact": imp.get("politicalImpact") or "",
                    "economicImpact": imp.get("economicImpact") or "",
                    "socialImpact": imp.get("socialImpact") or "",
                    "technologicalImpact": imp.get("technologicalImpact") or "",
                    "legalImpact": imp.get("legalImpact") or "",
                    "environmentalImpact": imp.get("environmentalImpact") or "",
                    "overallAssessment": imp.get("overallAssessment") or "",
                })
            pm["eventImpacts"] = cleaned_impacts

    # -- Sanitize shortestPathLinks --
    paths = result.get("shortestPathLinks")
    if not isinstance(paths, list):
        result["shortestPathLinks"] = []
    else:
        result["shortestPathLinks"] = [
            _sanitize_shortest_path(sp) if isinstance(sp, dict) else _sanitize_shortest_path({})
            for sp in paths
        ]

    # -- Sanitize centralEvents --
    central = result.get("centralEvents")
    if not isinstance(central, list):
        result["centralEvents"] = []
    else:
        result["centralEvents"] = [
            _sanitize_central_event(ce) if isinstance(ce, dict) else _sanitize_central_event({})
            for ce in central
        ]

    return result
