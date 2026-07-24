import xml.etree.ElementTree as ET
import unittest
from pathlib import Path

from anidiagram.illustrated_registry import illustrated_definition, illustrated_icon_ids
from anidiagram.illustrated_convention_alignment_review import convention_alignment_definition
from anidiagram.illustrated_expansion_batch_1 import (
    ILLUSTRATED_EXPANSION_BATCH_1_METADATA,
    expansion_batch_1_definition,
    expansion_batch_1_icon_ids,
)
from anidiagram.illustrated_tokens import illustrated_geometry_tokens, illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style
from scripts.render_illustrated_expansion_batch_1 import render_svg


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ("database", "api", "search", "memory")


def _structure(markup: str):
    root = ET.fromstring(markup)
    signature = []
    for element in root.iter():
        attrs = tuple(
            sorted(
                (name, value)
                for name, value in element.attrib.items()
                if name not in {"fill", "stroke", "id"}
            )
        )
        signature.append((element.tag, attrs))
    return signature


class IllustratedExpansionBatch1Test(unittest.TestCase):
    def test_batch_is_static_approved_and_promoted_to_the_public_registry(self):
        self.assertEqual(EXPECTED, expansion_batch_1_icon_ids())
        self.assertEqual("approved", ILLUSTRATED_EXPANSION_BATCH_1_METADATA["status"])
        self.assertEqual("confirmed", ILLUSTRATED_EXPANSION_BATCH_1_METADATA["human_visual_acceptance"])
        self.assertEqual("2.1.0", ILLUSTRATED_EXPANSION_BATCH_1_METADATA["target_version"])
        self.assertTrue(ILLUSTRATED_EXPANSION_BATCH_1_METADATA["public_registry_changed"])
        self.assertEqual("approved", ILLUSTRATED_EXPANSION_BATCH_1_METADATA["motion_status"])
        self.assertEqual("confirmed", ILLUSTRATED_EXPANSION_BATCH_1_METADATA["motion_human_acceptance"])
        self.assertEqual(
            ("human-confirmation", "final-acceptance"),
            ILLUSTRATED_EXPANSION_BATCH_1_METADATA["accessory_policy"]["check_reserved_for"],
        )
        self.assertEqual(
            "integrated-semantic-cue",
            ILLUSTRATED_EXPANSION_BATCH_1_METADATA["accessory_policy"]["default"],
        )
        self.assertFalse(
            ILLUSTRATED_EXPANSION_BATCH_1_METADATA["accessory_policy"]["decoration_only_accessories"]
        )
        self.assertEqual(
            ("agent", "operator", "tool", "output", "database", "api", "search", "memory"),
            illustrated_icon_ids()[:8],
        )
        for icon_id in EXPECTED:
            expected = convention_alignment_definition(icon_id) or expansion_batch_1_definition(icon_id)
            self.assertIs(expected, illustrated_definition(icon_id))

    def test_candidates_have_one_semantic_role_and_unique_stable_parts(self):
        expected_roles = {
            "database": "data-ingest-store-persist",
            "api": "request-route-response",
            "search": "query-scan-discover",
            "memory": "context-capture-index-recall",
        }
        for icon_id in EXPECTED:
            with self.subTest(icon_id=icon_id):
                definition = expansion_batch_1_definition(icon_id)
                self.assertEqual(expected_roles[icon_id], definition.semantic_role)
                self.assertEqual("root", definition.parts[0])
                self.assertEqual(len(definition.parts), len(set(definition.parts)))
                self.assertEqual(set(definition.parts[1:]), {primitive.part for primitive in definition.primitives})
                self.assertLessEqual(len(definition.parts), 10)

    def test_accessories_are_semantic_and_checks_are_not_used_as_generic_results(self):
        for icon_id in EXPECTED:
            with self.subTest(icon_id=icon_id):
                definition = expansion_batch_1_definition(icon_id)
                self.assertNotIn("status-check", definition.parts)
        self.assertTrue({"commit-ripple", "stored-bead"}.issubset(expansion_batch_1_definition("database").parts))
        self.assertTrue({"request-token", "response-token"}.issubset(expansion_batch_1_definition("api").parts))
        self.assertTrue({"target-ring", "discovery"}.issubset(expansion_batch_1_definition("search").parts))
        self.assertTrue({"bookmark", "result"}.issubset(expansion_batch_1_definition("memory").parts))

    def test_warm_and_deep_tech_candidates_have_identical_structure(self):
        warm = illustrated_tokens_for_style(load_style(ROOT / "styles" / "illustrated-character-v2-concept.json"))
        deep = illustrated_tokens_for_style(load_style(ROOT / "styles" / "deep-tech.json"))
        for icon_id in EXPECTED:
            definition = expansion_batch_1_definition(icon_id)
            warm_markup = render_character_v2_icon(definition, "proof", 80, 80, 120, warm)
            deep_markup = render_character_v2_icon(definition, "proof", 80, 80, 120, deep)
            self.assertEqual(_structure(warm_markup), _structure(deep_markup), icon_id)

    def test_contact_sheet_contains_twenty_unique_static_instances(self):
        warm_style = load_style(ROOT / "styles" / "illustrated-character-v2-concept.json")
        deep_style = load_style(ROOT / "styles" / "deep-tech.json")
        root = ET.fromstring(render_svg(warm_style, deep_style))
        ids = [element.attrib["id"] for element in root.iter() if "id" in element.attrib]
        instances = [
            element for element in root.iter() if "candidate-instance" in element.attrib.get("class", "")
        ]
        cards = [element for element in root.iter() if "candidate-card" in element.attrib.get("class", "")]

        self.assertEqual(20, len(instances))
        self.assertEqual({"64", "96", "120", "142"}, {item.attrib["data-size"] for item in instances})
        self.assertEqual(8, len(cards))
        self.assertEqual({"warm", "deep-tech"}, {card.attrib["data-theme"] for card in cards})
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(120, illustrated_geometry_tokens()["view_box"])


if __name__ == "__main__":
    unittest.main()
