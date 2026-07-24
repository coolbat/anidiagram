import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from anidiagram.quality import quality_report
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style
from render_readme_showcase_round_1 import CASES, build_specs, render_round


class ReadmeShowcaseRound1Test(unittest.TestCase):
    def setUp(self):
        self.specs = build_specs()

    def test_round_has_one_hero_three_template_proofs_and_two_layout_proofs(self):
        self.assertEqual(
            [
                "hero-governed-rag",
                "template-agent-lifecycle-minimal-light",
                "template-agent-lifecycle-deep-tech",
                "template-agent-lifecycle-claude-warm",
                "layout-enterprise-rag-pipeline",
                "layout-mcp-tool-hub",
            ],
            [case["id"] for case in CASES],
        )
        self.assertEqual({case["id"] for case in CASES}, set(self.specs))
        self.assertEqual(1, sum(case["kind"] == "hero" for case in CASES))
        self.assertEqual(3, sum(case["kind"] == "template" for case in CASES))
        self.assertEqual(2, sum(case["kind"] == "layout" for case in CASES))

    def test_specs_use_readme_canvas_current_systems_and_showcase_motion(self):
        for case in CASES:
            with self.subTest(case=case["id"]):
                spec = self.specs[case["id"]]
                self.assertEqual({"width": 1600, "height": 900}, spec["canvas"])
                self.assertEqual("composition-v1", spec["composition_policy"])
                self.assertEqual("showcase-v1", spec["motion"]["profile"])
                self.assertEqual("showcase-v1", spec["resolved_presentation"]["motion"]["value"])
                self.assertTrue(all(edge.get("animated", True) for edge in spec["edges"]))
                self.assertTrue(all(edge.get("effect", {}).get("preset") for edge in spec["edges"]))
                self.assertEqual(
                    "illustrated" if case["kind"] in {"hero", "template"} else "diagram-core-v1",
                    spec["icon_system"],
                )
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

    def test_renderer_writes_six_complete_review_bundles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = render_round(root / "specs", root / "outputs")
            self.assertEqual(6, result["case_count"])
            self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, result["quality_summary"])
            manifest = json.loads((root / "outputs" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(6, len(manifest["cases"]))
            for case in manifest["cases"]:
                for key in ("spec", "preview", "svg", "html", "quality"):
                    self.assertTrue((root / case[key]).is_file(), case[key])
            review = (root / "outputs" / "readme-showcase-round-1.html").read_text(encoding="utf-8")
            self.assertEqual(6, review.count("<article"))
            self.assertEqual(6, review.count("<img "))
            self.assertIn("README Showcase · Round 1", review)

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
            self.assertEqual(6, report["cases"])
            self.assertEqual(50, report["nodes"])
            self.assertEqual(47, report["edges"])
            self.assertEqual(47, report["active_runtime_edges"])
            self.assertEqual([], report["console_errors"])
            self.assertEqual([], report["overflow"])


if __name__ == "__main__":
    unittest.main()
