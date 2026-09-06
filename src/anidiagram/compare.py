"""Compare authored Plan meaning by stable IDs and report layout changes separately."""

from copy import deepcopy
from html import escape
import json
from pathlib import Path

from .artifact_bundle import commit_bundle
from .delivery import canonical_json_bytes, digest_bytes
from .planner import compile_plan
from .quality import quality_report
from .renderer_html_runtime import render_html_runtime
from .schema import compile_scene
from .styles import load_style
from .resources import resource_path


def _normalize(value, key=""):
    if isinstance(value, dict):
        return {name: _normalize(item, name) for name, item in sorted(value.items())}
    if isinstance(value, list):
        items = [_normalize(item) for item in value]
        # relation_ids is ordered choreography; do not sort it.
        if key in {"entities", "relations", "groups", "flows", "sources"}:
            return sorted(items, key=lambda item: item["id"])
        if key in {"source_refs", "members", "tags", "audience", "exclusions", "annotations"}:
            return sorted(items)
        return items
    return value


def canonical_semantic(plan):
    semantic = deepcopy(plan["semantic"])
    for collection in ("relations", "groups", "flows", "sources"):
        semantic.setdefault(collection, [])
    for relation in semantic["relations"]:
        relation.setdefault("direction", "forward")
    for flow in semantic["flows"]:
        flow.setdefault("repeat", "once")
    return _normalize(semantic)


def _fields(before, after):
    return [field for field in sorted(set(before) | set(after)) if before.get(field) != after.get(field)]


def compare_plans(base, head):
    if base.get("version") != "0.2" or head.get("version") != "0.2":
        raise ValueError("semantic comparison requires DiagramPlan 0.2 with stable IDs")
    specifications = [compile_plan(plan) for plan in (base, head)]
    old, new = canonical_semantic(base), canonical_semantic(head)
    changes = []
    for collection in ("entities", "relations", "groups", "flows", "sources"):
        before = {item["id"]: item for item in old[collection]}
        after = {item["id"]: item for item in new[collection]}
        for item_id in sorted(set(before) | set(after)):
            left, right = before.get(item_id), after.get(item_id)
            if left == right:
                continue
            fields = _fields(left or {}, right or {})
            categories = set()
            for field in fields:
                category = ("evidence" if collection == "sources" or field == "source_refs" else
                            "topology" if collection == "relations" and field in {"from", "to", "direction"} else
                            "scope" if collection == "groups" and field in {"members", "parent"} else "semantic")
                categories.add(category)
            changes.append({"collection": collection, "id": item_id,
                            "status": "added" if left is None else "removed" if right is None else "changed",
                            "categories": sorted(categories), "fields": fields, "before": left, "after": right})
    root_fields = _fields({k: v for k, v in old.items() if k not in {"entities", "relations", "groups", "flows", "sources"}},
                          {k: v for k, v in new.items() if k not in {"entities", "relations", "groups", "flows", "sources"}})
    for field in root_fields:
        changes.append({"collection": "semantic", "id": field, "status": "changed", "categories": ["semantic"],
                        "fields": [field], "before": old.get(field), "after": new.get(field)})
    geometry = []
    for collection, identity, fields in (("nodes", "id", ("position", "size", "shape")),
                                        ("edges", "semantic_relation_id", ("route", "points")),
                                        ("groups", "id", ("bounds",))):
        before = {item[identity]: item for item in specifications[0][collection]}
        after = {item[identity]: item for item in specifications[1][collection]}
        for item_id in sorted(set(before) & set(after)):
            left = {key: before[item_id].get(key) for key in fields}
            right = {key: after[item_id].get(key) for key in fields}
            if left != right:
                geometry.append({"collection": collection, "id": item_id, "status": "rerouted" if collection == "edges" else "moved", "before": left, "after": right})
    presentation = []
    for field in ("presentation", "presentation_sources", "reader"):
        if base.get(field) != head.get(field):
            presentation.append({"field": field, "before": base.get(field), "after": head.get(field)})
    return {"schema": {"name": "AniDiagramComparison", "version": "0.1"},
            "semantic_changes": changes, "presentation_changes": presentation, "geometry_changes": geometry,
            "semantic_equal": old == new,
            "summary": {"semantic": len(changes), "presentation": len(presentation), "geometry": len(geometry)},
            "canonical": {"base": digest_bytes(canonical_json_bytes(old)), "head": digest_bytes(canonical_json_bytes(new))}}


def deliver_comparison(base_path, head_path, output, *, receipt=None, repo_root=None):
    base_path, head_path, output = Path(base_path), Path(head_path), Path(output).absolute()
    receipt_path = Path(receipt).absolute() if receipt else output.with_suffix(".comparison.json")
    if output == receipt_path:
        raise ValueError("comparison HTML and receipt must use distinct paths")
    raw = [path.read_bytes() for path in (base_path, head_path)]
    plans = [json.loads(data) for data in raw]
    result = compare_plans(*plans)
    previews, validation = [], []
    for plan in plans:
        scene = compile_scene(compile_plan(plan), repo_root=repo_root)
        style = load_style(resource_path("styles", scene.style.name + ".json"))
        quality = quality_report(scene, style)
        if quality["summary"]["errors"]:
            raise ValueError("comparison requires both diagrams to pass the quality error gate")
        validation.append(quality["summary"])
        previews.append(render_html_runtime(scene, style, dependency_mode="none"))
    rows = []
    for name in ("semantic_changes", "presentation_changes", "geometry_changes"):
        rows.append(f'<h2>{escape(name)}</h2>')
        for entry in result[name]:
            rows.append('<details><summary>' + escape(str(entry.get("id", entry.get("field")))) + ' · ' + escape(entry.get("status", "changed")) + '</summary><pre>' + escape(json.dumps(entry, ensure_ascii=False, indent=2)) + '</pre></details>')
        if not result[name]:
            rows.append('<p>No changes / 无变化</p>')
    html = ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>AniDiagram — Architecture comparison</title><style>body{font:16px system-ui;margin:24px;background:#f8fafc;color:#172033}'
            'iframe{width:100%;height:75vh;border:1px solid #cbd5e1}pre{white-space:pre-wrap;overflow-wrap:anywhere}details{padding:8px}nav a{margin-right:20px}</style>'
            '<h1>Architecture comparison / 架构变化</h1><nav><a href="#before">Before</a><a href="#delta">Delta</a><a href="#after">After</a></nav>'
            '<section id="delta"><h2>Delta</h2><p>' + escape(json.dumps(result["summary"])) + '</p>' + ''.join(rows) + '</section>'
            '<section id="before"><h2>Before</h2><iframe title="Before" sandbox="allow-scripts" srcdoc="' + escape(previews[0], quote=True) + '"></iframe></section>'
            '<section id="after"><h2>After</h2><iframe title="After" sandbox="allow-scripts" srcdoc="' + escape(previews[1], quote=True) + '"></iframe></section></html>').encode()
    result["inputs"] = {side: digest_bytes(data) for side, data in zip(("base", "head"), raw)}
    result["validation"] = validation
    result["artifact"] = {"path": output.name, **digest_bytes(html)}
    commit_bundle({output: html, receipt_path: canonical_json_bytes(result)}, inputs=(base_path, head_path))
    return {"ok": True, "output": str(output), "receipt": str(receipt_path), **result["summary"]}
