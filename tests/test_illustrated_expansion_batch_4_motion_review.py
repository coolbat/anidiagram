import json
import unittest
from pathlib import Path

from anidiagram.illustrated_expansion_batch_4 import (
    expansion_batch_4_definition,
    expansion_batch_4_icon_ids,
)
from anidiagram.illustrated_registry import illustrated_icon_ids
from anidiagram.illustrated_expansion_batch_4_motion import (
    ILLUSTRATED_V5_REVIEW_ICON_PERFORMANCES,
    ILLUSTRATED_V5_REVIEW_REST_AT,
)
from scripts.render_illustrated_expansion_batch_4_motion_review import (
    build_motion_review_manifest,
    render_motion_review_html,
    render_motion_review_svg,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ("vector-database", "knowledge-base", "gateway", "container")
RUNTIME_FUNCTIONS = {
    "vector-database": "playIllustratedVectorDatabase",
    "knowledge-base": "playIllustratedKnowledgeBase",
    "gateway": "playIllustratedGateway",
    "container": "playIllustratedContainer",
}


class IllustratedExpansionBatch4MotionReviewTest(unittest.TestCase):
    def test_static_acceptance_remains_frozen_after_public_24_promotion(self):
        acceptance = json.loads(
            (ROOT / "assets" / "illustrated" / "reviews" / "2.4.0-static-acceptance.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("static-confirmed-motion-pending", acceptance["status"])
        self.assertEqual(list(EXPECTED), acceptance["static_acceptance"]["approved_icons"])
        self.assertEqual("pending-human-review", acceptance["motion_acceptance"]["status"])
        self.assertEqual("illustrated-performance-v5-review", acceptance["motion_acceptance"]["review_contract"])
        self.assertEqual(16, acceptance["public_showcase"]["static_icon_count"])
        self.assertEqual(16, acceptance["public_showcase"]["automatic_motion_icon_count"])
        self.assertFalse(acceptance["public_showcase"]["public_registry_changed"])
        self.assertEqual(20, len(illustrated_icon_ids()))
        self.assertTrue(set(EXPECTED).issubset(illustrated_icon_ids()))

    def test_review_contract_covers_exactly_the_four_static_approved_candidates(self):
        contract = json.loads(
            (
                ROOT
                / "assets"
                / "illustrated"
                / "motion-contracts"
                / "illustrated-performance-v5.review.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual("2.4.0-candidate", contract["icon_system_version"])
        self.assertEqual("illustrated-performance-v4", contract["extends"])
        self.assertEqual("visual-review", contract["status"])
        self.assertFalse(contract["public_showcase_enabled"])
        self.assertEqual("explicit-review-only", contract["selection_policy"])
        self.assertEqual(set(EXPECTED), {item["icon"] for item in contract["performances"]})
        for item in contract["performances"]:
            definition = expansion_batch_4_definition(item["icon"])
            self.assertEqual(ILLUSTRATED_V5_REVIEW_ICON_PERFORMANCES[item["icon"]], item["id"])
            self.assertEqual(ILLUSTRATED_V5_REVIEW_REST_AT[item["icon"]], item["rest_at"])
            self.assertLessEqual(set(item["primary_parts"]), set(definition.parts))

    def test_review_page_emits_four_explicit_candidate_timelines_with_unique_parts(self):
        manifest = build_motion_review_manifest()
        svg = render_motion_review_svg()
        html = render_motion_review_html(svg, manifest)

        self.assertEqual("illustrated", manifest["icon_system"])
        self.assertEqual("2.4.0-candidate", manifest["icon_system_version"])
        self.assertEqual(4, len(manifest["icons"]))
        self.assertEqual(set(EXPECTED), {entry["icon"] for entry in manifest["icons"]})
        self.assertEqual(4, html.count('class="semantic-icon semantic-icon-illustrated"'))
        self.assertIn('id="anidiagram-motion-manifest"', html)
        for entry in manifest["icons"]:
            definition = expansion_batch_4_definition(entry["icon"])
            self.assertEqual("illustrated-performance-v5-review", entry["motion_contract"])
            self.assertEqual("visual-review", entry["motion_status"])
            self.assertEqual("explicit-review-only", entry["selection_policy"])
            self.assertEqual(set(definition.parts), set(entry["parts"]))
            for selector in entry["parts"].values():
                self.assertEqual(1, html.count(f'id="{selector[1:]}"'), selector)

    def test_runtime_dispatches_every_v5_review_performance(self):
        source = (
            ROOT / "runtime" / "illustrated-performance-v5-review-runtime.js"
        ).read_text(encoding="utf-8")
        for icon, performance in ILLUSTRATED_V5_REVIEW_ICON_PERFORMANCES.items():
            function_name = RUNTIME_FUNCTIONS[icon]
            self.assertIn(f"function {function_name}", source)
            self.assertIn(f'performances["{performance}"] = {function_name}', source)


if __name__ == "__main__":
    unittest.main()
