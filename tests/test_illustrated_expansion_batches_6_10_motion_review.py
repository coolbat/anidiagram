import json
import unittest
from pathlib import Path

from anidiagram.illustrated_expansion_batches_6_10 import expansion_6_10_definition, expansion_6_10_icon_ids
from anidiagram.illustrated_expansion_batches_6_10_motion import (
    ILLUSTRATED_V7_REVIEW_ICON_PERFORMANCES,
    ILLUSTRATED_V7_REVIEW_MOTION_SPECS,
)
from anidiagram.illustrated_registry import illustrated_icon_ids
from scripts.build_illustrated_v7_review_contract import build_contract
from scripts.render_illustrated_expansion_batches_6_10_motion_review import (
    build_motion_review_manifest,
    build_review_runtime,
    render_motion_review_html,
    render_motion_review_svg,
)


ROOT = Path(__file__).resolve().parents[1]


class IllustratedExpansionBatches6To10MotionReviewTest(unittest.TestCase):
    def test_static_acceptance_is_frozen_and_batch5_motion_is_approved(self):
        static = json.loads((ROOT / "assets/illustrated/reviews/2.5.0-batches-6-10-static-acceptance.json").read_text(encoding="utf-8"))
        batch5 = json.loads((ROOT / "assets/illustrated/reviews/2.5.0-batch-5-motion-acceptance.json").read_text(encoding="utf-8"))
        self.assertEqual("static-confirmed-motion-pending", static["status"])
        self.assertEqual(30, static["approved_icon_count"])
        self.assertEqual("pending-human-review", static["motion_acceptance"]["status"])
        self.assertEqual("approved", batch5["status"])
        self.assertEqual(6, batch5["rest_pose_verified"])
        self.assertEqual(6, batch5["reduced_motion_verified"])
        self.assertFalse(static["public_registry_changed"])
        self.assertEqual(56, len(illustrated_icon_ids()))

    def test_motion_specs_cover_exactly_thirty_icons_with_valid_phase_parts(self):
        icon_ids = expansion_6_10_icon_ids()
        self.assertEqual(set(icon_ids), set(ILLUSTRATED_V7_REVIEW_MOTION_SPECS))
        self.assertEqual(set(icon_ids), set(ILLUSTRATED_V7_REVIEW_ICON_PERFORMANCES))
        self.assertEqual({"draw", "cascade", "fan", "oscillate", "sweep", "bounce"},
                         {spec["recipe"] for spec in ILLUSTRATED_V7_REVIEW_MOTION_SPECS.values()})
        for icon_id in icon_ids:
            definition = expansion_6_10_definition(icon_id)
            spec = ILLUSTRATED_V7_REVIEW_MOTION_SPECS[icon_id]
            referenced = set(spec["prepare_parts"]) | set(spec["action_parts"]) | set(spec["result_parts"])
            with self.subTest(icon=icon_id):
                self.assertLessEqual(referenced, set(definition.parts))
                self.assertTrue(spec["prepare_parts"])
                self.assertTrue(spec["action_parts"])
                self.assertTrue(spec["result_parts"])
                self.assertGreaterEqual(spec["rest_at"], 1.8)

    def test_review_contract_matches_specs_and_extends_batch5_review(self):
        contract = build_contract()
        self.assertEqual("illustrated-performance-v7-review", contract["contract"])
        self.assertEqual("illustrated-performance-v6-review", contract["extends"])
        self.assertEqual("visual-review", contract["status"])
        self.assertFalse(contract["public_showcase_enabled"])
        self.assertEqual(30, len(contract["performances"]))
        for item in contract["performances"]:
            self.assertEqual(ILLUSTRATED_V7_REVIEW_ICON_PERFORMANCES[item["icon"]], item["id"])
            self.assertLessEqual(set(item["primary_parts"]), set(expansion_6_10_definition(item["icon"]).parts))

    def test_review_page_emits_thirty_timelines_and_five_switchable_panels(self):
        manifest = build_motion_review_manifest()
        svg = render_motion_review_svg()
        html = render_motion_review_html(svg, manifest)
        self.assertEqual(30, len(manifest["icons"]))
        self.assertEqual(30, html.count('class="semantic-icon semantic-icon-illustrated"'))
        self.assertEqual(5, html.count('class="motion-batch-panel"'))
        self.assertIn('id="anidiagram-motion-manifest"', html)
        for entry in manifest["icons"]:
            self.assertEqual("illustrated-performance-v7-review", entry["motion_contract"])
            self.assertEqual("visual-review", entry["motion_status"])
            self.assertEqual(set(expansion_6_10_definition(entry["icon"]).parts), set(entry["parts"]))
            for selector in entry["parts"].values():
                self.assertEqual(1, html.count(f'id="{selector[1:]}"'), selector)

    def test_generated_runtime_registers_all_thirty_performances(self):
        source = build_review_runtime()
        self.assertIn("function playIllustratedV7Configured", source)
        for performance in ILLUSTRATED_V7_REVIEW_ICON_PERFORMANCES.values():
            self.assertIn(f'performances["{performance}"] = playIllustratedV7Configured;', source)


if __name__ == "__main__": unittest.main()
