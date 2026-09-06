"""Deterministic opt-in label placement; browser checks remain the final geometry gate."""

import unicodedata


def intersects(a, b):
    return a[0] < b[0] + b[2] and a[0] + a[2] > b[0] and a[1] < b[1] + b[3] and a[1] + a[3] > b[1]


def readable_labels(style):
    return style.get('edge', {}).get('label_placement') == 'avoid-nodes'


def place_labels(scene):
    from .renderer_svg import curve_controls, node_box, route_points
    nodes = {n.node_id: node_box(n) for n in scene.nodes}
    occupied = [(n.position[0] - 6, n.position[1] - 6, n.size[0] + 12, n.size[1] + 12) for n in scene.nodes]
    # Keep labels off group headings as well as the main title area.
    occupied.extend((g.bounds[0] + 10, g.bounds[1] + 5, min(g.bounds[2] - 20, len(g.label) * 12 + 30), 28)
                    for g in scene.groups)
    result = {}
    for index, edge in enumerate(scene.edges, 1):
        if not edge.label:
            continue
        width = sum(14 if unicodedata.east_asian_width(c) in 'WF' else 9 for c in edge.label)
        badge = 30 if edge.step is not None else 0
        points = route_points(edge, nodes)
        if edge.route == 'curved' and len(edge.points) < 2:
            start, end = points
            c1, c2 = curve_controls(start, end)
            points = [tuple((1-t)**3 * start[d] + 3*(1-t)**2*t*c1[d] +
                            3*(1-t)*t*t*c2[d] + t**3*end[d] for d in (0, 1))
                      for t in (i / 24 for i in range(25))]
        segments = sorted(zip(points, points[1:]), key=lambda p: -(abs(p[1][0] - p[0][0]) + abs(p[1][1] - p[0][1])))
        candidates = []
        for a, b in segments:
            for fraction in (0.5, 0.25, 0.75):
                anchor = (a[0] + (b[0] - a[0]) * fraction, a[1] + (b[1] - a[1]) * fraction)
                for dy in (-22, 28, -44, 50, -70, 76, -100, 106):
                    for dx in (0, -30, 30, -70, 70):
                        x, y = anchor[0] - width / 2 + dx, anchor[1] + dy
                        box = (x - badge - 4, y - 18, width + badge + 8, 24)
                        if box[0] < 12 or box[1] < 90 or box[0] + box[2] > scene.canvas.width - 12 or box[1] + box[3] > scene.canvas.height - 12:
                            continue
                        if any(intersects(box, other) for other in occupied):
                            continue
                        candidates.append((abs(dx) + abs(dy), x, y, box, anchor))
        if candidates:
            _, x, y, box, anchor = min(candidates, key=lambda c: c[0])
            occupied.append(box)
            result[index] = {'x': x, 'y': y, 'box': box, 'anchor': anchor, 'placed': True}
        else:
            start, end = points[0], points[-1]
            result[index] = {'x': (start[0] + end[0]) / 2, 'y': (start[1] + end[1]) / 2 - 22,
                             'placed': False, 'reason': 'Full label cannot fit without collision; expand/rearrange the diagram.'}
    return result
