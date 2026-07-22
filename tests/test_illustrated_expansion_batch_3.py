import xml.etree.ElementTree as ET
import unittest
from pathlib import Path

from anidiagram.illustrated_expansion_batch_3 import (
    ILLUSTRATED_EXPANSION_BATCH_3_METADATA,
    expansion_batch_3_definition,
    expansion_batch_3_icon_ids,
)
from anidiagram.illustrated_registry import illustrated_definition, illustrated_icon_ids
from anidiagram.illustrated_tokens import illustrated_geometry_tokens, illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style
from scripts.render_illustrated_expansion_batch_3 import render_svg


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ("user", "server", "ai-model", "message-queue")


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


class IllustratedExpansionBatch3Test(unittest.TestCase):
    def test_batch_static_and_motion_are_approved(self):
        self.assertEqual(EXPECTED, expansion_batch_3_icon_ids())
        self.assertEqual("approved", ILLUSTRATED_EXPANSION_BATCH_3_METADATA["status"])
        self.assertEqual("confirmed", ILLUSTRATED_EXPANSION_BATCH_3_METADATA["human_visual_acceptance"])
        self.assertEqual("2026-07-20", ILLUSTRATED_EXPANSION_BATCH_3_METADATA["static_approved_at"])
        self.assertEqual("2.2.0", ILLUSTRATED_EXPANSION_BATCH_3_METADATA["baseline_version"])
        self.assertEqual("2.3.0", ILLUSTRATED_EXPANSION_BATCH_3_METADATA["target_version"])
        self.assertTrue(ILLUSTRATED_EXPANSION_BATCH_3_METADATA["public_registry_changed"])
        self.assertEqual("approved", ILLUSTRATED_EXPANSION_BATCH_3_METADATA["motion_status"])
        self.assertEqual("confirmed", ILLUSTRATED_EXPANSION_BATCH_3_METADATA["motion_human_acceptance"])
        self.assertEqual("2026-07-20", ILLUSTRATED_EXPANSION_BATCH_3_METADATA["motion_approved_at"])
        self.assertEqual(EXPECTED, illustrated_icon_ids()[12:16])
        for icon_id in EXPECTED:
            self.assertIs(expansion_batch_3_definition(icon_id), illustrated_definition(icon_id))

    def test_candidates_have_distinct_semantics_and_unique_stable_parts(self):
        expected_roles = {
            "user": "external-person-request-interact",
            "server": "compute-host-run-service",
            "ai-model": "model-inference-transform-predict",
            "message-queue": "async-buffer-order-deliver",
        }
        for icon_id in EXPECTED:
            with self.subTest(icon_id=icon_id):
                definition = expansion_batch_3_definition(icon_id)
                self.assertEqual(expected_roles[icon_id], definition.semantic_role)
                self.assertEqual("root", definition.parts[0])
                self.assertEqual(len(definition.parts), len(set(definition.parts)))
                self.assertEqual(set(definition.parts[1:]), {primitive.part for primitive in definition.primitives})
                self.assertLessEqual(len(definition.parts), 10)

    def test_candidates_do_not_reuse_generic_status_or_direction_accessories(self):
        forbidden_fragments = ("check", "badge", "status", "arrow", "triangle")
        all_parts = {
            icon_id: expansion_batch_3_definition(icon_id).parts
            for icon_id in EXPECTED
        }
        for icon_id, parts in all_parts.items():
            with self.subTest(icon_id=icon_id):
                self.assertFalse(
                    any(fragment in part for fragment in forbidden_fragments for part in parts),
                    parts,
                )

        self.assertTrue({"portrait-body", "conversation-card"}.issubset(all_parts["user"]))
        self.assertTrue({"rack-shell", "rack-ports", "activity-lights"}.issubset(all_parts["server"]))
        self.assertTrue({"network-links", "hidden-neurons", "output-neuron"}.issubset(all_parts["ai-model"]))
        self.assertTrue({"queue-rail", "buffer-gates", "sequence-dots"}.issubset(all_parts["message-queue"]))

    def test_warm_and_deep_tech_candidates_have_identical_structure(self):
        warm = illustrated_tokens_for_style(load_style(ROOT / "styles" / "illustrated-character-v2-concept.json"))
        deep = illustrated_tokens_for_style(load_style(ROOT / "styles" / "deep-tech.json"))
        for icon_id in EXPECTED:
            definition = expansion_batch_3_definition(icon_id)
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
