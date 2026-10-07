"""Deterministic orthogonal visibility-grid routing for compiled Plans.

Only the Plan compiler calls this module. Authored Script points and directions
are never rewritten. Obstacles include node bodies and group headings; existing
tracks add congestion cost and candidate lanes spaced by eight pixels.
"""
from __future__ import annotations

from collections import defaultdict
from heapq import heappop, heappush
import math

from .text_layout import visual_units

CLEARANCE = 12.0
TRACK_SPACING = 8.0


def _crosses(a, b, r):
    if a[0] == b[0]:
        return r[0] < a[0] < r[2] and max(min(a[1], b[1]), r[1]) < min(max(a[1], b[1]), r[3])
    return r[1] < a[1] < r[3] and max(min(a[0], b[0]), r[0]) < min(max(a[0], b[0]), r[2])


def _ports(node, offset):
    x, y = node['position']
    w, h = node['size']
    cy = y + h / 2 + max(-h / 4, min(h / 4, offset))
    cx = x + w / 2 + max(-w / 4, min(w / 4, offset))
    # The stub clears the inflated body before the first bend.
    stub = CLEARANCE + TRACK_SPACING
    return [((x + w, cy), (x + w + stub, cy)), ((x, cy), (x - stub, cy)),
            ((cx, y + h), (cx, y + h + stub)), ((cx, y), (cx, y - stub))]


def _congestion(a, b, tracks):
    horizontal = a[1] == b[1]
    axis = 0 if horizontal else 1
    lo, hi = sorted((a[axis], b[axis]))
    cost = 0.0
    for c, d in tracks:
        other_horizontal = c[1] == d[1]
        if horizontal == other_horizontal:
            overlap = min(hi, max(c[axis], d[axis])) - max(lo, min(c[axis], d[axis]))
            distance = abs(a[1 - axis] - c[1 - axis])
            if overlap > 0 and distance < TRACK_SPACING - 0.01:
                cost += overlap * 8 + 40
        elif min(c[1-axis], d[1-axis]) < a[1-axis] < max(c[1-axis], d[1-axis]) and lo < c[axis] < hi:
            cost += 12
    return cost


def _simplify(points):
    result = []
    for point in points:
        if result and result[-1] == point:
            continue
        if len(result) >= 2 and ((result[-2][0] == result[-1][0] == point[0]) or
                                 (result[-2][1] == result[-1][1] == point[1])):
            result[-1] = point
        else:
            result.append(point)
    return [list(point) for point in result]


def _route(source, target, obstacles, tracks, canvas, offset):
    starts = _ports(source, offset)
    ends = _ports(target, offset)
    if source['id'] == target['id']:
        starts, ends = starts[:1], ends[2:3]
    # The endpoint body is intentionally crossed by its own outward stub only.
    def usable(pair, own):
        a, b = pair
        return 12 <= b[0] <= canvas['width'] - 12 and 112 <= b[1] <= canvas['height'] - 12 and not any(
            _crosses(a, b, r) for key, r in obstacles if key != own)
    starts = [p for p in starts if usable(p, source['id'])]
    ends = [p for p in ends if usable(p, target['id'])]
    # A port already used by another edge would merge two arrows into one stub.
    claimed = {tuple(point) for track in tracks for point in track}
    starts = [p for p in starts if tuple(p[0]) not in claimed] or starts
    ends = [p for p in ends if tuple(p[0]) not in claimed] or ends
    if not starts or not ends:
        return None
    xs = {12.0, canvas['width'] - 12.0}
    ys = {112.0, canvas['height'] - 12.0}
    for _, r in obstacles:
        xs.update((r[0], r[2]))
        ys.update((r[1], r[3]))
    for a, b in starts + ends:
        xs.add(b[0]); ys.add(b[1])
    for a, b in tracks:
        if a[0] == b[0]:
            xs.update((a[0] - TRACK_SPACING, a[0] + TRACK_SPACING))
        if a[1] == b[1]:
            ys.update((a[1] - TRACK_SPACING, a[1] + TRACK_SPACING))
    xs = sorted(x for x in xs if 12 <= x <= canvas['width'] - 12)
    ys = sorted(y for y in ys if 112 <= y <= canvas['height'] - 12)
    xi, yi = {x: i for i, x in enumerate(xs)}, {y: i for i, y in enumerate(ys)}
    rects = [r for _, r in obstacles]
    blocked = {(i, j) for i, x in enumerate(xs) for j, y in enumerate(ys)
               if any(r[0] < x < r[2] and r[1] < y < r[3] for r in rects)}
    goal = {(xi[p[1][0]], yi[p[1][1]]): p[0] for p in ends}
    queue, distance, parent, origins = [], {}, {}, {}
    goal_points = [(xs[i], ys[j]) for i, j in goal]
    def heuristic(i, j):
        return min(abs(xs[i] - x) + abs(ys[j] - y) for x, y in goal_points)
    # Each geometric link can be visited in both directions and with either
    # incoming heading. Its obstacle/congestion cost is invariant per edge.
    link_costs = {}
    for a, b in starts:
        coord = (xi[b[0]], yi[b[1]])
        if coord in blocked:
            continue
        axis = 0 if a[1] == b[1] else 1
        state = (*coord, axis)
        distance[state] = 0.0
        parent[state] = None
        origins[state] = a
        heappush(queue, (heuristic(*coord), 0.0, state))
    while queue:
        _, cost, state = heappop(queue)
        if cost != distance[state]:
            continue
        i, j, direction = state
        if (i, j) in goal:
            path = [(xs[i], ys[j]), goal[(i, j)]]
            cursor = state
            while parent[cursor] is not None:
                cursor = parent[cursor]
                path.insert(0, (xs[cursor[0]], ys[cursor[1]]))
            path.insert(0, origins[cursor])
            return _simplify(path)
        a = (xs[i], ys[j])
        for ni, nj, axis in ((i-1, j, 0), (i+1, j, 0), (i, j-1, 1), (i, j+1, 1)):
            if not (0 <= ni < len(xs) and 0 <= nj < len(ys)) or (ni, nj) in blocked:
                continue
            b = (xs[ni], ys[nj])
            key = tuple(sorted(((i, j), (ni, nj))))
            if key not in link_costs:
                link_costs[key] = (math.inf if any(_crosses(a, b, r) for r in rects) else
                                  abs(b[0]-a[0]) + abs(b[1]-a[1]) + _congestion(a, b, tracks))
            travel = link_costs[key]
            if travel == math.inf:
                continue
            next_state = (ni, nj, axis)
            new_cost = cost + travel + (28 if axis != direction else 0)
            if new_cost < distance.get(next_state, math.inf):
                distance[next_state] = new_cost
                parent[next_state] = state
                heappush(queue, (new_cost + heuristic(ni, nj), new_cost, next_state))
    return None


def route_compiled_edges(nodes, edges, groups, canvas):
    """Set auto edges to cardinal, obstacle-aware polylines in stable order.

    The fallback stays visibly orthogonal and remains diagnosable by quality;
    no failure hides an edge, changes topology, or silently drops a label.
    """
    by_id = {node['id']: node for node in nodes}
    obstacles = []
    for node in nodes:
        x, y = node['position']; w, h = node['size']
        obstacles.append((node['id'], (x-CLEARANCE, y-CLEARANCE, x+w+CLEARANCE, y+h+CLEARANCE)))
    for group in groups:
        x, y, _, _ = group['bounds']
        width = visual_units(group['label'].upper()) * 8.12 + len(group['label']) * 1.12
        obstacles.append(('@group:' + group['id'], (x+12, y+10, x+24+width, y+39)))
    bundles = defaultdict(list)
    for edge in edges:
        bundles[tuple(sorted((edge['from'], edge['to'])))].append(edge)
    tracks = []
    # Earlier narrative steps claim the direct lanes; feedback edges detour.
    order = sorted(range(len(edges)), key=lambda i: (edges[i].get('step') is None, edges[i].get('step') or 0, i))
    for edge in (edges[i] for i in order):
        bundle = bundles[tuple(sorted((edge['from'], edge['to'])))]
        offset = (bundle.index(edge) - (len(bundle)-1)/2) * TRACK_SPACING
        source, target = by_id[edge['from']], by_id[edge['to']]
        points = _route(source, target, obstacles, tracks, canvas, offset)
        edge['route'] = 'orthogonal'
        edge.pop('points', None)
        if points:
            edge['points'] = points
            tracks.extend(zip(points, points[1:]))
