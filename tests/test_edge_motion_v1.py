import hashlib
import json
import unittest
from pathlib import Path

from anidiagram.edge_motion import (
    CANONICAL_EDGE_MOTION,
    EDGE_MOTION_CONTRACT,
    EDGE_MOTION_VERSION,
    LEGACY_EDGE_MOTION_ALIASES,
    canonical_edge_motion,
)
from anidiagram.renderer_html_runtime import render_html_runtime
from anidiagram.renderer_svg import render_svg
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]


class EdgeMotionV1Test(unittest.TestCase):
    def _scene(self, effect: str):
        return compile_scene(
            {
                "version": "0.3",
                "canvas": {"width": 560, "height": 300},
                "title": {"text": "Edge Motion", "subtitle": "contract proof"},
                "motion": {"profile": "showcase-v1", "edge": {"preset": effect}},
                "nodes": [
                    {"id": "a", "label": "A", "position": [60, 150], "size": [140, 72]},
                    {"id": "b", "label": "B", "position": [360, 150], "size": [140, 72]},
                ],
                "edges": [{"from": "a", "to": "b", "effect": {"preset": effect}}],
            }
        )

    def test_contract_has_six_canonical_ids_and_complete_legacy_aliases(self):
        contract = json.loads(
            (ROOT / "assets" / "edge-motion" / "edge-motion-v1.json").read_text(encoding="utf-8")
        )
        self.assertEqual(EDGE_MOTION_CONTRACT, contract["id"])
        self.assertEqual(EDGE_MOTION_VERSION, contract["version"])
        self.assertEqual(CANONICAL_EDGE_MOTION, frozenset(contract["canonical_effects"]))
        self.assertEqual(LEGACY_EDGE_MOTION_ALIASES, contract["legacy_aliases"])

    def test_legacy_packet_alias_renders_one_borderless_packet_without_stream(self):
        scene = self._scene("flow-arrow")
        svg = render_svg(scene, load_style(ROOT / "styles" / "minimal-light.json"))
        self.assertEqual("packet-flow", canonical_edge_motion("flow-arrow"))
        self.assertEqual(1, svg.count('class="edge-particle edge-packet"'))
        self.assertIn('stroke="none"', svg)
        self.assertNotIn("edge-flow-stream-flow", svg)

    def test_legacy_stream_alias_renders_moving_dash_without_packet(self):
        scene = self._scene("dynamic-dash")
        svg = render_svg(scene, load_style(ROOT / "styles" / "minimal-light.json"))
        self.assertEqual("stream-flow", canonical_edge_motion("dynamic-dash"))
        self.assertEqual(1, svg.count("edge-flow-stream-flow"))
        self.assertNotIn('class="edge-particle edge-packet"', svg)

    def test_comet_flow_renders_one_head_and_three_borderless_fading_echoes(self):
        scene = self._scene("ghost-flow")
        svg = render_svg(scene, load_style(ROOT / "styles" / "minimal-light.json"))
        self.assertEqual("comet-flow", canonical_edge_motion("ghost-flow"))
        self.assertEqual(1, svg.count("edge-comet-head"))
        self.assertEqual(3, svg.count("edge-comet-tail"))
        self.assertEqual(4, svg.count('class="edge-particle edge-comet'))
        self.assertNotIn("edge-flow-stream-flow", svg)
        self.assertNotIn('class="edge-particle edge-packet"', svg)

    def test_new_html_uses_versioned_manifest_and_additive_runtime(self):
        scene = self._scene("packet-flow")
        html = render_html_runtime(scene, load_style(ROOT / "styles" / "minimal-light.json"))
        self.assertIn('"version": "motion-manifest-0.2"', html)
        self.assertIn('"edge_motion_contract": "edge-motion-v1"', html)
        self.assertIn('"edge_motion_version": "1.0.0"', html)
        self.assertIn("AniDiagramEdgeMotion", html)
        self.assertIn('stroke: "none"', html)
        self.assertIn("runtime-edge-comet", html)

    def test_comet_manifest_has_one_head_and_three_fading_echoes(self):
        scene = self._scene("comet-flow")
        html = render_html_runtime(scene, load_style(ROOT / "styles" / "minimal-light.json"))
        marker = '<script type="application/json" id="anidiagram-motion-manifest">'
        start = html.index(marker) + len(marker)
        manifest = json.loads(html[start : html.index("</script>", start)])
        entry = manifest["edges"][0]
        self.assertEqual("comet-flow", entry["effect"])
        self.assertEqual("comet", entry["motion_kind"])
        self.assertEqual("solid-dot", entry["particle"])
        self.assertEqual("fading-echoes", entry["trail"])
        self.assertEqual(3, entry["trail_count"])

    def test_frozen_release_hashes_match_approved_sources(self):
        release = json.loads(
            (ROOT / "assets" / "edge-motion" / "releases" / "v1.0.0.json").read_text(
                encoding="utf-8"
            )
        )
        acceptance = json.loads(
            (ROOT / release["paths"]["acceptance_record"]).read_text(encoding="utf-8")
        )
        contract = json.loads(
            (ROOT / release["paths"]["contract"]).read_text(encoding="utf-8")
        )
        self.assertEqual("frozen-approved-release", release["status"])
        self.assertEqual("confirmed", release["human_visual_acceptance"])
        self.assertEqual(4, release["canonical_dynamic_effect_count"])
        self.assertEqual("confirmed", acceptance["status"])
        self.assertFalse(acceptance["release_boundary"]["illustrated_2_4_candidate_promoted"])
        self.assertEqual("approved", contract["status"])
        self.assertEqual("frozen", contract["lifecycle"])
        for name, relative_path in release["paths"].items():
            expected = release["hashes"][f"{name}_sha256"]
            actual = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
            self.assertEqual(expected, actual, name)


if __name__ == "__main__":
    unittest.main()
