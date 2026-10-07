import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from anidiagram.cli import main
from anidiagram.planner import brief_to_plan, compile_plan
from anidiagram.quality import quality_report
from anidiagram.renderer_svg import render_svg
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style


ROOT = Path(__file__).resolve().parents[1]


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

        self.assertEqual("zh-CN", plan["semantic"]["language"])
        self.assertEqual("zh-CN", spec["locale"])
        self.assertEqual("zh-CN", scene.locale)
        self.assertEqual("illustrated", scene.icon_system)
        self.assertEqual("showcase-v1", scene.motion.profile)
        self.assertEqual(0, quality_report(scene, load_style())["summary"]["errors"])

    def test_long_chinese_brief_keeps_visible_architecture_copy_in_chinese(self):
        plan = brief_to_plan(
            "构建企业级智能体平台架构：用户请求进入 API 网关，智能体读取长期记忆，"
            "调用搜索工具和知识库，经过安全校验后输出结果；失败时根据反馈重新规划并重试。",
            planner="template",
        )
        semantic = plan["semantic"]

        self.assertEqual("zh-CN", semantic["language"])
        self.assertEqual("企业级智能体平台架构", semantic["title"])
        self.assertEqual("智能体流程模板草稿，需对照原始需求核验。", semantic["subtitle"])
        self.assertEqual(["技术团队"], semantic["intent"]["audience"])
        self.assertEqual("主请求流程", semantic["flows"][0]["label"])
        self.assertEqual(
            ["处理请求", "读取上下文", "返回上下文", "调用工具", "执行校验", "输出结果", "失败重试"],
            [relation["label"] for relation in semantic["relations"]],
        )

    def test_explicit_chinese_locale_overrides_an_english_brief(self):
        plan = brief_to_plan(
            "Build an agent architecture with memory, search tools, validation, retry, and output.",
            language="zh-CN",
        )

        self.assertEqual("zh-CN", plan["semantic"]["language"])
        self.assertEqual("请求", plan["semantic"]["entities"][0]["label"])
        self.assertEqual("主请求流程", plan["semantic"]["flows"][0]["label"])

    def test_chinese_svg_declares_language_and_cjk_font_fallbacks(self):
        scene = compile_scene(compile_plan(brief_to_plan("画一个智能体、知识库、搜索工具和安全校验组成的中文架构图")))
        svg = render_svg(scene, load_style())

        self.assertIn('lang="zh-CN"', svg)
        self.assertIn('xml:lang="zh-CN"', svg)
        self.assertIn('data-locale="zh-CN"', svg)
        self.assertIn('"Noto Sans CJK SC"', svg)
        self.assertIn('"PingFang SC"', svg)
        self.assertIn("paint-order: stroke", svg)

    def test_cli_generates_chinese_plan_spec_svg_and_html_end_to_end(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(
                    [
                        "--text",
                        "Build an agent architecture with memory, search tools, validation, retry, and output.",
                        "--diagram-locale",
                        "zh-CN",
                        "--viewer-locale",
                        "auto",
                        "--runtime-dependency",
                        "none",
                        "--outdir",
                        directory,
                        "--basename",
                        "chinese-agent",
                        "--formats",
                        "svg,html,quality",
                        "--plan-out",
                        str(root / "chinese-agent.plan.json"),
                        "--spec-out",
                        str(root / "chinese-agent.diagram.json"),
                    ]
                )

            result = json.loads(stdout.getvalue())
            plan = json.loads((root / "chinese-agent.plan.json").read_text(encoding="utf-8"))
            spec = json.loads((root / "chinese-agent.diagram.json").read_text(encoding="utf-8"))
            svg = (root / "chinese-agent.svg").read_text(encoding="utf-8")
            html = (root / "chinese-agent.html").read_text(encoding="utf-8")

            self.assertTrue(result["ok"])
            self.assertEqual("zh-CN", result["locale"])
            self.assertEqual("zh-CN", plan["semantic"]["language"])
            self.assertEqual("zh-CN", spec["locale"])
            self.assertIn("主请求流程", json.dumps(plan, ensure_ascii=False))
            self.assertIn('data-locale="zh-CN"', svg)
            self.assertIn('<html lang="zh-CN">', html)
            self.assertEqual(0, result["outputs"]["quality"]["summary"]["errors"])

    def test_chinese_layered_loop_uses_distinct_pair_channels_and_external_retry(self):
        plan = json.loads(
            (ROOT / "examples" / "zh-CN" / "enterprise-agent-platform.plan.json").read_text(encoding="utf-8")
        )
        spec = compile_plan(plan)
        edges = {edge["semantic_relation_id"]: edge for edge in spec["edges"]}
        nodes = {node["id"]: node for node in spec["nodes"]}
        group_left = min(group["bounds"][0] for group in spec["groups"])
        group_right = max(group["bounds"][0] + group["bounds"][2] for group in spec["groups"])

        self.assertEqual(1020, spec["canvas"]["width"])
        self.assertEqual(group_left, spec["canvas"]["width"] - group_right)

        self.assertEqual(("agent-orchestrator", "safety-gate"), (edges["agent-validates"]["from"], edges["agent-validates"]["to"]))
        self.assertEqual(("safety-gate", "verified-output"), (edges["gate-delivers"]["from"], edges["gate-delivers"]["to"]))
        self.assertEqual(("verified-output", "agent-orchestrator"), (edges["output-retries"]["from"], edges["output-retries"]["to"]))

        retry = edges["output-retries"]
        self.assertEqual("orthogonal", retry["route"])
        self.assertGreaterEqual(len(retry["points"]), 3)

        pair_ids = (
            "agent-reads-memory", "memory-returns",
            "agent-retrieves", "knowledge-grounds",
            "agent-searches", "search-returns",
        )
        self.assertTrue(all("step" not in edges[relation_id] for relation_id in (*pair_ids, "output-retries")))
        self.assertTrue(all("step" in edges[relation_id] for relation_id in ("request-enters", "gateway-routes", "agent-validates", "gate-delivers")))
        paths = []
        for relation_id in pair_ids:
            edge = edges[relation_id]
            self.assertEqual("orthogonal", edge["route"])
            self.assertGreaterEqual(len(edge["points"]), 2)
            paths.append(tuple(map(tuple, edge["points"])))
        self.assertEqual(len(pair_ids), len(set(paths)))
        report = quality_report(compile_scene(spec), load_style())
        self.assertFalse([issue for issue in report["issues"] if "collision" in issue["code"]], report["issues"])

        for edge in edges.values():
            self.assertEqual("orthogonal", edge["route"])
            for left, right in zip(edge["points"], edge["points"][1:]):
                for node_id, node in nodes.items():
                    if node_id in {edge["from"], edge["to"]}:
                        continue
                    self.assertFalse(
                        self._segment_crosses_node(left, right, node),
                        f"{edge['semantic_relation_id']} crosses {node_id}: {left} -> {right}",
                    )

    @staticmethod
    def _segment_crosses_node(left, right, node):
        x, y = node["position"]
        width, height = node["size"]
        inset = 2
        min_x, max_x = x + inset, x + width - inset
        min_y, max_y = y + inset, y + height - inset
        if left[0] == right[0]:
            return min_x < left[0] < max_x and max(min(left[1], right[1]), min_y) < min(max(left[1], right[1]), max_y)
        if left[1] == right[1]:
            return min_y < left[1] < max_y and max(min(left[0], right[0]), min_x) < min(max(left[0], right[0]), max_x)
        return False


if __name__ == "__main__":
    unittest.main()
