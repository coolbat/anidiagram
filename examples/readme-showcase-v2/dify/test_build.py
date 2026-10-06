"""Test showcase presentation invariants, not Dify runtime or independent semantics."""
import copy
import json
import re
import unittest
from build import REVISION, author_geometry, compile_plan, make_facts, make_plan


class DifyBuildTests(unittest.TestCase):
    def test_translation_changes_copy_only(self):
        def structural(plan):
            result = copy.deepcopy(plan)
            semantic = result["semantic"]
            for field in ("language", "title", "subtitle", "summary"):
                semantic.pop(field)
            for field in ("primary_question", "audience", "scope", "exclusions"):
                semantic["intent"].pop(field)
            for field in ("entities", "relations", "groups", "flows"):
                for item in semantic[field]:
                    item.pop("label", None)
                    item.pop("description", None)
            for item in result["reader"]["views"]:
                item.pop("label")
            return result
        self.assertEqual(structural(make_plan()), structural(make_plan("en")))

    def test_english_plan_and_facts_have_no_untranslated_chinese(self):
        english = make_plan("en")
        self.assertIsNone(re.search(r"[\u3400-\u9fff]", json.dumps([english, make_facts(english)], ensure_ascii=False)))
        compiled = compile_plan(english)
        result = author_geometry(compiled, english["semantic"])
        self.assertEqual(result["evidence"], compiled["evidence"])
        self.assertEqual(len(result["edges"]), 13)

    def test_translated_facts_preserve_evidence_and_required_status(self):
        chinese = make_facts(make_plan())["claims"]
        english = make_facts(make_plan("en"))["claims"]
        for a, b in zip(chinese, english):
            a, b = copy.deepcopy(a), copy.deepcopy(b)
            if a["predicate"] == "behavior":
                a.pop("object")
                b.pop("object")
            self.assertEqual(a, b)
        self.assertEqual(len(chinese), len(english))

    def test_unsupported_language_is_rejected(self):
        with self.assertRaises(ValueError):
            make_plan("fr")

    def test_geometry_preserves_semantics(self):
        plan = make_plan()
        compiled = compile_plan(plan)
        before = copy.deepcopy(compiled)
        result = author_geometry(compiled, plan["semantic"])
        self.assertEqual(compiled, before)
        self.assertEqual(result["evidence"], compiled["evidence"])
        for a, b in zip(compiled["nodes"], result["nodes"]):
            for key in ("id", "label", "caption", "semantic_kind"):
                self.assertEqual(a[key], b[key])
        self.assertEqual(len(result["groups"]), 3)
        self.assertEqual(len(result["nodes"]), 10)

    def test_changed_relation_direction_is_rejected(self):
        plan = make_plan()
        compiled = compile_plan(plan)
        compiled["edges"][0]["from"], compiled["edges"][0]["to"] = compiled["edges"][0]["to"], compiled["edges"][0]["from"]
        with self.assertRaises(AssertionError):
            author_geometry(compiled, plan["semantic"])

    def test_dropped_cache_condition_is_rejected(self):
        plan = make_plan()
        compiled = compile_plan(plan)
        edge = next(e for e in compiled["edges"] if e["semantic_relation_id"] == "api-plugin")
        edge["condition"] = "Every request calls embedding"
        with self.assertRaises(AssertionError):
            author_geometry(compiled, plan["semantic"])

    def test_all_relations_have_required_facts_and_pinned_sources(self):
        plan = make_plan()
        facts = make_facts(plan)["claims"]
        sources = {s["id"] for s in plan["semantic"]["sources"]}
        self.assertEqual(len(facts), 23)
        self.assertTrue(all(f["required"] and set(f["source_refs"]) <= sources for f in facts))
        self.assertTrue(all(s["repository"]["revision"] == REVISION for s in plan["semantic"]["sources"]))
        self.assertEqual({f["subject"] for f in facts if f["predicate"] == "relation"}, {r["id"] for r in plan["semantic"]["relations"]})

    def test_online_query_does_not_include_celery_worker(self):
        plan = make_plan()
        query = next(v for v in plan["reader"]["views"] if v["id"] == "query")
        selected = [r for r in plan["semantic"]["relations"] if r["id"] in query["relation_ids"]]
        self.assertTrue(all("worker" not in (r["from"], r["to"]) for r in selected))
        self.assertIn("api-vector", query["relation_ids"])
        self.assertIn("api-plugin", query["relation_ids"])


if __name__ == "__main__":
    unittest.main()
