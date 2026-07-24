import json
import unittest
from pathlib import Path

from anidiagram.illustrated_expansion_batch_5 import (
    expansion_batch_5_definition,
    expansion_batch_5_icon_ids,
)
from anidiagram.illustrated_expansion_batch_5_motion import (
    ILLUSTRATED_V6_REVIEW_ICON_PERFORMANCES,
    ILLUSTRATED_V6_REVIEW_REST_AT,
)
from anidiagram.illustrated_registry import illustrated_icon_ids
from scripts.render_illustrated_expansion_batch_5_motion_review import (
    build_motion_review_manifest,
    build_review_runtime,
    render_motion_review_html,
    render_motion_review_svg,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ("developer", "agent-team", "assistant", "human-reviewer", "llm", "reasoning")
RUNTIME_FUNCTIONS = {
    "developer": "playIllustratedDeveloper",
    "agent-team": "playIllustratedAgentTeam",
    "assistant": "playIllustratedAssistant",
    "human-reviewer": "playIllustratedHumanReviewer",
    "llm": "playIllustratedLlm",
    "reasoning": "playIllustratedReasoning",
}


class IllustratedExpansionBatch5MotionReviewTest(unittest.TestCase):
    def test_static_acceptance_is_frozen_while_motion_stays_review_only(self):
        acceptance = json.loads(
            (ROOT / "assets" / "illustrated" / "reviews" / "2.5.0-batch-5-static-acceptance.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("static-confirmed-motion-pending", acceptance["status"])
        self.assertEqual(list(EXPECTED), acceptance["approved_icons"])
        self.assertEqual("pending-human-review", acceptance["motion_acceptance"]["status"])
        self.assertFalse(acceptance["public_registry_changed"])
        self.assertEqual(56, len(illustrated_icon_ids()))
        self.assertTrue(set(EXPECTED).issubset(illustrated_icon_ids()))

    def test_review_contract_covers_exactly_the_six_static_approved_candidates(self):
        contract = json.loads(
            (ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v6.review.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("2.5.0-candidate", contract["icon_system_version"])
        self.assertEqual("illustrated-performance-v5", contract["extends"])
        self.assertEqual("visual-review", contract["status"])
        self.assertFalse(contract["public_showcase_enabled"])
        self.assertEqual("explicit-review-only", contract["selection_policy"])
        self.assertEqual(set(EXPECTED), {item["icon"] for item in contract["performances"]})
        for item in contract["performances"]:
            definition = expansion_batch_5_definition(item["icon"])
            self.assertEqual(ILLUSTRATED_V6_REVIEW_ICON_PERFORMANCES[item["icon"]], item["id"])
            self.assertEqual(ILLUSTRATED_V6_REVIEW_REST_AT[item["icon"]], item["rest_at"])
            self.assertLessEqual(set(item["primary_parts"]), set(definition.parts))

    def test_review_page_emits_six_explicit_candidate_timelines_with_unique_parts(self):
        manifest = build_motion_review_manifest()
        svg = render_motion_review_svg()
        html = render_motion_review_html(svg, manifest)
        self.assertEqual("illustrated", manifest["icon_system"])
        self.assertEqual("2.5.0-candidate", manifest["icon_system_version"])
        self.assertEqual(6, len(manifest["icons"]))
        self.assertEqual(set(EXPECTED), {entry["icon"] for entry in manifest["icons"]})
        self.assertEqual(6, html.count('class="semantic-icon semantic-icon-illustrated"'))
        self.assertIn('id="anidiagram-motion-manifest"', html)
        for entry in manifest["icons"]:
            definition = expansion_batch_5_definition(entry["icon"])
            self.assertEqual("illustrated-performance-v6-review", entry["motion_contract"])
            self.assertEqual("visual-review", entry["motion_status"])
            self.assertEqual(set(definition.parts), set(entry["parts"]))
            for selector in entry["parts"].values():
                self.assertEqual(1, html.count(f'id="{selector[1:]}"'), selector)

    def test_generated_runtime_dispatches_every_v6_review_performance(self):
        source = build_review_runtime()
        for icon, performance in ILLUSTRATED_V6_REVIEW_ICON_PERFORMANCES.items():
            function_name = RUNTIME_FUNCTIONS[icon]
            self.assertIn(f"function {function_name}", source)
            self.assertIn(f'performances["{performance}"] = {function_name}', source)


if __name__ == "__main__":
    unittest.main()
