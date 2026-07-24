import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from anidiagram.diagram_core.catalog import approved_icon_ids
from anidiagram.illustrated_expansion_batch_5 import expansion_batch_5_icon_ids
from anidiagram.illustrated_expansion_batches_6_10 import (
    BATCHES,
    ILLUSTRATED_EXPANSION_6_10_METADATA,
    expansion_6_10_definition,
    expansion_6_10_icon_ids,
    expansion_batch_icon_ids,
)
from anidiagram.illustrated_registry import illustrated_definition, illustrated_icon_ids
from anidiagram.illustrated_convention_alignment_review import (
    convention_alignment_definition,
    convention_alignment_icon_ids,
)
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style
from scripts.render_illustrated_expansion_batches_6_10 import render_html


ROOT = Path(__file__).resolve().parents[1]


def _structure(markup: str):
    root = ET.fromstring(markup)
    return [
        (element.tag, tuple(sorted((k, v) for k, v in element.attrib.items() if k not in {"fill", "stroke", "id"})))
        for element in root.iter()
    ]


class IllustratedExpansionBatches6To10Test(unittest.TestCase):
    def test_five_batches_cover_exactly_the_remaining_thirty_diagram_core_icons(self):
        public = set(illustrated_icon_ids())
        batch5 = set(expansion_batch_5_icon_ids())
        remaining = set(expansion_6_10_icon_ids())
        self.assertEqual(56, len(public))
        self.assertEqual(6, len(batch5))
        self.assertEqual(30, len(remaining))
        self.assertEqual(set(approved_icon_ids()), public)
        self.assertLessEqual(batch5, public)
        self.assertLessEqual(remaining, public)
        self.assertFalse(batch5 & remaining)
        self.assertEqual([6, 7, 8, 9, 10], list(BATCHES))
        for batch in BATCHES:
            self.assertEqual(6, len(expansion_batch_icon_ids(batch)))

    def test_review_sources_remain_frozen_after_public_promotion(self):
        self.assertEqual("approved", ILLUSTRATED_EXPANSION_6_10_METADATA["status"])
        self.assertEqual("confirmed", ILLUSTRATED_EXPANSION_6_10_METADATA["human_visual_acceptance"])
        self.assertEqual("2026-07-23", ILLUSTRATED_EXPANSION_6_10_METADATA["static_approved_at"])
        self.assertFalse(ILLUSTRATED_EXPANSION_6_10_METADATA["public_registry_changed"])
        self.assertEqual("visual-review", ILLUSTRATED_EXPANSION_6_10_METADATA["motion_status"])
        self.assertEqual("illustrated-performance-v7-review", ILLUSTRATED_EXPANSION_6_10_METADATA["review_motion_contract"])
        revised = set(convention_alignment_icon_ids())
        for icon_id in expansion_6_10_icon_ids():
            expected = convention_alignment_definition(icon_id) if icon_id in revised else expansion_6_10_definition(icon_id)
            self.assertIs(expected, illustrated_definition(icon_id), icon_id)

    def test_each_candidate_has_unique_stable_parts_and_no_generic_decorations(self):
        forbidden = ("check", "arrow", "triangle", "badge", "status", "spark")
        roles = set()
        for icon_id in expansion_6_10_icon_ids():
            definition = expansion_6_10_definition(icon_id)
            roles.add(definition.semantic_role)
            with self.subTest(icon_id=icon_id):
                self.assertEqual("root", definition.parts[0])
                self.assertEqual(len(definition.parts), len(set(definition.parts)))
                self.assertEqual(set(definition.parts[1:]), {item.part for item in definition.primitives})
                self.assertLessEqual(len(definition.parts), 10)
                self.assertFalse(any(word in part for word in forbidden for part in definition.parts), definition.parts)
        self.assertEqual(30, len(roles))

    def test_warm_and_deep_tech_render_with_identical_structure(self):
        warm = illustrated_tokens_for_style(load_style(ROOT / "styles" / "illustrated-character-v2-concept.json"))
        deep = illustrated_tokens_for_style(load_style(ROOT / "styles" / "deep-tech.json"))
        for icon_id in expansion_6_10_icon_ids():
            definition = expansion_6_10_definition(icon_id)
            warm_markup = render_character_v2_icon(definition, "proof", 60, 60, 120, warm)
            deep_markup = render_character_v2_icon(definition, "proof", 60, 60, 120, deep)
            with self.subTest(icon_id=icon_id):
                self.assertEqual(_structure(warm_markup), _structure(deep_markup))

    def test_review_page_contains_five_batches_and_150_unique_instances(self):
        warm = load_style(ROOT / "styles" / "illustrated-character-v2-concept.json")
        deep = load_style(ROOT / "styles" / "deep-tech.json")
        source = render_html(warm, deep)
        self.assertEqual(5, source.count('class="batch-section"'))
        self.assertEqual(60, source.count('class="candidate-card"'))
        self.assertEqual(30, source.count('class="size-card"'))
        self.assertEqual(150, source.count('class="candidate-instance"'))
        ids = re.findall(r' id="([^"]+)"', source)
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__": unittest.main()
