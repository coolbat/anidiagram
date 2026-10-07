"""Renderer-aligned geometry diagnostics.

Routes and text layout share the SVG renderer's rules. Text widths remain
estimates (fonts vary by browser), so text collisions are warnings, not errors.
Only explicit group membership establishes semantic ownership.
"""

from __future__ import annotations

from math import hypot

from .model import Edge, Node, Scene
from .text_layout import fitted_text_length, node_text_region, node_text_vertical_region, text_block_layout, visual_units


def rect(bounds):
    x, y, width, height = bounds
    return x, y, x + width, y + height


def node_rect(node):
    return rect((*node.position, *node.size))


def contains(outer, inner):
    return outer[0] <= inner[0] and outer[1] <= inner[1] and outer[2] >= inner[2] and outer[3] >= inner[3]


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def segment_crosses_rect(start, end, bounds):
    # Interior intersection only: an authored route touching a boundary is not
    # evidence that it passes through a node or through text.
    from .quality import _segment_intersects_rect
    inset = 1e-6
    interior = bounds[0] + inset, bounds[1] + inset, bounds[2] - inset, bounds[3] - inset
    return _segment_intersects_rect(start, end, interior)


def segment_crosses_node(start, end, node):
    if node.shape != "decision":
        return segment_crosses_rect(start, end, node_rect(node))
    # A diamond's empty bounding-box corners must not become false positives.
    x, y = node.position
    width, height = node.size
    def transform(point):
        u = (point[0] - x - width / 2) / (width / 2)
        v = (point[1] - y - height / 2) / (height / 2)
        return u + v, u - v
    return segment_crosses_rect(transform(start), transform(end), (-1, -1, 1, 1))


def rendered_route(edge: Edge, boxes):
    """Use the actual trimmed routes; flatten cubic curves to <=0.5px error."""
    from .renderer_svg import curve_controls, route_points
    points = route_points(edge, boxes)
    if edge.route != "curved" or len(edge.points) >= 2 or len(points) < 2:
        return points
    start, end = points
    first, second = curve_controls(start, end)
    def midpoint(a, b):
        return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    def flatten(a, b, c, d, depth=0):
        chord = hypot(d[0] - a[0], d[1] - a[1])
        if chord:
            distances = [abs((p[0] - a[0]) * (d[1] - a[1]) - (p[1] - a[1]) * (d[0] - a[0])) / chord for p in (b, c)]
        else:
            distances = [hypot(p[0] - a[0], p[1] - a[1]) for p in (b, c)]
        if max(distances) <= 0.5 or depth >= 12:
            return [a, d]
        ab, bc, cd = midpoint(a, b), midpoint(b, c), midpoint(c, d)
        abc, bcd = midpoint(ab, bc), midpoint(bc, cd)
        middle = midpoint(abc, bcd)
        return flatten(a, ab, abc, middle, depth + 1)[:-1] + flatten(middle, bcd, cd, d, depth + 1)
    return flatten(start, first, second, end)


def group_title_rect(group, locale):
    x, y, _, _ = group.bounds
    label = group.label if locale == "zh-CN" else group.label.upper()
    spacing = 14 * (0.04 if locale == "zh-CN" else 0.08)
    width = visual_units(label) * 14 * 0.58 + len(label) * spacing
    return x + 18, y + 16, x + 18 + width, y + 33


def check_groups(scene: Scene, issues, advisories):
    from .localization import scene_locale
    from .quality import QualityIssue
    groups = {group.group_id: group for group in scene.groups}
    nodes = {node.node_id: (index, node) for index, node in enumerate(scene.nodes)}
    ancestors = {}
    for group in scene.groups:
        seen = set()
        parent = group.parent
        while parent in groups and parent not in seen:
            seen.add(parent)
            parent = groups[parent].parent
        ancestors[group.group_id] = seen
    for index, group in enumerate(scene.groups):
        bounds = rect(group.bounds)
        if group.parent in groups and not contains(rect(groups[group.parent].bounds), bounds):
            issues.append(QualityIssue(
                "group_out_of_parent_bounds", "error", f"$.groups[{index}].bounds",
                f"group {group.group_id!r} exceeds its declared parent {group.parent!r}",
                subject={"group_id": group.group_id, "parent_id": group.parent},
                evidence={"group_rect": list(bounds), "parent_rect": list(rect(groups[group.parent].bounds))},
                supported_fixes=("resize_group", "move_group"),
            ))
        for other in scene.groups[index + 1:]:
            other_bounds = rect(other.bounds)
            if not overlaps(bounds, other_bounds):
                continue
            if group.group_id in ancestors[other.group_id] or other.group_id in ancestors[group.group_id]:
                continue
            nested = contains(bounds, other_bounds) or contains(other_bounds, bounds)
            shared_members = sorted(set(group.members) & set(other.members))
            ambiguous = nested or bool(shared_members)
            target = advisories if ambiguous else issues
            target.append(QualityIssue(
                "group_containment_unverified" if nested else "group_shared_membership_overlap" if shared_members else "group_overlap",
                "advisory" if ambiguous else "error", f"$.groups[{index}].bounds",
                (f"groups {group.group_id!r} and {other.group_id!r} are nested without a declared parent"
                 if nested else f"groups {group.group_id!r} and {other.group_id!r} overlap and explicitly share members; confirm intended overlap"
                 if shared_members else f"group {group.group_id!r} overlaps unrelated group {other.group_id!r}"),
                subject={"group_ids": [group.group_id, other.group_id]},
                evidence={"source_rect": list(bounds), "target_rect": list(other_bounds), "shared_members": shared_members},
                supported_fixes=("declare_group_parent",) if nested else ("adjust_layout_spacing", "resize_group"),
            ))
        for member in group.members:
            if member not in nodes:
                continue  # Schema owns dangling-member validation.
            node_index, node = nodes[member]
            if not contains(bounds, node_rect(node)):
                issues.append(QualityIssue(
                    "node_out_of_group", "error", f"$.nodes[{node_index}]",
                    f"node {member!r} exceeds its declared group {group.group_id!r}",
                    subject={"node_id": member, "group_id": group.group_id},
                    evidence={"node_rect": list(node_rect(node)), "group_rect": list(bounds), "ownership": "explicit-membership"},
                    supported_fixes=("move_node", "resize_group", "adjust_layout_spacing"),
                ))
        title = group_title_rect(group, scene_locale(scene))
        for node_index, node in nodes.values():
            if group.label and overlaps(node_rect(node), title):
                issues.append(QualityIssue(
                    "node_group_title_collision", "warning", f"$.nodes[{node_index}]",
                    f"node {node.node_id!r} overlaps the title of group {group.group_id!r}",
                    subject={"node_id": node.node_id, "group_id": group.group_id},
                    evidence={"node_rect": list(node_rect(node)), "title_rect": list(title), "measurement": "estimated-text-bounds"},
                    supported_fixes=("move_node", "reserve_group_title_space"),
                ))


def node_label_rects(node: Node, icon_system):
    offset, width = node_text_region(node.size[0], icon_system=icon_system, has_icon=bool(node.icon), decision=node.shape == "decision")
    y_offset, height = node_text_vertical_region(node.size[1], node.shape == "decision")
    layout = text_block_layout(node.label, node.caption, width, height)
    left = node.position[0] + offset
    baseline = node.position[1] + y_offset + layout.first_baseline
    lines = [(line, 18, 18) for line in layout.label_lines] + [(line, 13, 17) for line in layout.caption_lines]
    for index, (line, size, line_height) in enumerate(lines):
        if index:
            baseline += line_height
        measured_width = fitted_text_length(line, width, size) or visual_units(line) * size * 0.58
        yield left, baseline - size, left + measured_width, baseline + 3


def circle_overlaps_rect(center, radius, bounds):
    nearest = max(bounds[0], min(center[0], bounds[2])), max(bounds[1], min(center[1], bounds[3]))
    return hypot(center[0] - nearest[0], center[1] - nearest[1]) < radius


def check_route_decorations(scene: Scene, style, icon_system, issues, advisories, placements=None):
    from .label_placement import place_labels, readable_labels
    from .localization import scene_locale
    from .quality import QualityIssue
    from .renderer_svg import edge_label_has_clearance, edge_points, node_box
    boxes = {node.node_id: node_box(node) for node in scene.nodes}
    if placements is None:
        placements = place_labels(scene) if readable_labels(style, scene) else {}
    labels = []
    badges = []
    for index, node in enumerate(scene.nodes):
        labels.extend(("node", index, bounds) for bounds in node_label_rects(node, icon_system))
        if node.step is not None and not any(edge.step is not None for edge in scene.edges):
            badges.append(("node", index, (node.position[0] + 18, node.position[1] + 18)))
    for index, group in enumerate(scene.groups):
        if group.label:
            labels.append(("group", index, group_title_rect(group, scene_locale(scene))))
    for index, edge in enumerate(scene.edges):
        start, end = edge_points(edge, boxes)
        x = (start[0] + end[0]) / 2
        offset = -14 if edge.route == "straight" else (-18 if (index + 1) % 2 == 0 else 22)
        y = (start[1] + end[1]) / 2 + offset
        placement = placements.get(index + 1)
        if placement is not None:
            x, y = placement["x"], placement["y"]
        if edge.label and (placement is not None or edge_label_has_clearance(edge, start, end)):
            # SVG edge-label has the default START anchor, including when it
            # shares a baseline with a badge. Never assume a centered label.
            labels.append(("edge", index, (x, y - 12, x + visual_units(edge.label) * 12 * 0.58, y + 3)))
        if edge.step is not None:
            badges.append(("edge", index, (x - 22, y - 5)))
        points = rendered_route(edge, boxes)
        if edge.route != "curved" or len(edge.points) >= 2:
            diagonal = next(((a, b) for a, b in zip(points, points[1:])
                             if abs(b[0] - a[0]) > 24 and abs(b[1] - a[1]) > 24 and hypot(b[0] - a[0], b[1] - a[1]) > 240), None)
            if diagonal:
                advisories.append(QualityIssue(
                    "long_diagonal_edge", "advisory", f"$.edges[{index}].route",
                    "long diagonal route may reduce readability; it is not invalid geometry",
                    subject={"edge_index": index, "source": edge.source, "target": edge.target},
                    evidence={"segment": [list(point) for point in diagonal], "threshold_px": 240},
                    supported_fixes=("reroute_edge_points", "change_layout"),
                ))
    for edge_index, edge in enumerate(scene.edges):
        points = rendered_route(edge, boxes)
        for kind, index, bounds in labels:
            if kind == "node":
                continue  # Full node collision already covers these labels.
            collision = next(((a, b) for a, b in zip(points, points[1:]) if segment_crosses_rect(a, b, bounds)), None)
            if collision:
                issues.append(QualityIssue(
                    "edge_group_title_collision" if kind == "group" else "edge_label_collision",
                    "warning", f"$.edges[{edge_index}]",
                    f"edge from {edge.source!r} to {edge.target!r} crosses {'group title' if kind == 'group' else 'edge label'} {index}",
                    subject={"edge_index": edge_index, f"{kind}_index": index} if kind == "group" else {"edge_index": edge_index, "label_edge_index": index},
                    evidence={"segment": [list(point) for point in collision], "label_rect": list(bounds), "measurement": "estimated-text-bounds"},
                    supported_fixes=("reroute_edge_points", "reposition_label"),
                ))
    for badge_kind, badge_index, center in badges:
        seen = set()
        for label_kind, label_index, bounds in labels:
            key = label_kind, label_index
            if key in seen or not circle_overlaps_rect(center, 14, bounds):
                continue
            seen.add(key)
            issues.append(QualityIssue(
                "badge_label_collision", "warning", f"$.{badge_kind}s[{badge_index}].step",
                f"{badge_kind} step badge overlaps {label_kind} text",
                subject={"badge_kind": badge_kind, "badge_index": badge_index, "label_kind": label_kind, "label_index": label_index},
                evidence={"badge_center": list(center), "badge_radius": 14, "label_rect": list(bounds), "measurement": "estimated-text-bounds"},
                supported_fixes=("move_step_badge", "resize_node", "reposition_label"),
            ))
