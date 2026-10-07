import hashlib
import json
import unittest
from pathlib import Path

from anidiagram.illustrated_registry import illustrated_definition, illustrated_icon_ids
from anidiagram.motion_manifest import ILLUSTRATED_ICON_PERFORMANCES, ILLUSTRATED_REST_AT
from anidiagram.renderer_html_runtime import _runtime_source, render_html_runtime
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]
NEW_ICONS = ("vector-database", "knowledge-base", "gateway", "container")
HISTORICAL_ICONS = (
    "agent", "operator", "tool", "output", "database", "api", "search", "memory",
    "file", "folder", "cloud", "shield", "user", "server", "ai-model", "message-queue",
    "vector-database", "knowledge-base", "gateway", "container",
)
RUNTIME_FUNCTIONS = {
    "vector-database": "playIllustratedVectorDatabase",
    "knowledge-base": "playIllustratedKnowledgeBase",
    "gateway": "playIllustratedGateway",
    "container": "playIllustratedContainer",
}


def _manifest(html: str) -> dict:
    marker = '<script type="application/json" id="anidiagram-motion-manifest">'
    start = html.index(marker) + len(marker)
    return json.loads(html[start : html.index("</script>", start)])


def _archived_parts(icon: str) -> set[str]:
    catalog = json.loads(
        (ROOT / "assets" / "illustrated" / "snapshots" / "catalog-2.4.0.json").read_text(encoding="utf-8")
    )
    return set(next(item for item in catalog["icons"] if item["id"] == icon)["parts"])


class IllustratedRelease24Test(unittest.TestCase):
    def test_release_records_twenty_approved_static_and_motion_icons(self):
        release = json.loads(
            (ROOT / "assets" / "illustrated" / "releases" / "2.4.0.json").read_text(encoding="utf-8")
        )
        catalog = json.loads(
            (ROOT / "assets" / "illustrated" / "snapshots" / "catalog-2.4.0.json").read_text(
                encoding="utf-8"
            )
        )
        quality = json.loads(
            (ROOT / "assets" / "illustrated" / "previews" / "illustrated-2.4.0.quality.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual("2.4.0", release["version"])
        self.assertEqual("frozen-approved-release", release["status"])
        self.assertEqual(20, release["icon_count"])
        self.assertEqual("illustrated-performance-v5", release["public_motion_contract"])
        self.assertEqual(20, release["public_motion_icon_count"])
        self.assertEqual("confirmed", release["real_case_human_acceptance"])
        self.assertEqual("confirmed", release["public_registration_acceptance"])
        self.assertEqual("2.3.0", release["previous_release"])

        self.assertEqual("2.4.0", catalog["version"])
        self.assertEqual(9, catalog["catalog_revision"])
        self.assertEqual(set(HISTORICAL_ICONS), {item["id"] for item in catalog["icons"]})
        self.assertEqual(20, quality["icon_count"])
        self.assertEqual([], quality["duplicate_ids"])
        self.assertEqual(0, quality["errors"])

    def test_release_hashes_match_frozen_release_authority(self):
        release = json.loads(
            (ROOT / "assets" / "illustrated" / "releases" / "2.4.0.json").read_text(encoding="utf-8")
        )
        paths = {
            "catalog_sha256": ROOT / "assets" / "illustrated" / "snapshots" / "catalog-2.4.0.json",
            "registry_sha256": ROOT / "assets" / "illustrated" / "snapshots" / "registry-2.4.0.py",
            "expansion_slice_sha256": ROOT / "src" / "anidiagram" / "illustrated_expansion_batch_4.py",
            "tokens_sha256": ROOT / "assets" / "illustrated" / "tokens-2.4.0.json",
            "renderer_sha256": ROOT / "src" / "anidiagram" / "renderer_illustrated_character_v2.py",
            "visual_snapshot_sha256": ROOT / "assets" / "illustrated" / "previews" / "illustrated-2.4.0.svg",
            "quality_sha256": ROOT / "assets" / "illustrated" / "previews" / "illustrated-2.4.0.quality.json",
            "public_motion_contract_sha256": ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v5.json",
            "archived_motion_review_contract_sha256": ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v5.review.json",
            "motion_manifest_sha256": ROOT / "src" / "anidiagram" / "motion_manifest.py",
            "motion_manifest_v2_sha256": ROOT / "assets" / "edge-motion" / "snapshots" / "motion_manifest_v1.0.0.py",
            "runtime_sha256": ROOT / "assets" / "illustrated" / "snapshots" / "anidiagram-runtime-2.4.0.js",
            "edge_motion_runtime_sha256": ROOT / "assets" / "edge-motion" / "snapshots" / "edge-motion-v1.0.0-runtime.js",
            "template_mapping_sha256": ROOT / "assets" / "illustrated" / "snapshots" / "template-mappings-2.4.0.json",
            "acceptance_record_sha256": ROOT / "assets" / "illustrated" / "reviews" / "2.4.0-acceptance.json",
            "static_acceptance_record_sha256": ROOT / "assets" / "illustrated" / "reviews" / "2.4.0-static-acceptance.json",
            "motion_acceptance_record_sha256": ROOT / "assets" / "illustrated" / "reviews" / "2.4.0-motion-acceptance.json",
            "real_case_acceptance_record_sha256": ROOT / "assets" / "illustrated" / "reviews" / "2.4.0-real-case-review.json",
            "public_showcase_spec_sha256": ROOT / "examples" / "illustrated-2.4-showcase.diagram.json",
            "edge_motion_release_sha256": ROOT / "assets" / "edge-motion" / "releases" / "v1.0.0.json",
            "previous_release_sha256": ROOT / "assets" / "illustrated" / "releases" / "2.3.0.json",
        }
        for key, path in paths.items():
            with self.subTest(key=key):
                if key == "motion_manifest_sha256":
                    self.assertEqual(64, len(release["hashes"][key]))
                    continue
                self.assertEqual(release["hashes"][key], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_final_acceptance_records_real_case_and_public_registration(self):
        acceptance = json.loads(
            (ROOT / "assets" / "illustrated" / "reviews" / "2.4.0-acceptance.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("confirmed", acceptance["status"])
        self.assertEqual(list(NEW_ICONS), acceptance["motion_acceptance"]["approved_icons"])
        self.assertEqual("confirmed", acceptance["real_case_acceptance"]["status"])
        self.assertEqual("confirmed", acceptance["public_registration"]["status"])
        self.assertEqual(20, acceptance["public_showcase"]["manifest_verified"])
        self.assertEqual(20, acceptance["public_showcase"]["rest_verified"])
        self.assertEqual(20, acceptance["public_showcase"]["reduced_motion_verified"])
        self.assertEqual(108, acceptance["public_showcase"]["browser_capture"]["distinct_frames"])

    def test_v5_public_contract_covers_all_twenty_icons(self):
        contract = json.loads(
            (ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v5.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("2.4.0", contract["icon_system_version"])
        self.assertEqual("illustrated-performance-v4", contract["supersedes"])
        self.assertEqual("illustrated-performance-v5-review", contract["review_source"])
        self.assertEqual("approved", contract["status"])
        self.assertTrue(contract["public_showcase_enabled"])
        self.assertEqual(set(HISTORICAL_ICONS), {item["icon"] for item in contract["performances"]})
        for item in contract["performances"]:
            self.assertEqual(ILLUSTRATED_ICON_PERFORMANCES[item["icon"]], item["id"])
            self.assertEqual(ILLUSTRATED_REST_AT[item["icon"]], item["rest_at"])
            self.assertLessEqual(set(item["primary_parts"]), _archived_parts(item["icon"]))

    def test_archived_showcase_renders_twenty_timelines_on_current_runtime(self):
        spec = json.loads(
            (ROOT / "examples" / "illustrated-2.4-showcase.diagram.json").read_text(encoding="utf-8")
        )
        spec["resolved_presentation"]["icon_system"]["version"] = "2.5.0"
        html = render_html_runtime(
            compile_scene(spec), load_style(ROOT / "styles" / "deep-tech.json"), runtime="gsap"
        )
        manifest = _manifest(html)
        self.assertEqual(20, html.count('class="semantic-icon semantic-icon-illustrated"'))
        self.assertEqual(20, len(manifest["icons"]))
        self.assertEqual(set(HISTORICAL_ICONS), {entry["icon"] for entry in manifest["icons"]})
        self.assertTrue(all(entry["motion_contract"] == "illustrated-performance-v6" for entry in manifest["icons"]))
        self.assertTrue(all(entry["asset_version"] == "2.5.0" for entry in manifest["icons"]))

    def test_runtime_dispatches_every_new_v5_performance(self):
        source = _runtime_source()
        for icon in NEW_ICONS:
            performance = ILLUSTRATED_ICON_PERFORMANCES[icon]
            function_name = RUNTIME_FUNCTIONS[icon]
            self.assertIn(f"function {function_name}", source)
            self.assertIn(f'"{performance}": {function_name}', source)
            self.assertIn(f'"{performance}",', source)


if __name__ == "__main__":
    unittest.main()
