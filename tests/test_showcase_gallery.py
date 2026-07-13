import json
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from anidiagram.quality import quality_report
from anidiagram.schema import compile_scene
from anidiagram.motion_manifest import CHARACTER_ICON_PERFORMANCES, CHARACTER_REST_AT
from anidiagram.illustrated_character_icons import character_definition
from anidiagram.renderer_svg import render_svg
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_showcase import LAYOUT_CASES, layout_showcase_specs, load_runtime_motion_catalog


class _LocalAssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key in ("href", "src"):
            if values.get(key):
                self.references.append(values[key])


class ShowcaseGalleryTest(unittest.TestCase):
    def test_representative_examples_use_default_character_icons_and_readable_budgets(self):
        targets = (
            ROOT / "examples" / "agent-memory.diagram.json",
            ROOT / "examples" / "high-fidelity-runtime.diagram.json",
            ROOT / "outputs" / "loop-engineering-architecture" / "loop-engineering-architecture.diagram.json",
            ROOT / "examples" / "showcase" / "layouts" / "pipeline-rag-ingestion-pipeline.diagram.json",
            ROOT / "examples" / "showcase" / "layouts" / "layered-llm-app-architecture-layers.diagram.json",
            ROOT / "examples" / "showcase" / "layouts" / "sequence-api-tool-calling-sequence.diagram.json",
        )
        for path in targets:
            with self.subTest(path=path.name):
                source = path.read_text(encoding="utf-8")
                spec = json.loads(source)
                scene = compile_scene(spec)
                style = load_style(ROOT / "styles" / f"{spec.get('style', 'minimal-light')}.json")
                self.assertTrue(all(node.icon for node in scene.nodes), path)
                self.assertNotIn('"icon_motion":', source, path)
                self.assertIn('data-icon-system="illustrated-character-v1"', render_svg(scene, style), path)
                self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, quality_report(scene, style)["summary"], path)
                if len(scene.nodes) >= 6:
                    self.assertIn(scene.motion_policy.profile, {"focused", "readable", "readable-runtime"}, path)
                self.assertNotIn(scene.motion.group, {"border-scan", "marching-ants"}, path)

    def test_gallery_quality_writers_pass_the_resolved_style(self):
        for relative in ("scripts/build_showcase.py", "scripts/build_style_showcase.py", "scripts/batch_render.py"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("write_quality(scene, quality_path)", source, relative)
            self.assertNotIn("write_quality(scene, outdir /", source, relative)
            self.assertIn("write_quality(scene, style,", source, relative)

    def test_character_motion_catalog_freezes_v1_and_keeps_legacy_explicit(self):
        catalog = load_runtime_motion_catalog()
        character_entries = catalog["character_performances"]
        legacy_entries = catalog["performances"]

        self.assertEqual(set(CHARACTER_ICON_PERFORMANCES.values()), {entry["id"] for entry in character_entries})
        self.assertEqual("illustrated-character-v1", catalog["default_runtime"]["icon_system"])
        self.assertEqual("motion-coordination-v1.1", catalog["default_runtime"]["motion_contract"])
        self.assertEqual(
            {"source": "scene.motion.stagger", "minimum": 0.08, "mode": "per-icon-delay"},
            catalog["default_runtime"]["stagger_contract"],
        )
        for entry in character_entries:
            icon = entry["icon"]
            self.assertEqual("illustrated-character-v1", entry["icon_system"])
            self.assertEqual(list(character_definition(icon).parts), entry["parts"])
            self.assertEqual(CHARACTER_REST_AT[icon], entry["rest_at"])
            self.assertEqual(0.8, entry["repeat_delay"])
            self.assertEqual({"duration": 0.44, "scale": 1.012}, entry["idle_breathe"])
        self.assertTrue(all(entry["icon_system"] == "semantic-line-v1" for entry in legacy_entries))

    def test_character_theme_catalog_and_comparison_surface_are_complete(self):
        style_catalog = json.loads((ROOT / "styles" / "catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(
            ["illustrated-character", "deep-tech", "teaching-sketch-character"],
            style_catalog["character_themes"],
        )
        manifest = json.loads((ROOT / "gallery" / "showcase_manifest.json").read_text(encoding="utf-8"))
        comparison = manifest["character_theme_comparison"]
        self.assertEqual("gallery/character-themes.html", comparison["page"])
        self.assertEqual(style_catalog["character_themes"], [entry["style"] for entry in comparison["themes"]])
        self.assertTrue((ROOT / comparison["page"]).is_file())
        for entry in comparison["themes"]:
            for key in ("svg", "html", "webp", "quality"):
                self.assertTrue((ROOT / entry[key]).is_file(), entry[key])
            summary = json.loads((ROOT / entry["quality"]).read_text(encoding="utf-8"))["summary"]
            self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, summary)

        compatibility = (ROOT / "docs" / "illustrated-character-theme-compatibility.md").read_text(encoding="utf-8")
        for style in ("minimal-light", "dark-luxury", "blueprint", "claude-warm", "aurora-orb"):
            self.assertIn(f"`{style}`", compatibility)
        self.assertIn("Pass", compatibility)
        self.assertIn("Tune", compatibility)
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
        catalog = load_runtime_motion_catalog()

        self.assertEqual("Agent Runtime Flow", manifest["hero"]["title"])
        self.assertEqual(12, len(manifest["styles"]))
        self.assertEqual(14, len(manifest["layouts"]))
        self.assertEqual("runtime/motion-catalog.json", manifest["runtime_motion_catalog"])
        self.assertEqual("gallery/runtime-motion.html", manifest["runtime_motion_page"])
        self.assertEqual("illustrated-character-v1", manifest["hero"]["icon_system"])
        self.assertTrue(all(entry["icon_system"] == "illustrated-character-v1" for entry in manifest["styles"]))
        self.assertTrue(all(entry["icon_system"] == "illustrated-character-v1" for entry in manifest["layouts"]))
        self.assertEqual("semantic-line-v1", manifest["runtime_motion_overview"]["icon_system"])
        self.assertTrue((ROOT / manifest["runtime_motion_page"]).is_file())
        self.assertTrue((ROOT / manifest["runtime_motion_overview"]["html"]).is_file())
        self.assertTrue((ROOT / manifest["runtime_motion_overview"]["quality"]).is_file())
        self.assertEqual(27, len(manifest["runtime_motion_demos"]))
        self.assertEqual(
            [
                "runtime-edge-packet-flow",
                "runtime-title-sweep",
                "agent-think-act-v2",
                "search-discover-v2",
                "api-request-response-v2",
                "database-write-v2",
                "memory-commit-v2",
                "tool-run-v2",
                "token-intent-v2",
                "output-reveal-v2",
                "file-lines-v2",
                "folder-open-v2",
                "cloud-upload-v2",
                "shield-check-v2",
            ],
            [entry["id"] for entry in manifest["runtime_motion_demos"] if entry["kind"] != "icon-performance-character"],
        )
        for entry in manifest["runtime_motion_demos"]:
            with self.subTest(runtime_motion_demo=entry["id"]):
                for key in ("spec", "svg", "html", "quality"):
                    self.assertTrue((ROOT / entry[key]).is_file(), entry[key])
                self.assertGreaterEqual(len(entry["phases"]), 1)
                summary = json.loads((ROOT / entry["quality"]).read_text(encoding="utf-8"))["summary"]
                self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, summary)
        self.assertTrue(catalog["change_control"]["requires_confirmation"])
        self.assertEqual(
            [entry["id"] for entry in [*catalog["character_performances"], *catalog["performances"]]],
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

    def test_gallery_pages_have_no_broken_local_asset_links(self):
        for page in (ROOT / "gallery").rglob("*.html"):
            parser = _LocalAssetParser()
            parser.feed(page.read_text(encoding="utf-8"))
            for reference in parser.references:
                parsed = urlsplit(reference)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                with self.subTest(page=page.relative_to(ROOT), reference=reference):
                    self.assertTrue((page.parent / parsed.path).resolve().is_file())

    def test_documentation_states_character_defaults_modes_and_verifiers(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        diagram_script = (ROOT / "docs" / "diagram-script.md").read_text(encoding="utf-8")
        html_runtime = (ROOT / "docs" / "html-runtime.md").read_text(encoding="utf-8")

        for source in (readme, readme_zh, diagram_script):
            self.assertIn("illustrated-character-v1", source)
            self.assertIn("illustrated-v1", source)
            self.assertIn("semantic-line-v1", source)
        for source in (readme, readme_zh, html_runtime):
            self.assertIn("Expressive", source)
            self.assertIn("Readable", source)
            self.assertIn("Off", source)
            self.assertIn("0.7", source)
            self.assertIn("gallery/character-themes.html", source)
        self.assertIn("node scripts/verify_stage_motion_modes.mjs", html_runtime)
        self.assertIn("prefers-reduced-motion: reduce", html_runtime)


if __name__ == "__main__":
    unittest.main()
