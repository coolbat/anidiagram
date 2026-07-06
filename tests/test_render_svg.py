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
from anidiagram.planner import brief_to_plan
from anidiagram.planner import compile_plan
from anidiagram.presets import preset_names
from anidiagram.quality import quality_report
from anidiagram.renderer_svg import icon_surface_accent
from anidiagram.renderer_svg import icon_surface_fill
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
            "ea7ca75496ed55477d7d17d231d32ac35e0ed184fe8967199161b5af2b57f9f5",
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

    def test_motion_policy_limits_arrow_particles_and_pulses(self):
        spec = {
            "version": "0.3",
            "canvas": {"width": 860, "height": 460},
            "title": {"text": "Motion Budget", "subtitle": "focused movement"},
            "motion": {
                "profile": "teaching",
                "edge": {"preset": "flow-arrow", "particle": "soft-arrow"},
                "node": {"preset": "icon-pulse"},
                "group": {"preset": "border-scan"},
            },
            "motion_policy": {
                "profile": "focused",
                "max_active_flow_edges": 1,
                "max_particle_edges": 1,
                "particle_count_per_edge": 1,
                "max_active_pulse_nodes": 1,
                "max_scanning_groups": 0,
            },
            "groups": [
                {"id": "panel", "label": "Panel", "bounds": [45, 140, 770, 185], "role": "process"}
            ],
            "nodes": [
                {"id": "a", "label": "Input", "caption": "source", "position": [90, 195], "size": [150, 82], "role": "agent", "icon": "search"},
                {"id": "b", "label": "Process", "caption": "work", "position": [355, 195], "size": [150, 82], "role": "output", "icon": "agent"},
                {"id": "c", "label": "Output", "caption": "done", "position": [620, 195], "size": [150, 82], "role": "risk", "icon": "shield"},
            ],
            "edges": [
                {"from": "a", "to": "b", "label": "one", "effect": {"preset": "flow-arrow", "particle": "soft-arrow"}},
                {"from": "b", "to": "c", "label": "two", "effect": {"preset": "flow-arrow", "particle": "soft-arrow"}},
                {"from": "a", "to": "c", "label": "three", "route": "points", "points": [[165, 195], [165, 150], [695, 150], [695, 195]], "effect": {"preset": "flow-arrow", "particle": "soft-arrow"}},
            ],
        }
        scene = compile_scene(spec)
        svg = render_svg(scene, load_style(ROOT / "styles" / "sketch-board.json"))

        self.assertEqual(1, svg.count('class="edge-particle edge-arrow-particle"'))
        self.assertEqual(2, svg.count('class="node-burst"'))
        self.assertNotIn("group-border-scan", svg)

    def test_quality_report_warns_motion_overload(self):
        spec = {
            "version": "0.3",
            "canvas": {"width": 660, "height": 360},
            "title": {"text": "Overload", "subtitle": "budget warning"},
            "motion": {
                "profile": "teaching",
                "edge": {"preset": "flow-arrow", "particle": "soft-arrow"},
                "node": {"preset": "icon-pulse"},
            },
            "motion_policy": {
                "profile": "readable",
                "max_active_flow_edges": 1,
                "max_active_pulse_nodes": 0,
            },
            "nodes": [
                {"id": "a", "label": "A", "caption": "source", "position": [80, 165], "size": [130, 74], "role": "agent"},
                {"id": "b", "label": "B", "caption": "process", "position": [270, 165], "size": [130, 74], "role": "process"},
                {"id": "c", "label": "C", "caption": "output", "position": [460, 165], "size": [130, 74], "role": "output"},
            ],
            "edges": [
                {"from": "a", "to": "b", "label": "one"},
                {"from": "b", "to": "c", "label": "two"},
            ],
        }
        scene = compile_scene(spec)
        report = quality_report(scene)

        self.assertTrue(report["ok"])
        self.assertGreater(report["summary"]["warnings"], 0)
        self.assertIn("motion_overload", {issue["code"] for issue in report["issues"]})

    def test_runtime_loop_motion_keeps_frames_static_and_animates_micro_elements(self):
        spec = {
            "version": "0.3",
            "canvas": {"width": 760, "height": 430},
            "title": {"text": "Runtime Loop", "subtitle": "micro motion"},
            "motion": {
                "profile": "runtime-loop",
                "edge": {"preset": "signal-dot"},
                "node": {"preset": "icon-breathe"},
                "group": {"preset": "static"},
                "title": {"preset": "breathe"},
            },
            "motion_policy": {"profile": "readable-runtime"},
            "groups": [
                {"id": "g", "label": "Loop", "bounds": [45, 140, 665, 180], "role": "process"}
            ],
            "nodes": [
                {"id": "a", "label": "Think", "caption": "reason", "position": [90, 195], "size": [145, 78], "role": "agent", "icon": "agent"},
                {"id": "b", "label": "Act", "caption": "tool call", "position": [310, 195], "size": [145, 78], "role": "tool", "icon": "tool"},
                {"id": "c", "label": "Observe", "caption": "result", "position": [530, 195], "size": [145, 78], "role": "output", "icon": "search"},
            ],
            "edges": [
                {"from": "a", "to": "b", "label": "signal", "effect": {"preset": "signal-dot"}},
                {"from": "b", "to": "c", "label": "arrow", "effect": {"preset": "signal-arrow"}},
                {
                    "from": "c",
                    "to": "a",
                    "label": "retry",
                    "route": "points",
                    "points": [[602, 273], [602, 342], [162, 342], [162, 273]],
                    "effect": {"preset": "dash-flow"},
                },
            ],
        }
        scene = compile_scene(spec)
        report = quality_report(scene)
        svg = render_svg(scene, load_style(ROOT / "styles" / "minimal-light.json"))

        self.assertEqual("runtime-loop", scene.motion.profile)
        self.assertEqual("micro", scene.motion_policy.motion_area)
        self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, report["summary"])
        self.assertIn('data-motion-sequence="loop"', svg)
        self.assertIn("edge-flow-dash-flow", svg)
        self.assertIn('class="edge-particle"', svg)
        self.assertIn('class="edge-particle edge-arrow-particle"', svg)
        self.assertIn("semantic-icon-breathe", svg)
        self.assertIn("icon-breathe-halo", svg)
        self.assertIn("semanticIconBreathe", svg)
        self.assertIn('values="0.86;1;0.86"', svg)
        self.assertNotIn('class="node-burst"', svg)
        self.assertNotIn('class="node-glow"', svg)
        self.assertNotIn("group-border-scan", svg)
        self.assertNotIn('values="1;0"', svg)

    def test_icon_semantic_motion_renders_icon_specific_micro_animations(self):
        spec = {
            "version": "0.3",
            "canvas": {"width": 1040, "height": 520},
            "title": {"text": "Semantic Icon Motion", "subtitle": "icon-local micro animation"},
            "motion": {
                "profile": "runtime-loop",
                "node": {"preset": "icon-semantic"},
                "edge": {"preset": "static"},
                "group": {"preset": "static"},
                "title": {"preset": "breathe"},
            },
            "motion_policy": {
                "profile": "readable-runtime",
                "max_active_pulse_nodes": 12,
            },
            "nodes": [
                {"id": "database", "label": "Database", "caption": "write", "position": [70, 150], "size": [150, 72], "role": "memory", "icon": "database"},
                {"id": "file", "label": "File", "caption": "lines", "position": [245, 150], "size": [150, 72], "role": "source", "icon": "file"},
                {"id": "folder", "label": "Folder", "caption": "open", "position": [420, 150], "size": [150, 72], "role": "tool", "icon": "folder"},
                {"id": "api", "label": "API", "caption": "ping", "position": [595, 150], "size": [150, 72], "role": "process", "icon": "api"},
                {"id": "cloud", "label": "Cloud", "caption": "upload", "position": [770, 150], "size": [150, 72], "role": "agent", "icon": "cloud"},
                {"id": "search", "label": "Search", "caption": "sweep", "position": [70, 285], "size": [150, 72], "role": "source", "icon": "search"},
                {"id": "shield", "label": "Shield", "caption": "check", "position": [245, 285], "size": [150, 72], "role": "risk", "icon": "shield"},
                {"id": "agent", "label": "Agent", "caption": "orbit", "position": [420, 285], "size": [150, 72], "role": "agent", "icon": "agent"},
                {"id": "tool", "label": "Tool", "caption": "tap", "position": [595, 285], "size": [150, 72], "role": "tool", "icon": "tool"},
                {"id": "output", "label": "Output", "caption": "check", "position": [770, 285], "size": [150, 72], "role": "output", "icon": "output"},
                {"id": "token", "label": "Token", "caption": "pulse", "position": [70, 405], "size": [150, 72], "role": "neutral", "icon": "token"},
            ],
        }
        scene = compile_scene(spec)
        report = quality_report(scene)
        svg = render_svg(scene, load_style(ROOT / "styles" / "minimal-light.json"))

        self.assertEqual("icon-semantic", scene.motion.node_effect.preset)
        self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, report["summary"])
        for motion_id in [
            "database-write",
            "file-lines",
            "folder-open",
            "api-ping",
            "cloud-upload",
            "search-sweep",
            "shield-check",
            "agent-orbit",
            "tool-tap",
            "output-check",
            "token-pulse",
        ]:
            self.assertIn(f'data-icon-motion="{motion_id}"', svg)
            self.assertIn(f"icon-motion-{motion_id}", svg)
        self.assertIn("animateMotion", svg)
        self.assertIn("animateTransform", svg)
        self.assertIn("icon-file-sheet", svg)
        self.assertIn('class="semantic-icon icon-filled semantic-icon-file icon-file-sheet"', svg)
        self.assertIn(".semantic-icon { vector-effect: non-scaling-stroke; }", svg)
        self.assertNotIn(".semantic-icon { fill: none;", svg)
        self.assertNotRegex(svg, r'fill="none"[^>]*fill="#')
        self.assertIn('fill="#a8dde8"', svg)
        self.assertIn("icon-file-page-motion", svg)
        self.assertIn("icon-file-fold-motion", svg)
        self.assertIn("icon-folder-body", svg)
        self.assertIn("icon-database-top-bounce", svg)
        self.assertIn("icon-database-layer-flash", svg)
        self.assertIn("icon-folder-file-line", svg)
        self.assertIn("icon-cloud-dot", svg)
        self.assertIn("icon-search-light", svg)
        self.assertIn("icon-shield-pulse", svg)
        self.assertIn("icon-agent-core", svg)
        self.assertIn("icon-tool-spark", svg)
        self.assertIn("icon-output-line", svg)
        self.assertIn("icon-token-core", svg)
        self.assertIn("icon-token-tick", svg)
        self.assertIn('values="0.78;1.22;1;1"', svg)
        self.assertIn('keyTimes="0;0.08;0.68;1"', svg)
        self.assertIn('dur="1.91s"', svg)
        self.assertIn('values="3 ', svg)
        self.assertIn(';-20 ', svg)
        self.assertIn(';-24 ', svg)
        self.assertIn(';32 ', svg)
        self.assertNotIn('class="node-burst"', svg)
        self.assertNotIn('class="node-glow"', svg)

    def test_icon_surface_fill_is_visible_on_light_nodes(self):
        self.assertEqual("#a8dde8", icon_surface_fill("#ecfeff", "#0891b2"))
        self.assertEqual("#f4b5b5", icon_surface_fill("#fef2f2", "#dc2626"))
        self.assertEqual("#75c5d7", icon_surface_accent("#a8dde8", "#0891b2"))

    def test_motion_policy_limits_semantic_icon_motion(self):
        spec = {
            "version": "0.3",
            "canvas": {"width": 640, "height": 330},
            "title": {"text": "Icon Budget", "subtitle": "one active icon"},
            "motion": {
                "profile": "runtime-loop",
                "node": {"preset": "icon-semantic"},
                "edge": {"preset": "static"},
            },
            "motion_policy": {"profile": "readable", "max_active_pulse_nodes": 1},
            "nodes": [
                {"id": "a", "label": "Database", "caption": "write", "position": [70, 160], "size": [150, 72], "role": "memory", "icon": "database"},
                {"id": "b", "label": "Search", "caption": "sweep", "position": [245, 160], "size": [150, 72], "role": "source", "icon": "search"},
                {"id": "c", "label": "Shield", "caption": "check", "position": [420, 160], "size": [150, 72], "role": "risk", "icon": "shield"},
            ],
        }
        svg = render_svg(compile_scene(spec), load_style(ROOT / "styles" / "minimal-light.json"))

        self.assertEqual(1, svg.count("icon-semantic-motion"))
        self.assertIn('data-icon-motion="database-write"', svg)
        self.assertNotIn('data-icon-motion="search-sweep"', svg)
        self.assertNotIn('data-icon-motion="shield-check"', svg)

    def test_decision_node_shape_renders_as_polygon(self):
        spec = {
            "version": "0.3",
            "canvas": {"width": 500, "height": 320},
            "title": {"text": "Decision", "subtitle": "shape"},
            "motion": {"profile": "teaching"},
            "nodes": [
                {"id": "a", "label": "Check", "caption": "gate", "position": [170, 150], "size": [160, 100], "shape": "decision", "role": "risk"}
            ],
        }
        scene = compile_scene(spec)
        svg = render_svg(scene, load_style(ROOT / "styles" / "minimal-light.json"))

        self.assertEqual("decision", scene.nodes[0].shape)
        self.assertIn("node-decision-shape", svg)
        self.assertIn("<polygon", svg)

    def test_brief_planner_compiles_to_freeform_diagram(self):
        brief = (ROOT / "examples" / "briefs" / "loop-engineering.txt").read_text(encoding="utf-8")
        plan = brief_to_plan(brief)
        spec = compile_plan(plan)
        scene = compile_scene(spec)
        report = quality_report(scene)
        svg = render_svg(scene, load_style(ROOT / "styles" / "sketch-board.json"))

        self.assertEqual("0.1", plan["version"])
        self.assertEqual("explainer-board", plan["layout_strategy"])
        self.assertEqual("brief-explainer", scene.preset)
        self.assertEqual("0.3", scene.version)
        self.assertEqual({"nodes": 18, "edges": 14, "groups": 5}, scene.stats())
        self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, report["summary"])
        self.assertIn("node-decision-shape", svg)
        self.assertIn("edge-arrow-particle", svg)
        self.assertLessEqual(svg.count('class="edge-particle edge-arrow-particle"'), 3)
        self.assertIn("edge-flow-dynamic-dash", svg)

    def test_cli_compiles_brief_to_plan_spec_and_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "loop.plan.json"
            spec_path = Path(tmp) / "loop.diagram.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(
                    [
                        "--brief",
                        str(ROOT / "examples" / "briefs" / "loop-engineering.txt"),
                        "--style",
                        str(ROOT / "styles" / "sketch-board.json"),
                        "--outdir",
                        tmp,
                        "--basename",
                        "loop",
                        "--formats",
                        "svg,quality",
                        "--plan-out",
                        str(plan_path),
                        "--spec-out",
                        str(spec_path),
                    ]
                )

            result = json.loads(stdout.getvalue())
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            spec = json.loads(spec_path.read_text(encoding="utf-8"))

            self.assertTrue(result["ok"])
            self.assertEqual("brief", result["source"])
            self.assertEqual({"name": "DiagramPlan", "version": "0.1"}, result["plan"]["schema"])
            self.assertEqual("explainer-board", plan["layout_strategy"])
            self.assertEqual("0.3", spec["version"])
            self.assertTrue(Path(result["outputs"]["svg"]["path"]).is_file())
            self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, result["outputs"]["quality"]["summary"])

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
