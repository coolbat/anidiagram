import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from pathlib import Path

from anidiagram.cli import main
from anidiagram.planner import brief_to_plan, compile_plan
from anidiagram.quality import quality_report
from anidiagram.schema import DiagramScriptValidationError, compile_scene
from anidiagram.styles import load_style


ECOMMERCE_BRIEFS = (
    "构建电商订单系统：用户下单经过网关进入订单服务，订单服务调用库存服务和支付服务，支付成功后通过消息队列通知物流服务和积分服务，所有服务写入各自数据库，监控系统采集指标并告警。",
    "Build an ecommerce order system: requests pass through a gateway to the order service, which calls inventory and payment services. After payment succeeds, a message queue notifies logistics and loyalty services. All services write to databases; monitoring collects metrics and alerts.",
)


class BriefDiagnosticsTests(unittest.TestCase):
    def test_ecommerce_omissions_are_visible_in_both_languages(self):
        for brief in ECOMMERCE_BRIEFS:
            with self.subTest(brief=brief):
                plan = brief_to_plan(brief, planner="template")
                planning = plan["planning"]
                self.assertEqual("not-assessed", planning["semantic_accuracy"])
                self.assertEqual("partial", planning["coverage"]["status"])
                self.assertIn("gateway", planning["coverage"]["unmatched_terms"])
                self.assertIn("payment", planning["coverage"]["unmatched_terms"])
                self.assertIn("message-queue", planning["coverage"]["unmatched_terms"])
                self.assertLess(planning["coverage"]["ratio"], 0.5)
                scene = compile_scene(compile_plan(plan))
                self.assertEqual(planning, scene.planning)
                report = quality_report(scene, load_style())
                self.assertEqual(planning, report["planning"])
                self.assertIn("brief_coverage_low", [issue["code"] for issue in report["issues"]])

    def test_supported_template_reports_only_known_term_coverage(self):
        plan = brief_to_plan("An agent receives a request, uses memory and search tools, validates policy, then retries from feedback and returns output.")
        planning = plan["planning"]
        self.assertEqual("agent-template-v1", planning["method"])
        self.assertEqual("known-term-heuristic-v1", planning["coverage"]["method"])
        self.assertEqual("template-match", planning["coverage"]["status"])
        self.assertEqual(1.0, planning["coverage"]["ratio"])
        self.assertEqual([], planning["warnings"])
        self.assertEqual("not-assessed", planning["semantic_accuracy"])
        self.assertIn("not", planning["limitations"])

    def test_unrecognized_domain_or_language_is_unassessed(self):
        for brief in ("Design restaurant seating reservations.", "Опишите бронирование столиков.", "予約システムを表示してください", "", "An agent handles an unspecified workflow."):
            with self.subTest(brief=brief):
                planning = brief_to_plan(brief)["planning"]
                self.assertEqual("unassessed", planning["coverage"]["status"])
                self.assertIsNone(planning["coverage"]["ratio"])
                self.assertIn("brief_coverage_unassessed", [warning["code"] for warning in planning["warnings"]])

    def test_known_agent_terms_do_not_hide_an_unrecognized_business_domain(self):
        for brief in ("An agent uses memory and tools for restaurant reservations.",
                      "智能体使用记忆和工具处理酒店预订。"):
            planning = brief_to_plan(brief)["planning"]
            self.assertEqual("unassessed", planning["coverage"]["status"])
            self.assertIsNone(planning["coverage"]["ratio"])
            self.assertTrue(planning["coverage"]["unrecognized_fragments"])
            self.assertEqual("brief_coverage_unassessed", planning["warnings"][0]["code"])

    def test_english_copy_does_not_stitch_input_keywords(self):
        plan = brief_to_plan("Show a user request flowing through an API gateway, an AI agent, tools, validation, and a verified output.")
        self.assertEqual("Agent workflow template", plan["semantic"]["title"])
        self.assertEqual("input brief", plan["semantic"]["entities"][0]["description"])
        self.assertIn("template", plan["semantic"]["subtitle"])
        self.assertNotIn("extracted directly", plan["semantic"]["flows"][0]["description"])
        self.assertEqual("My title", brief_to_plan("agent memory tool", title="My title")["semantic"]["title"])

    def test_cli_warnings_survive_delivery_and_saved_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan_path = root / "ecommerce.plan.json"
            spec_path = root / "ecommerce.diagram.json"
            for source in (["--text", ECOMMERCE_BRIEFS[0], "--planner", "template", "--plan-out", str(plan_path), "--spec-out", str(spec_path)],
                           ["--plan", str(plan_path)], ["--spec", str(spec_path)]):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    main([*source, "--outdir", directory, "--basename", "ecommerce", "--formats", "quality", "--deliver"])
                result = json.loads(stdout.getvalue())
                self.assertTrue(result["ok"])
                self.assertEqual("partial", result["planning"]["coverage"]["status"])
                self.assertIn("brief_coverage_low", [warning["code"] for warning in result["planning"]["warnings"]])
                report = json.loads((root / "ecommerce.quality.json").read_text())
                receipt = json.loads((root / "ecommerce.delivery.json").read_text())
                self.assertGreaterEqual(report["summary"]["warnings"], 1)
                self.assertGreaterEqual(receipt["validation"]["quality"]["warnings"], 1)

    def test_cli_reports_template_limitations_without_quality_export(self):
        with tempfile.TemporaryDirectory() as directory:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                main(["--text", ECOMMERCE_BRIEFS[1], "--outdir", directory, "--formats", "svg"])
            result = json.loads(stdout.getvalue())
            self.assertIn("planning", result)
            self.assertEqual("not-assessed", result["planning"]["semantic_accuracy"])
            self.assertTrue(result["planning"]["warnings"])

    def test_invalid_diagnostics_are_rejected_at_plan_and_script_boundaries(self):
        valid = brief_to_plan("An agent uses memory and tools.")
        for bad_value in ({}, {**valid["planning"], "semantic_accuracy": "verified"},
                          {**valid["planning"], "coverage": {**valid["planning"]["coverage"], "ratio": True}},
                          {**valid["planning"], "coverage": {**valid["planning"]["coverage"], "ratio": 0.5}},
                          {**brief_to_plan(ECOMMERCE_BRIEFS[0])["planning"], "warnings": []},
                          {**valid["planning"], "coverage": {**valid["planning"]["coverage"], "status": []}}):
            with self.subTest(bad_value=bad_value):
                plan = deepcopy(valid)
                plan["planning"] = bad_value
                with self.assertRaisesRegex(ValueError, "planning"):
                    compile_plan(plan)
                spec = compile_plan(valid)
                spec["planning"] = bad_value
                with self.assertRaisesRegex(DiagramScriptValidationError, "planning"):
                    compile_scene(spec)

    def test_keyword_boundaries_do_not_treat_capital_as_an_api_tool(self):
        plan = brief_to_plan("A capital budgeting process.")
        self.assertNotIn("tool", [entity["id"] for entity in plan["semantic"]["entities"]])


if __name__ == "__main__":
    unittest.main()
