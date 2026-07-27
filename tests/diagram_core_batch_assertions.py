import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from anidiagram.diagram_core.asset_loader import load_asset
from anidiagram.diagram_core.catalog import catalog_entry


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets" / "diagram-core"
PAINTABLE_TAGS = {"circle", "ellipse", "line", "path", "polygon", "polyline", "rect"}


def local_name(name):
    return name.rsplit("}", 1)[-1]


def assert_catalog_and_manifests(testcase, expected):
    for icon_id, contract in expected.items():
        with testcase.subTest(icon_id=icon_id):
            entry = catalog_entry(icon_id)
            manifest = json.loads(
                (ASSET_ROOT / "manifests" / f"{icon_id}.json").read_text(
                    encoding="utf-8"
                )
            )
            testcase.assertEqual("visual-review", entry.status)
            testcase.assertEqual(1, entry.asset_revision)
            testcase.assertEqual(contract["prototype"], entry.structural_prototype)
            testcase.assertEqual(contract["parts"], entry.parts)
            testcase.assertEqual((), entry.supported_states)
            testcase.assertEqual(contract["actions"], entry.supported_actions)
            testcase.assertEqual(icon_id, manifest["id"])
            testcase.assertEqual("diagram-core-v1", manifest["system"])
            testcase.assertEqual("0 0 96 96", manifest["viewBox"])
            testcase.assertEqual(1, manifest["asset_revision"])
            testcase.assertEqual(contract["prototype"], manifest["structural_prototype"])
            testcase.assertEqual(list(contract["parts"]), manifest["parts"])
            testcase.assertEqual([], manifest["states"])
            testcase.assertEqual(list(contract["actions"]), manifest["actions"])
            testcase.assertEqual("visual-review", manifest["status"])


def assert_svg_contract(testcase, expected):
    prototypes = set()
    signatures = set()
    for icon_id, contract in expected.items():
        with testcase.subTest(icon_id=icon_id):
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
            prototypes.add(contract["prototype"])
            signatures.add(parts)
            testcase.assertEqual("0 0 96 96", asset.root.attrib["viewBox"])
            testcase.assertEqual(icon_id, asset.root.attrib["data-icon"])
            testcase.assertEqual(contract["parts"], parts)
            testcase.assertTrue(
                all(
                    token in source
                    for token in (
                        "--icon-surface-main",
                        "--icon-stroke",
                        "--icon-accent-secondary",
                    )
                )
            )
            testcase.assertNotIn("<text", source)
            testcase.assertNotIn("data-icon-state", source)
            testcase.assertNotIn("data-state-mark", source)
            testcase.assertGreaterEqual(len(paintables), 7)
            testcase.assertLessEqual(len(paintables), 24)
            testcase.assertLessEqual(asset.metrics.raw_size_bytes, 12 * 1024)
            testcase.assertLessEqual(asset.metrics.gzip_size_bytes, 6 * 1024)
            for element in paintables:
                stroke = element.attrib.get("stroke", "none")
                if stroke != "none":
                    testcase.assertIn(
                        element.attrib.get("stroke-width"), {"1.375", "2.125"}
                    )
    testcase.assertEqual(len(expected), len(prototypes))
    testcase.assertEqual(len(expected), len(signatures))


def assert_motion_contract(testcase, expected):
    catalog = json.loads(
        (ROOT / "runtime" / "motion-catalog.json").read_text(encoding="utf-8")
    )
    definitions = {
        item["icon"]: item
        for item in catalog["diagram_core_presentations"]
        if item["icon"] in expected
    }
    testcase.assertEqual(set(expected), set(definitions))
    for icon_id, definition in definitions.items():
        with testcase.subTest(icon_id=icon_id):
            tracks = definition["recipe"]["tracks"]
            targets = tuple(part for track in tracks for part in track["parts"])
            testcase.assertEqual(f"{icon_id}.showcase-loop-v1", definition["id"])
            testcase.assertEqual(f"{icon_id}-showcase-loop-v1", definition["runtime_id"])
            testcase.assertEqual("presentation", definition["kind"])
            testcase.assertEqual("showcase", definition["profile"])
            testcase.assertEqual("visual-review", definition["status"])
            testcase.assertEqual("authored-rest-pose", definition["rest_pose"])
            testcase.assertEqual("scene-controlled", definition["repeat_policy"])
            testcase.assertEqual("restore-rest-pose", definition["cancel_behavior"])
            testcase.assertEqual("static-rest", definition["reduced_motion_behavior"])
            testcase.assertTrue(1600 <= definition["duration_ms"] <= 2400)
            testcase.assertTrue(0.8 <= definition["repeat_delay"] <= 1.4)
            testcase.assertTrue(3 <= len(targets) <= 5)
            testcase.assertEqual(len(targets), len(set(targets)))
            testcase.assertTrue(set(targets).issubset(definition["required_parts"]))
            testcase.assertTrue(
                set(definition["required_parts"]).issubset(expected[icon_id]["parts"])
            )
            for track in tracks:
                testcase.assertEqual(1, len(track["parts"]))
                testcase.assertGreaterEqual(len(track["steps"]), 2)
                for step in track["steps"]:
                    for name, value in step["to"].items():
                        if name in {"x", "y"}:
                            testcase.assertLessEqual(abs(value), 8)
                        elif name == "rotate":
                            testcase.assertLessEqual(abs(value), 12)
                        elif name in {"scale", "scaleX", "scaleY"}:
                            testcase.assertTrue(0.88 <= value <= 1.4)
                final = track["steps"][-1]
                testcase.assertLessEqual(
                    final["at"] + final["duration"], definition["rest_at"]
                )
                testcase.assertTrue(
                    all(value in (0, 1) for value in final["to"].values())
                )


def assert_baseline_stable(testcase, icon_id, svg_hash, manifest_hash, motion_hash):
    svg = (ASSET_ROOT / "icons" / f"{icon_id}.svg").read_bytes()
    manifest = (ASSET_ROOT / "manifests" / f"{icon_id}.json").read_bytes()
    catalog = json.loads(
        (ROOT / "runtime" / "motion-catalog.json").read_text(encoding="utf-8")
    )
    motion = next(
        item
        for item in catalog["diagram_core_presentations"]
        if item["icon"] == icon_id
    )
    testcase.assertEqual(svg_hash, hashlib.sha256(svg).hexdigest())
    testcase.assertEqual(manifest_hash, hashlib.sha256(manifest).hexdigest())
    testcase.assertEqual(
        motion_hash, hashlib.sha256(json.dumps(motion).encode()).hexdigest()
    )


def assert_review_inventory(testcase, expected, minimum_implemented):
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
    testcase.assertEqual(0, completed.returncode, completed.stderr)
    report = json.loads(completed.stdout)
    testcase.assertTrue(set(expected).issubset(report["paintable_elements_by_icon"]))
    testcase.assertGreaterEqual(report["visual_review"], minimum_implemented)
    testcase.assertEqual(report["visual_review"], report["svg"])
    testcase.assertEqual(report["visual_review"], report["manifests"])
    testcase.assertEqual(56, report["visual_review"] + report["planned"])
    testcase.assertEqual(0, report["errors"])
