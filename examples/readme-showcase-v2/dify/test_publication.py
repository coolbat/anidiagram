"""Frozen publication consistency only, not independent Dify semantic review."""
import copy
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from build import HERE, REVISION, ROOT, STYLES, make_facts, make_plan, page_name, page_source, variant_stem
from publish import EXPECTED, SOURCE_FILES, digest, encoded, prepare

PUBLIC = ROOT / "gallery/cases/dify"


class DifyPublicationTests(unittest.TestCase):
    def test_complete_bundle_and_current_source_hashes(self):
        manifest = json.loads((PUBLIC / "manifest.json").read_text())
        self.assertEqual(manifest["revision"], REVISION)
        self.assertEqual(manifest["status"], "draft")
        self.assertEqual(manifest["independent_semantic_review"], "pending")
        self.assertEqual(manifest["dify_runtime"], "not run")
        self.assertNotIn("source_root", manifest)
        self.assertEqual(set(manifest["files"]), EXPECTED)
        self.assertEqual({p.name for p in PUBLIC.iterdir()}, EXPECTED | {"manifest.json"})
        self.assertEqual(set(manifest["source_files"]), SOURCE_FILES)
        for name, expected in manifest["source_files"].items():
            self.assertEqual(digest((HERE / name).read_bytes()), expected, name)
        for name, expected in manifest["files"].items():
            data = (PUBLIC / name).read_bytes()
            self.assertEqual(digest(data), expected, name)
            if not name.endswith(".webp"):
                self.assertNotRegex(data.decode(), r"/Users/|/home/")

    def test_both_languages_match_builder_and_keep_unresolved_facts(self):
        for style, language in [(s, l) for s in STYLES for l in ("zh-CN", "en")]:
            stem = variant_stem(language, style)
            suffix = ".en" if language == "en" else ""
            style_suffix = ".deep-tech" if style == "deep-tech" else ""
            plan = json.loads((PUBLIC / f"{stem}.plan.json").read_text())
            self.assertEqual(plan, make_plan(language, style))
            self.assertEqual(json.loads((PUBLIC / f"facts{suffix}.json").read_text()), make_facts(plan))
            accuracy = json.loads((PUBLIC / f"accuracy{style_suffix}{suffix}.json").read_text())
            self.assertFalse(accuracy["ready"])
            self.assertEqual(sum(c["status"] == "pending" for c in accuracy["claims"]), 19)
            self.assertEqual(sum(c["status"] == "supported" for c in accuracy["claims"]), 4)

    def test_delivery_hashes_still_bind_the_published_bytes(self):
        for name in sorted(EXPECTED):
            if name.endswith(".delivery.json"):
                receipt = json.loads((PUBLIC / name).read_text())
                for item in [receipt["input"]["source"], *receipt["artifacts"].values()]:
                    self.assertEqual(Path(item["path"]).name, item["path"])
                    data = (PUBLIC / item["path"]).read_bytes()
                    self.assertEqual(item["sha256"], digest(data), name)
                    self.assertEqual(item["bytes"], len(data), name)

    def test_page_assets_and_local_links_exist(self):
        for style, language in [(s, l) for s in STYLES for l in ("zh-CN", "en")]:
            name = page_name(language, style)
            text = (PUBLIC / name).read_text()
            self.assertEqual(text, page_source(language, style))
            other_language = "zh-CN" if language == "en" else "en"
            self.assertIn(f'href="{page_name(other_language, style)}"', text)
            self.assertIn(f'src="{variant_stem(language, style)}-static.svg"', text)
            self.assertNotIn("<!-- STYLE_SWITCH -->", text)
            for href in re.findall(r'(?:href|src)="([^"]+)"', text):
                if not href.startswith(("#", "https:", "data:")):
                    self.assertIn(href, EXPECTED)
        for readme, stem, page in [("README.md", "dify-en", "index.en.html"), ("README.zh-CN.md", "dify", "index.html")]:
            text = (ROOT / readme).read_text()
            self.assertIn(f"gallery/cases/dify/{stem}-static.svg", text)
            self.assertIn(f"gallery/cases/dify/{page}", text)

    def test_publisher_rejects_extra_paths_and_tampered_artifacts_before_writing(self):
        manifest = json.loads((PUBLIC / "manifest.json").read_text())
        # Header validation precedes artifact reads, even for traversal names.
        invalid = copy.deepcopy(manifest)
        invalid["files"]["../unexpected.txt"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "manifest.json").write_bytes(encoded(invalid))
            with self.assertRaisesRegex(ValueError, "file list"):
                prepare(directory)
        # No disk mutation needed to simulate a changed artifact.
        original = Path.read_bytes
        def tampered(path):
            return b"tampered" if path == PUBLIC / "dify.html" else original(path)
        with patch.object(Path, "read_bytes", tampered):
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                prepare(PUBLIC)


if __name__ == "__main__":
    unittest.main()
