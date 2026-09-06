"""Validate public follow-up contracts with an independent JSON Schema implementation.

Development-only dependency: jsonschema 4.x. The engine retains stdlib validators.
"""
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from anidiagram.planner import compile_plan

ROOT = Path(__file__).resolve().parents[1]
schemas = {path.name: json.loads(path.read_text()) for path in (ROOT / "schemas").glob("*.schema.json")}
registry = Registry().with_resources((value["$id"], Resource.from_contents(value)) for value in schemas.values())
count = 0
for schema in schemas.values():
    Draft202012Validator.check_schema(schema)


def check(schema, value):
    global count
    Draft202012Validator(schemas[schema], registry=registry).validate(value)
    count += 1


for path in (ROOT / "examples/verified-reading").glob("*.plan.json"):
    plan = json.loads(path.read_text())
    check("diagram-plan-v0.2.schema.json", plan)
    check("diagram-script-v0.4.schema.json", compile_plan(plan))
for path in (ROOT / "outputs/archify-followups").glob("*.delivery.json"):
    check("delivery-receipt-v0.1.schema.json", json.loads(path.read_text()))
for path in (ROOT / "outputs/archify-followups").glob("*.comparison.json"):
    check("comparison-v0.1.schema.json", json.loads(path.read_text()))
for path in (ROOT / "outputs/archify-followups").glob("*.visual.json"):
    check("visual-check-v0.1.schema.json", json.loads(path.read_text()))
print(json.dumps({"ok": True, "documents": count, "schemas": len(schemas), "validator": "Draft202012Validator"}))
