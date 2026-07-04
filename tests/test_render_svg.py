import json
import tempfile
import unittest
from pathlib import Path

from anidiagram.cli import main
from anidiagram.renderer_svg import render_svg
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]


class SvgRendererTest(unittest.TestCase):
    def test_render_svg_contains_animation_and_labels(self):
        spec = json.loads((ROOT / "examples" / "agent-memory.diagram.json").read_text(encoding="utf-8"))
        style = load_style(ROOT / "styles" / "blueprint.json")

        svg = render_svg(spec, style)

        self.assertIn("<svg", svg)
        self.assertIn("animateMotion", svg)
        self.assertIn("Agent Memory System", svg)
        self.assertIn("Planner Agent", svg)
        self.assertIn("marker-end", svg)

    def test_cli_writes_svg_and_html(self):
        with tempfile.TemporaryDirectory() as tmp:
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


if __name__ == "__main__":
    unittest.main()
