import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from anidiagram.illustrated_convention_alignment_review import (
    ALIGNMENT_GROUPS,
    ALIGNMENT_REFERENCE_ANCHORS,
    CONVENTION_ALIGNMENT_METADATA,
    convention_alignment_definition,
    convention_alignment_icon_ids,
    current_alignment_definition,
    current_alignment_status,
)
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style
from scripts.render_illustrated_convention_alignment_review import render_html


ROOT = Path(__file__).resolve().parents[1]


def _structure(markup: str):
    root = ET.fromstring(markup)
    return [
        (element.tag, tuple(sorted((key, value) for key, value in element.attrib.items() if key not in {"fill", "stroke", "id"})))
        for element in root.iter()
    ]


class IllustratedConventionAlignmentReviewTest(unittest.TestCase):
    def test_scope_contains_four_priority_one_and_eight_priority_two_icons(self):
        self.assertEqual(
            ("token", "document-store", "webhook", "pull-request"),
            ALIGNMENT_GROUPS["p1-industry-anchor"]["icons"],
        )
        self.assertEqual(
            (
                "output",
                "memory",
                "gateway",
                "data-warehouse",
                "git-repository",
                "branch",
                "ci-cd",
                "deployment",
            ),
            ALIGNMENT_GROUPS["p2-semantic-alignment"]["icons"],
        )
        self.assertEqual(12, len(convention_alignment_icon_ids()))
        self.assertEqual(12, len(set(convention_alignment_icon_ids())))

    def test_approved_definitions_preserve_review_baselines_and_enter_public_registry(self):
        self.assertEqual("approved", CONVENTION_ALIGNMENT_METADATA["status"])
        self.assertTrue(CONVENTION_ALIGNMENT_METADATA["public_registry_changed"])
        self.assertTrue(CONVENTION_ALIGNMENT_METADATA["motion_contract_changed"])
        self.assertEqual(set(convention_alignment_icon_ids()), set(ALIGNMENT_REFERENCE_ANCHORS))
        self.assertGreaterEqual(len(CONVENTION_ALIGNMENT_METADATA["official_references"]), 12)
        for icon_id, anchor in ALIGNMENT_REFERENCE_ANCHORS.items():
            with self.subTest(reference_icon=icon_id):
                self.assertTrue(anchor["title"])
                self.assertTrue(anchor["note"])
                self.assertTrue(anchor["references"])
                self.assertTrue(all(reference["provider"] for reference in anchor["references"]))
                self.assertTrue(all(reference["url"].startswith("https://") for reference in anchor["references"]))
        for icon_id in convention_alignment_icon_ids():
            current = current_alignment_definition(icon_id)
            candidate = convention_alignment_definition(icon_id)
            with self.subTest(icon_id=icon_id):
                self.assertIsNotNone(current)
                self.assertIsNot(current, candidate)
                self.assertEqual(current.icon, candidate.icon)
                self.assertEqual(current.semantic_role, candidate.semantic_role)
        self.assertEqual(
            {"output", "memory", "gateway"},
            {icon_id for icon_id in convention_alignment_icon_ids() if current_alignment_status(icon_id) == "public"},
        )
        self.assertEqual(
            9,
            sum(current_alignment_status(icon_id) == "accepted-candidate" for icon_id in convention_alignment_icon_ids()),
        )

    def test_candidate_parts_are_stable_unique_and_free_of_generic_decorations(self):
        forbidden = ("check", "badge", "spark", "triangle", "generic-arrow")
        for icon_id in convention_alignment_icon_ids():
            definition = convention_alignment_definition(icon_id)
            primitive_parts = {primitive.part for primitive in definition.primitives}
            with self.subTest(icon_id=icon_id):
                self.assertEqual("root", definition.parts[0])
                self.assertEqual(len(definition.parts), len(set(definition.parts)))
                self.assertEqual(set(definition.parts[1:]), primitive_parts)
                self.assertLessEqual(len(definition.parts), 10)
                self.assertFalse(any(term in part for term in forbidden for part in definition.parts), definition.parts)

        pull_request = convention_alignment_definition("pull-request")
        self.assertIn("target-node", pull_request.parts)
        self.assertNotIn("target-nodes", pull_request.parts)
        self.assertNotIn("target-rail", pull_request.parts)

    def test_warm_and_deep_tech_use_identical_geometry(self):
        warm = illustrated_tokens_for_style(load_style(ROOT / "styles" / "illustrated-character-v2-concept.json"))
        deep = illustrated_tokens_for_style(load_style(ROOT / "styles" / "deep-tech.json"))
        for icon_id in convention_alignment_icon_ids():
            definition = convention_alignment_definition(icon_id)
            warm_markup = render_character_v2_icon(definition, f"warm-{icon_id}", 60, 60, 120, warm)
            deep_markup = render_character_v2_icon(definition, f"deep-{icon_id}", 60, 60, 120, deep)
            with self.subTest(icon_id=icon_id):
                self.assertEqual(_structure(warm_markup), _structure(deep_markup))

    def test_review_page_contains_72_unique_icon_instances(self):
        warm = load_style(ROOT / "styles" / "illustrated-character-v2-concept.json")
        deep = load_style(ROOT / "styles" / "deep-tech.json")
        source = render_html(warm, deep)
        self.assertEqual(12, source.count('class="comparison-card"'))
        self.assertEqual(72, source.count('class="candidate-instance"'))
        self.assertIn("Current public", source)
        self.assertIn("Accepted baseline", source)
        self.assertIn("Revised candidate", source)
        self.assertIn("Deep Tech", source)
        self.assertIn("Official anchor", source)
        ids = re.findall(r' id="([^"]+)"', source)
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
