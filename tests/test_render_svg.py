import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from anidiagram.cli import main
from anidiagram.exporters import _render_frames
from anidiagram.exporters import write_gif
from anidiagram.presets import preset_names
from anidiagram.quality import quality_report
from anidiagram.renderer_svg import render_svg
from anidiagram.renderer_svg import render_html
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
        self.assertIn("edge-draw", svg)
        self.assertIn("edge-flow", svg)
        self.assertIn("node-glow", svg)
        self.assertIn("node-burst", svg)
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
        self.assertIn({"path": "$.edges[0].to", "message": "unknown node id 'missing'", "code": "reference", "severity": "error"}, issues)
        self.assertIn({"path": "$.edges[0].animated", "message": "expected a boolean", "code": "type", "severity": "error"}, issues)

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
            "c8c81975843f94faceb7667b3ca8d4b913e4c21cab2428d365135c740898d44b",
            hashlib.sha256(svg.encode("utf-8")).hexdigest(),
        )

    def test_motion_profile_off_renders_static_svg(self):
        spec = json.loads((ROOT / "tests" / "fixtures" / "minimal.diagram.json").read_text(encoding="utf-8"))
        spec["version"] = "0.2"
        spec["motion"] = {"profile": "off"}
        scene = compile_scene(spec)
        svg = render_svg(scene, load_style(ROOT / "styles" / "minimal-light.json"))

        self.assertEqual("off", scene.motion.profile)
        self.assertIn('data-motion-profile="off"', svg)
        self.assertNotIn("animateMotion", svg)
        self.assertNotIn('class="edge-flow', svg)
        self.assertNotIn('class="edge-particle', svg)

    def test_motion_profile_expressive_adds_viewer_controls(self):
        spec = json.loads((ROOT / "tests" / "fixtures" / "minimal.diagram.json").read_text(encoding="utf-8"))
        spec["version"] = "0.2"
        spec["motion"] = {
            "profile": "expressive",
            "sequence": "layered",
            "edge": "comet-flow",
            "node": "pop",
            "group": "marching-ants",
        }
        scene = compile_scene(spec)
        svg = render_svg(scene, load_style(ROOT / "styles" / "minimal-light.json"))
        html = render_html(svg, "Motion Test")

        self.assertEqual("expressive", scene.motion.profile)
        self.assertIn('data-motion-sequence="layered"', svg)
        self.assertIn("Full Motion", html)
        self.assertIn("setMotionMode", html)
        self.assertIn("motion-subtle", html)
        self.assertIn("motion-off", html)

    def test_structured_motion_effects_render_icons_and_effects(self):
        spec = {
            "version": "0.3",
            "canvas": {"width": 720, "height": 420},
            "style": "sketch-board",
            "title": {"text": "Effect Test", "subtitle": "structured motion"},
            "motion": {
                "profile": "teaching",
                "edge": {"preset": "flow-arrow", "particle": "soft-arrow"},
                "node": {"preset": "icon-pulse"},
                "group": {"preset": "border-scan"},
                "title": {"preset": "handwrite-reveal"},
            },
            "groups": [
                {"id": "g", "label": "Panel", "bounds": [60, 130, 600, 210], "role": "process"}
            ],
            "nodes": [
                {"id": "a", "label": "Search", "caption": "source", "position": [110, 205], "size": [180, 82], "role": "source", "icon": "search"},
                {"id": "b", "label": "Guard", "caption": "output", "position": [430, 205], "size": [180, 82], "role": "risk", "icon": "shield"}
            ],
            "edges": [
                {"from": "a", "to": "b", "label": "flow", "role": "process", "effect": {"preset": "flow-arrow", "particle": "soft-arrow"}}
            ],
        }
        scene = compile_scene(spec)
        svg = render_svg(scene, load_style(ROOT / "styles" / "sketch-board.json"))

        self.assertEqual("0.3", scene.version)
        self.assertEqual("flow-arrow", scene.motion.edge_effect.preset)
        self.assertIn('data-motion-profile="teaching"', svg)
        self.assertIn('data-motion-title="handwrite-reveal"', svg)
        self.assertIn("edge-arrow-particle", svg)
        self.assertIn("group-border-scan", svg)
        self.assertIn("title-handwrite", svg)
        self.assertIn("semantic-icon-search", svg)
        self.assertIn("semantic-icon-shield", svg)

    def test_cli_renders_preset_lottie_and_quality(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(
                    [
                        "--preset",
                        "agent-memory",
                        "--outdir",
                        tmp,
                        "--basename",
                        "agent-memory",
                        "--formats",
                        "svg,html,lottie,quality",
                    ]
                )

            result = json.loads(stdout.getvalue())

            self.assertTrue(result["ok"])
            self.assertEqual("0.2", result["schema"]["version"])
            self.assertEqual("agent-memory", result["preset"])
            self.assertTrue(Path(result["outputs"]["svg"]["path"]).is_file())
            self.assertTrue(Path(result["outputs"]["html"]["path"]).is_file())
            self.assertTrue(Path(result["outputs"]["lottie"]["path"]).is_file())
            self.assertTrue(Path(result["outputs"]["quality"]["path"]).is_file())
            self.assertIn("summary", result["outputs"]["quality"])

    def test_raster_animation_frames_change_over_time(self):
        try:
            from PIL import Image, ImageChops
        except Exception:
            self.skipTest("Pillow is not installed")
        spec = json.loads((ROOT / "tests" / "fixtures" / "minimal.diagram.json").read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        style = load_style(ROOT / "styles" / "minimal-light.json")

        frames = _render_frames(scene, style, 4)

        self.assertEqual(4, len(frames))
        self.assertIsNotNone(ImageChops.difference(frames[0], frames[1]).getbbox())
        with tempfile.TemporaryDirectory() as tmp:
            gif_path = Path(tmp) / "motion.gif"
            result = write_gif(scene, style, gif_path, frames=4)
            self.assertEqual("written", result["status"])
            gif = Image.open(gif_path)
            gif.seek(0)
            first = gif.copy().convert("RGB")
            gif.seek(1)
            second = gif.copy().convert("RGB")
            gif.close()
            self.assertIsNotNone(ImageChops.difference(first, second).getbbox())

    def test_all_presets_compile_and_render(self):
        for name in preset_names():
            stdout = io.StringIO()
            with tempfile.TemporaryDirectory() as tmp, redirect_stdout(stdout):
                main(["--preset", name, "--outdir", tmp, "--basename", name, "--formats", "svg,quality"])
            result = json.loads(stdout.getvalue())
            self.assertTrue(result["ok"], name)
            self.assertEqual(name, result["preset"])

    def test_style_catalog_loads(self):
        catalog = json.loads((ROOT / "styles" / "catalog.json").read_text(encoding="utf-8"))
        for name in catalog["styles"]:
            style = load_style(ROOT / "styles" / f"{name}.json")
            self.assertEqual(name, style["name"])

    def test_style_showcase_specs_cover_catalog(self):
        catalog = json.loads((ROOT / "styles" / "catalog.json").read_text(encoding="utf-8"))
        specs_dir = ROOT / "examples" / "style-showcase"
        gallery_dir = ROOT / "gallery" / "styles"

        self.assertTrue((gallery_dir / "index.html").is_file())
        for name in catalog["styles"]:
            spec_path = specs_dir / f"{name}.diagram.json"
            svg_path = gallery_dir / f"{name}.svg"
            html_path = gallery_dir / f"{name}.html"
            quality_path = gallery_dir / f"{name}.quality.json"

            self.assertTrue(spec_path.is_file(), name)
            self.assertTrue(svg_path.is_file(), name)
            self.assertTrue(html_path.is_file(), name)
            self.assertTrue(quality_path.is_file(), name)

            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            scene = compile_scene(spec)
            report = quality_report(scene)

            self.assertEqual(name, scene.style.name)
            self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, report["summary"], name)
            self.assertIn("<svg", svg_path.read_text(encoding="utf-8"))
            self.assertIn("<!doctype html>", html_path.read_text(encoding="utf-8"))

    def test_aurora_orb_style_renders_gradient_texture_nodes(self):
        spec = json.loads((ROOT / "tests" / "fixtures" / "minimal.diagram.json").read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        svg = render_svg(scene, load_style(ROOT / "styles" / "aurora-orb.json"))

        self.assertIn('id="aurora-node-process"', svg)
        self.assertIn('id="grain-texture"', svg)
        self.assertIn('clip-path="url(#clip-', svg)
        self.assertIn('fill="url(#aurora-node-', svg)

    def test_teaching_transformer_example_renders_cleanly(self):
        spec = json.loads((ROOT / "examples" / "teaching-transformer.diagram.json").read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        svg = render_svg(scene, load_style(ROOT / "styles" / "sketch-board.json"))
        report = quality_report(scene)

        self.assertTrue(report["ok"])
        self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, report["summary"])
        self.assertIn("semantic-icon-database", svg)
        self.assertIn("edge-flow-ghost-flow", svg)
        self.assertIn("edge-flow-dynamic-dash", svg)
        self.assertIn("edge-flow-glow-line", svg)

    def test_quality_report_detects_overlap(self):
        spec = json.loads((ROOT / "tests" / "fixtures" / "minimal.diagram.json").read_text(encoding="utf-8"))
        spec["nodes"][1]["position"] = [90, 155]
        scene = compile_scene(spec)

        report = quality_report(scene)

        self.assertFalse(report["ok"])
        self.assertEqual("node_overlap", report["issues"][0]["code"])


if __name__ == "__main__":
    unittest.main()
