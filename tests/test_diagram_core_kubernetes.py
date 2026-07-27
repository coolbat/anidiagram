import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets" / "diagram-core"
RELEASE_PATH = ASSET_ROOT / "releases" / "v1.0.0.json"
SPEC_PATH = ROOT / "examples" / "diagram-core" / "kubernetes-production.json"
SCRIPT_PATH = ROOT / "scripts" / "render_diagram_core_kubernetes.py"
COMMITTED_OUTPUT = ROOT / "gallery" / "diagram-core" / "kubernetes-production.html"
DEEP_TECH_OUTPUT = ROOT / "gallery" / "diagram-core" / "kubernetes-production-deep-tech.html"


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _asset_tree_sha256():
    digest = hashlib.sha256()
    paths = sorted((ASSET_ROOT / "icons").glob("*.svg")) + sorted(
        (ASSET_ROOT / "manifests").glob("*.json")
    )
    for path in paths:
        relative = path.relative_to(ROOT).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _motion_manifest(source):
    marker = '<script type="application/json" id="anidiagram-motion-manifest">'
    start = source.index(marker) + len(marker)
    return json.loads(source[start : source.index("</script>", start)])


def _contrast_ratio(first, second):
    def luminance(color):
        channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


class DiagramCoreKubernetesTests(unittest.TestCase):
    def _run_generator(self, output, style=None):
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT / "src")
        command = [
            sys.executable,
            str(SCRIPT_PATH),
            "--spec",
            str(SPEC_PATH),
            "--output",
            str(output),
        ]
        if style is not None:
            command.extend(("--style", style))
        return subprocess.run(
            command,
            cwd=str(ROOT),
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_v1_release_lock_freezes_the_current_icon_and_motion_sources(self):
        self.assertTrue(RELEASE_PATH.is_file(), "Diagram Core v1.0.0 release lock is missing")
        release = json.loads(RELEASE_PATH.read_text(encoding="utf-8"))

        self.assertEqual("diagram-core-v1", release["system"])
        self.assertEqual("1.0.0", release["version"])
        self.assertEqual("frozen", release["status"])
        self.assertEqual("confirmed", release["human_visual_acceptance"])
        self.assertEqual(56, release["icon_count"])
        self.assertFalse(release["default_icon_system_changed"])
        self.assertEqual(_sha256(ASSET_ROOT / "catalog.json"), release["hashes"]["catalog_sha256"])
        self.assertEqual(_sha256(ASSET_ROOT / "tokens.css"), release["hashes"]["tokens_sha256"])
        self.assertEqual(
            _sha256(ROOT / "runtime" / "motion-catalog.json"),
            release["hashes"]["motion_catalog_sha256"],
        )
        self.assertEqual(_asset_tree_sha256(), release["hashes"]["asset_tree_sha256"])

    def test_kubernetes_spec_uses_the_frozen_system_and_a_focused_three_plane_story(self):
        self.assertTrue(SPEC_PATH.is_file(), "Kubernetes Diagram Core spec is missing")
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        node_ids = tuple(node["id"] for node in spec["nodes"])
        icons = {node["icon"] for node in spec["nodes"]}
        edge_count = len(spec["edges"])

        self.assertEqual("diagram-core-v1", spec["icon_system"])
        self.assertEqual("1.0.0", spec["diagram_core_release"])
        self.assertEqual("diagram-core-light", spec["style"])
        self.assertEqual((1600, 900), (spec["canvas"]["width"], spec["canvas"]["height"]))
        self.assertEqual(len(node_ids), len(set(node_ids)))
        self.assertGreaterEqual(len(node_ids), 18)
        self.assertTrue(
            {
                "developer",
                "git-repository",
                "ci-cd",
                "container",
                "user",
                "api",
                "scheduler",
                "agent-team",
                "database",
                "gateway",
                "load-balancer",
                "deployment",
                "message-queue",
                "monitoring",
                "logs",
                "alert",
            }.issubset(icons)
        )
        self.assertTrue(
            {"delivery", "cluster", "control-plane", "workload-plane", "observability"}.issubset(
                {group["id"] for group in spec["groups"]}
            )
        )
        self.assertEqual(node_ids, tuple(spec["motion"]["animated_nodes"]))
        self.assertEqual(list(range(edge_count)), spec["motion"]["active_edge_indices"])
        self.assertEqual([3, 18], spec["motion"]["labeled_edge_indices"])
        self.assertEqual(2, len(spec["motion"]["readable_edge_indices"]))

    def test_generator_produces_a_self_contained_frozen_diagram_core_runtime(self):
        with tempfile.TemporaryDirectory(dir=str(ROOT / "build")) as directory:
            output = Path(directory) / "kubernetes-production.html"
            completed = self._run_generator(output)
            self.assertEqual(0, completed.returncode, completed.stderr)
            source = output.read_text(encoding="utf-8")

        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        manifest = _motion_manifest(source)
        self.assertEqual(len(spec["nodes"]), source.count('data-architecture-node="'))
        self.assertEqual(len(spec["nodes"]), source.count('data-icon-source="diagram-core-v1"'))
        self.assertEqual(len(spec["nodes"]), source.count('data-icon-presentation="showcase"'))
        self.assertEqual("diagram-core-v1", manifest["icon_system"])
        self.assertEqual("1.0.0", manifest["diagram_core_release"])
        self.assertEqual("diagram-core-light", manifest["style"])
        self.assertIn('data-template-style="diagram-core-light"', source)
        self.assertRegex(
            source,
            r'<text id="diagram-title"[^>]*>Kubernetes Production Architecture</text>',
        )
        self.assertRegex(
            source,
            r'<text id="diagram-summary"[^>]*>All nodes alive · all data paths flowing</text>',
        )
        self.assertEqual(len(spec["motion"]["animated_nodes"]), len(manifest["icons"]))
        self.assertEqual(spec["motion"]["active_edge_indices"], manifest["stage"]["active_edge_indices"])
        self.assertEqual(spec["motion"]["readable_edge_indices"], manifest["stage"]["readable_edge_indices"])
        self.assertIn('id="motion-expressive"', source)
        self.assertIn('id="motion-readable"', source)
        self.assertIn('id="motion-off"', source)
        self.assertIn('has("no-gsap")', source)
        self.assertNotIn("<script src=", source)
        self.assertIsNone(re.search(r'(?:src|href)=["\']https?://', source))
        self.assertEqual(source, COMMITTED_OUTPUT.read_text(encoding="utf-8"))

    def test_generator_produces_a_deep_tech_variant_from_the_same_architecture(self):
        with tempfile.TemporaryDirectory(dir=str(ROOT / "build")) as directory:
            output = Path(directory) / "kubernetes-production-deep-tech.html"
            completed = self._run_generator(output, style="deep-tech")
            self.assertEqual(0, completed.returncode, completed.stderr)
            source = output.read_text(encoding="utf-8")

        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        manifest = _motion_manifest(source)
        self.assertEqual("deep-tech", manifest["style"])
        self.assertIn('data-template-style="deep-tech"', source)
        self.assertIn('<meta name="color-scheme" content="dark">', source)
        self.assertIn('<rect width="1600" height="900" fill="#050816"/>', source)
        self.assertIn("--icon-surface-main:#202838", source)
        self.assertIn("--icon-accent:#65d8ff", source)
        self.assertIn('data-node-domain="delivery"', source)
        self.assertIn('data-node-domain="control-plane"', source)
        self.assertIn('data-node-domain="workload-plane"', source)
        self.assertIn('data-node-domain="observability"', source)
        self.assertIn('stroke="#a78bfa"', source)
        self.assertIn('stroke="#60a5fa"', source)
        self.assertIn('stroke="#34d399"', source)
        self.assertIn('stroke="#fb7185"', source)
        self.assertIn('id="arrow-delivery"', source)
        self.assertIn('id="arrow-control-plane"', source)
        self.assertIn('id="arrow-workload-plane"', source)
        self.assertIn('id="arrow-observability"', source)
        self.assertEqual(
            {"delivery", "control-plane", "workload-plane", "observability"},
            {edge["color_role"] for edge in manifest["edges"]},
        )
        node_color_pairs = re.findall(
            r'<g class="architecture-node[^>]*>\s*<rect[^>]*fill="(#[0-9a-f]{6})" stroke="(#[0-9a-f]{6})"',
            source,
        )
        self.assertEqual(len(spec["nodes"]), len(node_color_pairs))
        self.assertTrue(
            all(_contrast_ratio(fill, stroke) >= 3 for fill, stroke in node_color_pairs),
            "deep-tech semantic node borders must retain at least 3:1 contrast",
        )
        self.assertEqual(len(spec["nodes"]), source.count('data-architecture-node="'))
        self.assertEqual(len(spec["nodes"]), len(manifest["icons"]))
        self.assertEqual(len(spec["edges"]), len(manifest["stage"]["active_edge_indices"]))
        self.assertNotIn("diagram-core-light · Frozen", source)
        self.assertNotIn("<script src=", source)
        self.assertIsNone(re.search(r'(?:src|href)=["\']https?://', source))
        self.assertEqual(source, DEEP_TECH_OUTPUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
