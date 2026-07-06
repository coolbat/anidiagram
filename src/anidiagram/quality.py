"""Quality checks for compiled AniDiagram scenes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from .effects import channel_effect, effect_active
from .model import Edge, Node, Point, Scene


Rect = Tuple[float, float, float, float]
CONTINUOUS_EDGE_MOTION = {
    "pulse",
    "trace",
    "comet-flow",
    "dynamic-dash",
    "dash-flow",
    "flow-dot",
    "flow-arrow",
    "signal-dot",
    "signal-arrow",
    "ghost-flow",
    "glow-line",
    "comet",
}
PARTICLE_EDGE_MOTION = {"comet-flow", "comet", "flow-dot", "flow-arrow", "signal-dot", "signal-arrow", "ghost-flow"}
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

    def to_dict(self) -> Dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }


def quality_report(scene: Scene) -> Dict[str, object]:
    issues: List[QualityIssue] = []
    nodes = {node.node_id: node for node in scene.nodes}
    _check_node_bounds(scene, issues)
    _check_node_collisions(scene.nodes, issues)
    _check_text_fit(scene.nodes, issues)
    _check_edge_node_collisions(scene.edges, nodes, issues)
    _check_motion_budget(scene, issues)
    errors = sum(1 for issue in issues if issue.severity == "error")
    warnings = sum(1 for issue in issues if issue.severity == "warning")
    score = max(0, 100 - errors * 20 - warnings * 5)
    return {
        "ok": errors == 0,
        "score": score,
        "summary": {"errors": errors, "warnings": warnings, "issues": len(issues)},
        "issues": [issue.to_dict() for issue in issues],
    }


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
            if _rects_overlap(_node_rect(left), _node_rect(right)):
                issues.append(
                    QualityIssue(
                        "node_overlap",
                        "error",
                        f"$.nodes[{left_index}]",
                        f"node {left.node_id!r} overlaps node {right.node_id!r}",
                    )
                )


def _check_text_fit(nodes: List[Node], issues: List[QualityIssue]) -> None:
    for index, node in enumerate(nodes):
        width, height = node.size
        label_capacity = max(8, int((width - 24) / 9))
        caption_capacity = max(10, int((width - 24) / 7))
        if len(node.label) > label_capacity * 2:
            issues.append(
                QualityIssue(
                    "text_overflow",
                    "warning",
                    f"$.nodes[{index}].label",
                    f"label on node {node.node_id!r} is likely to overflow",
                )
            )
        if len(node.caption) > caption_capacity * 2 or height < 64:
            issues.append(
                QualityIssue(
                    "caption_overflow",
                    "warning",
                    f"$.nodes[{index}].caption",
                    f"caption on node {node.node_id!r} is likely to overflow",
                )
            )


def _check_edge_node_collisions(edges: Iterable[Edge], nodes: Dict[str, Node], issues: List[QualityIssue]) -> None:
    for index, edge in enumerate(edges):
        if len(edge.points) < 2:
            continue
        for node_id, node in nodes.items():
            if node_id in {edge.source, edge.target}:
                continue
            if any(_point_in_rect(point, _node_rect(node)) for point in edge.points):
                issues.append(
                    QualityIssue(
                        "edge_node_collision",
                        "warning",
                        f"$.edges[{index}].points",
                        f"edge from {edge.source!r} to {edge.target!r} passes through node {node_id!r}",
                    )
                )


def _point_in_rect(point: Point, rect: Rect) -> bool:
    x, y = point
    return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]


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
        effect = channel_effect(scene.motion, {}, "edge", edge.effect)
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
