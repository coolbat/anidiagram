import json
import os
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from render_diagram_core_showcase import _validate_recipe

CATALOG = json.loads(
    (ROOT / "assets" / "diagram-core" / "catalog.json").read_text(encoding="utf-8")
)
VISUAL_REVIEW_ICONS = frozenset(
    item["id"] for item in CATALOG["icons"] if item["status"] == "visual-review"
)
MOTION_CATALOG = json.loads(
    (ROOT / "runtime" / "motion-catalog.json").read_text(encoding="utf-8")
)
SHOWCASE_ICONS = tuple(
    item["icon"] for item in MOTION_CATALOG["diagram_core_presentations"]
)
PUBLIC_IDS = tuple("{0}.showcase-loop-v1".format(icon) for icon in SHOWCASE_ICONS)
RUNTIME_IDS = tuple("{0}-showcase-loop-v1".format(icon) for icon in SHOWCASE_ICONS)
HAND_TUNED_ICONS = ("agent", "database", "api", "server")


class DiagramCoreShowcaseTests(unittest.TestCase):
    def _temporary_directory(self):
        parent = ROOT / "build"
        parent.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(dir=str(parent))

    def _run_generator(self, output, icons=None, check=True):
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(ROOT / "src")
        command = [
            sys.executable,
            str(ROOT / "scripts" / "render_diagram_core_showcase.py"),
        ]
        if icons is not None:
            command.extend(("--icons", ",".join(icons)))
        command.extend(("--output", str(output)))
        return subprocess.run(
            command,
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
        self.assertEqual(frozenset(SHOWCASE_ICONS), VISUAL_REVIEW_ICONS)
        self.assertEqual(tuple(item["id"] for item in definitions), PUBLIC_IDS)
        self.assertEqual(tuple(item["runtime_id"] for item in definitions), RUNTIME_IDS)
        self.assertEqual(tuple(item["icon"] for item in definitions), SHOWCASE_ICONS)
        self.assertTrue(all(item["kind"] == "presentation" for item in definitions))
        self.assertTrue(all(item["profile"] == "showcase" for item in definitions))
        self.assertTrue(all(item["status"] == "visual-review" for item in definitions))
        self.assertTrue(all(item["required_parts"] for item in definitions))
        self.assertTrue(all(isinstance(item["optional_parts"], list) for item in definitions))
        self.assertTrue(all(1600 <= item["duration_ms"] <= 2400 for item in definitions))
        self.assertTrue(all(item["repeat_policy"] == "scene-controlled" for item in definitions))

    def test_generator_produces_one_self_contained_showcase_profile(self):
        with self._temporary_directory() as directory:
            output = Path(directory) / "showcase.html"
            completed = self._run_generator(output)
            self.assertIn("profile=showcase", completed.stdout)
            source = output.read_text(encoding="utf-8")

        self.assertEqual(source.count('data-showcase-card="'), len(SHOWCASE_ICONS))
        self.assertEqual(
            source.count('data-icon-presentation="showcase"'),
            len(SHOWCASE_ICONS),
        )
        self.assertIn('data-showcase-columns="4"', source)
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

    def test_generator_accepts_a_presentation_ordered_subset(self):
        selected = SHOWCASE_ICONS[:: max(1, len(SHOWCASE_ICONS) - 1)]
        with self._temporary_directory() as directory:
            output = Path(directory) / "showcase.html"
            completed = self._run_generator(output, icons=selected)
            source = output.read_text(encoding="utf-8")

        self.assertIn("icons={0}".format(len(selected)), completed.stdout)
        self.assertEqual(source.count('data-showcase-card="'), len(selected))
        positions = tuple(
            source.index('data-showcase-card="{0}"'.format(icon))
            for icon in selected
        )
        self.assertEqual(positions, tuple(sorted(positions)))
        for icon in set(SHOWCASE_ICONS) - set(selected):
            self.assertNotIn('data-showcase-card="{0}"'.format(icon), source)

    def test_generator_rejects_unknown_or_non_visual_review_icons(self):
        with self._temporary_directory() as directory:
            output = Path(directory) / "showcase.html"
            completed = self._run_generator(
                output,
                icons=("agent", "not-a-diagram-core-icon"),
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not an implemented visual-review icon", completed.stderr)

    def test_generator_derives_icons_and_part_bindings_from_control_data(self):
        source = (ROOT / "scripts" / "render_diagram_core_showcase.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("ICONS =", source)
        self.assertNotIn("PART_BINDINGS =", source)
        self.assertIn("load_catalog", source)
        self.assertIn("load_manifest", source)

    def test_four_icon_benchmark_keeps_original_first_row_geometry(self):
        self.assertEqual(SHOWCASE_ICONS[:4], HAND_TUNED_ICONS)
        with self._temporary_directory() as directory:
            output = Path(directory) / "showcase.html"
            self._run_generator(output)
            source = output.read_text(encoding="utf-8")
        for icon, x in zip(HAND_TUNED_ICONS, (32, 256, 480, 704)):
            card_start = source.index('data-showcase-card="{0}"'.format(icon))
            card_end = source.index("</g>", card_start)
            self.assertIn(
                'x="{0}" y="32" width="200" height="244"'.format(x),
                source[card_start:card_end],
            )

    def test_generator_rejects_dangling_symlink_output(self):
        with self._temporary_directory() as directory:
            output = Path(directory) / "showcase.html"
            output.symlink_to(Path(directory) / "missing.html")
            completed = self._run_generator(output, check=False)
            self.assertNotEqual(completed.returncode, 0)
            self.assertTrue(output.is_symlink())
            self.assertFalse((Path(directory) / "missing.html").exists())

    def test_runtime_preserves_four_hand_tuned_showcase_performances(self):
        source = (ROOT / "runtime" / "anidiagram-runtime.js").read_text(
            encoding="utf-8"
        )
        for icon in HAND_TUNED_ICONS:
            runtime_id = "{0}-showcase-loop-v1".format(icon)
            self.assertIn('"{0}": play{1}Showcase'.format(runtime_id, icon.title()), source)
        self.assertIn("const SHOWCASE_TIME_SCALE = 0.6", source)
        self.assertIn("timeline.__anidiagramRestAt = config.rest_at", source)
        self.assertIn("config.repeat_delay * SHOWCASE_TIME_SCALE", source)
        self.assertIn("timeline.timeScale(SHOWCASE_TIME_SCALE)", source)

    def test_runtime_declares_a_strict_declarative_recipe_allowlist(self):
        source = (ROOT / "runtime" / "anidiagram-runtime.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function playDeclarativeShowcase", source)
        self.assertIn('new Set(["x", "y", "rotate", "scale", "scaleX", "scaleY", "opacity"])', source)
        self.assertIn("validateShowcaseRecipe", source)
        self.assertIn("iconConfig.recipe", source)

    def test_runtime_resolves_recipe_parts_inside_one_null_prototype_instance(self):
        source = (ROOT / "runtime" / "anidiagram-runtime.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("Object.create(null)", source)
        self.assertIn("function resolveIconInstanceRoot", source)
        self.assertIn("part instanceof Element", source)
        self.assertIn("Object.prototype.hasOwnProperty.call(parts, name)", source)

    def test_python_recipe_validator_rejects_cross_track_part_contention(self):
        track = {
            "parts": ["body"],
            "steps": [
                {
                    "to": {"y": -4},
                    "duration": 0.18,
                    "ease": "power2.out",
                    "at": 0,
                }
            ],
        }
        recipe = {"tracks": [track, deepcopy(track)]}
        with self.assertRaisesRegex(RuntimeError, "more than one recipe track"):
            _validate_recipe("fixture", recipe, ("body",), 0.4)

    def test_python_recipe_validator_allows_only_the_search_scan_one_full_rotation(self):
        recipe = {
            "tracks": [
                {
                    "parts": ["scan"],
                    "steps": [
                        {
                            "to": {"rotate": 360},
                            "duration": 0.4,
                            "ease": "power2.inOut",
                            "at": 0,
                        }
                    ],
                }
            ]
        }
        _validate_recipe("search", recipe, ("scan",), 0.4)

        recipe["tracks"][0]["steps"][0]["to"]["rotate"] = 361
        with self.assertRaisesRegex(RuntimeError, "rotation exceeds 360 degrees"):
            _validate_recipe("search", recipe, ("scan",), 0.4)

        recipe["tracks"][0]["steps"][0]["to"]["rotate"] = 15
        with self.assertRaisesRegex(RuntimeError, "rotation exceeds 14 degrees"):
            _validate_recipe("fixture", recipe, ("scan",), 0.4)

    def test_database_showcase_uses_aligned_top_to_bottom_layer_wave(self):
        source = (ROOT / "runtime" / "anidiagram-runtime.js").read_text(
            encoding="utf-8"
        )
        start = source.index("function playDatabaseShowcase")
        end = source.index("function playApiShowcase", start)
        database_source = source[start:end]
        self.assertIn('const layers = [parts.layerTop, parts.layerMiddle, parts.layerBottom]', database_source)
        self.assertIn('y: -2, scaleX: 0.94', database_source)
        self.assertIn('stagger: 0.07', database_source)
        self.assertNotIn('x:', database_source)

    def test_search_showcase_traces_a_clockwise_whole_body_circle_before_scan_and_dot_pulses(self):
        definition = next(
            item
            for item in MOTION_CATALOG["diagram_core_presentations"]
            if item["icon"] == "search"
        )
        tracks = {
            track["parts"][0]: track
            for track in definition["recipe"]["tracks"]
        }

        self.assertEqual(("body", "scan", "target", "indicator"), tuple(tracks))
        self.assertNotIn("lens", tracks)
        self.assertNotIn("handle", tracks)

        body_steps = tracks["body"]["steps"]
        self.assertEqual(
            (
                (0, -4),
                (3, -3),
                (4, 0),
                (3, 3),
                (0, 4),
                (-3, 3),
                (-4, 0),
                (-3, -3),
                (0, -4),
                (0, 0),
            ),
            tuple((step["to"].get("x"), step["to"].get("y")) for step in body_steps),
        )
        self.assertTrue(
            all("rotate" not in step["to"] for step in body_steps),
            "the rigid magnifier must keep its orientation while its lens center traces the circle",
        )
        self.assertTrue(all(step["ease"] == "none" for step in body_steps[1:-1]))
        self.assertEqual({"x": 0, "y": 0}, body_steps[-1]["to"])

        scan_steps = tracks["scan"]["steps"]
        self.assertEqual((180, 360), tuple(step["to"]["rotate"] for step in scan_steps))
        body_end = body_steps[-1]["at"] + body_steps[-1]["duration"]
        scan_end = scan_steps[-1]["at"] + scan_steps[-1]["duration"]
        self.assertEqual(body_end, scan_steps[0]["at"])
        self.assertEqual(scan_end, tracks["target"]["steps"][0]["at"])

        self.assertEqual(
            (
                ({"scale": 1.45}, 0.22, "power2.out"),
                ({"scale": 1}, 0.2, "power2.out"),
            ),
            tuple(
                (step["to"], step["duration"], step["ease"])
                for step in tracks["target"]["steps"]
            ),
        )
        self.assertEqual(
            (
                ({"scale": 1.45}, 0.2, "power2.out"),
                ({"scale": 1}, 0.2, "power2.out"),
            ),
            tuple(
                (step["to"], step["duration"], step["ease"])
                for step in tracks["indicator"]["steps"]
            ),
        )
        self.assertLess(
            tracks["target"]["steps"][0]["at"],
            tracks["indicator"]["steps"][0]["at"],
        )

    def test_large_catalog_repeat_isolation_crosses_playwright_as_json_only(self):
        source = (
            ROOT / "scripts" / "verify_diagram_core_showcase_motion.mjs"
        ).read_text(encoding="utf-8")
        start = source.index("async function verifyRepeatedInstanceIsolation")
        end = source.index("async function verifyTwentyIconPerformance", start)
        isolation_source = source[start:end]

        self.assertNotIn(
            "page.evaluate(() => window.AniDiagramRuntime.play())",
            isolation_source,
        )
        self.assertIn("const isolationJson = await page.evaluate", isolation_source)
        self.assertIn("return JSON.stringify(results);", isolation_source)
        self.assertIn("const isolation = JSON.parse(isolationJson);", isolation_source)
        self.assertIn("if (isolation.length !== ICON_COUNT)", isolation_source)
        self.assertIn(
            "const failures = isolation.filter((entry) => !entry.firstOnly || !entry.secondOnly)",
            isolation_source,
        )

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
