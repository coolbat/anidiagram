"""DiagramScript schema validation and IR compilation."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set

from .composition import DIAGRAM_CORE_ICONS, ICON_SYSTEMS, LAYOUTS, MOTIONS, STYLES
from .edge_motion import KNOWN_EDGE_MOTION
from .icon_system import canonical_icon_system_id, icon_system_version
from .illustrated_registry import illustrated_icon_ids
from .localization import resolve_locale
from .repository_evidence import EvidenceError, verify_evidence
from .model import Bounds, Canvas, Edge, EffectConfig, Group, Motion, MotionPolicy, Node, Point, Scene, SceneMotion, Style, Title


SUPPORTED_VERSIONS = ("0.1", "0.2", "0.3", "0.4")
KNOWN_ROLES = {
    "actor",
    "source",
    "process",
    "agent",
    "memory",
    "tool",
    "output",
    "risk",
    "neutral",
}
KNOWN_ROUTES = {"curved", "straight", "hv", "vh", "orthogonal", "points"}
KNOWN_EDGE_DIRECTIONS = {"forward", "bidirectional", "undirected"}
KNOWN_MOTION_PROFILES = {"off", "subtle", "normal", "expressive", "teaching", "runtime-loop", "showcase-v1"}
KNOWN_MOTION_SEQUENCES = {"simultaneous", "step-stagger", "layered", "staged", "loop"}
KNOWN_MOTION_EASES = {"linear", "calm", "snappy", "back-out", "elastic", "spring"}
KNOWN_NODE_MOTION = {
    "none",
    "fade",
    "float",
    "glow-breathe",
    "pop",
    "pulse",
    "ripple",
    "status-blink",
    "icon-pulse",
    "icon-breathe",
    "icon-semantic",
    "icon-performance",
    "micro-icon",
}
KNOWN_GROUP_MOTION = {"none", "static", "soft-reveal", "marching-ants", "border-scan", "corner-pulse"}
KNOWN_REDUCED_MOTION = {"static", "subtle", "pause"}
KNOWN_TITLE_MOTION = {"none", "fade", "breathe", "handwrite-reveal", "highlight-sweep"}
KNOWN_ICONS = {"database", "file", "folder", "api", "cloud", "search", "shield", "agent", "operator", "token", "memory", "tool", "output"}
KNOWN_NODE_SHAPES = {"rect", "decision"}
KNOWN_MOTION_POLICY_PROFILES = {"unrestricted", "readable", "focused", "expressive", "readable-runtime"}
KNOWN_PULSE_MODES = {"all", "rotate"}
KNOWN_MOTION_AREAS = {"auto", "micro", "small", "medium", "unrestricted"}
KNOWN_ICON_RESOLUTIONS = {"exact", "alias", "role-fallback"}
KNOWN_IMPORTANCE = {"primary", "supporting", "context"}
KNOWN_FLOW_REPEAT = {"once", "loop", "event-driven"}
KNOWN_RESOLUTION_SOURCES = {"explicit", "model", "default", "fallback", "legacy"}
SEMANTIC_KIND_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str
    code: str = "invalid"
    severity: str = "error"

    def to_dict(self) -> Dict[str, str]:
        return {
            "path": self.path,
            "message": self.message,
            "code": self.code,
            "severity": self.severity,
        }


class DiagramScriptValidationError(ValueError):
    """Raised when a DiagramScript document cannot compile to a Scene."""

    def __init__(self, issues: Iterable[ValidationIssue]):
        self.issues = list(issues)
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in self.issues)
        super().__init__(f"DiagramScript validation failed: {details}")

    def to_result(self) -> Dict[str, Any]:
        return {
            "code": "diagram_script_validation_failed",
            "issues": [issue.to_dict() for issue in self.issues],
        }


def compile_scene(data: Dict[str, Any], *, repo_root=None) -> Scene:
    """Validate DiagramScript JSON and compile it to the AniDiagram IR."""

    issues: List[ValidationIssue] = []
    if not isinstance(data, dict):
        raise DiagramScriptValidationError([ValidationIssue("$", "expected a JSON object", "type")])

    version = _string(data, "version", "$.version", issues, required=True)
    if version and version not in SUPPORTED_VERSIONS:
        issues.append(
            ValidationIssue(
                "$.version",
                f"unsupported version {version!r}; supported versions: {', '.join(SUPPORTED_VERSIONS)}",
                "unsupported_version",
            )
        )

    canvas = _parse_canvas(data.get("canvas", {}), "$.canvas", issues)
    title = _parse_title(data.get("title", {}), "$.title", issues)
    style = Style(name=_string(data, "style", "$.style", issues, required=False))
    raw_icon_system = (
        _enum(data, "icon_system", "$.icon_system", ICON_SYSTEMS, issues, default="diagram-core-v1")
        if version == "0.4"
        else None
    )
    icon_system = canonical_icon_system_id(raw_icon_system) if raw_icon_system is not None else None
    composition_policy = _string(data, "composition_policy", "$.composition_policy", issues, required=False)
    if composition_policy is not None and composition_policy != "composition-v1":
        issues.append(
            ValidationIssue(
                "$.composition_policy",
                "expected 'composition-v1'",
                "enum",
            )
        )
    if composition_policy == "composition-v1":
        for required_field in ("icon_system", "style", "motion", "resolved_presentation"):
            if required_field not in data:
                issues.append(
                    ValidationIssue(
                        f"$.{required_field}",
                        "is required for composition-v1",
                        "required",
                    )
                )
    resolved_presentation = data.get("resolved_presentation", {})
    if not isinstance(resolved_presentation, dict):
        issues.append(ValidationIssue("$.resolved_presentation", "expected an object", "type"))
        resolved_presentation = {}
    motion = _parse_scene_motion(data.get("motion", {}), "$.motion", issues)
    motion_policy = _parse_motion_policy(data.get("motion_policy"), "$.motion_policy", issues)
    groups = _parse_groups(data.get("groups", []), "$.groups", issues, canvas)
    allowed_icons = _icons_for_system(icon_system)
    nodes = _parse_nodes(data.get("nodes"), "$.nodes", issues, canvas, allowed_icons)
    node_ids = {node.node_id for node in nodes}
    edges = _parse_edges(data.get("edges", []), "$.edges", node_ids, issues)
    requested_locale = _optional_enum(data, "locale", "$.locale", {"auto", "en", "zh-CN"}, issues) or "auto"
    locale = resolve_locale(
        requested_locale,
        (
            title.text,
            title.subtitle,
            *(value for node in nodes for value in (node.label, node.caption)),
            *(edge.label for edge in edges),
            *(group.label for group in groups),
        ),
    )
    preset = _string(data, "preset", "$.preset", issues, required=False)
    layout = _optional_enum(data, "layout", "$.layout", LAYOUTS, issues)
    _validate_resolved_presentation(
        resolved_presentation,
        icon_system=icon_system,
        style=style.name,
        layout=layout,
        motion=motion.profile,
        composition_policy=composition_policy,
        issues=issues,
    )

    if issues:
        raise DiagramScriptValidationError(issues)

    type_semantics = {}
    if "type_semantics" in data:
        from .type_semantics import validate_compiled_type
        try:
            if version != "0.4":
                raise ValueError("typed semantics require DiagramScript 0.4")
            validate_compiled_type(data["type_semantics"], nodes, edges, groups)
            type_semantics = dict(data["type_semantics"])
        except ValueError as error:
            raise DiagramScriptValidationError([ValidationIssue("$.type_semantics", str(error))]) from error
    reader = {}
    if "reader" in data:
        from .reader import validate_reader
        try:
            if version != "0.4":
                raise ValueError("reader requires DiagramScript 0.4")
            validate_reader(data["reader"], data["nodes"], data.get("edges", []))
            reader = dict(data["reader"])
        except ValueError as error:
            raise DiagramScriptValidationError([ValidationIssue("$.reader", str(error))]) from error
    source_evidence = {}
    if "evidence" in data:
        try:
            if version != "0.4":
                raise EvidenceError("evidence_version", "repository evidence requires DiagramScript 0.4")
            subject_ids = node_ids | {group.group_id for group in groups} | {
                edge.semantic_relation_id for edge in edges if edge.semantic_relation_id
            }
            source_evidence = verify_evidence(data["evidence"], repo_root, subject_ids)
        except EvidenceError as error:
            raise DiagramScriptValidationError([ValidationIssue("$.evidence", str(error), error.code)]) from error

    return Scene(
        version=version or SUPPORTED_VERSIONS[0],
        canvas=canvas,
        title=title,
        style=style,
        nodes=nodes,
        edges=edges,
        groups=groups,
        locale=locale,
        icon_system=icon_system,
        composition_policy=composition_policy,
        resolved_presentation=dict(resolved_presentation),
        motion=motion,
        motion_policy=motion_policy,
        preset=preset,
        layout=layout,
        source_evidence=source_evidence,
        reader=reader,
        type_semantics=type_semantics,
    )


def validate_scene(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return structured validation status without raising on invalid input."""

    try:
        scene = compile_scene(data)
    except DiagramScriptValidationError as exc:
        return {"ok": False, "error": exc.to_result()}
    return {"ok": True, "schema": {"name": "DiagramScript", "version": scene.version}, "stats": scene.stats()}


def _validate_resolved_presentation(
    resolved: Dict[str, Any],
    *,
    icon_system: Optional[str],
    style: Optional[str],
    layout: Optional[str],
    motion: str,
    composition_policy: Optional[str],
    issues: List[ValidationIssue],
) -> None:
    required = composition_policy == "composition-v1"
    actual = {
        "icon_system": icon_system,
        "style": style,
        "layout": layout,
        "motion": motion,
    }
    allowed_values = {
        "icon_system": ICON_SYSTEMS,
        "style": STYLES,
        "layout": LAYOUTS,
        "motion": MOTIONS,
    }
    for name, actual_value in actual.items():
        path = f"$.resolved_presentation.{name}"
        axis = resolved.get(name)
        if axis is None:
            if required:
                issues.append(ValidationIssue(path, "is required for composition-v1", "required"))
            continue
        if not isinstance(axis, dict):
            issues.append(ValidationIssue(path, "expected an object", "type"))
            continue
        unknown = sorted(set(axis) - {"value", "source", "version"})
        for field in unknown:
            issues.append(
                ValidationIssue(
                    f"{path}.{field}",
                    "unsupported resolved axis field",
                    "additional_property",
                )
            )
        value = axis.get("value")
        source = axis.get("source")
        if not isinstance(value, str) or not value:
            issues.append(ValidationIssue(f"{path}.value", "expected a non-empty string", "type"))
        else:
            resolved_value = canonical_icon_system_id(value) if name == "icon_system" else value
            canonical_allowed = (
                {canonical_icon_system_id(item) for item in allowed_values[name]}
                if name == "icon_system"
                else allowed_values[name]
            )
            if resolved_value not in canonical_allowed:
                issues.append(ValidationIssue(f"{path}.value", "is not a registered presentation value", "enum"))
            if actual_value is None and name != "layout":
                issues.append(
                    ValidationIssue(
                        f"{path}.value",
                        f"cannot be resolved without $.{name}",
                        "inconsistent_presentation",
                    )
                )
            elif actual_value is not None and resolved_value != actual_value:
                target = f"$.{name}"
                issues.append(
                    ValidationIssue(
                        f"{path}.value",
                        f"must match {target}",
                        "inconsistent_presentation",
                    )
                )
        if source not in KNOWN_RESOLUTION_SOURCES:
            issues.append(
                ValidationIssue(
                    f"{path}.source",
                    f"expected one of: {', '.join(sorted(KNOWN_RESOLUTION_SOURCES))}",
                    "enum",
                )
            )

    axis = resolved.get("icon_system")
    if isinstance(axis, dict):
        expected_version = icon_system_version(icon_system) if icon_system is not None else None
        declared_version = axis.get("version")
        if expected_version is not None and declared_version is not None and declared_version != expected_version:
            issues.append(
                ValidationIssue(
                    "$.resolved_presentation.icon_system.version",
                    f"version {declared_version!r} is not renderable by the current {icon_system} {expected_version} runtime",
                    "unsupported_icon_system_version",
                )
            )


def _parse_canvas(value: Any, path: str, issues: List[ValidationIssue]) -> Canvas:
    if value is None:
        return Canvas()
    if not isinstance(value, dict):
        issues.append(ValidationIssue(path, "expected an object", "type"))
        return Canvas()
    width = _positive_int(value, "width", f"{path}.width", issues, default=1200)
    height = _positive_int(value, "height", f"{path}.height", issues, default=720)
    return Canvas(width=width, height=height)


def _parse_title(value: Any, path: str, issues: List[ValidationIssue]) -> Title:
    if value is None:
        return Title()
    if not isinstance(value, dict):
        issues.append(ValidationIssue(path, "expected an object", "type"))
        return Title()
    return Title(
        text=_string(value, "text", f"{path}.text", issues, required=False) or "AniDiagram",
        subtitle=_string(value, "subtitle", f"{path}.subtitle", issues, required=False) or "",
    )


def _parse_scene_motion(value: Any, path: str, issues: List[ValidationIssue]) -> SceneMotion:
    if value is None:
        return _motion_defaults("expressive")
    if not isinstance(value, dict):
        issues.append(ValidationIssue(path, "expected an object", "type"))
        return _motion_defaults("expressive")
    profile = _enum(value, "profile", f"{path}.profile", KNOWN_MOTION_PROFILES, issues, default="expressive")
    defaults = _motion_defaults(profile)
    edge_effect = _effect_config(value.get("edge"), f"{path}.edge", KNOWN_EDGE_MOTION, issues, defaults.edge_effect)
    node_effect = _effect_config(value.get("node"), f"{path}.node", KNOWN_NODE_MOTION, issues, defaults.node_effect)
    group_effect = _effect_config(value.get("group"), f"{path}.group", KNOWN_GROUP_MOTION, issues, defaults.group_effect)
    title_effect = _effect_config(value.get("title"), f"{path}.title", KNOWN_TITLE_MOTION, issues, defaults.title_effect)
    return SceneMotion(
        profile=profile,
        sequence=_enum(value, "sequence", f"{path}.sequence", KNOWN_MOTION_SEQUENCES, issues, default=defaults.sequence),
        ease=_enum(value, "ease", f"{path}.ease", KNOWN_MOTION_EASES, issues, default=defaults.ease),
        stagger=_optional_number(value, "stagger", f"{path}.stagger", issues, positive=False, default=defaults.stagger),
        duration_scale=_optional_number(
            value,
            "duration_scale",
            f"{path}.duration_scale",
            issues,
            positive=True,
            default=defaults.duration_scale,
        ),
        intensity=_optional_number(value, "intensity", f"{path}.intensity", issues, positive=False, default=defaults.intensity),
        node=node_effect.preset,
        edge=edge_effect.preset,
        group=group_effect.preset,
        reduced_motion=_enum(
            value,
            "reduced_motion",
            f"{path}.reduced_motion",
            KNOWN_REDUCED_MOTION,
            issues,
            default=defaults.reduced_motion,
        ),
        edge_effect=edge_effect,
        node_effect=node_effect,
        group_effect=group_effect,
        title_effect=title_effect,
    )


def _motion_defaults(profile: str) -> SceneMotion:
    if profile == "off":
        return _scene_motion("off", "simultaneous", "linear", 0.0, 1.0, 0.0, "none", "none", "none", "none", "static")
    if profile == "subtle":
        return _scene_motion("subtle", "step-stagger", "calm", 0.08, 1.2, 0.55, "fade", "draw", "soft-reveal", "fade", "static")
    if profile == "normal":
        return _scene_motion("normal", "step-stagger", "calm", 0.12, 1.0, 1.0, "glow-breathe", "packet-flow", "marching-ants", "fade", "subtle")
    if profile == "expressive":
        return _scene_motion("expressive", "layered", "spring", 0.16, 0.9, 1.25, "pop", "packet-flow", "marching-ants", "highlight-sweep", "subtle")
    if profile == "teaching":
        return _scene_motion("teaching", "staged", "spring", 0.14, 0.95, 1.15, "icon-pulse", "packet-flow", "border-scan", "handwrite-reveal", "subtle")
    if profile == "runtime-loop":
        return _scene_motion("runtime-loop", "loop", "linear", 0.09, 1.0, 0.82, "icon-breathe", "packet-flow", "static", "breathe", "subtle")
    if profile == "showcase-v1":
        return _scene_motion("showcase-v1", "staged", "spring", 0.12, 1.0, 1.0, "icon-performance", "packet-flow", "border-scan", "highlight-sweep", "subtle")
    return SceneMotion()


def _parse_motion_policy(value: Any, path: str, issues: List[ValidationIssue]) -> MotionPolicy:
    if value is None:
        return MotionPolicy()
    if not isinstance(value, dict):
        issues.append(ValidationIssue(path, "expected an object", "type"))
        return MotionPolicy()
    profile = _enum(value, "profile", f"{path}.profile", KNOWN_MOTION_POLICY_PROFILES, issues, default="unrestricted")
    defaults = _motion_policy_defaults(profile)
    return MotionPolicy(
        profile=profile,
        motion_area=_enum(value, "motion_area", f"{path}.motion_area", KNOWN_MOTION_AREAS, issues, default=defaults.motion_area),
        max_active_flow_edges=_optional_non_negative_int(
            value, "max_active_flow_edges", f"{path}.max_active_flow_edges", issues, defaults.max_active_flow_edges
        ),
        max_particle_edges=_optional_non_negative_int(
            value, "max_particle_edges", f"{path}.max_particle_edges", issues, defaults.max_particle_edges
        ),
        particle_count_per_edge=_optional_non_negative_int(
            value, "particle_count_per_edge", f"{path}.particle_count_per_edge", issues, defaults.particle_count_per_edge
        ),
        flow_trail_count=_optional_non_negative_int(
            value, "flow_trail_count", f"{path}.flow_trail_count", issues, defaults.flow_trail_count
        ),
        max_active_pulse_nodes=_optional_non_negative_int(
            value, "max_active_pulse_nodes", f"{path}.max_active_pulse_nodes", issues, defaults.max_active_pulse_nodes
        ),
        pulse_mode=_enum(value, "pulse_mode", f"{path}.pulse_mode", KNOWN_PULSE_MODES, issues, default=defaults.pulse_mode),
        max_scanning_groups=_optional_non_negative_int(
            value, "max_scanning_groups", f"{path}.max_scanning_groups", issues, defaults.max_scanning_groups
        ),
    )


def _motion_policy_defaults(profile: str) -> MotionPolicy:
    if profile == "readable-runtime":
        return MotionPolicy(
            profile=profile,
            motion_area="micro",
            max_active_flow_edges=12,
            max_particle_edges=12,
            particle_count_per_edge=1,
            flow_trail_count=0,
            max_active_pulse_nodes=4,
            pulse_mode="rotate",
            max_scanning_groups=0,
        )
    if profile == "readable":
        return MotionPolicy(
            profile=profile,
            motion_area="small",
            max_active_flow_edges=3,
            max_particle_edges=2,
            particle_count_per_edge=1,
            flow_trail_count=1,
            max_active_pulse_nodes=1,
            pulse_mode="rotate",
            max_scanning_groups=0,
        )
    if profile == "focused":
        return MotionPolicy(
            profile=profile,
            motion_area="small",
            max_active_flow_edges=4,
            max_particle_edges=3,
            particle_count_per_edge=1,
            flow_trail_count=2,
            max_active_pulse_nodes=1,
            pulse_mode="rotate",
            max_scanning_groups=1,
        )
    if profile == "expressive":
        return MotionPolicy(
            profile=profile,
            motion_area="medium",
            max_active_flow_edges=8,
            max_particle_edges=5,
            particle_count_per_edge=2,
            flow_trail_count=3,
            max_active_pulse_nodes=3,
            pulse_mode="rotate",
            max_scanning_groups=2,
        )
    return MotionPolicy(profile=profile)


def _scene_motion(
    profile: str,
    sequence: str,
    ease: str,
    stagger: float,
    duration_scale: float,
    intensity: float,
    node: str,
    edge: str,
    group: str,
    title: str,
    reduced_motion: str,
) -> SceneMotion:
    return SceneMotion(
        profile=profile,
        sequence=sequence,
        ease=ease,
        stagger=stagger,
        duration_scale=duration_scale,
        intensity=intensity,
        node=node,
        edge=edge,
        group=group,
        reduced_motion=reduced_motion,
        node_effect=EffectConfig(preset=node),
        edge_effect=EffectConfig(preset=edge),
        group_effect=EffectConfig(preset=group),
        title_effect=EffectConfig(preset=title),
    )


def _effect_config(
    value: Any,
    path: str,
    allowed_presets: Set[str],
    issues: List[ValidationIssue],
    default: EffectConfig,
) -> EffectConfig:
    if value is None:
        return default
    if isinstance(value, str):
        if value not in allowed_presets:
            issues.append(ValidationIssue(path, f"expected one of: {', '.join(sorted(allowed_presets))}", "enum"))
            return default
        return EffectConfig(preset=value, explicit=True)
    if not isinstance(value, dict):
        issues.append(ValidationIssue(path, "expected a string or object", "type"))
        return default
    preset = value.get("preset", default.preset)
    if not isinstance(preset, str):
        issues.append(ValidationIssue(f"{path}.preset", "expected a string", "type"))
        preset = default.preset
    elif preset not in allowed_presets:
        issues.append(ValidationIssue(f"{path}.preset", f"expected one of: {', '.join(sorted(allowed_presets))}", "enum"))
        preset = default.preset
    for key in ("line", "particle", "trail", "entry", "accent", "icon", "icon_motion"):
        if key in value and value[key] is not None and not isinstance(value[key], (str, bool)):
            issues.append(ValidationIssue(f"{path}.{key}", "expected a string or boolean", "type"))
    trail = value.get("trail")
    return EffectConfig(
        preset=preset,
        explicit=bool(value),
        line=_optional_string_token(value, "line"),
        particle=_optional_string_token(value, "particle"),
        trail=str(trail).lower() if isinstance(trail, bool) else _optional_string_token(value, "trail"),
        particle_count=_optional_non_negative_int(value, "particle_count", f"{path}.particle_count", issues),
        trail_count=_optional_non_negative_int(value, "trail_count", f"{path}.trail_count", issues),
        entry=_optional_string_token(value, "entry"),
        accent=_optional_string_token(value, "accent"),
        icon=_optional_string_token(value, "icon"),
        icon_motion=_optional_string_token(value, "icon_motion"),
    )


def _optional_string_token(data: Dict[str, Any], key: str) -> Optional[str]:
    value = data.get(key)
    return value if isinstance(value, str) else None


def _parse_groups(value: Any, path: str, issues: List[ValidationIssue], canvas: Canvas) -> List[Group]:
    if value is None:
        return []
    if not isinstance(value, list):
        issues.append(ValidationIssue(path, "expected an array", "type"))
        return []

    groups: List[Group] = []
    seen: Set[str] = set()
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            issues.append(ValidationIssue(item_path, "expected an object", "type"))
            continue
        group_id = _non_empty_string(item, "id", f"{item_path}.id", issues)
        if group_id:
            _check_duplicate(group_id, seen, f"{item_path}.id", "group id", issues)
        bounds = _bounds(item.get("bounds"), f"{item_path}.bounds", issues)
        _check_bounds_inside_canvas(bounds, canvas, f"{item_path}.bounds", issues)
        groups.append(
            Group(
                group_id=group_id or f"group-{index + 1}",
                label=_string(item, "label", f"{item_path}.label", issues, required=False) or group_id or "",
                bounds=bounds,
                role=_role(item, "role", f"{item_path}.role", issues),
                fill=_string(item, "fill", f"{item_path}.fill", issues, required=False),
                stroke=_string(item, "stroke", f"{item_path}.stroke", issues, required=False),
                semantic_kind=_optional_semantic_kind(
                    item,
                    "semantic_kind",
                    f"{item_path}.semantic_kind",
                    issues,
                ),
                importance=_optional_enum(
                    item,
                    "importance",
                    f"{item_path}.importance",
                    KNOWN_IMPORTANCE,
                    issues,
                ),
                parent=_string(item, "parent", f"{item_path}.parent", issues, required=False),
                effect=_effect_config(item.get("effect"), f"{item_path}.effect", KNOWN_GROUP_MOTION, issues, EffectConfig()),
            )
        )
    return groups


def _parse_nodes(
    value: Any,
    path: str,
    issues: List[ValidationIssue],
    canvas: Canvas,
    allowed_icons: Set[str] = KNOWN_ICONS,
) -> List[Node]:
    if not isinstance(value, list):
        issues.append(ValidationIssue(path, "expected a non-empty array", "type"))
        return []
    if not value:
        issues.append(ValidationIssue(path, "must contain at least one node", "required"))

    nodes: List[Node] = []
    seen: Set[str] = set()
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            issues.append(ValidationIssue(item_path, "expected an object", "type"))
            continue
        node_id = _non_empty_string(item, "id", f"{item_path}.id", issues)
        if node_id:
            _check_duplicate(node_id, seen, f"{item_path}.id", "node id", issues)
        position = _point(item.get("position"), f"{item_path}.position", issues, required=True)
        size = _point(item.get("size"), f"{item_path}.size", issues, required=True, positive=True)
        _check_box_inside_canvas(position, size, canvas, item_path, issues)
        nodes.append(
            Node(
                node_id=node_id or f"node-{index + 1}",
                label=_string(item, "label", f"{item_path}.label", issues, required=False) or node_id or "",
                caption=_string(item, "caption", f"{item_path}.caption", issues, required=False) or "",
                position=position,
                size=size,
                shape=_enum(item, "shape", f"{item_path}.shape", KNOWN_NODE_SHAPES, issues, default="rect"),
                role=_role(item, "role", f"{item_path}.role", issues),
                step=_optional_positive_int(item, "step", f"{item_path}.step", issues),
                radius=_optional_number(item, "radius", f"{item_path}.radius", issues, positive=True),
                fill=_string(item, "fill", f"{item_path}.fill", issues, required=False),
                stroke=_string(item, "stroke", f"{item_path}.stroke", issues, required=False),
                stroke_width=_optional_number(item, "stroke_width", f"{item_path}.stroke_width", issues, positive=True),
                icon=_icon(item, "icon", f"{item_path}.icon", issues, allowed_icons),
                semantic_kind=_optional_semantic_kind(
                    item,
                    "semantic_kind",
                    f"{item_path}.semantic_kind",
                    issues,
                ),
                icon_resolution=_optional_enum(
                    item,
                    "icon_resolution",
                    f"{item_path}.icon_resolution",
                    KNOWN_ICON_RESOLUTIONS,
                    issues,
                ),
                importance=_optional_enum(
                    item,
                    "importance",
                    f"{item_path}.importance",
                    KNOWN_IMPORTANCE,
                    issues,
                ),
                state=_parse_semantic_state(item.get("state"), f"{item_path}.state", issues),
                effect=_effect_config(item.get("effect"), f"{item_path}.effect", KNOWN_NODE_MOTION, issues, EffectConfig()),
            )
        )
    return nodes


def _parse_edges(value: Any, path: str, node_ids: Set[str], issues: List[ValidationIssue]) -> List[Edge]:
    if value is None:
        return []
    if not isinstance(value, list):
        issues.append(ValidationIssue(path, "expected an array", "type"))
        return []

    edges: List[Edge] = []
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            issues.append(ValidationIssue(item_path, "expected an object", "type"))
            continue
        source = _non_empty_string(item, "from", f"{item_path}.from", issues)
        target = _non_empty_string(item, "to", f"{item_path}.to", issues)
        if source and source not in node_ids:
            issues.append(ValidationIssue(f"{item_path}.from", f"unknown node id {source!r}", "reference"))
        if target and target not in node_ids:
            issues.append(ValidationIssue(f"{item_path}.to", f"unknown node id {target!r}", "reference"))

        route = _enum(item, "route", f"{item_path}.route", KNOWN_ROUTES, issues, default="curved")
        points = tuple(_points(item.get("points"), f"{item_path}.points", issues))
        if route == "points" and len(points) < 2:
            issues.append(ValidationIssue(f"{item_path}.points", "route 'points' requires at least two points", "required"))
        duration = _string(item, "duration", f"{item_path}.duration", issues, required=False)
        delay = _optional_number(item, "delay", f"{item_path}.delay", issues, positive=False) or 0.0
        animated = _optional_bool(item, "animated", f"{item_path}.animated", issues, default=True)
        edges.append(
            Edge(
                source=source or "",
                target=target or "",
                label=_string(item, "label", f"{item_path}.label", issues, required=False) or "",
                role=_role(item, "role", f"{item_path}.role", issues),
                direction=_enum(
                    item,
                    "direction",
                    f"{item_path}.direction",
                    KNOWN_EDGE_DIRECTIONS,
                    issues,
                    default="forward",
                ),
                route=route,
                step=_optional_positive_int(item, "step", f"{item_path}.step", issues),
                points=points,
                stroke=_string(item, "stroke", f"{item_path}.stroke", issues, required=False),
                width=_optional_number(item, "width", f"{item_path}.width", issues, positive=True),
                semantic_relation_id=_string(
                    item,
                    "semantic_relation_id",
                    f"{item_path}.semantic_relation_id",
                    issues,
                    required=False,
                ),
                semantic_kind=_optional_semantic_kind(
                    item,
                    "semantic_kind",
                    f"{item_path}.semantic_kind",
                    issues,
                ),
                importance=_optional_enum(
                    item,
                    "importance",
                    f"{item_path}.importance",
                    KNOWN_IMPORTANCE,
                    issues,
                ),
                condition=_string(item, "condition", f"{item_path}.condition", issues, required=False),
                protocol=_string(item, "protocol", f"{item_path}.protocol", issues, required=False),
                flow_id=_string(item, "flow_id", f"{item_path}.flow_id", issues, required=False),
                flow_importance=_optional_enum(
                    item,
                    "flow_importance",
                    f"{item_path}.flow_importance",
                    KNOWN_IMPORTANCE,
                    issues,
                ),
                flow_repeat=_optional_enum(
                    item,
                    "flow_repeat",
                    f"{item_path}.flow_repeat",
                    KNOWN_FLOW_REPEAT,
                    issues,
                ),
                motion=Motion(duration=duration, delay=delay, enabled=animated),
                effect=_effect_config(item.get("effect"), f"{item_path}.effect", KNOWN_EDGE_MOTION, issues, EffectConfig()),
            )
        )
    return edges


def _icon(
    data: Dict[str, Any],
    key: str,
    path: str,
    issues: List[ValidationIssue],
    allowed_icons: Set[str] = KNOWN_ICONS,
) -> Optional[str]:
    value = _string(data, key, path, issues, required=False)
    if value is None:
        return None
    if value not in allowed_icons:
        issues.append(ValidationIssue(path, f"expected one of: {', '.join(sorted(allowed_icons))}", "enum"))
        return None
    return value


def _icons_for_system(icon_system: Optional[str]) -> Set[str]:
    if icon_system == "diagram-core-v1":
        return set(DIAGRAM_CORE_ICONS)
    if icon_system == "illustrated":
        return set(illustrated_icon_ids())
    return set(KNOWN_ICONS)


def _role(data: Dict[str, Any], key: str, path: str, issues: List[ValidationIssue]) -> str:
    return _enum(data, key, path, KNOWN_ROLES, issues, default="neutral")


def _optional_enum(
    data: Dict[str, Any],
    key: str,
    path: str,
    allowed: Set[str],
    issues: List[ValidationIssue],
) -> Optional[str]:
    value = _string(data, key, path, issues, required=False)
    if value is None:
        return None
    if value not in allowed:
        issues.append(ValidationIssue(path, f"expected one of: {', '.join(sorted(allowed))}", "enum"))
        return None
    return value


def _optional_semantic_kind(
    data: Dict[str, Any], key: str, path: str, issues: List[ValidationIssue]
) -> Optional[str]:
    value = _string(data, key, path, issues, required=False)
    if value is None:
        return None
    if SEMANTIC_KIND_PATTERN.fullmatch(value) is None:
        issues.append(ValidationIssue(path, "expected a lowercase semantic kind", "pattern"))
        return None
    return value


def _parse_semantic_state(value: Any, path: str, issues: List[ValidationIssue]) -> Dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        issues.append(ValidationIssue(path, "expected an object", "type"))
        return {}
    state: Dict[str, str] = {}
    allowed = {"phase", "result", "availability"}
    for key in value:
        if key not in allowed:
            issues.append(ValidationIssue(f"{path}.{key}", "unsupported state field", "additional_property"))
            continue
        item = value[key]
        if not isinstance(item, str) or not item:
            issues.append(ValidationIssue(f"{path}.{key}", "expected a non-empty string", "type"))
            continue
        state[key] = item
    return state


def _enum(
    data: Dict[str, Any],
    key: str,
    path: str,
    allowed: Set[str],
    issues: List[ValidationIssue],
    default: str,
) -> str:
    value = _string(data, key, path, issues, required=False)
    if value is None:
        return default
    if value not in allowed:
        issues.append(ValidationIssue(path, f"expected one of: {', '.join(sorted(allowed))}", "enum"))
        return default
    return value


def _string(data: Dict[str, Any], key: str, path: str, issues: List[ValidationIssue], required: bool) -> Optional[str]:
    if key not in data:
        if required:
            issues.append(ValidationIssue(path, "is required", "required"))
        return None
    value = data[key]
    if not isinstance(value, str):
        issues.append(ValidationIssue(path, "expected a string", "type"))
        return None
    return value


def _non_empty_string(data: Dict[str, Any], key: str, path: str, issues: List[ValidationIssue]) -> Optional[str]:
    value = _string(data, key, path, issues, required=True)
    if value is not None and not value.strip():
        issues.append(ValidationIssue(path, "must not be empty", "required"))
        return None
    return value


def _positive_int(data: Dict[str, Any], key: str, path: str, issues: List[ValidationIssue], default: int) -> int:
    if key not in data:
        return default
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        issues.append(ValidationIssue(path, "expected a positive integer", "type"))
        return default
    if value <= 0:
        issues.append(ValidationIssue(path, "must be greater than zero", "range"))
        return default
    return value


def _optional_positive_int(data: Dict[str, Any], key: str, path: str, issues: List[ValidationIssue]) -> Optional[int]:
    if key not in data:
        return None
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        issues.append(ValidationIssue(path, "expected a positive integer", "type"))
        return None
    if value <= 0:
        issues.append(ValidationIssue(path, "must be greater than zero", "range"))
        return None
    return value


def _optional_non_negative_int(
    data: Dict[str, Any],
    key: str,
    path: str,
    issues: List[ValidationIssue],
    default: Optional[int] = None,
) -> Optional[int]:
    if key not in data:
        return default
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        issues.append(ValidationIssue(path, "expected a non-negative integer", "type"))
        return default
    if value < 0:
        issues.append(ValidationIssue(path, "must be greater than or equal to zero", "range"))
        return default
    return value


def _optional_number(
    data: Dict[str, Any],
    key: str,
    path: str,
    issues: List[ValidationIssue],
    positive: bool,
    default: Optional[float] = None,
) -> Optional[float]:
    if key not in data:
        return default
    value = data[key]
    if not _is_number(value):
        issues.append(ValidationIssue(path, "expected a number", "type"))
        return None
    number = float(value)
    if positive and number <= 0:
        issues.append(ValidationIssue(path, "must be greater than zero", "range"))
        return default
    if not positive and number < 0:
        issues.append(ValidationIssue(path, "must be greater than or equal to zero", "range"))
        return default
    return number


def _optional_bool(data: Dict[str, Any], key: str, path: str, issues: List[ValidationIssue], default: bool) -> bool:
    if key not in data:
        return default
    value = data[key]
    if not isinstance(value, bool):
        issues.append(ValidationIssue(path, "expected a boolean", "type"))
        return default
    return value


def _point(value: Any, path: str, issues: List[ValidationIssue], required: bool, positive: bool = False) -> Point:
    if value is None:
        if required:
            issues.append(ValidationIssue(path, "is required", "required"))
        return (0.0, 0.0)
    if not isinstance(value, list) or len(value) != 2 or not all(_is_number(item) for item in value):
        issues.append(ValidationIssue(path, "expected [x, y] numeric coordinates", "type"))
        return (0.0, 0.0)
    point = (float(value[0]), float(value[1]))
    if positive and (point[0] <= 0 or point[1] <= 0):
        issues.append(ValidationIssue(path, "width and height must be greater than zero", "range"))
    return point


def _bounds(value: Any, path: str, issues: List[ValidationIssue]) -> Bounds:
    if not isinstance(value, list) or len(value) != 4 or not all(_is_number(item) for item in value):
        issues.append(ValidationIssue(path, "expected [x, y, width, height] numeric bounds", "type"))
        return (0.0, 0.0, 0.0, 0.0)
    bounds = (float(value[0]), float(value[1]), float(value[2]), float(value[3]))
    if bounds[2] <= 0 or bounds[3] <= 0:
        issues.append(ValidationIssue(path, "width and height must be greater than zero", "range"))
    return bounds


def _points(value: Any, path: str, issues: List[ValidationIssue]) -> List[Point]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) < 2:
        issues.append(ValidationIssue(path, "expected an array with at least two points", "type"))
        return []
    points: List[Point] = []
    for index, item in enumerate(value):
        points.append(_point(item, f"{path}[{index}]", issues, required=True))
    return points


def _check_box_inside_canvas(
    position: Point,
    size: Point,
    canvas: Canvas,
    path: str,
    issues: List[ValidationIssue],
) -> None:
    x, y = position
    w, h = size
    if x < 0 or y < 0 or x + w > canvas.width or y + h > canvas.height:
        issues.append(ValidationIssue(path, "node bounds must stay inside canvas", "bounds"))


def _check_bounds_inside_canvas(
    bounds: Bounds,
    canvas: Canvas,
    path: str,
    issues: List[ValidationIssue],
) -> None:
    x, y, w, h = bounds
    if x < 0 or y < 0 or x + w > canvas.width or y + h > canvas.height:
        issues.append(ValidationIssue(path, "bounds must stay inside canvas", "bounds"))


def _check_duplicate(value: str, seen: Set[str], path: str, label: str, issues: List[ValidationIssue]) -> None:
    if value in seen:
        issues.append(ValidationIssue(path, f"duplicate {label} {value!r}", "duplicate"))
        return
    seen.add(value)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
