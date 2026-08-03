import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from anidiagram.quality import quality_report
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style
from render_readme_showcase_round_1 import CASES, _validate_reused_webp, build_specs, render_round


class ReadmeShowcaseRound1Test(unittest.TestCase):
    def setUp(self):
        self.specs = build_specs()

    def test_round_has_three_heroes_three_template_proofs_and_two_layout_proofs(self):
        self.assertEqual(
            [
                "hero-loop-engineering",
                "hero-governed-rag",
                "hero-kubernetes-three-layer",
                "template-agent-lifecycle-minimal-light",
                "template-agent-lifecycle-deep-tech",
                "template-agent-lifecycle-claude-warm",
                "layout-enterprise-rag-pipeline",
                "layout-mcp-tool-hub",
            ],
            [case["id"] for case in CASES],
        )
        self.assertEqual({case["id"] for case in CASES}, set(self.specs))
        self.assertEqual(3, sum(case["kind"] == "hero" for case in CASES))
        self.assertEqual(3, sum(case["kind"] == "template" for case in CASES))
        self.assertEqual(2, sum(case["kind"] == "layout" for case in CASES))

    def test_specs_use_readme_canvas_current_systems_and_showcase_motion(self):
        for case in CASES:
            with self.subTest(case=case["id"]):
                spec = self.specs[case["id"]]
                expected_canvas = (
                    {"width": 1020, "height": 920}
                    if case["id"] == "hero-loop-engineering"
                    else {"width": 1600, "height": 900}
                )
                self.assertEqual(expected_canvas, spec["canvas"])
                self.assertEqual("composition-v1", spec["composition_policy"])
                self.assertEqual("showcase-v1", spec["motion"]["profile"])
                self.assertEqual("showcase-v1", spec["resolved_presentation"]["motion"]["value"])
                self.assertTrue(all(edge.get("animated", True) for edge in spec["edges"]))
                self.assertTrue(all(edge.get("effect", {}).get("preset") for edge in spec["edges"]))
                self.assertEqual(case["icon_system"], spec["icon_system"])
                scene = compile_scene(spec)
                style = load_style(ROOT / "styles" / f'{spec["style"]}.json')
                self.assertEqual(
                    {"errors": 0, "warnings": 0, "issues": 0},
                    quality_report(scene, style)["summary"],
                )

    def test_template_comparison_changes_only_the_style_axis(self):
        template_ids = [case["id"] for case in CASES if case["kind"] == "template"]
        normalized = []
        for case_id in template_ids:
            spec = deepcopy(self.specs[case_id])
            spec["style"] = "comparison-style"
            spec["resolved_presentation"]["style"]["value"] = "comparison-style"
            normalized.append(spec)
        self.assertTrue(all(spec == normalized[0] for spec in normalized[1:]))
        self.assertEqual(
            ["minimal-light", "deep-tech", "claude-warm"],
            [self.specs[case_id]["style"] for case_id in template_ids],
        )

    def test_layout_proofs_hold_system_theme_and_motion_constant(self):
        layout_cases = [case for case in CASES if case["kind"] == "layout"]
        self.assertEqual(["pipeline", "hub-spoke"], [case["layout"] for case in layout_cases])
        for case in layout_cases:
            spec = self.specs[case["id"]]
            self.assertEqual("diagram-core-v1", spec["icon_system"])
            self.assertEqual("minimal-light", spec["style"])
            self.assertEqual(case["layout"], spec["layout"])

    def test_kubernetes_hero_has_three_explicit_vertical_layers(self):
        spec = self.specs["hero-kubernetes-three-layer"]
        self.assertEqual("Kubernetes Production Architecture", spec["title"]["text"])
        self.assertEqual("diagram-core-v1", spec["icon_system"])
        self.assertEqual("deep-tech", spec["style"])
        self.assertEqual("layered", spec["layout"])
        self.assertEqual(
            ["Traffic & Operations", "Kubernetes Control Plane", "Runtime & Reliability"],
            [group["label"] for group in spec["groups"]],
        )
        self.assertEqual(sorted(group["bounds"][1] for group in spec["groups"]), [145, 350, 570])
        for node in spec["nodes"]:
            x, y = node["position"]
            width, height = node["size"]
            self.assertTrue(
                any(
                    x >= gx and y >= gy and x + width <= gx + gw and y + height <= gy + gh
                    for gx, gy, gw, gh in (group["bounds"] for group in spec["groups"])
                ),
                node["id"],
            )

    def test_loop_engineering_is_the_first_layered_loop_hero(self):
        spec = self.specs["hero-loop-engineering"]
        self.assertEqual("hero-loop-engineering", CASES[0]["id"])
        self.assertEqual("Loop Engineering Operating Architecture", spec["title"]["text"])
        self.assertEqual("layered-loop", spec["layout"])
        self.assertEqual("minimal-light", spec["style"])
        self.assertEqual("illustrated", spec["icon_system"])
        self.assertEqual({"nodes": 8, "edges": 8, "groups": 3}, compile_scene(spec).stats())

    def test_renderer_writes_eight_complete_readme_bundles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = render_round(root / "specs", root / "outputs")
            self.assertEqual(8, result["case_count"])
            self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, result["quality_summary"])
            manifest = json.loads((root / "outputs" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("approved", manifest["status"])
            self.assertTrue(manifest["readme_mutated"])
            self.assertEqual("per-case", manifest["canvas_policy"])
            self.assertNotIn("canvas", manifest)
            self.assertEqual(8, len(manifest["cases"]))
            for case in manifest["cases"]:
                for key in ("spec", "preview", "svg", "html", "quality"):
                    self.assertTrue((root / case[key]).is_file(), case[key])
            review = (root / "outputs" / "readme-showcase-round-1.html").read_text(encoding="utf-8")
            self.assertEqual(8, review.count("<article"))
            self.assertEqual(8, review.count("<img "))
            self.assertIn("README Showcase · Round 1", review)
            self.assertIn("Eight approved showcase cases", review)

    def test_renderer_exports_readme_webp_with_the_browser_capture_contract(self):
        captures = []

        def fake_capture(scene, style, path, format_name, **options):
            path.write_bytes(b"RIFF-test-WEBP")
            captures.append((scene.title.text, format_name, options))
            return {
                "status": "written",
                "path": str(path),
                "renderer": "browser",
                "fps": options["fps"],
                "frames": options["frames"],
                "scale": options["scale"],
                "loop_blend_frames": options["loop_blend_frames"],
                "quality": options["quality"],
                "runtime_dependency": "gsap@3.15.0",
                "capture_contract": "browser-capture-v1",
                "input_sha256": "fake-input-hash",
            }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("render_readme_showcase_round_1.write_browser_capture", side_effect=fake_capture):
                render_round(root / "specs", root / "outputs", export_webp=True)

            self.assertEqual(8, len(captures))
            for _title, format_name, options in captures:
                self.assertEqual("webp", format_name)
                self.assertEqual("gsap", options["runtime"])
                self.assertEqual(12, options["fps"])
                self.assertEqual(24, options["frames"])
                self.assertEqual(1.0, options["scale"])
                self.assertEqual(4, options["loop_blend_frames"])
                self.assertEqual(65, options["quality"])

            manifest = json.loads((root / "outputs" / "manifest.json").read_text(encoding="utf-8"))
            for case in manifest["cases"]:
                self.assertTrue((root / case["webp"]).is_file(), case["webp"])
                self.assertEqual(
                    {
                        "renderer": "browser",
                        "fps": 12,
                        "frames": 24,
                        "scale": 1.0,
                        "loop_blend_frames": 4,
                        "quality": 65,
                        "runtime_dependency": "gsap@3.15.0",
                        "capture_contract": "browser-capture-v1",
                        "input_sha256": "fake-input-hash",
                    },
                    case["webp_capture"],
                )
            review = (root / "outputs" / "readme-showcase-round-1.html").read_text(encoding="utf-8")
            self.assertEqual(8, review.count("Animated WebP preview of"))
            self.assertEqual(8, review.count('.webp"'))
            self.assertNotIn('.preview.svg" alt="Static preview', review)

    def test_renderer_reuses_committed_webp_without_recapturing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "canonical"
            outdir = root / "outputs"
            source_dir.mkdir()
            outdir.mkdir()
            for case in CASES:
                (source_dir / f'{case["id"]}.webp').write_bytes(
                    f'RIFF-{case["id"]}-WEBP'.encode()
                )
            (source_dir / "manifest.json").write_text(
                json.dumps({"cases": [
                    {
                        "id": case["id"],
                        "webp_capture": {
                            "renderer": "browser", "fps": 12, "frames": 24, "scale": 1.0,
                            "loop_blend_frames": 4, "quality": 65, "runtime_dependency": "gsap@3.15.0",
                            "capture_contract": "browser-capture-v1",
                            "input_sha256": "fake-input-hash",
                        },
                    }
                    for case in CASES
                ]}),
                encoding="utf-8",
            )

            with patch("render_readme_showcase_round_1.write_browser_capture") as capture, \
                 patch("render_readme_showcase_round_1._validate_reused_webp"), \
                 patch("render_readme_showcase_round_1.webp_browser_capture_input_sha256", return_value="fake-input-hash"):
                render_round(
                    root / "specs",
                    outdir,
                    reuse_webp=True,
                    webp_source_dir=source_dir,
                )

            capture.assert_not_called()
            for case in CASES:
                self.assertEqual(
                    (source_dir / f'{case["id"]}.webp').read_bytes(),
                    (outdir / f'{case["id"]}.webp').read_bytes(),
                )
            manifest = json.loads((outdir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(8, len(manifest["cases"]))
            self.assertTrue(all(case["webp_capture"]["runtime_dependency"] == "gsap@3.15.0" for case in manifest["cases"]))
            review = (outdir / "readme-showcase-round-1.html").read_text(encoding="utf-8")
            self.assertEqual(8, review.count("Animated WebP preview of"))

    def test_reused_webp_validation_rejects_invalid_media(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.webp"
            path.write_bytes(b"not-a-webp")
            with self.assertRaisesRegex(RuntimeError, "invalid"):
                _validate_reused_webp(path, {"width": 1600, "height": 900})

    def test_browser_runtime_has_no_overflow_or_inactive_edges(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            render_round(root / "specs", root / "outputs")
            result = subprocess.run(
                [
                    "node",
                    str(ROOT / "scripts" / "verify_readme_showcase_round_1.mjs"),
                    str(root / "outputs"),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr or result.stdout)
            report = json.loads(result.stdout)
            self.assertEqual(8, report["cases"])
            self.assertEqual(70, report["nodes"])
            self.assertEqual(66, report["edges"])
            self.assertEqual(66, report["active_runtime_edges"])
            self.assertEqual(0, report["animated_webp_previews"])
            self.assertEqual([], report["console_errors"])
            self.assertEqual([], report["overflow"])
            self.assertEqual([], report["text_overflow"])
            self.assertEqual([], report["title_text_overflow"])
            self.assertEqual([], report["label_collisions"])


if __name__ == "__main__":
    unittest.main()
