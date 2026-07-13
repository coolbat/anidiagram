import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from anidiagram.cli import main
from anidiagram.exporters import _render_frames
from anidiagram.exporters import _browser_capture_script
from anidiagram.exporters import write_browser_capture
from anidiagram.exporters import write_gif
from anidiagram.illustrated_character_icons import character_definition, character_icon_ids
from anidiagram.icon_system import resolve_icon_system
from anidiagram.motion_manifest import CHARACTER_ICON_PERFORMANCES, CHARACTER_REST_AT
from anidiagram.planner import brief_to_plan
from anidiagram.planner import compile_plan
from anidiagram.presets import preset_names
from anidiagram.quality import quality_report
from anidiagram.renderer_svg import icon_surface_accent
from anidiagram.renderer_svg import icon_surface_fill
from anidiagram.renderer_svg import render_svg
from anidiagram.renderer_svg import render_html
from anidiagram.renderer_html_runtime import render_html_runtime
from anidiagram.schema import KNOWN_ICONS, DiagramScriptValidationError, compile_scene
from anidiagram.styles import deep_merge, load_style, validate_style_profile


ROOT = Path(__file__).resolve().parents[1]


class SvgRendererTest(unittest.TestCase):
    def _scene_with_icons(self):
        icons = sorted(KNOWN_ICONS)
        return compile_scene(
            {
                "version": "0.3",
                "canvas": {"width": 1180, "height": 520},
                "title": {"text": "Illustrated character icon registry"},
                "motion": {"profile": "expressive", "node": {"preset": "icon-performance"}},
                "nodes": [
                    {
                        "id": icon,
                        "label": icon.title(),
                        "caption": "character registry",
                        "position": [70 + (index % 6) * 180, 125 + (index // 6) * 150],
                        "size": [145, 78],
                        "role": "neutral",
                        "icon": icon,
                    }
                    for index, icon in enumerate(icons)
                ],
            }
        )

    def _scene_with_icon(self, icon, *, motion=None, node_effect=None):
        node = {
            "id": icon,
            "label": icon.title(),
            "caption": "semantic icon",
            "position": [180, 150],
            "size": [240, 100],
            "role": "agent",
            "icon": icon,
        }
        if node_effect is not None:
            node["effect"] = node_effect
        return compile_scene(
            {
                "version": "0.3",
                "canvas": {"width": 640, "height": 360},
                "title": {"text": "Character icon", "subtitle": "clean-room test"},
                "motion": motion or {"profile": "expressive", "node": {"preset": "icon-performance"}},
                "nodes": [node],
            }
        )

    def _manifest_from_html(self, html):
        marker = '<script type="application/json" id="anidiagram-motion-manifest">'
        start = html.index(marker) + len(marker)
        return json.loads(html[start:html.index("</script>", start)])

    def test_default_icon_system_is_illustrated_character_v1(self):
        self.assertEqual("illustrated-character-v1", load_style()["icon_system"])
        svg = render_svg(self._scene_with_icon("agent"), load_style())
        self.assertIn('data-icon-system="illustrated-character-v1"', svg)
        self.assertIn('id="icon-agent-chip"', svg)

    def test_character_registry_and_manifest_cover_every_known_icon(self):
        self.assertEqual(set(character_icon_ids()), KNOWN_ICONS)
        for icon in KNOWN_ICONS:
            definition = character_definition(icon)
            self.assertIsNotNone(definition, icon)
            self.assertEqual("root", definition.parts[0], icon)
            self.assertEqual(len(definition.parts), len(set(definition.parts)), icon)

        html = render_html_runtime(self._scene_with_icons(), load_style(), runtime="gsap")
        manifest = self._manifest_from_html(html)

        self.assertEqual("illustrated-character-v1", manifest["icon_system"])
        self.assertEqual(KNOWN_ICONS, {entry["icon"] for entry in manifest["icons"]})
        for entry in manifest["icons"]:
            definition = character_definition(entry["icon"])
            self.assertEqual(CHARACTER_ICON_PERFORMANCES[entry["icon"]], entry["performance"])
            self.assertEqual(set(definition.parts), set(entry["parts"]))
            for selector in entry["parts"].values():
                self.assertEqual(1, html.count(f'id="{selector[1:]}"'), selector)

    def test_icon_system_resolution_prefers_top_level_then_legacy_effects(self):
        self.assertEqual("illustrated-v1", resolve_icon_system({"icon_system": "illustrated-v1"}))
        self.assertEqual("semantic-line-v1", resolve_icon_system({"effects": {"icon_system": "semantic-line-v1"}}))
        self.assertEqual(
            "semantic-line-v1",
            resolve_icon_system({"icon_system": "semantic-line-v1", "effects": {"icon_system": "illustrated-v1"}}),
        )

    def test_icon_system_rejects_unknown_values_with_precise_paths(self):
        issues = validate_style_profile({"icon_system": "unknown-v1", "effects": {"icon_system": "also-unknown"}})
        self.assertEqual(["$.icon_system", "$.effects.icon_system"], [issue.path for issue in issues])

    def test_operator_is_a_valid_schema_icon_and_has_line_fallback(self):
        scene = self._scene_with_icon("operator")
        self.assertEqual("operator", scene.nodes[0].icon)
        svg = render_svg(scene, deep_merge(load_style(), {"icon_system": "semantic-line-v1"}))
        self.assertIn('semantic-icon-operator', svg)
        self.assertIn('id="icon-operator-laptop"', svg)

    def test_character_default_covers_api_without_a_line_fallback(self):
        report = quality_report(self._scene_with_icon("api"), load_style())
        warnings = [issue for issue in report["issues"] if issue["code"] == "character_icon_fallback"]
        self.assertEqual([], warnings)

    def test_character_manifests_use_their_performances_and_parts(self):
        for icon, performance, part_id in (
            ("agent", "brain-think-pulse-v1", "#icon-agent-chip"),
            ("operator", "operator-type-focus-v1", "#icon-operator-laptop"),
            ("database", "bucket-ingest-confirm-v1", "#icon-database-liquid"),
        ):
            manifest = self._manifest_from_html(render_html_runtime(self._scene_with_icon(icon), load_style(), runtime="gsap"))
            entry = manifest["icons"][0]
            self.assertEqual("illustrated-character-v1", manifest["icon_system"])
            self.assertEqual(performance, entry["performance"])
            self.assertIn(part_id, entry["parts"].values())

    def test_character_manifest_inherits_motion_for_omitted_or_empty_node_effect(self):
        for node_effect in (None, {}):
            scene = self._scene_with_icon("search", node_effect=node_effect)
            manifest = self._manifest_from_html(render_html_runtime(scene, load_style(), runtime="gsap"))

            self.assertEqual(["search-scout-find-v1"], [entry["performance"] for entry in manifest["icons"]])

    def test_character_manifest_has_no_runtime_icon_when_profile_is_off(self):
        scene = self._scene_with_icon("search", motion={"profile": "off", "node": {"preset": "icon-performance"}})
        manifest = self._manifest_from_html(render_html_runtime(scene, load_style(), runtime="gsap"))

        self.assertEqual("illustrated-character-v1", manifest["icon_system"])
        self.assertEqual([], manifest["icons"])

    def test_character_manifest_honors_explicit_node_effect_none(self):
        scene = self._scene_with_icon("search", node_effect={"preset": "none"})
        manifest = self._manifest_from_html(render_html_runtime(scene, load_style(), runtime="gsap"))

        self.assertEqual("illustrated-character-v1", manifest["icon_system"])
        self.assertEqual([], manifest["icons"])

    def test_manifest_serializes_explicit_legacy_icon_systems(self):
        for icon_system in ("illustrated-v1", "semantic-line-v1"):
            manifest = self._manifest_from_html(
                render_html_runtime(self._scene_with_icon("agent"), deep_merge(load_style(), {"icon_system": icon_system}), runtime="gsap")
            )
            self.assertEqual(icon_system, manifest["icon_system"])

    def test_character_runtime_contract_covers_all_icons_with_exact_parts_and_dispatch(self):
        source = (ROOT / "runtime" / "anidiagram-runtime.js").read_text(encoding="utf-8")
        contract = {
            "brain-think-pulse-v1": ("playBrainThinkPulse", ["brain-left", "brain-right", "chip", "signal", "spark"]),
            "operator-type-focus-v1": ("playOperatorTypeFocus", ["hair", "face", "glasses", "hands", "laptop", "cursor"]),
            "bucket-ingest-confirm-v1": ("playBucketIngestConfirm", ["hat", "bucket", "liquid", "bead", "check"]),
            "search-scout-find-v1": ("playSearchScoutFind", ["lens", "scan", "marker", "spark"]),
            "tool-kit-action-v1": ("playToolKitAction", ["bucket", "lid", "wrench", "spark"]),
            "api-signal-return-v1": ("playApiSignalReturn", ["interface", "request", "receipt", "status"]),
            "memory-index-commit-v1": ("playMemoryIndexCommit", ["back-card", "front-card", "bookmark", "key-line"]),
            "output-envelope-reveal-v1": ("playOutputEnvelopeReveal", ["envelope", "card", "check", "spark"]),
            "file-note-write-v1": ("playFileNoteWrite", ["page", "corner", "line-1", "line-2", "line-3", "dot"]),
            "folder-file-store-v1": ("playFolderFileStore", ["folder", "tab", "sheet", "seal"]),
            "cloud-uplink-ready-v1": ("playCloudUplinkReady", ["cloud", "kite", "data-dot", "ready-light"]),
            "shield-guard-confirm-v1": ("playShieldGuardConfirm", ["shell", "core", "scan", "check"]),
            "token-intent-ready-v1": ("playTokenIntentReady", ["shell", "core", "tick-left", "tick-right", "tick-top", "tick-bottom"]),
        }

        self.assertEqual(set(CHARACTER_ICON_PERFORMANCES.values()), set(contract))
        for performance, (function_name, expected_parts) in contract.items():
            icon = next(icon for icon, name in CHARACTER_ICON_PERFORMANCES.items() if name == performance)
            self.assertEqual(list(character_definition(icon).parts[1:]), expected_parts)
            body = self._javascript_function_body(source, function_name)
            actual_parts = self._javascript_required_parts(body)
            self.assertEqual(expected_parts, actual_parts, performance)
            self.assertIn("hasParts(parts, required)", body)
            self.assertIn("setInitial(parts, gsap)", body)
            self.assertIn(f'"{performance}": {function_name}', source)

    def test_character_runtime_uses_compact_idle_gap_and_subtle_breath_shell(self):
        runtime_source = (ROOT / "runtime" / "anidiagram-runtime.js").read_text(encoding="utf-8")
        renderer_source = (ROOT / "src" / "anidiagram" / "renderer_illustrated_character.py").read_text(encoding="utf-8")
        performer_names = (
            "playBrainThinkPulse",
            "playOperatorTypeFocus",
            "playBucketIngestConfirm",
            "playSearchScoutFind",
            "playToolKitAction",
            "playApiSignalReturn",
            "playMemoryIndexCommit",
            "playOutputEnvelopeReveal",
            "playFileNoteWrite",
            "playFolderFileStore",
            "playCloudUplinkReady",
            "playShieldGuardConfirm",
            "playTokenIntentReady",
        )

        self.assertIn("const CHARACTER_REPEAT_DELAY = 0.8;", runtime_source)
        self.assertIn("const CHARACTER_IDLE_BREATHE_SCALE = 1.012;", runtime_source)
        self.assertIn('class="illustrated-character-motion-shell"', renderer_source)
        rest_body = self._javascript_function_body(runtime_source, "finishCharacterAtRest")
        self.assertIn('querySelector(".illustrated-character-motion-shell")', rest_body)
        self.assertIn("CHARACTER_IDLE_BREATHE_SCALE", rest_body)
        self.assertIn("duration: 0.22", rest_body)
        for function_name in performer_names:
            body = self._javascript_function_body(runtime_source, function_name)
            self.assertIn("repeatDelay: CHARACTER_REPEAT_DELAY", body, function_name)
            self.assertNotRegex(body, r"repeatDelay:\s*1\.")

    def test_stage_runtime_contract_has_distinct_modes_and_quiet_packet_rhythm(self):
        runtime_source = (ROOT / "runtime" / "anidiagram-runtime.js").read_text(encoding="utf-8")
        manifest_source = (ROOT / "src" / "anidiagram" / "motion_manifest.py").read_text(encoding="utf-8")
        verifier_source = (ROOT / "scripts" / "verify_stage_motion_modes.mjs").read_text(encoding="utf-8")

        self.assertIn("const EDGE_PACKET_COUNT = 1;", runtime_source)
        self.assertIn("const EDGE_PACKET_REPEAT_DELAY = 0.7;", runtime_source)
        self.assertIn("repeatDelay: EDGE_PACKET_REPEAT_DELAY", runtime_source)
        self.assertIn('__anidiagramStage = "edge-packet"', runtime_source)
        self.assertIn('__anidiagramStage = "title-entry"', runtime_source)
        self.assertIn('playStageEffects(manifest, "readable")', runtime_source)
        self.assertIn("settleCharacterTimelines", runtime_source)
        title_body = self._javascript_function_body(runtime_source, "playTitleSweep")
        self.assertNotIn("repeat: -1", title_body)
        self.assertIn("scaleX", title_body)
        edge_body = self._javascript_function_body(runtime_source, "playRuntimeEdgeFlow")
        self.assertIn("EDGE_PACKET_COUNT", edge_body)
        self.assertIn("readable_edge_limit", edge_body)
        self.assertNotIn('filter: "url(#particle-glow)"', edge_body)
        self.assertIn('"edge_limit"', manifest_source)
        self.assertIn('"readable_edge_limit"', manifest_source)
        self.assertIn('require("playwright")', verifier_source)
        self.assertIn("Expressive -> Readable -> Off -> Expressive", verifier_source)
        self.assertIn("duplicate runtime-generated stage elements", verifier_source)

    def test_character_theme_defaults_keep_frames_stable_and_group_reveal_soft(self):
        flow = json.loads((ROOT / "examples" / "illustrated-character-v1-flow.diagram.json").read_text(encoding="utf-8"))
        gallery = json.loads((ROOT / "examples" / "illustrated-character-v1-icons.diagram.json").read_text(encoding="utf-8"))

        self.assertEqual("icon-performance", flow["motion"]["node"]["preset"])
        self.assertEqual("soft-reveal", flow["motion"]["group"]["preset"])
        self.assertEqual("icon-performance", gallery["motion"]["node"]["preset"])
        self.assertEqual("static", gallery["motion"]["group"]["preset"])
        source = (ROOT / "src" / "anidiagram" / "renderer_svg.py").read_text(encoding="utf-8")
        self.assertNotIn('node_mode in {"float", "glow-breathe", "pop", "icon-pulse", "pulse", "ripple", "icon-performance"}', source)

    def test_character_rest_reset_preserves_svg_root_anchor(self):
        runtime_source = (ROOT / "runtime" / "anidiagram-runtime.js").read_text(encoding="utf-8")
        verifier_source = (ROOT / "scripts" / "verify_character_motion_rest.mjs").read_text(encoding="utf-8")
        reset_body = self._javascript_function_body(runtime_source, "finishCharacterAtRest")

        self.assertIn('name !== "root"', reset_body)
        self.assertIn("getScreenCTM()", verifier_source)
        self.assertIn("root anchor changed", verifier_source)

    def test_character_browser_verifiers_resolve_local_then_global_playwright_portably(self):
        for name in ("verify_character_motion_rest.mjs", "verify_character_reduced_motion.mjs"):
            source = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            self.assertIn('require("playwright")', source)
            self.assertIn('execFileSync("npm", ["root", "-g"]', source)
            self.assertIn('createRequire(path.join(globalRoot, "package.json"))', source)
            self.assertIn("Unable to resolve Playwright", source)

    def test_character_browser_verifiers_require_valid_character_manifests(self):
        rest_source = (ROOT / "scripts" / "verify_character_motion_rest.mjs").read_text(encoding="utf-8")
        reduced_source = (ROOT / "scripts" / "verify_character_reduced_motion.mjs").read_text(encoding="utf-8")

        self.assertIn("readCharacterManifest", rest_source)
        self.assertIn('manifest.icon_system !== "illustrated-character-v1"', rest_source)
        self.assertIn("FULL_GALLERY_CHARACTER_COUNT = 13", rest_source)
        self.assertNotIn("CHARACTER_PERFORMANCE_IDS", rest_source)
        self.assertIn("readCharacterManifest", reduced_source)
        self.assertIn('manifest.icon_system !== "illustrated-character-v1"', reduced_source)
        self.assertIn("expected-character-icon-count", reduced_source)
        self.assertIn("verified reduced motion for", reduced_source)

    def test_html_runtime_docs_show_direct_character_verification_commands(self):
        source = (ROOT / "docs" / "html-runtime.md").read_text(encoding="utf-8")
        self.assertIn("verify_character_motion_rest.mjs outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html", source)
        self.assertIn("verify_character_reduced_motion.mjs outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html 13", source)
        self.assertIn("verify_character_reduced_motion.mjs outputs/illustrated-character-v1-flow/illustrated-character-v1-flow.html 8", source)
        self.assertIn("local project dependency first, then `npm root -g`", source)

    def test_character_manifest_serializes_deterministic_rest_times(self):
        manifest = self._manifest_from_html(render_html_runtime(self._scene_with_icons(), load_style(), runtime="gsap"))
        self.assertEqual(set(CHARACTER_ICON_PERFORMANCES), set(CHARACTER_REST_AT))
        for entry in manifest["icons"]:
            self.assertEqual(CHARACTER_REST_AT[entry["icon"]], entry["rest_at"])

    def test_legacy_illustrated_manifest_does_not_serialize_character_rest_times(self):
        manifest = self._manifest_from_html(
            render_html_runtime(
                self._scene_with_icon("search"),
                deep_merge(load_style(), {"icon_system": "illustrated-v1"}),
                runtime="gsap",
            )
        )
        self.assertEqual("illustrated-v1", manifest["icon_system"])
        self.assertNotIn("rest_at", manifest["icons"][0])

    def test_character_svg_emits_source_opacity_for_every_rest_checked_part(self):
        svg = render_svg(self._scene_with_icons(), load_style())
        expected_elements = 0
        for icon in character_icon_ids():
            definition = character_definition(icon)
            expected_elements += 1 + len(definition.primitives)
            for part in definition.parts:
                self.assertIn(f'id="icon-{icon}-{part}"', svg)
        self.assertEqual(expected_elements, svg.count('data-rest-opacity="1"'))

    def test_character_default_ignores_legacy_icon_motion_but_semantic_line_honors_it(self):
        scene = self._scene_with_icon("search", node_effect={"preset": "icon-performance", "icon_motion": "api-request-response-v2"})
        character_manifest = self._manifest_from_html(render_html_runtime(scene, load_style(), runtime="gsap"))
        line_manifest = self._manifest_from_html(
            render_html_runtime(scene, deep_merge(load_style(), {"icon_system": "semantic-line-v1"}), runtime="gsap")
        )
        self.assertEqual("search-scout-find-v1", character_manifest["icons"][0]["performance"])
        self.assertEqual("api-request-response-v2", line_manifest["icons"][0]["performance"])

    def test_semantic_line_rejects_character_v1_request_and_falls_back_to_line_v2(self):
        scene = self._scene_with_icon("search", node_effect={"preset": "icon-performance", "icon_motion": "search-scout-find-v1"})
        manifest = self._manifest_from_html(
            render_html_runtime(scene, deep_merge(load_style(), {"icon_system": "semantic-line-v1"}), runtime="gsap")
        )
        self.assertEqual("search-discover-v2", manifest["icons"][0]["performance"])

    @staticmethod
    def _javascript_function_body(source, function_name):
        marker = f"function {function_name}("
        start = source.index(marker)
        open_brace = source.index("{", source.index(")", start))
        depth = 0
        for index in range(open_brace, len(source)):
            if source[index] == "{":
                depth += 1
            elif source[index] == "}":
                depth -= 1
                if depth == 0:
                    return source[open_brace + 1:index]
        raise AssertionError(f"unterminated JavaScript function: {function_name}")

    @staticmethod
    def _javascript_required_parts(body):
        import re

        match = re.search(r'const required = \[(.*?)\];', body, re.DOTALL)
        if match is None:
            raise AssertionError("character performer must declare const required")
        return re.findall(r'[\"\']([^\"\']+)[\"\']', match.group(1))

    def test_illustrated_character_gallery_covers_every_known_icon_once(self):
        style = load_style(ROOT / "styles" / "illustrated-character.json")
        spec = json.loads((ROOT / "examples" / "illustrated-character-v1-icons.diagram.json").read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        manifest = self._manifest_from_html(render_html_runtime(scene, style, runtime="gsap"))

        self.assertEqual(KNOWN_ICONS, {node["icon"] for node in spec["nodes"]})
        self.assertEqual(len(KNOWN_ICONS), len(spec["nodes"]))
        self.assertEqual(len(KNOWN_ICONS), len(manifest["icons"]))
        self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, quality_report(scene, style)["summary"])

    def test_illustrated_character_flow_uses_covered_icons_without_fallback_copy(self):
        style = load_style(ROOT / "styles" / "illustrated-character.json")
        path = ROOT / "examples" / "illustrated-character-v1-flow.diagram.json"
        source = path.read_text(encoding="utf-8")
        spec = json.loads(source)
        scene = compile_scene(spec)

        self.assertTrue({node["icon"] for node in spec["nodes"]}.issubset(KNOWN_ICONS))
        self.assertNotIn("fallback", source.lower())
        self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, quality_report(scene, style)["summary"])

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
        self.assertIn('class="node-title">Planner</tspan>', svg)
        self.assertIn('class="node-title">Agent</tspan>', svg)
        self.assertIn("marker-end", svg)

    def test_cli_writes_svg_and_html_runtime(self):
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
            self.assertIn("anidiagram-motion-manifest", html.read_text(encoding="utf-8"))
            self.assertIn("window.AniDiagramRuntime", html.read_text(encoding="utf-8"))

    def test_cli_writes_debug_viewer(self):
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
                        "--formats",
                        "viewer",
                    ]
                )

            viewer = Path(tmp) / "agent-memory.viewer.html"
            self.assertTrue(viewer.is_file())
            viewer_text = viewer.read_text(encoding="utf-8")
            self.assertIn("<!doctype html>", viewer_text)
            self.assertIn("setMotionMode", viewer_text)
            self.assertNotIn("anidiagram-motion-manifest", viewer_text)

    def test_html_runtime_contains_manifest_runtime_and_matching_part_ids(self):
        spec = json.loads((ROOT / "examples" / "high-fidelity-runtime.diagram.json").read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        style = load_style(ROOT / "styles" / "deep-tech.json")

        html = render_html_runtime(scene, style, runtime="gsap")
        marker = '<script type="application/json" id="anidiagram-motion-manifest">'
        start = html.index(marker) + len(marker)
        end = html.index("</script>", start)
        manifest = json.loads(html[start:end])

        self.assertEqual("motion-manifest-0.1", manifest["version"])
        self.assertEqual("gsap", manifest["runtime"])
        self.assertEqual("ambient", manifest["mode"])
        self.assertEqual("independent-icon-loops", manifest["sequence"])
        self.assertEqual("layered", manifest["scene_sequence"])
        self.assertEqual(
            {"edge_flow": True, "title_sweep": True, "edge_limit": 4, "readable_edge_limit": 2},
            manifest["stage"],
        )
        self.assertEqual(
            {
                "token-intent-ready-v1",
                "brain-think-pulse-v1",
                "api-signal-return-v1",
                "search-scout-find-v1",
                "memory-index-commit-v1",
                "tool-kit-action-v1",
                "output-envelope-reveal-v1",
            },
            {icon["performance"] for icon in manifest["icons"]},
        )
        self.assertIn("window.AniDiagramRuntime", html)
        self.assertIn("https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js", html)
        self.assertNotIn("data-icon-motion=", html)
        self.assertNotIn("<animate", html)
        self.assertNotIn("<set", html)
        self.assertNotIn("animateMotion", html)
        self.assertNotIn("animateTransform", html)
        self.assertNotIn('transformBox = "fill-box"', html)
        self.assertIn('data-motion-profile="expressive"', html)
        self.assertNotIn('data-motion-profile="off"', html)
        agent_icon = next(icon for icon in manifest["icons"] if icon["performance"] == "brain-think-pulse-v1")
        self.assertEqual(
            {
                "root",
                "brain-left",
                "brain-right",
                "chip",
                "signal",
                "spark",
            },
            set(agent_icon["parts"]),
        )
        self.assertIn("#icon-agent-brain-left", agent_icon["parts"].values())
        self.assertIn("#icon-agent-chip", agent_icon["parts"].values())
        self.assertIn("#icon-agent-spark", agent_icon["parts"].values())
        for icon in manifest["icons"]:
            for selector in icon["parts"].values():
                self.assertTrue(selector.startswith("#"))
                self.assertIn(f'id="{selector[1:]}"', html)

    def test_html_runtime_default_expressive_covers_builtin_icon_performances(self):
        icons = ["agent", "operator", "api", "search", "database", "memory", "tool", "token", "output", "file", "folder", "cloud", "shield"]
        spec = {
            "version": "0.3",
            "canvas": {"width": 1180, "height": 520},
            "title": {"text": "All Runtime Icons"},
            "nodes": [
                {
                    "id": icon,
                    "label": icon.title(),
                    "caption": "runtime",
                    "position": [70 + (index % 6) * 180, 125 + (index // 6) * 150],
                    "size": [145, 78],
                    "role": "neutral",
                    "icon": icon,
                }
                for index, icon in enumerate(icons)
            ],
        }
        scene = compile_scene(spec)
        html = render_html_runtime(scene, load_style(ROOT / "styles" / "deep-tech.json"), runtime="gsap")
        marker = '<script type="application/json" id="anidiagram-motion-manifest">'
        start = html.index(marker) + len(marker)
        end = html.index("</script>", start)
        manifest = json.loads(html[start:end])

        self.assertEqual("expressive", scene.motion.profile)
        self.assertEqual("expressive", manifest["profile"])
        self.assertEqual(
            {"edge_flow": True, "title_sweep": True, "edge_limit": None, "readable_edge_limit": 2},
            manifest["stage"],
        )
        self.assertEqual(
            {
                "brain-think-pulse-v1",
                "operator-type-focus-v1",
                "api-signal-return-v1",
                "search-scout-find-v1",
                "bucket-ingest-confirm-v1",
                "memory-index-commit-v1",
                "tool-kit-action-v1",
                "token-intent-ready-v1",
                "output-envelope-reveal-v1",
                "file-note-write-v1",
                "folder-file-store-v1",
                "cloud-uplink-ready-v1",
                "shield-guard-confirm-v1",
            },
            {icon["performance"] for icon in manifest["icons"]},
        )
        for performance in [
            "file-note-write-v1",
            "folder-file-store-v1",
            "cloud-uplink-ready-v1",
            "shield-guard-confirm-v1",
        ]:
            self.assertIn(performance, html)
        self.assertIn("playStageEffects", html)
        self.assertIn("runtime-edge-flow", html)
        self.assertIn("runtime-edge-packet", html)
        for icon in manifest["icons"]:
            for selector in icon["parts"].values():
                self.assertTrue(selector.startswith("#"))
                self.assertIn(f'id="{selector[1:]}"', html)

    def test_illustrated_bubble_runtime_exposes_registry_parts_and_stage_effects(self):
        spec = json.loads((ROOT / "examples" / "illustrated-bubble-runtime.diagram.json").read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        html = render_html_runtime(scene, load_style(ROOT / "styles" / "illustrated-bubble.json"), runtime="gsap")
        marker = '<script type="application/json" id="anidiagram-motion-manifest">'
        start = html.index(marker) + len(marker)
        end = html.index("</script>", start)
        manifest = json.loads(html[start:end])

        self.assertEqual("illustrated-v1", manifest["icon_system"])
        self.assertEqual("expressive", manifest["profile"])
        self.assertEqual(True, manifest["stage"]["edge_flow"])
        self.assertEqual(True, manifest["stage"]["relation_circles"])
        self.assertEqual(True, manifest["stage"]["group_fields"])
        self.assertEqual(True, manifest["stage"]["data_particles"])
        self.assertIn('data-icon-system="illustrated-v1"', html)
        self.assertIn("playIllustratedCommon", html)
        self.assertIn("playRuntimeRelationCircles", html)
        self.assertIn("playRuntimeGroupFields", html)
        self.assertIn("runtime-relation-circle", html)
        self.assertIn("runtime-group-field", html)
        self.assertEqual(12, len(manifest["icons"]))
        agent_icon = next(icon for icon in manifest["icons"] if icon["node_id"] == "agent")
        self.assertEqual("think-decide-act", agent_icon["semantic_role"])
        self.assertIn("primary", agent_icon["colors"])
        for common_part in ["bubble", "bubbleHalo", "wash", "accentMark", "sparkle", "orbitDot"]:
            self.assertIn(common_part, agent_icon["parts"])
            selector = agent_icon["parts"][common_part]
            self.assertTrue(selector.startswith("#"))
            self.assertIn(f'id="{selector[1:]}"', html)
        for icon in manifest["icons"]:
            for selector in icon["parts"].values():
                self.assertTrue(selector.startswith("#"))
                self.assertIn(f'id="{selector[1:]}"', html)

    def test_html_runtime_suppresses_svg_icon_fallbacks(self):
        spec = {
            "version": "0.3",
            "canvas": {"width": 420, "height": 260},
            "title": {"text": "Runtime Only", "subtitle": "no svg icon fallback"},
            "motion": {
                "profile": "teaching",
                "node": {"preset": "icon-semantic"},
                "edge": {"preset": "static"},
            },
            "nodes": [
                {"id": "shield", "label": "Shield", "caption": "static in runtime", "position": [120, 130], "size": [170, 78], "role": "risk", "icon": "shield"}
            ],
        }
        scene = compile_scene(spec)
        html = render_html_runtime(
            scene,
            deep_merge(load_style(ROOT / "styles" / "minimal-light.json"), {"icon_system": "semantic-line-v1"}),
            runtime="gsap",
        )
        marker = '<script type="application/json" id="anidiagram-motion-manifest">'
        start = html.index(marker) + len(marker)
        end = html.index("</script>", start)
        manifest = json.loads(html[start:end])

        self.assertIn("semantic-icon-shield", html)
        self.assertIn("shield-check-v2", {icon["performance"] for icon in manifest["icons"]})
        self.assertIn('id="icon-shield-pulse"', html)
        self.assertIn('id="icon-shield-scan"', html)
        self.assertNotIn("data-icon-motion=", html)
        self.assertNotIn("<animate", html)
        self.assertNotIn("<set", html)
        self.assertNotIn("animateMotion", html)
        self.assertNotIn("animateTransform", html)

    def test_svg_output_uses_lightweight_icon_fallback_without_runtime_manifest(self):
        spec = json.loads((ROOT / "examples" / "high-fidelity-runtime.diagram.json").read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        style = deep_merge(load_style(ROOT / "styles" / "deep-tech.json"), {"icon_system": "semantic-line-v1"})

        svg = render_svg(scene, style)

        self.assertNotIn("anidiagram-motion-manifest", svg)
        self.assertNotIn("title-handwrite", svg)
        self.assertIn("title-sweep", svg)
        self.assertIn("data-icon-motion=", svg)
        self.assertIn('data-icon-motion="token-pulse"', svg)
        self.assertIn('data-icon-motion="agent-orbit"', svg)
        self.assertIn('data-icon-motion="search-sweep"', svg)
        self.assertNotIn('data-icon-motion="database-write"', svg)
        self.assertNotIn("token-intent-v2", svg)
        self.assertNotIn("agent-think-act-v2", svg)
        self.assertIn('id="icon-agent-outline-left"', svg)
        self.assertIn('id="icon-agent-branch-right"', svg)
        self.assertIn('id="icon-agent-node-center"', svg)
        self.assertIn('id="icon-agent-decision-token"', svg)
        self.assertIn('id="icon-request-core"', svg)
        self.assertIn('id="icon-tool-connector"', svg)
        self.assertIn('id="icon-output-check"', svg)
        self.assertIn('id="icon-api-request-token"', svg)
        self.assertIn('id="icon-search-result-1"', svg)
        self.assertIn('id="icon-memory-commit-token"', svg)
        self.assertIn('id="icon-memory-front-card"', svg)

    def test_render_svg_runtime_stage_suppresses_icon_smil_fallbacks(self):
        spec = json.loads((ROOT / "examples" / "high-fidelity-runtime.diagram.json").read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        style = deep_merge(load_style(ROOT / "styles" / "deep-tech.json"), {"icon_system": "semantic-line-v1"})

        svg = render_svg(scene, style, animation_mode="runtime-stage")

        self.assertIn('id="icon-agent-outline-left"', svg)
        self.assertIn('id="icon-agent-node-center"', svg)
        self.assertIn('id="icon-agent-decision-token"', svg)
        self.assertNotIn("data-icon-motion=", svg)
        self.assertNotIn("<animate", svg)
        self.assertNotIn("<set", svg)
        self.assertNotIn("animateMotion", svg)
        self.assertNotIn("animateTransform", svg)
        self.assertNotIn("icon-agent-line-draw", svg)
        self.assertNotIn("icon-search-light", svg)
        self.assertNotIn("icon-database-top-bounce", svg)

    def test_cli_writes_html_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(
                    [
                        "--spec",
                        str(ROOT / "examples" / "high-fidelity-runtime.diagram.json"),
                        "--style",
                        str(ROOT / "styles" / "deep-tech.json"),
                        "--outdir",
                        tmp,
                        "--basename",
                        "high-fidelity-runtime",
                        "--formats",
                        "svg,html-runtime,quality",
                        "--html-runtime",
                        "gsap",
                    ]
                )

            result = json.loads(stdout.getvalue())
            runtime_html = Path(tmp) / "high-fidelity-runtime.html"

            self.assertTrue(result["ok"])
            self.assertTrue(runtime_html.is_file())
            self.assertNotIn("html-runtime", result["outputs"])
            self.assertTrue(Path(result["outputs"]["html"]["path"]).is_file())
            self.assertIn("anidiagram-motion-manifest", runtime_html.read_text(encoding="utf-8"))
            self.assertEqual(0, result["outputs"]["quality"]["summary"]["errors"])
            self.assertEqual(0, result["outputs"]["quality"]["summary"]["warnings"])

    def test_cli_routes_browser_renderer_for_raster_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout = io.StringIO()
            browser_result = {
                "format": "png",
                "path": str(Path(tmp) / "minimal.png"),
                "status": "written",
                "renderer": "browser",
                "fps": 24,
                "frames": 1,
                "scale": 2.0,
            }
            with patch("anidiagram.cli.write_browser_capture", return_value=browser_result) as capture:
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
                            "--formats",
                            "png,quality",
                            "--html-runtime",
                            "gsap",
                            "--export-renderer",
                            "browser",
                            "--export-fps",
                            "24",
                            "--export-frames",
                            "12",
                            "--export-scale",
                            "2",
                        ]
                    )

            result = json.loads(stdout.getvalue())

            capture.assert_called_once()
            self.assertEqual("browser", result["outputs"]["png"]["renderer"])
            self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, result["outputs"]["quality"]["summary"])

    def test_browser_capture_skips_when_playwright_is_unavailable(self):
        spec = json.loads((ROOT / "tests" / "fixtures" / "minimal.diagram.json").read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        style = load_style(ROOT / "styles" / "minimal-light.json")

        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "anidiagram.exporters._playwright_node_env",
                return_value=("", {}, "Node Playwright is not installed"),
            ):
                result = write_browser_capture(scene, style, Path(tmp) / "minimal.png", "png")

        self.assertEqual("skipped", result["status"])
        self.assertIn("Node Playwright", result["reason"])

    def test_browser_capture_script_seeks_runtime_timelines_per_frame(self):
        script = _browser_capture_script()

        self.assertIn("const frameSeconds = index / fps;", script)
        self.assertIn("svgElement.setCurrentTime(seconds)", script)
        self.assertIn("window.__ANIDIAGRAM_TIMELINES__", script)
        self.assertIn("tl.totalTime(localSeconds % cycleSeconds, false)", script)

    def test_browser_capture_lottie_packages_captured_frames(self):
        spec = json.loads((ROOT / "tests" / "fixtures" / "minimal.diagram.json").read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        style = load_style(ROOT / "styles" / "minimal-light.json")

        def fake_capture(**kwargs):
            for index in range(kwargs["frames"]):
                (kwargs["frames_dir"] / f"frame-{index:04d}.png").write_bytes(b"captured frame")
            return {"status": "written", "reason": ""}

        with tempfile.TemporaryDirectory() as tmp:
            lottie_path = Path(tmp) / "minimal.lottie.json"
            with patch("anidiagram.exporters._capture_browser_runtime", side_effect=fake_capture):
                result = write_browser_capture(scene, style, lottie_path, "lottie", frames=2, fps=12, scale=1)

            data = json.loads(lottie_path.read_text(encoding="utf-8"))

        self.assertEqual("written", result["status"])
        self.assertEqual("browser", result["renderer"])
        self.assertEqual(12, data["fr"])
        self.assertEqual(2, len(data["assets"]))
        self.assertEqual(2, len(data["layers"]))
        self.assertEqual("browser", data["meta"]["renderer"])

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
            "44b4673059951bc2143ed182c4fa829c65b7fce6d93249a827b088bdbbefb133",
            hashlib.sha256(svg.encode("utf-8")).hexdigest(),
        )

    def test_motion_profile_off_renders_static_svg(self):
        spec = json.loads((ROOT / "tests" / "fixtures" / "minimal.diagram.json").read_text(encoding="utf-8"))
        spec["version"] = "0.2"
        spec["motion"] = {"profile": "off"}
        scene = compile_scene(spec)
        svg = render_svg(scene, deep_merge(load_style(ROOT / "styles" / "minimal-light.json"), {"icon_system": "semantic-line-v1"}))

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
        svg = render_svg(
            scene,
            deep_merge(load_style(ROOT / "styles" / "sketch-board.json"), {"icon_system": "semantic-line-v1"}),
        )

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
                {"id": "memory_stack", "label": "Memory", "caption": "stack", "position": [245, 405], "size": [150, 72], "role": "memory", "icon": "memory", "effect": {"preset": "none"}},
            ],
        }
        scene = compile_scene(spec)
        report = quality_report(scene)
        svg = render_svg(scene, deep_merge(load_style(ROOT / "styles" / "minimal-light.json"), {"icon_system": "semantic-line-v1"}))

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
        self.assertIn('fill="#c8edf3"', svg)
        self.assertIn("icon-file-page-motion", svg)
        self.assertIn("icon-file-fold-motion", svg)
        self.assertIn("icon-folder-body", svg)
        self.assertIn("icon-api-left-endpoint", svg)
        self.assertIn("icon-api-right-endpoint", svg)
        self.assertIn("icon-database-top-bounce", svg)
        self.assertIn("icon-database-layer-flash", svg)
        self.assertIn("icon-folder-file-line", svg)
        self.assertIn("icon-cloud-dot", svg)
        self.assertIn("icon-search-light", svg)
        self.assertIn("icon-shield-pulse", svg)
        self.assertIn("icon-agent-line", svg)
        self.assertIn("icon-agent-node", svg)
        self.assertIn("icon-agent-decision-token", svg)
        self.assertIn("icon-tool-spark", svg)
        self.assertIn(">fx</text>", svg)
        self.assertIn("icon-output-line", svg)
        self.assertIn("icon-token-core", svg)
        self.assertIn("icon-token-tick", svg)
        self.assertIn("icon-memory-front-card", svg)
        self.assertIn("icon-memory-trace", svg)
        self.assertIn("icon-memory-dot", svg)
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
        self.assertEqual("#c8edf3", icon_surface_fill("#ecfeff", "#0891b2"))
        self.assertEqual("#f9d1d1", icon_surface_fill("#fef2f2", "#dc2626"))
        self.assertEqual("#85ccdc", icon_surface_accent("#a8dde8", "#0891b2"))

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
        svg = render_svg(compile_scene(spec), deep_merge(load_style(ROOT / "styles" / "minimal-light.json"), {"icon_system": "semantic-line-v1"}))

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
            self.assertEqual(0, result["outputs"]["quality"]["summary"]["errors"])
            self.assertEqual(0, result["outputs"]["quality"]["summary"]["warnings"])

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
        self.assertIn("semantic-icon-illustrated-character-v1", svg)
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
