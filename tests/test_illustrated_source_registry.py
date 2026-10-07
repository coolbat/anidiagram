import dataclasses
import hashlib
import json
import unittest
from pathlib import Path

from anidiagram.illustrated_registry import ILLUSTRATED_DEFINITIONS
from anidiagram.illustrated_public_motion import ILLUSTRATED_PUBLIC_ICON_PERFORMANCES, ILLUSTRATED_PUBLIC_REST_AT, ILLUSTRATED_PUBLIC_MOTION_SPECS
from anidiagram.illustrated_sources import ILLUSTRATED_SOURCES, compose_static_definitions, merge_registered_maps, source_value
from anidiagram.runtime_registry import archived_runtime_source


class IllustratedSourceRegistryTests(unittest.TestCase):
    def test_current_public_assets_match_pre_refactor_fingerprint(self):
        payload = {'definitions': {key: dataclasses.asdict(value) for key, value in ILLUSTRATED_DEFINITIONS.items()}, 'performances': ILLUSTRATED_PUBLIC_ICON_PERFORMANCES, 'rest': ILLUSTRATED_PUBLIC_REST_AT, 'specs': ILLUSTRATED_PUBLIC_MOTION_SPECS}
        self.assertEqual(56, len(ILLUSTRATED_DEFINITIONS))
        self.assertEqual('c89e7b4f4399c72ed9e5930f505767ac460746480f9dbb591c91823a25b3a496', hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest())
        self.assertEqual(ILLUSTRATED_DEFINITIONS, compose_static_definitions())

    def test_duplicate_registration_requires_explicit_override(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            merge_registered_maps([('a', {'icon': 1}, ()), ('b', {'icon': 2}, ())])
        self.assertEqual({'icon': 2}, merge_registered_maps([('a', {'icon': 1}, ()), ('b', {'icon': 2}, ('icon',))]))
        with self.assertRaisesRegex(ValueError, 'duplicate source'):
            merge_registered_maps([('a', {'one': 1}, ()), ('a', {'two': 2}, ())])
        self.assertEqual(len(ILLUSTRATED_SOURCES), len({item.id for item in ILLUSTRATED_SOURCES}))

    def test_archived_runtime_contract_resolves_frozen_source(self):
        root = Path(__file__).resolve().parents[1]
        expected = (root / 'runtime/illustrated-performance-v5-review-runtime.js').read_text()
        self.assertEqual(expected, archived_runtime_source('illustrated-performance-v5-review'))
        with self.assertRaisesRegex(ValueError, 'Unknown archived runtime'):
            archived_runtime_source('../other')
        with self.assertRaisesRegex(ValueError, 'Unknown Illustrated source'):
            source_value('unknown', 'definitions')


if __name__ == '__main__':
    unittest.main()
