import hashlib
import json
import unittest
from pathlib import Path

from anidiagram.illustrated_registry import illustrated_icon_ids
from anidiagram.motion_manifest import ILLUSTRATED_V2_ICON_PERFORMANCES


ROOT = Path(__file__).resolve().parents[1]


class IllustratedRelease21Test(unittest.TestCase):
    def test_release_records_eight_approved_static_and_motion_icons(self):
        release = json.loads(
            (ROOT / "assets" / "illustrated" / "releases" / "2.1.0.json").read_text(encoding="utf-8")
        )
        catalog = json.loads(
            (ROOT / "assets" / "illustrated" / "snapshots" / "catalog-2.1.0.json").read_text(encoding="utf-8")
        )
        quality = json.loads(
            (ROOT / "assets" / "illustrated" / "previews" / "illustrated-2.1.0.quality.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual("2.1.0", release["version"])
        self.assertEqual("frozen-approved-release", release["status"])
        self.assertEqual("confirmed", release["human_static_acceptance"])
        self.assertEqual("approved", release["motion_status"])
        self.assertEqual("illustrated-performance-v2", release["public_motion_contract"])
        self.assertEqual("confirmed", release["motion_human_acceptance"])
        self.assertEqual(8, release["icon_count"])
        self.assertEqual(8, release["public_motion_icon_count"])
        self.assertEqual(set(ILLUSTRATED_V2_ICON_PERFORMANCES), {item["id"] for item in catalog["icons"]})
        self.assertEqual({"approved"}, {item["motion_status"] for item in catalog["icons"]})
        self.assertEqual(8, quality["icon_count"])
        self.assertEqual([], quality["duplicate_ids"])
        self.assertEqual(0, quality["errors"])
        self.assertEqual("approved", quality["motion_status"])

    def test_release_hashes_match_the_current_release_authority(self):
        release = json.loads(
            (ROOT / "assets" / "illustrated" / "releases" / "2.1.0.json").read_text(encoding="utf-8")
        )
        files = {
            "catalog_sha256": ROOT / "assets" / "illustrated" / "snapshots" / "catalog-2.1.0.json",
            "registry_sha256": ROOT / "assets" / "illustrated" / "snapshots" / "registry-2.1.0.py",
            "expansion_slice_sha256": ROOT / "src" / "anidiagram" / "illustrated_expansion_batch_1.py",
            "tokens_sha256": ROOT / "assets" / "illustrated" / "tokens-2.1.0.json",
            "renderer_sha256": ROOT / "src" / "anidiagram" / "renderer_illustrated_character_v2.py",
            "visual_snapshot_sha256": ROOT / "assets" / "illustrated" / "previews" / "illustrated-2.1.0.svg",
            "quality_sha256": ROOT / "assets" / "illustrated" / "previews" / "illustrated-2.1.0.quality.json",
            "public_motion_contract_sha256": ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v2.json",
            "archived_motion_review_contract_sha256": ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v2.review.json",
            "showcase_spec_sha256": ROOT / "examples" / "illustrated-2.1-showcase.diagram.json",
            "acceptance_record_sha256": ROOT / "assets" / "illustrated" / "reviews" / "2.1.0-acceptance.json",
        }
        for key, path in files.items():
            self.assertEqual(release["hashes"][key], hashlib.sha256(path.read_bytes()).hexdigest(), key)
        self.assertEqual(
            "b7a95b9dc14fb6328fdca5358cfd3a7bfd154d25a648d9c74b97b7f8dd699799",
            release["hashes"]["motion_manifest_sha256"],
        )
        self.assertEqual(
            "946fa4aae06ac8403c934478e10c29cddf3a83a3f17b08738e85e42ef4f7b099",
            release["hashes"]["runtime_sha256"],
        )

    def test_acceptance_record_keeps_review_evidence_without_release_dependency_on_outputs(self):
        acceptance = json.loads(
            (ROOT / "assets" / "illustrated" / "reviews" / "2.1.0-acceptance.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual("confirmed", acceptance["status"])
        self.assertEqual("confirmed", acceptance["static_acceptance"]["status"])
        self.assertEqual("confirmed", acceptance["motion_acceptance"]["status"])
        self.assertEqual(8, acceptance["public_showcase"]["icon_count"])
        self.assertTrue(acceptance["public_showcase"]["automatic_motion_selection"])
        self.assertEqual("8/8", acceptance["public_showcase"]["validation"]["authored_rest"])
        self.assertEqual("8/8", acceptance["public_showcase"]["validation"]["reduced_motion"])


if __name__ == "__main__":
    unittest.main()
