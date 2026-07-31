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

    def _agent_loop_plan(self):
        def entity(entity_id, label, kind, role):
            return {
                "id": entity_id,
                "label": label,
                "kind": kind,
                "role": role,
                "importance": "primary",
            }

        def relation(relation_id, source, target, kind="data-flow"):
            return {
                "id": relation_id,
                "from": source,
                "to": target,
                "kind": kind,
                "direction": "forward",
                "importance": "primary",
            }

        entities = [
            entity("trigger", "Trigger / Input", "scheduler", "source"),
            entity("think", "Think", "reasoning", "agent"),
            entity("act", "Act", "agent", "agent"),
            entity("observe", "Observe", "monitoring", "output"),
            entity("done", "Done?", "task", "risk"),
            entity("output", "Output", "output", "output"),
            entity("working-memory", "Working Memory", "memory", "memory"),
            entity("long-term-memory", "Long-Term Memory", "vector-database", "memory"),
            entity("validate", "Validate", "shield", "risk"),
            entity("scope", "Scope", "token", "risk"),
            entity("budget", "Budget", "scheduler", "risk"),
            entity("allow", "Allow", "shield", "risk"),
            entity("reject", "Reject + Replan", "reasoning", "risk"),
            entity("tool-types", "Tool Types", "tool", "tool"),
            entity("dispatch", "Dispatch", "gateway", "tool"),
            entity("return-result", "Return Result", "output", "tool"),
        ]
        relations = [
            relation("trigger-think", "trigger", "think"),
            relation("think-act", "think", "act"),
            relation("act-observe", "act", "observe"),
            relation("observe-done", "observe", "done"),
            relation("done-output", "done", "output"),
            relation("done-think", "done", "think", "feedback"),
            relation("act-validate", "act", "validate", "security"),
            relation("validate-scope", "validate", "scope", "security"),
            relation("scope-budget", "scope", "budget", "security"),
            relation("budget-allow", "budget", "allow", "security"),
            relation("allow-tool", "allow", "tool-types"),
            relation("tool-dispatch", "tool-types", "dispatch"),
            relation("dispatch-return", "dispatch", "return-result"),
            relation("return-observe", "return-result", "observe"),
            relation("think-working", "think", "working-memory", "context-loading"),
            relation("long-think", "long-term-memory", "think", "context-loading"),
            relation("allow-reject", "allow", "reject", "failure"),
            relation("reject-think", "reject", "think", "feedback"),
        ]
        next(item for item in relations if item["id"] == "done-output")["condition"] = "Final answer is ready"
        next(item for item in relations if item["id"] == "done-think")["condition"] = "Another iteration is needed"
        return {
            "version": "0.2",
            "semantic": {
                "title": "Agent loop internals",
                "intent": {
                    "diagram_kind": "architecture",
                    "primary_question": "How does a governed agent loop run?",
                    "audience": ["technical"],
                    "scope": "Trigger, cognition, memory, safety, tools, and output",
                },
                "entities": entities,
                "relations": relations,
                "groups": [
                    {"id": "trigger-input", "label": "Trigger / Input", "kind": "trigger", "members": ["trigger"]},
                    {"id": "cognitive-core", "label": "Cognitive Core", "kind": "agent-loop", "members": ["think", "act", "observe", "done", "output"]},
                    {"id": "memory-layer", "label": "Memory", "kind": "memory", "members": ["working-memory", "long-term-memory"]},
                    {"id": "safety-layers", "label": "Safety Layers", "kind": "safety", "members": ["validate", "scope", "budget", "allow", "reject"]},
                    {"id": "tool-execution", "label": "Tool Execution", "kind": "tool-execution", "members": ["tool-types", "dispatch", "return-result"]},
                ],
                "flows": [
                    {"id": "main", "label": "Main loop", "relation_ids": ["trigger-think", "think-act", "act-observe", "observe-done", "done-output"], "importance": "primary", "repeat": "event-driven"},
                    {"id": "tool-loop", "label": "Governed tool loop", "relation_ids": ["act-validate", "validate-scope", "scope-budget", "budget-allow", "allow-tool", "tool-dispatch", "dispatch-return", "return-observe", "observe-done", "done-think"], "importance": "primary", "repeat": "loop"},
                ],
            },
            "presentation": {
                "icon_system": "auto",
                "style": "sketch-board",
                "layout": "agent-loop",
                "motion": "showcase-v1",
            },
        }

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

        self.assertEqual(16, len(signatures))
        self.assertEqual(16, len(set(signatures.values())))

    def test_layered_loop_layout_uses_three_title_safe_serpentine_layers(self):
        plan = json.loads((ROOT / "examples" / "loop-engineering-minimal-light.plan.json").read_text(encoding="utf-8"))
        spec = compile_plan(plan)
        scene = compile_scene(spec)

        self.assertEqual("layered-loop", spec["layout"])
        self.assertEqual(
            {"value": "layered-loop", "source": "explicit"},
            spec["resolved_presentation"]["layout"],
        )
        self.assertEqual({"nodes": 8, "edges": 8, "groups": 3}, scene.stats())
        positions = {node["id"]: node["position"] for node in spec["nodes"]}
        self.assertEqual(1020, spec["canvas"]["width"])
        self.assertEqual([100, 235], positions["human-engineer"])
        self.assertEqual([700, 235], positions["automation-heartbeat"])
        self.assertEqual([700, 455], positions["isolated-worktree"])
        self.assertEqual([400, 455], positions["project-skills"])
        self.assertEqual([100, 455], positions["maker-agent"])
        self.assertEqual([100, 675], positions["verifier-agent"])
        self.assertEqual([400, 675], positions["tool-connectors"])
        self.assertEqual([700, 675], positions["external-state"])
        group_left = min(group["bounds"][0] for group in spec["groups"])
        group_right = max(group["bounds"][0] + group["bounds"][2] for group in spec["groups"])
        self.assertEqual(group_left, spec["canvas"]["width"] - group_right)
        self.assertGreaterEqual(min(node["position"][1] for node in spec["nodes"]), 235)
        self.assertGreaterEqual(min(group["bounds"][1] for group in spec["groups"]), 193)
        self.assertGreaterEqual(spec["canvas"]["height"], 920)
        edges = {edge["semantic_relation_id"]: edge for edge in spec["edges"]}
        self.assertEqual("straight", edges["human-governs-automation"]["route"])
        self.assertEqual("straight", edges["automation-opens-worktree"]["route"])
        self.assertEqual("straight", edges["maker-submits-draft"]["route"])
        self.assertEqual("points", edges["state-informs-human"]["route"])
        self.assertLess(edges["state-informs-human"]["points"][2][0], 50)
        self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, quality_report(scene)["summary"])

    def test_layered_loop_routes_skip_lane_and_dense_feedback_outside_content(self):
        plan = json.loads((ROOT / "examples" / "loop-engineering-minimal-light.plan.json").read_text(encoding="utf-8"))
        relations = plan["semantic"]["relations"]
        relations.append(
            {
                "id": "human-state-audit",
                "from": "human-engineer",
                "to": "external-state",
                "kind": "governance",
                "direction": "forward",
                "importance": "supporting",
            }
        )
        bottom_nodes = ("verifier-agent", "tool-connectors", "external-state")
        top_nodes = ("human-engineer", "automation-heartbeat")
        for index in range(7):
            relations.append(
                {
                    "id": f"dense-feedback-{index + 1}",
                    "from": bottom_nodes[index % len(bottom_nodes)],
                    "to": top_nodes[index % len(top_nodes)],
                    "kind": "feedback",
                    "direction": "forward",
                    "importance": "supporting",
                }
            )

        spec = compile_plan(plan)
        scene = compile_scene(spec)
        edges = {edge["semantic_relation_id"]: edge for edge in spec["edges"]}
        skip_lane = edges["human-state-audit"]
        feedbacks = [
            edge
            for relation_id, edge in edges.items()
            if relation_id == "state-informs-human" or relation_id.startswith("dense-feedback-")
        ]
        node_bottom = max(node["position"][1] + node["size"][1] for node in spec["nodes"])

        self.assertIn(spec["canvas"]["width"] - 36, [point[0] for point in skip_lane["points"]])
        self.assertTrue(all(edge["points"][2][0] == 36 for edge in feedbacks))
        self.assertGreater(min(edge["points"][1][1] for edge in feedbacks), node_bottom)
        self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, quality_report(scene)["summary"])

    def test_agent_loop_layout_reproduces_the_reference_zones(self):
        spec = compile_plan(self._agent_loop_plan())
        positions = {node["id"]: node["position"] for node in spec["nodes"]}
        nodes = {node["id"]: node for node in spec["nodes"]}
        groups = {group["id"]: group for group in spec["groups"]}
        edges = {edge["semantic_relation_id"]: edge for edge in spec["edges"]}

        self.assertEqual("agent-loop", spec["layout"])
        self.assertEqual({"width": 1640, "height": 1240}, spec["canvas"])
        self.assertEqual([710, 175], positions["trigger"])
        self.assertEqual([[90, 365], [450, 365], [810, 365]], [positions[item] for item in ("think", "act", "observe")])
        self.assertEqual([[790, 535], [1180, 535]], [positions[item] for item in ("done", "output")])
        self.assertEqual([55, 790], positions["working-memory"])
        self.assertEqual([330, 790], positions["validate"])
        self.assertEqual([1360, 760], positions["tool-types"])
        self.assertEqual("decision", nodes["done"]["shape"])
        self.assertEqual("task", nodes["done"]["icon"])
        self.assertEqual("straight", edges["think-act"]["route"])
        self.assertEqual("orthogonal", edges["observe-done"]["route"])
        self.assertEqual("points", edges["done-think"]["route"])
        self.assertTrue(all("step" not in node for node in nodes.values()))
        self.assertTrue(all("step" not in edge for edge in edges.values()))
        self.assertLess(groups["trigger-input"]["bounds"][1], groups["cognitive-core"]["bounds"][1])
        self.assertLess(groups["cognitive-core"]["bounds"][1], groups["memory-layer"]["bounds"][1])
        self.assertLess(
            groups["memory-layer"]["bounds"][0] + groups["memory-layer"]["bounds"][2],
            groups["safety-layers"]["bounds"][0],
        )
        self.assertLess(
            groups["safety-layers"]["bounds"][0] + groups["safety-layers"]["bounds"][2],
            groups["tool-execution"]["bounds"][0],
        )

    def test_agent_loop_layout_wraps_extended_core_nodes_without_overlap_or_zone_drift(self):
        plan = self._agent_loop_plan()
        cognitive = next(group for group in plan["semantic"]["groups"] if group["id"] == "cognitive-core")
        extra_ids = []
        for index in range(5):
            entity_id = f"review-{index + 1}"
            extra_ids.append(entity_id)
            plan["semantic"]["entities"].append(
                {
                    "id": entity_id,
                    "label": f"Review {index + 1}",
                    "kind": "human-reviewer",
                    "role": "agent",
                    "importance": "supporting",
                }
            )
        cognitive["members"].extend(extra_ids)
        plan["semantic"]["relations"].append(
            {
                "id": "deep-review-feedback",
                "from": extra_ids[-1],
                "to": "think",
                "kind": "feedback",
                "direction": "forward",
                "importance": "supporting",
            }
        )

        spec = compile_plan(plan)
        scene = compile_scene(spec)
        report = quality_report(scene, load_style(ROOT / "styles" / "sketch-board.json"))

        self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, report["summary"])
        core_nodes = [node for node in spec["nodes"] if node["id"] in cognitive["members"]]
        rectangles = [(*node["position"], *node["size"]) for node in core_nodes]
        for index, left in enumerate(rectangles):
            for right in rectangles[index + 1 :]:
                overlaps = (
                    left[0] < right[0] + right[2]
                    and left[0] + left[2] > right[0]
                    and left[1] < right[1] + right[3]
                    and left[1] + left[3] > right[1]
                )
                self.assertFalse(overlaps, (left, right))
        deepest = next(node for node in spec["nodes"] if node["id"] == extra_ids[-1])
        feedback = next(edge for edge in spec["edges"] if edge["semantic_relation_id"] == "deep-review-feedback")
        self.assertGreaterEqual(deepest["position"][1], 835)
        self.assertEqual(deepest["position"][1] + deepest["size"][1], feedback["points"][0][1])

    def test_agent_loop_layout_reflows_a_wide_safety_decision(self):
        plan = self._agent_loop_plan()
        validate_scope = next(
            relation for relation in plan["semantic"]["relations"] if relation["id"] == "validate-scope"
        )
        validate_scope["condition"] = "Scope is valid"
        plan["semantic"]["relations"].append(
            {
                "id": "validate-reject",
                "from": "validate",
                "to": "reject",
                "kind": "failure",
                "direction": "forward",
                "importance": "supporting",
                "condition": "Scope is invalid",
            }
        )

        spec = compile_plan(plan)
        scene = compile_scene(spec)
        report = quality_report(scene, load_style(ROOT / "styles" / "sketch-board.json"))
        nodes = {node["id"]: node for node in spec["nodes"]}

        self.assertEqual("decision", nodes["validate"]["shape"])
        self.assertEqual([320, 116], nodes["validate"]["size"])
        self.assertGreaterEqual(nodes["scope"]["position"][0] - 24, nodes["validate"]["position"][0] + 320)
        self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, report["summary"])

    def test_agent_loop_layout_reserves_space_for_dense_cross_zone_corridors(self):
        plan = self._agent_loop_plan()
        for index in range(11):
            plan["semantic"]["relations"].append(
                {
                    "id": f"dense-policy-{index + 1}",
                    "from": "observe",
                    "to": "validate",
                    "kind": "security",
                    "direction": "forward",
                    "importance": "supporting",
                }
            )

        spec = compile_plan(plan)
        scene = compile_scene(spec)
        report = quality_report(scene, load_style(ROOT / "styles" / "sketch-board.json"))
        nodes = {node["id"]: node for node in spec["nodes"]}
        corridors = [
            edge["points"][1][1]
            for edge in spec["edges"]
            if str(edge.get("semantic_relation_id", "")).startswith("dense-policy-")
        ]

        self.assertLess(max(corridors) + 30, nodes["validate"]["position"][1])
        self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, report["summary"])

    def test_agent_loop_limits_inferred_decisions_to_core_and_safety_zones(self):
        plan = self._agent_loop_plan()
        relations = plan["semantic"]["relations"]
        next(relation for relation in relations if relation["id"] == "trigger-think")["condition"] = "Start thinking"
        next(relation for relation in relations if relation["id"] == "dispatch-return")["condition"] = "Return directly"
        relations.extend(
            [
                {
                    "id": "trigger-act",
                    "from": "trigger",
                    "to": "act",
                    "kind": "data-flow",
                    "direction": "forward",
                    "importance": "supporting",
                    "condition": "Start acting",
                },
                {
                    "id": "working-think",
                    "from": "working-memory",
                    "to": "think",
                    "kind": "context-loading",
                    "direction": "forward",
                    "importance": "supporting",
                    "condition": "Recall context",
                },
                {
                    "id": "working-act",
                    "from": "working-memory",
                    "to": "act",
                    "kind": "context-loading",
                    "direction": "forward",
                    "importance": "supporting",
                    "condition": "Recall tools",
                },
                {
                    "id": "dispatch-observe",
                    "from": "dispatch",
                    "to": "observe",
                    "kind": "data-flow",
                    "direction": "forward",
                    "importance": "supporting",
                    "condition": "Stream partial result",
                },
            ]
        )

        spec = compile_plan(plan)
        scene = compile_scene(spec)
        nodes = {node["id"]: node for node in spec["nodes"]}

        for node_id in ("trigger", "working-memory", "dispatch"):
            self.assertNotEqual("decision", nodes[node_id].get("shape"))
            self.assertEqual([220, 116], nodes[node_id]["size"])
        self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, quality_report(scene)["summary"])

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
        self.assertEqual("stream-flow", edge_by_relation["client-request"]["effect"]["preset"])
        self.assertEqual(1, edge_by_relation["client-request"]["step"])
        self.assertEqual(2, edge_by_relation["ingress-route"]["step"])

    def test_semantic_fallback_state_and_group_metadata_survive_compilation(self):
        plan = self._plan()
        plan["presentation"]["icon_system"] = "illustrated"
        workload = next(entity for entity in plan["semantic"]["entities"] if entity["id"] == "workload")
        workload["kind"] = "kubernetes-pod"
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

        self.assertEqual("kubernetes-pod", node["semantic_kind"])
        self.assertEqual("role-fallback", node["icon_resolution"])
        self.assertEqual(workload["state"], node["state"])
        self.assertEqual("system", group["semantic_kind"])
        self.assertEqual("primary", group["importance"])
        self.assertEqual("platform", group["parent"])

        scene = compile_scene(spec)
        scene_node = next(item for item in scene.nodes if item.node_id == "workload")
        scene_group = next(item for item in scene.groups if item.group_id == "runtime")
        self.assertEqual("kubernetes-pod", scene_node.semantic_kind)
        self.assertEqual("role-fallback", scene_node.icon_resolution)
        self.assertEqual(workload["state"], scene_node.state)
        self.assertEqual("platform", scene_group.parent)

        report = quality_report(scene, load_style())
        fallback_issues = [issue for issue in report["issues"] if issue["code"] == "semantic_icon_fallback"]
        self.assertTrue(fallback_issues)
        self.assertTrue(any("kubernetes-pod" in issue["message"] for issue in fallback_issues))

    def test_composition_v1_rejects_any_stale_resolved_axis(self):
        spec = compile_plan(self._plan())
        mutations = {
            "icon_system": "diagram-core-v1",
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
        script_schema = json.loads((ROOT / "schemas" / "diagram-script-v0.4.schema.json").read_text(encoding="utf-8"))
        self.assertIn("presentation", schema["required"])
        self.assertEqual("array", schema["$defs"]["intent"]["properties"]["exclusions"]["type"])
        self.assertIn("agent-loop", schema["$defs"]["presentation"]["properties"]["layout"]["enum"])
        self.assertIn("layered-loop", schema["$defs"]["presentation"]["properties"]["layout"]["enum"])
        self.assertIn("agent-loop", script_schema["properties"]["layout"]["enum"])
        self.assertIn("layered-loop", script_schema["properties"]["layout"]["enum"])
        self.assertIn(
            "agent-loop",
            script_schema["$defs"]["resolved_presentation"]["properties"]["layout"]["allOf"][1]["properties"]["value"]["enum"],
        )
        self.assertIn(
            "layered-loop",
            script_schema["$defs"]["resolved_presentation"]["properties"]["layout"]["allOf"][1]["properties"]["value"]["enum"],
        )

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
