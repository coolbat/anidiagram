"""DiagramScript schema validation and IR compilation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .model import Bounds, Canvas, Edge, Group, Motion, Node, Point, Scene, Style, Title


SUPPORTED_VERSIONS = ("0.1",)


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str
    code: str = "invalid"

    def to_dict(self) -> Dict[str, str]:
        return {"path": self.path, "message": self.message, "code": self.code}


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


def compile_scene(data: Dict[str, Any]) -> Scene:
    """Validate DiagramScript v0.1 JSON and compile it to the AniDiagram IR."""

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
    groups = _parse_groups(data.get("groups", []), "$.groups", issues)
    nodes = _parse_nodes(data.get("nodes"), "$.nodes", issues)
    node_ids = {node.node_id for node in nodes}
    edges = _parse_edges(data.get("edges", []), "$.edges", node_ids, issues)

    if issues:
        raise DiagramScriptValidationError(issues)

    return Scene(
        version=version or SUPPORTED_VERSIONS[0],
        canvas=canvas,
        title=title,
        style=style,
        nodes=nodes,
        edges=edges,
        groups=groups,
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


def _parse_groups(value: Any, path: str, issues: List[ValidationIssue]) -> List[Group]:
    if value is None:
        return []
    if not isinstance(value, list):
        issues.append(ValidationIssue(path, "expected an array", "type"))
        return []

    groups: List[Group] = []
    seen: set = set()
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            issues.append(ValidationIssue(item_path, "expected an object", "type"))
            continue
        group_id = _non_empty_string(item, "id", f"{item_path}.id", issues)
        if group_id:
            _check_duplicate(group_id, seen, f"{item_path}.id", "group id", issues)
        bounds = _bounds(item.get("bounds"), f"{item_path}.bounds", issues)
        groups.append(
            Group(
                group_id=group_id or f"group-{index + 1}",
                label=_string(item, "label", f"{item_path}.label", issues, required=False) or group_id or "",
                bounds=bounds,
                role=_string(item, "role", f"{item_path}.role", issues, required=False) or "neutral",
                fill=_string(item, "fill", f"{item_path}.fill", issues, required=False),
                stroke=_string(item, "stroke", f"{item_path}.stroke", issues, required=False),
            )
        )
    return groups


def _parse_nodes(value: Any, path: str, issues: List[ValidationIssue]) -> List[Node]:
    if not isinstance(value, list):
        issues.append(ValidationIssue(path, "expected a non-empty array", "type"))
        return []
    if not value:
        issues.append(ValidationIssue(path, "must contain at least one node", "required"))

    nodes: List[Node] = []
    seen: set = set()
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
        nodes.append(
            Node(
                node_id=node_id or f"node-{index + 1}",
                label=_string(item, "label", f"{item_path}.label", issues, required=False) or node_id or "",
                caption=_string(item, "caption", f"{item_path}.caption", issues, required=False) or "",
                position=position,
                size=size,
                role=_string(item, "role", f"{item_path}.role", issues, required=False) or "neutral",
                radius=_optional_number(item, "radius", f"{item_path}.radius", issues, positive=True),
                fill=_string(item, "fill", f"{item_path}.fill", issues, required=False),
                stroke=_string(item, "stroke", f"{item_path}.stroke", issues, required=False),
                stroke_width=_optional_number(item, "stroke_width", f"{item_path}.stroke_width", issues, positive=True),
            )
        )
    return nodes


def _parse_edges(value: Any, path: str, node_ids: set, issues: List[ValidationIssue]) -> List[Edge]:
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

        duration = _string(item, "duration", f"{item_path}.duration", issues, required=False)
        delay = _optional_number(item, "delay", f"{item_path}.delay", issues, positive=False) or 0.0
        animated = _optional_bool(item, "animated", f"{item_path}.animated", issues, default=True)
        edges.append(
            Edge(
                source=source or "",
                target=target or "",
                label=_string(item, "label", f"{item_path}.label", issues, required=False) or "",
                role=_string(item, "role", f"{item_path}.role", issues, required=False) or "neutral",
                points=tuple(_points(item.get("points"), f"{item_path}.points", issues)),
                stroke=_string(item, "stroke", f"{item_path}.stroke", issues, required=False),
                width=_optional_number(item, "width", f"{item_path}.width", issues, positive=True),
                motion=Motion(duration=duration, delay=delay, enabled=animated),
            )
        )
    return edges


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


def _optional_number(
    data: Dict[str, Any],
    key: str,
    path: str,
    issues: List[ValidationIssue],
    positive: bool,
) -> Optional[float]:
    if key not in data:
        return None
    value = data[key]
    if not _is_number(value):
        issues.append(ValidationIssue(path, "expected a number", "type"))
        return None
    number = float(value)
    if positive and number <= 0:
        issues.append(ValidationIssue(path, "must be greater than zero", "range"))
        return None
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


def _check_duplicate(value: str, seen: set, path: str, label: str, issues: List[ValidationIssue]) -> None:
    if value in seen:
        issues.append(ValidationIssue(path, f"duplicate {label} {value!r}", "duplicate"))
        return
    seen.add(value)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
