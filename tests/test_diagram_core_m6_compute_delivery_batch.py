import unittest

from tests.diagram_core_batch_assertions import (
    assert_baseline_stable,
    assert_catalog_and_manifests,
    assert_motion_contract,
    assert_review_inventory,
    assert_svg_contract,
)


EXPECTED = {
    "function": {
        "prototype": "triggered-function-capsule",
        "parts": ("body", "shell", "trigger", "function-core", "result", "indicator"),
        "actions": ("receive", "trigger", "compute", "send"),
    },
    "edge-node": {
        "prototype": "signal-edge-node",
        "parts": ("body", "shell", "signal", "core", "sync", "latency-ring", "indicator"),
        "actions": ("receive", "sync", "process", "send"),
    },
    "source-code": {
        "prototype": "source-editor-panel",
        "parts": ("body", "shell", "cursor", "code-lines", "gutter", "indicator"),
        "actions": ("receive", "open", "edit", "send"),
    },
    "git-repository": {
        "prototype": "versioned-repository-box",
        "parts": ("body", "box", "branch-tree", "commit", "history", "indicator"),
        "actions": ("receive", "commit", "store", "send"),
    },
    "branch": {
        "prototype": "forked-commit-line",
        "parts": ("body", "main-line", "branch-line", "commit-a", "commit-b", "commit-c", "indicator"),
        "actions": ("receive", "fork", "advance", "send"),
    },
    "pull-request": {
        "prototype": "reviewed-merge-flow",
        "parts": ("body", "source-path", "review", "merge", "target", "indicator"),
        "actions": ("receive", "review", "merge", "send"),
    },
    "deployment": {
        "prototype": "package-to-runtime",
        "parts": ("body", "package", "path", "target", "release-core", "indicator"),
        "actions": ("receive", "deploy", "release", "send"),
    },
}


class DiagramCoreM6ComputeDeliveryBatchTest(unittest.TestCase):
    def test_catalog_and_manifests_promote_exactly_the_frozen_batch(self):
        assert_catalog_and_manifests(self, EXPECTED)

    def test_svgs_are_compact_non_text_and_brand_neutral(self):
        assert_svg_contract(self, EXPECTED)

    def test_prd_identity_parts_preserve_compute_and_delivery_roles(self):
        parts = {icon_id: set(contract["parts"]) for icon_id, contract in EXPECTED.items()}
        self.assertTrue({"trigger", "function-core", "result"}.issubset(parts["function"]))
        self.assertTrue({"signal", "core", "sync", "latency-ring"}.issubset(parts["edge-node"]))
        self.assertTrue({"cursor", "code-lines", "gutter"}.issubset(parts["source-code"]))
        self.assertTrue({"box", "branch-tree", "commit", "history"}.issubset(parts["git-repository"]))
        self.assertTrue({"main-line", "branch-line", "commit-a", "commit-b", "commit-c"}.issubset(parts["branch"]))
        self.assertTrue({"source-path", "review", "merge", "target"}.issubset(parts["pull-request"]))
        self.assertTrue({"package", "path", "target", "release-core"}.issubset(parts["deployment"]))

    def test_motion_catalog_declares_bounded_authored_rest_recipes(self):
        assert_motion_contract(self, EXPECTED)

    def test_code_file_and_reasoning_baselines_remain_stable(self):
        assert_baseline_stable(
            self, "code-file",
            "424de592517a5688114f6276e210ec884433e5a83225848d13890b883fc83c9b",
            "8cd1f7b4431eb2d77ef6e64f077a844b364578255908a401b729ffe7b067f25a",
            "92c86b8f9d01ddfedb23ba297834eb96bb8b5d9032a6bf572c2f509c8025fdb2",
        )
        assert_baseline_stable(
            self, "reasoning",
            "e937e133ec6cb24d0b6a5ac995778fcb30532c8f26fba909329a511ddb910328",
            "98603491c18e48f6b3587350619539b1e4ff5326f70bb5bf31d5e45e8647a12b",
            "630aa90a8c2904d017ad55aa1c4dc3d77d74c1ce1b42520dfa956533bb473457",
        )

    def test_review_validator_includes_the_batch_without_inventory_drift(self):
        assert_review_inventory(self, EXPECTED, 49)


if __name__ == "__main__":
    unittest.main()
