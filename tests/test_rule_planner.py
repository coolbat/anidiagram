import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from pathlib import Path

from anidiagram.cli import main
from anidiagram.planner import brief_to_plan, compile_plan
from anidiagram.schema import compile_scene
from anidiagram.planning import validate_planning


ZH = '构建电商订单系统：用户下单经过网关进入订单服务，订单服务调用库存服务和支付服务，支付成功后通过消息队列通知物流服务和积分服务，所有服务写入各自数据库，监控系统采集指标并告警。'
EN = 'Build an ecommerce order system: requests pass through a gateway to the order service, which calls inventory and payment services. After payment succeeds, a message queue notifies logistics and loyalty services. All services write to databases; monitoring collects metrics and alerts.'


def topology(plan):
    names = {entity['id']: entity['label'].lower() for entity in plan['semantic']['entities']}
    return {(names[edge['from']], names[edge['to']], edge['kind']) for edge in plan['semantic']['relations']}


class RulePlannerTests(unittest.TestCase):
    def test_extracts_custom_en_and_zh_call_write_and_via_relations(self):
        cases = [
            ('Atlas calls Boreal and Cygnus. Boreal writes to Ledger. Atlas through Bus notifies Delta.', [('atlas', 'boreal', 'request'), ('atlas', 'cygnus', 'request'), ('boreal', 'ledger', 'data-write'), ('atlas', 'bus', 'async-message'), ('bus', 'delta', 'async-message')]),
            ('青鸟调用星河和天枢；星河写入账本；青鸟通过队列通知苍穹。', [('青鸟', '星河', 'request'), ('青鸟', '天枢', 'request'), ('星河', '账本', 'data-write'), ('青鸟', '队列', 'async-message'), ('队列', '苍穹', 'async-message')]),
        ]
        for brief, expected in cases:
            plan = brief_to_plan(brief)
            self.assertEqual('explicit-rules-v1', plan['planning']['method'])
            self.assertEqual(set(expected), topology(plan))
            self.assertEqual('not-assessed', plan['planning']['semantic_accuracy'])
            self.assertTrue(all(edge['source_refs'] for edge in plan['semantic']['relations']))
            self.assertTrue(all(brief[item['start']:item['end']] == item['text'] for item in plan['planning']['provenance']))
            self.assertEqual(plan['planning'], compile_scene(compile_plan(plan)).planning)

    def test_review_ecommerce_briefs_keep_domain_entities(self):
        for brief, expected in [(ZH, [('网关','订单服务','request'), ('订单服务','库存服务','request'), ('订单服务','支付服务','request'), ('消息队列','物流服务','async-message'), ('消息队列','积分服务','async-message')]), (EN, [('gateway','order service','request'), ('order service','inventory service','request'), ('order service','payment service','request'), ('message queue','logistics service','async-message'), ('message queue','loyalty service','async-message')])]:
            plan = brief_to_plan(brief)
            self.assertTrue(set(expected).issubset(topology(plan)), topology(plan))
            self.assertGreaterEqual(len(plan['semantic']['entities']), 10)
            self.assertNotIn(('monitoring', 'alerts', 'data-read'), topology(plan))
            self.assertEqual('partial', plan['planning']['coverage']['status'])
            self.assertTrue(plan['planning']['coverage']['unparsed_spans'])
            validate_planning(plan['planning'])
            compile_scene(compile_plan(plan))

    def test_negation_and_ambiguous_pronouns_never_become_positive_edges(self):
        for brief in ('Atlas does not call Boreal.', '青鸟不调用星河。', 'Atlas never calls Boreal.'):
            plan = brief_to_plan(brief)
            self.assertEqual([], plan['semantic']['relations'])
            self.assertIn('brief_rule_negation', [w['code'] for w in plan['planning']['warnings']])
        plan = brief_to_plan('Atlas calls Boreal and Cygnus. It writes to Ledger.')
        self.assertEqual({('atlas','boreal','request'),('atlas','cygnus','request')}, topology(plan))
        self.assertIn('It writes to Ledger', ' '.join(plan['planning']['coverage']['unparsed_spans']))

    def test_relative_subject_and_coordinated_predicates_have_direction(self):
        plan = brief_to_plan('Client calls Gateway, which calls Worker and writes to Ledger.')
        self.assertEqual({('client','gateway','request'),('gateway','worker','request'),('gateway','ledger','data-write')}, topology(plan))
        plan = brief_to_plan('A and B call C. C writes to D.')
        self.assertEqual({('a','c','request'),('b','c','request'),('c','d','data-write')}, topology(plan))

    def test_unsupported_residue_and_conditions_are_retained(self):
        brief = 'If checkout succeeds, Gateway calls Worker. invent unicorn automation.'
        plan = brief_to_plan(brief)
        self.assertEqual('If checkout succeeds', plan['semantic']['relations'][0]['condition'])
        self.assertIn('invent unicorn automation', plan['planning']['coverage']['unparsed_spans'])
        self.assertTrue(any(source.get('note') == brief for source in plan['semantic']['sources']))

    def test_template_is_explicit_and_rules_only_does_not_fabricate_fallback(self):
        self.assertEqual('agent-template-v1', brief_to_plan('Atlas calls Boreal.', planner='template')['planning']['method'])
        self.assertEqual('agent-template-v1', brief_to_plan('Draw an agent with memory and tools.')['planning']['method'])
        self.assertEqual('agent-template-v1', brief_to_plan('Draw tool calls, tool results, and verified output.')['planning']['method'])
        with self.assertRaisesRegex(ValueError, 'No supported explicit relation'):
            brief_to_plan('Design restaurant reservations.', planner='rules')

    def test_ambiguous_only_or_negated_imperative_never_falls_back_to_positive_template(self):
        for brief in ('It calls B.', 'Do not call B.', 'A calls B or C.', '禁止调用支付服务。'):
            with self.subTest(brief=brief), self.assertRaisesRegex(ValueError, 'No positive template'):
                brief_to_plan(brief)

    def test_conditions_containing_verbs_do_not_become_asserted_edges(self):
        plan = brief_to_plan('If A calls B, C writes to D.')
        self.assertEqual({('c', 'd', 'data-write')}, topology(plan))
        self.assertEqual('If A calls B', plan['semantic']['relations'][0]['condition'])
        plan = brief_to_plan('如果支付成功，订单服务调用库存服务。')
        self.assertEqual('如果支付成功', plan['semantic']['relations'][0]['condition'])

    def test_command_requires_explicit_opt_in_and_valid_limits(self):
        with self.assertRaisesRegex(ValueError, "requires planner='subprocess'"):
            brief_to_plan('A calls B.', planner_command=[sys.executable])
        for timeout in (0, -1, True, float('inf'), 301):
            with self.assertRaisesRegex(ValueError, 'timeout'):
                brief_to_plan('brief', planner='subprocess', planner_command=[sys.executable], planner_timeout=timeout)
        for command in (None, [], 'python3', ['python3', 1]):
            with self.assertRaisesRegex(ValueError, 'argv array'):
                brief_to_plan('brief', planner='subprocess', planner_command=command)

    def test_rule_diagnostics_cannot_claim_certification_or_drop_residue_warning(self):
        planning = brief_to_plan('A calls B. Unknown prose.')['planning']
        for changed in ({'semantic_accuracy': 'verified'}, {'warnings': []}, {'coverage': {**planning['coverage'], 'ratio': True}}, {'provenance': [{**planning['provenance'][0], 'status': []}]}):
            with self.assertRaisesRegex(ValueError, 'planning'):
                validate_planning({**deepcopy(planning), **changed})

    def test_cli_rule_plan_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rules.plan.json'
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(['--text', 'A calls B.', '--planner', 'rules', '--formats', 'quality', '--outdir', directory, '--plan-out', str(path)])
            self.assertEqual('explicit-rules-v1', json.loads(stdout.getvalue())['planning']['method'])
            self.assertEqual({('a','b','request')}, topology(json.loads(path.read_text())))

    def test_subprocess_cli_failure_is_structured_and_emits_no_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stub = root / 'invalid.py'
            stub.write_text('print("not-json-secret")\n')
            stderr = io.StringIO()
            with redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
                main(['--text', 'brief', '--planner', 'subprocess', '--planner-command', json.dumps([sys.executable, str(stub)]), '--outdir', directory, '--formats', 'svg', '--plan-out', str(root / 'plan.json')])
            self.assertEqual(2, error.exception.code)
            result = json.loads(stderr.getvalue())
            self.assertEqual('brief_planning_failed', result['error']['code'])
            self.assertNotIn('not-json-secret', stderr.getvalue())
            self.assertFalse((root / 'plan.json').exists())
            self.assertFalse((root / 'diagram.svg').exists())

    def test_subprocess_is_opt_in_validates_and_redacts_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            valid = brief_to_plan('A calls B.', planner='rules')
            stub = root / 'stub.py'
            stub.write_text('import json,sys\nrequest=json.load(sys.stdin)\nassert request["brief"] == "provider brief"\nprint(' + repr(json.dumps(valid)) + ')\n')
            plan = brief_to_plan('provider brief', planner='subprocess', planner_command=[sys.executable, str(stub)])
            self.assertEqual('subprocess-plan-v1', plan['planning']['method'])
            compile_scene(compile_plan(plan))
            stub.write_text('import sys\nprint("secret-provider-token", file=sys.stderr)\nsys.exit(4)\n')
            with self.assertRaisesRegex(ValueError, 'exit code 4') as error:
                brief_to_plan('provider brief', planner='subprocess', planner_command=[sys.executable, str(stub)])
            self.assertNotIn('secret-provider-token', str(error.exception))
            for malformed in ('{}', '[]', '{\"version\": \"0.2\", \"version\": \"0.1\"}', '{\"attributes\": NaN}'):
                stub.write_text('print(' + repr(malformed) + ')\n')
                with self.assertRaisesRegex(ValueError, 'invalid DiagramPlan'):
                    brief_to_plan('provider brief', planner='subprocess', planner_command=[sys.executable, str(stub)])
            stub.write_text('import time\ntime.sleep(2)\n')
            with self.assertRaisesRegex(ValueError, 'timed out'):
                brief_to_plan('provider brief', planner='subprocess', planner_command=[sys.executable, str(stub)], planner_timeout=0.01)


if __name__ == '__main__':
    unittest.main()
