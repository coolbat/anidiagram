import json
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

try:
    from PIL import Image
except ImportError:  # pragma: no cover - exercised by the base install contract
    Image = None

from anidiagram.quality import quality_report
from quality_expectations import assert_quality_baseline
from anidiagram.schema import compile_scene
from anidiagram.motion_manifest import CHARACTER_ICON_PERFORMANCES, CHARACTER_REST_AT, build_motion_manifest
from anidiagram.edge_motion import canonical_edge_motion
from anidiagram.illustrated_character_icons import character_definition
from anidiagram.renderer_svg import node_box, render_svg, route_points
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_showcase import LAYOUT_CASES, layout_showcase_specs, load_runtime_motion_catalog
from build_style_showcase import apply_public_showcase_contract, style_showcase_specs


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
    def test_kubernetes_hero_candidate_has_three_planes_and_focused_motion(self):
        spec_path = ROOT / "examples" / "kubernetes-production-cluster.diagram.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        style = load_style(ROOT / "styles" / "deep-tech.json")

        self.assertEqual((1280, 740), (scene.canvas.width, scene.canvas.height))
        self.assertGreaterEqual(len(scene.nodes), 16)
        self.assertGreaterEqual(len(scene.groups), 6)
        self.assertTrue({"access", "control-plane", "workload-plane"}.issubset({group.group_id for group in scene.groups}))
        self.assertTrue({"api-server", "scheduler", "controllers", "etcd", "kubelet-a", "pod-a", "kubelet-b", "pod-b"}.issubset({node.node_id for node in scene.nodes}))
        self.assertEqual("focused", scene.motion_policy.profile)
        assert_quality_baseline(self, quality_report(scene, style))
        self.assertIn('data-icon-system="illustrated-character-v1"', render_svg(scene, style))

        manifest = build_motion_manifest(scene, style)
        self.assertEqual([1, 3, 5, 8], manifest["stage"]["active_edge_indices"])
        self.assertEqual([1, 3], manifest["stage"]["readable_edge_indices"])
        self.assertEqual(
            ["kubectl->api-server", "ingress->service", "api-server->scheduler", "api-server->kubelet-a"],
            [
                f'{manifest["edges"][index]["source"]}->{manifest["edges"][index]["target"]}'
                for index in manifest["stage"]["active_edge_indices"]
            ],
        )
        self.assertTrue(all(manifest["edges"][index]["animated"] for index in manifest["stage"]["active_edge_indices"]))
        self.assertTrue(all(manifest["edges"][index]["effect"] == "signal-arrow" for index in manifest["stage"]["active_edge_indices"]))

    def test_kubernetes_hero_routes_have_visible_shafts_and_no_shared_segments(self):
        spec = json.loads((ROOT / "examples" / "kubernetes-production-cluster.diagram.json").read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        boxes = {node.node_id: node_box(node) for node in scene.nodes}
        segments = []
        short_edges = []

        for edge_index, edge in enumerate(scene.edges):
            points = route_points(edge, boxes)
            length = sum(((right[0] - left[0]) ** 2 + (right[1] - left[1]) ** 2) ** 0.5 for left, right in zip(points, points[1:]))
            if length < 24:
                short_edges.append(f"{edge.source}->{edge.target}:{length:.1f}")
            for segment_index, (left, right) in enumerate(zip(points, points[1:])):
                if abs(left[1] - right[1]) < 0.01:
                    segments.append((edge_index, segment_index, "h", left[1], *sorted((left[0], right[0]))))
                elif abs(left[0] - right[0]) < 0.01:
                    segments.append((edge_index, segment_index, "v", left[0], *sorted((left[1], right[1]))))

        overlaps = []
        for index, left in enumerate(segments):
            for right in segments[index + 1:]:
                if left[0] == right[0] or left[2] != right[2] or abs(left[3] - right[3]) >= 0.01:
                    continue
                overlap = min(left[5], right[5]) - max(left[4], right[4])
                if overlap > 1:
                    left_edge = scene.edges[left[0]]
                    right_edge = scene.edges[right[0]]
                    overlaps.append(f"{left_edge.source}->{left_edge.target} / {right_edge.source}->{right_edge.target}:{overlap:.1f}")

        self.assertEqual([], short_edges)
        self.assertEqual([], overlaps)

    def test_hero_uses_a_focal_agent_and_complete_runtime_story(self):
        spec_path = ROOT / "examples" / "high-fidelity-runtime.diagram.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        style = load_style(ROOT / "styles" / "deep-tech.json")
        agent = next(node for node in scene.nodes if node.node_id == "agent")
        satellites = [node for node in scene.nodes if node.node_id != "agent"]

        self.assertGreaterEqual(len(scene.nodes), 8)
        self.assertGreaterEqual(len(scene.groups), 3)
        self.assertGreater(agent.size[0] * agent.size[1], max(node.size[0] * node.size[1] for node in satellites))
        self.assertTrue({"token", "agent", "search", "tool", "api", "shield", "memory", "output"}.issubset({node.icon for node in scene.nodes}))
        self.assertEqual("focused", scene.motion_policy.profile)
        assert_quality_baseline(self, quality_report(scene, style))

        capture_docs = (ROOT / "docs" / "html-runtime.md").read_text(encoding="utf-8")
        readme_command = capture_docs.split("For a README hero preview", 1)[1].split("Use the animated WebP", 1)[0]
        self.assertIn("--export-fps 12", readme_command)
        self.assertIn("--export-frames 24", readme_command)
        self.assertIn("--export-loop-blend-frames 4", readme_command)
        self.assertIn("--export-quality 65", readme_command)

    def test_representative_examples_use_default_character_icons_and_readable_budgets(self):
        targets = (
            ROOT / "examples" / "agent-memory.diagram.json",
            ROOT / "examples" / "high-fidelity-runtime.diagram.json",
            ROOT / "examples" / "illustrated-character-strong-loop-cases.diagram.json",
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
                assert_quality_baseline(self, quality_report(scene, style), path.name)
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
        self.assertEqual("motion-coordination-v2", catalog["default_runtime"]["motion_contract"])
        self.assertEqual(
            {"source": "4-second global beat", "mode": "aligned-cycle", "long_paths": "integer multiples of the common cycle"},
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
            for key in ("svg", "html", "preview", "quality"):
                self.assertTrue((ROOT / entry[key]).is_file(), entry[key])
            self.assertEqual(entry["svg"], entry["preview"])
            self.assertNotIn("webp", entry)
            summary = json.loads((ROOT / entry["quality"]).read_text(encoding="utf-8"))["summary"]
            self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, summary)

        compatibility = (ROOT / "docs" / "illustrated-character-theme-compatibility.md").read_text(encoding="utf-8")
        for style in ("minimal-light", "dark-luxury", "blueprint", "claude-warm", "aurora-orb"):
            self.assertIn(f"`{style}`", compatibility)
        self.assertIn("Pass", compatibility)
        self.assertIn("Tune", compatibility)
    def test_layout_showcase_specs_cover_all_cases_with_known_diagnostics(self):
        specs = layout_showcase_specs()
        expected = [case[0] for case in LAYOUT_CASES]

        self.assertEqual(expected, list(specs))
        for preset, spec in specs.items():
            with self.subTest(preset=preset):
                scene = compile_scene(spec)
                assert_quality_baseline(self, quality_report(scene), preset)

    def test_public_showcase_specs_use_composition_v1_illustrated_2_5_and_full_motion(self):
        hero_source = json.loads((ROOT / "examples" / "high-fidelity-runtime.diagram.json").read_text(encoding="utf-8"))
        collections = {
            "hero": {"agent-runtime-flow": apply_public_showcase_contract(hero_source, layout="layered")},
            "styles": style_showcase_specs(),
            "layouts": {
                preset: spec
                for preset, spec in layout_showcase_specs().items()
                if preset not in {"agent-loop", "layered-loop"}
            },
        }

        for collection, specs in collections.items():
            expected_count = {"hero": 1, "styles": 13, "layouts": 14}[collection]
            self.assertEqual(expected_count, len(specs), collection)
            for name, spec in specs.items():
                with self.subTest(collection=collection, name=name):
                    self.assertEqual("0.4", spec["version"])
                    self.assertEqual("composition-v1", spec["composition_policy"])
                    self.assertEqual("illustrated", spec["icon_system"])
                    self.assertEqual("2.5.0", spec["resolved_presentation"]["icon_system"]["version"])
                    self.assertEqual("illustrated", spec["resolved_presentation"]["icon_system"]["value"])
                    self.assertEqual("showcase-v1", spec["resolved_presentation"]["motion"]["value"])
                    self.assertEqual("showcase-v1", spec["motion"]["profile"])
                    self.assertEqual("unrestricted", spec["motion_policy"]["profile"])
                    self.assertGreaterEqual(spec["canvas"]["width"], 1400)
                    self.assertTrue(all(node["size"][0] >= 240 for node in spec["nodes"]))
                    self.assertTrue(all(edge.get("animated") is True for edge in spec["edges"]))
                    self.assertTrue(
                        all(
                            canonical_edge_motion(edge["effect"]["preset"])
                            in {"packet-flow", "comet-flow", "stream-flow"}
                            for edge in spec["edges"]
                        )
                    )

                    scene = compile_scene(spec)
                    style = load_style(ROOT / "styles" / f'{spec["style"]}.json')
                    manifest = build_motion_manifest(scene, style)
                    self.assertEqual(list(range(len(scene.edges))), manifest["stage"]["active_edge_indices"])
                    assert_quality_baseline(self, quality_report(scene, style), f"{collection}/{name}")

        agent_loop = layout_showcase_specs()["agent-loop"]
        self.assertEqual("composition-v1", agent_loop["composition_policy"])
        self.assertEqual("illustrated", agent_loop["icon_system"])
        self.assertEqual("2.5.0", agent_loop["resolved_presentation"]["icon_system"]["version"])
        self.assertEqual("showcase-v1", agent_loop["motion"]["profile"])
        layered_loop = layout_showcase_specs()["layered-loop"]
        self.assertEqual("composition-v1", layered_loop["composition_policy"])
        self.assertEqual("illustrated", layered_loop["icon_system"])
        self.assertEqual("2.5.0", layered_loop["resolved_presentation"]["icon_system"]["version"])
        self.assertEqual("showcase-v1", layered_loop["motion"]["profile"])

    def test_showcase_manifest_points_to_generated_assets(self):
        manifest_path = ROOT / "gallery" / "showcase_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        catalog = load_runtime_motion_catalog()

        self.assertEqual("Dify · From Document to Answer", manifest["hero"]["title"])
        self.assertEqual(13, len(manifest["styles"]))
        self.assertEqual(16, len(manifest["layouts"]))
        self.assertEqual("runtime/motion-catalog.json", manifest["runtime_motion_catalog"])
        self.assertEqual("gallery/runtime-motion.html", manifest["runtime_motion_page"])
        self.assertEqual(
            {
                "status": "approved",
                "case_count": 8,
                "review_page": "gallery/readme-showcase/readme-showcase-round-1.html",
                "manifest": "gallery/readme-showcase/manifest.json",
            },
            manifest["readme_showcase"],
        )
        self.assertEqual("illustrated", manifest["hero"]["icon_system"])
        self.assertTrue(all(entry["icon_system"] == "illustrated" for entry in manifest["styles"]))
        self.assertTrue(all(entry["icon_system"] == "illustrated" for entry in manifest["layouts"]))
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
        self.assertIn("Agent Loop Runtime Architecture", [entry["title"] for entry in manifest["layouts"]])
        self.assertIn("Loop Engineering Operating Architecture", [entry["title"] for entry in manifest["layouts"]])

        entries = [manifest["hero"], *manifest["styles"], *manifest["layouts"]]
        for entry in entries:
            with self.subTest(entry=entry["title"]):
                for key in ("spec", "svg", "html", "quality"):
                    self.assertTrue((ROOT / entry[key]).is_file(), entry[key])
                spec = json.loads((ROOT / entry["spec"]).read_text(encoding="utf-8"))
                self.assertEqual("0.4", spec["version"])
                self.assertEqual("composition-v1", spec["composition_policy"])
                self.assertEqual("illustrated", spec["icon_system"])
                self.assertEqual("2.5.0", spec["resolved_presentation"]["icon_system"]["version"])
                self.assertEqual("showcase-v1", spec["motion"]["profile"])
                for key in ("svg", "html"):
                    rendered = (ROOT / entry[key]).read_text(encoding="utf-8")
                    self.assertIn(f'data-icon-system="{entry["icon_system"]}"', rendered, entry[key])
                    self.assertIn("semantic-icon-illustrated", rendered, entry[key])
                summary = json.loads((ROOT / entry["quality"]).read_text(encoding="utf-8"))["summary"]
                self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, summary)

    def test_readmes_use_one_animated_proof_with_reproducible_live_links(self):
        expected_by_readme = {
            "README.md": {
                "animated": "gallery/readme-showcase/hero-loop-engineering.webp",
                "local_links": [
                    "examples/loop-engineering-minimal-light.plan.json",
                    "examples/readme-showcase-round-1/hero-loop-engineering.diagram.json",
                    "gallery/readme-showcase/hero-loop-engineering.svg",
                    "gallery/readme-showcase/hero-loop-engineering.quality.json",
                ],
                "live": "https://coolbat.github.io/anidiagram/gallery/readme-showcase/hero-loop-engineering.html",
            },
            "README.zh-CN.md": {
                "animated": "assets/readme/enterprise-agent-platform-zh.webp",
                "local_links": [
                    "examples/zh-CN/enterprise-agent-platform.plan.json",
                    "assets/readme/enterprise-agent-platform-zh.svg",
                ],
                "live": "https://coolbat.github.io/anidiagram/gallery/readme-showcase/enterprise-agent-platform-zh.html",
            },
        }
        all_secondary_webps = {
            "gallery/readme-showcase/hero-governed-rag.webp",
            "gallery/readme-showcase/hero-kubernetes-three-layer.webp",
            "gallery/readme-showcase/template-agent-lifecycle-minimal-light.webp",
            "gallery/readme-showcase/template-agent-lifecycle-deep-tech.webp",
            "gallery/readme-showcase/template-agent-lifecycle-claude-warm.webp",
            "gallery/readme-showcase/layout-enterprise-rag-pipeline.webp",
            "gallery/readme-showcase/layout-mcp-tool-hub.webp",
        }
        for relative, expected in expected_by_readme.items():
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(1, len(re.findall(r"\]\(\./[^)]+\.webp\)", source)), relative)
            self.assertIn(f'](./{expected["animated"]})', source)
            self.assertIn(expected["live"], source)
            for path in expected["local_links"]:
                self.assertIn(f'](./{path})', source)
                self.assertTrue((ROOT / path).is_file(), path)
            for path in all_secondary_webps:
                self.assertNotIn(path, source)
            self.assertIn("scripts/render_readme_showcase_round_1.py", source)
        self.assertTrue((ROOT / ".nojekyll").is_file())
        self.assertTrue((ROOT / "gallery" / "readme-showcase" / "enterprise-agent-platform-zh.html").is_file())

    @unittest.skipIf(Image is None, "Pillow is required to inspect animated WebP frames")
    def test_chinese_readme_uses_centered_chinese_animated_proof(self):
        webp_path = ROOT / "assets" / "readme" / "enterprise-agent-platform-zh.webp"
        svg_path = ROOT / "assets" / "readme" / "enterprise-agent-platform-zh.svg"
        self.assertLess(webp_path.stat().st_size, 1024 * 1024)
        with Image.open(webp_path) as image:
            self.assertTrue(getattr(image, "is_animated", False))
            self.assertEqual(24, image.n_frames)
            self.assertEqual((1020, 920), image.size)
        svg = svg_path.read_text(encoding="utf-8")
        self.assertIn('lang="zh-CN"', svg)
        self.assertIn("企业级智能体平台架构", svg)

    def test_readmes_do_not_repeat_clean_room_boundary_declarations(self):
        self.assertNotIn("Clean-room boundary", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertNotIn("Clean-Room 边界", (ROOT / "README.zh-CN.md").read_text(encoding="utf-8"))

    @unittest.skipIf(Image is None, "Pillow is required to inspect animated WebP frames")
    def test_curated_showcase_uses_animated_webp_previews(self):
        manifest = json.loads((ROOT / "gallery" / "readme-showcase" / "manifest.json").read_text(encoding="utf-8"))
        review = (ROOT / "gallery" / "readme-showcase" / "readme-showcase-round-1.html").read_text(encoding="utf-8")
        self.assertEqual(8, len(manifest["cases"]))
        total_bytes = 0
        for case in manifest["cases"]:
            path = ROOT / case["webp"]
            self.assertTrue(path.is_file(), case["webp"])
            total_bytes += path.stat().st_size
            self.assertLess(path.stat().st_size, 6_000_000, case["webp"])
            self.assertIn(f'src="{path.name}"', review)
            self.assertNotIn(f'src="{case["id"]}.preview.svg"', review)
            self.assertEqual("browser", case["webp_capture"]["renderer"])
            self.assertEqual(24, case["webp_capture"]["frames"])
            self.assertEqual(12, case["webp_capture"]["fps"])
            self.assertEqual(65, case["webp_capture"]["quality"])
            self.assertEqual("gsap@3.15.0", case["webp_capture"]["runtime_dependency"])
            self.assertEqual("browser-capture-v1", case["webp_capture"]["capture_contract"])
            self.assertEqual(64, len(case["webp_capture"]["input_sha256"]))
            with Image.open(path) as image:
                self.assertTrue(getattr(image, "is_animated", False), case["webp"])
                self.assertEqual(24, image.n_frames, case["webp"])
        self.assertLess(total_bytes, 6_000_000)

    def test_full_gallery_builders_keep_two_column_style_grids(self):

        build_showcase = (ROOT / "scripts" / "build_showcase.py").read_text(encoding="utf-8")
        style_builder = (ROOT / "scripts" / "build_style_showcase.py").read_text(encoding="utf-8")
        self.assertIn('class="grid style-grid"', build_showcase)
        self.assertIn(".style-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }", build_showcase)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr));", style_builder)

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
            self.assertIn("gallery/character-themes.html", source)
        self.assertIn("continu", readme.lower())
        self.assertIn("持续", readme_zh)
        self.assertIn("continu", html_runtime.lower())
        self.assertIn("node scripts/verify_stage_motion_modes.mjs", html_runtime)
        self.assertIn("prefers-reduced-motion: reduce", html_runtime)


if __name__ == "__main__":
    unittest.main()
