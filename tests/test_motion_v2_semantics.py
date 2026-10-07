import unittest
from pathlib import Path

from anidiagram.motion_manifest_v2 import build_motion_manifest
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style

ROOT = Path(__file__).resolve().parents[1]


class MotionV2SemanticsTests(unittest.TestCase):
    def manifest(self, *, mode='ambient', kinds=('request', 'response', 'async', 'stream', 'reject'), policy=None):
        data = {
            'version': '0.3', 'motion': {'profile': 'expressive'},
            'nodes': [{'id': f'n{i}', 'label': f'N{i}', 'icon': 'api', 'position': [30+i*170, 150], 'size': [120, 70]} for i in range(len(kinds)+1)],
            'edges': [{'from': f'n{i}', 'to': f'n{i+1}', 'semantic_kind': kind,
                       'importance': 'primary' if i < 2 else 'supporting'} for i, kind in enumerate(kinds)],
        }
        if policy is not None:
            data['motion_policy'] = policy
        return build_motion_manifest(compile_scene(data), load_style(ROOT/'styles/minimal-light.json'), mode=mode)

    def test_semantic_motion_overlays_keep_canonical_effect_ids(self):
        manifest = self.manifest()
        self.assertEqual(['sync', 'sync', 'async', 'stream', 'failure'], [e['signal_semantic'] for e in manifest['edges']])
        self.assertEqual(['comet', 'comet', 'packet', 'stream', 'comet'], [e['motion_kind'] for e in manifest['edges']])
        self.assertTrue(all(e['speed_px_per_second'] == 180 for e in manifest['edges']))
        self.assertEqual(0.35, manifest['edges'][2]['departure_delay'])
        self.assertEqual('#dc2626', manifest['edges'][4]['signal_color'])

    def test_default_budget_reserves_primary_edges_and_limits_icons(self):
        manifest = self.manifest()
        stage = manifest['stage']
        self.assertEqual([0, 1], stage['active_edge_indices'])
        self.assertEqual([2, 3, 4], stage['hover_edge_indices'])
        self.assertLessEqual(len(stage['active_icon_node_ids']) + len(stage['active_edge_indices']), 5)
        self.assertEqual(4, stage['beat_seconds'])
        self.assertEqual('ambient', manifest['mode'])

    def test_explicit_showcase_budget_is_honored_and_zero_disables(self):
        manifest = self.manifest(policy={'max_active_flow_edges': 0, 'max_active_pulse_nodes': 8})
        self.assertEqual([], manifest['stage']['active_edge_indices'])
        self.assertEqual([], manifest['stage']['hover_edge_indices'])
        self.assertEqual(6, len(manifest['stage']['active_icon_node_ids']))

    def test_event_driven_is_explicit_and_uses_arrival_trigger(self):
        manifest = self.manifest(mode='event-driven')
        self.assertEqual('signal-arrival-events', manifest['sequence'])
        self.assertEqual(0.15, manifest['event_driven']['arrival_feedback_seconds'])
        self.assertTrue(all(icon['trigger'] == 'edge-arrival' for icon in manifest['icons']))

    def test_off_profile_cannot_reenable_semantic_signals(self):
        scene = compile_scene({'version':'0.3','motion':{'profile':'off'},'nodes':[{'id':'a','label':'A','position':[0,0],'size':[100,60]},{'id':'b','label':'B','position':[200,0],'size':[100,60]}], 'edges':[{'from':'a','to':'b','semantic_kind':'request'}]})
        manifest = build_motion_manifest(scene, load_style(ROOT/'styles/minimal-light.json'), mode='event-driven')
        self.assertFalse(manifest['edges'][0]['active'])
        self.assertEqual([], manifest['stage']['active_edge_indices'])

if __name__ == '__main__':
    unittest.main()
