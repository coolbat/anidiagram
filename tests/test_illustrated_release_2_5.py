import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from anidiagram.diagram_core.catalog import approved_icon_ids
from anidiagram.icon_system import ILLUSTRATED_ICON_SYSTEM_VERSION
from anidiagram.illustrated_convention_alignment_review import (
    convention_alignment_definition,
    convention_alignment_icon_ids,
)
from anidiagram.illustrated_registry import illustrated_definition, illustrated_icon_ids
from anidiagram.motion_manifest import ILLUSTRATED_ICON_PERFORMANCES, ILLUSTRATED_REST_AT
from anidiagram.renderer_html_runtime import render_html_runtime
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style
from scripts import promote_illustrated_2_5 as release_promotion


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _manifest(html: str) -> dict:
    marker = '<script type="application/json" id="anidiagram-motion-manifest">'
    start = html.index(marker) + len(marker)
    return json.loads(html[start : html.index("</script>", start)])


class IllustratedRelease25Test(unittest.TestCase):
    def test_current_registry_is_exactly_the_fifty_six_diagram_core_icons(self):
        self.assertEqual("2.5.0", ILLUSTRATED_ICON_SYSTEM_VERSION)
        self.assertEqual(56, len(illustrated_icon_ids()))
        self.assertEqual(set(approved_icon_ids()), set(illustrated_icon_ids()))
        for icon_id in convention_alignment_icon_ids():
            with self.subTest(icon=icon_id):
                self.assertIs(illustrated_definition(icon_id), convention_alignment_definition(icon_id))

    def test_catalog_tokens_and_template_mapping_publish_the_25_identity(self):
        catalog = _read("assets/illustrated/catalog.json")
        tokens = _read("assets/illustrated/tokens-2.5.0.json")
        mapping = _read("assets/illustrated/template-mappings.json")
        self.assertEqual("2.5.0", catalog["version"])
        self.assertEqual(10, catalog["catalog_revision"])
        self.assertEqual(56, len(catalog["icons"]))
        self.assertEqual(set(illustrated_icon_ids()), {item["id"] for item in catalog["icons"]})
        self.assertEqual("illustrated-performance-v6", catalog["motion_contract"]["id"])
        self.assertEqual("2.5.0", tokens["version"])
        self.assertEqual("2.5.0", mapping["version"])
        self.assertEqual("illustrated-performance-v6", mapping["public_motion_contract"])
        self.assertEqual(12, len(mapping["mappings"]))

    def test_public_v6_motion_contract_covers_every_public_icon(self):
        contract = _read("assets/illustrated/motion-contracts/illustrated-performance-v6.json")
        self.assertEqual("2.5.0", contract["icon_system_version"])
        self.assertEqual("illustrated-performance-v5", contract["supersedes"])
        self.assertEqual("approved", contract["status"])
        self.assertTrue(contract["public_showcase_enabled"])
        self.assertEqual(set(illustrated_icon_ids()), set(ILLUSTRATED_ICON_PERFORMANCES))
        self.assertEqual(set(illustrated_icon_ids()), {item["icon"] for item in contract["performances"]})
        for item in contract["performances"]:
            with self.subTest(icon=item["icon"]):
                self.assertEqual(ILLUSTRATED_ICON_PERFORMANCES[item["icon"]], item["id"])
                self.assertEqual(ILLUSTRATED_REST_AT[item["icon"]], item["rest_at"])
                self.assertLessEqual(set(item["primary_parts"]), set(illustrated_definition(item["icon"]).parts))

    def test_public_showcase_renders_fifty_six_automatic_timelines(self):
        spec = _read("examples/illustrated-2.5-showcase.diagram.json")
        html = render_html_runtime(
            compile_scene(spec),
            load_style(ROOT / "styles" / "deep-tech.json"),
            runtime="gsap",
        )
        manifest = _manifest(html)
        self.assertEqual(56, html.count('class="semantic-icon semantic-icon-illustrated"'))
        self.assertEqual(56, len(manifest["icons"]))
        self.assertEqual(set(illustrated_icon_ids()), {entry["icon"] for entry in manifest["icons"]})
        self.assertTrue(all(entry["motion_contract"] == "illustrated-performance-v6" for entry in manifest["icons"]))
        self.assertTrue(all(entry["asset_version"] == "2.5.0" for entry in manifest["icons"]))
        self.assertIn("playIllustratedPublicConfigured", html)
        self.assertIn("playIllustratedDeveloper", html)

    def test_release_and_acceptance_records_freeze_the_56_icon_result(self):
        acceptance = _read("assets/illustrated/reviews/2.5.0-acceptance.json")
        release = _read("assets/illustrated/releases/2.5.0.json")
        validation = _read("assets/illustrated/reviews/2.5.0-validation.json")
        self.assertEqual("confirmed", acceptance["status"])
        self.assertEqual(56, acceptance["public_showcase"]["automatic_motion_icon_count"])
        self.assertEqual(56, acceptance["public_showcase"]["rest_verified"])
        self.assertEqual(56, acceptance["public_showcase"]["reduced_motion_verified"])
        self.assertEqual(12, acceptance["convention_alignment"]["approved_icon_count"])
        self.assertEqual("2.5.0", release["version"])
        self.assertEqual("frozen-approved-release", release["status"])
        self.assertEqual(56, release["icon_count"])
        self.assertEqual("illustrated-performance-v6", release["public_motion_contract"])
        self.assertEqual("2.4.0", release["previous_release"])
        self.assertEqual("verified", validation["status"])
        self.assertEqual(249, validation["python_tests"]["passed"])
        self.assertEqual(56, validation["diagram_core_strict"]["approved"])
        self.assertEqual(13, validation["real_case"]["animated_edges"])
        self.assertEqual(10, validation["export_evidence"]["formats"])
        self.assertEqual("pending-source-push", validation["remote_ci"]["status"])

    def test_versioned_release_writer_is_write_once(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(release_promotion, "ROOT", Path(directory)):
                release_promotion._write("assets/example.json", {"version": "2.5.0"})
                release_promotion._write("assets/example.json", {"version": "2.5.0"})
                with self.assertRaisesRegex(RuntimeError, "immutable"):
                    release_promotion._write("assets/example.json", {"version": "2.5.1"})


if __name__ == "__main__":
    unittest.main()
