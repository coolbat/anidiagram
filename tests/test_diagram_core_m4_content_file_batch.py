import unittest

from tests.diagram_core_batch_assertions import (
    assert_baseline_stable,
    assert_catalog_and_manifests,
    assert_motion_contract,
    assert_review_inventory,
    assert_svg_contract,
)


EXPECTED = {
    "document-store": {
        "prototype": "document-drawer-store",
        "parts": ("body", "shell", "drawer", "document-card-front", "document-card-back", "indicator"),
        "actions": ("receive", "store", "retrieve", "send"),
    },
    "document": {
        "prototype": "text-document-file",
        "parts": ("body", "page", "fold", "line-top", "line-middle", "line-bottom", "indicator"),
        "actions": ("receive", "open", "read", "send"),
    },
    "pdf": {
        "prototype": "paginated-pdf-file",
        "parts": ("body", "page", "fold", "pages", "spine", "badge", "indicator"),
        "actions": ("receive", "open", "page", "send"),
    },
    "image": {
        "prototype": "image-preview-file",
        "parts": ("body", "page", "fold", "preview", "scan-line", "badge", "indicator"),
        "actions": ("receive", "open", "scan", "send"),
    },
    "audio": {
        "prototype": "audio-waveform-file",
        "parts": ("body", "page", "fold", "waveform", "playhead", "badge", "indicator"),
        "actions": ("receive", "play", "scrub", "send"),
    },
    "video": {
        "prototype": "video-frame-file",
        "parts": ("body", "page", "fold", "play", "frame-a", "frame-b", "indicator"),
        "actions": ("receive", "play", "frame", "send"),
    },
    "code-file": {
        "prototype": "code-script-file",
        "parts": ("body", "page", "fold", "code-lines", "cursor", "badge", "indicator"),
        "actions": ("receive", "open", "edit", "send"),
    },
}


class DiagramCoreM4ContentFileBatchTest(unittest.TestCase):
    def test_catalog_and_manifests_promote_exactly_the_frozen_batch(self):
        assert_catalog_and_manifests(self, EXPECTED)

    def test_svgs_share_the_file_family_without_becoming_interchangeable(self):
        assert_svg_contract(self, EXPECTED)

    def test_prd_identity_parts_are_present_without_text_dependent_badges(self):
        parts = {icon_id: set(contract["parts"]) for icon_id, contract in EXPECTED.items()}
        self.assertTrue({"drawer", "document-card-front", "document-card-back"}.issubset(parts["document-store"]))
        self.assertTrue({"line-top", "line-middle", "line-bottom"}.issubset(parts["document"]))
        self.assertTrue({"pages", "spine", "badge"}.issubset(parts["pdf"]))
        self.assertTrue({"preview", "scan-line"}.issubset(parts["image"]))
        self.assertTrue({"waveform", "playhead"}.issubset(parts["audio"]))
        self.assertTrue({"play", "frame-a", "frame-b"}.issubset(parts["video"]))
        self.assertTrue({"code-lines", "cursor"}.issubset(parts["code-file"]))

    def test_motion_catalog_declares_bounded_authored_rest_recipes(self):
        assert_motion_contract(self, EXPECTED)

    def test_file_benchmark_remains_stable(self):
        assert_baseline_stable(
            self,
            "file",
            "2e3bece9c2ca6b9139a6ef7b3b878676f245f61912f4b43ecb2583b44535fc8c",
            "1c42c094ececbc322227d1194489fc6b8f0953a9823f2e505a57ecec08a64b93",
            "6797dd523c8dcc60f41ced94d681f641651411b6aa7a101c9308ca117dbab9c3",
        )

    def test_review_validator_includes_the_batch_without_inventory_drift(self):
        assert_review_inventory(self, EXPECTED, 35)


if __name__ == "__main__":
    unittest.main()
