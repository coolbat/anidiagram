import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from anidiagram.cli import main
from anidiagram.composition import DIAGRAM_CORE_ICONS
from anidiagram.diagram_core.catalog import approved_icon_ids
from anidiagram.motion_manifest import build_motion_manifest
from anidiagram.planner import compile_plan
from anidiagram.renderer_svg import render_svg
from anidiagram.schema import DiagramScriptValidationError, compile_scene
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]


class CompositionContractTest(unittest.TestCase):
    def _plan(self):
        return json.loads(
            (ROOT / "examples" / "contracts" / "production-request-path.plan.json").read_text(encoding="utf-8")
        )

    def test_v02_auto_presentation_resolves_once_into_v04(self):
        spec = compile_plan(self._plan())

        self.assertEqual("0.4", spec["version"])
        self.assertEqual("diagram-core-v1", spec["icon_system"])
        self.assertEqual("minimal-light", spec["style"])
        self.assertEqual("layered", spec["preset"])
        self.assertEqual("showcase-v1", spec["motion"]["profile"])
        self.assertEqual(
            {
                "profile": "unrestricted",
                "motion_area": "unrestricted",
                "pulse_mode": "all",
            },
            spec["motion_policy"],
        )
        self.assertEqual(
            {
                "icon_system": {"value": "diagram-core-v1", "source": "default"},
                "style": {"value": "minimal-light", "source": "fallback"},
                "layout": {"value": "layered", "source": "fallback"},
                "motion": {"value": "showcase-v1", "source": "explicit"},
            },
            spec["resolved_presentation"],
        )
        self.assertEqual(4, len(spec["nodes"]))
        self.assertEqual(3, len(spec["edges"]))
        self.assertEqual(1, len(spec["groups"]))
        self.assertEqual("gateway", next(node for node in spec["nodes"] if node["id"] == "ingress")["icon"])

        scene = compile_scene(spec)
        self.assertEqual("diagram-core-v1", scene.icon_system)
        self.assertEqual("showcase-v1", scene.motion.profile)
        self.assertEqual("layered", scene.preset)
        self.assertEqual("unrestricted", scene.motion_policy.profile)
        self.assertEqual("unrestricted", scene.motion_policy.motion_area)
        self.assertEqual("all", scene.motion_policy.pulse_mode)

        svg = render_svg(scene, load_style())
        self.assertIn('data-icon-system="diagram-core-v1"', svg)
        self.assertIn('data-icon-source="diagram-core-v1"', svg)
        self.assertIn('id="node_u2x2eingress__gateway__root"', svg)
        self.assertNotIn("semantic-icon-character-wrap", svg)

        manifest = build_motion_manifest(scene, load_style())
        self.assertEqual(4, len(manifest["icons"]))
        self.assertEqual([0, 1, 2], manifest["stage"]["active_edge_indices"])
        gateway = next(item for item in manifest["icons"] if item["icon"] == "gateway")
        self.assertEqual("gateway-showcase-loop-v1", gateway["performance"])
        self.assertIn("recipe", gateway)
        self.assertEqual(
            "#node_u2x2eingress__gateway__gate",
            gateway["parts"]["gate"],
        )

    def test_v02_explicit_presentation_is_preserved(self):
        plan = self._plan()
        plan["presentation"] = {
            "icon_system": "illustrated",
            "style": "claude-warm",
            "layout": "pipeline",
            "motion": "teaching",
        }

        spec = compile_plan(plan)

        self.assertEqual("illustrated", spec["icon_system"])
        self.assertEqual("claude-warm", spec["style"])
        self.assertEqual("pipeline", spec["preset"])
        self.assertEqual("teaching", spec["motion"]["profile"])
        self.assertEqual(
            {"value": "illustrated", "version": "2.3.0", "source": "explicit"},
            spec["resolved_presentation"]["icon_system"],
        )

    def test_v02_legacy_illustrated_v2_id_resolves_to_versioned_illustrated_identity(self):
        plan = self._plan()
        plan["presentation"]["icon_system"] = "illustrated-character-v2"

        spec = compile_plan(plan)

        self.assertEqual("illustrated", spec["icon_system"])
        self.assertEqual(
            {"value": "illustrated", "version": "2.3.0", "source": "explicit"},
            spec["resolved_presentation"]["icon_system"],
        )

    def test_v02_illustrated_prefers_new_exact_kind_mappings(self):
        plan = self._plan()
        plan["presentation"]["icon_system"] = "illustrated"
        kinds = ("database", "api", "search", "memory")
        for entity, kind in zip(plan["semantic"]["entities"], kinds):
            entity["kind"] = kind

        spec = compile_plan(plan)

        self.assertEqual(kinds, tuple(node["icon"] for node in spec["nodes"]))

    def test_v04_rejects_stale_illustrated_version_instead_of_silently_rendering_current(self):
        plan = self._plan()
        plan["presentation"]["icon_system"] = "illustrated"
        spec = compile_plan(plan)
        spec["resolved_presentation"]["icon_system"]["version"] = "2.0.0"

        with self.assertRaisesRegex(
            DiagramScriptValidationError,
            "not renderable by the current illustrated 2.3.0 runtime",
        ):
            compile_scene(spec)

    def test_v02_records_model_selected_style_and_layout(self):
        plan = self._plan()
        plan["presentation"]["style"] = "deep-tech"
        plan["presentation"]["layout"] = "pipeline"
        plan["presentation_sources"] = {"style": "model", "layout": "model"}

        spec = compile_plan(plan)

        self.assertEqual({"value": "deep-tech", "source": "model"}, spec["resolved_presentation"]["style"])
        self.assertEqual({"value": "pipeline", "source": "model"}, spec["resolved_presentation"]["layout"])

    def test_v02_true_presentation_omission_uses_composition_defaults(self):
        plan = self._plan()
        plan["presentation"] = {}

        spec = compile_plan(plan)

        self.assertEqual(
            {
                "icon_system": {"value": "diagram-core-v1", "source": "default"},
                "style": {"value": "minimal-light", "source": "fallback"},
                "layout": {"value": "layered", "source": "fallback"},
                "motion": {"value": "showcase-v1", "source": "default"},
            },
            spec["resolved_presentation"],
        )
        self.assertEqual("showcase-v1", spec["motion"]["profile"])
        self.assertEqual("unrestricted", spec["motion_policy"]["profile"])

    def test_direct_v04_omission_retains_manual_authoring_compatibility_defaults(self):
        scene = compile_scene(
            {
                "version": "0.4",
                "nodes": [
                    {
                        "id": "agent",
                        "position": [40, 40],
                        "size": [180, 96],
                        "icon": "agent",
                    }
                ],
            }
        )

        self.assertIsNone(scene.composition_policy)
        self.assertEqual("diagram-core-v1", scene.icon_system)
        self.assertEqual("expressive", scene.motion.profile)
        self.assertEqual("unrestricted", scene.motion_policy.profile)

    def test_v02_rejects_dangling_semantic_relation(self):
        plan = self._plan()
        plan["semantic"]["relations"][0]["to"] = "missing-node"

        with self.assertRaisesRegex(ValueError, "missing-node"):
            compile_plan(plan)

    def test_v02_rejects_renderer_fields_inside_semantic_content(self):
        plan = self._plan()
        plan["semantic"]["entities"][0]["position"] = [10, 20]

        with self.assertRaisesRegex(ValueError, "position"):
            compile_plan(plan)

    def test_v02_preserves_relation_direction_through_rendering(self):
        plan = self._plan()
        plan["semantic"]["relations"][0]["direction"] = "bidirectional"
        scene = compile_scene(compile_plan(plan))
        svg = render_svg(scene, load_style())

        self.assertEqual("bidirectional", scene.edges[0].direction)
        self.assertIn('marker-start="url(#arrow-1)" marker-end="url(#arrow-1)"', svg)

    def test_cli_accepts_plan_and_writes_compiled_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec_path = Path(tmp) / "production.diagram.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(
                    [
                        "--plan",
                        str(ROOT / "examples" / "contracts" / "production-request-path.plan.json"),
                        "--outdir",
                        tmp,
                        "--basename",
                        "production",
                        "--formats",
                        "svg,quality",
                        "--spec-out",
                        str(spec_path),
                    ]
                )

            result = json.loads(stdout.getvalue())
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            self.assertTrue(result["ok"])
            self.assertEqual("plan", result["source"])
            self.assertEqual({"name": "DiagramPlan", "version": "0.2"}, result["plan"]["schema"])
            self.assertEqual("diagram-core-v1", result["icon_system"])
            self.assertEqual("0.4", spec["version"])
            self.assertEqual(0, result["outputs"]["quality"]["summary"]["errors"])

    def test_all_56_approved_core_icons_render_and_receive_showcase_motion(self):
        icon_ids = sorted(DIAGRAM_CORE_ICONS)
        spec = {
            "version": "0.4",
            "icon_system": "diagram-core-v1",
            "canvas": {"width": 1280, "height": 1320},
            "title": {"text": "Diagram Core registry"},
            "motion": {"profile": "showcase-v1"},
            "nodes": [
                {
                    "id": f"core-{icon_id}",
                    "label": icon_id,
                    "position": [25 + (index % 6) * 205, 105 + (index // 6) * 120],
                    "size": [190, 100],
                    "role": "neutral",
                    "icon": icon_id,
                    "effect": {"preset": "icon-performance"},
                }
                for index, icon_id in enumerate(icon_ids)
            ],
        }
        scene = compile_scene(spec)
        svg = render_svg(scene, load_style())
        manifest = build_motion_manifest(scene, load_style())

        self.assertEqual(56, len(icon_ids))
        self.assertEqual(set(icon_ids), set(approved_icon_ids()))
        self.assertEqual(56, svg.count('data-icon-source="diagram-core-v1"'))
        self.assertEqual(56, len(manifest["icons"]))
        self.assertEqual(set(icon_ids), {entry["icon"] for entry in manifest["icons"]})


if __name__ == "__main__":
    unittest.main()
