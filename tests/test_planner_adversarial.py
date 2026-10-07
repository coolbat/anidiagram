import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from anidiagram.planner import brief_to_plan
from test_rule_planner import topology


ROOT = Path(__file__).resolve().parents[1]


class PlannerAdversarialTests(unittest.TestCase):
    def test_negative_contractions_and_prefixed_prohibitions_do_not_create_edges(self):
        for brief in ("A won't call B.", 'A won’t call B.', "A wouldn't call B.", "A couldn't call B.", "A hasn't called B.", 'Do not draw: A calls B.', '禁止：A 调用 B。'):
            with self.subTest(brief=brief):
                try:
                    plan = brief_to_plan(brief)
                except ValueError:
                    continue
                self.assertEqual([], plan['semantic']['relations'])
                self.assertEqual('explicit-rules-v1', plan['planning']['method'])
                self.assertIn('brief_rule_negation', [warning['code'] for warning in plan['planning']['warnings']])

    def test_modality_and_arbitrary_prefix_are_not_silently_asserted(self):
        for brief in ('A can call B.', 'A may call B.', 'A must call B.'):
            with self.subTest(brief=brief), self.assertRaisesRegex(ValueError, 'No positive template'):
                brief_to_plan(brief)
        plan = brief_to_plan('Invent unicorn automation: A calls B.')
        self.assertEqual({('a', 'b', 'request')}, topology(plan))
        self.assertEqual('partial', plan['planning']['coverage']['status'])
        self.assertIn('Invent unicorn automation: A calls B', plan['planning']['coverage']['unparsed_spans'])

    def test_relative_clause_cannot_cross_sentence_or_unparsed_predicate(self):
        for brief in ('A calls B. which calls C.', 'A calls B and alerts, which calls C.'):
            with self.subTest(brief=brief):
                plan = brief_to_plan(brief)
                self.assertEqual({('a', 'b', 'request')}, topology(plan))
                self.assertEqual('partial', plan['planning']['coverage']['status'])

    def test_conditions_and_relations_have_exact_original_author_provenance(self):
        brief = '  If A calls B,\n C writes to D. unsupported detail. '
        plan = brief_to_plan(brief)
        sources = {item['id']: item for item in plan['semantic']['sources']}
        for clause in plan['planning']['provenance']:
            self.assertEqual(brief[clause['start']:clause['end']], clause['text'])
            self.assertEqual(clause['text'], sources[clause['source_ref']]['note'])
        edge = plan['semantic']['relations'][0]
        self.assertEqual({'C writes to D', 'If A calls B'}, {sources[ref]['note'] for ref in edge['source_refs']})
        self.assertEqual(brief, sources['input-brief']['note'])

    def test_provider_rejects_bad_input_before_starting_a_process(self):
        for changed in ({'brief': {}}, {'title': []}, {'style': 123}, {'planner_command': ['python\x00secret']}):
            with self.subTest(changed=changed), patch('anidiagram.provider_planner.subprocess.run') as run:
                args = {'brief': 'brief', 'planner': 'subprocess', 'planner_command': [sys.executable]}
                args.update(changed)
                with self.assertRaises(ValueError):
                    brief_to_plan(**args)
                run.assert_not_called()

    def test_provider_deep_json_error_is_sanitized(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'deep.py'
            path.write_text("print('['*2000+'0'+']'*2000)\n")
            with self.assertRaisesRegex(ValueError, 'invalid DiagramPlan'):
                brief_to_plan('brief', planner='subprocess', planner_command=[sys.executable, str(path)])

    def test_new_modules_use_python39_grammar_and_stdlib_dependencies(self):
        for name in ('rule_planner', 'provider_planner', 'illustrated_sources', 'runtime_registry'):
            tree = ast.parse((ROOT / ('src/anidiagram/' + name + '.py')).read_text(), feature_version=(3, 9))
            imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
            for node in imports:
                if isinstance(node, ast.ImportFrom) and node.level:
                    continue
                modules = [node.module] if isinstance(node, ast.ImportFrom) else [item.name for item in node.names]
                self.assertTrue(all(module in {'__future__', 're', 'typing', 'json', 'math', 'subprocess', 'dataclasses', 'importlib', 'pathlib'} for module in modules))


if __name__ == '__main__':
    unittest.main()
