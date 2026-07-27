#!/usr/bin/env python3
"""Render the approved curated showcase used by the GitHub README.

The proof deliberately isolates the three presentation questions:

* three README hero cases;
* one fixed semantic diagram rendered through three templates;
* two topology-specific examples using one icon system and one template.

The generated page remains a convenient visual QA surface for the tracked
README assets.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from functools import partial
from html import escape
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anidiagram.exporters import write_html, write_quality, write_svg
from anidiagram.planner import compile_plan
from anidiagram.quality import quality_report
from anidiagram.renderer_svg import render_svg
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style


Spec = dict[str, Any]
CANVAS = {"width": 1600, "height": 900}

CASES = (
    {
        "id": "hero-loop-engineering",
        "kind": "hero",
        "label": "Hero · Layered Loop",
        "style": "minimal-light",
        "layout": "layered-loop",
        "icon_system": "illustrated",
    },
    {
        "id": "hero-governed-rag",
        "kind": "hero",
        "label": "Hero candidate",
        "style": "minimal-light",
        "layout": "layered",
        "icon_system": "illustrated",
    },
    {
        "id": "hero-kubernetes-three-layer",
        "kind": "hero",
        "label": "Hero candidate · Three layers",
        "style": "deep-tech",
        "layout": "layered",
        "icon_system": "diagram-core-v1",
    },
    {
        "id": "template-agent-lifecycle-minimal-light",
        "kind": "template",
        "label": "Template · Minimal Light",
        "style": "minimal-light",
        "layout": "layered",
        "icon_system": "illustrated",
    },
    {
        "id": "template-agent-lifecycle-deep-tech",
        "kind": "template",
        "label": "Template · Deep Tech",
        "style": "deep-tech",
        "layout": "layered",
        "icon_system": "illustrated",
    },
    {
        "id": "template-agent-lifecycle-claude-warm",
        "kind": "template",
        "label": "Template · Claude Warm",
        "style": "claude-warm",
        "layout": "layered",
        "icon_system": "illustrated",
    },
    {
        "id": "layout-enterprise-rag-pipeline",
        "kind": "layout",
        "label": "Layout · Pipeline",
        "style": "minimal-light",
        "layout": "pipeline",
        "icon_system": "diagram-core-v1",
    },
    {
        "id": "layout-mcp-tool-hub",
        "kind": "layout",
        "label": "Layout · Hub & Spoke",
        "style": "minimal-light",
        "layout": "hub-spoke",
        "icon_system": "diagram-core-v1",
    },
)


def _node(
    node_id: str,
    label: str,
    caption: str,
    icon: str,
    role: str,
    x: int,
    y: int,
    width: int = 240,
    height: int = 150,
) -> Spec:
    return {
        "id": node_id,
        "label": label,
        "caption": caption,
        "position": [x, y],
        "size": [width, height],
        "role": role,
        "icon": icon,
        "importance": "primary" if role in {"actor", "agent", "output"} else "supporting",
    }


def _edge(
    source: str,
    target: str,
    label: str,
    index: int,
    *,
    role: str = "process",
    route: str = "curved",
    effect: str | None = None,
    importance: str = "primary",
    flow_id: str = "primary-flow",
    flow_repeat: str = "event-driven",
) -> Spec:
    motion = effect or ("packet-flow", "comet-flow", "stream-flow")[index % 3]
    return {
        "from": source,
        "to": target,
        "label": label,
        "role": role,
        "route": route,
        "animated": True,
        "delay": round(index * 0.08, 2),
        "importance": importance,
        "flow_id": flow_id,
        "flow_importance": importance,
        "flow_repeat": flow_repeat,
        "effect": {
            "preset": motion,
            "particle": "high-contrast-dot" if motion in {"packet-flow", "comet-flow"} else "soft-dot",
            "trail": motion == "comet-flow",
        },
    }


def _base_spec(
    *,
    title: str,
    subtitle: str,
    style: str,
    icon_system: str,
    layout: str,
    nodes: list[Spec],
    edges: list[Spec],
) -> Spec:
    icon_axis: Spec = {"value": icon_system, "source": "explicit"}
    if icon_system == "illustrated":
        icon_axis["version"] = "2.5.0"
    return {
        "version": "0.4",
        "composition_policy": "composition-v1",
        "resolved_presentation": {
            "icon_system": icon_axis,
            "style": {"value": style, "source": "explicit"},
            "layout": {"value": layout, "source": "explicit"},
            "motion": {"value": "showcase-v1", "source": "explicit"},
        },
        "icon_system": icon_system,
        "layout": layout,
        "preset": layout,
        "canvas": dict(CANVAS),
        "style": style,
        "title": {"text": title, "subtitle": subtitle},
        "motion": {
            "profile": "showcase-v1",
            "sequence": "staged",
            "ease": "spring",
            "stagger": 0.08,
            "duration_scale": 1.0,
            "intensity": 1.0,
            "node": {"preset": "icon-performance"},
            "edge": {"preset": "packet-flow", "particle": "high-contrast-dot", "trail": False},
            "group": {"preset": "none"},
            "title": {"preset": "highlight-sweep"},
            "reduced_motion": "static",
        },
        "motion_policy": {
            "profile": "unrestricted",
            "motion_area": "unrestricted",
            "max_active_flow_edges": len(edges),
            "max_particle_edges": len(edges),
            "particle_count_per_edge": 1,
            "flow_trail_count": 2,
            "max_active_pulse_nodes": len(nodes),
            "pulse_mode": "all",
            "max_scanning_groups": 0,
        },
        "nodes": nodes,
        "edges": edges,
    }


def _loop_engineering_spec() -> Spec:
    plan = json.loads((ROOT / "examples" / "loop-engineering-minimal-light.plan.json").read_text(encoding="utf-8"))
    return compile_plan(plan)


def _hero_spec() -> Spec:
    nodes = [
        _node("user", "Application User", "submits governed query", "user", "actor", 40, 210),
        _node("gateway", "Policy Gateway", "authenticates and scopes", "gateway", "risk", 350, 210),
        _node("agent", "RAG Agent", "plans grounded response", "agent", "agent", 660, 210),
        _node("model", "Language Model", "generates with evidence", "llm", "agent", 970, 210),
        _node("output", "Cited Output", "returns traceable answer", "output", "output", 1280, 210),
        _node("documents", "Source Documents", "approved knowledge corpus", "document", "source", 40, 600),
        _node("tokenizer", "Tokenizer", "segments and budgets", "token", "process", 350, 600),
        _node("embedding", "Embedding Service", "vectorizes document chunks", "embedding", "process", 660, 600),
        _node("index", "Vector Index", "retrieves semantic matches", "vector-database", "memory", 970, 600),
        _node("monitoring", "Runtime Monitoring", "observes quality and latency", "monitoring", "process", 1280, 600),
    ]
    links = [
        ("user", "gateway", "query", "actor", "online-query"),
        ("gateway", "agent", "admit", "risk", "online-query"),
        ("agent", "model", "grounded prompt", "agent", "online-query"),
        ("model", "output", "cited response", "output", "online-query"),
        ("documents", "tokenizer", "content", "source", "knowledge-preparation"),
        ("tokenizer", "embedding", "chunks", "process", "knowledge-preparation"),
        ("embedding", "index", "vectors", "memory", "knowledge-preparation"),
        ("index", "agent", "retrieve", "memory", "online-query"),
        ("agent", "monitoring", "telemetry", "process", "observability"),
    ]
    edges = [
        _edge(source, target, label, index, role=role, flow_id=flow_id, flow_repeat="loop" if index in {4, 5, 6, 8} else "event-driven")
        for index, (source, target, label, role, flow_id) in enumerate(links)
    ]
    return _base_spec(
        title="Governed RAG Production Architecture",
        subtitle="Knowledge preparation · policy-scoped retrieval · evidence-backed response",
        style="minimal-light",
        icon_system="illustrated",
        layout="layered",
        nodes=nodes,
        edges=edges,
    )


def _kubernetes_three_layer_spec() -> Spec:
    nodes = [
        _node("external-users", "External Users", "production application traffic", "user", "actor", 85, 185, 250, 120),
        _node("automation-clients", "Automation Clients", "CI/CD and platform APIs", "api", "source", 450, 185, 250, 120),
        _node("platform-operators", "Platform Operators", "operate and troubleshoot", "operator", "actor", 815, 185, 250, 120),
        _node("security-policy", "Security Policy", "identity and admission rules", "shield", "risk", 1180, 185, 250, 120),
        _node("ingress", "Ingress Gateway", "routes trusted traffic", "gateway", "risk", 85, 390, 250, 125),
        _node("api-server", "Kubernetes API", "declares desired state", "api", "process", 450, 390, 250, 125),
        _node("scheduler", "Scheduler", "places workloads", "scheduler", "process", 815, 390, 250, 125),
        _node("controller", "Control Plane", "reconciles cluster state", "server-cluster", "agent", 1180, 390, 250, 125),
        _node("deployments", "Deployments", "versioned application releases", "deployment", "process", 85, 620, 250, 140),
        _node("containers", "Container Workloads", "replicated services", "container", "process", 450, 620, 250, 140),
        _node("stateful-data", "Stateful Data", "persistent production data", "database", "memory", 815, 620, 250, 140),
        _node("observability", "Observability", "metrics, logs, and alerts", "monitoring", "output", 1180, 620, 250, 140),
    ]
    links = [
        ("external-users", "ingress", "request", "actor", "traffic"),
        ("automation-clients", "api-server", "automate", "source", "operations"),
        ("platform-operators", "scheduler", "operate", "actor", "operations"),
        ("security-policy", "controller", "enforce", "risk", "governance"),
        ("ingress", "api-server", "admit", "risk", "control-plane"),
        ("api-server", "scheduler", "schedule", "process", "control-plane"),
        ("scheduler", "controller", "reconcile", "agent", "control-plane"),
        ("ingress", "deployments", "route", "process", "runtime"),
        ("api-server", "containers", "deploy", "process", "runtime"),
        ("scheduler", "stateful-data", "place", "memory", "runtime"),
        ("controller", "observability", "telemetry", "output", "reliability"),
    ]
    edges = [
        _edge(
            source,
            target,
            label,
            index,
            role=role,
            route="straight" if index in {0, 1, 2, 3, 7, 8, 9, 10} else "curved",
            flow_id=flow_id,
            flow_repeat="loop" if flow_id in {"traffic", "runtime", "reliability"} else "event-driven",
        )
        for index, (source, target, label, role, flow_id) in enumerate(links)
    ]
    spec = _base_spec(
        title="Kubernetes Production Architecture",
        subtitle="Traffic & operations → Kubernetes control plane → runtime & reliability",
        style="deep-tech",
        icon_system="diagram-core-v1",
        layout="layered",
        nodes=nodes,
        edges=edges,
    )
    spec["groups"] = [
        {"id": "traffic-operations", "label": "Traffic & Operations", "bounds": [40, 145, 1520, 180], "role": "actor", "importance": "primary"},
        {"id": "control-plane", "label": "Kubernetes Control Plane", "bounds": [40, 350, 1520, 190], "role": "agent", "importance": "primary"},
        {"id": "runtime-reliability", "label": "Runtime & Reliability", "bounds": [40, 570, 1520, 245], "role": "process", "importance": "primary"},
    ]
    return spec


def _template_spec(style: str) -> Spec:
    nodes = [
        _node("user", "User Request", "goal and context", "user", "actor", 40, 215),
        _node("gateway", "API Gateway", "authenticate and route", "gateway", "risk", 350, 215),
        _node("agent", "Agent Runtime", "plan and coordinate", "agent", "agent", 660, 215),
        _node("model", "Language Model", "reason and generate", "llm", "agent", 970, 215),
        _node("output", "Verified Output", "deliver and explain", "output", "output", 1280, 215),
        _node("knowledge", "Knowledge Base", "retrieve trusted facts", "knowledge-base", "source", 195, 605),
        _node("memory", "Working Memory", "retain task context", "memory", "memory", 505, 605),
        _node("tool", "Tool Execution", "act on external systems", "tool", "tool", 815, 605),
        _node("monitoring", "Runtime Monitoring", "measure quality and cost", "monitoring", "process", 1125, 605),
    ]
    links = [
        ("user", "gateway", "request", "actor", "request-lifecycle"),
        ("gateway", "agent", "dispatch", "risk", "request-lifecycle"),
        ("agent", "model", "prompt", "agent", "request-lifecycle"),
        ("model", "output", "answer", "output", "request-lifecycle"),
        ("knowledge", "agent", "grounding", "source", "agent-context"),
        ("memory", "agent", "recall", "memory", "agent-context"),
        ("agent", "tool", "execute", "tool", "tool-loop"),
        ("tool", "agent", "result", "tool", "tool-loop"),
        ("agent", "monitoring", "telemetry", "process", "observability"),
    ]
    edges = [
        _edge(
            source,
            target,
            label,
            index,
            role=role,
            flow_id=flow_id,
            importance="supporting" if index >= 4 else "primary",
            flow_repeat="loop" if index >= 4 else "event-driven",
        )
        for index, (source, target, label, role, flow_id) in enumerate(links)
    ]
    return _base_spec(
        title="Production AI Agent Request Lifecycle",
        subtitle="One semantic diagram · three visual templates · unchanged content and geometry",
        style=style,
        icon_system="illustrated",
        layout="layered",
        nodes=nodes,
        edges=edges,
    )


def _pipeline_spec() -> Spec:
    nodes = [
        _node("documents", "Documents", "approved source files", "document", "source", 45, 355, 215, 150),
        _node("tokenizer", "Tokenizer", "split and budget", "token", "process", 305, 355, 215, 150),
        _node("embedding", "Embedding", "encode semantics", "embedding", "process", 565, 355, 215, 150),
        _node("index", "Vector Index", "store searchable vectors", "vector-database", "memory", 825, 355, 215, 150),
        _node("retrieval", "Retrieval", "rank relevant context", "search", "agent", 1085, 355, 215, 150),
        _node("output", "Grounded Output", "answer with citations", "output", "output", 1345, 355, 215, 150),
    ]
    labels = ("ingest", "chunks", "vectors", "top-k", "evidence")
    edges = [
        _edge(nodes[index]["id"], nodes[index + 1]["id"], label, index, route="straight", flow_id="rag-ingestion", flow_repeat="loop")
        for index, label in enumerate(labels)
    ]
    return _base_spec(
        title="Enterprise RAG Ingestion Pipeline",
        subtitle="A strict left-to-right topology for sequential transformation and retrieval",
        style="minimal-light",
        icon_system="diagram-core-v1",
        layout="pipeline",
        nodes=nodes,
        edges=edges,
    )


def _hub_spec() -> Spec:
    nodes = [
        _node("agent", "MCP Orchestrator", "routes capability calls", "agent", "agent", 675, 365, 250, 165),
        _node("gateway", "MCP Gateway", "policy and protocol", "gateway", "risk", 690, 145, 220, 140),
        _node("search", "Search", "discover evidence", "search", "source", 210, 195, 220, 140),
        _node("documents", "Documents", "read trusted files", "document-store", "source", 1170, 195, 220, 140),
        _node("code", "Code Runtime", "execute safely", "source-code", "tool", 170, 585, 220, 140),
        _node("memory", "Agent Memory", "retain context", "memory", "memory", 690, 625, 220, 140),
        _node("monitoring", "Monitoring", "observe every call", "monitoring", "process", 1210, 585, 220, 140),
    ]
    spokes = [
        ("gateway", "policy"),
        ("search", "query"),
        ("documents", "read"),
        ("code", "execute"),
        ("memory", "recall"),
        ("monitoring", "telemetry"),
    ]
    edges = [
        _edge("agent", target, label, index, role=nodes[index + 1]["role"], flow_id="mcp-capability", flow_repeat="event-driven")
        for index, (target, label) in enumerate(spokes)
    ]
    return _base_spec(
        title="MCP Tool Orchestration Hub",
        subtitle="A central agent coordinates policy, knowledge, execution, memory, and observability",
        style="minimal-light",
        icon_system="diagram-core-v1",
        layout="hub-spoke",
        nodes=nodes,
        edges=edges,
    )


def build_specs() -> dict[str, Spec]:
    builders = {
        "hero-loop-engineering": _loop_engineering_spec,
        "hero-governed-rag": _hero_spec,
        "hero-kubernetes-three-layer": _kubernetes_three_layer_spec,
        "template-agent-lifecycle-minimal-light": partial(_template_spec, "minimal-light"),
        "template-agent-lifecycle-deep-tech": partial(_template_spec, "deep-tech"),
        "template-agent-lifecycle-claude-warm": partial(_template_spec, "claude-warm"),
        "layout-enterprise-rag-pipeline": _pipeline_spec,
        "layout-mcp-tool-hub": _hub_spec,
    }
    expected = {case["id"] for case in CASES}
    if set(builders) != expected:
        raise RuntimeError("Round 1 case registry and spec builders must match exactly")
    return {case["id"]: builders[case["id"]]() for case in CASES}


def _relative(path: Path, base: Path) -> str:
    return str(path.resolve().relative_to(base.resolve()))


def _review_page(entries: list[Spec]) -> str:
    groups = (
        ("Hero showcase", "hero", "Lead with Loop Engineering, followed by governed RAG and three-layer infrastructure."),
        ("Template comparison", "template", "Identical semantics and geometry; only the template changes."),
        ("Layout comparison", "layout", "One icon system and one template; the topology matches the content."),
    )
    sections: list[str] = []
    for heading, kind, description in groups:
        cards = []
        for entry in (item for item in entries if item["kind"] == kind):
            cards.append(
                f'''<article data-kind="{escape(kind)}" data-case="{escape(entry["id"])}">
  <div class="card-head"><div><span>{escape(entry["label"])}</span><h3>{escape(entry["title"])}</h3></div>
  <code>{escape(entry["icon_system"])} · {escape(entry["style"])} · {escape(entry["layout"])}</code></div>
  <a class="preview" href="{escape(entry["html_name"])}" aria-label="Open animated {escape(entry["title"])}">
    <img src="{escape(entry["preview_name"])}" alt="Static preview of {escape(entry["title"])}" width="{entry["canvas"]["width"]}" height="{entry["canvas"]["height"]}">
  </a>
  <p class="links"><a href="{escape(entry["html_name"])}">Animated HTML</a><a href="{escape(entry["svg_name"])}">SVG</a><a href="{escape(entry["quality_name"])}">Quality</a><a href="{escape(entry["spec_relative"])}">DiagramScript</a></p>
</article>'''
            )
        sections.append(
            f'<section><header><p>ROUND 1</p><h2>{escape(heading)}</h2><span>{escape(description)}</span></header>'
            f'<div class="grid {escape(kind)}">{"".join(cards)}</div></section>'
        )
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>README Showcase · Round 1</title>
  <style>
    :root {{ color-scheme: light; --ink:#172033; --muted:#667085; --line:#dbe3ef; --paper:#fff; --wash:#f4f7fb; --accent:#635bff; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--wash); color:var(--ink); font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif; }}
    main {{ width:min(1480px,calc(100% - 40px)); margin:0 auto; padding:48px 0 80px; }}
    .intro {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(320px,.55fr); gap:32px; align-items:end; padding:34px; background:#101828; color:#fff; border-radius:28px; box-shadow:0 24px 70px rgba(16,24,40,.16); }}
    .eyebrow, section>header>p {{ margin:0 0 10px; color:#a7a0ff; font-size:12px; font-weight:800; letter-spacing:.16em; }}
    h1 {{ max-width:760px; margin:0; font-size:clamp(38px,6vw,72px); line-height:.98; letter-spacing:-.055em; }}
    .intro p:last-child {{ margin:0; color:#cbd5e1; font-size:17px; line-height:1.65; }}
    section {{ margin-top:58px; }} section>header {{ display:grid; grid-template-columns:1fr auto; gap:8px 24px; align-items:end; margin-bottom:18px; }}
    section>header>p {{ grid-column:1/-1; color:var(--accent); margin:0; }} h2 {{ margin:0; font-size:30px; letter-spacing:-.03em; }} section>header>span {{ color:var(--muted); }}
    .grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:22px; }} .grid.hero {{ grid-template-columns:1fr; }} .grid.template {{ grid-template-columns:repeat(3,minmax(0,1fr)); }}
    article {{ overflow:hidden; background:var(--paper); border:1px solid var(--line); border-radius:20px; box-shadow:0 8px 28px rgba(16,24,40,.06); }}
    .card-head {{ display:flex; justify-content:space-between; gap:18px; align-items:flex-start; padding:20px 22px 16px; }} .card-head span {{ color:var(--accent); font-weight:750; font-size:13px; }}
    h3 {{ margin:5px 0 0; font-size:20px; letter-spacing:-.02em; }} code {{ color:#475467; font-size:12px; white-space:nowrap; }}
    .grid.template .card-head {{ display:block; }} .grid.template .card-head code {{ display:block; margin-top:10px; white-space:normal; }} .grid.template h3 {{ font-size:18px; }}
    .preview {{ display:block; aspect-ratio:16/9; overflow:hidden; background:#e8edf5; border-block:1px solid var(--line); }} .preview img {{ display:block; width:100%; height:100%; object-fit:contain; }}
    .links {{ display:flex; gap:18px; flex-wrap:wrap; margin:0; padding:15px 22px 18px; }} .links a {{ color:#475467; font-size:13px; font-weight:700; text-decoration:none; }} .links a:hover {{ color:var(--accent); }}
    @media (max-width:1180px) {{ .grid.template {{ grid-template-columns:1fr; }} }}
    @media (max-width:900px) {{ .intro,section>header,.grid {{ grid-template-columns:1fr; }} section>header>span {{ margin-top:4px; }} .card-head {{ display:block; }} code {{ display:block; margin-top:10px; white-space:normal; }} }}
  </style>
</head>
<body><main>
  <div class="intro"><div><p class="eyebrow">ANIDIAGRAM · APPROVED CURATED SHOWCASE</p><h1>README Showcase · Round 1</h1></div><p>Eight approved showcase cases. This surface mirrors the GitHub README selection and order.</p></div>
  {''.join(sections)}
</main></body></html>
'''


def render_round(spec_root: Path, outdir: Path) -> Spec:
    spec_root = spec_root.resolve()
    outdir = outdir.resolve()
    spec_root.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)
    base = Path(os.path.commonpath([spec_root, outdir]))
    entries: list[Spec] = []
    combined = {"errors": 0, "warnings": 0, "issues": 0}
    specs = build_specs()

    for case in CASES:
        case_id = case["id"]
        spec = specs[case_id]
        spec_path = spec_root / f"{case_id}.diagram.json"
        preview_path = outdir / f"{case_id}.preview.svg"
        svg_path = outdir / f"{case_id}.svg"
        html_path = outdir / f"{case_id}.html"
        quality_path = outdir / f"{case_id}.quality.json"
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        scene = compile_scene(spec)
        style = load_style(ROOT / "styles" / f'{case["style"]}.json')
        preview_path.write_text(render_svg(scene, style, animation_mode="runtime-stage"), encoding="utf-8")
        write_svg(scene, style, svg_path)
        write_html(scene, style, html_path)
        html_source = html_path.read_text(encoding="utf-8")
        html_path.write_text(
            html_source.replace('<meta name="viewport" content="width=device-width, initial-scale=1">', '<meta name="viewport" content="width=device-width, initial-scale=1">\n  <link rel="icon" href="data:,">', 1),
            encoding="utf-8",
        )
        write_quality(scene, style, quality_path)
        summary = quality_report(scene, style)["summary"]
        for key in combined:
            combined[key] += int(summary[key])
        entries.append(
            {
                **case,
                "title": spec["title"]["text"],
                "spec": _relative(spec_path, base),
                "preview": _relative(preview_path, base),
                "svg": _relative(svg_path, base),
                "html": _relative(html_path, base),
                "quality": _relative(quality_path, base),
                "spec_relative": os.path.relpath(spec_path, outdir),
                "preview_name": preview_path.name,
                "svg_name": svg_path.name,
                "html_name": html_path.name,
                "quality_name": quality_path.name,
                "quality_summary": summary,
                "canvas": dict(spec["canvas"]),
            }
        )

    review_path = outdir / "readme-showcase-round-1.html"
    review_path.write_text(_review_page(entries), encoding="utf-8")
    manifest = {
        "schema": "readme-showcase-v1",
        "round": 1,
        "status": "approved",
        "readme_mutated": True,
        "canvas_policy": "per-case",
        "quality_summary": combined,
        "review_page": _relative(review_path, base),
        "cases": [
            {key: value for key, value in entry.items() if key not in {"spec_relative", "preview_name", "svg_name", "html_name", "quality_name"}}
            for entry in entries
        ],
    }
    (outdir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": combined == {"errors": 0, "warnings": 0, "issues": 0},
        "case_count": len(entries),
        "quality_summary": combined,
        "review_page": str(review_path),
        "manifest": str(outdir / "manifest.json"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec-root", type=Path, default=ROOT / "examples" / "readme-showcase-round-1")
    parser.add_argument("--outdir", type=Path, default=ROOT / "outputs" / "readme-showcase-round-1")
    args = parser.parse_args()
    print(json.dumps(render_round(args.spec_root, args.outdir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
