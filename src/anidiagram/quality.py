"""Quality checks for compiled AniDiagram scenes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .effects import canonical_edge_effect, channel_effect, effect_active
from .edge_motion import CONTINUOUS_EDGE_MOTION, PARTICLE_EDGE_MOTION
from .diagram_core.catalog import approved_icon_ids
from .icon_system import resolve_icon_system
from .styles import deep_merge
from .illustrated_character_icons import character_icon_ids
from .illustrated_registry import illustrated_icon_ids
from .model import Edge, Node, Point, Scene
from .text_layout import node_text_region, text_block_layout


Rect = Tuple[float, float, float, float]
CONTINUOUS_NODE_MOTION = {
    "float",
    "glow-breathe",
    "pop",
    "pulse",
    "ripple",
    "status-blink",
    "icon-pulse",
    "icon-breathe",
    "icon-semantic",
    "micro-icon",
}
SCANNING_GROUP_MOTION = {"marching-ants", "border-scan", "corner-pulse"}


@dataclass(frozen=True)
class QualityIssue:
    code: str
    severity: str
    path: str
    message: str
    subject: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)
    supported_fixes: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, object]:
        return {
            "code": self.code,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
            "subject": dict(self.subject),
            "evidence": dict(self.evidence),
            "supported_fixes": list(self.supported_fixes),
        }


def quality_report(scene: Scene, style: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    issues: List[QualityIssue] = []
    advisories: List[QualityIssue] = []
    nodes = {node.node_id: node for node in scene.nodes}
    _check_node_bounds(scene, issues)
    _check_node_collisions(scene.nodes, issues)
    quality_icon_system = scene.icon_system or (resolve_icon_system(style) if style is not None else "semantic-line-v1")
    _check_text_fit(scene.nodes, issues, quality_icon_system)
    _check_edge_node_collisions(scene.edges, nodes, issues, advisories)
    _check_hidden_edge_labels(scene.edges, nodes, advisories)
    _check_motion_budget(scene, issues)
    _check_semantic_icon_fallbacks(scene, issues)
    if style is not None:
        if scene.icon_system:
            style = deep_merge(style, {"icon_system": scene.icon_system})
        icon_system = resolve_icon_system(style)
        if icon_system == "illustrated-character-v1":
            _check_character_icon_fallbacks(scene, issues, icon_system, character_icon_ids())
        elif icon_system == "illustrated":
            _check_character_icon_fallbacks(scene, issues, icon_system, illustrated_icon_ids())
        elif icon_system == "diagram-core-v1":
            _check_diagram_core_coverage(scene, issues)
    errors = sum(1 for issue in issues if issue.severity == "error")
    warnings = sum(1 for issue in issues if issue.severity == "warning")
    score = max(0, 100 - errors * 20 - warnings * 5)
    return {
        "ok": errors == 0,
        "score": score,
        "summary": {"errors": errors, "warnings": warnings, "issues": len(issues)},
        "issues": [issue.to_dict() for issue in issues],
        "advisories": [advisory.to_dict() for advisory in advisories],
    }


def _check_character_icon_fallbacks(
    scene: Scene,
    issues: List[QualityIssue],
    icon_system: str = "illustrated-character-v1",
    covered_icons: Iterable[str] = (),
) -> None:
    covered = set(covered_icons or character_icon_ids())
    for index, node in enumerate(scene.nodes):
        if node.icon and node.icon not in covered:
            issues.append(
                QualityIssue(
                    "character_icon_fallback",
                    "warning",
                    f"$.nodes[{index}].icon",
                    f"icon '{node.icon}' is not covered by {icon_system}; rendered with semantic-line-v1",
                )
            )


def _check_semantic_icon_fallbacks(scene: Scene, issues: List[QualityIssue]) -> None:
    for index, node in enumerate(scene.nodes):
        if node.icon_resolution != "role-fallback":
            continue
        semantic_kind = node.semantic_kind or "unknown"
        rendered_icon = node.icon or "none"
        issues.append(
            QualityIssue(
                "semantic_icon_fallback",
                "warning",
                f"$.nodes[{index}].icon_resolution",
                f"semantic kind '{semantic_kind}' uses role-fallback icon '{rendered_icon}'",
            )
        )


def _check_diagram_core_coverage(scene: Scene, issues: List[QualityIssue]) -> None:
    covered = approved_icon_ids()
    for index, node in enumerate(scene.nodes):
        if node.icon and node.icon not in covered:
            issues.append(
                QualityIssue(
                    "diagram_core_icon_not_approved",
                    "error",
                    f"$.nodes[{index}].icon",
                    f"icon '{node.icon}' is not an approved diagram-core-v1 asset",
                )
            )


def _node_rect(node: Node) -> Rect:
    x, y = node.position
    w, h = node.size
    return (x, y, x + w, y + h)


def _rects_overlap(a: Rect, b: Rect) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def _check_node_bounds(scene: Scene, issues: List[QualityIssue]) -> None:
    for index, node in enumerate(scene.nodes):
        x, y, right, bottom = _node_rect(node)
        if x < 0 or y < 0 or right > scene.canvas.width or bottom > scene.canvas.height:
            issues.append(
                QualityIssue(
                    "node_out_of_bounds",
                    "error",
                    f"$.nodes[{index}]",
                    f"node {node.node_id!r} exceeds the canvas",
                )
            )


def _check_node_collisions(nodes: List[Node], issues: List[QualityIssue]) -> None:
    for left_index, left in enumerate(nodes):
        for right_index in range(left_index + 1, len(nodes)):
            right = nodes[right_index]
            left_rect = _node_rect(left)
            right_rect = _node_rect(right)
            if _rects_overlap(left_rect, right_rect):
                overlap_width = min(left_rect[2], right_rect[2]) - max(left_rect[0], right_rect[0])
                overlap_height = min(left_rect[3], right_rect[3]) - max(left_rect[1], right_rect[1])
                issues.append(
                    QualityIssue(
                        "node_overlap",
                        "error",
                        f"$.nodes[{left_index}]",
                        f"node {left.node_id!r} overlaps node {right.node_id!r}",
                        subject={"node_ids": [left.node_id, right.node_id]},
                        evidence={
                            "source_rect": list(left_rect),
                            "target_rect": list(right_rect),
                            "overlap": [overlap_width, overlap_height],
                        },
                        supported_fixes=("move_node", "adjust_layout_spacing", "resize_node"),
                    )
                )


def _check_text_fit(nodes: List[Node], issues: List[QualityIssue], icon_system: str) -> None:
    for index, node in enumerate(nodes):
        width, height = node.size
        _offset, text_width = node_text_region(
            width,
            icon_system=icon_system,
            has_icon=bool(node.icon),
            decision=node.shape == "decision",
        )
        layout = text_block_layout(node.label, node.caption, text_width, height)
        if layout.all_label_lines > 2:
            issues.append(
                QualityIssue(
                    "text_overflow",
                    "warning",
                    f"$.nodes[{index}].label",
                    f"label on node {node.node_id!r} is likely to overflow",
                )
            )
        if layout.all_caption_lines > len(layout.caption_lines) or layout.total_height + 20 > height:
            issues.append(
                QualityIssue(
                    "caption_overflow",
                    "warning",
                    f"$.nodes[{index}].caption",
                    f"caption on node {node.node_id!r} is likely to overflow",
                )
            )


def _check_edge_node_collisions(
    edges: Iterable[Edge],
    nodes: Dict[str, Node],
    issues: List[QualityIssue],
    advisories: List[QualityIssue],
) -> None:
    for index, edge in enumerate(edges):
        if len(edge.points) < 2:
            continue
        for node_id, node in nodes.items():
            if node_id in {edge.source, edge.target}:
                continue
            node_rect = _node_rect(node)
            collision = next(
                (
                    (segment_index, start, end)
                    for segment_index, (start, end) in enumerate(zip(edge.points, edge.points[1:]))
                    if _segment_intersects_rect(start, end, node_rect)
                ),
                None,
            )
            if collision is not None:
                segment_index, start, end = collision
                waypoint_inside = any(_point_in_rect(point, node_rect) for point in edge.points)
                target = issues if waypoint_inside else advisories
                target.append(
                    QualityIssue(
                        "edge_node_collision" if waypoint_inside else "edge_segment_node_collision",
                        "warning" if waypoint_inside else "advisory",
                        f"$.edges[{index}].points",
                        f"edge from {edge.source!r} to {edge.target!r} passes through node {node_id!r}",
                        subject={
                            "edge_index": index,
                            "source": edge.source,
                            "target": edge.target,
                            "blocking_node": node_id,
                        },
                        evidence={
                            "segment_index": segment_index,
                            "segment": [list(start), list(end)],
                            "node_rect": list(node_rect),
                        },
                        supported_fixes=("reroute_edge_points", "move_blocking_node", "change_layout"),
                    )
                )


def _point_in_rect(point: Point, rect: Rect) -> bool:
    x, y = point
    return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]


def _segment_intersects_rect(start: Point, end: Point, rect: Rect) -> bool:
    """Return whether a finite line segment touches or crosses a rectangle."""

    if _point_in_rect(start, rect) or _point_in_rect(end, rect):
        return True
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    lower = 0.0
    upper = 1.0
    for direction, distance in (
        (-dx, x1 - rect[0]),
        (dx, rect[2] - x1),
        (-dy, y1 - rect[1]),
        (dy, rect[3] - y1),
    ):
        if direction == 0:
            if distance < 0:
                return False
            continue
        ratio = distance / direction
        if direction < 0:
            lower = max(lower, ratio)
        else:
            upper = min(upper, ratio)
        if lower > upper:
            return False
    return True


def _check_hidden_edge_labels(
    edges: Iterable[Edge], nodes: Dict[str, Node], advisories: List[QualityIssue]
) -> None:
    """Report labels that the SVG renderer would otherwise omit silently."""

    from .renderer_svg import NodeBox, edge_label_has_clearance, edge_points

    boxes = {
        node_id: NodeBox(node_id, node.position[0], node.position[1], node.size[0], node.size[1])
        for node_id, node in nodes.items()
    }
    for index, edge in enumerate(edges):
        if not edge.label:
            continue
        start, end = edge_points(edge, boxes)
        if edge_label_has_clearance(edge, start, end):
            continue
        available_width = abs(end[0] - start[0])
        required_width = max(48, len(edge.label) * 7 + 18)
        advisories.append(
            QualityIssue(
                "edge_label_hidden",
                "advisory",
                f"$.edges[{index}].label",
                f"label on edge from {edge.source!r} to {edge.target!r} will be hidden because the straight route is too short",
                subject={"edge_index": index, "source": edge.source, "target": edge.target},
                evidence={
                    "label": edge.label,
                    "available_width": available_width,
                    "required_width": required_width,
                    "start": list(start),
                    "end": list(end),
                },
                supported_fixes=("increase_node_spacing", "shorten_edge_label", "change_edge_route"),
            )
        )


def _check_motion_budget(scene: Scene, issues: List[QualityIssue]) -> None:
    policy = scene.motion_policy
    if (
        policy.max_active_flow_edges is None
        and policy.max_particle_edges is None
        and policy.max_active_pulse_nodes is None
        and policy.max_scanning_groups is None
    ):
        return
    edge_motion_count = 0
    particle_edge_count = 0
    for edge in scene.edges:
        if not edge.motion.enabled:
            continue
        effect = canonical_edge_effect(channel_effect(scene.motion, {}, "edge", edge.effect))
        if not effect_active(scene.motion, effect):
            continue
        if effect.preset in CONTINUOUS_EDGE_MOTION:
            edge_motion_count += 1
        if effect.preset in PARTICLE_EDGE_MOTION:
            particle_edge_count += 1
    node_motion_count = sum(
        1
        for node in scene.nodes
        if (effect := channel_effect(scene.motion, {}, "node", node.effect)).preset in CONTINUOUS_NODE_MOTION
        and effect_active(scene.motion, effect)
    )
    group_motion_count = sum(
        1
        for group in scene.groups
        if (effect := channel_effect(scene.motion, {}, "group", group.effect)).preset in SCANNING_GROUP_MOTION
        and effect_active(scene.motion, effect)
    )
    _motion_budget_warning(
        issues,
        "$.motion_policy.max_active_flow_edges",
        edge_motion_count,
        policy.max_active_flow_edges,
        "active flow edges",
    )
    _motion_budget_warning(
        issues,
        "$.motion_policy.max_particle_edges",
        particle_edge_count,
        policy.max_particle_edges,
        "particle edges",
    )
    _motion_budget_warning(
        issues,
        "$.motion_policy.max_active_pulse_nodes",
        node_motion_count,
        policy.max_active_pulse_nodes,
        "pulse nodes",
    )
    _motion_budget_warning(
        issues,
        "$.motion_policy.max_scanning_groups",
        group_motion_count,
        policy.max_scanning_groups,
        "scanning groups",
    )


def _motion_budget_warning(
    issues: List[QualityIssue],
    path: str,
    configured: int,
    limit: Optional[int],
    label: str,
) -> None:
    if limit is None or configured <= limit:
        return
    issues.append(
        QualityIssue(
            "motion_overload",
            "warning",
            path,
            f"{configured} configured {label} exceed the motion policy limit of {limit}; renderer will clamp the extras",
        )
    )
