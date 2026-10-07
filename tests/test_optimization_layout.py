import json
import unittest
from copy import deepcopy
from pathlib import Path

from anidiagram.planner import compile_plan
from anidiagram.presets import compile_preset
from anidiagram.schema import DiagramScriptValidationError, compile_scene


ROOT = Path(__file__).resolve().parents[1]


def overlaps(left, right):
    lx, ly, lw, lh = left
    rx, ry, rw, rh = right
    return lx < rx + rw and rx < lx + lw and ly < ry + rh and ry < ly + lh


class OptimizationLayoutTest(unittest.TestCase):
    def rag_plan(self):
        return json.loads((ROOT / "examples/enterprise-rag-production-illustrated.plan.json").read_text())

    def assert_members_fit(self, spec, memberships):
        nodes = {node["id"]: node for node in spec["nodes"]}
        groups = {group["id"]: group for group in spec["groups"]}
        for group_id, members in memberships.items():
            x, y, width, height = groups[group_id]["bounds"]
            for member_id in members:
                node = nodes[member_id]
                nx, ny = node["position"]
                nw, nh = node["size"]
                with self.subTest(group=group_id, member=member_id):
                    self.assertGreaterEqual(nx, x)
                    self.assertGreaterEqual(ny, y + 42, "member must clear the group title region")
                    self.assertLessEqual(nx + nw, x + width)
                    self.assertLessEqual(ny + nh, y + height)

    def test_rag_layered_groups_are_separate_and_contain_their_members(self):
        plan = self.rag_plan()
        original = deepcopy(plan)
        spec = compile_plan(plan)
        self.assertEqual(original, plan)
        left, right = spec["groups"]
        self.assertFalse(overlaps(left["bounds"], right["bounds"]))
        self.assert_members_fit(spec, {group["id"]: group["members"] for group in plan["semantic"]["groups"]})
        self.assertEqual({item["id"] for item in plan["semantic"]["relations"]}, {edge["semantic_relation_id"] for edge in spec["edges"]})
        compile_scene(spec)  # Also checks every node and group fits the canvas.
        self.assertEqual(spec, compile_plan(plan), "layout must be deterministic")

    def test_grouped_layered_layout_keeps_ungrouped_entities(self):
        plan = self.rag_plan()
        plan["semantic"]["entities"].append({"id": "monitor", "label": "Monitor", "kind": "monitoring", "role": "tool"})
        spec = compile_plan(plan)
        self.assertEqual(13, len(spec["nodes"]))
        monitor = next(node for node in spec["nodes"] if node["id"] == "monitor")
        box = monitor["position"] + monitor["size"]
        for group in spec["groups"]:
            self.assertFalse(overlaps(box, group["bounds"]))
        compile_scene(spec)

    def test_group_membership_survives_plan_script_scene_compilation(self):
        plan = self.rag_plan()
        spec = compile_plan(plan)
        scene = compile_scene(spec)
        expected = {group["id"]: tuple(group["members"]) for group in plan["semantic"]["groups"]}
        self.assertEqual(expected, {group.group_id: group.members for group in scene.groups})
        self.assertEqual(expected, {group["id"]: tuple(group["members"]) for group in spec["groups"]})

    def test_swimlane_preset_reserves_title_space_and_keeps_notify_inside(self):
        spec = compile_preset("swimlane")
        expected = {"customer": ["request", "notify"], "team": ["triage", "approve"], "system": ["automate"]}
        self.assert_members_fit(spec, expected)
        self.assertEqual(expected, {group["id"]: group["members"] for group in spec["groups"]})
        compile_scene(spec)

    def test_authored_script_geometry_is_preserved_with_optional_membership(self):
        spec = compile_preset("compare")
        spec["groups"][0]["members"] = ["a-cost", "a-risk"]
        scene = compile_scene(spec)
        self.assertEqual(tuple(spec["nodes"][0]["position"]), scene.nodes[0].position)
        self.assertEqual(("a-cost", "a-risk"), scene.groups[0].members)
        self.assertEqual((), scene.groups[1].members)

    def test_group_membership_rejects_unknown_duplicate_and_invalid_ids(self):
        for members in (["missing"], ["request", "request"], [42], "request"):
            spec = compile_preset("swimlane")
            spec["groups"][0]["members"] = members
            with self.subTest(members=members), self.assertRaises(DiagramScriptValidationError):
                compile_scene(spec)


if __name__ == "__main__":
    unittest.main()
