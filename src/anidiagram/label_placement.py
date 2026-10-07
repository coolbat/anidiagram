"""Deterministic edge label placement shared by SVG, raster, and diagnostics."""
from math import hypot
from .text_layout import visual_units


def intersects(a, b):
    return a[0] < b[0] + b[2] and a[0] + a[2] > b[0] and a[1] < b[1] + b[3] and a[1] + a[3] > b[1]


def readable_labels(style, scene=None):
    choice = (style or {}).get('edge', {}).get('label_placement')
    return choice == 'avoid-nodes' or (choice != 'legacy' and scene is not None and scene.composition_policy == 'composition-v1')


def place_labels(scene):
    from .renderer_svg import node_box
    from .quality_geometry import rendered_route, segment_crosses_rect, group_title_rect
    from .localization import scene_locale
    nodes = {n.node_id: node_box(n) for n in scene.nodes}
    occupied = [(n.position[0] - 6, n.position[1] - 6, n.size[0] + 12, n.size[1] + 12) for n in scene.nodes]
    for group in scene.groups:
        x1, y1, x2, y2 = group_title_rect(group, scene_locale(scene))
        occupied.append((x1-4, y1-4, x2-x1+8, y2-y1+8))
    routes = [rendered_route(edge, nodes) for edge in scene.edges]
    segments_all = [pair for route in routes for pair in zip(route, route[1:])]
    result = {}
    for index, edge in enumerate(scene.edges, 1):
        if not edge.label and edge.step is None:
            continue
        width = visual_units(edge.label) * 13 * 0.62
        badge = 38 if edge.step is not None else 0
        points = routes[index - 1]
        lengths = [hypot(b[0]-a[0], b[1]-a[1]) for a, b in zip(points, points[1:])]
        midpoint = sum(lengths) / 2
        candidates, elapsed = [], 0.0
        for (a, b), length in zip(zip(points, points[1:]), lengths):
            for fraction in (0.5, 0.25, 0.75):
                anchor = (a[0] + (b[0] - a[0]) * fraction, a[1] + (b[1] - a[1]) * fraction)
                for dy in (5, -22, 30, -46, 54, -74, 82, -106, 114):
                    for dx in (0, -30, 30, -70, 70, -110, 110, -160, 160, -220, 220, -280, 280, -340, 340, -420, 420):
                        x, y = anchor[0] - width / 2 + dx + badge / 2, anchor[1] + dy
                        box = (x - badge - 4, y - 20, width + badge + 8, 30)
                        if box[0] < 12 or box[1] < 90 or box[0] + box[2] > scene.canvas.width - 12 or box[1] + box[3] > scene.canvas.height - 12:
                            continue
                        score = abs(dx) + abs(dy) + abs(elapsed + length * fraction - midpoint) * 0.25
                        candidates.append((score, x, y, box, anchor))
            elapsed += length
        placed = None
        for candidate in sorted(candidates, key=lambda c: c[0]):
            _, x, y, box, anchor = candidate
            if any(intersects(box, other) for other in occupied):
                continue
            bounds = (box[0]-2, box[1]-2, box[0]+box[2]+2, box[1]+box[3]+2)
            if any(segment_crosses_rect(c, d, bounds) for c, d in segments_all):
                continue
            placed = candidate
            break
        if placed is not None:
            _, x, y, box, anchor = placed
            occupied.append(box)
            result[index] = {'x': x, 'y': y, 'box': box, 'anchor': anchor, 'placed': True}
        else:
            start, end = points[0], points[-1]
            result[index] = {'x': (start[0] + end[0]) / 2, 'y': (start[1] + end[1]) / 2 - 22,
                             'placed': False, 'reason': 'Full label cannot fit without collision; expand/rearrange the diagram.'}
    return result
