import json
import sys
import unittest
from pathlib import Path

from anidiagram.quality import quality_report
from anidiagram.schema import compile_scene


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_showcase import LAYOUT_CASES, layout_showcase_specs


class ShowcaseGalleryTest(unittest.TestCase):
    def test_layout_showcase_specs_cover_all_cases_with_clean_quality(self):
        specs = layout_showcase_specs()
        expected = [case[0] for case in LAYOUT_CASES]

        self.assertEqual(expected, list(specs))
        for preset, spec in specs.items():
            with self.subTest(preset=preset):
                scene = compile_scene(spec)
                self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, quality_report(scene)["summary"])

    def test_showcase_manifest_points_to_generated_assets(self):
        manifest_path = ROOT / "gallery" / "showcase_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual("Agent Runtime Flow", manifest["hero"]["title"])
        self.assertEqual(12, len(manifest["styles"]))
        self.assertEqual(14, len(manifest["layouts"]))
        self.assertEqual(
            [
                "agent-think-act-v2",
                "search-discover-v2",
                "api-request-response-v2",
                "database-write-v2",
            ],
            [entry["id"] for entry in manifest["runtime_motion"]],
        )
        self.assertIn("MCP Server Architecture", [entry["title"] for entry in manifest["styles"]])
        self.assertIn("AI Growth Funnel", [entry["title"] for entry in manifest["styles"]])
        self.assertIn("RAG Ingestion Pipeline", [entry["title"] for entry in manifest["layouts"]])
        self.assertIn("Personalized Agent Memory Flow", [entry["title"] for entry in manifest["layouts"]])

        entries = [manifest["hero"], *manifest["styles"], *manifest["layouts"]]
        for entry in entries:
            with self.subTest(entry=entry["title"]):
                for key in ("spec", "svg", "html", "quality"):
                    self.assertTrue((ROOT / entry[key]).is_file(), entry[key])
                summary = json.loads((ROOT / entry["quality"]).read_text(encoding="utf-8"))["summary"]
                self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, summary)


if __name__ == "__main__":
    unittest.main()
