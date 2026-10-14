import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from anidiagram.planner import compile_plan
from anidiagram.quality_geometry import rendered_route
from anidiagram.renderer_svg import edge_points, node_box, render_svg, route_points
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]


class EdgeRouteEndpointsTest(unittest.TestCase):
    def _scene(self, points=None):
        edge = {'from': 'a', 'to': 'b', 'label': ''}
        if points is not None:
            edge.update(route='points', points=points)
        return compile_scene({
            'version': '0.4', 'canvas': {'width': 700, 'height': 500},
            'nodes': [
                {'id': 'a', 'label': 'A', 'position': [50, 200], 'size': [160, 80]},
                {'id': 'b', 'label': 'B', 'position': [490, 200], 'size': [160, 80]},
            ],
            'edges': [edge],
        })

    def test_explicit_routes_keep_authored_endpoints_in_svg_and_quality(self):
        for points in (
            [[210, 240], [490, 240]],
            [[210, 240], [250, 240], [250, 150], [450, 150], [450, 240], [490, 240]],
        ):
            with self.subTest(points=points):
                scene = self._scene(points)
                boxes = {node.node_id: node_box(node) for node in scene.nodes}
                expected = tuple(map(tuple, points))
                self.assertEqual(expected, tuple(route_points(scene.edges[0], boxes)))
                self.assertEqual((expected[0], expected[-1]), edge_points(scene.edges[0], boxes))
                self.assertEqual(expected, tuple(rendered_route(scene.edges[0], boxes)))
                tree = ET.fromstring(render_svg(scene, load_style()))
                path = next(el for el in tree.iter() if el.get('class') == 'edge-draw').get('d')
                self.assertTrue(path.startswith('M 210.0 240.0 '), path)
                self.assertTrue(path.endswith('L 490.0 240.0'), path)

    def test_automatic_straight_edge_keeps_existing_node_gap(self):
        scene = self._scene()
        boxes = {node.node_id: node_box(node) for node in scene.nodes}
        self.assertEqual([(222.0, 240.0), (478.0, 240.0)], route_points(scene.edges[0], boxes))

    def test_compiled_skip_lane_edges_use_distinct_final_routes_and_normal_ports(self):
        plan = json.loads((ROOT / 'examples/loop-engineering-minimal-light.plan.json').read_text())
        for index, (source, target) in enumerate((
            ('human-engineer', 'external-state'),
            ('automation-heartbeat', 'verifier-agent'),
            ('automation-heartbeat', 'tool-connectors'),
        )):
            plan['semantic']['relations'].append({
                'id': f'skip-{index}', 'from': source, 'to': target,
                'kind': 'data-flow', 'direction': 'forward', 'importance': 'supporting',
            })
        spec = compile_plan(plan)
        nodes = {node['id']: node for node in spec['nodes']}
        edges = [edge for edge in spec['edges'] if edge['semantic_relation_id'].startswith('skip-')]
        self.assertEqual(3, len({tuple(map(tuple, edge['points'])) for edge in edges}))
        trunks = []
        for edge in edges:
            self.assertEqual('orthogonal', edge['route'])
            trunks.append({a[0] for a, b in zip(edge['points'], edge['points'][1:])
                           if a[0] == b[0] and abs(a[1] - b[1]) > 200})
            a, b = edge['points'][-2:]
            target = nodes[edge['to']]
            x, y = target['position']
            width, height = target['size']
            if a[0] == b[0]:
                self.assertIn(b[1], (y, y + height))
                self.assertLess(x, b[0])
                self.assertLess(b[0], x + width)
            else:
                self.assertIn(b[0], (x, x + width))
                self.assertLess(y, b[1])
                self.assertLess(b[1], y + height)
        for index, trunk in enumerate(trunks):
            for other in trunks[index + 1:]:
                self.assertTrue(trunk.isdisjoint(other), trunks)
        scene = compile_scene(spec)
        boxes = {node.node_id: node_box(node) for node in scene.nodes}
        for edge in scene.edges:
            if edge.semantic_relation_id.startswith('skip-'):
                self.assertEqual(edge.points, tuple(rendered_route(edge, boxes)))


if __name__ == '__main__':
    unittest.main()
