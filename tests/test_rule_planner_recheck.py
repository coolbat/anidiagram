import unittest

from anidiagram.planner import brief_to_plan, compile_plan
from anidiagram.schema import compile_scene
from anidiagram.planning import validate_planning
from test_rule_planner import topology


REVIEW_EN = ('User places an order through the API gateway into the order service, which calls inventory and payment services. '
             'On payment success, a message queue notifies shipping and loyalty services. '
             'Each service writes to its own database; monitoring collects metrics and raises alerts.')


def labels(plan):
    return {entity['label'].lower() for entity in plan['semantic']['entities']}


class RulePlannerRecheckTests(unittest.TestCase):
    def test_original_review_english_ecommerce_brief(self):
        plan = brief_to_plan(REVIEW_EN)
        edges = topology(plan)
        for edge in [('user', 'api gateway', 'request'), ('api gateway', 'order service', 'request'),
                     ('order service', 'inventory service', 'request'), ('order service', 'payment service', 'request'),
                     ('message queue', 'shipping service', 'async-message'), ('message queue', 'loyalty service', 'async-message'),
                     ('order service', 'order service database', 'data-write'), ('monitoring', 'metrics', 'data-read')]:
            self.assertIn(edge, edges)
        self.assertTrue(labels(plan).isdisjoint({'each service', 'its own database', 'raises alerts'}), labels(plan))
        self.assertIn('payment success', plan['semantic']['relations'][4].get('condition', '').lower())
        self.assertIn('raises alerts', ' '.join(plan['planning']['coverage']['unparsed_spans']))
        validate_planning(plan['planning'])
        compile_scene(compile_plan(plan))

    def test_common_request_read_and_route_phrasings(self):
        cases = [
            ('The API gateway forwards requests to the order service. The order service calls the inventory service and the payment service.',
             {('api gateway', 'order service', 'request'), ('order service', 'inventory service', 'request'), ('order service', 'payment service', 'request')}),
            ('Orders go from the gateway to the order service, then the order service talks to inventory and payment.',
             {('gateway', 'order service', 'request'), ('order service', 'inventory', 'request'), ('order service', 'payment', 'request')}),
            ('The frontend sends requests to the backend, which reads from Redis and writes to Postgres.',
             {('frontend', 'backend', 'request'), ('backend', 'redis', 'data-read'), ('backend', 'postgres', 'data-write')}),
            ('前端把请求发给后端，后端读取 Redis 并写入 Postgres。',
             {('前端', '后端', 'request'), ('后端', 'redis', 'data-read'), ('后端', 'postgres', 'data-write')}),
            ('用户通过网关访问订单服务。', {('用户', '网关', 'request'), ('网关', '订单服务', 'request')}),
            ('The service sends data to analytics and stores logs in S3.',
             {('service', 'analytics', 'request'), ('service', 's3', 'data-write')}),
            ('订单服务把消息推送到消息队列，消息队列通知物流服务。',
             {('订单服务', '消息队列', 'async-message'), ('消息队列', '物流服务', 'async-message')}),
        ]
        for brief, expected in cases:
            with self.subTest(brief=brief):
                plan = brief_to_plan(brief)
                self.assertEqual('explicit-rules-v1', plan['planning']['method'])
                self.assertEqual(expected, topology(plan))

    def test_verb_inside_entity_name_does_not_hide_later_relation(self):
        self.assertEqual({('查询服务', '账本', 'request')}, topology(brief_to_plan('查询服务调用账本。')))

    def test_negated_clause_adverbs_do_not_create_phantom_entities(self):
        plan = brief_to_plan('用户通过网关访问订单服务；订单服务不直接调用物流服务。')
        self.assertEqual({('用户', '网关', 'request'), ('网关', '订单服务', 'request')}, topology(plan))
        self.assertEqual({'用户', '网关', '订单服务', '物流服务'}, labels(plan))
        plan = brief_to_plan('Gateway calls Worker. Worker does not directly call Ledger.')
        self.assertEqual({'gateway', 'worker', 'ledger'}, labels(plan))

    def test_service_suffix_alias_is_merged(self):
        plan = brief_to_plan('The web app calls the auth service. The auth service does not call the billing service. Billing writes to Postgres.')
        self.assertEqual({'web app', 'auth service', 'billing service', 'postgres'}, labels(plan))
        self.assertIn(('billing service', 'postgres', 'data-write'), topology(plan))

    def test_unresolved_relative_clause_does_not_fall_back_to_template(self):
        with self.assertRaisesRegex(ValueError, 'No positive template'):
            brief_to_plan('Requests somehow arrive at the backend, which writes to Postgres.')


if __name__ == '__main__':
    unittest.main()
