from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import os

from anidiagram.artifact_bundle import commit_bundle
from anidiagram.delivery import DeliveryError

from anidiagram.compare import compare_plans, deliver_comparison

ROOT = Path(__file__).resolve().parents[1]


class ComparisonTest(unittest.TestCase):
    def setUp(self):
        self.base = json.loads((ROOT / "examples/contracts/production-request-path.plan.json").read_text())

    def test_reordered_entities_are_not_semantic_changes(self):
        head = deepcopy(self.base)
        head["semantic"]["entities"].reverse()
        result = compare_plans(self.base, head)
        self.assertTrue(result["semantic_equal"])
        self.assertEqual([], result["semantic_changes"])
        self.assertEqual(result["canonical"]["base"], result["canonical"]["head"])

    def test_style_only_is_not_system_change(self):
        head = deepcopy(self.base)
        head["presentation"]["style"] = "deep-tech"
        result = compare_plans(self.base, head)
        self.assertTrue(result["semantic_equal"])
        self.assertEqual(1, result["summary"]["presentation"])
        self.assertEqual([], result["geometry_changes"])

    def test_semantics_and_geometry_are_independent(self):
        head = deepcopy(self.base)
        head["semantic"]["entities"][0]["label"] = "Web client"
        head["presentation"]["layout"] = "pipeline"
        result = compare_plans(self.base, head)
        self.assertEqual("client", result["semantic_changes"][0]["id"])
        self.assertGreater(len(result["geometry_changes"]), 0)

    def test_add_remove_topology_and_evidence_classification(self):
        head = deepcopy(self.base)
        head["semantic"]["sources"] = [{"id": "document", "type": "document", "uri": "local"}]
        head["semantic"]["entities"][0]["source_refs"] = ["document"]
        head["semantic"]["relations"][0]["direction"] = "bidirectional"
        result = compare_plans(self.base, head)
        by_id = {entry["id"]: entry for entry in result["semantic_changes"]}
        self.assertEqual(["evidence"], by_id["client"]["categories"])
        self.assertEqual(["topology"], by_id["client-request"]["categories"])
        self.assertEqual("added", by_id["document"]["status"])

    def test_invalid_id_and_incoherent_flow_are_rejected(self):
        for mutate in (lambda p: p["semantic"]["entities"].append(p["semantic"]["entities"][0]),
                       lambda p: p["semantic"]["flows"][0]["relation_ids"].reverse()):
            head = deepcopy(self.base)
            mutate(head)
            with self.assertRaises(ValueError):
                compare_plans(self.base, head)

    def test_pair_delivery_hash_and_input_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head, out = root / "base.json", root / "head.json", root / "delta.html"
            base.write_text(json.dumps(self.base))
            head.write_bytes(base.read_bytes())
            delivered = deliver_comparison(base, head, out)
            receipt = json.loads(Path(delivered["receipt"]).read_text())
            self.assertEqual(hashlib.sha256(out.read_bytes()).hexdigest(), receipt["artifact"]["sha256"])
            self.assertIn('sandbox="allow-scripts"', out.read_text())
            before = base.read_bytes()
            with self.assertRaisesRegex(ValueError, "input file"):
                deliver_comparison(base, head, base)
            self.assertEqual(before, base.read_bytes())
            head.write_text("{}")
            last_good = out.read_bytes()
            with self.assertRaises(ValueError):
                deliver_comparison(base, head, out)
            self.assertEqual(last_good, out.read_bytes())

    def test_pair_commit_rolls_back_both_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "out.html", Path(tmp) / "receipt.json"
            first.write_bytes(b"old html")
            second.write_bytes(b"old receipt")
            replace = os.replace
            def fail_second(source, target):
                if Path(source).name == "receipt.json" and Path(target) == second:
                    raise OSError("test replacement failure")
                return replace(source, target)
            with patch("anidiagram.delivery.os.replace", side_effect=fail_second), self.assertRaises(DeliveryError):
                commit_bundle({first: b"new html", second: b"new receipt"})
            self.assertEqual(b"old html", first.read_bytes())
            self.assertEqual(b"old receipt", second.read_bytes())
