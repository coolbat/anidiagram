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
from anidiagram.quality import quality_report
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style
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
    runtime_entries = [
        {
            "id": "agent-think-act-v2",
            "title": "Agent Think Act",
            "best_for": ["Think", "Decide", "Act"],
        },
        {
            "id": "search-discover-v2",
            "title": "Search Discover",
            "best_for": ["Scan", "Find", "Lock target"],
        },
        {
            "id": "api-request-response-v2",
            "title": "API Request Response",
            "best_for": ["Request", "Response", "Status"],
        },
        {
            "id": "database-write-v2",
            "title": "Database Write",
            "best_for": ["Write", "Commit", "Confirm"],
        },
    ]
    manifest = {
        "hero": hero_entry,
        "styles": style_entries,
        "layouts": layout_entries,
        "runtime_motion": runtime_entries,
    }
    (outdir / "showcase_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_gallery_index(outdir, hero_entry, style_entries, layout_entries, runtime_entries)
    return {
        "ok": True,
        "hero": hero_entry["id"],
        "styles": len(style_entries),
        "layouts": len(layout_entries),
        "manifest": str((outdir / "showcase_manifest.json").resolve()),
    }


def layout_showcase_specs() -> Dict[str, Spec]:
    return {
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
            _motion("teaching", "signal-arrow", "icon-performance", "border-scan", "highlight-sweep", intensity=1.1),
        ),
    }


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
    write_svg(scene, style, svg_path)
    write_html(scene, style, html_path)
    summary = quality_report(scene)["summary"]
    if quality:
        write_quality(scene, quality_path)
    _write_section_index(outdir, "Hero Demo", [("agent-runtime-flow", spec["title"]["text"], spec["title"]["subtitle"], svg_path.name, html_path.name)])
    return {
        "id": "agent-runtime-flow",
        "title": spec["title"]["text"],
        "basename": "agent-runtime-flow",
        "spec": _rel(spec_path),
        "style": "deep-tech",
        "svg": _rel(svg_path),
        "html": _rel(html_path),
        "quality": _rel(quality_path),
        "best_for": ["High-fidelity runtime", "Agent flow", "Semantic icon performance"],
        "summary": summary,
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
            write_quality(scene, quality_path)
        entry = {
            "style": style_name,
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
            write_quality(scene, quality_path)
        entry = {
            "preset": preset,
            "title": title,
            "style": style_name,
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


def _write_gallery_index(
    outdir: Path,
    hero: Dict[str, Any],
    styles: List[Dict[str, Any]],
    layouts: List[Dict[str, Any]],
    runtime_motion: List[Dict[str, Any]],
) -> None:
    style_cards = "\n".join(_entry_card_html(entry["style"], entry) for entry in styles)
    layout_cards = "\n".join(_entry_card_html(entry["preset"], entry) for entry in layouts)
    hero_cli = _cli_command(hero)
    motion_cards = "\n".join(
        f"<article><h3>{entry['id']}</h3><p>{entry['title']}</p><p>{', '.join(entry['best_for'])}</p></article>"
        for entry in runtime_motion
    )
    (outdir / "index.html").write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AniDiagram Showcase</title>
  <style>
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: #f8fafc; color: #111827; }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 28px; }}
    h1 {{ font-size: 36px; margin: 0 0 8px; letter-spacing: 0; }}
    h2 {{ font-size: 24px; margin: 34px 0 12px; }}
    h3 {{ font-size: 16px; margin: 12px 14px 4px; }}
    p {{ color: #4b5563; }}
    .hero img {{ width: 100%; display: block; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }}
    article {{ border: 1px solid #e5e7eb; border-radius: 8px; background: #ffffff; overflow: hidden; }}
    article img {{ display: block; width: 100%; height: auto; }}
    article p {{ margin: 0 14px 14px; }}
    .actions {{ display: flex; gap: 8px; margin: 0 14px 14px; }}
    .actions a, .actions button {{ border: 1px solid #d1d5db; border-radius: 6px; background: #fff; color: #111827; padding: 7px 9px; font: inherit; text-decoration: none; cursor: pointer; }}
    .links a {{ margin-right: 12px; }}
  </style>
</head>
<body>
  <main>
    <h1>AniDiagram Showcase</h1>
    <p>Style Showcase makes diagrams look right. Layout Showcase makes diagram purpose obvious. The hero demonstrates the high-fidelity HTML runtime.</p>
    <section class="hero">
      <h2>Hero Demo</h2>
      <a href="{_path_for_html(hero['html'])}"><img src="{_path_for_html(hero['svg'])}" alt="{hero['title']}"></a>
      <p>{hero['title']} - {', '.join(hero['best_for'])}</p>
      <p class="actions"><a href="{_path_for_html(hero['html'])}">Open HTML</a><button type="button" data-copy="{html_escape(hero_cli, quote=True)}">Copy CLI</button></p>
      <p class="links"><a href="hero/index.html">Open hero gallery</a><a href="showcase_manifest.json">View manifest</a></p>
    </section>
    <section>
      <h2>Style Showcase</h2>
      <p>One signature case for every bundled visual style.</p>
      <div class="grid">
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
      <p>The current P0 high-fidelity icon performances used by the runtime HTML output.</p>
      <div class="grid">
{motion_cards}
      </div>
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
  <style>
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: #f8fafc; color: #111827; }}
    main {{ max-width: 1220px; margin: 0 auto; padding: 28px; }}
    h1 {{ font-size: 32px; margin: 0 0 8px; }}
    .intro {{ color: #4b5563; margin: 0 0 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }}
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
    <section class="grid">
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


if __name__ == "__main__":
    main()
