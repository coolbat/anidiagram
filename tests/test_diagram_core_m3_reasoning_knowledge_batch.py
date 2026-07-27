import hashlib
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
ICON_IDS = (
    "neural-network",
    "reasoning",
    "embedding",
    "vector-database",
    "data-warehouse",
    "knowledge-base",
    "dataset",
)

EXPECTED = {
    "neural-network": (
        "layered-neural-network",
        ("body", "shell", "layer-a", "layer-b", "layer-c", "signal", "indicator"),
        ("receive", "propagate", "activate", "send"),
    ),
    "reasoning": (
        "branching-reasoning-path",
        ("body", "shell", "premise", "path", "branch", "result", "indicator"),
        ("receive", "decompose", "decide", "send"),
    ),
    "embedding": (
        "vector-mapping-space",
        ("body", "input-card", "coordinate-space", "points", "vector", "projection", "indicator"),
        ("receive", "map", "embed", "send"),
    ),
    "vector-database": (
        "vector-index-vault",
        ("body", "shell", "layers", "points", "scanner", "indicator"),
        ("receive", "index", "search", "send"),
    ),
    "data-warehouse": (
        "aggregated-data-warehouse",
        ("body", "shell", "roof", "bins", "door", "indicator"),
        ("receive", "aggregate", "store", "send"),
    ),
    "knowledge-base": (
        "linked-knowledge-cards",
        ("body", "card-left", "card-center", "card-right", "links", "core", "indicator"),
        ("receive", "organize", "retrieve", "send"),
    ),
    "dataset": (
        "mixed-card-container",
        ("body", "container", "cards", "filter", "record", "indicator"),
        ("receive", "filter", "sample", "send"),
    ),
}

PAINTABLE_TAGS = {"circle", "ellipse", "line", "path", "polygon", "polyline", "rect"}


def local_name(name):
    return name.rsplit("}", 1)[-1]


class DiagramCoreM3ReasoningKnowledgeBatchTest(unittest.TestCase):
    def test_catalog_and_manifests_promote_exactly_the_frozen_batch(self):
        for icon_id in ICON_IDS:
            with self.subTest(icon_id=icon_id):
                prototype, parts, actions = EXPECTED[icon_id]
                entry = catalog_entry(icon_id)
                manifest = json.loads(
                    (ASSET_ROOT / "manifests" / f"{icon_id}.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual("visual-review", entry.status)
                self.assertEqual(1, entry.asset_revision)
                self.assertEqual(prototype, entry.structural_prototype)
                self.assertEqual(parts, entry.parts)
                self.assertEqual((), entry.supported_states)
                self.assertEqual(actions, entry.supported_actions)
                self.assertEqual(icon_id, manifest["id"])
                self.assertEqual("diagram-core-v1", manifest["system"])
                self.assertEqual("0 0 96 96", manifest["viewBox"])
                self.assertEqual(1, manifest["asset_revision"])
                self.assertEqual(prototype, manifest["structural_prototype"])
                self.assertEqual(list(parts), manifest["parts"])
                self.assertEqual([], manifest["states"])
                self.assertEqual(list(actions), manifest["actions"])
                self.assertEqual("visual-review", manifest["status"])

    def test_svgs_are_compact_shared_style_non_text_and_distinct(self):
        prototypes = set()
        part_signatures = set()
        for icon_id in ICON_IDS:
            with self.subTest(icon_id=icon_id):
                prototype, expected_parts, _ = EXPECTED[icon_id]
                asset = load_asset(icon_id, allow_statuses={"visual-review"})
                source = asset.svg_source
                parts = tuple(
                    element.attrib["data-part"]
                    for element in asset.root.iter()
                    if "data-part" in element.attrib
                )
                paintables = [
                    element
                    for element in asset.root.iter()
                    if local_name(element.tag) in PAINTABLE_TAGS
                ]
                prototypes.add(prototype)
                part_signatures.add(parts)
                self.assertEqual("0 0 96 96", asset.root.attrib["viewBox"])
                self.assertEqual(icon_id, asset.root.attrib["data-icon"])
                self.assertEqual(expected_parts, parts)
                self.assertTrue(
                    all(
                        token in source
                        for token in (
                            "--icon-surface-main",
                            "--icon-stroke",
                            "--icon-accent-secondary",
                        )
                    )
                )
                self.assertNotIn("<text", source)
                self.assertNotIn("data-icon-state", source)
                self.assertNotIn("data-state-mark", source)
                self.assertGreaterEqual(len(paintables), 7)
                self.assertLessEqual(len(paintables), 24)
                self.assertLessEqual(asset.metrics.raw_size_bytes, 12 * 1024)
                self.assertLessEqual(asset.metrics.gzip_size_bytes, 6 * 1024)
                for element in paintables:
                    stroke = element.attrib.get("stroke", "none")
                    if stroke != "none":
                        self.assertIn(element.attrib.get("stroke-width"), {"1.375", "2.125"})
        self.assertEqual(7, len(prototypes))
        self.assertEqual(7, len(part_signatures))

    def test_semantic_parts_preserve_the_prd_identity_contract(self):
        parts = {icon_id: set(EXPECTED[icon_id][1]) for icon_id in ICON_IDS}
        self.assertTrue({"layer-a", "layer-b", "layer-c", "signal"}.issubset(parts["neural-network"]))
        self.assertTrue({"premise", "branch", "result"}.issubset(parts["reasoning"]))
        self.assertTrue({"input-card", "coordinate-space", "points", "vector"}.issubset(parts["embedding"]))
        self.assertTrue({"layers", "points", "scanner"}.issubset(parts["vector-database"]))
        self.assertTrue({"roof", "bins", "door"}.issubset(parts["data-warehouse"]))
        self.assertTrue({"card-left", "card-center", "card-right", "links", "core"}.issubset(parts["knowledge-base"]))
        self.assertTrue({"container", "cards", "filter", "record"}.issubset(parts["dataset"]))

    def test_motion_catalog_declares_bounded_authored_rest_recipes(self):
        catalog = json.loads((ROOT / "runtime" / "motion-catalog.json").read_text(encoding="utf-8"))
        definitions = {
            item["icon"]: item
            for item in catalog["diagram_core_presentations"]
            if item["icon"] in ICON_IDS
        }
        self.assertEqual(set(ICON_IDS), set(definitions))
        for icon_id, definition in definitions.items():
            with self.subTest(icon_id=icon_id):
                tracks = definition["recipe"]["tracks"]
                targets = tuple(part for track in tracks for part in track["parts"])
                self.assertEqual(f"{icon_id}.showcase-loop-v1", definition["id"])
                self.assertEqual(f"{icon_id}-showcase-loop-v1", definition["runtime_id"])
                self.assertEqual("presentation", definition["kind"])
                self.assertEqual("showcase", definition["profile"])
                self.assertEqual("visual-review", definition["status"])
                self.assertEqual("authored-rest-pose", definition["rest_pose"])
                self.assertEqual("scene-controlled", definition["repeat_policy"])
                self.assertEqual("restore-rest-pose", definition["cancel_behavior"])
                self.assertEqual("static-rest", definition["reduced_motion_behavior"])
                self.assertTrue(1600 <= definition["duration_ms"] <= 2400)
                self.assertTrue(0.8 <= definition["repeat_delay"] <= 1.4)
                self.assertTrue(3 <= len(targets) <= 5)
                self.assertEqual(len(targets), len(set(targets)))
                self.assertTrue(set(targets).issubset(definition["required_parts"]))
                self.assertTrue(set(definition["required_parts"]).issubset(EXPECTED[icon_id][1]))
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
                    self.assertLessEqual(final["at"] + final["duration"], definition["rest_at"])
                    self.assertTrue(all(value in (0, 1) for value in final["to"].values()))

    def test_database_benchmark_remains_stable(self):
        svg = (ASSET_ROOT / "icons" / "database.svg").read_bytes()
        manifest = (ASSET_ROOT / "manifests" / "database.json").read_bytes()
        catalog = json.loads((ROOT / "runtime" / "motion-catalog.json").read_text(encoding="utf-8"))
        motion = next(item for item in catalog["diagram_core_presentations"] if item["icon"] == "database")
        self.assertEqual("c9e5a61893711f2a7234ef6757ca99544e3eb126d79ee5f9df4b763d42c7d4b7", hashlib.sha256(svg).hexdigest())
        self.assertEqual("f8d76365934c0891ac44ce7363bb5149f620f4e026798438e485a14b0ba06939", hashlib.sha256(manifest).hexdigest())
        self.assertEqual("5b3146889c323cabe7ad7b9286924f820ee9da01f6add00f085a39ea882ad885", hashlib.sha256(json.dumps(motion).encode()).hexdigest())

    def test_review_validator_includes_the_batch_without_inventory_drift(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_diagram_core_assets.py"), "--review", "--json"],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertTrue(set(ICON_IDS).issubset(report["paintable_elements_by_icon"]))
        self.assertGreaterEqual(report["visual_review"], 28)
        self.assertEqual(report["visual_review"], report["svg"])
        self.assertEqual(report["visual_review"], report["manifests"])
        self.assertEqual(56, report["visual_review"] + report["planned"])
        self.assertEqual(0, report["errors"])


if __name__ == "__main__":
    unittest.main()
