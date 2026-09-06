import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

from anidiagram.accuracy import check_accuracy
from anidiagram.cli import main
from anidiagram.delivery import canonical_json_bytes


class AccuracyTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Accuracy fixture')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('remote', 'add', 'origin', 'https://github.com/example/fixture.git')
        (self.root / 'cli.py').write_text('def dispatch(scene):\n    return scene\n')
        self.git('add', 'cli.py')
        self.git('commit', '-qm', 'fixture')
        revision = self.git('rev-parse', 'HEAD').strip()
        self.spec = {'version': '0.4', 'canvas': {'width': 800, 'height': 500},
                     'nodes': [{'id': 'cli', 'label': 'cli.py', 'position': [80, 140], 'size': [160, 80]},
                               {'id': 'renderer', 'label': 'Renderer', 'position': [480, 140], 'size': [180, 80]}],
                     'edges': [{'from': 'cli', 'to': 'renderer', 'label': 'render', 'semantic_relation_id': 'render',
                                'semantic_kind': 'function-call', 'condition': 'errors == 0', 'direction': 'forward'}],
                     'evidence': {'sources': [{'id': 'code', 'type': 'repository', 'repository': {
                         'url': 'https://github.com/example/fixture', 'revision': revision,
                         'path': 'cli.py', 'line': 1, 'end_line': 2}}],
                         'subjects': {'cli': ['code'], 'render': ['code']}}}
        self.facts = {'version': '0.1', 'claims': [{'id': 'definition', 'subject': 'cli',
                       'predicate': 'python-definition', 'object': {'path': 'cli.py', 'symbol': 'dispatch'},
                       'condition': '', 'source_refs': ['code']}]}

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True, stderr=subprocess.PIPE)

    def check(self, review=None):
        return check_accuracy(self.spec, self.facts, repo_root=self.root, review=review)

    def behavior(self):
        self.facts['claims'] = [{'id': 'behavior', 'subject': 'render', 'predicate': 'behavior',
                                'object': 'errors still render', 'condition': 'errors > 0', 'source_refs': ['code']}]

    def review(self, verdict='supported'):
        return {'version': '0.1', 'reviewer': 'independent source reviewer',
                'specification_sha256': hashlib.sha256(canonical_json_bytes(self.spec)).hexdigest(),
                'facts_sha256': hashlib.sha256(canonical_json_bytes(self.facts)).hexdigest(),
                'decisions': [{'claim_id': c['id'], 'verdict': verdict, 'rationale': 'Read the fixed source.',
                               'source_refs': ['code']} for c in self.facts['claims']]}

    def test_definition_uses_commit_not_dirty_tree(self):
        (self.root / 'cli.py').write_text('raise RuntimeError("must not execute")\n')
        result = self.check()
        self.assertTrue(result['ready'])
        self.assertEqual('python-ast', result['claims'][0]['basis'])
        self.assertEqual('not-checked', result['gates']['rendered_readability'])

    def test_wrong_module_and_display_owner_rejected(self):
        self.facts['claims'][0]['object']['path'] = 'exporters.py'
        self.assertEqual('contradicted', self.check()['claims'][0]['status'])
        self.facts['claims'][0]['object']['path'] = 'cli.py'
        self.spec['nodes'][0]['label'] = 'exporters.py'
        self.assertFalse(self.check()['ready'])

    def test_existing_file_does_not_prove_symbol_or_behavior(self):
        self.facts['claims'][0]['object']['symbol'] = 'missing'
        self.assertFalse(self.check()['ok'])
        self.behavior()
        result = self.check()
        self.assertTrue(result['ok'])
        self.assertFalse(result['ready'])
        self.assertEqual('pending', result['claims'][0]['status'])

    def test_relation_direction_and_condition_are_exact(self):
        self.facts['claims'] = [{'id': 'relation', 'subject': 'render', 'predicate': 'relation',
                                'object': {'from': 'cli', 'to': 'renderer', 'direction': 'forward', 'kind': 'function-call'},
                                'condition': 'errors == 0', 'source_refs': ['code']}]
        self.assertFalse(self.check()['ready'])  # Matching authored fields is not source causality proof.
        self.assertTrue(self.check(self.review())['ready'])
        self.facts['claims'][0]['condition'] = 'errors > 0'
        self.assertFalse(self.check()['ok'])
        self.facts['claims'][0]['condition'] = 'errors == 0'
        self.facts['claims'][0]['object']['direction'] = 'bidirectional'
        self.assertFalse(self.check()['ok'])

    def test_review_bound_to_exact_inputs_and_not_a_machine_proof(self):
        self.behavior()
        result = self.check(self.review('contradicted'))
        self.assertFalse(result['ready'])
        self.assertEqual('review-record', result['claims'][0]['basis'])
        review = self.review()
        self.facts['claims'][0]['condition'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'hash'):
            self.check(review)

    def test_unknown_required_claim_does_not_pass_strict(self):
        self.facts['claims'][0]['confidence'] = 'unknown'
        self.assertFalse(self.check()['ready'])
        self.facts['claims'][0]['required'] = False
        self.assertTrue(self.check()['ready'])
        self.assertEqual('unknown', self.check()['claims'][0]['status'])

    def test_cannot_override_mechanical_contradiction_with_review(self):
        self.facts['claims'][0]['object']['symbol'] = 'missing'
        self.assertFalse(self.check(self.review())['ok'])

    def test_unknown_without_evidence_stays_unknown(self):
        self.facts['claims'][0].update(confidence='unknown', source_refs=[])
        result = self.check()
        self.assertTrue(result['ok'])
        self.assertFalse(result['ready'])
        self.assertEqual('unknown', result['claims'][0]['status'])

    def test_definition_cannot_certify_behavioral_condition(self):
        self.facts['claims'][0]['condition'] = 'errors still render'
        with self.assertRaisesRegex(ValueError, 'condition must be empty'):
            self.check()

    def test_matching_false_behavior_is_not_automatically_supported(self):
        self.test_relation_direction_and_condition_are_exact()
        self.facts['claims'][0]['object']['direction'] = 'forward'
        self.spec['edges'][0]['condition'] = self.facts['claims'][0]['condition'] = 'invented condition'
        result = self.check()
        self.assertFalse(result['ready'])
        self.assertEqual('pending', result['claims'][0]['status'])

    def test_invalid_or_unbound_claims_fail_closed(self):
        original = copy.deepcopy(self.facts)
        for change in ({'subject': 'missing'}, {'predicate': 'trust-me'}, {'required': 'false'},
                       {'confidence': 'verified'}, {'source_refs': ['missing']}, {'object': []}):
            self.facts = copy.deepcopy(original)
            self.facts['claims'][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.check()
        self.facts = copy.deepcopy(original)
        self.facts['claims'].append(copy.deepcopy(self.facts['claims'][0]))
        with self.assertRaisesRegex(ValueError, 'unique'):
            self.check()

    def test_cli_strict_pending_and_output_cannot_replace_input(self):
        self.behavior()
        spec, facts, output = [self.root / name for name in ('spec.json', 'facts.json', 'check.json')]
        spec.write_text(json.dumps(self.spec))
        facts.write_text(json.dumps(self.facts))
        args = ['accuracy-check', str(spec), '--facts', str(facts), '--repo-root', str(self.root), '--out', str(output)]
        with redirect_stdout(io.StringIO()):
            main(args)
        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised:
            main(args + ['--strict'])
        self.assertEqual(1, raised.exception.code)
        before = spec.read_bytes()
        args[-1] = str(spec)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(args)
        self.assertEqual(before, spec.read_bytes())
