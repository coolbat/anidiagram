import json
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


class _LocalAssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key in ("href", "src"):
            if values.get(key):
                self.references.append(values[key])


def _motion_manifest(html):
    marker = '<script type="application/json" id="anidiagram-motion-manifest">'
    start = html.index(marker) + len(marker)
    return json.loads(html[start : html.index("</script>", start)])


class IconSystemReleaseGalleryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (ROOT / "gallery" / "showcase_manifest.json").read_text(encoding="utf-8")
        )

    def test_manifest_exposes_both_current_public_icon_system_releases(self):
        releases = self.manifest["icon_system_releases"]
        self.assertEqual(["diagram-core-v1", "illustrated-2.4"], [entry["id"] for entry in releases])

        core, illustrated = releases
        self.assertEqual("diagram-core-v1", core["icon_system"])
        self.assertEqual("1.0.0", core["version"])
        self.assertEqual(56, core["icon_count"])
        self.assertEqual(56, core["rendered_icon_count"])
        self.assertEqual(56, core["automatic_motion_icon_count"])
        self.assertEqual("showcase-v1", core["motion_contract"])

        self.assertEqual("illustrated", illustrated["icon_system"])
        self.assertEqual("2.4.0", illustrated["version"])
        self.assertEqual(20, illustrated["icon_count"])
        self.assertEqual(20, illustrated["rendered_icon_count"])
        self.assertEqual(20, illustrated["automatic_motion_icon_count"])
        self.assertEqual("illustrated-performance-v5", illustrated["motion_contract"])

    def test_diagram_core_showcase_covers_all_frozen_icons_without_explicit_motion(self):
        spec_path = ROOT / "examples" / "diagram-core-v1-showcase.diagram.json"
        source = spec_path.read_text(encoding="utf-8")
        spec = json.loads(source)
        catalog = json.loads((ROOT / "assets" / "diagram-core" / "catalog.json").read_text(encoding="utf-8"))

        self.assertEqual("diagram-core-v1", spec["icon_system"])
        self.assertEqual(56, len(spec["nodes"]))
        self.assertEqual({entry["id"] for entry in catalog["icons"]}, {node["icon"] for node in spec["nodes"]})
        self.assertNotIn('"icon_motion"', source)

        entry = self.manifest["icon_system_releases"][0]
        html = (ROOT / entry["html"]).read_text(encoding="utf-8")
        motion = _motion_manifest(html)
        self.assertEqual(56, html.count('data-icon-source="diagram-core-v1"'))
        self.assertEqual(56, len(motion["icons"]))
        self.assertEqual({node["icon"] for node in spec["nodes"]}, {item["icon"] for item in motion["icons"]})

    def test_illustrated_showcase_is_twenty_icon_public_v5_without_explicit_motion(self):
        source = (ROOT / "examples" / "illustrated-2.4-showcase.diagram.json").read_text(encoding="utf-8")
        spec = json.loads(source)
        self.assertEqual("illustrated", spec["icon_system"])
        self.assertEqual(20, len(spec["nodes"]))
        self.assertNotIn('"icon_motion"', source)

        entry = self.manifest["icon_system_releases"][1]
        html = (ROOT / entry["html"]).read_text(encoding="utf-8")
        motion = _motion_manifest(html)
        self.assertEqual(20, len(motion["icons"]))
        self.assertTrue(all(item["motion_contract"] == "illustrated-performance-v5" for item in motion["icons"]))
        self.assertTrue(all(item["motion_status"] == "approved" for item in motion["icons"]))

    def test_release_gallery_artifacts_are_clean_and_links_are_local(self):
        for entry in self.manifest["icon_system_releases"]:
            for key in ("spec", "release", "svg", "html", "quality"):
                with self.subTest(release=entry["id"], key=key):
                    self.assertTrue((ROOT / entry[key]).is_file(), entry[key])
            quality = json.loads((ROOT / entry["quality"]).read_text(encoding="utf-8"))
            self.assertEqual({"errors": 0, "warnings": 0, "issues": 0}, quality["summary"])

        for page in (ROOT / "gallery" / "icon-systems").rglob("*.html"):
            parser = _LocalAssetParser()
            parser.feed(page.read_text(encoding="utf-8"))
            for reference in parser.references:
                parsed = urlsplit(reference)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                with self.subTest(page=page.name, reference=reference):
                    self.assertTrue((page.parent / parsed.path).resolve().is_file())

        home = (ROOT / "gallery" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="icon-systems/index.html"', home)

    def test_export_evidence_tool_has_full_matrix_and_configurable_browser_capture(self):
        from build_icon_system_release_evidence import CASES, EXPORT_FORMATS, _expected_icon_ids, _parser

        self.assertEqual(
            ("svg", "html", "png", "webp", "gif", "apng", "mp4", "pdf", "lottie", "quality"),
            EXPORT_FORMATS,
        )
        args = _parser().parse_args(["--verify", "--fps", "12", "--frames", "24", "--scale", "1"])
        self.assertTrue(args.verify)
        self.assertEqual((12, 24, 1.0), (args.fps, args.frames, args.scale))
        self.assertEqual((56, 20), tuple(len(_expected_icon_ids(case)) for case in CASES))

    def test_export_verifier_rejects_unverified_non_browser_capture(self):
        from build_icon_system_release_evidence import EXPORT_FORMATS, verify_evidence

        document = {
            "schema": "public-icon-system-export-evidence-v1",
            "status": "generated",
            "capture": {"renderer": "python", "fps": 0, "frames": 1, "scale": 0},
            "formats": list(EXPORT_FORMATS),
            "systems": [],
        }
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "evidence.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            report = verify_evidence(path)

        self.assertFalse(report["ok"])
        self.assertIn("evidence status is not verified", report["issues"])
        self.assertIn("capture renderer must be browser", report["issues"])
        self.assertIn(
            "capture metadata must use positive fps/scale and at least two frames",
            report["issues"],
        )

    def test_exact_icon_coverage_rejects_duplicates(self):
        from build_icon_system_release_evidence import _check_exact_icon_coverage

        issues = []
        _check_exact_icon_coverage(
            [("node-a", "agent"), ("node-b", "agent")],
            {"agent", "tool"},
            issues,
            "proof",
        )

        self.assertIn("proof: duplicate icon identity", issues)
        self.assertIn("proof: icon set does not exactly match the approved catalog", issues)


if __name__ == "__main__":
    unittest.main()
