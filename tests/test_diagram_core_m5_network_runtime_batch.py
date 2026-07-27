import unittest

from tests.diagram_core_batch_assertions import (
    assert_baseline_stable,
    assert_catalog_and_manifests,
    assert_motion_contract,
    assert_review_inventory,
    assert_svg_contract,
)


EXPECTED = {
    "webhook": {
        "prototype": "event-webhook-trigger",
        "parts": ("body", "shell", "trigger", "event-dot", "pulse", "indicator"),
        "actions": ("receive", "trigger", "notify", "send"),
    },
    "http-request": {
        "prototype": "directional-http-packet",
        "parts": ("body", "packet", "header", "payload", "direction-gap", "indicator"),
        "actions": ("receive", "request", "transfer", "send"),
    },
    "gateway": {
        "prototype": "scanning-entry-gateway",
        "parts": ("body", "gate", "scanner", "core", "input", "output", "indicator"),
        "actions": ("receive", "inspect", "route", "send"),
    },
    "load-balancer": {
        "prototype": "three-way-load-distributor",
        "parts": ("body", "distributor", "input", "outlet-top", "outlet-middle", "outlet-bottom", "indicator"),
        "actions": ("receive", "balance", "distribute", "send"),
    },
    "message-queue": {
        "prototype": "conveyor-message-queue",
        "parts": ("body", "shell", "message-a", "message-b", "message-c", "consumer", "indicator"),
        "actions": ("receive", "queue", "consume", "send"),
    },
    "server-cluster": {
        "prototype": "coordinated-server-cluster",
        "parts": ("body", "node-a", "node-b", "node-c", "sync", "indicator"),
        "actions": ("receive", "coordinate", "process", "send"),
    },
    "container": {
        "prototype": "isolated-runtime-container",
        "parts": ("body", "shell", "door", "app-core", "boundary", "indicator"),
        "actions": ("receive", "isolate", "run", "send"),
    },
}


class DiagramCoreM5NetworkRuntimeBatchTest(unittest.TestCase):
    def test_catalog_and_manifests_promote_exactly_the_frozen_batch(self):
        assert_catalog_and_manifests(self, EXPECTED)

    def test_svgs_are_compact_non_text_and_not_generic_interface_boxes(self):
        assert_svg_contract(self, EXPECTED)

    def test_prd_identity_parts_preserve_network_and_runtime_roles(self):
        parts = {icon_id: set(contract["parts"]) for icon_id, contract in EXPECTED.items()}
        self.assertTrue({"trigger", "event-dot", "pulse"}.issubset(parts["webhook"]))
        self.assertTrue({"packet", "header", "direction-gap"}.issubset(parts["http-request"]))
        self.assertTrue({"gate", "scanner", "core"}.issubset(parts["gateway"]))
        self.assertTrue({"distributor", "outlet-top", "outlet-middle", "outlet-bottom"}.issubset(parts["load-balancer"]))
        self.assertTrue({"message-a", "message-b", "message-c", "consumer"}.issubset(parts["message-queue"]))
        self.assertTrue({"node-a", "node-b", "node-c", "sync"}.issubset(parts["server-cluster"]))
        self.assertTrue({"door", "app-core", "boundary"}.issubset(parts["container"]))

    def test_motion_catalog_declares_bounded_authored_rest_recipes(self):
        assert_motion_contract(self, EXPECTED)

    def test_api_and_server_benchmarks_remain_stable(self):
        assert_baseline_stable(
            self, "api",
            "2cb54e773dbb9c33750c6637d80108e59e16153c2d15b2ed318ba131a45ba21a",
            "b173a1e8d8df1004beb28e339e1ea3b0fd1c14733f3c213914198cc1a69182d4",
            "0578325be32248e2cba489adadb04a32b452440f4f97db0d8a7c695d05ce97fe",
        )
        assert_baseline_stable(
            self, "server",
            "994bbb969a47d2eb90dfb4b6ea3adfaa6b3b4e029345ceb9a2a46eb0d4ce2785",
            "32fc43fd3fa309fc3839ffe30a10124810c7445b9bc35fd7eceb6046b7410706",
            "20a57bd6434944abfe21ddf3a4a2be8d6171a7b419452c8c3344150ae5deff73",
        )

    def test_review_validator_includes_the_batch_without_inventory_drift(self):
        assert_review_inventory(self, EXPECTED, 42)


if __name__ == "__main__":
    unittest.main()
