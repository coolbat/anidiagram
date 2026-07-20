import hashlib
import json
import unittest
from pathlib import Path

from anidiagram.illustrated_registry import illustrated_icon_ids
from anidiagram.motion_manifest import ILLUSTRATED_V3_ICON_PERFORMANCES


ROOT = Path(__file__).resolve().parents[1]


class IllustratedRelease22Test(unittest.TestCase):
    def test_release_approves_twelve_static_and_public_motion_icons(self):
        release = json.loads(
            (ROOT / "assets" / "illustrated" / "releases" / "2.2.0.json").read_text(
                encoding="utf-8"
            )
        )
        catalog = json.loads(
            (ROOT / "assets" / "illustrated" / "snapshots" / "catalog-2.2.0.json").read_text(
                encoding="utf-8"
            )
        )
        quality = json.loads(
            (ROOT / "assets" / "illustrated" / "previews" / "illustrated-2.2.0.quality.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual("2.2.0", release["version"])
        self.assertEqual("frozen-approved-release", release["status"])
        self.assertEqual("twelve-icon-static-and-motion-release", release["scope"])
        self.assertEqual("confirmed", release["human_static_acceptance"])
        self.assertEqual("approved", release["motion_status"])
        self.assertEqual("confirmed", release["motion_human_acceptance"])
        self.assertEqual("illustrated-performance-v3", release["public_motion_contract"])
        self.assertEqual(12, release["icon_count"])
        self.assertEqual(12, release["public_motion_icon_count"])
        frozen_icons = tuple(item["id"] for item in catalog["icons"])
        self.assertEqual(12, len(frozen_icons))
        self.assertEqual(set(ILLUSTRATED_V3_ICON_PERFORMANCES), set(frozen_icons))
        self.assertEqual({"approved"}, {item["motion_status"] for item in catalog["icons"]})
        self.assertEqual(12, quality["icon_count"])
        self.assertEqual([], quality["duplicate_ids"])
        self.assertEqual(0, quality["errors"])
        self.assertEqual("approved", quality["motion_status"])

    def test_release_hashes_match_frozen_release_authority(self):
        release = json.loads(
            (ROOT / "assets" / "illustrated" / "releases" / "2.2.0.json").read_text(
                encoding="utf-8"
            )
        )
        files = {
            "catalog_sha256": ROOT / "assets" / "illustrated" / "snapshots" / "catalog-2.2.0.json",
            "registry_sha256": ROOT / "assets" / "illustrated" / "snapshots" / "registry-2.2.0.py",
            "expansion_slice_sha256": ROOT / "src" / "anidiagram" / "illustrated_expansion_batch_2.py",
            "tokens_sha256": ROOT / "assets" / "illustrated" / "tokens-2.2.0.json",
            "renderer_sha256": ROOT / "src" / "anidiagram" / "renderer_illustrated_character_v2.py",
            "visual_snapshot_sha256": ROOT / "assets" / "illustrated" / "previews" / "illustrated-2.2.0.svg",
            "quality_sha256": ROOT / "assets" / "illustrated" / "previews" / "illustrated-2.2.0.quality.json",
            "public_motion_contract_sha256": ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v3.json",
            "archived_public_motion_contract_sha256": ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v2.json",
            "archived_motion_review_contract_sha256": ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v3.review.json",
            "stage_motion_catalog_sha256": ROOT / "runtime" / "motion-catalog.json",
            "stage_motion_acceptance_sha256": ROOT / "assets" / "illustrated" / "reviews" / "motion-coordination-v1.2-acceptance.json",
            "showcase_spec_sha256": ROOT / "examples" / "illustrated-2.2-showcase.diagram.json",
            "acceptance_record_sha256": ROOT / "assets" / "illustrated" / "reviews" / "2.2.0-acceptance.json",
            "previous_stage_sha256": ROOT / "assets" / "illustrated" / "releases" / "2.2.0.static-motion-review.json",
            "previous_release_sha256": ROOT / "assets" / "illustrated" / "releases" / "2.1.0.json",
            "template_mapping_sha256": ROOT / "assets" / "illustrated" / "snapshots" / "template-mappings-2.2.0.json",
        }
        for key, path in files.items():
            self.assertEqual(release["hashes"][key], hashlib.sha256(path.read_bytes()).hexdigest(), key)
        self.assertEqual(
            "567275ee4b36ed07e678bd21b83df4987310d9bae12e0f43913a6a9e1af21518",
            release["hashes"]["motion_manifest_sha256"],
        )
        self.assertEqual(
            "6137e06ae57079f1bdf641dd3f9c29b5adf6fb3291716ccb79dffb3d5b89370c",
            release["hashes"]["runtime_sha256"],
        )

    def test_acceptance_records_review_and_automatic_public_showcase(self):
        acceptance = json.loads(
            (ROOT / "assets" / "illustrated" / "reviews" / "2.2.0-acceptance.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual("confirmed", acceptance["status"])
        self.assertEqual("confirmed", acceptance["static_acceptance"]["status"])
        self.assertEqual("confirmed", acceptance["motion_acceptance"]["status"])
        self.assertEqual("illustrated-performance-v3", acceptance["motion_acceptance"]["approved_contract"])
        self.assertEqual("bottom-to-top", acceptance["motion_acceptance"]["cloud_directional_reveal"]["upload-arrow"])
        self.assertEqual("top-to-bottom", acceptance["motion_acceptance"]["cloud_directional_reveal"]["download-arrow"])
        self.assertEqual(12, acceptance["public_showcase"]["icon_count"])
        self.assertTrue(acceptance["public_showcase"]["automatic_motion_selection"])
        self.assertEqual(0, acceptance["public_showcase"]["explicit_icon_motion_count"])
        self.assertEqual("12/12", acceptance["public_showcase"]["validation"]["manifest_entries"])
        self.assertEqual("12/12", acceptance["public_showcase"]["validation"]["authored_rest"])
        self.assertEqual("12/12", acceptance["public_showcase"]["validation"]["reduced_motion"])

    def test_stage_motion_v12_records_continuous_unoutlined_short_edge_flow(self):
        release = json.loads(
            (ROOT / "assets" / "illustrated" / "releases" / "2.2.0.json").read_text(
                encoding="utf-8"
            )
        )
        acceptance = json.loads(
            (ROOT / "assets" / "illustrated" / "reviews" / "motion-coordination-v1.2-acceptance.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual("motion-coordination-v1.2", release["stage_motion_contract"])
        self.assertEqual("approved", release["stage_motion_status"])
        self.assertEqual("confirmed", release["stage_motion_human_acceptance"])
        self.assertEqual("confirmed", acceptance["status"])
        self.assertEqual("confirmed", acceptance["human_visual_acceptance"])
        self.assertTrue(acceptance["behavior"]["expressive"]["continuous_track"])
        self.assertEqual(0, acceptance["behavior"]["expressive"]["packet_repeat_delay_seconds"])
        self.assertEqual(
            "solid-role-colored-dot-no-stroke",
            acceptance["behavior"]["expressive"]["short_edge_packet"],
        )
        self.assertEqual("12/12", acceptance["validation"]["expressive_continuous_tracks"])
        self.assertEqual("7/7", acceptance["validation"]["short_edge_solid_dots"])
        self.assertEqual(0, acceptance["validation"]["short_edge_stroke_attributes"])

    def test_historical_release_and_contract_files_remain_immutable(self):
        expected = {
            ROOT / "assets" / "illustrated" / "releases" / "2.0.0.json": "98bb5a5b9b80b8dc5cc8f809963caa1daa0088011e3dd75e5b7b93f996279496",
            ROOT / "assets" / "illustrated" / "releases" / "2.1.0.json": "0a2ff8388d65e1e50f68f8bbbb4b1f3a020645432de1a78e5fa2b844908734df",
            ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v1.json": "88d0c5ca97cb659b1e628492815b1fb2d2610b4619ebd203c3378013adb9be81",
            ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v2.json": "3f28539adc121a621c0be1bff382119a8db0e184c15515f6a74111e18772b3d5",
        }
        for path, digest in expected.items():
            self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest(), path.name)


if __name__ == "__main__":
    unittest.main()
