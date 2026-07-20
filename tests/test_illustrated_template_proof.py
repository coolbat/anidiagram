import xml.etree.ElementTree as ET
import unittest
from pathlib import Path

from anidiagram.illustrated_character_v2_icons import character_v2_definition, character_v2_icon_ids
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style
from scripts.render_illustrated_template_proof import ICON_IDS, render_svg


ROOT = Path(__file__).resolve().parents[1]


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


class IllustratedTemplateProofTest(unittest.TestCase):
    def test_review_page_contains_two_unique_four_icon_rows(self):
        warm_style = load_style(ROOT / "styles" / "illustrated-character-v2-concept.json")
        deep_style = load_style(ROOT / "styles" / "deep-tech.json")
        root = ET.fromstring(render_svg(warm_style, deep_style))
        ids = [element.attrib["id"] for element in root.iter() if "id" in element.attrib]
        cards = [element for element in root.iter() if "theme-card" in element.attrib.get("class", "")]

        self.assertEqual(tuple(character_v2_icon_ids()), ICON_IDS)
        self.assertEqual(8, len(cards))
        self.assertEqual({"warm", "deep-tech"}, {card.attrib["data-theme"] for card in cards})
        self.assertEqual(len(ids), len(set(ids)))

    def test_warm_and_deep_tech_rendering_have_identical_structure(self):
        deep_style = load_style(ROOT / "styles" / "deep-tech.json")
        warm_tokens = illustrated_tokens_for_style()
        deep_tokens = illustrated_tokens_for_style(deep_style)

        for icon_id in ICON_IDS:
            definition = character_v2_definition(icon_id)
            warm = render_character_v2_icon(definition, "warm", 80, 80, 120, warm_tokens)
            deep = render_character_v2_icon(definition, "deep", 80, 80, 120, deep_tokens)
            self.assertEqual(_structure(warm), _structure(deep), icon_id)


if __name__ == "__main__":
    unittest.main()
