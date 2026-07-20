"""Composition-policy v1 resolution and DiagramPlan v0.2 compilation helpers."""

from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .icon_system import canonical_icon_system_id, icon_system_version
from .illustrated_registry import illustrated_icon_ids


DEFAULT_ICON_SYSTEM = "diagram-core-v1"
DEFAULT_STYLE = "minimal-light"
DEFAULT_LAYOUT = "layered"
DEFAULT_MOTION = "showcase-v1"

ICON_SYSTEMS = {
    "diagram-core-v1",
    "illustrated",
    "illustrated-character-v1",
    "illustrated-character-v2",
    "illustrated-v1",
    "semantic-line-v1",
}
STYLES = {
    "minimal-light",
    "deep-tech",
    "blueprint",
    "flat-icon",
    "dark-terminal",
    "notion-clean",
    "glassmorphism",
    "claude-warm",
    "openai-minimal",
    "dark-luxury",
    "aurora-orb",
    "illustrated-semantic",
    "sketch-board",
}
LAYOUTS = {
    "pipeline",
    "loop",
    "hub-spoke",
    "layered",
    "swimlane",
    "compare",
    "matrix",
    "timeline",
    "stack",
    "funnel",
    "sequence",
    "er",
    "network",
    "agent-memory",
}
MOTIONS = {"off", "subtle", "normal", "expressive", "teaching", "runtime-loop", "showcase-v1"}

DIAGRAM_CORE_ICONS = {
    "user", "developer", "operator", "agent", "agent-team", "assistant", "human-reviewer", "ai-model", "llm",
    "neural-network", "reasoning", "embedding", "memory", "tool", "token", "database", "vector-database",
    "data-warehouse", "document-store", "knowledge-base", "dataset", "search", "file", "folder", "document", "pdf",
    "image", "audio", "video", "code-file", "output", "api", "webhook", "http-request", "gateway", "load-balancer",
    "message-queue", "shield", "server", "server-cluster", "cloud", "container", "function", "edge-node", "source-code",
    "git-repository", "branch", "pull-request", "ci-cd", "deployment", "task", "scheduler", "monitoring", "logs", "alert",
    "debug",
}
LEGACY_ICONS = {"database", "file", "folder", "api", "cloud", "search", "shield", "agent", "operator", "token", "memory", "tool", "output"}

_KIND_ALIASES = {
    "actor": "user",
    "service": "server",
    "application": "server",
    "workload": "container",
    "observability": "monitoring",
    "metrics": "monitoring",
    "repository": "git-repository",
    "queue": "message-queue",
    "model": "ai-model",
    "reviewer": "human-reviewer",
    "code": "source-code",
}
_ROLE_FALLBACK = {
    "actor": "user",
    "source": "api",
    "process": "server",
    "agent": "agent",
    "memory": "memory",
    "tool": "tool",
    "output": "output",
    "risk": "shield",
    "neutral": "server",
}
_LEGACY_ROLE_FALLBACK = {
    "actor": "operator",
    "source": "api",
    "process": "agent",
    "agent": "agent",
    "memory": "memory",
    "tool": "tool",
    "output": "output",
    "risk": "shield",
    "neutral": "file",
}
_V2_ROLE_FALLBACK = {
    "actor": "operator",
    "source": "api",
    "process": "agent",
    "agent": "agent",
    "memory": "memory",
    "tool": "tool",
    "output": "output",
    "risk": "operator",
    "neutral": "agent",
}

_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_KIND_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
_ROLES = {"actor", "source", "process", "agent", "memory", "tool", "output", "risk", "neutral"}
_IMPORTANCE = {"primary", "supporting", "context"}
_PLAN_FIELDS = {"version", "semantic", "presentation", "presentation_sources"}
_SEMANTIC_FIELDS = {"title", "subtitle", "summary", "intent", "entities", "relations", "groups", "flows", "sources", "annotations"}
_INTENT_FIELDS = {"diagram_kind", "primary_question", "audience", "scope", "exclusions"}
_ENTITY_FIELDS = {"id", "label", "description", "kind", "role", "importance", "tags", "attributes", "state", "source_refs"}
_RELATION_FIELDS = {"id", "from", "to", "kind", "label", "description", "direction", "importance", "condition", "protocol", "attributes", "source_refs"}
_GROUP_FIELDS = {"id", "label", "description", "kind", "members", "importance", "parent", "source_refs"}
_FLOW_FIELDS = {"id", "label", "description", "relation_ids", "importance", "repeat", "source_refs"}
_SOURCE_FIELDS = {"id", "type", "title", "uri", "note"}


def compile_plan_v02(plan: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate DiagramPlan v0.2 and compile it to resolved DiagramScript v0.4."""

    semantic = _validate_plan(plan)
    resolved = resolve_presentation(plan.get("presentation"), plan.get("presentation_sources"))
    icon_system = resolved["icon_system"]["value"]
    entities = list(semantic["entities"])
    relations = list(semantic.get("relations", []))
    positions, canvas = _layout_entities(entities, relations, resolved["layout"]["value"])
    nodes = [_compile_entity(entity, positions[str(entity["id"])], icon_system, index + 1) for index, entity in enumerate(entities)]
    edges = [_compile_relation(relation, index + 1) for index, relation in enumerate(relations)]
    groups = _compile_semantic_groups(semantic.get("groups", []), nodes)

    return {
        "version": "0.4",
        "composition_policy": "composition-v1",
        "resolved_presentation": deepcopy(resolved),
        "icon_system": icon_system,
        "preset": resolved["layout"]["value"],
        "canvas": canvas,
        "style": resolved["style"]["value"],
        "title": {
            "text": str(semantic["title"]),
            "subtitle": str(semantic.get("subtitle") or semantic.get("summary") or ""),
        },
        "motion": _motion_config(resolved["motion"]["value"]),
        "motion_policy": _showcase_motion_policy() if resolved["motion"]["value"] == "showcase-v1" else {"profile": "unrestricted"},
        "groups": groups,
        "nodes": nodes,
        "edges": edges,
    }


def resolve_presentation(value: Any, source_value: Any = None) -> Dict[str, Dict[str, str]]:
    presentation = value if isinstance(value, Mapping) else {}
    sources = source_value if isinstance(source_value, Mapping) else {}
    icon_system = _resolve_axis(
        presentation.get("icon_system"),
        DEFAULT_ICON_SYSTEM,
        ICON_SYSTEMS,
        "default",
        sources.get("icon_system"),
    )
    icon_system["value"] = canonical_icon_system_id(icon_system["value"])
    version = icon_system_version(icon_system["value"])
    if version is not None:
        icon_system["version"] = version
    return {
        "icon_system": icon_system,
        "style": _resolve_axis(presentation.get("style"), DEFAULT_STYLE, STYLES, "fallback", sources.get("style")),
        "layout": _resolve_axis(presentation.get("layout"), DEFAULT_LAYOUT, LAYOUTS, "fallback", sources.get("layout")),
        "motion": _resolve_axis(presentation.get("motion"), DEFAULT_MOTION, MOTIONS, "default", sources.get("motion")),
    }


def _resolve_axis(
    value: Any,
    default: str,
    supported: Iterable[str],
    default_source: str,
    requested_source: Any = None,
) -> Dict[str, str]:
    if value is None or value == "auto":
        if requested_source is not None:
            raise ValueError("presentation_sources cannot mark an 'auto' presentation value")
        return {"value": default, "source": default_source}
    if not isinstance(value, str) or value not in supported:
        raise ValueError(f"unsupported presentation value {value!r}; expected 'auto' or one of: {', '.join(sorted(supported))}")
    if requested_source not in {None, "explicit", "model"}:
        raise ValueError("presentation source must be 'explicit' or 'model'")
    return {"value": value, "source": str(requested_source or "explicit")}


def _validate_plan(plan: Mapping[str, Any]) -> Mapping[str, Any]:
    _assert_keys(plan, _PLAN_FIELDS, "DiagramPlan")
    if plan.get("version") != "0.2":
        raise ValueError("DiagramPlan version must be '0.2'")
    semantic = plan.get("semantic")
    if not isinstance(semantic, Mapping):
        raise ValueError("DiagramPlan v0.2 requires a semantic object")
    _assert_keys(semantic, _SEMANTIC_FIELDS, "semantic")
    if not str(semantic.get("title") or "").strip():
        raise ValueError("semantic.title must be non-empty")
    intent = semantic.get("intent")
    if not isinstance(intent, Mapping) or not str(intent.get("primary_question") or "").strip():
        raise ValueError("semantic.intent.primary_question must be non-empty")
    _assert_keys(intent, _INTENT_FIELDS, "semantic.intent")
    _semantic_kind_value(intent.get("diagram_kind"), "semantic.intent.diagram_kind")
    audience = intent.get("audience")
    if not isinstance(audience, Sequence) or isinstance(audience, (str, bytes)) or not audience:
        raise ValueError("semantic.intent.audience must be a non-empty array")
    entities = semantic.get("entities")
    if not isinstance(entities, Sequence) or isinstance(entities, (str, bytes)) or not entities:
        raise ValueError("semantic.entities must be a non-empty array")

    collections = ("entities", "relations", "groups", "flows", "sources")
    seen: Dict[str, str] = {}
    for collection in collections:
        values = semantic.get(collection, [])
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise ValueError(f"semantic.{collection} must be an array")
        for index, item in enumerate(values):
            if not isinstance(item, Mapping):
                raise ValueError(f"semantic.{collection}[{index}] must be an object")
            item_id = str(item.get("id") or "")
            _semantic_id(item_id, f"semantic.{collection}[{index}].id")
            if item_id in seen:
                raise ValueError(f"duplicate semantic id {item_id!r} in {collection}; already used in {seen[item_id]}")
            seen[item_id] = collection

    for index, entity in enumerate(entities):
        path = f"semantic.entities[{index}]"
        _assert_keys(entity, _ENTITY_FIELDS, path)
        if not str(entity.get("label") or "").strip():
            raise ValueError(f"{path}.label must be non-empty")
        _semantic_kind_value(entity.get("kind"), f"{path}.kind")
        if entity.get("role") not in _ROLES:
            raise ValueError(f"{path}.role must be a registered semantic role")
        _optional_importance(entity, path)

    entity_ids = {str(item["id"]) for item in entities}
    relations = list(semantic.get("relations", []))
    relation_by_id = {str(item["id"]): item for item in relations}
    for relation in relations:
        path = f"semantic.relations[{relations.index(relation)}]"
        _assert_keys(relation, _RELATION_FIELDS, path)
        _semantic_kind_value(relation.get("kind"), f"{path}.kind")
        if relation.get("direction", "forward") not in {"forward", "bidirectional", "undirected"}:
            raise ValueError(f"{path}.direction is not supported")
        _optional_importance(relation, path)
        for endpoint in ("from", "to"):
            target = str(relation.get(endpoint) or "")
            if target not in entity_ids:
                raise ValueError(f"relation {relation['id']!r} references missing entity {target!r}")

    groups = list(semantic.get("groups", []))
    group_ids = {str(group["id"]) for group in groups}
    parents: Dict[str, str] = {}
    for group in groups:
        path = f"semantic.groups[{groups.index(group)}]"
        _assert_keys(group, _GROUP_FIELDS, path)
        if not str(group.get("label") or "").strip():
            raise ValueError(f"{path}.label must be non-empty")
        _semantic_kind_value(group.get("kind"), f"{path}.kind")
        _optional_importance(group, path)
        members = group.get("members")
        if not isinstance(members, Sequence) or isinstance(members, (str, bytes)) or not members:
            raise ValueError(f"group {group['id']!r} must contain at least one member")
        missing = [str(member) for member in members if str(member) not in entity_ids]
        if missing:
            raise ValueError(f"group {group['id']!r} references missing member(s): {', '.join(missing)}")
        if group.get("parent") is not None:
            parent = str(group["parent"])
            if parent not in group_ids:
                raise ValueError(f"group {group['id']!r} references missing parent {parent!r}")
            parents[str(group["id"])] = parent
    _validate_group_cycles(parents)

    for flow in semantic.get("flows", []):
        path = f"semantic.flows[{list(semantic.get('flows', [])).index(flow)}]"
        _assert_keys(flow, _FLOW_FIELDS, path)
        if not str(flow.get("label") or "").strip():
            raise ValueError(f"{path}.label must be non-empty")
        if flow.get("repeat", "once") not in {"once", "loop", "event-driven"}:
            raise ValueError(f"{path}.repeat is not supported")
        _optional_importance(flow, path)
        relation_ids = flow.get("relation_ids")
        if not isinstance(relation_ids, Sequence) or isinstance(relation_ids, (str, bytes)) or not relation_ids:
            raise ValueError(f"flow {flow['id']!r} must contain relation_ids")
        missing = [str(relation_id) for relation_id in relation_ids if str(relation_id) not in relation_by_id]
        if missing:
            raise ValueError(f"flow {flow['id']!r} references missing relation(s): {', '.join(missing)}")
        ordered = [relation_by_id[str(relation_id)] for relation_id in relation_ids]
        for left, right in zip(ordered, ordered[1:]):
            if str(left.get("to")) != str(right.get("from")):
                raise ValueError(f"flow {flow['id']!r} is not coherent between {left['id']!r} and {right['id']!r}")

    sources = list(semantic.get("sources", []))
    source_ids = {str(source["id"]) for source in sources}
    for index, source in enumerate(sources):
        path = f"semantic.sources[{index}]"
        _assert_keys(source, _SOURCE_FIELDS, path)
        _semantic_kind_value(source.get("type"), f"{path}.type")
    for collection in ("entities", "relations", "groups", "flows"):
        for index, item in enumerate(semantic.get(collection, [])):
            refs = item.get("source_refs", [])
            if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes)):
                raise ValueError(f"semantic.{collection}[{index}].source_refs must be an array")
            missing = [str(ref) for ref in refs if str(ref) not in source_ids]
            if missing:
                raise ValueError(f"semantic.{collection}[{index}] references missing source(s): {', '.join(missing)}")

    presentation = plan.get("presentation", {})
    if not isinstance(presentation, Mapping):
        raise ValueError("presentation must be an object")
    _assert_keys(presentation, {"icon_system", "style", "layout", "motion"}, "presentation")
    presentation_sources = plan.get("presentation_sources", {})
    if not isinstance(presentation_sources, Mapping):
        raise ValueError("presentation_sources must be an object")
    _assert_keys(
        presentation_sources,
        {"icon_system", "style", "layout", "motion"},
        "presentation_sources",
    )
    resolve_presentation(presentation, presentation_sources)
    return semantic


def _assert_keys(value: Mapping[str, Any], allowed: Iterable[str], path: str) -> None:
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        raise ValueError(f"{path} contains unsupported field(s): {', '.join(unknown)}")


def _semantic_id(value: Any, path: str) -> str:
    if not isinstance(value, str) or _ID_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{path} must be a valid semantic id")
    return value


def _semantic_kind_value(value: Any, path: str) -> str:
    if not isinstance(value, str) or _KIND_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{path} must be a lowercase semantic kind")
    return value


def _optional_importance(value: Mapping[str, Any], path: str) -> None:
    if value.get("importance") is not None and value.get("importance") not in _IMPORTANCE:
        raise ValueError(f"{path}.importance is not supported")


def _validate_group_cycles(parents: Mapping[str, str]) -> None:
    for group_id in parents:
        path = set()
        current = group_id
        while current in parents:
            if current in path:
                raise ValueError(f"group nesting contains a cycle at {current!r}")
            path.add(current)
            current = parents[current]


def _layout_entities(
    entities: Sequence[Mapping[str, Any]], relations: Sequence[Mapping[str, Any]], layout: str
) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    # v0.4 serializes a concrete layout choice; this deterministic graph layout
    # supplies resolved coordinates until the individual layout engines evolve.
    ids = [str(entity["id"]) for entity in entities]
    incoming = {item_id: 0 for item_id in ids}
    outgoing: Dict[str, List[str]] = defaultdict(list)
    for relation in relations:
        source, target = str(relation["from"]), str(relation["to"])
        outgoing[source].append(target)
        incoming[target] += 1
    queue = deque(item_id for item_id in ids if incoming[item_id] == 0)
    rank = {item_id: 0 for item_id in ids}
    visited = set()
    while queue:
        source = queue.popleft()
        visited.add(source)
        for target in outgoing[source]:
            rank[target] = max(rank[target], rank[source] + 1)
            incoming[target] -= 1
            if incoming[target] == 0:
                queue.append(target)
    for item_id in ids:
        if item_id not in visited:
            rank[item_id] = max(rank.values(), default=0) + 1

    by_rank: Dict[int, List[str]] = defaultdict(list)
    for item_id in ids:
        by_rank[rank[item_id]].append(item_id)
    max_rank = max(by_rank, default=0)
    width = max(960, 340 + max_rank * 280)
    max_rows = max((len(items) for items in by_rank.values()), default=1)
    height = max(720, 280 + max_rows * 150)
    positions: Dict[str, Tuple[int, int]] = {}
    for level, items in sorted(by_rank.items()):
        x = 70 + level * 280
        total = len(items) * 108 + max(0, len(items) - 1) * 42
        y = max(150, (height - total) // 2 + 45)
        for index, item_id in enumerate(items):
            positions[item_id] = (x, y + index * 150)
    return positions, {"width": width, "height": height}


def _compile_entity(entity: Mapping[str, Any], position: Tuple[int, int], icon_system: str, step: int) -> Dict[str, Any]:
    role = str(entity.get("role") or "neutral")
    return {
        "id": str(entity["id"]),
        "label": str(entity.get("label") or entity["id"])[:42],
        "caption": str(entity.get("description") or entity.get("kind") or "")[:64],
        "position": [position[0], position[1]],
        "size": [220, 108],
        "role": role,
        "icon": _icon_for_entity(entity, icon_system),
        "step": step,
        "effect": {"preset": "icon-performance"},
    }


def _icon_for_entity(entity: Mapping[str, Any], icon_system: str) -> str:
    kind = str(entity.get("kind") or "")
    role = str(entity.get("role") or "neutral")
    if icon_system == "diagram-core-v1":
        candidate = _KIND_ALIASES.get(kind, kind)
        return candidate if candidate in DIAGRAM_CORE_ICONS else _ROLE_FALLBACK.get(role, "server")
    if icon_system == "illustrated":
        candidate = _KIND_ALIASES.get(kind, kind)
        return candidate if candidate in set(illustrated_icon_ids()) else _V2_ROLE_FALLBACK.get(role, "agent")
    candidate = _KIND_ALIASES.get(kind, kind)
    return candidate if candidate in LEGACY_ICONS else _LEGACY_ROLE_FALLBACK.get(role, "file")


def _compile_relation(relation: Mapping[str, Any], step: int) -> Dict[str, Any]:
    importance = str(relation.get("importance") or "supporting")
    effect = "flow-arrow" if importance in {"primary", "supporting"} else "draw"
    return {
        "from": str(relation["from"]),
        "to": str(relation["to"]),
        "label": str(relation.get("label") or "")[:44],
        "role": _relation_role(str(relation.get("kind") or ""), importance),
        "direction": str(relation.get("direction") or "forward"),
        "route": "straight",
        "step": step,
        "effect": {"preset": effect, "particle": "soft-arrow", "particle_count": 1, "trail_count": 1},
    }


def _relation_role(kind: str, importance: str) -> str:
    if kind in {"observability", "feedback"}:
        return "output"
    if kind in {"security", "risk", "failure"}:
        return "risk"
    return "process" if importance == "primary" else "neutral"


def _compile_semantic_groups(groups: Any, nodes: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    node_by_id = {str(node["id"]): node for node in nodes}
    compiled = []
    for group in groups if isinstance(groups, Sequence) and not isinstance(groups, (str, bytes)) else []:
        members = [node_by_id[str(member)] for member in group.get("members", [])]
        left = min(node["position"][0] for node in members) - 26
        top = min(node["position"][1] for node in members) - 42
        right = max(node["position"][0] + node["size"][0] for node in members) + 26
        bottom = max(node["position"][1] + node["size"][1] for node in members) + 26
        compiled.append(
            {
                "id": str(group["id"]),
                "label": str(group.get("label") or group["id"]),
                "bounds": [left, top, right - left, bottom - top],
                "role": "neutral",
                "effect": {"preset": "border-scan"},
            }
        )
    return compiled


def _motion_config(profile: str) -> Dict[str, Any]:
    if profile != "showcase-v1":
        return {"profile": profile}
    return {
        "profile": "showcase-v1",
        "sequence": "staged",
        "ease": "spring",
        "stagger": 0.12,
        "duration_scale": 1.0,
        "intensity": 1.0,
        "edge": {"preset": "flow-arrow"},
        "node": {"preset": "icon-performance"},
        "group": {"preset": "border-scan"},
        "title": {"preset": "highlight-sweep"},
        "reduced_motion": "subtle",
    }


def _showcase_motion_policy() -> Dict[str, Any]:
    return {
        "profile": "unrestricted",
        "motion_area": "unrestricted",
        "pulse_mode": "all",
    }
