import json
from copy import deepcopy
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from anidiagram.composition import LAYOUTS, compile_plan_v02
from anidiagram.label_placement import place_labels
from anidiagram.quality import quality_report
from anidiagram.renderer_svg import render_svg
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style
from anidiagram.text_layout import text_block_layout

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.w3.org/2000/svg'}


def plan():
    return {'version': '0.2', 'semantic': {
        'title': 'Obstacle routing', 'intent': {'diagram_kind': 'architecture', 'primary_question': 'How does the request travel?', 'audience': ['technical'], 'scope': 'Three services'}, 'entities': [
            {'id': key, 'label': key.upper(), 'kind': 'server', 'role': 'process'} for key in ('a', 'b', 'c')],
        'relations': [
            {'id': 'a-b', 'from': 'a', 'to': 'b', 'kind': 'request', 'label': 'First request'},
            {'id': 'b-c', 'from': 'b', 'to': 'c', 'kind': 'request', 'label': 'Next request'},
            {'id': 'a-c', 'from': 'a', 'to': 'c', 'kind': 'request', 'label': 'Skip intermediate'},
        ]}, 'presentation': {'layout': 'pipeline', 'motion': 'off'}}


class P2LayoutTest(unittest.TestCase):
    def test_compiled_routes_avoid_intermediate_node(self):
        spec = compile_plan_v02(plan())
        self.assertTrue(all(edge['route'] == 'orthogonal' for edge in spec['edges']))
        self.assertTrue(all(edge.get('points') for edge in spec['edges']))
        issues = quality_report(compile_scene(spec), load_style())['issues']
        self.assertFalse([issue for issue in issues if 'collision' in issue['code']], issues)

    def test_parallel_relations_have_separate_tracks(self):
        value = plan()
        value['semantic']['relations'] = [dict(value['semantic']['relations'][0], id='r1'),
                                          dict(value['semantic']['relations'][0], id='r2', direction='bidirectional')]
        spec = compile_plan_v02(value)
        self.assertNotEqual(spec['edges'][0].get('points'), spec['edges'][1].get('points'))
        self.assertEqual('bidirectional', spec['edges'][1]['direction'])
        self.assertGreaterEqual(abs(spec['edges'][0]['points'][0][1] - spec['edges'][1]['points'][0][1]), 8)

    def test_caption_is_two_lines_ellipsized_with_full_hover_text(self):
        value = plan()
        description = 'Preserve this complete description with several additional details for accessible hover disclosure. ' * 3
        value['semantic']['entities'][0]['description'] = description
        spec = compile_plan_v02(value)
        self.assertEqual(description, spec['nodes'][0]['caption'])
        layout = text_block_layout('Title', description, 110, 108)
        self.assertEqual(2, len(layout.caption_lines))
        self.assertTrue(layout.caption_lines[-1].endswith('…'))
        tree = ET.fromstring(render_svg(compile_scene(spec), load_style()))
        node = tree.find(".//s:g[@id='node-a']", NS)
        self.assertIn(description, node.find('s:title', NS).text)
        self.assertEqual('start', node.find('.//s:text[@class="node-text-block"]', NS).get('text-anchor'))
        self.assertFalse(node.findall('.//s:text[@class="step-label"]', NS))
        report = quality_report(compile_scene(spec), load_style())
        self.assertFalse(any(issue['code'] == 'caption_overflow' for issue in report['issues']))
        self.assertTrue(any(issue['code'] == 'caption_truncated' for issue in report['advisories']))

    def test_plan_relations_are_semantically_invariant_across_layouts(self):
        value = plan()
        value['semantic']['relations'][0].update(direction='undirected', condition='ready', protocol='RPC')
        original = deepcopy(value)
        signatures = []
        for layout in sorted(LAYOUTS):
            value['presentation']['layout'] = layout
            spec = compile_plan_v02(value)
            signatures.append([(e['semantic_relation_id'], e['from'], e['to'], e['direction'], e.get('condition'), e.get('protocol'), e['label']) for e in spec['edges']])
        self.assertTrue(all(signature == signatures[0] for signature in signatures))
        self.assertEqual(original['semantic'], value['semantic'])

    def test_authored_script_points_and_direction_stay_unchanged(self):
        spec = {'version': '0.4', 'nodes': [{'id': 'a', 'label': 'A', 'position': [30, 130], 'size': [220, 108]}, {'id': 'b', 'label': 'B', 'position': [450, 130], 'size': [220, 108]}],
                'edges': [{'from': 'a', 'to': 'b', 'direction': 'undirected', 'route': 'points', 'points': [[250, 180], [320, 230], [450, 180]]}]}
        original = deepcopy(spec)
        scene = compile_scene(spec)
        render_svg(scene, load_style())
        self.assertEqual(original, spec)
        self.assertEqual(tuple(map(tuple, spec['edges'][0]['points'])), scene.edges[0].points)

    def test_rag_routes_and_labels_have_no_geometry_collisions(self):
        value = json.loads((ROOT / 'examples/enterprise-rag-production-illustrated.plan.json').read_text())
        value['presentation']['layout'] = 'layered'
        report = quality_report(compile_scene(compile_plan_v02(value)), load_style())
        self.assertFalse([issue for issue in report['issues'] if 'collision' in issue['code'] or issue['severity'] == 'error'], report['issues'])

    def test_swimlane_members_fit_below_each_group_heading(self):
        value = plan()
        value['presentation']['layout'] = 'swimlane'
        value['semantic']['groups'] = [
            {'id': 'team', 'label': 'Team', 'kind': 'lane', 'members': ['a', 'b']},
            {'id': 'system', 'label': 'System', 'kind': 'lane', 'members': ['c']}]
        spec = compile_plan_v02(value)
        self.assertEqual([['a', 'b'], ['c']], [group['members'] for group in spec['groups']])
        report = quality_report(compile_scene(spec), load_style())
        self.assertFalse([issue for issue in report['issues'] if issue['code'] in {
            'node_out_of_group', 'node_group_title_collision', 'group_out_of_bounds', 'group_overlap'}])

    def test_self_loop_stays_visible_outside_node(self):
        value = plan()
        value['semantic']['relations'] = [{'id': 'retry', 'from': 'a', 'to': 'a', 'kind': 'feedback', 'label': 'Retry'}]
        spec = compile_plan_v02(value)
        points = spec['edges'][0]['points']
        self.assertGreaterEqual(len(points), 4)
        self.assertNotEqual(points[0], points[-1])
        self.assertFalse([issue for issue in quality_report(compile_scene(spec), load_style())['issues'] if 'collision' in issue['code']])

    def test_decision_icon_and_text_have_separate_zones(self):
        spec = {'version': '0.4', 'nodes': [{'id': 'ready', 'label': 'Ready?', 'caption': 'Policy valid', 'shape': 'decision', 'icon': 'shield', 'position': [140, 180], 'size': [260, 160]}]}
        tree = ET.fromstring(render_svg(compile_scene(spec), load_style()))
        self.assertIsNotNone(tree.find('.//s:g[@class="decision-icon-zone"]', NS))


if __name__ == '__main__':
    unittest.main()
