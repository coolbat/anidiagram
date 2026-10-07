import hashlib
import json
import unittest
from pathlib import Path

from anidiagram.illustrated_registry import illustrated_definition, illustrated_icon_ids
from anidiagram.motion_manifest import (
    ILLUSTRATED_ICON_PERFORMANCES,
    ILLUSTRATED_REST_AT,
    ILLUSTRATED_V4_REVIEW_ICON_PERFORMANCES,
    ILLUSTRATED_V4_REVIEW_REST_AT,
)
from anidiagram.renderer_html_runtime import _runtime_source, render_html_runtime
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]
NEW_ICONS = ("user", "server", "ai-model", "message-queue")
HISTORICAL_ICONS = (
    "agent", "operator", "tool", "output", "database", "api", "search", "memory",
    "file", "folder", "cloud", "shield", *NEW_ICONS,
)
RUNTIME_FUNCTIONS = {
    "user": "playIllustratedUserInteract",
    "server": "playIllustratedServerCompute",
    "ai-model": "playIllustratedAiModelInfer",
    "message-queue": "playIllustratedMessageQueue",
}


def _archived_parts(icon: str) -> set[str]:
    catalog = json.loads(
        (ROOT / "assets" / "illustrated" / "snapshots" / "catalog-2.3.0.json").read_text(encoding="utf-8")
    )
    return set(next(item for item in catalog["icons"] if item["id"] == icon)["parts"])


def _manifest(html: str) -> dict:
    marker = '<script type="application/json" id="anidiagram-motion-manifest">'
    start = html.index(marker) + len(marker)
    return json.loads(html[start : html.index("</script>", start)])


class IllustratedRelease23Test(unittest.TestCase):
    def test_release_records_sixteen_approved_static_and_motion_icons(self):
        release = json.loads(
            (ROOT / "assets" / "illustrated" / "releases" / "2.3.0.json").read_text(encoding="utf-8")
        )
        catalog = json.loads(
            (ROOT / "assets" / "illustrated" / "snapshots" / "catalog-2.3.0.json").read_text(
                encoding="utf-8"
            )
        )
        quality = json.loads(
            (ROOT / "assets" / "illustrated" / "previews" / "illustrated-2.3.0.quality.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual("2.3.0", release["version"])
        self.assertEqual("frozen-approved-release", release["status"])
        self.assertEqual("confirmed", release["human_static_acceptance"])
        self.assertEqual(16, release["icon_count"])
        self.assertEqual("approved", release["motion_status"])
        self.assertEqual("illustrated-performance-v4", release["public_motion_contract"])
        self.assertEqual(16, release["public_motion_icon_count"])
        self.assertEqual("illustrated-performance-v4-review", release["archived_motion_review_contract"])
        self.assertEqual(0, release["review_motion_icon_count"])
        self.assertEqual("confirmed", release["motion_human_acceptance"])
        self.assertEqual("motion-coordination-v1.2", release["stage_motion_contract"])
        self.assertEqual("approved", release["stage_motion_status"])

        self.assertEqual("2.3.0", catalog["version"])
        self.assertEqual(8, catalog["catalog_revision"])
        self.assertEqual("approved", catalog["motion_status"])
        self.assertEqual(16, len(catalog["icons"]))
        self.assertEqual(set(HISTORICAL_ICONS), {item["id"] for item in catalog["icons"]})
        for icon in NEW_ICONS:
            item = next(value for value in catalog["icons"] if value["id"] == icon)
            self.assertEqual("approved", item["status"])
            self.assertEqual("approved", item["motion_status"])

        self.assertEqual(16, quality["icon_count"])
        self.assertEqual("approved", quality["motion_status"])
        self.assertEqual([], quality["duplicate_ids"])
        self.assertEqual(0, quality["errors"])

    def test_release_hashes_match_frozen_release_authority(self):
        release = json.loads(
            (ROOT / "assets" / "illustrated" / "releases" / "2.3.0.json").read_text(encoding="utf-8")
        )
        paths = {
            "catalog_sha256": ROOT / "assets" / "illustrated" / "snapshots" / "catalog-2.3.0.json",
            "registry_sha256": ROOT / "assets" / "illustrated" / "snapshots" / "registry-2.3.0.py",
            "expansion_slice_sha256": ROOT / "src" / "anidiagram" / "illustrated_expansion_batch_3.py",
            "tokens_sha256": ROOT / "assets" / "illustrated" / "tokens-2.3.0.json",
            "renderer_sha256": ROOT / "src" / "anidiagram" / "renderer_illustrated_character_v2.py",
            "visual_snapshot_sha256": ROOT / "assets" / "illustrated" / "previews" / "illustrated-2.3.0.svg",
            "quality_sha256": ROOT / "assets" / "illustrated" / "previews" / "illustrated-2.3.0.quality.json",
            "public_motion_contract_sha256": ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v4.json",
            "archived_motion_review_contract_sha256": ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v4.review.json",
            "template_mapping_sha256": ROOT / "assets" / "illustrated" / "snapshots" / "template-mappings-2.3.0.json",
            "acceptance_record_sha256": ROOT / "assets" / "illustrated" / "reviews" / "2.3.0-acceptance.json",
            "public_showcase_spec_sha256": ROOT / "examples" / "illustrated-2.3-showcase.diagram.json",
            "motion_review_spec_sha256": ROOT / "examples" / "illustrated-expansion-batch-3-motion-review.diagram.json",
            "stage_motion_catalog_sha256": ROOT / "assets" / "illustrated" / "snapshots" / "runtime-motion-catalog-2026-07-08.json",
            "stage_motion_acceptance_sha256": ROOT / "assets" / "illustrated" / "reviews" / "motion-coordination-v1.2-acceptance.json",
            "previous_stage_release_sha256": ROOT / "assets" / "illustrated" / "releases" / "2.3.0.static-motion-review.json",
            "previous_release_sha256": ROOT / "assets" / "illustrated" / "releases" / "2.2.0.json",
        }
        for key, path in paths.items():
            with self.subTest(key=key):
                self.assertEqual(release["hashes"][key], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_static_acceptance_freezes_review_evidence_without_approving_motion(self):
        acceptance = json.loads(
            (ROOT / "assets" / "illustrated" / "reviews" / "2.3.0-static-acceptance.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("static-confirmed-motion-pending", acceptance["status"])
        self.assertEqual(list(NEW_ICONS), acceptance["static_acceptance"]["approved_icons"])
        self.assertEqual([64, 96, 120], acceptance["static_acceptance"]["review_sizes"])
        self.assertEqual(20, acceptance["static_acceptance"]["static_instance_count"])
        self.assertTrue(acceptance["static_acceptance"]["unique_dom_ids"])
        self.assertEqual("pending-human-review", acceptance["motion_acceptance"]["status"])
        self.assertEqual("illustrated-performance-v4-review", acceptance["motion_acceptance"]["review_contract"])
        self.assertEqual(12, acceptance["public_showcase"]["automatic_motion_icon_count"])
        self.assertEqual(4, acceptance["public_showcase"]["review_motion_icon_count"])
        self.assertFalse(acceptance["public_showcase"]["review_motion_is_automatic"])

    def test_final_acceptance_records_human_motion_approval_and_public_validation(self):
        acceptance = json.loads(
            (ROOT / "assets" / "illustrated" / "reviews" / "2.3.0-acceptance.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("confirmed", acceptance["status"])
        self.assertEqual("confirmed", acceptance["static_acceptance"]["status"])
        self.assertEqual("confirmed", acceptance["motion_acceptance"]["status"])
        self.assertEqual("illustrated-performance-v4", acceptance["motion_acceptance"]["approved_contract"])
        self.assertEqual("illustrated-performance-v4-review", acceptance["motion_acceptance"]["review_contract"])
        self.assertEqual(list(NEW_ICONS), acceptance["motion_acceptance"]["approved_icons"])
        self.assertEqual(16, acceptance["public_showcase"]["automatic_motion_icon_count"])
        self.assertEqual(16, acceptance["public_showcase"]["rest_verified"])
        self.assertEqual(16, acceptance["public_showcase"]["reduced_motion_verified"])
        self.assertEqual(0, acceptance["public_showcase"]["review_motion_icon_count"])

    def test_v4_review_contract_matches_four_approved_static_icons(self):
        contract = json.loads(
            (ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v4.review.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("2.3.0", contract["icon_system_version"])
        self.assertEqual("illustrated-performance-v3", contract["extends"])
        self.assertEqual("visual-review", contract["status"])
        self.assertFalse(contract["public_showcase_enabled"])
        self.assertEqual("explicit-review-only", contract["selection_policy"])
        self.assertEqual(set(NEW_ICONS), {item["icon"] for item in contract["performances"]})
        for item in contract["performances"]:
            definition = illustrated_definition(item["icon"])
            self.assertEqual(ILLUSTRATED_V4_REVIEW_ICON_PERFORMANCES[item["icon"]], item["id"])
            self.assertEqual(ILLUSTRATED_V4_REVIEW_REST_AT[item["icon"]], item["rest_at"])
            self.assertLessEqual(set(item["primary_parts"]), set(definition.parts))

    def test_v4_public_contract_approves_all_sixteen_icons(self):
        contract = json.loads(
            (ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v4.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("2.3.0", contract["icon_system_version"])
        self.assertEqual("illustrated-performance-v3", contract["supersedes"])
        self.assertEqual("illustrated-performance-v4-review", contract["review_source"])
        self.assertEqual("approved", contract["status"])
        self.assertEqual("confirmed", contract["human_visual_acceptance"])
        self.assertTrue(contract["public_showcase_enabled"])
        self.assertEqual("automatic-for-supported-showcase-icons", contract["selection_policy"])
        historical_performances = {
            icon: ILLUSTRATED_ICON_PERFORMANCES[icon] for icon in HISTORICAL_ICONS
        }
        self.assertEqual(set(historical_performances), {item["icon"] for item in contract["performances"]})
        for item in contract["performances"]:
            self.assertEqual(historical_performances[item["icon"]], item["id"])
            self.assertEqual(ILLUSTRATED_REST_AT[item["icon"]], item["rest_at"])
            self.assertLessEqual(set(item["primary_parts"]), _archived_parts(item["icon"]))

    def test_public_showcase_spec_remains_a_sixteen_icon_v4_archive(self):
        spec = json.loads(
            (ROOT / "examples" / "illustrated-2.3-showcase.diagram.json").read_text(encoding="utf-8")
        )
        self.assertEqual(16, len(spec["nodes"]))
        self.assertTrue(all("effect" not in node for node in spec["nodes"]))
        self.assertEqual("2.3.0", spec["resolved_presentation"]["icon_system"]["version"])
        self.assertEqual(16, len(spec["nodes"]))
        self.assertEqual(set(HISTORICAL_ICONS), {node["icon"] for node in spec["nodes"]})

    def test_archived_v4_review_spec_retains_its_23_identity(self):
        spec = json.loads(
            (ROOT / "examples" / "illustrated-expansion-batch-3-motion-review.diagram.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("2.3.0", spec["resolved_presentation"]["icon_system"]["version"])
        self.assertEqual(set(NEW_ICONS), {node["icon"] for node in spec["nodes"]})
        self.assertEqual("illustrated-expansion-batch-3-motion-review", spec["preset"])
        self.assertTrue(all("icon_motion" in node["effect"] for node in spec["nodes"]))

    def test_runtime_dispatches_every_v4_review_performance(self):
        source = _runtime_source()
        for icon, performance in ILLUSTRATED_V4_REVIEW_ICON_PERFORMANCES.items():
            function_name = RUNTIME_FUNCTIONS[icon]
            self.assertIn(f"function {function_name}", source)
            self.assertIn(f'"{performance}": {function_name}', source)
            self.assertIn(f'"{performance}",', source)

    def test_historical_releases_snapshots_and_public_contracts_remain_immutable(self):
        expected = {
            ROOT / "assets" / "illustrated" / "releases" / "2.0.0.json": "98bb5a5b9b80b8dc5cc8f809963caa1daa0088011e3dd75e5b7b93f996279496",
            ROOT / "assets" / "illustrated" / "releases" / "2.1.0.json": "0a2ff8388d65e1e50f68f8bbbb4b1f3a020645432de1a78e5fa2b844908734df",
            ROOT / "assets" / "illustrated" / "releases" / "2.2.0.json": "c6d7c6bf1fdaa43129f24b2fa841b5bcc8f33ebb04b09299f1f2ae252937c518",
            ROOT / "assets" / "illustrated" / "snapshots" / "catalog-2.2.0.json": "a0f20547ab3cb34910fdf2de08105e4bf9bdce6a54d24676530824af9b4c09c8",
            ROOT / "assets" / "illustrated" / "snapshots" / "registry-2.2.0.py": "fd32a4a28905112a9a45266e2b6e233223b25ac0cf04da8fdaf956dfdd1f605d",
            ROOT / "assets" / "illustrated" / "snapshots" / "template-mappings-2.2.0.json": "568222e4e73e258a315f8239c8b96fb4b21e9f9df68f14be96fa92c1c1147a89",
            ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v1.json": "88d0c5ca97cb659b1e628492815b1fb2d2610b4619ebd203c3378013adb9be81",
            ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v2.json": "3f28539adc121a621c0be1bff382119a8db0e184c15515f6a74111e18772b3d5",
            ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v3.json": "74e04b8db9d862ce734446e59052c18ee9266d169042a9f13785c9ba6dc16582",
            ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v4.review.json": "4f89961475374a7b04ddf5201396d22069dbd8959903932ddfc2715c205d1104",
            ROOT / "assets" / "illustrated" / "releases" / "2.3.0.static-motion-review.json": "6f898de2a734555dc973b8f9457b498dca59afb95caa7ab24dd4ecde39cbc308",
            ROOT / "assets" / "illustrated" / "snapshots" / "catalog-2.3.0.static-motion-review.json": "9c85bf4bb65e56c1324756f515656263cc21bcd9f5d75882c946e741164ee2e5",
            ROOT / "assets" / "illustrated" / "snapshots" / "registry-2.3.0.static-motion-review.py": "502c5fb1e49b982e1a7449b182f73c33e2e8cc0781b85642fa9509ceb509c968",
            ROOT / "assets" / "illustrated" / "snapshots" / "template-mappings-2.3.0.static-motion-review.json": "1e44693f4de272c8c9287127193c3e171fabfcfd9e862db37f19ab48caa86554",
            ROOT / "assets" / "illustrated" / "reviews" / "2.3.0-static-acceptance.json": "58b958dd28d718a0eda212a06630a373086a80ce5c3f83f85e1e33d82cafbebc",
            ROOT / "examples" / "illustrated-expansion-batch-3-motion-review.diagram.json": "7957ab687a6cd862ee928e24add19ac4d1a2f55d95091d331175d67c64734c20",
        }
        for path, digest in expected.items():
            with self.subTest(path=path.name):
                self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
