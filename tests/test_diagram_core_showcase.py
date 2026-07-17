import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHOWCASE_ICONS = ("agent", "database", "api", "server")
PUBLIC_IDS = tuple("{0}.showcase-loop-v1".format(icon) for icon in SHOWCASE_ICONS)
RUNTIME_IDS = tuple("{0}-showcase-loop-v1".format(icon) for icon in SHOWCASE_ICONS)


class DiagramCoreShowcaseTests(unittest.TestCase):
    def _temporary_directory(self):
        parent = ROOT / "build"
        parent.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(dir=str(parent))

    def _run_generator(self, output, check=True):
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "render_diagram_core_showcase.py"),
                "--icons",
                ",".join(SHOWCASE_ICONS),
                "--output",
                str(output),
            ],
            cwd=str(ROOT),
            env=environment,
            check=check,
            capture_output=True,
            text=True,
        )

    def test_motion_catalog_declares_one_presentation_per_icon(self):
        payload = json.loads(
            (ROOT / "runtime" / "motion-catalog.json").read_text(encoding="utf-8")
        )
        definitions = payload["diagram_core_presentations"]
        self.assertEqual(tuple(item["id"] for item in definitions), PUBLIC_IDS)
        self.assertEqual(tuple(item["runtime_id"] for item in definitions), RUNTIME_IDS)
        self.assertEqual(tuple(item["icon"] for item in definitions), SHOWCASE_ICONS)
        self.assertTrue(all(item["kind"] == "presentation" for item in definitions))
        self.assertTrue(all(item["profile"] == "showcase" for item in definitions))
        self.assertTrue(all(item["status"] == "visual-review" for item in definitions))
        self.assertTrue(all(item["required_parts"] for item in definitions))
        self.assertTrue(all(item["optional_parts"] == [] for item in definitions))
        self.assertTrue(all(1600 <= item["duration_ms"] <= 2400 for item in definitions))
        self.assertTrue(all(item["repeat_policy"] == "scene-controlled" for item in definitions))

    def test_generator_produces_one_self_contained_showcase_profile(self):
        with self._temporary_directory() as directory:
            output = Path(directory) / "showcase.html"
            completed = self._run_generator(output)
            self.assertIn("profile=showcase", completed.stdout)
            source = output.read_text(encoding="utf-8")

        self.assertEqual(source.count('data-showcase-card="'), 4)
        self.assertEqual(source.count('data-icon-presentation="showcase"'), 4)
        self.assertNotIn("data-icon-state", source)
        self.assertNotIn("data-state-mark", source)
        self.assertNotIn(">Readable<", source)
        self.assertNotIn("<script src=", source)
        self.assertNotRegex(source, r'(?:src|href)=["\']https?://')
        self.assertIn('has("no-gsap")', source)
        committed = (ROOT / "gallery" / "diagram-core" / "showcase.html").read_text(
            encoding="utf-8"
        )
        self.assertEqual(source, committed)

    def test_generator_rejects_dangling_symlink_output(self):
        with self._temporary_directory() as directory:
            output = Path(directory) / "showcase.html"
            output.symlink_to(Path(directory) / "missing.html")
            completed = self._run_generator(output, check=False)
            self.assertNotEqual(completed.returncode, 0)
            self.assertTrue(output.is_symlink())
            self.assertFalse((Path(directory) / "missing.html").exists())

    def test_runtime_registers_four_isolated_showcase_performances(self):
        source = (ROOT / "runtime" / "anidiagram-runtime.js").read_text(
            encoding="utf-8"
        )
        for icon, runtime_id in zip(SHOWCASE_ICONS, RUNTIME_IDS):
            self.assertIn('"{0}": play{1}Showcase'.format(runtime_id, icon.title()), source)
        self.assertIn("const SHOWCASE_TIME_SCALE = 0.6", source)
        self.assertIn("timeline.__anidiagramRestAt = config.rest_at", source)
        self.assertIn("config.repeat_delay * SHOWCASE_TIME_SCALE", source)
        self.assertIn("timeline.timeScale(SHOWCASE_TIME_SCALE)", source)

    def test_canonical_assets_expose_no_semantic_state(self):
        for icon in SHOWCASE_ICONS:
            source = (
                ROOT / "assets" / "diagram-core" / "icons" / (icon + ".svg")
            ).read_text(encoding="utf-8")
            self.assertIn('data-part="body"', source)
            self.assertNotIn("data-icon-state", source)
            self.assertNotIn("data-state-mark", source)


if __name__ == "__main__":
    unittest.main()
