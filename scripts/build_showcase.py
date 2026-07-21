#!/usr/bin/env python3
"""Build the hero, style, and layout showcases."""

from __future__ import annotations

import argparse
import json
import sys
from html import escape as html_escape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in (SRC, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from anidiagram.exporters import write_html, write_quality, write_svg
from anidiagram.icon_system import resolve_icon_system
from anidiagram.quality import quality_report
from anidiagram.schema import compile_scene
from anidiagram.styles import deep_merge, load_style
from build_style_showcase import _catalog_styles, _chain, _edge, _flow_case, _group, _motion, _node, style_showcase_specs


Spec = Dict[str, Any]

STYLE_BEST_FOR = {
    "minimal-light": ["SaaS", "Operations", "Support flows"],
    "deep-tech": ["AI ops", "Realtime systems", "Agent meshes"],
    "blueprint": ["Architecture", "Protocols", "Cloud boundaries"],
    "flat-icon": ["Roadmaps", "Priority boards", "Product planning"],
    "dark-terminal": ["Incident response", "Debugging", "Runbooks"],
    "notion-clean": ["Product discovery", "Docs", "Workflow notes"],
    "glassmorphism": ["Growth funnels", "Journeys", "Presentation flows"],
    "claude-warm": ["Reasoning", "Research loops", "Planning"],
    "openai-minimal": ["Evaluation", "Benchmarks", "Quality gates"],
    "dark-luxury": ["Executive views", "Signal maps", "Strategy"],
    "aurora-orb": ["Creative tools", "Multimodal agents", "Studio flows"],
    "illustrated-semantic": ["Technical explainers", "Semantic workflows", "Warm presentations"],
    "sketch-board": ["Teaching", "Attention flows", "Explainers"],
}

LAYOUT_CASES = (
    ("pipeline", "RAG Ingestion Pipeline", "blueprint", ["ETL", "Build steps", "AI pipelines"]),
    ("loop", "Agent Reflection Loop", "claude-warm", ["Feedback loops", "Agent learning", "Refinement"]),
    ("hub-spoke", "Agent Tool Hub", "deep-tech", ["Tool routers", "Agent hubs", "Capability maps"]),
    ("layered", "LLM App Architecture Layers", "notion-clean", ["System layers", "Architecture", "Ownership"]),
    ("swimlane", "Human-in-the-loop Approval Flow", "minimal-light", ["Handoffs", "Approvals", "Responsibility"]),
    ("compare", "RAG vs Agentic RAG", "openai-minimal", ["Tradeoffs", "Before after", "Architecture decisions"]),
    ("matrix", "AI Feature Priority Matrix", "flat-icon", ["Prioritization", "PM planning", "Roadmaps"]),
    ("timeline", "AI Product Launch Roadmap", "blueprint", ["Roadmaps", "Milestones", "Release planning"]),
    ("stack", "AI Runtime Stack", "dark-terminal", ["Runtime layers", "Infrastructure", "Dependencies"]),
    ("funnel", "Lead-to-Agent Automation Funnel", "glassmorphism", ["Qualification", "Conversion", "Automation"]),
    ("sequence", "API Tool Calling Sequence", "notion-clean", ["Request chains", "Tool calls", "Protocols"]),
    ("er", "Agent Memory Data Model", "openai-minimal", ["Data models", "Relationships", "Memory schemas"]),
    ("network", "Distributed Agent Runtime Mesh", "dark-luxury", ["Distributed systems", "Runtime meshes", "Routing"]),
    ("agent-memory", "Personalized Agent Memory Flow", "deep-tech", ["Agent memory", "Retrieval", "Grounded output"]),
)

MOTION_CATALOG_PATH = ROOT / "runtime" / "motion-catalog.json"
RUNTIME_MOTION_SPEC_PATH = ROOT / "examples" / "runtime-motion-catalog.diagram.json"
CHARACTER_THEME_CASES = (
    ("illustrated-character", "Default Character"),
    ("deep-tech", "Deep Tech"),
    ("teaching-sketch-character", "Teaching Sketch Character"),
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate AniDiagram hero, style, and layout showcases.")
    parser.add_argument("--spec-root", default="examples/showcase", help="Directory for generated DiagramScript specs.")
    parser.add_argument("--outdir", default="gallery", help="Directory for generated gallery assets.")
    parser.add_argument("--quality", action="store_true", help="Also write quality report JSON files.")
    args = parser.parse_args()

    result = build_showcase(Path(args.spec_root), Path(args.outdir), args.quality)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def build_showcase(spec_root: Path, outdir: Path, quality: bool = True) -> Dict[str, Any]:
    spec_root.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)

    hero_entry = _build_hero(spec_root / "hero", outdir / "hero", quality)
    style_entries = _build_styles(spec_root / "styles", outdir / "styles", quality)
    layout_entries = _build_layouts(spec_root / "layouts", outdir / "layouts", quality)
    runtime_catalog = load_runtime_motion_catalog()
    runtime_entries = [*runtime_catalog.get("character_performances", []), *runtime_catalog["performances"]]
    runtime_bundle = _build_runtime_motion(spec_root / "runtime-motion", outdir / "runtime-motion", runtime_catalog, quality)
    runtime_overview = runtime_bundle["overview"]
    runtime_demos = runtime_bundle["demos"]
    character_theme_comparison = _build_character_theme_comparison(outdir, quality)
    icon_system_releases = _build_icon_system_releases(outdir / "icon-systems", quality)
    manifest = {
        "hero": hero_entry,
        "styles": style_entries,
        "layouts": layout_entries,
        "runtime_motion_page": _rel(outdir / "runtime-motion.html"),
        "runtime_motion_catalog": _rel(MOTION_CATALOG_PATH),
        "runtime_motion_overview": runtime_overview,
        "runtime_motion_demos": runtime_demos,
        "runtime_motion": runtime_entries,
        "character_theme_comparison": character_theme_comparison,
        "icon_system_releases": icon_system_releases,
    }
    (outdir / "showcase_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_runtime_motion_index(outdir, runtime_catalog, runtime_entries, runtime_overview, runtime_demos)
    _write_gallery_index(
        outdir,
        hero_entry,
        style_entries,
        layout_entries,
        runtime_entries,
        runtime_overview,
        icon_system_releases,
    )
    return {
        "ok": True,
        "hero": hero_entry["id"],
        "styles": len(style_entries),
        "layouts": len(layout_entries),
        "runtime_motion": len(runtime_entries),
        "character_themes": len(character_theme_comparison["themes"]),
        "icon_system_releases": len(icon_system_releases),
        "runtime_motion_page": str((outdir / "runtime-motion.html").resolve()),
        "manifest": str((outdir / "showcase_manifest.json").resolve()),
    }


def _build_icon_system_releases(outdir: Path, quality: bool) -> List[Dict[str, Any]]:
    outdir.mkdir(parents=True, exist_ok=True)
    definitions = (
        {
            "id": "diagram-core-v1",
            "title": "Diagram Core v1",
            "icon_system": "diagram-core-v1",
            "version": "1.0.0",
            "motion_contract": "showcase-v1",
            "spec": ROOT / "examples" / "diagram-core-v1-showcase.diagram.json",
            "release": ROOT / "assets" / "diagram-core" / "releases" / "v1.0.0.json",
            "catalog": ROOT / "assets" / "diagram-core" / "catalog.json",
            "style": ROOT / "styles" / "minimal-light.json",
            "best_for": ["Infrastructure diagrams", "Architecture systems", "Technical operations"],
        },
        {
            "id": "illustrated-2.3",
            "title": "Illustrated 2.3",
            "icon_system": "illustrated",
            "version": "2.3.0",
            "motion_contract": "illustrated-performance-v4",
            "spec": ROOT / "examples" / "illustrated-2.3-showcase.diagram.json",
            "release": ROOT / "assets" / "illustrated" / "releases" / "2.3.0.json",
            "catalog": ROOT / "assets" / "illustrated" / "catalog.json",
            "motion_authority": ROOT / "assets" / "illustrated" / "motion-contracts" / "illustrated-performance-v4.json",
            "style": ROOT / "styles" / "deep-tech.json",
            "best_for": ["AI explainers", "Character-led workflows", "Animated presentations"],
        },
    )
    entries = []
    for definition in definitions:
        spec = json.loads(definition["spec"].read_text(encoding="utf-8"))
        release = json.loads(definition["release"].read_text(encoding="utf-8"))
        scene = compile_scene(spec)
        style = load_style(definition["style"])
        basename = definition["id"]
        svg_path = outdir / f"{basename}.svg"
        html_path = outdir / f"{basename}.html"
        quality_path = outdir / f"{basename}.quality.json"
        write_svg(scene, style, svg_path)
        write_html(scene, style, html_path)
        report = quality_report(scene, style)
        # Public release entries always carry their portable quality proof,
        # even when the optional legacy-gallery quality flag is omitted.
        write_quality(scene, style, quality_path)

        catalog = json.loads(definition["catalog"].read_text(encoding="utf-8"))
        expected_icons = {
            item["id"] for item in catalog.get("icons", []) if item.get("status") == "approved"
        }
        spec_pairs = [(node["id"], node.get("icon")) for node in spec.get("nodes", [])]
        motion_pairs = _html_motion_icon_pairs(html_path)
        if definition.get("motion_authority"):
            contract = json.loads(definition["motion_authority"].read_text(encoding="utf-8"))
            contract_icons = [item.get("icon") for item in contract.get("performances", [])]
            if len(contract_icons) != len(set(contract_icons)) or set(contract_icons) != expected_icons:
                raise ValueError(f'{definition["id"]} public motion contract does not exactly cover its catalog')
        _require_exact_icon_pairs(spec_pairs, expected_icons, f'{definition["id"]} spec')
        _require_exact_icon_pairs(motion_pairs, expected_icons, f'{definition["id"]} motion manifest')
        if set(spec_pairs) != set(motion_pairs):
            raise ValueError(f'{definition["id"]} node/icon mappings differ between spec and motion manifest')
        rendered_icon_count = len(spec_pairs)
        automatic_motion_icon_count = len(motion_pairs)
        expected_count = int(release["icon_count"])
        if rendered_icon_count != expected_count or automatic_motion_icon_count != expected_count:
            raise ValueError(
                f'{definition["id"]} public showcase coverage is '
                f"{rendered_icon_count}/{automatic_motion_icon_count}; expected {expected_count}/{expected_count}"
            )
        entries.append(
            {
                "id": definition["id"],
                "title": definition["title"],
                "basename": definition["id"],
                "icon_system": definition["icon_system"],
                "version": definition["version"],
                "status": release["status"],
                "icon_count": expected_count,
                "rendered_icon_count": rendered_icon_count,
                "automatic_motion_icon_count": automatic_motion_icon_count,
                "motion_contract": definition["motion_contract"],
                "spec": _rel(definition["spec"]),
                "release": _rel(definition["release"]),
                "style": spec["style"],
                "svg": _rel(svg_path),
                "html": _rel(html_path),
                "quality": _rel(quality_path),
                "best_for": definition["best_for"],
                "summary": report["summary"],
            }
        )
    _write_icon_system_release_index(outdir, entries)
    return entries


def _html_motion_icon_pairs(path: Path) -> List[tuple[str, str]]:
    source = path.read_text(encoding="utf-8")
    marker = '<script type="application/json" id="anidiagram-motion-manifest">'
    start = source.index(marker) + len(marker)
    manifest = json.loads(source[start : source.index("</script>", start)])
    return [(item.get("node_id"), item.get("icon")) for item in manifest["icons"]]


def _require_exact_icon_pairs(
    pairs: List[tuple[str, str]], expected_icons: set[str], label: str
) -> None:
    node_ids = [node_id for node_id, _ in pairs]
    icons = [icon for _, icon in pairs]
    if any(not node_id for node_id in node_ids) or len(node_ids) != len(set(node_ids)):
        raise ValueError(f"{label} has missing or duplicate node ids")
    if len(icons) != len(set(icons)) or set(icons) != expected_icons:
        raise ValueError(f"{label} does not exactly cover the approved icon catalog")


def _write_icon_system_release_index(outdir: Path, entries: List[Dict[str, Any]]) -> None:
    cards = "\n".join(
        f'<article><a href="{Path(entry["html"]).name}"><img src="{Path(entry["svg"]).name}" '
        f'alt="{html_escape(entry["title"])} public showcase"></a>'
        f'<div class="body"><h2>{html_escape(entry["title"])}</h2>'
        f'<p><code>{html_escape(entry["icon_system"])}</code> · {entry["rendered_icon_count"]}/{entry["icon_count"]} icons · '
        f'<code>{html_escape(entry["motion_contract"])}</code></p>'
        f'<p>{html_escape(", ".join(entry["best_for"]))}</p>'
        f'<p><a href="{Path(entry["html"]).name}">HTML</a> · '
        f'<a href="{Path(entry["svg"]).name}">SVG</a> · '
        f'<a href="{Path(entry["quality"]).name}">Quality</a> · '
        f'<a href="../../{entry["spec"]}">Spec</a> · '
        f'<a href="../../{entry["release"]}">Frozen release</a></p></div></article>'
        for entry in entries
    )
    (outdir / "index.html").write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AniDiagram Public Icon Systems</title>
  <link rel="icon" href="data:,">
  <style>
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: #f8fafc; color: #172033; }}
    main {{ max-width: 1320px; margin: 0 auto; padding: 28px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
    article {{ overflow: hidden; border: 1px solid #dfe3ec; border-radius: 12px; background: #fff; }}
    img {{ display: block; width: 100%; height: auto; background: #fff; }}
    .body {{ padding: 0 16px 14px; }}
    p {{ color: #526075; }}
    a {{ color: #315ac7; }}
    code {{ color: #5b48ae; }}
    @media (max-width: 760px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body><main>
  <p><a href="../index.html">Back to gallery</a> · <a href="../showcase_manifest.json">Manifest</a></p>
  <h1>Public Icon Systems</h1>
  <p>Current frozen releases with complete public showcase coverage. Full browser export matrices are produced separately as release evidence.</p>
  <p><code>PYTHONPATH=src python3 scripts/build_icon_system_release_evidence.py</code><br>
  Verify later with <code>PYTHONPATH=src python3 scripts/build_icon_system_release_evidence.py --verify</code>.</p>
  <section class="grid">{cards}</section>
</main></body>
</html>
""",
        encoding="utf-8",
    )


def load_runtime_motion_catalog(path: Path = MOTION_CATALOG_PATH) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def layout_showcase_specs() -> Dict[str, Spec]:
    specs = {
        "pipeline": _flow_case(
            "blueprint",
            "RAG Ingestion Pipeline",
            "documents become chunks, embeddings, retrieval, and grounded answers",
            [
                _node("docs", "Docs", "source files", (70, 315), "source", "folder"),
                _node("chunk", "Chunk", "split text", (265, 315), "process", "file"),
                _node("embed", "Embed", "vectors", (460, 315), "tool", "api"),
                _node("vector", "Vector DB", "store", (655, 315), "memory", "database"),
                _node("retrieve", "Retrieve", "top-k", (850, 315), "agent", "search"),
                _node("answer", "Answer", "grounded", (1045, 315), "output", "output"),
            ],
            _chain(["docs", "chunk", "embed", "vector", "retrieve", "answer"], "flow", "straight"),
            [_group("rag", "RAG Pipeline", (45, 250, 1180, 185), "process")],
            _motion("teaching", "signal-arrow", "icon-performance", "soft-reveal", "highlight-sweep", intensity=1.0),
        ),
        "loop": _flow_case(
            "claude-warm",
            "Agent Reflection Loop",
            "observe, plan, act, evaluate, and learn with a quiet feedback rhythm",
            [
                _node("observe", "Observe", "state", (515, 130), "source", "search"),
                _node("plan", "Plan", "next step", (800, 305), "agent", "agent"),
                _node("act", "Act", "tool use", (515, 480), "tool", "tool"),
                _node("evaluate", "Evaluate", "quality", (230, 305), "risk", "shield"),
                _node("learn", "Learn", "memory", (515, 305), "memory", "memory"),
            ],
            [
                _edge("observe", "plan", "signal", "source", "curved"),
                _edge("plan", "act", "execute", "agent", "curved", effect="flow-arrow"),
                _edge("act", "evaluate", "result", "tool", "curved"),
                _edge("evaluate", "observe", "revise", "risk", "curved", effect="dynamic-dash"),
                _edge("learn", "plan", "recall", "memory", "straight", effect="flow-dot"),
            ],
            [_group("loop", "Reflection Loop", (190, 85, 820, 535), "neutral")],
            _motion("teaching", "ghost-flow", "icon-performance", "border-scan", "highlight-sweep", intensity=1.0),
        ),
        "hub-spoke": _flow_case(
            "deep-tech",
            "Agent Tool Hub",
            "one agent coordinates search, browser, api, memory, and code tools",
            [
                _node("agent", "Agent", "route tasks", (535, 315), "agent", "agent", (200, 92)),
                _node("search", "Search", "discover", (215, 145), "source", "search"),
                _node("browser", "Browser", "inspect", (855, 145), "tool", "cloud"),
                _node("api", "API", "call", (930, 455), "tool", "api"),
                _node("memory", "Memory", "recall", (515, 520), "memory", "memory"),
                _node("code", "Code Tool", "execute", (140, 455), "process", "tool"),
            ],
            [
                _edge("agent", "search", "query", "source", "straight", effect="signal-arrow"),
                _edge("agent", "browser", "open", "tool", "straight", effect="signal-arrow"),
                _edge("agent", "api", "request", "tool", "straight", effect="signal-arrow"),
                _edge("agent", "memory", "store", "memory", "straight", effect="signal-dot"),
                _edge("agent", "code", "run", "process", "straight", effect="signal-arrow"),
            ],
            [_group("hub", "Tool Hub", (90, 95, 1050, 560), "agent")],
            _motion("teaching", "signal-arrow", "icon-performance", "border-scan", "highlight-sweep", intensity=1.1),
        ),
        "layered": _flow_case(
            "notion-clean",
            "LLM App Architecture Layers",
            "interface, orchestration, tools, data, and observability stay separated",
            [
                _node("ui", "UI", "chat + admin", (150, 180), "actor", "file"),
                _node("agent", "Agent Layer", "plan + route", (500, 300), "agent", "agent", (210, 84)),
                _node("tools", "Tool Layer", "api + code", (845, 300), "tool", "tool"),
                _node("data", "Data Layer", "memory + db", (500, 455), "memory", "database", (210, 84)),
                _node("observe", "Observability", "trace + eval", (845, 455), "source", "search", (210, 84)),
            ],
            [
                _edge("ui", "agent", "intent", "actor", "straight"),
                _edge("agent", "tools", "invoke", "tool", "straight"),
                _edge("agent", "data", "context", "memory", "vh"),
                _edge("tools", "observe", "events", "source", "vh"),
                _edge("data", "observe", "metrics", "source", "straight"),
            ],
            [
                _group("interface", "Interface", (70, 150, 1080, 100), "actor"),
                _group("runtime", "Runtime", (70, 285, 1080, 125), "agent"),
                _group("foundation", "Data + Ops", (70, 440, 1080, 125), "memory"),
            ],
            _motion("subtle", "draw", "fade", "soft-reveal", "fade", intensity=0.55),
        ),
        "swimlane": _flow_case(
            "minimal-light",
            "Human-in-the-loop Approval Flow",
            "user, agent, reviewer, and system each own a clear lane",
            [
                _node("request", "Request", "submit", (110, 175), "actor", "agent"),
                _node("draft", "Draft", "agent proposal", (350, 315), "agent", "file"),
                _node("review", "Review", "human check", (590, 455), "risk", "shield"),
                _node("approve", "Approve", "decision", (830, 455), "output", "output"),
                _node("execute", "Execute", "system action", (830, 315), "tool", "api"),
                _node("notify", "Notify", "result", (1030, 175), "output", "output"),
            ],
            _chain(["request", "draft", "review", "approve", "execute", "notify"], "handoff", "orthogonal"),
            [
                _group("user", "User", (60, 145, 1100, 100), "actor"),
                _group("agent", "Agent", (60, 285, 1100, 100), "agent"),
                _group("reviewer", "Reviewer", (60, 425, 1100, 100), "risk"),
            ],
            _motion("subtle", "draw", "fade", "soft-reveal", "fade", intensity=0.55),
        ),
        "compare": _flow_case(
            "openai-minimal",
            "RAG vs Agentic RAG",
            "compare retrieval-only flow with planning, tools, memory, and evaluation",
            [
                _node("rag-query", "Query", "ask", (190, 245), "actor", "file"),
                _node("rag-retrieve", "Retrieve", "top-k", (190, 390), "memory", "search"),
                _node("rag-answer", "Answer", "compose", (190, 535), "output", "output"),
                _node("agent-plan", "Plan", "decompose", (760, 215), "agent", "agent"),
                _node("agent-tools", "Tools", "act", (760, 360), "tool", "tool"),
                _node("agent-memory", "Memory", "learn", (760, 505), "memory", "memory"),
                _node("decision", "Choose", "fit by task", (500, 610), "output", "shield"),
            ],
            [
                _edge("rag-query", "rag-retrieve", "search", "memory", "vh"),
                _edge("rag-retrieve", "rag-answer", "context", "output", "vh"),
                _edge("agent-plan", "agent-tools", "invoke", "tool", "vh"),
                _edge("agent-tools", "agent-memory", "state", "memory", "vh"),
                _edge("rag-answer", "decision", "simple", "output", "straight"),
                _edge("agent-memory", "decision", "complex", "agent", "straight"),
            ],
            [
                _group("rag", "RAG", (110, 170, 380, 430), "process"),
                _group("agentic", "Agentic RAG", (690, 170, 380, 430), "agent"),
            ],
            _motion("subtle", "draw", "fade", "soft-reveal", "fade", intensity=0.45),
        ),
        "matrix": _flow_case(
            "flat-icon",
            "AI Feature Priority Matrix",
            "impact and effort separate quick wins from big bets",
            [
                _node("quick", "Quick Wins", "high impact", (330, 205), "output", "tool", (190, 86)),
                _node("big", "Big Bets", "strategic", (690, 205), "agent", "agent", (190, 86)),
                _node("fill", "Fill-ins", "small wins", (330, 435), "tool", "file", (190, 86)),
                _node("avoid", "Avoid", "low return", (690, 435), "risk", "shield", (190, 86)),
                _node("signals", "Signals", "demand", (90, 320), "source", "search"),
                _node("roadmap", "Roadmap", "commit", (1010, 320), "memory", "folder"),
            ],
            [
                _edge("signals", "quick", "score", "source", "orthogonal"),
                _edge("signals", "fill", "score", "source", "orthogonal"),
                _edge("quick", "roadmap", "select", "output", "orthogonal", effect="flow-dot"),
                _edge("big", "roadmap", "plan", "agent", "orthogonal"),
            ],
            [_group("matrix", "Impact x Effort", (280, 155, 620, 405), "neutral")],
            _motion("normal", "flow-dot", "icon-pulse", "soft-reveal", "fade", intensity=0.85),
        ),
        "timeline": _flow_case(
            "blueprint",
            "AI Product Launch Roadmap",
            "alpha, beta, public launch, scale, and learning milestones",
            [
                _node("alpha", "Alpha", "internal", (90, 325), "source", "file"),
                _node("beta", "Beta", "trusted users", (305, 325), "process", "agent"),
                _node("public", "Public", "launch", (520, 325), "output", "cloud"),
                _node("scale", "Scale", "automate", (735, 325), "tool", "api"),
                _node("learn", "Learn", "feedback", (950, 325), "memory", "memory"),
            ],
            _chain(["alpha", "beta", "public", "scale", "learn"], "milestone", "straight"),
            [_group("roadmap", "Launch Window", (55, 260, 1120, 190), "process")],
            _motion("teaching", "signal-arrow", "pop", "soft-reveal", "highlight-sweep", intensity=0.9),
        ),
        "stack": _flow_case(
            "dark-terminal",
            "AI Runtime Stack",
            "ui, orchestration, model, tools, memory, and infrastructure layers",
            [
                _node("ui", "UI", "surface", (520, 105), "actor", "file", (220, 72)),
                _node("orch", "Orchestration", "router", (520, 205), "agent", "agent", (220, 72)),
                _node("model", "Model", "inference", (520, 305), "tool", "api", (220, 72)),
                _node("tools", "Tools", "actions", (520, 405), "process", "tool", (220, 72)),
                _node("memory", "Memory", "state", (520, 505), "memory", "database", (220, 72)),
                _node("infra", "Infra", "queue + cache", (520, 605), "source", "cloud", (220, 72)),
            ],
            _chain(["ui", "orch", "model", "tools", "memory", "infra"], "depends", "vh"),
            [_group("stack", "Runtime Stack", (455, 80, 350, 610), "neutral")],
            _motion("normal", "dynamic-dash", "status-blink", "corner-pulse", "highlight-sweep", intensity=1.0),
        ),
        "funnel": _flow_case(
            "glassmorphism",
            "Lead-to-Agent Automation Funnel",
            "capture, qualify, enrich, score, and hand off the right lead",
            [
                _node("capture", "Capture", "forms + chat", (500, 115), "source", "cloud", (260, 76)),
                _node("qualify", "Qualify", "rules", (520, 220), "process", "search", (220, 76)),
                _node("enrich", "Enrich", "context", (540, 325), "memory", "database", (180, 76)),
                _node("score", "Score", "agent fit", (560, 430), "agent", "agent", (145, 76)),
                _node("handoff", "Handoff", "sales task", (570, 535), "output", "output", (125, 72)),
            ],
            _chain(["capture", "qualify", "enrich", "score", "handoff"], "filter", "vh"),
            [_group("funnel", "Automation Funnel", (445, 80, 365, 555), "process")],
            _motion("expressive", "ghost-flow", "pulse", "border-scan", "highlight-sweep", intensity=0.95),
        ),
        "sequence": _flow_case(
            "notion-clean",
            "API Tool Calling Sequence",
            "user, agent, tool, api, memory, and output exchange ordered messages",
            [
                _node("user", "User", "asks", (70, 245), "actor", "agent"),
                _node("agent", "Agent", "plans", (265, 245), "agent", "agent"),
                _node("tool", "Tool", "runs", (460, 245), "tool", "tool"),
                _node("api", "API", "responds", (655, 245), "process", "api"),
                _node("memory", "Memory", "commit", (850, 245), "memory", "database"),
                _node("output", "Output", "answer", (1045, 245), "output", "output"),
            ],
            [
                _edge("user", "agent", "prompt", "actor", "straight"),
                _edge("agent", "tool", "call", "tool", "straight", effect="signal-arrow"),
                _edge("tool", "api", "request", "process", "straight", effect="signal-arrow"),
                _edge("api", "memory", "result", "memory", "straight", effect="signal-dot"),
                _edge("memory", "output", "ground", "output", "straight"),
            ],
            [_group("sequence", "Call Sequence", (45, 180, 1185, 190), "neutral")],
            _motion("teaching", "signal-arrow", "icon-performance", "soft-reveal", "highlight-sweep", intensity=1.0),
        ),
        "er": _flow_case(
            "openai-minimal",
            "Agent Memory Data Model",
            "users, sessions, messages, memories, tool calls, and artifacts",
            [
                _node("user", "User", "id, plan", (105, 225), "actor", "agent"),
                _node("session", "Session", "started_at", (350, 225), "process", "folder"),
                _node("message", "Message", "role, text", (595, 225), "source", "file"),
                _node("memory", "Memory", "scope, value", (840, 225), "memory", "database"),
                _node("toolcall", "ToolCall", "name, status", (470, 455), "tool", "api"),
                _node("artifact", "Artifact", "uri, type", (715, 455), "output", "output"),
            ],
            [
                _edge("user", "session", "has", "actor", "straight"),
                _edge("session", "message", "contains", "process", "straight"),
                _edge("message", "memory", "summarizes", "memory", "straight"),
                _edge("message", "toolcall", "invokes", "tool", "vh"),
                _edge("toolcall", "artifact", "creates", "output", "straight"),
            ],
            [_group("model", "Memory Schema", (70, 165, 1080, 410), "neutral")],
            _motion("subtle", "draw", "fade", "soft-reveal", "fade", intensity=0.45),
        ),
        "network": _flow_case(
            "dark-luxury",
            "Distributed Agent Runtime Mesh",
            "workers, queues, caches, routers, and models coordinate across a mesh",
            [
                _node("router", "Router", "dispatch", (520, 300), "agent", "agent", (200, 92)),
                _node("worker-a", "Worker A", "tools", (190, 170), "tool", "tool"),
                _node("worker-b", "Worker B", "browser", (850, 170), "tool", "cloud"),
                _node("queue", "Queue", "jobs", (190, 485), "source", "api"),
                _node("cache", "Cache", "state", (520, 520), "memory", "database"),
                _node("model", "Model", "route", (850, 485), "process", "api"),
            ],
            [
                _edge("router", "worker-a", "assign", "tool", "straight", effect="signal-arrow"),
                _edge("router", "worker-b", "assign", "tool", "straight", effect="signal-arrow"),
                _edge("queue", "router", "jobs", "source", "straight", effect="signal-dot"),
                _edge("router", "cache", "state", "memory", "straight", effect="flow-dot"),
                _edge("router", "model", "infer", "process", "straight", effect="signal-arrow"),
                _edge("worker-a", "cache", "write", "memory", "straight"),
                _edge("worker-b", "model", "call", "process", "straight"),
            ],
            [_group("mesh", "Runtime Mesh", (125, 115, 980, 510), "agent")],
            _motion("expressive", "signal-arrow", "pulse", "border-scan", "highlight-sweep", intensity=1.05),
        ),
        "agent-memory": _flow_case(
            "deep-tech",
            "Personalized Agent Memory Flow",
            "the agent retrieves context, commits memory, and produces a grounded answer",
            [
                _node("user", "User", "preference", (80, 315), "actor", "token"),
                _node("agent", "Agent", "think + act", (295, 315), "agent", "agent", (190, 92)),
                _node("search", "Search", "retrieve", (525, 205), "source", "search"),
                _node("memory", "Memory", "commit", (760, 315), "memory", "database", (190, 92)),
                _node("tool", "Tool", "do work", (525, 425), "tool", "tool"),
                _node("output", "Output", "answer", (1005, 315), "output", "output"),
            ],
            [
                _edge("user", "agent", "intent", "actor", "straight"),
                _edge("agent", "search", "context", "source", "orthogonal", effect="signal-arrow"),
                _edge("agent", "tool", "action", "tool", "orthogonal", effect="signal-arrow"),
                _edge("search", "memory", "facts", "memory", "orthogonal", effect="signal-dot"),
                _edge("tool", "memory", "result", "memory", "orthogonal", effect="signal-dot"),
                _edge("memory", "output", "ground", "output", "straight"),
            ],
            [
                _group("runtime", "Agent Runtime", (55, 155, 630, 410), "agent"),
                _group("state", "Memory + Output", (710, 205, 430, 215), "memory"),
            ],
            _motion("teaching", "signal-arrow", "icon-performance", "soft-reveal", "highlight-sweep", intensity=1.1),
        ),
    }
    focused_policy = {
        "profile": "focused",
        "motion_area": "small",
        "max_active_flow_edges": 4,
        "max_particle_edges": 4,
        "particle_count_per_edge": 1,
        "flow_trail_count": 0,
        "max_active_pulse_nodes": 3,
        "pulse_mode": "rotate",
        "max_scanning_groups": 0,
    }
    for preset in ("pipeline", "sequence", "agent-memory"):
        specs[preset]["motion_policy"] = dict(focused_policy)
    intentionally_static_edges = {
        "pipeline": {("retrieve", "answer")},
        "sequence": {("memory", "output")},
        "agent-memory": {("agent", "tool"), ("tool", "memory")},
    }
    for preset, edge_pairs in intentionally_static_edges.items():
        for edge in specs[preset]["edges"]:
            if (edge["from"], edge["to"]) in edge_pairs:
                edge["animated"] = False
    return specs


def _build_hero(spec_dir: Path, outdir: Path, quality: bool) -> Dict[str, Any]:
    spec_dir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)
    spec = json.loads((ROOT / "examples" / "high-fidelity-runtime.diagram.json").read_text(encoding="utf-8"))
    spec_path = spec_dir / "agent-runtime-flow.diagram.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    scene = compile_scene(spec)
    style = load_style(ROOT / "styles" / "deep-tech.json")
    svg_path = outdir / "agent-runtime-flow.svg"
    html_path = outdir / "agent-runtime-flow.html"
    quality_path = outdir / "agent-runtime-flow.quality.json"
    preview_dir = outdir.parent / "previews"
    preview_paths = {
        "preview_webp": preview_dir / "agent-runtime-flow.webp",
        "preview_gif": preview_dir / "agent-runtime-flow.gif",
        "preview_apng": preview_dir / "agent-runtime-flow.apng",
        "preview_mp4": preview_dir / "agent-runtime-flow.mp4",
    }
    write_svg(scene, style, svg_path)
    write_html(scene, style, html_path)
    summary = quality_report(scene)["summary"]
    if quality:
        write_quality(scene, style, quality_path)
    _write_section_index(outdir, "Hero Demo", [("agent-runtime-flow", spec["title"]["text"], spec["title"]["subtitle"], svg_path.name, html_path.name)])
    return {
        "id": "agent-runtime-flow",
        "title": spec["title"]["text"],
        "basename": "agent-runtime-flow",
        "spec": _rel(spec_path),
        "style": "deep-tech",
        "icon_system": resolve_icon_system(style),
        "svg": _rel(svg_path),
        "html": _rel(html_path),
        "quality": _rel(quality_path),
        "best_for": ["High-fidelity runtime", "Agent flow", "Semantic icon performance"],
        "summary": summary,
        **{key: _rel(path) for key, path in preview_paths.items() if path.exists()},
    }


def _build_styles(spec_dir: Path, outdir: Path, quality: bool) -> List[Dict[str, Any]]:
    catalog_styles = _catalog_styles()
    specs = style_showcase_specs()
    missing = [style for style in catalog_styles if style not in specs]
    extra = [style for style in specs if style not in catalog_styles]
    if missing or extra:
        raise SystemExit(json.dumps({"missing": missing, "extra": extra}, indent=2))
    spec_dir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)
    entries = []
    cards = []
    for style_name in catalog_styles:
        spec = specs[style_name]
        slug = _slug(spec["title"]["text"])
        spec_path = spec_dir / f"{style_name}-{slug}.diagram.json"
        svg_path = outdir / f"{style_name}.svg"
        html_path = outdir / f"{style_name}.html"
        quality_path = outdir / f"{style_name}.quality.json"
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        scene = compile_scene(spec)
        style = load_style(ROOT / "styles" / f"{style_name}.json")
        write_svg(scene, style, svg_path)
        write_html(scene, style, html_path)
        summary = quality_report(scene)["summary"]
        if quality:
            write_quality(scene, style, quality_path)
        entry = {
            "style": style_name,
            "icon_system": resolve_icon_system(style),
            "title": spec["title"]["text"],
            "basename": style_name,
            "spec": _rel(spec_path),
            "svg": _rel(svg_path),
            "html": _rel(html_path),
            "quality": _rel(quality_path),
            "best_for": STYLE_BEST_FOR[style_name],
            "summary": summary,
        }
        entries.append(entry)
        cards.append((style_name, entry["title"], spec["title"]["subtitle"], svg_path.name, html_path.name))
    _write_section_index(outdir, "Style Showcase", cards)
    return entries


def _build_layouts(spec_dir: Path, outdir: Path, quality: bool) -> List[Dict[str, Any]]:
    specs = layout_showcase_specs()
    expected = [case[0] for case in LAYOUT_CASES]
    missing = [preset for preset in expected if preset not in specs]
    extra = [preset for preset in specs if preset not in expected]
    if missing or extra:
        raise SystemExit(json.dumps({"missing": missing, "extra": extra}, indent=2))
    spec_dir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)
    entries = []
    cards = []
    for preset, title, style_name, best_for in LAYOUT_CASES:
        spec = specs[preset]
        spec["preset"] = preset
        slug = _slug(title)
        spec_path = spec_dir / f"{preset}-{slug}.diagram.json"
        svg_path = outdir / f"{preset}.svg"
        html_path = outdir / f"{preset}.html"
        quality_path = outdir / f"{preset}.quality.json"
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        scene = compile_scene(spec)
        style = load_style(ROOT / "styles" / f"{style_name}.json")
        write_svg(scene, style, svg_path)
        write_html(scene, style, html_path)
        summary = quality_report(scene)["summary"]
        if quality:
            write_quality(scene, style, quality_path)
        entry = {
            "preset": preset,
            "title": title,
            "style": style_name,
            "icon_system": resolve_icon_system(style),
            "basename": preset,
            "spec": _rel(spec_path),
            "svg": _rel(svg_path),
            "html": _rel(html_path),
            "quality": _rel(quality_path),
            "best_for": best_for,
            "summary": summary,
        }
        entries.append(entry)
        cards.append((preset, title, spec["title"]["subtitle"], svg_path.name, html_path.name))
    _write_section_index(outdir, "Layout Showcase", cards)
    return entries


def _build_runtime_motion(
    spec_dir: Path,
    outdir: Path,
    catalog: Dict[str, Any],
    quality: bool,
) -> Dict[str, Any]:
    spec_dir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)
    spec = json.loads(RUNTIME_MOTION_SPEC_PATH.read_text(encoding="utf-8"))
    scene = compile_scene(spec)
    style_name = "deep-tech"
    style = deep_merge(load_style(ROOT / "styles" / f"{style_name}.json"), {"icon_system": "semantic-line-v1"})
    svg_path = outdir / "overview.svg"
    html_path = outdir / "overview.html"
    quality_path = outdir / "overview.quality.json"
    write_svg(scene, style, svg_path)
    write_html(scene, style, html_path)
    summary = quality_report(scene)["summary"]
    if quality:
        write_quality(scene, style, quality_path)
    overview = {
        "id": "runtime-motion-catalog",
        "title": "Legacy v2 Runtime Motion Overview",
        "style": style_name,
        "icon_system": resolve_icon_system(style),
        "basename": "runtime-motion-catalog",
        "spec": _rel(RUNTIME_MOTION_SPEC_PATH),
        "svg": _rel(svg_path),
        "html": _rel(html_path),
        "quality": _rel(quality_path),
        "best_for": ["Motion QA", "Runtime review", "Baseline management"],
        "summary": summary,
    }
    demos = []
    items_dir = outdir / "items"
    items_dir.mkdir(parents=True, exist_ok=True)
    for effect in catalog.get("stage_effects", []):
        demo_spec = _runtime_stage_demo_spec(effect)
        demos.append(_write_runtime_motion_demo(spec_dir, items_dir, demo_spec, effect, "stage-effect", quality))
    for performance in catalog.get("character_performances", []):
        demo_spec = _runtime_performance_demo_spec(performance)
        demos.append(_write_runtime_motion_demo(spec_dir, items_dir, demo_spec, performance, "icon-performance-character", quality))
    for performance in catalog.get("performances", []):
        demo_spec = _runtime_performance_demo_spec(performance)
        demos.append(_write_runtime_motion_demo(spec_dir, items_dir, demo_spec, performance, "icon-performance", quality))
    return {"overview": overview, "demos": demos}


def _write_runtime_motion_demo(
    spec_dir: Path,
    outdir: Path,
    spec: Spec,
    catalog_entry: Dict[str, Any],
    kind: str,
    quality: bool,
) -> Dict[str, Any]:
    item_id = catalog_entry["id"]
    spec_path = spec_dir / f"{item_id}.diagram.json"
    svg_path = outdir / f"{item_id}.svg"
    html_path = outdir / f"{item_id}.html"
    quality_path = outdir / f"{item_id}.quality.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    scene = compile_scene(spec)
    style = deep_merge(
        load_style(ROOT / "styles" / "deep-tech.json"),
        {"icon_system": catalog_entry.get("icon_system", "illustrated-character-v1")},
    )
    write_svg(scene, style, svg_path)
    write_html(scene, style, html_path)
    summary = quality_report(scene)["summary"]
    if quality:
        write_quality(scene, style, quality_path)
    return {
        "id": item_id,
        "kind": kind,
        "title": catalog_entry["title"],
        "icon": catalog_entry.get("icon"),
        "icon_system": catalog_entry.get("icon_system"),
        "spec": _rel(spec_path),
        "svg": _rel(svg_path),
        "html": _rel(html_path),
        "quality": _rel(quality_path),
        "phases": catalog_entry.get("phases", []),
        "parts": catalog_entry.get("parts", []),
        "selectors": catalog_entry.get("selectors", []),
        "status": catalog_entry.get("status", ""),
        "summary": summary,
    }


def _build_character_theme_comparison(outdir: Path, quality: bool) -> Dict[str, Any]:
    source_path = ROOT / "examples" / "illustrated-character-v1-flow.diagram.json"
    spec = json.loads(source_path.read_text(encoding="utf-8"))
    comparison_dir = outdir / "character-themes"
    comparison_dir.mkdir(parents=True, exist_ok=True)
    entries: List[Dict[str, Any]] = []
    for style_name, label in CHARACTER_THEME_CASES:
        scene = compile_scene(spec)
        style = load_style(ROOT / "styles" / f"{style_name}.json")
        svg_path = comparison_dir / f"{style_name}.svg"
        html_path = comparison_dir / f"{style_name}.html"
        quality_path = comparison_dir / f"{style_name}.quality.json"
        write_svg(scene, style, svg_path)
        write_html(scene, style, html_path)
        if quality:
            write_quality(scene, style, quality_path)
        webp_path = ROOT / "outputs" / "illustrated-character-theme-comparison" / f"{style_name}.webp"
        entries.append(
            {
                "style": style_name,
                "label": label,
                "spec": _rel(source_path),
                "svg": _rel(svg_path),
                "html": _rel(html_path),
                "webp": _rel(webp_path),
                "quality": _rel(quality_path),
                "icon_system": "illustrated-character-v1",
                "motion_mode": "ambient / expressive",
            }
        )
    page_path = outdir / "character-themes.html"
    cards = "\n".join(
        f'<article><h2>{html_escape(entry["label"])}</h2>'
        f'<p><code>{html_escape(entry["style"])}</code> · <code>{entry["icon_system"]}</code> · <code>{entry["motion_mode"]}</code></p>'
        f'<a href="{_path_for_html(entry["html"])}"><img src="{_path_from_gallery(entry["webp"])}" alt="{html_escape(entry["label"])} animated preview"></a>'
        f'<p><a href="{_path_for_html(entry["html"])}">HTML</a> · <a href="{_path_for_html(entry["svg"])}">SVG</a> · '
        f'<a href="{_path_from_gallery(entry["webp"])}">WebP</a> · <a href="{_path_for_html(entry["quality"])}">Quality</a></p></article>'
        for entry in entries
    )
    page_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Illustrated Character Theme Comparison</title>
  <style>
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: #f6f7fb; color: #182033; }}
    main {{ max-width: 1320px; margin: 0 auto; padding: 28px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 18px; }}
    article {{ background: #fff; border: 1px solid #dfe3ec; border-radius: 12px; padding: 16px; }}
    img {{ display: block; width: 100%; border-radius: 8px; background: #0b1020; }}
    code {{ color: #5b48ae; }}
    a {{ color: #315ac7; }}
  </style>
</head>
<body><main>
  <p><a href="index.html">Back to gallery</a></p>
  <h1>Illustrated Character Theme Comparison</h1>
  <p>The same eight-icon flow rendered with the three supported Character v1 themes.</p>
  <section class="grid">{cards}</section>
</main></body>
</html>
""",
        encoding="utf-8",
    )
    return {"page": _rel(page_path), "themes": entries}


def _runtime_performance_demo_spec(entry: Dict[str, Any]) -> Spec:
    icon = entry.get("icon") or "agent"
    role = _role_for_icon(icon)
    return {
        "version": "0.3",
        "preset": entry["id"],
        "canvas": {"width": 560, "height": 360},
        "style": "deep-tech",
        "title": {
            "text": entry["title"],
            "subtitle": entry["id"],
        },
        "motion": _runtime_demo_motion(edge="static", node="icon-performance", title="none", group="static"),
        "motion_policy": _runtime_demo_policy(),
        "nodes": [
            {
                "id": icon,
                "label": entry["title"],
                "caption": " / ".join(entry.get("best_for", [])),
                "position": [170, 190],
                "size": [220, 96],
                "role": role,
                "icon": icon,
                "effect": {"preset": "icon-performance", "icon_motion": entry["id"]},
            }
        ],
        "edges": [],
    }


def _runtime_stage_demo_spec(effect: Dict[str, Any]) -> Spec:
    if effect["id"] == "runtime-title-sweep":
        return {
            "version": "0.3",
            "preset": effect["id"],
            "canvas": {"width": 560, "height": 360},
            "style": "deep-tech",
            "title": {
                "text": effect["title"],
                "subtitle": effect["meaning"],
            },
            "motion": _runtime_demo_motion(edge="static", node="none", title="highlight-sweep", group="static"),
            "motion_policy": _runtime_demo_policy(),
            "nodes": [
                {
                    "id": "marker",
                    "label": "Title Layer",
                    "caption": "highlight sweep",
                    "position": [170, 210],
                    "size": [220, 88],
                    "role": "process",
                    "effect": {"preset": "fade"},
                }
            ],
            "edges": [],
        }
    return {
        "version": "0.3",
        "preset": effect["id"],
        "canvas": {"width": 560, "height": 360},
        "style": "deep-tech",
        "title": {
            "text": effect["title"],
            "subtitle": effect["meaning"],
        },
        "motion": _runtime_demo_motion(edge="signal-arrow", node="none", title="none", group="static"),
        "motion_policy": _runtime_demo_policy(),
        "nodes": [
            {
                "id": "source",
                "label": "Source",
                "caption": "packet enters",
                "position": [70, 205],
                "size": [160, 84],
                "role": "source",
                "effect": {"preset": "fade"},
            },
            {
                "id": "target",
                "label": "Target",
                "caption": "packet exits",
                "position": [330, 205],
                "size": [160, 84],
                "role": "memory",
                "effect": {"preset": "fade"},
            },
        ],
        "edges": [
            {"from": "source", "to": "target", "label": "data flow", "role": "source", "effect": {"preset": "signal-arrow"}}
        ],
    }


def _runtime_demo_motion(edge: str, node: str, title: str, group: str) -> Dict[str, Any]:
    return {
        "profile": "expressive",
        "sequence": "simultaneous",
        "ease": "spring",
        "stagger": 0.08,
        "duration_scale": 0.95,
        "intensity": 1.1,
        "edge": {"preset": edge, "particle_count": 1, "trail_count": 0},
        "node": {"preset": node},
        "group": {"preset": group},
        "title": {"preset": title},
        "reduced_motion": "subtle",
    }


def _runtime_demo_policy() -> Dict[str, Any]:
    return {
        "profile": "expressive",
        "motion_area": "small",
        "max_active_flow_edges": 4,
        "max_particle_edges": 4,
        "particle_count_per_edge": 1,
        "flow_trail_count": 0,
        "max_active_pulse_nodes": 4,
        "max_scanning_groups": 0,
    }


def _role_for_icon(icon: str) -> str:
    return {
        "agent": "agent",
        "api": "tool",
        "search": "source",
        "database": "memory",
        "memory": "memory",
        "tool": "tool",
        "token": "source",
        "output": "output",
        "file": "source",
        "folder": "source",
        "cloud": "tool",
        "shield": "risk",
    }.get(icon, "neutral")


def _write_runtime_motion_index(
    outdir: Path,
    catalog: Dict[str, Any],
    runtime_motion: List[Dict[str, Any]],
    overview: Dict[str, Any],
    demos: List[Dict[str, Any]],
) -> None:
    stage_visual_cards = "\n".join(_motion_visual_card(demo) for demo in demos if demo["kind"] == "stage-effect")
    character_visual_cards = "\n".join(_motion_visual_card(demo) for demo in demos if demo["kind"] == "icon-performance-character")
    legacy_visual_cards = "\n".join(_motion_visual_card(demo) for demo in demos if demo["kind"] == "icon-performance")
    stage_cards = "\n".join(
        _motion_detail_card(
            effect["id"],
            effect["title"],
            " -> ".join(effect.get("phases", [])) or effect.get("meaning", ""),
            effect.get("selectors", []),
            effect.get("status", ""),
        )
        for effect in catalog.get("stage_effects", [])
    )
    character_cards = "\n".join(
        _motion_detail_card(
            entry["id"],
            entry["title"],
            " -> ".join(entry.get("phases", [])),
            entry.get("parts", []),
            entry.get("status", ""),
            icon=entry.get("icon", ""),
        )
        for entry in runtime_motion
        if entry.get("icon_system") == "illustrated-character-v1"
    )
    legacy_cards = "\n".join(
        _motion_detail_card(
            entry["id"],
            entry["title"],
            " -> ".join(entry.get("phases", [])),
            entry.get("parts", []),
            entry.get("status", ""),
            icon=entry.get("icon", ""),
        )
        for entry in runtime_motion
        if entry.get("icon_system") == "semantic-line-v1"
    )
    default_runtime = catalog.get("default_runtime", {})
    change_control = catalog.get("change_control", {})
    allowed_changes = ", ".join(change_control.get("allowed_without_confirmation", []))
    (outdir / "runtime-motion.html").write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AniDiagram Runtime Motion Catalog</title>
  <link rel="icon" href="data:,">
  <style>
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: #0b1020; color: #f8fafc; }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 28px; }}
    h1 {{ font-size: 34px; margin: 0 0 8px; letter-spacing: 0; }}
    h2 {{ font-size: 22px; margin: 30px 0 12px; }}
    h3 {{ font-size: 15px; margin: 0 0 8px; }}
    p {{ color: #cbd5e1; line-height: 1.55; }}
    a {{ color: #67e8f9; }}
    code {{ color: #fef3c7; }}
    .topbar {{ display: flex; flex-wrap: wrap; gap: 12px; margin: 18px 0 22px; }}
    .topbar a {{ border: 1px solid #334155; border-radius: 7px; padding: 8px 10px; color: #f8fafc; text-decoration: none; background: #111827; }}
    .notice {{ border: 1px solid #f59e0b; background: rgba(245, 158, 11, 0.10); border-radius: 8px; padding: 14px 16px; }}
    .meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 16px 0; }}
    .meta div, article {{ border: 1px solid #243244; border-radius: 8px; background: #111827; padding: 14px; }}
    iframe {{ width: 100%; height: 620px; border: 1px solid #334155; border-radius: 10px; background: #020617; }}
    .visual-card iframe {{ height: 360px; margin: 10px 0 12px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }}
    .visual-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 16px; }}
    .phase-list {{ margin: 8px 0 0 20px; padding: 0; color: #cbd5e1; }}
    .phase-list li {{ margin: 4px 0; }}
    .small {{ font-size: 13px; color: #94a3b8; }}
  </style>
</head>
<body>
  <main>
    <h1>Runtime Motion Catalog</h1>
    <p>Frozen baseline for the current high-fidelity HTML runtime effects. This page is the review surface for semantic icon performances, edge packet flow, and title sweep.</p>
    <nav class="topbar">
      <a href="index.html">Gallery Home</a>
      <a href="{_path_for_html(overview['html'])}">Open Overview Runtime</a>
      <a href="{_path_for_html(overview['svg'])}">Open SVG Fallback</a>
      <a href="../runtime/motion-catalog.json">View Catalog JSON</a>
      <a href="../docs/html-runtime.md">Runtime Docs</a>
    </nav>
    <section class="notice">
      <h2>Change Control</h2>
      <p>{html_escape(change_control.get("rule", ""))}</p>
      <p class="small">Allowed without confirmation: {html_escape(allowed_changes)}.</p>
    </section>
    <section class="meta">
      <div><h3>Status</h3><p><code>{html_escape(catalog.get("status", ""))}</code></p></div>
      <div><h3>Baseline Date</h3><p><code>{html_escape(catalog.get("baseline_date", ""))}</code></p></div>
      <div><h3>Runtime</h3><p><code>{html_escape(default_runtime.get("runtime", ""))}</code> / <code>{html_escape(default_runtime.get("mode", ""))}</code></p></div>
      <div><h3>Profile</h3><p><code>{html_escape(default_runtime.get("profile", ""))}</code> / <code>{html_escape(default_runtime.get("sequence", ""))}</code></p></div>
    </section>
    <section>
      <h2>Legacy v2 Live Overview</h2>
      <p>The overview preserves the explicit <code>semantic-line-v1</code> compatibility baseline; Character v1 is reviewed in the individual cards below.</p>
      <iframe src="{_path_for_html(overview['html'])}" title="Legacy v2 Runtime Motion Catalog Overview"></iframe>
    </section>
    <section>
      <h2>Individual Stage Effect Visuals</h2>
      <p>Each stage effect is isolated in its own runtime page so it can be reviewed without changing the baseline implementation.</p>
      <div class="visual-grid">
{stage_visual_cards}
      </div>
    </section>
    <section>
      <h2>Character v1 Performance Visuals</h2>
      <p>The default Character v1 performances use the frozen repeat gap, canonical rest, and idle-breath contract.</p>
      <div class="visual-grid">
{character_visual_cards}
      </div>
    </section>
    <section>
      <h2>Legacy v2 Performance Visuals</h2>
      <p>Compatibility demos explicitly request <code>semantic-line-v1</code>; they do not replace the Character v1 default.</p>
      <div class="visual-grid">
{legacy_visual_cards}
      </div>
    </section>
    <section>
      <h2>Stage Effects</h2>
      <div class="grid">
{stage_cards}
      </div>
    </section>
    <section>
      <h2>Character v1 Performances</h2>
      <div class="grid">
{character_cards}
      </div>
    </section>
    <section>
      <h2>Legacy v2 Performances</h2>
      <div class="grid">
{legacy_cards}
      </div>
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


def _motion_visual_card(demo: Dict[str, Any]) -> str:
    phases = "".join(f"<li>{html_escape(str(phase))}</li>" for phase in demo.get("phases", []))
    detail_items = demo.get("parts") or demo.get("selectors") or []
    detail_text = ", ".join(f"<code>{html_escape(str(item))}</code>" for item in detail_items)
    icon = demo.get("icon")
    icon_line = f'<p class="small">Icon: <code>{html_escape(str(icon))}</code></p>' if icon else ""
    return (
        f'<article class="visual-card" id="{html_escape(demo["id"])}">'
        f"<h3>{html_escape(demo['id'])}</h3>"
        f"<p>{html_escape(demo['title'])}</p>{icon_line}"
        f'<iframe src="{_path_for_html(demo["html"])}" title="{html_escape(demo["title"])}"></iframe>'
        f"<p class=\"small\">Semantic phases</p><ol class=\"phase-list\">{phases}</ol>"
        f'<p class="small">Parts/selectors: {detail_text}</p>'
        f'<p class="small"><a href="{_path_from_gallery(demo["html"])}">Open demo</a> · <a href="{_path_from_gallery(demo["spec"])}">Spec</a> · <a href="{_path_from_gallery(demo["svg"])}">SVG</a></p>'
        "</article>"
    )


def _motion_detail_card(
    item_id: str,
    title: str,
    description: str,
    items: Iterable[str],
    status: str,
    *,
    icon: str = "",
) -> str:
    item_text = ", ".join(f"<code>{html_escape(str(item))}</code>" for item in items)
    icon_line = f'<p class="small">Icon: <code>{html_escape(icon)}</code></p>' if icon else ""
    return (
        f"<article><h3>{html_escape(item_id)}</h3>"
        f"<p>{html_escape(title)}</p>{icon_line}"
        f'<p class="small">{html_escape(description)}</p>'
        f'<p class="small">Parts/selectors: {item_text}</p>'
        f'<p class="small">Status: <code>{html_escape(status)}</code></p></article>'
    )


def _write_gallery_index(
    outdir: Path,
    hero: Dict[str, Any],
    styles: List[Dict[str, Any]],
    layouts: List[Dict[str, Any]],
    runtime_motion: List[Dict[str, Any]],
    runtime_overview: Dict[str, Any],
    icon_system_releases: List[Dict[str, Any]],
) -> None:
    style_cards = "\n".join(_entry_card_html(entry["style"], entry) for entry in styles)
    layout_cards = "\n".join(_entry_card_html(entry["preset"], entry) for entry in layouts)
    hero_cli = _cli_command(hero)
    hero_preview = hero.get("preview_webp") or hero["svg"]
    hero_link = hero.get("preview_mp4") or hero["html"]
    motion_cards = "\n".join(_motion_card_html(entry) for entry in runtime_motion)
    icon_system_cards = "\n".join(
        _entry_card_html(entry["title"], entry) for entry in icon_system_releases
    )
    (outdir / "index.html").write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AniDiagram Showcase</title>
  <link rel="icon" href="data:,">
  <style>
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: #f8fafc; color: #111827; }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 28px; }}
    h1 {{ font-size: 36px; margin: 0 0 8px; letter-spacing: 0; }}
    h2 {{ font-size: 24px; margin: 34px 0 12px; }}
    h3 {{ font-size: 16px; margin: 12px 14px 4px; }}
    p {{ color: #4b5563; }}
    .hero img {{ width: 100%; display: block; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }}
    .style-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    article {{ border: 1px solid #e5e7eb; border-radius: 8px; background: #ffffff; overflow: hidden; }}
    article img {{ display: block; width: 100%; height: auto; }}
    article p {{ margin: 0 14px 14px; }}
    .actions {{ display: flex; gap: 8px; margin: 0 14px 14px; }}
    .actions a, .actions button {{ border: 1px solid #d1d5db; border-radius: 6px; background: #fff; color: #111827; padding: 7px 9px; font: inherit; text-decoration: none; cursor: pointer; }}
    .links a {{ margin-right: 12px; }}
    @media (max-width: 760px) {{ .style-grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <h1>AniDiagram Showcase</h1>
    <p>Style Showcase makes diagrams look right. Layout Showcase makes diagram purpose obvious. The hero preview is browser-captured runtime media when available; card images stay lightweight SVG previews.</p>
    <section>
      <h2>Public Icon Systems</h2>
      <p>The current frozen Diagram Core v1 and Illustrated 2.3 public releases, each with complete static and automatic-motion coverage.</p>
      <p class="links"><a href="icon-systems/index.html">Open public icon systems</a></p>
      <div class="grid">
{icon_system_cards}
      </div>
    </section>
    <section class="hero">
      <h2>Hero Demo</h2>
      <a href="{_path_for_html(hero_link)}"><img src="{_path_for_html(hero_preview)}" alt="{hero['title']}"></a>
      <p>{hero['title']} - {', '.join(hero['best_for'])}</p>
      <p class="actions"><a href="{_path_for_html(hero['html'])}">Open HTML</a><button type="button" data-copy="{html_escape(hero_cli, quote=True)}">Copy CLI</button></p>
      <p class="links"><a href="hero/index.html">Open hero gallery</a><a href="showcase_manifest.json">View manifest</a></p>
    </section>
    <section>
      <h2>Style Showcase</h2>
      <p>One signature case for every bundled visual style.</p>
      <div class="grid style-grid">
{style_cards}
      </div>
    </section>
    <section>
      <h2>Layout Showcase</h2>
      <p>One standard teaching case for every clean-room layout preset.</p>
      <div class="grid">
{layout_cards}
      </div>
    </section>
    <section>
      <h2>Runtime Motion Showcase</h2>
      <p>The frozen high-fidelity runtime baseline. Open the catalog to review current semantics, part IDs, stage effects, and change-control rules.</p>
      <p class="links"><a href="runtime-motion.html">Open runtime motion catalog</a><a href="{_path_for_html(runtime_overview['html'])}">Open live overview</a></p>
      <div class="grid">
{motion_cards}
      </div>
    </section>
    <section>
      <h2>Illustrated Character Themes</h2>
      <p>Compare the same Character v1 flow in Default Character, Deep Tech, and Teaching Sketch Character.</p>
      <p class="links"><a href="character-themes.html">Open three-theme comparison</a></p>
    </section>
  </main>
  <script>
    document.querySelectorAll("[data-copy]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        try {{
          await navigator.clipboard.writeText(button.dataset.copy || "");
          button.textContent = "Copied";
          setTimeout(() => {{ button.textContent = "Copy CLI"; }}, 1400);
        }} catch (error) {{
          button.textContent = "Copy failed";
        }}
      }});
    }});
  </script>
</body>
</html>
""",
        encoding="utf-8",
    )


def _write_section_index(outdir: Path, title: str, cards: Iterable[Tuple[str, str, str, str, str]]) -> None:
    grid_class = "grid style-grid" if title == "Style Showcase" else "grid"
    style_grid_css = (
        "    .style-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }\n"
        "    @media (max-width: 760px) { .style-grid { grid-template-columns: 1fr; } }\n"
        if title == "Style Showcase"
        else ""
    )
    body = "\n".join(
        f'      <article><a href="{html}"><img src="{svg}" alt="{label} showcase"></a>'
        f"<h2>{label}</h2><h3>{case_title}</h3><p>{subtitle}</p></article>"
        for label, case_title, subtitle, svg, html in cards
    )
    (outdir / "index.html").write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AniDiagram {title}</title>
  <link rel="icon" href="data:,">
  <style>
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: #f8fafc; color: #111827; }}
    main {{ max-width: 1220px; margin: 0 auto; padding: 28px; }}
    h1 {{ font-size: 32px; margin: 0 0 8px; }}
    .intro {{ color: #4b5563; margin: 0 0 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }}
{style_grid_css.rstrip()}
    article {{ border: 1px solid #e5e7eb; border-radius: 8px; background: #ffffff; overflow: hidden; }}
    img {{ display: block; width: 100%; height: auto; }}
    h2 {{ font-size: 18px; margin: 12px 14px 2px; }}
    h3 {{ font-size: 15px; margin: 0 14px 4px; font-weight: 600; color: #1f2937; }}
    p {{ margin: 0 14px 14px; color: #4b5563; }}
  </style>
</head>
<body>
  <main>
    <h1>AniDiagram {title}</h1>
    <p class="intro"><a href="../index.html">Back to gallery home</a></p>
    <section class="{grid_class}">
{body}
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


def _entry_card_html(label: str, entry: Dict[str, Any]) -> str:
    title = entry["title"]
    svg_path = entry["svg"]
    html_path = entry["html"]
    best_for = entry["best_for"]
    cli = _cli_command(entry)
    return (
        f'<article><a href="{_path_for_html(html_path)}"><img src="{_path_for_html(svg_path)}" alt="{label} showcase"></a>'
        f"<h3>{label}</h3><p>{title}</p><p>{', '.join(best_for)}</p>"
        f'<p class="actions"><a href="{_path_for_html(html_path)}">Open HTML</a><button type="button" data-copy="{html_escape(cli, quote=True)}">Copy CLI</button></p></article>'
    )


def _motion_card_html(entry: Dict[str, Any]) -> str:
    best_for = ", ".join(entry.get("best_for", []))
    icon = entry.get("icon", "")
    icon_line = f"<p>Icon: {html_escape(icon)}</p>" if icon else ""
    return (
        f"<article><h3>{html_escape(entry['id'])}</h3>"
        f"<p>{html_escape(entry['title'])}</p>{icon_line}"
        f"<p>{html_escape(best_for)}</p>"
        f'<p class="actions"><a href="runtime-motion.html">Review</a></p></article>'
    )


def _cli_command(entry: Dict[str, Any]) -> str:
    basename = entry.get("basename") or entry.get("preset") or entry.get("style") or entry["id"]
    return (
        "PYTHONPATH=src python3 -m anidiagram.cli "
        f"--spec {entry['spec']} "
        f"--style styles/{entry['style']}.json "
        "--outdir outputs "
        f"--basename {basename} "
        "--formats svg,html,quality "
        "--html-runtime gsap"
    )


def _slug(value: str) -> str:
    text = value.lower()
    cleaned = "".join(char if char.isalnum() else "-" for char in text).strip("-")
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned or "case"


def _rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def _path_for_html(path: str) -> str:
    if path.startswith("gallery/"):
        return path[len("gallery/") :]
    return path


def _path_from_gallery(path: str) -> str:
    if path.startswith("gallery/"):
        return path[len("gallery/") :]
    return f"../{path}"


if __name__ == "__main__":
    main()
