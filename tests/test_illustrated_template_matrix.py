import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from anidiagram.illustrated_registry import illustrated_definition, illustrated_icon_ids
from anidiagram.illustrated_tokens import illustrated_token_document, illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from scripts import promote_illustrated_template_matrix as template_promotion
from scripts.render_illustrated_template_matrix import render_html


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "styles" / "catalog.json"
MATRIX_PATH = ROOT / "assets" / "illustrated" / "reviews" / "template-matrix-2.5.0-candidate.json"
PUBLIC_MAPPING_PATH = ROOT / "assets" / "illustrated" / "template-mappings.json"
ACCEPTANCE_PATH = ROOT / "assets" / "illustrated" / "reviews" / "2.5.0-template-acceptance.json"


def _structure(markup: str):
    root = ET.fromstring(markup)
    return [
        (
            element.tag,
            tuple(
                sorted(
                    (name, value)
                    for name, value in element.attrib.items()
                    if name not in {"fill", "stroke", "id"}
                )
            ),
        )
        for element in root.iter()
    ]


class IllustratedTemplateMatrixTest(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        self.matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))

    def test_candidate_covers_all_thirteen_public_styles_with_complete_color_tokens(self):
        styles = self.catalog["styles"]
        mappings = self.matrix["mappings"]
        allowed = set(illustrated_token_document()["override_policy"]["allowed_color_tokens"])

        self.assertEqual(12, len(styles))
        self.assertEqual(13, len(mappings))
        self.assertEqual(styles, [item["style"] for item in mappings if item["style"] != "minimal-light"])
        self.assertEqual({"approved", "visual-review"}, {item["status"] for item in mappings})
        self.assertEqual("approved", next(item for item in mappings if item["style"] == "deep-tech")["status"])
        for item in mappings:
            with self.subTest(style=item["style"]):
                self.assertEqual(allowed, set(item["illustrated_tokens"]))
                self.assertGreaterEqual(len(set(item["illustrated_tokens"].values())), 12)
                resolved = illustrated_tokens_for_style({"illustrated_tokens": item["illustrated_tokens"]})
                self.assertEqual(item["illustrated_tokens"], dict(resolved))
                self.assertFalse(item["constraints"]["geometry_overrides"])
                self.assertFalse(item["constraints"]["semantic_structure_overrides"])

    def test_every_candidate_palette_preserves_all_fifty_six_icon_structures(self):
        baseline_tokens = illustrated_tokens_for_style()
        for icon_id in illustrated_icon_ids():
            definition = illustrated_definition(icon_id)
            baseline = render_character_v2_icon(definition, "baseline", 60, 60, 120, baseline_tokens)
            for item in self.matrix["mappings"]:
                candidate = render_character_v2_icon(
                    definition,
                    "candidate",
                    60,
                    60,
                    120,
                    item["illustrated_tokens"],
                )
                with self.subTest(icon=icon_id, style=item["style"]):
                    self.assertEqual(_structure(baseline), _structure(candidate))

    def test_review_page_contains_thirteen_themes_and_728_unique_icon_instances(self):
        source = render_html(self.matrix)

        self.assertEqual(13, source.count('class="theme-section"'))
        self.assertEqual(728, source.count('class="icon-card"'))
        self.assertEqual(728, source.count('class="semantic-icon semantic-icon-illustrated"'))
        ids = []
        for fragment in source.split(' id="')[1:]:
            ids.append(fragment.split('"', 1)[0])
        self.assertEqual(len(ids), len(set(ids)))

    def test_human_approved_matrix_is_promoted_to_every_public_style(self):
        public = json.loads(PUBLIC_MAPPING_PATH.read_text(encoding="utf-8"))
        acceptance = json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))
        candidate_by_style = {item["style"]: item for item in self.matrix["mappings"]}
        public_by_style = {item["style"]: item for item in public["mappings"]}

        self.assertEqual(self.catalog["styles"], list(public_by_style))
        self.assertEqual("approved", acceptance["status"])
        self.assertEqual(13, acceptance["style_count"])
        self.assertEqual(20, acceptance["reviewed_icon_count"])
        self.assertTrue(acceptance["final_56_icon_matrix_required"])
        for style_id in self.catalog["styles"]:
            with self.subTest(style=style_id):
                style = json.loads((ROOT / "styles" / f"{style_id}.json").read_text(encoding="utf-8"))
                self.assertEqual(candidate_by_style[style_id]["illustrated_tokens"], style["illustrated_tokens"])
                self.assertEqual("approved", public_by_style[style_id]["status"])
                self.assertEqual("confirmed", public_by_style[style_id]["human_visual_acceptance"])
                self.assertFalse(public_by_style[style_id]["constraints"]["geometry_overrides"])
                self.assertFalse(public_by_style[style_id]["constraints"]["semantic_structure_overrides"])

    def test_template_promotion_requires_a_separate_existing_human_acceptance(self):
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))["styles"]
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing-acceptance.json"
            with patch.object(template_promotion, "ACCEPTANCE_PATH", missing):
                with self.assertRaisesRegex(RuntimeError, "independent human acceptance"):
                    template_promotion._require_human_acceptance(self.matrix, catalog)


if __name__ == "__main__":
    unittest.main()
