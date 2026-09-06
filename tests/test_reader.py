from copy import deepcopy
import json
from pathlib import Path
import unittest

from anidiagram.planner import compile_plan
from anidiagram.schema import compile_scene, DiagramScriptValidationError
from anidiagram.renderer_html_runtime import render_html_runtime
from anidiagram.renderer_svg import render_svg
from anidiagram.styles import load_style

ROOT = Path(__file__).resolve().parents[1]


class ReaderTest(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT / "examples/contracts/production-request-path.plan.json").read_text())

    def test_reader_is_opt_in_and_never_changes_svg(self):
        old = compile_scene(compile_plan(self.plan))
        self.plan["reader"] = {"enabled": True}
        scene = compile_scene(compile_plan(self.plan))
        style = load_style()
        self.assertEqual(render_svg(old, style), render_svg(scene, style))
        self.assertNotIn('id="diagram-reader"', render_html_runtime(old, style))
        self.assertIn('id="diagram-reader"', render_html_runtime(scene, style))

    def test_user_copy_cannot_escape_json_or_controls(self):
        self.plan["reader"] = {"enabled": True}
        self.plan["semantic"]["entities"][0]["label"] = '</script><script>alert("injected")</script>'
        html = render_html_runtime(compile_scene(compile_plan(self.plan)), load_style())
        self.assertNotIn('<script>alert("injected")</script>', html)
        self.assertIn('\\u003c/script>', html)

    def test_legacy_and_invalid_reader_options_rejected(self):
        for value in (True, {"enabled": "yes"}, {"enabled": True, "unknown": 1}):
            self.plan["reader"] = value
            with self.assertRaises(ValueError):
                compile_plan(self.plan)
        spec = {"version": "0.1", "nodes": [{"id": "a", "label": "A", "position": [100, 100], "size": [180, 80]}], "reader": {"enabled": True}}
        with self.assertRaisesRegex(DiagramScriptValidationError, "0.4"):
            compile_scene(spec)
