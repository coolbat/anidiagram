import json
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from anidiagram.composition import LAYOUTS
from anidiagram.planner import brief_to_plan, compile_plan
from anidiagram.quality import quality_report
from anidiagram.schema import DiagramScriptValidationError, compile_scene
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]


class CompositionClosureTest(unittest.TestCase):
    def _plan(self):
        return json.loads(
            (ROOT / "examples" / "contracts" / "production-request-path.plan.json").read_text(encoding="utf-8")
        )

    def test_all_registered_layouts_dispatch_to_distinct_geometry(self):
        signatures = {}
        for layout in sorted(LAYOUTS):
            plan = self._plan()
            plan["presentation"]["layout"] = layout
            spec = compile_plan(plan)
            signatures[layout] = (
                tuple((node["id"], tuple(node["position"])) for node in spec["nodes"]),
                (spec["canvas"]["width"], spec["canvas"]["height"]),
            )

        self.assertEqual(14, len(signatures))
        self.assertEqual(14, len(set(signatures.values())))

    def test_flow_order_controls_pipeline_order_and_repeat_controls_motion(self):
        plan = self._plan()
        plan["presentation"]["layout"] = "pipeline"
        plan["semantic"]["entities"] = list(reversed(plan["semantic"]["entities"]))
        plan["semantic"]["flows"][0]["repeat"] = "loop"
        spec = compile_plan(plan)

        x_by_id = {node["id"]: node["position"][0] for node in spec["nodes"]}
        self.assertLess(x_by_id["client"], x_by_id["ingress"])
        self.assertLess(x_by_id["ingress"], x_by_id["workload"])
        edge_by_relation = {edge["semantic_relation_id"]: edge for edge in spec["edges"]}
        self.assertEqual("dynamic-dash", edge_by_relation["client-request"]["effect"]["preset"])
        self.assertEqual(1, edge_by_relation["client-request"]["step"])
        self.assertEqual(2, edge_by_relation["ingress-route"]["step"])

    def test_semantic_fallback_state_and_group_metadata_survive_compilation(self):
        plan = self._plan()
        plan["presentation"]["icon_system"] = "illustrated"
        workload = next(entity for entity in plan["semantic"]["entities"] if entity["id"] == "workload")
        workload["kind"] = "container"
        plan["semantic"]["groups"].append(
            {
                "id": "platform",
                "label": "Platform",
                "kind": "boundary",
                "members": ["client", "telemetry"],
                "importance": "context",
            }
        )
        plan["semantic"]["groups"][0]["parent"] = "platform"

        spec = compile_plan(plan)
        node = next(item for item in spec["nodes"] if item["id"] == "workload")
        group = next(item for item in spec["groups"] if item["id"] == "runtime")

        self.assertEqual("container", node["semantic_kind"])
        self.assertEqual("role-fallback", node["icon_resolution"])
        self.assertEqual(workload["state"], node["state"])
        self.assertEqual("system", group["semantic_kind"])
        self.assertEqual("primary", group["importance"])
        self.assertEqual("platform", group["parent"])

        scene = compile_scene(spec)
        scene_node = next(item for item in scene.nodes if item.node_id == "workload")
        scene_group = next(item for item in scene.groups if item.group_id == "runtime")
        self.assertEqual("container", scene_node.semantic_kind)
        self.assertEqual("role-fallback", scene_node.icon_resolution)
        self.assertEqual(workload["state"], scene_node.state)
        self.assertEqual("platform", scene_group.parent)

        report = quality_report(scene, load_style())
        fallback_issues = [issue for issue in report["issues"] if issue["code"] == "semantic_icon_fallback"]
        self.assertTrue(fallback_issues)
        self.assertTrue(any("container" in issue["message"] for issue in fallback_issues))

    def test_composition_v1_rejects_any_stale_resolved_axis(self):
        spec = compile_plan(self._plan())
        mutations = {
            "icon_system": "illustrated",
            "style": "deep-tech",
            "layout": "pipeline",
            "motion": "teaching",
        }
        for axis, stale_value in mutations.items():
            with self.subTest(axis=axis):
                changed = deepcopy(spec)
                changed["resolved_presentation"][axis]["value"] = stale_value
                with self.assertRaisesRegex(DiagramScriptValidationError, "must match"):
                    compile_scene(changed)

        missing = deepcopy(spec)
        del missing["resolved_presentation"]["style"]
        with self.assertRaisesRegex(DiagramScriptValidationError, "resolved_presentation.style"):
            compile_scene(missing)

    def test_plan_validator_matches_schema_for_required_presentation_and_exclusions(self):
        schema = json.loads((ROOT / "schemas" / "diagram-plan-v0.2.schema.json").read_text(encoding="utf-8"))
        self.assertIn("presentation", schema["required"])
        self.assertEqual("array", schema["$defs"]["intent"]["properties"]["exclusions"]["type"])

        missing_presentation = self._plan()
        del missing_presentation["presentation"]
        with self.assertRaisesRegex(ValueError, "requires a presentation"):
            compile_plan(missing_presentation)

        invalid_exclusions = self._plan()
        invalid_exclusions["semantic"]["intent"]["exclusions"] = "internal details"
        with self.assertRaisesRegex(ValueError, "exclusions must be an array"):
            compile_plan(invalid_exclusions)

    def test_brief_to_plan_v02_is_native_semantic_extraction(self):
        brief = "An agent receives a request, uses search tools and memory, validates policy, then retries from feedback."
        with patch("anidiagram.planner._brief_to_plan_v01", side_effect=AssertionError("legacy adapter used")):
            plan = brief_to_plan(brief, title="Agent request loop")

        semantic = plan["semantic"]
        self.assertEqual("0.2", plan["version"])
        self.assertTrue(semantic["intent"])
        self.assertTrue(semantic["entities"])
        self.assertTrue(semantic["relations"])
        self.assertTrue(semantic["flows"])
        self.assertEqual(["input-brief"], [source["id"] for source in semantic["sources"]])
        self.assertEqual("0.4", compile_plan(plan)["version"])


if __name__ == "__main__":
    unittest.main()
