import json
import unittest
from pathlib import Path

from anidiagram.illustrated_registry import illustrated_icon_ids
from anidiagram.motion_manifest import (
    ILLUSTRATED_V3_ICON_PERFORMANCES,
    build_motion_manifest,
)
from anidiagram.quality import quality_report
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style
from scripts.build_enterprise_rag_production_case import build_case


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "examples" / "enterprise-rag-production-illustrated.plan.json"


class EnterpriseRagProductionCaseTest(unittest.TestCase):
    def _plan(self):
        return json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    def _spec(self):
        return build_case(self._plan())

    def test_semantic_plan_uses_all_twelve_illustrated_icons_once(self):
        plan = self._plan()
        semantic = plan["semantic"]

        self.assertEqual(12, len(semantic["entities"]))
        self.assertEqual(set(ILLUSTRATED_V3_ICON_PERFORMANCES), {item["kind"] for item in semantic["entities"]})
        self.assertEqual(12, len(semantic["relations"]))
        self.assertEqual(4, len(semantic["flows"]))
        relation_ids = {item["id"] for item in semantic["relations"]}
        self.assertEqual(
            relation_ids,
            {relation_id for flow in semantic["flows"] for relation_id in flow["relation_ids"]},
        )

    def test_case_resolves_frozen_presentation_and_passes_quality(self):
        spec = self._spec()
        scene = compile_scene(spec)
        style = load_style(ROOT / "styles" / "minimal-light.json")
        report = quality_report(scene, style)

        self.assertEqual("illustrated", spec["icon_system"])
        self.assertEqual("2.4.0", spec["resolved_presentation"]["icon_system"]["version"])
        self.assertEqual(
            {"value": "minimal-light", "source": "model"},
            spec["resolved_presentation"]["style"],
        )
        self.assertEqual("showcase-v1", spec["resolved_presentation"]["motion"]["value"])
        self.assertEqual(set(ILLUSTRATED_V3_ICON_PERFORMANCES), {node["icon"] for node in spec["nodes"]})
        self.assertEqual(12, len(spec["edges"]))
        self.assertEqual(2, len(spec["groups"]))
        self.assertTrue(report["ok"])
        self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, report["summary"])

    def test_showcase_motion_is_automatic_and_public_for_all_twelve_icons(self):
        spec = self._spec()
        self.assertFalse(
            any("icon_motion" in node.get("effect", {}) for node in spec["nodes"])
        )
        scene = compile_scene(spec)
        manifest = build_motion_manifest(scene, load_style(ROOT / "styles" / "minimal-light.json"))

        self.assertEqual(12, len(manifest["icons"]))
        self.assertEqual(set(ILLUSTRATED_V3_ICON_PERFORMANCES), {entry["icon"] for entry in manifest["icons"]})
        self.assertEqual(
            {"illustrated-performance-v5"},
            {entry["motion_contract"] for entry in manifest["icons"]},
        )
        self.assertEqual({"approved"}, {entry["motion_status"] for entry in manifest["icons"]})
        self.assertEqual(
            {"automatic-for-supported-showcase-icons"},
            {entry["selection_policy"] for entry in manifest["icons"]},
        )
        self.assertEqual(12, len({entry["node_id"] for entry in manifest["icons"]}))

    def test_node_boxes_do_not_overlap(self):
        nodes = self._spec()["nodes"]
        for index, left in enumerate(nodes):
            lx, ly = left["position"]
            lw, lh = left["size"]
            for right in nodes[index + 1 :]:
                rx, ry = right["position"]
                rw, rh = right["size"]
                overlap = lx < rx + rw and lx + lw > rx and ly < ry + rh and ly + lh > ry
                self.assertFalse(overlap, f"{left['id']} overlaps {right['id']}")


if __name__ == "__main__":
    unittest.main()
