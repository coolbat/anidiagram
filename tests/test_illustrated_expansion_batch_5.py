import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from anidiagram.illustrated_expansion_batch_5 import (
    ILLUSTRATED_EXPANSION_BATCH_5_METADATA,
    expansion_batch_5_definition,
    expansion_batch_5_icon_ids,
)
from anidiagram.illustrated_registry import illustrated_definition, illustrated_icon_ids
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style
from scripts.render_illustrated_expansion_batch_5 import render_html


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = (
    "developer",
    "agent-team",
    "assistant",
    "human-reviewer",
    "llm",
    "reasoning",
)


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


class IllustratedExpansionBatch5Test(unittest.TestCase):
    def test_approved_batch_is_preserved_and_promoted_in_public_25_registry(self):
        self.assertEqual(EXPECTED, expansion_batch_5_icon_ids())
        self.assertEqual("approved", ILLUSTRATED_EXPANSION_BATCH_5_METADATA["status"])
        self.assertEqual("confirmed", ILLUSTRATED_EXPANSION_BATCH_5_METADATA["human_visual_acceptance"])
        self.assertEqual("2026-07-22", ILLUSTRATED_EXPANSION_BATCH_5_METADATA["static_approved_at"])
        self.assertEqual("2.4.0", ILLUSTRATED_EXPANSION_BATCH_5_METADATA["baseline_version"])
        self.assertEqual("2.5.0", ILLUSTRATED_EXPANSION_BATCH_5_METADATA["target_version"])
        self.assertFalse(ILLUSTRATED_EXPANSION_BATCH_5_METADATA["public_registry_changed"])
        self.assertEqual("approved", ILLUSTRATED_EXPANSION_BATCH_5_METADATA["motion_status"])
        self.assertEqual("2026-07-23", ILLUSTRATED_EXPANSION_BATCH_5_METADATA["motion_approved_at"])
        self.assertEqual("illustrated-performance-v6-review", ILLUSTRATED_EXPANSION_BATCH_5_METADATA["review_motion_contract"])
        self.assertEqual(56, len(illustrated_icon_ids()))
        for icon_id in EXPECTED:
            self.assertIs(expansion_batch_5_definition(icon_id), illustrated_definition(icon_id), icon_id)

    def test_candidates_have_distinct_semantics_and_stable_parts(self):
        roles = {
            "developer": "person-code-build-deliver",
            "agent-team": "agents-coordinate-delegate-synthesize",
            "assistant": "assistant-listen-guide-respond",
            "human-reviewer": "human-inspect-decide-annotate",
            "llm": "language-context-transform-generate",
            "reasoning": "premise-connect-infer-conclude",
        }
        for icon_id, role in roles.items():
            definition = expansion_batch_5_definition(icon_id)
            with self.subTest(icon_id=icon_id):
                self.assertEqual(role, definition.semantic_role)
                self.assertEqual("root", definition.parts[0])
                self.assertEqual(len(definition.parts), len(set(definition.parts)))
                self.assertEqual(set(definition.parts[1:]), {item.part for item in definition.primitives})
                self.assertLessEqual(len(definition.parts), 10)

    def test_candidates_do_not_use_generic_peripheral_decorations(self):
        forbidden = ("check", "arrow", "triangle", "badge", "status", "spark")
        for icon_id in EXPECTED:
            parts = expansion_batch_5_definition(icon_id).parts
            with self.subTest(icon_id=icon_id):
                self.assertFalse(any(word in part for word in forbidden for part in parts), parts)

    def test_warm_and_deep_tech_candidates_have_identical_structure(self):
        warm = illustrated_tokens_for_style(load_style(ROOT / "styles" / "illustrated-character-v2-concept.json"))
        deep = illustrated_tokens_for_style(load_style(ROOT / "styles" / "deep-tech.json"))
        for icon_id in EXPECTED:
            definition = expansion_batch_5_definition(icon_id)
            warm_markup = render_character_v2_icon(definition, "proof", 60, 60, 120, warm)
            deep_markup = render_character_v2_icon(definition, "proof", 60, 60, 120, deep)
            with self.subTest(icon_id=icon_id):
                self.assertEqual(_structure(warm_markup), _structure(deep_markup))

    def test_review_page_contains_thirty_unique_static_instances(self):
        warm_style = load_style(ROOT / "styles" / "illustrated-character-v2-concept.json")
        deep_style = load_style(ROOT / "styles" / "deep-tech.json")
        source = render_html(warm_style, deep_style)
        self.assertEqual(30, source.count('class="candidate-instance"'))
        self.assertEqual(12, source.count('class="candidate-card"'))
        self.assertEqual(6, source.count('class="size-card"'))
        self.assertEqual({"64", "96", "120"}, set(re.findall(r'data-size="(64|96|120)"', source)))
        ids = re.findall(r' id="([^"]+)"', source)
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
