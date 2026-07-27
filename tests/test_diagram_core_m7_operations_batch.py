import unittest

from tests.diagram_core_batch_assertions import (
    assert_baseline_stable,
    assert_catalog_and_manifests,
    assert_motion_contract,
    assert_review_inventory,
    assert_svg_contract,
)


EXPECTED = {
    "ci-cd": {
        "prototype": "three-stage-delivery-pipeline",
        "parts": ("body", "shell", "build", "test", "deploy", "progress", "indicator"),
        "actions": ("receive", "build", "test", "deploy"),
    },
    "task": {
        "prototype": "work-task-card",
        "parts": ("body", "card", "progress", "check", "handle", "indicator"),
        "actions": ("receive", "start", "complete", "send"),
    },
    "scheduler": {
        "prototype": "timed-task-scheduler",
        "parts": ("body", "clock", "hand", "task-card", "trigger", "indicator"),
        "actions": ("receive", "schedule", "trigger", "send"),
    },
    "monitoring": {
        "prototype": "live-metric-monitor",
        "parts": ("body", "shell", "screen", "scanner", "metric-line", "indicator"),
        "actions": ("receive", "observe", "scan", "send"),
    },
    "logs": {
        "prototype": "streaming-log-terminal",
        "parts": ("body", "shell", "lines", "cursor", "highlight", "scroll", "indicator"),
        "actions": ("receive", "record", "inspect", "send"),
    },
    "alert": {
        "prototype": "signal-alert-beacon",
        "parts": ("body", "shell", "light", "wave", "core", "indicator"),
        "actions": ("receive", "detect", "notify", "send"),
    },
    "debug": {
        "prototype": "diagnostic-debug-lens",
        "parts": ("body", "scanner", "code-card", "bug-dot", "fix-check", "indicator"),
        "actions": ("receive", "scan", "fix", "send"),
    },
}


class DiagramCoreM7OperationsBatchTest(unittest.TestCase):
    def test_catalog_and_manifests_promote_exactly_the_frozen_batch(self):
        assert_catalog_and_manifests(self, EXPECTED)

    def test_svgs_are_compact_non_text_and_do_not_encode_runtime_states(self):
        assert_svg_contract(self, EXPECTED)

    def test_prd_identity_parts_preserve_operations_roles(self):
        parts = {icon_id: set(contract["parts"]) for icon_id, contract in EXPECTED.items()}
        self.assertTrue({"build", "test", "deploy", "progress"}.issubset(parts["ci-cd"]))
        self.assertTrue({"card", "progress", "check", "handle"}.issubset(parts["task"]))
        self.assertTrue({"clock", "hand", "task-card", "trigger"}.issubset(parts["scheduler"]))
        self.assertTrue({"screen", "scanner", "metric-line"}.issubset(parts["monitoring"]))
        self.assertTrue({"lines", "cursor", "highlight", "scroll"}.issubset(parts["logs"]))
        self.assertTrue({"light", "wave", "core"}.issubset(parts["alert"]))
        self.assertTrue({"scanner", "code-card", "bug-dot", "fix-check"}.issubset(parts["debug"]))

    def test_motion_catalog_declares_bounded_authored_rest_recipes(self):
        assert_motion_contract(self, EXPECTED)

    def test_deployment_and_search_baselines_remain_stable(self):
        assert_baseline_stable(
            self, "deployment",
            "e95c1a197e23fbaf5d3a34eba706ebcb8029a0e24e7a56c1f32eb51d7a0478e0",
            "e06c06e65cce4fa5cf850e51bf2913d80acdee12129e7a3a5ed30f80a114db4e",
            "a8be726f2a984af1ea525d7406b103ccd6d6893a05570a87207973e0fe02a417",
        )
        assert_baseline_stable(
            self, "search",
            "5bfd9339cb573ca5fdb05f2435850fdebdc25fdef2e2c25b0d6a4a3eaee18562",
            "fd2058f13af3a871536c80749d16de0dde930f95b4730a78eb324ba0c9c58852",
            "4d8dfb7f6adfa45403891ebe4d7a6af89a5a987a977c8a7f1b696f0928771683",
        )

    def test_review_validator_reports_the_complete_56_asset_catalog(self):
        assert_review_inventory(self, EXPECTED, 56)


if __name__ == "__main__":
    unittest.main()
