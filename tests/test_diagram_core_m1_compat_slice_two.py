import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from anidiagram.diagram_core.asset_loader import load_asset
from anidiagram.diagram_core.catalog import catalog_entry


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets" / "diagram-core"
ICON_IDS = ("file", "folder", "output", "shield", "cloud")

EXPECTED = {
    "file": {
        "prototype": "folded-file-card",
        "parts": (
            "body",
            "sheet",
            "fold",
            "content-line-top",
            "content-line-bottom",
            "indicator",
        ),
        "actions": ("receive", "open", "read", "send"),
        "semantic_parts": {"sheet", "fold"},
    },
    "folder": {
        "prototype": "tabbed-file-folder",
        "parts": ("body", "shell", "tab", "file-card", "file-line", "indicator"),
        "actions": ("receive", "open", "store", "send"),
        "semantic_parts": {"tab", "file-card"},
    },
    "output": {
        "prototype": "delivery-output-card",
        "parts": ("body", "shell", "card", "send-path", "check", "indicator"),
        "actions": ("receive", "reveal", "deliver", "send"),
        "semantic_parts": {"card", "send-path", "check"},
    },
    "shield": {
        "prototype": "scanning-security-shield",
        "parts": ("body", "shell", "scan", "core", "check"),
        "actions": ("receive", "scan", "validate", "send"),
        "semantic_parts": {"scan", "core", "check"},
    },
    "cloud": {
        "prototype": "modular-cloud-runtime",
        "parts": (
            "body",
            "cloud-shell",
            "module-left",
            "module-center",
            "module-right",
            "signal",
            "indicator",
        ),
        "actions": ("receive", "sync", "process", "send"),
        "semantic_parts": {
            "cloud-shell",
            "module-left",
            "module-center",
            "module-right",
            "signal",
        },
    },
}

PAINTABLE_TAGS = {
    "circle",
    "ellipse",
    "line",
    "path",
    "polygon",
    "polyline",
    "rect",
}


def local_name(name):
    return name.rsplit("}", 1)[-1]


class DiagramCoreM1CompatSliceTwoTest(unittest.TestCase):
    def test_catalog_and_manifests_promote_the_five_icons_atomically(self):
        for icon_id in ICON_IDS:
            with self.subTest(icon_id=icon_id):
                expected = EXPECTED[icon_id]
                entry = catalog_entry(icon_id)
                manifest = json.loads(
                    (ASSET_ROOT / "manifests" / (icon_id + ".json")).read_text(
                        encoding="utf-8"
                    )
                )

                self.assertEqual("visual-review", entry.status)
                self.assertEqual(1, entry.asset_revision)
                self.assertEqual(expected["prototype"], entry.structural_prototype)
                self.assertEqual(expected["parts"], entry.parts)
                self.assertEqual((), entry.supported_states)
                self.assertEqual(expected["actions"], entry.supported_actions)
                self.assertEqual(icon_id, manifest["id"])
                self.assertEqual("diagram-core-v1", manifest["system"])
                self.assertEqual("0 0 96 96", manifest["viewBox"])
                self.assertEqual(1, manifest["asset_revision"])
                self.assertEqual(expected["prototype"], manifest["structural_prototype"])
                self.assertEqual(list(expected["parts"]), manifest["parts"])
                self.assertEqual([], manifest["states"])
                self.assertEqual(list(expected["actions"]), manifest["actions"])
                self.assertEqual("visual-review", manifest["status"])

    def test_canonical_svgs_are_compact_shared_style_and_semantically_legible(self):
        required_shared_tokens = {
            "--icon-surface-main",
            "--icon-stroke",
            "--icon-accent-secondary",
        }
        for icon_id in ICON_IDS:
            with self.subTest(icon_id=icon_id):
                expected = EXPECTED[icon_id]
                asset = load_asset(icon_id, allow_statuses={"visual-review"})
                root = asset.root
                source = asset.svg_source
                public_parts = tuple(
                    element.attrib["data-part"]
                    for element in root.iter()
                    if "data-part" in element.attrib
                )
                paintables = [
                    element
                    for element in root.iter()
                    if local_name(element.tag) in PAINTABLE_TAGS
                ]

                self.assertEqual("0 0 96 96", root.attrib["viewBox"])
                self.assertEqual(icon_id, root.attrib["data-icon"])
                self.assertEqual(expected["parts"], public_parts)
                self.assertTrue(expected["semantic_parts"].issubset(public_parts))
                self.assertLessEqual(len(paintables), 24)
                self.assertGreaterEqual(len(paintables), 7)
                self.assertLessEqual(asset.metrics.raw_size_bytes, 12 * 1024)
                self.assertLessEqual(asset.metrics.gzip_size_bytes, 6 * 1024)
                self.assertTrue(all(token in source for token in required_shared_tokens))
                self.assertNotIn("data-icon-state", source)
                self.assertNotIn("data-state-mark", source)
                self.assertNotIn("--icon-status-success", source)
                for element in paintables:
                    stroke = element.attrib.get("stroke", "none")
                    if stroke != "none":
                        self.assertIn(
                            element.attrib.get("stroke-width"),
                            {"1.375", "2.125"},
                        )

    def test_motion_catalog_declares_safe_authored_rest_showcase_recipes(self):
        motion_catalog = json.loads(
            (ROOT / "runtime" / "motion-catalog.json").read_text(encoding="utf-8")
        )
        definitions = {
            item["icon"]: item
            for item in motion_catalog["diagram_core_presentations"]
            if item["icon"] in ICON_IDS
        }

        self.assertEqual(set(ICON_IDS), set(definitions))
        for icon_id in ICON_IDS:
            with self.subTest(icon_id=icon_id):
                definition = definitions[icon_id]
                tracks = definition["recipe"]["tracks"]
                targets = tuple(part for track in tracks for part in track["parts"])

                self.assertEqual(icon_id + ".showcase-loop-v1", definition["id"])
                self.assertEqual(icon_id + "-showcase-loop-v1", definition["runtime_id"])
                self.assertEqual("presentation", definition["kind"])
                self.assertEqual("showcase", definition["profile"])
                self.assertEqual("diagram-core-v1", definition["icon_system"])
                self.assertEqual("authored-rest-pose", definition["rest_pose"])
                self.assertEqual("scene-controlled", definition["repeat_policy"])
                self.assertEqual("restore-rest-pose", definition["cancel_behavior"])
                self.assertEqual("static-rest", definition["reduced_motion_behavior"])
                self.assertEqual("visual-review", definition["status"])
                self.assertTrue(1600 <= definition["duration_ms"] <= 2400)
                self.assertTrue(0.8 <= definition["repeat_delay"] <= 1.4)
                self.assertTrue(3 <= len(set(targets)) <= 5)
                self.assertEqual(len(targets), len(set(targets)))
                self.assertTrue(set(targets).issubset(definition["required_parts"]))
                self.assertTrue(
                    set(definition["required_parts"]).issubset(EXPECTED[icon_id]["parts"])
                )
                for track in tracks:
                    self.assertEqual(1, len(track["parts"]))
                    self.assertGreaterEqual(len(track["steps"]), 2)
                    for step in track["steps"]:
                        for name, value in step["to"].items():
                            if name in {"x", "y"}:
                                self.assertLessEqual(abs(value), 8)
                            elif name == "rotate":
                                self.assertLessEqual(abs(value), 12)
                            elif name in {"scale", "scaleX", "scaleY"}:
                                self.assertTrue(0.88 <= value <= 1.4)
                    final = track["steps"][-1]
                    self.assertLessEqual(
                        final["at"] + final["duration"], definition["rest_at"]
                    )
                    self.assertTrue(
                        all(value in (0, 1) for value in final["to"].values()),
                        "the final authored step must restore the neutral rest pose",
                    )

    def test_shield_check_is_capability_not_a_success_state(self):
        manifest = json.loads(
            (ASSET_ROOT / "manifests" / "shield.json").read_text(encoding="utf-8")
        )
        source = (ASSET_ROOT / "icons" / "shield.svg").read_text(encoding="utf-8")

        self.assertEqual([], manifest["states"])
        self.assertIn('data-part="check"', source)
        self.assertNotIn("success", source.lower())
        self.assertNotIn("data-state", source)

    def test_review_validator_includes_the_five_assets_without_inventory_drift(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_diagram_core_assets.py"),
                "--review",
                "--json",
            ],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertTrue(set(ICON_IDS).issubset(report["paintable_elements_by_icon"]))
        self.assertEqual(report["visual_review"], report["svg"])
        self.assertEqual(report["visual_review"], report["manifests"])
        self.assertEqual(56, report["visual_review"] + report["planned"])
        self.assertEqual(0, report["errors"])


if __name__ == "__main__":
    unittest.main()
