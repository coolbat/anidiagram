"""Composition-policy v1 resolution and DiagramPlan v0.2 compilation helpers."""

from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
import math
import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .icon_system import canonical_icon_system_id, icon_system_version
from .illustrated_registry import illustrated_icon_ids
from .localization import resolve_locale
from .repository_evidence import compile_evidence, validate_repository
from .planning import validate_planning


DEFAULT_ICON_SYSTEM = "illustrated"
DEFAULT_STYLE = "openai-minimal"
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
# Retired public styles that still validate and render as their replacement.
STYLE_ALIASES = {"minimal-light": "openai-minimal"}
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
    "agent-loop",
    "layered-loop",
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
_PLAN_FIELDS = {"version", "semantic", "presentation", "presentation_sources", "reader", "planning"}
_SEMANTIC_FIELDS = {"language", "title", "subtitle", "summary", "intent", "entities", "relations", "groups", "flows", "sources", "annotations", "type_details"}
_INTENT_FIELDS = {"diagram_kind", "primary_question", "audience", "scope", "exclusions"}
_ENTITY_FIELDS = {"id", "label", "description", "kind", "role", "importance", "tags", "attributes", "state", "source_refs"}
_RELATION_FIELDS = {"id", "from", "to", "kind", "label", "description", "direction", "importance", "condition", "protocol", "attributes", "source_refs"}
_GROUP_FIELDS = {"id", "label", "description", "kind", "members", "importance", "parent", "source_refs"}
_FLOW_FIELDS = {"id", "label", "description", "relation_ids", "importance", "repeat", "source_refs"}
_SOURCE_FIELDS = {"id", "type", "title", "uri", "note", "repository"}


def compile_plan_v02(plan: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate DiagramPlan v0.2 and compile it to resolved DiagramScript v0.4."""

    semantic = _validate_plan(plan)
    from .type_semantics import compile_type_semantics
    typed = compile_type_semantics(semantic)
    resolved = resolve_presentation(plan.get("presentation"), plan.get("presentation_sources"))
    icon_system = resolved["icon_system"]["value"]
    entities = list(semantic["entities"])
    relations = list(semantic.get("relations", []))
    flows = list(semantic.get("flows", []))
    groups_semantic = list(semantic.get("groups", []))
    entity_order = _ordered_entity_ids(entities, relations, flows)
    positions, canvas = _layout_entities(
        entities,
        relations,
        resolved["layout"]["value"],
        flows=flows,
        groups=groups_semantic,
    )
    step_by_entity = {entity_id: index + 1 for index, entity_id in enumerate(entity_order)}
    nodes = [
        _compile_entity(
            entity,
            positions[str(entity["id"])],
            icon_system,
            step_by_entity[str(entity["id"])],
        )
        for entity in entities
    ]
    flow_context = _flow_relation_context(flows)
    edges = [
        _compile_relation(relation, index + 1, flow_context.get(str(relation["id"])))
        for index, relation in enumerate(relations)
    ]
    if resolved["layout"]["value"] == "agent-loop":
        agent_loop_zones = _agent_loop_zones(
            entity_order,
            {str(entity["id"]): entity for entity in entities},
            groups_semantic,
        )
        zone_by_entity = {
            item_id: zone
            for zone, item_ids in agent_loop_zones.items()
            for item_id in item_ids
        }
        _apply_agent_loop_presentation(edges, nodes, zone_by_entity)
    elif resolved["layout"]["value"] == "layered-loop":
        lane_by_entity, lanes = _semantic_lanes(
            entity_order,
            {str(entity["id"]): entity for entity in entities},
            groups_semantic,
        )
        _apply_layered_loop_presentation(edges, nodes, lane_by_entity, lanes, canvas)
    groups = _compile_semantic_groups(groups_semantic, nodes)
    from .routing import route_compiled_edges
    route_compiled_edges(nodes, edges, groups, canvas)
    locale = resolve_locale(
        str(semantic.get("language") or "auto"),
        (
            semantic.get("title"),
            semantic.get("subtitle"),
            semantic.get("summary"),
            *(entity.get("label") for entity in entities),
            *(relation.get("label") for relation in relations),
        ),
    )

    specification = {
        "version": "0.4",
        "locale": locale,
        "composition_policy": "composition-v1",
        "resolved_presentation": deepcopy(resolved),
        "icon_system": icon_system,
        "layout": resolved["layout"]["value"],
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
    if "planning" in plan:
        specification["planning"] = validate_planning(plan["planning"])
    evidence = compile_evidence(semantic)
    if evidence is not None:
        specification["evidence"] = evidence
    if typed is not None:
        specification["type_semantics"] = typed
        if typed["kind"] == "sequence":
            steps = {message["relation_id"]: index + 1 for index, message in enumerate(typed["details"]["messages"])}
            for edge in specification["edges"]:
                if edge["semantic_relation_id"] in steps:
                    edge["step"] = steps[edge["semantic_relation_id"]]
    if "reader" in plan:
        from .reader import validate_reader
        validate_reader(plan["reader"], entities, relations)
        specification["reader"] = deepcopy(plan["reader"])
    return specification


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
        "style": _resolve_axis(STYLE_ALIASES.get(presentation.get("style"), presentation.get("style")), DEFAULT_STYLE, STYLES, "fallback", sources.get("style")),
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
    if semantic.get("language", "auto") not in {"auto", "en", "zh-CN"}:
        raise ValueError("semantic.language must be 'auto', 'en', or 'zh-CN'")
    _required_text(semantic, "title", "semantic.title")
    for field in ("subtitle", "summary"):
        _optional_text(semantic, field, f"semantic.{field}")
    intent = semantic.get("intent")
    if not isinstance(intent, Mapping):
        raise ValueError("semantic.intent.primary_question must be non-empty")
    _assert_keys(intent, _INTENT_FIELDS, "semantic.intent")
    _required_text(intent, "primary_question", "semantic.intent.primary_question")
    _semantic_kind_value(intent.get("diagram_kind"), "semantic.intent.diagram_kind")
    _string_array(intent.get("audience"), "semantic.intent.audience", required=True)
    _optional_text(intent, "scope", "semantic.intent.scope", allow_empty=True)
    if "exclusions" in intent:
        _string_array(intent["exclusions"], "semantic.intent.exclusions")
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
            item_id = _semantic_id(item.get("id"), f"semantic.{collection}[{index}].id")
            if item_id in seen:
                raise ValueError(f"duplicate semantic id {item_id!r} in {collection}; already used in {seen[item_id]}")
            seen[item_id] = collection

    for index, entity in enumerate(entities):
        path = f"semantic.entities[{index}]"
        _assert_keys(entity, _ENTITY_FIELDS, path)
        _required_text(entity, "label", f"{path}.label")
        _optional_text(entity, "description", f"{path}.description", allow_empty=True)
        _semantic_kind_value(entity.get("kind"), f"{path}.kind")
        if entity.get("role") not in _ROLES:
            raise ValueError(f"{path}.role must be a registered semantic role")
        _optional_importance(entity, path)
        if "tags" in entity:
            _string_array(entity["tags"], f"{path}.tags")
        _optional_mapping(entity, "attributes", f"{path}.attributes")
        _validate_state(entity.get("state"), f"{path}.state")

    entity_ids = {str(item["id"]) for item in entities}
    relations = list(semantic.get("relations", []))
    relation_by_id = {str(item["id"]): item for item in relations}
    for index, relation in enumerate(relations):
        path = f"semantic.relations[{index}]"
        _assert_keys(relation, _RELATION_FIELDS, path)
        _semantic_kind_value(relation.get("kind"), f"{path}.kind")
        for field in ("label", "description", "condition", "protocol"):
            _optional_text(relation, field, f"{path}.{field}", allow_empty=True)
        _optional_mapping(relation, "attributes", f"{path}.attributes")
        if relation.get("direction", "forward") not in {"forward", "bidirectional", "undirected"}:
            raise ValueError(f"{path}.direction is not supported")
        _optional_importance(relation, path)
        for endpoint in ("from", "to"):
            target = _semantic_id(relation.get(endpoint), f"{path}.{endpoint}")
            if target not in entity_ids:
                raise ValueError(f"relation {relation['id']!r} references missing entity {target!r}")

    groups = list(semantic.get("groups", []))
    group_ids = {str(group["id"]) for group in groups}
    parents: Dict[str, str] = {}
    for index, group in enumerate(groups):
        path = f"semantic.groups[{index}]"
        _assert_keys(group, _GROUP_FIELDS, path)
        _required_text(group, "label", f"{path}.label")
        _optional_text(group, "description", f"{path}.description", allow_empty=True)
        _semantic_kind_value(group.get("kind"), f"{path}.kind")
        _optional_importance(group, path)
        members = group.get("members")
        if not isinstance(members, Sequence) or isinstance(members, (str, bytes)) or not members:
            raise ValueError(f"group {group['id']!r} must contain at least one member")
        _string_array(members, f"{path}.members", required=True)
        for member_index, member in enumerate(members):
            _semantic_id(member, f"{path}.members[{member_index}]")
        missing = [str(member) for member in members if str(member) not in entity_ids]
        if missing:
            raise ValueError(f"group {group['id']!r} references missing member(s): {', '.join(missing)}")
        if group.get("parent") is not None:
            parent = _semantic_id(group["parent"], f"{path}.parent")
            if parent not in group_ids:
                raise ValueError(f"group {group['id']!r} references missing parent {parent!r}")
            parents[str(group["id"])] = parent
    _validate_group_cycles(parents)

    for index, flow in enumerate(semantic.get("flows", [])):
        path = f"semantic.flows[{index}]"
        _assert_keys(flow, _FLOW_FIELDS, path)
        _required_text(flow, "label", f"{path}.label")
        _optional_text(flow, "description", f"{path}.description", allow_empty=True)
        if flow.get("repeat", "once") not in {"once", "loop", "event-driven"}:
            raise ValueError(f"{path}.repeat is not supported")
        _optional_importance(flow, path)
        relation_ids = flow.get("relation_ids")
        if not isinstance(relation_ids, Sequence) or isinstance(relation_ids, (str, bytes)) or not relation_ids:
            raise ValueError(f"flow {flow['id']!r} must contain relation_ids")
        _string_array(relation_ids, f"{path}.relation_ids", required=True)
        for relation_index, relation_id in enumerate(relation_ids):
            _semantic_id(relation_id, f"{path}.relation_ids[{relation_index}]")
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
        for field in ("title", "uri", "note"):
            _optional_text(source, field, f"{path}.{field}", allow_empty=True)
        if "repository" in source:
            validate_repository(source["repository"])
    for collection in ("entities", "relations", "groups", "flows"):
        for index, item in enumerate(semantic.get(collection, [])):
            refs = item.get("source_refs", [])
            if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes)):
                raise ValueError(f"semantic.{collection}[{index}].source_refs must be an array")
            _string_array(refs, f"semantic.{collection}[{index}].source_refs")
            for ref_index, ref in enumerate(refs):
                _semantic_id(ref, f"semantic.{collection}[{index}].source_refs[{ref_index}]")
            missing = [str(ref) for ref in refs if str(ref) not in source_ids]
            if missing:
                raise ValueError(f"semantic.{collection}[{index}] references missing source(s): {', '.join(missing)}")

    if "presentation" not in plan:
        raise ValueError("DiagramPlan v0.2 requires a presentation object")
    presentation = plan.get("presentation")
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
    if "annotations" in semantic:
        _string_array(semantic["annotations"], "semantic.annotations")
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


def _required_text(value: Mapping[str, Any], field: str, path: str) -> str:
    item = value.get(field)
    if not isinstance(item, str) or not item.strip():
        raise ValueError(f"{path} must be non-empty")
    return item


def _optional_text(
    value: Mapping[str, Any], field: str, path: str, *, allow_empty: bool = False
) -> None:
    if field not in value:
        return
    item = value[field]
    if not isinstance(item, str) or (not allow_empty and not item.strip()):
        raise ValueError(f"{path} must be a string")


def _string_array(value: Any, path: str, *, required: bool = False) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        suffix = " a non-empty array" if required else " an array"
        raise ValueError(f"{path} must be{suffix}")
    if required and not value:
        raise ValueError(f"{path} must be a non-empty array")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{path} must contain non-empty strings")
    _unique_values(value, path)


def _unique_values(value: Sequence[Any], path: str) -> None:
    normalized = [str(item) for item in value]
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{path} must contain unique values")


def _optional_mapping(value: Mapping[str, Any], field: str, path: str) -> None:
    if field in value and not isinstance(value[field], Mapping):
        raise ValueError(f"{path} must be an object")


def _validate_state(value: Any, path: str) -> None:
    if value is None:
        return
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object")
    _assert_keys(value, {"phase", "result", "availability"}, path)
    for field in value:
        _required_text(value, field, f"{path}.{field}")


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
    entities: Sequence[Mapping[str, Any]],
    relations: Sequence[Mapping[str, Any]],
    layout: str,
    *,
    flows: Sequence[Mapping[str, Any]] = (),
    groups: Sequence[Mapping[str, Any]] = (),
) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    """Dispatch every registered layout to deterministic, semantic-aware geometry."""

    if layout not in LAYOUTS:
        raise ValueError(f"unsupported layout {layout!r}")
    ordered = _ordered_entity_ids(entities, relations, flows)
    entity_by_id = {str(entity["id"]): entity for entity in entities}
    dispatchers = {
        "pipeline": lambda: _linear_layout(ordered, horizontal=True, x=70, y=260, gap=280, canvas_height=720),
        "timeline": lambda: _timeline_layout(ordered),
        "sequence": lambda: _sequence_layout(ordered),
        "stack": lambda: _linear_layout(ordered, horizontal=False, x=110, y=135, gap=155, canvas_width=760),
        "layered": lambda: _layered_layout(ordered, relations, groups),
        "swimlane": lambda: _swimlane_layout(ordered, entity_by_id, groups),
        "compare": lambda: _compare_layout(ordered),
        "matrix": lambda: _grid_layout(ordered, columns=2, x=90, y=145, x_gap=330, y_gap=170, canvas_width=900),
        "hub-spoke": lambda: _radial_layout(ordered, relations, hub=True),
        "network": lambda: _radial_layout(ordered, relations, hub=False, elliptical=True),
        "loop": lambda: _radial_layout(list(reversed(ordered)), relations, hub=False, elliptical=False),
        "funnel": lambda: _funnel_layout(ordered),
        "er": lambda: _er_layout(ordered, relations),
        "agent-memory": lambda: _agent_memory_layout(ordered, entity_by_id),
        "agent-loop": lambda: _agent_loop_layout(ordered, entity_by_id, groups, relations),
        "layered-loop": lambda: _layered_loop_layout(ordered, entity_by_id, groups),
    }
    return dispatchers[layout]()


def _ordered_entity_ids(
    entities: Sequence[Mapping[str, Any]],
    relations: Sequence[Mapping[str, Any]],
    flows: Sequence[Mapping[str, Any]],
) -> List[str]:
    declared = [str(entity["id"]) for entity in entities]
    relation_by_id = {str(relation["id"]): relation for relation in relations}
    ordered: List[str] = []
    importance_order = {"primary": 0, "supporting": 1, "context": 2}
    ranked_flows = sorted(
        enumerate(flows),
        key=lambda item: (importance_order.get(str(item[1].get("importance") or "supporting"), 1), item[0]),
    )
    for _, flow in ranked_flows:
        for relation_id in flow.get("relation_ids", []):
            relation = relation_by_id.get(str(relation_id))
            if relation is None:
                continue
            for entity_id in (str(relation["from"]), str(relation["to"])):
                if entity_id not in ordered:
                    ordered.append(entity_id)
    for entity_id in declared:
        if entity_id not in ordered:
            ordered.append(entity_id)
    return ordered


def _linear_layout(
    ordered: Sequence[str],
    *,
    horizontal: bool,
    x: int,
    y: int,
    gap: int,
    canvas_width: int = 960,
    canvas_height: int = 720,
) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    if horizontal:
        positions = {item_id: (x + index * gap, y) for index, item_id in enumerate(ordered)}
        width = max(canvas_width, x * 2 + 220 + max(0, len(ordered) - 1) * gap)
        return positions, {"width": width, "height": canvas_height}
    positions = {item_id: (x, y + index * gap) for index, item_id in enumerate(ordered)}
    height = max(canvas_height, y + 150 + max(0, len(ordered) - 1) * gap)
    return positions, {"width": canvas_width, "height": height}


def _timeline_layout(ordered: Sequence[str]) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    positions = {
        item_id: (85 + index * 275, 175 + (index % 2) * 230)
        for index, item_id in enumerate(ordered)
    }
    return positions, {"width": max(1040, 390 + max(0, len(ordered) - 1) * 275), "height": 760}


def _sequence_layout(ordered: Sequence[str]) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    positions = {
        item_id: (260 + (index % 2) * 285, 125 + index * 150)
        for index, item_id in enumerate(ordered)
    }
    return positions, {"width": 1040, "height": max(760, 275 + max(0, len(ordered) - 1) * 150)}


def _layered_layout(
    ordered: Sequence[str],
    relations: Sequence[Mapping[str, Any]],
    groups: Sequence[Mapping[str, Any]] = (),
) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    # Rank independent semantic groups within separate bands. Ranking the whole
    # graph first can interleave groups, especially when cross-group feedback
    # stalls Kahn's traversal. Wrapping those interleaved nodes cannot produce
    # non-overlapping group boxes. Nested/shared groups retain their established
    # geometry; their membership is not a partition and must not be reassigned.
    bands: List[List[str]] = []
    assigned: set[str] = set()
    for group in groups:
        members = set(str(member) for member in group.get("members", []))
        if group.get("parent") or assigned.intersection(members):
            bands = []
            break
        bands.append([item_id for item_id in ordered if item_id in members])
        assigned.update(members)
    if bands:
        ungrouped = [item_id for item_id in ordered if item_id not in assigned]
        if ungrouped:
            bands.append(ungrouped)
    if len(bands) > 1:
        positions: Dict[str, Tuple[int, int]] = {}
        width, bottom, next_y = 960, 0, 210
        for band in bands:
            member_ids = set(band)
            local_relations = [
                relation for relation in relations
                if str(relation["from"]) in member_ids and str(relation["to"]) in member_ids
            ]
            local_positions, local_canvas = _layered_layout(band, local_relations)
            local_top = min(y for _, y in local_positions.values())
            for item_id, (x, y) in local_positions.items():
                positions[item_id] = (x, next_y + y - local_top)
            bottom = max(positions[item_id][1] + 108 for item_id in band)
            next_y = bottom + 110  # Group footer + gap + next group heading.
            width = max(width, local_canvas["width"])
        return positions, {"width": width, "height": max(720, bottom + 70)}

    ids = list(ordered)
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
            rank[item_id] = max(rank.values(), default=0)

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


def _swimlane_layout(
    ordered: Sequence[str], entity_by_id: Mapping[str, Mapping[str, Any]], groups: Sequence[Mapping[str, Any]]
) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    lane_by_entity, lanes = _semantic_lanes(ordered, entity_by_id, groups)
    counts: Dict[str, int] = defaultdict(int)
    positions = {}
    for item_id in ordered:
        lane = lane_by_entity[item_id]
        lane_index = lanes.index(lane)
        positions[item_id] = (80 + counts[lane] * 300, 125 + lane_index * 185)
        counts[lane] += 1
    return positions, {
        "width": max(1020, 380 + max(counts.values(), default=1) * 300),
        "height": max(720, 270 + max(0, len(lanes) - 1) * 185),
    }


def _layered_loop_layout(
    ordered: Sequence[str],
    entity_by_id: Mapping[str, Mapping[str, Any]],
    groups: Sequence[Mapping[str, Any]],
) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    lane_by_entity, lanes = _semantic_lanes(ordered, entity_by_id, groups)
    items_by_lane = {
        lane: [item_id for item_id in ordered if lane_by_entity[item_id] == lane]
        for lane in lanes
    }
    max_count = max((len(items) for items in items_by_lane.values()), default=1)
    node_width = 220
    column_gap = 300
    outer_padding = 100
    row_width = node_width + max(0, max_count - 1) * column_gap
    width = max(1020, row_width + outer_padding * 2)
    left = (width - row_width) // 2
    right = left + max(0, max_count - 1) * column_gap
    positions: Dict[str, Tuple[int, int]] = {}
    for lane_index, lane in enumerate(lanes):
        items = items_by_lane[lane]
        if len(items) == 1:
            positions[items[0]] = ((width - node_width) // 2, 235 + lane_index * 220)
            continue
        for index, item_id in enumerate(items):
            slot = index if lane_index % 2 == 0 else len(items) - 1 - index
            x = round(left + (right - left) * slot / (len(items) - 1))
            positions[item_id] = (x, 235 + lane_index * 220)
    return positions, {
        "width": width,
        "height": max(920, 430 + max(0, len(lanes) - 1) * 220),
    }


def _semantic_lanes(
    ordered: Sequence[str],
    entity_by_id: Mapping[str, Mapping[str, Any]],
    groups: Sequence[Mapping[str, Any]],
) -> Tuple[Dict[str, str], List[str]]:
    lane_by_entity: Dict[str, str] = {}
    for group in groups:
        for member in group.get("members", []):
            lane_by_entity.setdefault(str(member), str(group["id"]))
    for item_id in ordered:
        lane_by_entity.setdefault(item_id, str(entity_by_id[item_id].get("role") or "neutral"))
    lanes: List[str] = []
    for item_id in ordered:
        lane = lane_by_entity[item_id]
        if lane not in lanes:
            lanes.append(lane)
    return lane_by_entity, lanes


def _compare_layout(ordered: Sequence[str]) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    split = max(1, math.ceil(len(ordered) / 2))
    positions = {}
    for index, item_id in enumerate(ordered):
        column = 0 if index < split else 1
        row = index if column == 0 else index - split
        positions[item_id] = (130 + column * 520, 150 + row * 170 + column * 28)
    return positions, {"width": 1040, "height": max(720, 300 + max(0, split - 1) * 170)}


def _grid_layout(
    ordered: Sequence[str],
    *,
    columns: int,
    x: int,
    y: int,
    x_gap: int,
    y_gap: int,
    canvas_width: int,
) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    positions = {
        item_id: (x + (index % columns) * x_gap, y + (index // columns) * y_gap)
        for index, item_id in enumerate(ordered)
    }
    rows = max(1, math.ceil(len(ordered) / columns))
    return positions, {"width": canvas_width, "height": max(700, y + 160 + (rows - 1) * y_gap)}


def _radial_layout(
    ordered: Sequence[str],
    relations: Sequence[Mapping[str, Any]],
    *,
    hub: bool,
    elliptical: bool = False,
) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    width = 1120 if hub else (1180 if elliptical else 1060)
    height = 760 if hub else (700 if elliptical else 820)
    center = (width // 2 - 110, height // 2 - 54)
    positions: Dict[str, Tuple[int, int]] = {}
    ring = list(ordered)
    if hub and ring:
        degree = defaultdict(int)
        for relation in relations:
            degree[str(relation["from"])] += 1
            degree[str(relation["to"])] += 1
        hub_id = max(ring, key=lambda item_id: (degree[item_id], -ring.index(item_id)))
        positions[hub_id] = center
        ring = [item_id for item_id in ring if item_id != hub_id]
    radius_x = 390 if elliptical else (330 if hub else 350)
    radius_y = 215 if elliptical else (245 if hub else 295)
    for index, item_id in enumerate(ring):
        angle = -math.pi / 2 + (2 * math.pi * index / max(1, len(ring)))
        positions[item_id] = (
            round(center[0] + radius_x * math.cos(angle)),
            round(center[1] + radius_y * math.sin(angle)),
        )
    return positions, {"width": width, "height": height}


def _funnel_layout(ordered: Sequence[str]) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    positions = {
        item_id: (130 + index * 95, 115 + index * 155)
        for index, item_id in enumerate(ordered)
    }
    return positions, {"width": 920, "height": max(720, 265 + max(0, len(ordered) - 1) * 155)}


def _er_layout(
    ordered: Sequence[str], relations: Sequence[Mapping[str, Any]]
) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    degree = defaultdict(int)
    for relation in relations:
        degree[str(relation["from"])] += 1
        degree[str(relation["to"])] += 1
    ranked = sorted(ordered, key=lambda item_id: (-degree[item_id], ordered.index(item_id)))
    return _grid_layout(ranked, columns=3, x=75, y=175, x_gap=305, y_gap=190, canvas_width=1080)


def _agent_memory_layout(
    ordered: Sequence[str], entity_by_id: Mapping[str, Mapping[str, Any]]
) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    columns = {"left": [], "core": [], "memory": []}
    for item_id in ordered:
        role = str(entity_by_id[item_id].get("role") or "neutral")
        if role == "memory":
            columns["memory"].append(item_id)
        elif role in {"agent", "process", "tool"}:
            columns["core"].append(item_id)
        else:
            columns["left"].append(item_id)
    positions = {}
    for key, x in (("left", 80), ("core", 410), ("memory", 750)):
        for index, item_id in enumerate(columns[key]):
            positions[item_id] = (x, 155 + index * 175)
    return positions, {"width": 1080, "height": max(720, 305 + max((len(items) for items in columns.values()), default=1) * 175)}


def _agent_loop_layout(
    ordered: Sequence[str],
    entity_by_id: Mapping[str, Mapping[str, Any]],
    groups: Sequence[Mapping[str, Any]],
    relations: Sequence[Mapping[str, Any]],
) -> Tuple[Dict[str, Tuple[int, int]], Dict[str, int]]:
    """Place a trigger, cognitive loop, and three supporting agent domains."""

    zones = _agent_loop_zones(ordered, entity_by_id, groups)
    decision_capable = set(zones["core"]) | set(zones["safety"])
    decision_ids = _agent_loop_decision_ids(relations) & decision_capable

    positions: Dict[str, Tuple[int, int]] = {}
    _place_horizontal(positions, zones["trigger"], 210, 1210, 175)

    core_head = zones["core"][:3]
    core_tail = zones["core"][3:]
    _place_horizontal(positions, core_head, 90, 810, 365)
    core_tail_rows = _pack_agent_loop_rows(
        core_tail,
        lambda item_id: 320 if item_id in decision_ids else 220,
        max_items=3,
        available_width=920,
    )
    for row, row_items in enumerate(core_tail_rows):
        left, right_edge = (560, 1480) if len(row_items) == 3 else (790, 1400)
        widths = [320 if item_id in decision_ids else 220 for item_id in row_items]
        if sum(widths) + max(0, len(widths) - 1) * 24 > right_edge - left:
            left, right_edge = 560, 1480
        _place_horizontal_sized(positions, row_items, widths, left, right_edge, 535 + row * 150)

    core_row_count = len(core_tail_rows)
    core_bottom = 481 if not core_tail_rows else 535 + (core_row_count - 1) * 150 + 116
    corridor_bottom = _agent_loop_corridor_bottom(zones, relations, core_bottom)
    support_y = max(
        790 + max(0, core_row_count - 1) * 150,
        corridor_bottom + 48,
    )
    for index, item_id in enumerate(zones["memory"]):
        positions[item_id] = (55, support_y + index * 150)
    safety_rows = _pack_agent_loop_rows(
        zones["safety"],
        lambda item_id: 320 if item_id in decision_ids else 210,
        max_items=4,
        available_width=960,
    )
    for row, row_items in enumerate(safety_rows):
        _place_horizontal_sized(
            positions,
            row_items,
            [320 if item_id in decision_ids else 210 for item_id in row_items],
            330,
            1290,
            support_y + row * 150,
        )
    for index, item_id in enumerate(zones["tools"]):
        positions[item_id] = (1360, support_y - 30 + index * 150)

    content_bottom = max((y + 116 for _, y in positions.values()), default=116)
    return positions, {"width": 1640, "height": max(1240, content_bottom + 42)}


def _agent_loop_decision_ids(relations: Sequence[Mapping[str, Any]]) -> set[str]:
    conditional_outgoing: Dict[str, int] = defaultdict(int)
    for relation in relations:
        if relation.get("condition"):
            conditional_outgoing[str(relation["from"])] += 1
    return {item_id for item_id, count in conditional_outgoing.items() if count >= 2}


def _pack_agent_loop_rows(
    items: Sequence[str],
    width_for: Any,
    *,
    max_items: int,
    available_width: int,
    min_gap: int = 24,
) -> List[List[str]]:
    rows: List[List[str]] = []
    current: List[str] = []
    current_width = 0
    for item_id in items:
        item_width = int(width_for(item_id))
        candidate_width = current_width + item_width + (min_gap if current else 0)
        if current and (len(current) >= max_items or candidate_width > available_width):
            rows.append(current)
            current = []
            current_width = 0
            candidate_width = item_width
        current.append(item_id)
        current_width = candidate_width
    if current:
        rows.append(current)
    return rows


def _agent_loop_corridor_bottom(
    zones: Mapping[str, Sequence[str]],
    relations: Sequence[Mapping[str, Any]],
    core_bottom: int,
) -> int:
    zone_by_entity = {
        item_id: zone
        for zone, item_ids in zones.items()
        for item_id in item_ids
    }
    lane_counts: Dict[Tuple[str, str], int] = defaultdict(int)
    for relation in relations:
        source_zone = zone_by_entity[str(relation["from"])]
        target_zone = zone_by_entity[str(relation["to"])]
        if source_zone == "core" and target_zone == "core" and relation.get("kind") == "feedback":
            lane_counts[("core", "feedback")] += 1
        elif source_zone == "core" and target_zone in {"memory", "safety", "tools"}:
            lane_counts[(source_zone, target_zone)] += 1
        elif source_zone == "tools" and target_zone == "core":
            lane_counts[(source_zone, target_zone)] += 1
        elif source_zone in {"memory", "safety"} and target_zone == "core":
            lane_counts[(source_zone, target_zone)] += 1

    corridor_bottom = core_bottom
    for key, count in lane_counts.items():
        if not count:
            continue
        base = 38 if key == ("core", "feedback") else (20 if key == ("tools", "core") else 30)
        corridor_bottom = max(corridor_bottom, core_bottom + base + (count - 1) * 12)
    return corridor_bottom


def _agent_loop_zones(
    ordered: Sequence[str],
    entity_by_id: Mapping[str, Mapping[str, Any]],
    groups: Sequence[Mapping[str, Any]],
) -> Dict[str, List[str]]:
    group_zones = {
        "trigger": "trigger",
        "input": "trigger",
        "source": "trigger",
        "agent-loop": "core",
        "cognitive-core": "core",
        "reasoning-loop": "core",
        "runtime": "core",
        "memory": "memory",
        "safety": "safety",
        "guardrail": "safety",
        "policy": "safety",
        "tool-execution": "tools",
        "tooling": "tools",
        "tools": "tools",
    }
    zone_by_entity: Dict[str, str] = {}
    for group in groups:
        zone = group_zones.get(str(group.get("kind") or ""))
        if zone is None:
            continue
        for member in group.get("members", []):
            zone_by_entity.setdefault(str(member), zone)

    zones: Dict[str, List[str]] = {
        "trigger": [],
        "core": [],
        "memory": [],
        "safety": [],
        "tools": [],
    }
    role_zones = {
        "actor": "trigger",
        "source": "trigger",
        "memory": "memory",
        "risk": "safety",
        "tool": "tools",
    }
    for item_id in ordered:
        role = str(entity_by_id[item_id].get("role") or "neutral")
        zones[zone_by_entity.get(item_id, role_zones.get(role, "core"))].append(item_id)
    return zones


def _place_horizontal(
    positions: Dict[str, Tuple[int, int]],
    items: Sequence[str],
    left: int,
    right: int,
    y: int,
) -> None:
    if not items:
        return
    if len(items) == 1:
        positions[items[0]] = ((left + right) // 2, y)
        return
    for index, item_id in enumerate(items):
        x = round(left + (right - left) * index / (len(items) - 1))
        positions[item_id] = (x, y)


def _place_horizontal_sized(
    positions: Dict[str, Tuple[int, int]],
    items: Sequence[str],
    widths: Sequence[int],
    left: int,
    right_edge: int,
    y: int,
) -> None:
    if not items:
        return
    if len(items) == 1:
        positions[items[0]] = (left + (right_edge - left - int(widths[0])) // 2, y)
        return
    gap = (right_edge - left - sum(int(width) for width in widths)) / (len(items) - 1)
    x = float(left)
    for item_id, width in zip(items, widths):
        positions[item_id] = (round(x), y)
        x += int(width) + gap


def _compile_entity(entity: Mapping[str, Any], position: Tuple[int, int], icon_system: str, step: int) -> Dict[str, Any]:
    role = str(entity.get("role") or "neutral")
    icon, resolution = _resolve_icon_for_entity(entity, icon_system)
    compiled = {
        "id": str(entity["id"]),
        "label": str(entity.get("label") or entity["id"]),
        "caption": str(entity.get("description") or entity.get("kind") or ""),
        "position": [position[0], position[1]],
        "size": [220, 108],
        "role": role,
        "icon": icon,
        "semantic_kind": str(entity.get("kind") or "component"),
        "icon_resolution": resolution,
        "importance": str(entity.get("importance") or "supporting"),
        "step": step,
        "effect": {"preset": "icon-performance"},
    }
    if entity.get("state") is not None:
        compiled["state"] = deepcopy(entity["state"])
    return compiled


def _icon_for_entity(entity: Mapping[str, Any], icon_system: str) -> str:
    return _resolve_icon_for_entity(entity, icon_system)[0]


def _resolve_icon_for_entity(entity: Mapping[str, Any], icon_system: str) -> Tuple[str, str]:
    kind = str(entity.get("kind") or "")
    role = str(entity.get("role") or "neutral")
    candidate = _KIND_ALIASES.get(kind, kind)
    if icon_system == "diagram-core-v1":
        if candidate in DIAGRAM_CORE_ICONS:
            return candidate, "alias" if candidate != kind else "exact"
        return _ROLE_FALLBACK.get(role, "server"), "role-fallback"
    if icon_system == "illustrated":
        if candidate in set(illustrated_icon_ids()):
            return candidate, "alias" if candidate != kind else "exact"
        return _V2_ROLE_FALLBACK.get(role, "agent"), "role-fallback"
    if candidate in LEGACY_ICONS:
        return candidate, "alias" if candidate != kind else "exact"
    return _LEGACY_ROLE_FALLBACK.get(role, "file"), "role-fallback"


def _flow_relation_context(flows: Sequence[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    context: Dict[str, Dict[str, Any]] = {}
    importance_order = {"primary": 0, "supporting": 1, "context": 2}
    for flow_index, flow in enumerate(flows):
        candidate = {
            "flow_id": str(flow["id"]),
            "importance": str(flow.get("importance") or "supporting"),
            "repeat": str(flow.get("repeat") or "once"),
            "flow_index": flow_index,
        }
        for step, relation_id in enumerate(flow.get("relation_ids", []), start=1):
            relation_key = str(relation_id)
            item = dict(candidate, step=step)
            existing = context.get(relation_key)
            if existing is None or (
                importance_order[item["importance"]], item["flow_index"]
            ) < (
                importance_order[existing["importance"]], existing["flow_index"]
            ):
                if existing is not None and existing["repeat"] == "loop":
                    item["repeat"] = "loop"
                context[relation_key] = item
            elif item["repeat"] == "loop":
                existing["repeat"] = "loop"
    return context


def _compile_relation(
    relation: Mapping[str, Any], step: int, flow: Mapping[str, Any] | None = None
) -> Dict[str, Any]:
    importance = str(relation.get("importance") or "supporting")
    flow_importance = str(flow.get("importance")) if flow else importance
    repeat = str(flow.get("repeat")) if flow else "once"
    if repeat == "loop":
        effect = "stream-flow"
    else:
        effect = "packet-flow" if flow_importance in {"primary", "supporting"} else "draw"
    compiled = {
        "from": str(relation["from"]),
        "to": str(relation["to"]),
        "label": str(relation.get("label") or ""),
        "role": _relation_role(str(relation.get("kind") or ""), importance),
        "direction": str(relation.get("direction") or "forward"),
        "route": "straight",
        "step": int(flow.get("step")) if flow else step,
        "semantic_relation_id": str(relation["id"]),
        "semantic_kind": str(relation.get("kind") or "relation"),
        "importance": importance,
        "effect": {"preset": effect, "particle_count": 1},
    }
    for field in ("condition", "protocol"):
        if relation.get(field) is not None:
            compiled[field] = str(relation[field])
    if flow:
        compiled["flow_id"] = str(flow["flow_id"])
        compiled["flow_importance"] = flow_importance
        compiled["flow_repeat"] = repeat
    return compiled


def _apply_layered_loop_presentation(
    edges: Sequence[Dict[str, Any]],
    nodes: Sequence[Mapping[str, Any]],
    lane_by_entity: Mapping[str, str],
    lanes: Sequence[str],
    canvas: Dict[str, int],
) -> None:
    """Keep layered-loop transfers legible without overlapping reciprocal paths.

    Reciprocal relations between adjacent layers use independent anchors and
    parallel gutter channels. Same-layer feedback loops travel outside the node
    row instead of crossing the primary path. Only unmatched upward transfers
    retain the outer-canvas fallback used by older layered-loop diagrams.
    """

    node_by_id = {str(node["id"]): node for node in nodes}
    lane_index = {lane: index for index, lane in enumerate(lanes)}
    indexed_edges = list(enumerate(edges))
    directions = {(str(edge["from"]), str(edge["to"])) for edge in edges}
    paired_adjacent = {
        index
        for index, edge in indexed_edges
        if (str(edge["to"]), str(edge["from"])) in directions
        and abs(
            lane_index[lane_by_entity[str(edge["from"])]]
            - lane_index[lane_by_entity[str(edge["to"])]]
        ) == 1
    }

    anchor_requests: Dict[Tuple[str, str], List[Tuple[int, str, float, int]]] = defaultdict(list)
    boundary_edges: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    for index, edge in indexed_edges:
        if index not in paired_adjacent:
            continue
        source_id = str(edge["from"])
        target_id = str(edge["to"])
        source_lane = lane_index[lane_by_entity[source_id]]
        target_lane = lane_index[lane_by_entity[target_id]]
        source_side = "bottom" if source_lane < target_lane else "top"
        target_side = "top" if source_lane < target_lane else "bottom"
        source_center = _node_center_x(node_by_id[source_id])
        target_center = _node_center_x(node_by_id[target_id])
        anchor_requests[(source_id, source_side)].append((index, "source", target_center, 0))
        anchor_requests[(target_id, target_side)].append((index, "target", source_center, 1))
        boundary_edges[(min(source_lane, target_lane), max(source_lane, target_lane))].append(index)

    anchors: Dict[Tuple[int, str], List[int]] = {}
    for (node_id, side), requests in anchor_requests.items():
        node = node_by_id[node_id]
        x, y = (int(value) for value in node["position"])
        width, height = (int(value) for value in node["size"])
        ordered_requests = sorted(requests, key=lambda item: (item[2], item[3], item[0]))
        count = len(ordered_requests)
        center = x + width / 2
        span = min(width * 0.60, max(36, (count - 1) * 26))
        left = center - span / 2
        right = center + span / 2
        for slot, (edge_index, endpoint, _, _) in enumerate(ordered_requests):
            anchor_x = round(center) if count == 1 else round(left + (right - left) * slot / (count - 1))
            anchor_y = y if side == "top" else y + height
            anchors[(edge_index, endpoint)] = [anchor_x, anchor_y]

    corridors: Dict[int, int] = {}
    for (upper_lane, lower_lane), edge_indices in boundary_edges.items():
        upper_bottom = max(
            int(node["position"][1]) + int(node["size"][1])
            for node in nodes
            if lane_index[lane_by_entity[str(node["id"])]] == upper_lane
        )
        lower_top = min(
            int(node["position"][1])
            for node in nodes
            if lane_index[lane_by_entity[str(node["id"])]] == lower_lane
        )

        def boundary_order(edge_index: int) -> Tuple[float, int, int]:
            edge = edges[edge_index]
            source_lane = lane_index[lane_by_entity[str(edge["from"])]]
            lower_id = str(edge["to"]) if source_lane == upper_lane else str(edge["from"])
            direction_rank = 0 if source_lane == upper_lane else 1
            return (_node_center_x(node_by_id[lower_id]), direction_rank, edge_index)

        ordered_indices = sorted(edge_indices, key=boundary_order)
        first = upper_bottom + 38
        last = lower_top - 20
        if first > last:
            first = last = (upper_bottom + lower_top) // 2
        for slot, edge_index in enumerate(ordered_indices):
            corridor = (first + last) // 2 if len(ordered_indices) == 1 else round(
                first + (last - first) * slot / (len(ordered_indices) - 1)
            )
            corridors[edge_index] = corridor

    lane_spacing = 12
    outer_margin = 36
    bottom_margin = 30
    upward_count = sum(
        1
        for index, edge in indexed_edges
        if index not in paired_adjacent
        and lane_index[lane_by_entity[str(edge["from"])]]
        > lane_index[lane_by_entity[str(edge["to"])]]
    )
    canvas["height"] += max(0, upward_count - 1) * lane_spacing
    upward_lane = 0
    same_lane_feedback: Dict[str, int] = defaultdict(int)
    for index, edge in indexed_edges:
        if edge.get("flow_repeat") == "loop" and edge.get("flow_importance") != "primary":
            edge.pop("step", None)
        source_id = str(edge["from"])
        target_id = str(edge["to"])
        source_lane = lane_index[lane_by_entity[source_id]]
        target_lane = lane_index[lane_by_entity[target_id]]
        source = node_by_id[source_id]
        target = node_by_id[target_id]

        if index in paired_adjacent:
            source_anchor = anchors[(index, "source")]
            target_anchor = anchors[(index, "target")]
            corridor = corridors[index]
            edge["route"] = "points"
            edge["points"] = [
                source_anchor,
                [source_anchor[0], corridor],
                [target_anchor[0], corridor],
                target_anchor,
            ]
            continue

        if source_lane == target_lane:
            is_feedback = edge.get("semantic_kind") == "feedback"
            if not is_feedback:
                edge["route"] = "straight"
                continue
            feedback_slot = same_lane_feedback[lane_by_entity[source_id]]
            same_lane_feedback[lane_by_entity[source_id]] += 1
            source_anchor = list(_node_anchor(source, "bottom"))
            target_anchor = list(_node_anchor(target, "bottom"))
            row_bottom = max(source_anchor[1], target_anchor[1])
            corridor = row_bottom + 18 + feedback_slot * lane_spacing
            edge["route"] = "points"
            edge["points"] = [
                source_anchor,
                [source_anchor[0], corridor],
                [target_anchor[0], corridor],
                target_anchor,
            ]
            continue

        sx, sy = _node_anchor(source, "bottom")
        tx, ty = _node_anchor(target, "top")
        if source_lane < target_lane and target_lane - source_lane == 1 and sx == tx:
            edge["route"] = "straight"
            continue
        edge["route"] = "points"
        if source_lane < target_lane:
            if target_lane - source_lane > 1:
                first_gutter = (
                    sy
                    + min(
                        int(node["position"][1])
                        for node in nodes
                        if lane_index[lane_by_entity[str(node["id"])]] == source_lane + 1
                    )
                ) // 2
                right_corridor = int(canvas["width"]) - outer_margin
                edge["points"] = [
                    [sx, sy],
                    [sx, first_gutter],
                    [right_corridor, first_gutter],
                    [right_corridor, ty],
                    [tx, ty],
                ]
                continue
            corridor_y = (sy + ty) // 2
            edge["points"] = [[sx, sy], [sx, corridor_y], [tx, corridor_y], [tx, ty]]
            continue

        bottom_corridor = int(canvas["height"]) - bottom_margin - upward_lane * lane_spacing
        left_corridor = outer_margin
        upward_lane += 1
        target_left = [
            int(target["position"][0]),
            int(target["position"][1]) + int(target["size"][1]) // 2,
        ]
        edge["points"] = [
            [sx, sy],
            [sx, bottom_corridor],
            [left_corridor, bottom_corridor],
            [left_corridor, target_left[1]],
            target_left,
        ]


def _node_center_x(node: Mapping[str, Any]) -> float:
    return float(node["position"][0]) + float(node["size"][0]) / 2


def _apply_agent_loop_presentation(
    edges: Sequence[Dict[str, Any]],
    nodes: Sequence[Mapping[str, Any]],
    zone_by_entity: Mapping[str, str],
) -> None:
    node_by_id = {str(node["id"]): node for node in nodes}
    conditional_outgoing: Dict[str, int] = defaultdict(int)
    for edge in edges:
        if edge.get("condition"):
            conditional_outgoing[str(edge["from"])] += 1
    for node in nodes:
        node.pop("step", None)
        zone = zone_by_entity[str(node["id"])]
        node["size"] = [210, 116] if zone == "safety" else [220, 116]
        if zone in {"core", "safety"} and conditional_outgoing[str(node["id"])] >= 2:
            node["shape"] = "decision"
            node["size"] = [320, 116]

    core_bottom = max(
        (
            int(node["position"][1]) + int(node["size"][1])
            for node in nodes
            if zone_by_entity[str(node["id"])] == "core"
        ),
        default=660,
    )

    lane_counts: Dict[Tuple[str, str], int] = defaultdict(int)
    for edge in edges:
        edge.pop("step", None)
        source = node_by_id[str(edge["from"])]
        target = node_by_id[str(edge["to"])]
        source_zone = zone_by_entity[str(edge["from"])]
        target_zone = zone_by_entity[str(edge["to"])]
        sx, sy = _node_anchor(source, "bottom")
        tx, ty = _node_anchor(target, "top")
        if source["position"][1] == target["position"][1] or source["position"][0] == target["position"][0]:
            edge["route"] = "straight"
            continue
        if source_zone == "trigger" and target_zone == "core":
            edge["route"] = "points"
            edge["points"] = [[sx, sy], [sx, 315], [tx, 315], [tx, ty]]
            continue
        if (
            source_zone == "core"
            and target_zone == "core"
            and target["position"][0] < source["position"][0]
            and edge.get("semantic_kind") == "feedback"
        ):
            lane = lane_counts[("core", "feedback")]
            lane_counts[("core", "feedback")] += 1
            corridor = core_bottom + 38 + lane * 12
            edge["route"] = "points"
            edge["points"] = [[sx, sy], [sx, corridor], [tx, corridor], [tx, ty + int(target["size"][1])]]
            continue
        if source_zone == "core" and target_zone in {"memory", "safety", "tools"}:
            lane = lane_counts[(source_zone, target_zone)]
            lane_counts[(source_zone, target_zone)] += 1
            corridor = core_bottom + 30 + lane * 12
            edge["route"] = "points"
            edge["points"] = [[sx, sy], [sx, corridor], [tx, corridor], [tx, ty]]
            continue
        if source_zone == "tools" and target_zone == "core":
            lane = lane_counts[(source_zone, target_zone)]
            lane_counts[(source_zone, target_zone)] += 1
            source_top = _node_anchor(source, "top")
            target_right = (
                int(target["position"][0]) + int(target["size"][0]),
                int(target["position"][1]) + int(target["size"][1]) // 2,
            )
            corridor_y = core_bottom + 20 + lane * 12
            corridor_x = 1600 - lane * 14
            edge["route"] = "points"
            edge["points"] = [
                [source_top[0], source_top[1]],
                [source_top[0], corridor_y],
                [corridor_x, corridor_y],
                [corridor_x, target_right[1]],
                [target_right[0], target_right[1]],
            ]
            continue
        if source_zone in {"memory", "safety"} and target_zone == "core":
            lane = lane_counts[(source_zone, target_zone)]
            lane_counts[(source_zone, target_zone)] += 1
            corridor = core_bottom + 30 + lane * 12
            edge["route"] = "points"
            edge["points"] = [[sx, source["position"][1]], [sx, corridor], [tx, corridor], [tx, ty + int(target["size"][1])]]
            continue
        edge["route"] = "orthogonal"


def _node_anchor(node: Mapping[str, Any], side: str) -> Tuple[int, int]:
    x, y = int(node["position"][0]), int(node["position"][1])
    width, height = int(node["size"][0]), int(node["size"][1])
    return (x + width // 2, y + height) if side == "bottom" else (x + width // 2, y)


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
        compiled_group = {
            "id": str(group["id"]),
            "label": str(group.get("label") or group["id"]),
            "bounds": [left, top, right - left, bottom - top],
            "role": "neutral",
            "semantic_kind": str(group.get("kind") or "group"),
            "importance": str(group.get("importance") or "supporting"),
            "members": [str(member) for member in group.get("members", [])],
            "effect": {"preset": "border-scan"},
        }
        if group.get("parent") is not None:
            compiled_group["parent"] = str(group["parent"])
        compiled.append(compiled_group)
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
        "edge": {"preset": "packet-flow"},
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
