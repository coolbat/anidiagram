import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from anidiagram.cli import main
from anidiagram.renderer_svg import render_svg
from anidiagram.schema import DiagramScriptValidationError, compile_scene
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]


class SvgRendererTest(unittest.TestCase):
    def test_render_svg_contains_animation_and_labels(self):
        spec = json.loads((ROOT / "examples" / "agent-memory.diagram.json").read_text(encoding="utf-8"))
        style = load_style(ROOT / "styles" / "blueprint.json")

        scene = compile_scene(spec)
        svg = render_svg(scene, style)

        self.assertIn("<svg", svg)
        self.assertIn("animateMotion", svg)
        self.assertIn("Agent Memory System", svg)
        self.assertIn("Planner Agent", svg)
        self.assertIn("marker-end", svg)

    def test_cli_writes_svg_and_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(
                    [
                        "--spec",
                        str(ROOT / "examples" / "agent-memory.diagram.json"),
                        "--style",
                        str(ROOT / "styles" / "deep-tech.json"),
                        "--outdir",
                        tmp,
                        "--basename",
                        "agent-memory",
                        "--html",
                    ]
                )
            svg = Path(tmp) / "agent-memory.svg"
            html = Path(tmp) / "agent-memory.html"

            self.assertTrue(svg.is_file())
            self.assertTrue(html.is_file())
            self.assertIn("animateMotion", svg.read_text(encoding="utf-8"))
            self.assertIn("<!doctype html>", html.read_text(encoding="utf-8"))

    def test_cli_prints_structured_result_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(
                    [
                        "--spec",
                        str(ROOT / "tests" / "fixtures" / "minimal.diagram.json"),
                        "--style",
                        str(ROOT / "styles" / "minimal-light.json"),
                        "--outdir",
                        tmp,
                        "--basename",
                        "minimal",
                    ]
                )

            result = json.loads(stdout.getvalue())

            self.assertTrue(result["ok"])
            self.assertEqual({"name": "DiagramScript", "version": "0.1"}, result["schema"])
            self.assertEqual({"nodes": 2, "edges": 1, "groups": 0}, result["stats"])
            self.assertEqual("svg", result["outputs"]["svg"]["format"])
            self.assertTrue(Path(result["outputs"]["svg"]["path"]).is_file())

    def test_invalid_edge_reference_reports_path(self):
        spec = json.loads((ROOT / "tests" / "fixtures" / "invalid-edge.diagram.json").read_text(encoding="utf-8"))

        with self.assertRaises(DiagramScriptValidationError) as context:
            compile_scene(spec)

        issues = [issue.to_dict() for issue in context.exception.issues]
        self.assertIn({"path": "$.edges[0].to", "message": "unknown node id 'missing'", "code": "reference"}, issues)
        self.assertIn({"path": "$.edges[0].animated", "message": "expected a boolean", "code": "type"}, issues)

    def test_cli_prints_validation_error_json_to_stderr(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with self.assertRaises(SystemExit) as context:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    main(
                        [
                            "--spec",
                            str(ROOT / "tests" / "fixtures" / "invalid-edge.diagram.json"),
                            "--outdir",
                            tmp,
                            "--basename",
                            "broken",
                        ]
                    )

            self.assertEqual(2, context.exception.code)
            self.assertEqual("", stdout.getvalue())
            result = json.loads(stderr.getvalue())
            self.assertFalse(result["ok"])
            self.assertEqual("diagram_script_validation_failed", result["error"]["code"])
            self.assertEqual("$.edges[0].to", result["error"]["issues"][0]["path"])

    def test_fixture_svg_output_is_stable(self):
        spec = json.loads((ROOT / "tests" / "fixtures" / "minimal.diagram.json").read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        svg = render_svg(scene, load_style(ROOT / "styles" / "minimal-light.json"))

        self.assertEqual(
            "e389fecb13b5abc9a8bcb43a9bccf2e0c9a3e8570ca36cd9745dc5030b8fe0c0",
            hashlib.sha256(svg.encode("utf-8")).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
