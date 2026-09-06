from copy import deepcopy
import unittest

from anidiagram.planner import compile_plan
from anidiagram.schema import compile_scene, DiagramScriptValidationError
from anidiagram.renderer_svg import render_svg
from anidiagram.styles import load_style
from anidiagram.type_semantics import semantic_facts


def plan(kind, relations, details, *, states=None, groups=None):
    return {"version": "0.2", "semantic": {
        "title": kind + " proof", "intent": {"diagram_kind": kind, "primary_question": "How does this work?", "audience": ["technical"]},
        "entities": [{"id": item, "label": item.upper(), "kind": "service", "role": "process", "state": (states or {}).get(item, {})} for item in ("a", "b", "c")],
        "relations": [{"id": item[0], "from": item[1], "to": item[2], "kind": "data-flow", "condition": item[3] if len(item) > 3 else ""} for item in relations],
        "groups": groups or [], "type_details": details}, "presentation": {"layout": "pipeline"}}


class TypeSemanticsTest(unittest.TestCase):
    def test_sequence_return_order_activation_and_round_trip(self):
        value = plan("sequence", [("reply", "b", "a"), ("request", "a", "b")], {
            "participants": ["a", "b"], "messages": [{"relation_id": "request", "mode": "sync"}, {"relation_id": "reply", "mode": "return", "reply_to": "request"}],
            "activations": [{"participant": "b", "start": "request", "end": "reply"}]})
        spec = compile_plan(value)
        self.assertEqual([2, 1], [edge["step"] for edge in spec["edges"]])
        scene = compile_scene(spec)
        self.assertEqual(value["semantic"]["type_details"], scene.type_semantics["details"])
        self.assertIn("Synchronous call: A → B", semantic_facts(scene, "en")[0])
        self.assertIn('id="anidiagram-type-semantics"', render_svg(scene, load_style()))
        value["semantic"]["type_details"]["messages"].reverse()
        with self.assertRaisesRegex(ValueError, "preceding call"):
            compile_plan(value)

    def test_lifecycle_terminal_and_recovery_contract(self):
        value = plan("lifecycle", [("fail", "a", "b"), ("retry", "b", "a"), ("finish", "a", "c")],
                     {"initial": "a", "terminal": ["c"], "recovery_relations": ["retry"]}, states={"b": {"result": "failure"}})
        compile_scene(compile_plan(value))
        value["semantic"]["type_details"]["terminal"] = ["b"]
        with self.assertRaisesRegex(ValueError, "outgoing"):
            compile_plan(value)

    def test_dataflow_directions(self):
        value = plan("dataflow", [("read", "a", "b"), ("write", "b", "c")],
                     {"datasets": ["a", "c"], "transformations": [{"entity_id": "b", "inputs": ["read"], "outputs": ["write"]}]})
        compile_scene(compile_plan(value))
        value["semantic"]["relations"][0].update({"from": "b", "to": "a"})
        with self.assertRaisesRegex(ValueError, "dataset directions"):
            compile_plan(value)

    def test_workflow_distinct_approval_conditions(self):
        value = plan("workflow", [("yes", "a", "b", "approved"), ("no", "a", "c", "rejected")],
                     {"approvals": [{"entity_id": "a", "approved": "yes", "rejected": "no"}]})
        compile_scene(compile_plan(value))
        value["semantic"]["relations"][1]["condition"] = "approved"
        with self.assertRaisesRegex(ValueError, "distinguish"):
            compile_plan(value)

    def test_architecture_boundaries_and_direct_spec_revalidation(self):
        value = plan("architecture", [("enter", "a", "b"), ("internal", "b", "c")], {
            "ownership": [{"group_id": "service", "owner": "Platform"}], "trust_boundaries": ["service"],
            "crossings": [{"relation_id": "enter", "mechanism": "mTLS"}]},
            groups=[{"id": "service", "label": "Service", "kind": "security-boundary", "members": ["b", "c"]}])
        spec = compile_plan(value)
        compile_scene(spec)
        spec["edges"][0]["to"] = "a"
        with self.assertRaisesRegex(DiagramScriptValidationError, "crossings"):
            compile_scene(spec)

    def test_old_freeform_kinds_do_not_enable_strict_checks(self):
        value = plan("custom-architecture", [("edge", "a", "b")], {})
        del value["semantic"]["type_details"]
        self.assertNotIn("type_semantics", compile_plan(value))
