import unittest

from anidiagram.planner import brief_to_plan, compile_plan
from anidiagram.quality import quality_report
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style


class PlannerLocaleTest(unittest.TestCase):
    def test_chinese_and_english_equivalent_briefs_preserve_semantic_topology(self):
        briefs = (
            "Draw a loop architecture with user request, agent, long term memory, search tool, safety validation, retry, and output",
            "画一个包含用户请求、智能体、长期记忆、搜索工具、安全校验、失败重试和最终输出的循环架构图",
        )
        plans = [brief_to_plan(brief) for brief in briefs]

        entity_kinds = [
            [entity["kind"] for entity in plan["semantic"]["entities"]]
            for plan in plans
        ]
        relation_shapes = [
            [(relation["from"], relation["to"], relation["kind"]) for relation in plan["semantic"]["relations"]]
            for plan in plans
        ]
        flow_shapes = [
            [(flow["repeat"], tuple(flow["relation_ids"])) for flow in plan["semantic"]["flows"]]
            for plan in plans
        ]

        self.assertEqual(entity_kinds[0], entity_kinds[1])
        self.assertEqual(relation_shapes[0], relation_shapes[1])
        self.assertEqual(flow_shapes[0], flow_shapes[1])
        self.assertEqual("请求", plans[1]["semantic"]["entities"][0]["label"])
        self.assertEqual("搜索工具", plans[1]["semantic"]["entities"][3]["label"])

    def test_chinese_plan_compiles_with_clean_quality(self):
        plan = brief_to_plan("用户请求进入智能体，读取长期记忆，调用搜索工具，经过安全校验，失败时循环重试，最后输出结果")
        spec = compile_plan(plan)
        scene = compile_scene(spec)

        self.assertEqual("illustrated", scene.icon_system)
        self.assertEqual("showcase-v1", scene.motion.profile)
        self.assertEqual(0, quality_report(scene, load_style())["summary"]["errors"])


if __name__ == "__main__":
    unittest.main()
