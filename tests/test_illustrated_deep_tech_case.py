import json
import unittest
from pathlib import Path

from anidiagram.quality import quality_report
from quality_expectations import assert_quality_baseline
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style
from scripts.build_illustrated_deep_tech_case import build_case


ROOT = Path(__file__).resolve().parents[1]


class IllustratedDeepTechCaseTest(unittest.TestCase):
    def test_case_uses_only_frozen_icons_and_passes_quality(self):
        plan = json.loads(
            (ROOT / "examples" / "illustrated-deep-tech-software-delivery.plan.json").read_text(encoding="utf-8")
        )
        spec = build_case(plan)
        scene = compile_scene(spec)
        style = load_style(ROOT / "styles" / "deep-tech.json")
        report = quality_report(scene, style)

        self.assertEqual("illustrated", spec["icon_system"])
        self.assertEqual("2.5.0", spec["resolved_presentation"]["icon_system"]["version"])
        self.assertEqual("deep-tech", spec["resolved_presentation"]["style"]["value"])
        self.assertEqual("showcase-v1", spec["resolved_presentation"]["motion"]["value"])
        self.assertEqual({"agent", "operator", "tool", "output"}, {node["icon"] for node in spec["nodes"]})
        self.assertEqual(8, len(spec["nodes"]))
        self.assertEqual(7, len(spec["edges"]))
        self.assertEqual(3, len(spec["groups"]))
        self.assertTrue(report["ok"])
        assert_quality_baseline(self, report)

    def test_case_node_boxes_do_not_overlap(self):
        plan = json.loads(
            (ROOT / "examples" / "illustrated-deep-tech-software-delivery.plan.json").read_text(encoding="utf-8")
        )
        nodes = build_case(plan)["nodes"]
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
