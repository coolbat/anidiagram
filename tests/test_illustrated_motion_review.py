import json
import unittest
from pathlib import Path

from anidiagram.illustrated_character_v2_icons import character_v2_definition
from anidiagram.illustrated_registry import illustrated_definition, illustrated_icon_ids
from anidiagram.illustrated_public_motion import ILLUSTRATED_PUBLIC_MOTION_SPECS
from anidiagram.motion_manifest import (
    ILLUSTRATED_ICON_PERFORMANCES,
    ILLUSTRATED_REST_AT,
    ILLUSTRATED_V2_ICON_PERFORMANCES,
    ILLUSTRATED_V2_REST_AT,
    ILLUSTRATED_V3_ADDITIONAL_ICON_PERFORMANCES,
    ILLUSTRATED_V3_ADDITIONAL_REST_AT,
    ILLUSTRATED_V3_ICON_PERFORMANCES,
    ILLUSTRATED_V3_REST_AT,
)
from anidiagram.renderer_html_runtime import _runtime_source, render_html_runtime
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = {
    "agent": "playIllustratedAgentReason",
    "operator": "playIllustratedOperatorOperate",
    "tool": "playIllustratedToolExecute",
    "output": "playIllustratedOutputDeliver",
    "database": "playIllustratedDatabasePersist",
    "api": "playIllustratedApiRoute",
    "search": "playIllustratedSearchDiscover",
    "memory": "playIllustratedMemoryRecall",
}
FUNCTIONS.update({
    "file": "playIllustratedFileAttach",
    "folder": "playIllustratedFolderStore",
    "cloud": "playIllustratedCloudTransfer",
    "shield": "playIllustratedShieldLock",
    "user": "playIllustratedUserInteract",
    "server": "playIllustratedServerCompute",
    "ai-model": "playIllustratedAiModelInfer",
    "message-queue": "playIllustratedMessageQueue",
    "vector-database": "playIllustratedVectorDatabase",
    "knowledge-base": "playIllustratedKnowledgeBase",
    "gateway": "playIllustratedGateway",
    "container": "playIllustratedContainer",
})
FUNCTIONS.update({
    "developer": "playIllustratedDeveloper",
    "agent-team": "playIllustratedAgentTeam",
    "assistant": "playIllustratedAssistant",
    "human-reviewer": "playIllustratedHumanReviewer",
    "llm": "playIllustratedLlm",
    "reasoning": "playIllustratedReasoning",
})
FUNCTIONS.update({icon: "playIllustratedPublicConfigured" for icon in ILLUSTRATED_PUBLIC_MOTION_SPECS})


def _archived_parts(version: str, icon: str) -> set[str]:
    catalog = json.loads(
        (ROOT / "assets" / "illustrated" / "snapshots" / f"catalog-{version}.json").read_text(encoding="utf-8")
    )
    return set(next(item for item in catalog["icons"] if item["id"] == icon)["parts"])


def _manifest(html: str) -> dict:
    marker = '<script type="application/json" id="anidiagram-motion-manifest">'
    start = html.index(marker) + len(marker)
    return json.loads(html[start : html.index("</script>", start)])


class IllustratedMotionReviewTest(unittest.TestCase):
    def test_v1_contract_remains_an_immutable_four_icon_archive(self):
        contract = json.loads(
            (ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("2.0.0", contract["icon_system_version"])
        self.assertEqual({"agent", "operator", "tool", "output"}, {item["icon"] for item in contract["performances"]})
        for item in contract["performances"]:
            self.assertLessEqual(set(item["primary_parts"]), set(character_v2_definition(item["icon"]).parts))

    def test_v2_contract_matches_all_eight_public_icons(self):
        contract = json.loads(
            (ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v2.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual("2.1.0", contract["icon_system_version"])
        self.assertEqual("approved", contract["status"])
        self.assertEqual("confirmed", contract["human_visual_acceptance"])
        self.assertTrue(contract["public_showcase_enabled"])
        self.assertEqual("automatic-for-supported-showcase-icons", contract["selection_policy"])
        self.assertEqual(set(ILLUSTRATED_V2_ICON_PERFORMANCES), {item["icon"] for item in contract["performances"]})
        for item in contract["performances"]:
            self.assertEqual(ILLUSTRATED_V2_ICON_PERFORMANCES[item["icon"]], item["id"])
            self.assertEqual(ILLUSTRATED_V2_REST_AT[item["icon"]], item["rest_at"])
            self.assertLessEqual(set(item["primary_parts"]), _archived_parts("2.1.0", item["icon"]))

    def test_v3_contract_approves_all_twelve_public_icons(self):
        contract = json.loads(
            (ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v3.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual("2.2.0", contract["icon_system_version"])
        self.assertEqual("illustrated-performance-v3", contract["contract"])
        self.assertEqual("illustrated-performance-v2", contract["supersedes"])
        self.assertEqual("approved", contract["status"])
        self.assertEqual("confirmed", contract["human_visual_acceptance"])
        self.assertTrue(contract["public_showcase_enabled"])
        self.assertEqual("automatic-for-supported-showcase-icons", contract["selection_policy"])
        self.assertEqual(set(ILLUSTRATED_V3_ICON_PERFORMANCES), {item["icon"] for item in contract["performances"]})
        for item in contract["performances"]:
            self.assertEqual(ILLUSTRATED_V3_ICON_PERFORMANCES[item["icon"]], item["id"])
            self.assertEqual(ILLUSTRATED_V3_REST_AT[item["icon"]], item["rest_at"])
            self.assertLessEqual(set(item["primary_parts"]), _archived_parts("2.2.0", item["icon"]))

    def test_archived_twenty_icon_showcase_runs_on_the_current_v6_runtime(self):
        spec = json.loads(
            (ROOT / "examples" / "illustrated-2.4-showcase.diagram.json").read_text(encoding="utf-8")
        )
        self.assertTrue(all("effect" not in node for node in spec["nodes"]))
        spec["resolved_presentation"]["icon_system"]["version"] = "2.5.0"
        html = render_html_runtime(
            compile_scene(spec), load_style(ROOT / "styles" / "deep-tech.json"), runtime="gsap"
        )
        manifest = _manifest(html)

        self.assertEqual("illustrated", manifest["icon_system"])
        self.assertEqual("2.5.0", manifest["icon_system_version"])
        self.assertEqual(20, len(manifest["icons"]))
        self.assertEqual({node["icon"] for node in spec["nodes"]}, {entry["icon"] for entry in manifest["icons"]})
        for entry in manifest["icons"]:
            definition = illustrated_definition(entry["icon"])
            self.assertEqual(ILLUSTRATED_ICON_PERFORMANCES[entry["icon"]], entry["performance"])
            self.assertEqual(ILLUSTRATED_REST_AT[entry["icon"]], entry["rest_at"])
            self.assertEqual("illustrated-performance-v6", entry["motion_contract"])
            self.assertEqual("approved", entry["motion_status"])
            self.assertEqual("automatic-for-supported-showcase-icons", entry["selection_policy"])
            self.assertEqual("restore-authored-rest-pose", entry["cancel_behavior"])
            self.assertEqual("static-rest", entry["reduced_motion_behavior"])
            self.assertEqual("2.5.0", entry["asset_version"])
            self.assertEqual(set(definition.parts), set(entry["parts"]))
            for selector in entry["parts"].values():
                self.assertEqual(1, html.count(f'id="{selector[1:]}"'), selector)

    def test_explicit_motion_review_examples_now_resolve_to_the_approved_v2_contract(self):
        for filename, expected_count in (
            ("illustrated-motion-review.diagram.json", 4),
            ("illustrated-expansion-motion-review.diagram.json", 4),
        ):
            with self.subTest(filename=filename):
                spec = json.loads((ROOT / "examples" / filename).read_text(encoding="utf-8"))
                spec["resolved_presentation"]["icon_system"]["version"] = "2.5.0"
                manifest = _manifest(
                    render_html_runtime(
                        compile_scene(spec), load_style(ROOT / "styles" / "deep-tech.json"), runtime="gsap"
                    )
                )
                self.assertEqual(expected_count, len(manifest["icons"]))
                for entry in manifest["icons"]:
                    self.assertEqual("illustrated-performance-v6", entry["motion_contract"])
                    self.assertEqual("approved", entry["motion_status"])

    def test_existing_deep_tech_case_uses_v2_for_every_supported_instance(self):
        spec = json.loads(
            (ROOT / "examples" / "illustrated-deep-tech-software-delivery.diagram.json").read_text(encoding="utf-8")
        )
        spec["resolved_presentation"]["icon_system"]["version"] = "2.5.0"
        manifest = _manifest(
            render_html_runtime(
                compile_scene(spec), load_style(ROOT / "styles" / "deep-tech.json"), runtime="gsap"
            )
        )
        self.assertEqual(8, len(manifest["icons"]))
        self.assertEqual(
            {"agent": 3, "operator": 1, "tool": 2, "output": 2},
            {
                icon: sum(entry["icon"] == icon for entry in manifest["icons"])
                for icon in ("agent", "operator", "tool", "output")
            },
        )
        self.assertTrue(all(entry["motion_contract"] == "illustrated-performance-v6" for entry in manifest["icons"]))

    def test_archived_expansion_review_contract_preserves_the_approval_evidence(self):
        contract = json.loads(
            (ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v2.review.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("visual-review", contract["status"])
        self.assertFalse(contract["public_showcase_enabled"])
        self.assertEqual({"database", "api", "search", "memory"}, {item["icon"] for item in contract["performances"]})

    def test_v3_review_contract_is_explicit_only_for_batch_2(self):
        contract = json.loads(
            (ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v3.review.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("2.2.0", contract["icon_system_version"])
        self.assertEqual("visual-review", contract["status"])
        self.assertFalse(contract["public_showcase_enabled"])
        self.assertEqual("explicit-review-only", contract["selection_policy"])
        self.assertEqual(set(ILLUSTRATED_V3_ADDITIONAL_ICON_PERFORMANCES), {item["icon"] for item in contract["performances"]})
        for item in contract["performances"]:
            self.assertEqual(ILLUSTRATED_V3_ADDITIONAL_ICON_PERFORMANCES[item["icon"]], item["id"])
            self.assertEqual(ILLUSTRATED_V3_ADDITIONAL_REST_AT[item["icon"]], item["rest_at"])
            self.assertLessEqual(set(item["primary_parts"]), set(illustrated_definition(item["icon"]).parts))

    def test_batch_2_motion_is_public_with_or_without_explicit_selection(self):
        spec = json.loads(
            (ROOT / "examples" / "illustrated-expansion-batch-2-motion-review.diagram.json").read_text(
                encoding="utf-8"
            )
        )
        spec["resolved_presentation"]["icon_system"]["version"] = "2.5.0"
        explicit_html = render_html_runtime(
            compile_scene(spec), load_style(ROOT / "styles" / "deep-tech.json"), runtime="gsap"
        )
        explicit_manifest = _manifest(explicit_html)
        self.assertEqual(4, len(explicit_manifest["icons"]))
        for entry in explicit_manifest["icons"]:
            self.assertEqual("illustrated-performance-v6", entry["motion_contract"])
            self.assertEqual("approved", entry["motion_status"])
            self.assertEqual("automatic-for-supported-showcase-icons", entry["selection_policy"])
            self.assertEqual(ILLUSTRATED_V3_ADDITIONAL_ICON_PERFORMANCES[entry["icon"]], entry["performance"])

        for node in spec["nodes"]:
            node["effect"] = {"preset": "icon-performance"}
        automatic_manifest = _manifest(
            render_html_runtime(
                compile_scene(spec), load_style(ROOT / "styles" / "deep-tech.json"), runtime="gsap"
            )
        )
        self.assertEqual(4, len(automatic_manifest["icons"]))
        self.assertEqual(
            set(ILLUSTRATED_V3_ADDITIONAL_ICON_PERFORMANCES),
            {entry["icon"] for entry in automatic_manifest["icons"]},
        )

    def test_runtime_dispatches_every_public_v2_performance(self):
        source = _runtime_source()
        for icon, performance in ILLUSTRATED_ICON_PERFORMANCES.items():
            function_name = FUNCTIONS[icon]
            self.assertIn(f"function {function_name}", source)
            self.assertTrue(
                f'"{performance}": {function_name}' in source
                or f'performances["{performance}"] = {function_name}' in source
            )
            self.assertTrue(
                f'"{performance}",' in source
                or f'characterPerformanceIds.add("{performance}")' in source
            )

    def test_cloud_arrows_reveal_in_their_semantic_directions(self):
        contract = json.loads(
            (ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v3.json").read_text(
                encoding="utf-8"
            )
        )
        cloud = next(item for item in contract["performances"] if item["icon"] == "cloud")
        self.assertEqual(
            {
                "upload-arrow": "bottom-to-top",
                "download-arrow": "top-to-bottom",
                "mode": "directional-clip-fade",
            },
            cloud["directional_reveal"],
        )

        definition = illustrated_definition("cloud")
        paths = {primitive.part: primitive.attrs["d"] for primitive in definition.primitives if primitive.kind == "path"}
        self.assertTrue(paths["upload-arrow"].startswith("M44 80V49"))
        self.assertTrue(paths["download-arrow"].startswith("M76 47v31"))

        source = (ROOT / "runtime" / "anidiagram-runtime.js").read_text(encoding="utf-8")
        cloud_source = source[source.index("function playIllustratedCloudTransfer") : source.index("function playIllustratedShieldLock")]
        self.assertIn('clipPath: "inset(100% 0% 0% 0%)"', cloud_source)
        self.assertIn('clipPath: "inset(0% 0% 100% 0%)"', cloud_source)
        self.assertEqual(2, cloud_source.count('clipPath: "inset(0% 0% 0% 0%)"'))


if __name__ == "__main__":
    unittest.main()
