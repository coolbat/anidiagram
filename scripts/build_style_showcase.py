#!/usr/bin/env python3
"""Build one clean-room showcase case for every bundled style."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from anidiagram.exporters import write_html, write_quality, write_svg
from gallery_previews import live_preview, preview_controls, preview_head, write_preview_assets
from anidiagram.edge_motion import canonical_edge_motion
from anidiagram.quality import quality_report
from anidiagram.schema import compile_scene
from anidiagram.styles import load_style


Point = Tuple[int, int]
Size = Tuple[int, int]
Spec = Dict[str, Any]


STYLE_ORDER = (
    "minimal-light",
    "deep-tech",
    "blueprint",
    "flat-icon",
    "dark-terminal",
    "notion-clean",
    "glassmorphism",
    "claude-warm",
    "openai-minimal",
    "dark-luxury",
    "aurora-orb",
    "illustrated-semantic",
    "sketch-board",
)

STYLE_SHOWCASE_LAYOUTS = {
    "minimal-light": "pipeline",
    "deep-tech": "network",
    "blueprint": "layered",
    "flat-icon": "matrix",
    "dark-terminal": "pipeline",
    "notion-clean": "pipeline",
    "glassmorphism": "funnel",
    "claude-warm": "loop",
    "openai-minimal": "pipeline",
    "dark-luxury": "network",
    "aurora-orb": "hub-spoke",
    "illustrated-semantic": "pipeline",
    "sketch-board": "loop",
}

PUBLIC_SHOWCASE_ICON_SYSTEM = "illustrated"
PUBLIC_SHOWCASE_ICON_VERSION = "2.5.0"
PUBLIC_SHOWCASE_MOTION = "showcase-v1"
PUBLIC_SHOWCASE_HORIZONTAL_SCALE = 1.25
PUBLIC_SHOWCASE_RIGHT_MARGIN = 32
PUBLIC_SHOWCASE_MIN_NODE_WIDTH = 240
_DYNAMIC_EDGE_EFFECTS = {"packet-flow", "comet-flow", "stream-flow"}


def adapt_public_showcase_geometry(spec: Spec) -> None:
    """Expand legacy Character v1 geometry for Illustrated 2.5 cards."""

    scale = PUBLIC_SHOWCASE_HORIZONTAL_SCALE
    canvas = spec.get("canvas")
    if isinstance(canvas, dict) and isinstance(canvas.get("width"), (int, float)):
        canvas["width"] = round(canvas["width"] * scale) + PUBLIC_SHOWCASE_RIGHT_MARGIN
    for node in spec.get("nodes", []):
        position = node.get("position")
        size = node.get("size")
        if isinstance(position, list) and len(position) == 2:
            position[0] = round(position[0] * scale)
        if isinstance(size, list) and len(size) == 2:
            size[0] = max(PUBLIC_SHOWCASE_MIN_NODE_WIDTH, size[0])
    for group in spec.get("groups", []):
        bounds = group.get("bounds")
        if isinstance(bounds, list) and len(bounds) == 4:
            bounds[0] = round(bounds[0] * scale)
            bounds[2] = round(bounds[2] * scale)
    for edge in spec.get("edges", []):
        points = edge.get("points")
        if isinstance(points, list):
            for point in points:
                if isinstance(point, list) and len(point) == 2:
                    point[0] = round(point[0] * scale)


def apply_public_showcase_contract(
    source: Spec,
    *,
    layout: str,
    style_source: str = "explicit",
    layout_source: str = "explicit",
) -> Spec:
    """Return a composition-v1 public Showcase spec without changing geometry.

    The helper is intentionally shared by the standalone style builder and the
    combined gallery builder so either entry point resolves the same four
    presentation axes. Existing dynamic edge recipes are canonicalized through
    Edge Motion v1; static, draw-only, or omitted recipes become packet flow so
    every Showcase data-flow edge remains visibly active.
    """

    spec = deepcopy(source)
    adapt_public_showcase_geometry(spec)
    style = str(spec["style"])
    spec["version"] = "0.4"
    spec["composition_policy"] = "composition-v1"
    spec["icon_system"] = PUBLIC_SHOWCASE_ICON_SYSTEM
    spec["layout"] = layout
    spec["resolved_presentation"] = {
        "icon_system": {
            "value": PUBLIC_SHOWCASE_ICON_SYSTEM,
            "source": "default",
            "version": PUBLIC_SHOWCASE_ICON_VERSION,
        },
        "style": {"value": style, "source": style_source},
        "layout": {"value": layout, "source": layout_source},
        "motion": {"value": PUBLIC_SHOWCASE_MOTION, "source": "default"},
    }
    spec["motion"] = {
        "profile": PUBLIC_SHOWCASE_MOTION,
        "sequence": "staged",
        "ease": "spring",
        "stagger": 0.12,
        "duration_scale": 1.0,
        "intensity": 1.0,
        "edge": {"preset": "packet-flow"},
        "node": {"preset": "icon-performance"},
        "group": {"preset": "border-scan"},
        "title": {"preset": "highlight-sweep"},
        "reduced_motion": "subtle",
    }
    spec["motion_policy"] = {
        "profile": "unrestricted",
        "motion_area": "unrestricted",
        "pulse_mode": "all",
    }
    for edge in spec.get("edges", []):
        effect = edge.get("effect")
        preset = effect.get("preset") if isinstance(effect, dict) else effect
        canonical = canonical_edge_motion(str(preset or "packet-flow"))
        if canonical not in _DYNAMIC_EDGE_EFFECTS:
            canonical = "packet-flow"
        edge["animated"] = True
        edge["effect"] = {"preset": canonical}
    return spec


def style_showcase_specs() -> Dict[str, Spec]:
    specs = {
        "minimal-light": _flow_case(
            "minimal-light",
            "Customer Support Triage",
            "intake, classify, answer, and learn",
            [
                _node("customer", "Customer", "new request", (90, 335), "actor", "agent"),
                _node("inbox", "Inbox", "ticket queue", (300, 335), "source", "folder"),
                _node("triage", "Triage", "route issue", (510, 335), "process", "search"),
                _node("reply", "Reply", "draft answer", (720, 335), "tool", "file"),
                _node("learn", "Learn", "update notes", (930, 335), "memory", "memory"),
            ],
            _chain(["customer", "inbox", "triage", "reply", "learn"], "handoff", "straight"),
            [_group("ops", "Support Desk", (60, 250, 1080, 190), "neutral")],
            _motion("subtle", "draw", "fade", "soft-reveal", "fade", intensity=0.55),
        ),
        "deep-tech": _flow_case(
            "deep-tech",
            "Realtime AI Ops Mesh",
            "signals move through policy, model, and action loops",
            [
                _node("signals", "Signals", "events", (90, 195), "source", "cloud"),
                _node("stream", "Stream", "normalize", (315, 195), "process", "api"),
                _node("agent", "Agent", "coordinate", (540, 315), "agent", "agent", (190, 92)),
                _node("model", "Model", "score", (790, 195), "tool", "tool"),
                _node("policy", "Policy", "guard", (790, 445), "risk", "shield"),
                _node("action", "Action", "dispatch", (1015, 315), "output", "output"),
            ],
            [
                _edge("signals", "stream", "ingest", "source", "straight"),
                _edge("stream", "agent", "context", "process", "orthogonal"),
                _edge("agent", "model", "score", "tool", "orthogonal", effect="flow-arrow"),
                _edge("agent", "policy", "check", "risk", "orthogonal", effect="dynamic-dash"),
                _edge("model", "action", "pass", "output", "orthogonal"),
                _edge("policy", "action", "approve", "output", "orthogonal"),
            ],
            [
                _group("telemetry", "Telemetry", (60, 150, 475, 165), "source"),
                _group("runtime", "Runtime", (500, 145, 640, 420), "agent"),
            ],
            _motion("expressive", "flow-arrow", "glow-breathe", "marching-ants", "highlight-sweep", intensity=1.35),
        ),
        "blueprint": _flow_case(
            "blueprint",
            "MCP Server Architecture",
            "client requests route through tools, resources, auth, and transport",
            [
                _node("client", "Client", "LLM host", (90, 300), "actor", "agent"),
                _node("transport", "Transport", "stdio / http", (300, 300), "tool", "api"),
                _node("server", "MCP Server", "capability router", (520, 300), "agent", "tool", (190, 88)),
                _node("tools", "Tools", "actions", (775, 205), "process", "tool"),
                _node("resources", "Resources", "read context", (775, 395), "memory", "folder"),
                _node("policy", "Policy", "auth + limits", (1000, 300), "risk", "shield"),
            ],
            [
                _edge("client", "transport", "request", "actor", "straight"),
                _edge("transport", "server", "message", "tool", "straight"),
                _edge("server", "tools", "invoke", "process", "orthogonal", effect="flow-arrow"),
                _edge("server", "resources", "read", "memory", "orthogonal", effect="dynamic-dash"),
                _edge("tools", "policy", "guard", "risk", "orthogonal"),
                _edge("resources", "policy", "scope", "risk", "orthogonal"),
            ],
            [
                _group("client-plane", "Client Plane", (60, 225, 450, 195), "source"),
                _group("server-plane", "Server Plane", (490, 140, 655, 365), "agent"),
            ],
            _motion("expressive", "dynamic-dash", "pop", "border-scan", "highlight-sweep", intensity=1.1),
        ),
        "flat-icon": _flow_case(
            "flat-icon",
            "Feature Priority Board",
            "demand signals become a focused roadmap",
            [
                _node("demand", "Demand", "requests", (95, 320), "source", "search"),
                _node("quick", "Quick Win", "high value", (345, 205), "output", "tool"),
                _node("bet", "Big Bet", "strategic", (655, 205), "agent", "agent"),
                _node("fill", "Fill In", "low effort", (345, 425), "tool", "file"),
                _node("avoid", "Avoid", "too risky", (655, 425), "risk", "shield"),
                _node("roadmap", "Roadmap", "commit", (985, 320), "memory", "folder"),
            ],
            [
                _edge("demand", "quick", "score", "source", "orthogonal"),
                _edge("demand", "fill", "score", "source", "orthogonal"),
                _edge("quick", "roadmap", "select", "output", "orthogonal", effect="flow-dot"),
                _edge("bet", "roadmap", "sequence", "agent", "orthogonal"),
                _edge("avoid", "roadmap", "defer", "risk", "orthogonal", effect="static"),
            ],
            [_group("matrix", "Impact x Effort", (310, 150, 570, 380), "neutral")],
            _motion("normal", "flow-dot", "icon-pulse", "soft-reveal", "fade", intensity=0.95),
        ),
        "dark-terminal": _flow_case(
            "dark-terminal",
            "Incident Response Runbook",
            "operators isolate, patch, and verify production",
            [
                _node("alert", "Alert", "page on-call", (110, 145), "risk", "shield"),
                _node("shell", "Shell", "inspect", (110, 275), "tool", "api"),
                _node("isolate", "Isolate", "contain", (110, 405), "process", "cloud"),
                _node("patch", "Patch", "fix", (510, 275), "agent", "tool"),
                _node("verify", "Verify", "checks", (810, 275), "source", "search"),
                _node("notes", "Notes", "postmortem", (1010, 405), "memory", "file"),
            ],
            [
                _edge("alert", "shell", "open", "risk", "vh", effect="dynamic-dash"),
                _edge("shell", "isolate", "lock", "tool", "vh"),
                _edge("isolate", "patch", "handoff", "process", "orthogonal"),
                _edge("patch", "verify", "test", "agent", "straight", effect="flow-arrow"),
                _edge("verify", "notes", "record", "memory", "vh"),
            ],
            [_group("terminal", "War Room", (70, 95, 1110, 460), "neutral")],
            _motion("expressive", "dynamic-dash", "status-blink", "corner-pulse", "highlight-sweep", intensity=1.2),
        ),
        "notion-clean": _flow_case(
            "notion-clean",
            "Product Discovery Workflow",
            "research notes become a tested product decision",
            [
                _node("notes", "Notes", "interviews", (105, 285), "source", "file"),
                _node("patterns", "Patterns", "cluster", (325, 285), "memory", "folder"),
                _node("prototype", "Prototype", "try", (545, 285), "tool", "tool"),
                _node("test", "Test", "measure", (765, 285), "agent", "search"),
                _node("decision", "Decision", "ship or stop", (985, 285), "output", "output"),
            ],
            _chain(["notes", "patterns", "prototype", "test", "decision"], "next", "straight"),
            [
                _group("research", "Research", (70, 215, 450, 180), "source"),
                _group("decision", "Decision", (520, 215, 635, 180), "process"),
            ],
            _motion("subtle", "draw", "fade", "soft-reveal", "fade", intensity=0.5),
        ),
        "glassmorphism": _flow_case(
            "glassmorphism",
            "AI Growth Funnel",
            "signals become qualified users, activation, and expansion loops",
            [
                _node("traffic", "Traffic", "visits", (505, 130), "source", "cloud", (230, 78)),
                _node("qualify", "Qualify", "fit + intent", (525, 245), "process", "search", (190, 78)),
                _node("activate", "Activate", "first value", (545, 360), "agent", "agent", (150, 78)),
                _node("expand", "Expand", "next best action", (565, 475), "tool", "tool", (145, 78)),
                _node("retain", "Retain", "loop", (575, 590), "output", "output", (120, 70)),
                _node("crm", "Growth DB", "history", (870, 360), "memory", "database"),
            ],
            [
                _edge("traffic", "qualify", "filter", "source", "vh"),
                _edge("qualify", "activate", "rank", "process", "vh"),
                _edge("activate", "expand", "suggest", "agent", "vh", effect="ghost-flow"),
                _edge("expand", "retain", "commit", "output", "vh", effect="flow-dot"),
                _edge("crm", "activate", "context", "memory", "straight"),
            ],
            [_group("funnel", "Funnel", (450, 80, 345, 600), "process")],
            _motion("expressive", "ghost-flow", "pulse", "border-scan", "highlight-sweep", intensity=1.0),
        ),
        "claude-warm": _flow_case(
            "claude-warm",
            "Research Reasoning Loop",
            "questions cycle through evidence and critique",
            [
                _node("question", "Question", "frame", (515, 130), "actor", "agent"),
                _node("collect", "Collect", "sources", (780, 285), "source", "search"),
                _node("synth", "Synthesis", "draft", (515, 445), "process", "file"),
                _node("critique", "Critique", "check", (250, 285), "risk", "shield"),
                _node("memory", "Memory", "reuse", (515, 285), "memory", "memory"),
            ],
            [
                _edge("question", "collect", "look up", "source", "curved"),
                _edge("collect", "synth", "evidence", "source", "curved"),
                _edge("synth", "critique", "review", "risk", "curved", effect="dynamic-dash"),
                _edge("critique", "question", "revise", "actor", "curved"),
                _edge("memory", "synth", "recall", "memory", "vh", effect="flow-dot"),
            ],
            [_group("loop", "Reasoning Loop", (210, 90, 790, 500), "neutral")],
            _motion("expressive", "comet-flow", "pop", "marching-ants", "fade", intensity=0.9),
        ),
        "openai-minimal": _flow_case(
            "openai-minimal",
            "Evaluation Pipeline",
            "prompts, candidates, judges, and release reports",
            [
                _node("prompt", "Prompt", "task", (110, 315), "source", "file"),
                _node("candidates", "Candidates", "outputs", (330, 315), "agent", "agent"),
                _node("judge", "Judge", "rubric", (550, 315), "tool", "shield"),
                _node("report", "Report", "scores", (770, 315), "memory", "database"),
                _node("release", "Release", "decision", (990, 315), "output", "output"),
            ],
            _chain(["prompt", "candidates", "judge", "report", "release"], "eval", "straight"),
            [_group("eval", "Eval Harness", (75, 250, 1090, 185), "neutral")],
            _motion("subtle", "draw", "fade", "soft-reveal", "fade", intensity=0.45),
        ),
        "dark-luxury": _flow_case(
            "dark-luxury",
            "Executive Signal Network",
            "market, finance, and product signals converge",
            [
                _node("market", "Market", "signals", (185, 165), "source", "cloud"),
                _node("finance", "Finance", "metrics", (185, 465), "memory", "database"),
                _node("product", "Product", "usage", (825, 165), "tool", "search"),
                _node("board", "Board", "decision", (505, 315), "agent", "agent", (205, 92)),
                _node("action", "Action", "portfolio", (825, 465), "output", "output"),
                _node("risk", "Risk", "guardrail", (505, 535), "risk", "shield"),
            ],
            [
                _edge("market", "board", "trend", "source", "straight"),
                _edge("finance", "board", "margin", "memory", "straight"),
                _edge("product", "board", "usage", "tool", "straight"),
                _edge("board", "action", "allocate", "output", "straight", effect="flow-arrow"),
                _edge("risk", "board", "check", "risk", "vh", effect="glow-line"),
            ],
            [_group("signals", "Signal Room", (130, 110, 920, 530), "neutral")],
            _motion("expressive", "glow-line", "pulse", "border-scan", "highlight-sweep", intensity=1.05),
        ),
        "aurora-orb": _flow_case(
            "aurora-orb",
            "Creative Agent Studio",
            "briefs become variants, reviews, and publishable assets",
            [
                _node("brief", "Brief", "intent", (90, 315), "actor", "file"),
                _node("mood", "Mood", "palette", (305, 210), "source", "folder"),
                _node("agent", "Studio Agent", "compose", (520, 315), "agent", "agent", (205, 92)),
                _node("variants", "Variants", "options", (765, 210), "tool", "tool"),
                _node("review", "Review", "select", (765, 420), "risk", "shield"),
                _node("publish", "Publish", "export", (1000, 315), "output", "output"),
            ],
            [
                _edge("brief", "agent", "intent", "actor", "straight"),
                _edge("mood", "agent", "style", "source", "orthogonal", effect="ghost-flow"),
                _edge("agent", "variants", "create", "agent", "orthogonal", effect="flow-arrow"),
                _edge("variants", "review", "choose", "tool", "vh"),
                _edge("review", "publish", "approve", "output", "orthogonal", effect="flow-dot"),
            ],
            [_group("studio", "Studio Canvas", (55, 145, 1090, 420), "agent")],
            _motion("expressive", "ghost-flow", "icon-pulse", "border-scan", "highlight-sweep", intensity=1.2),
        ),
        "illustrated-semantic": _flow_case(
            "illustrated-semantic",
            "Semantic Delivery Pipeline",
            "clear illustrated roles on a warm, low-noise canvas",
            [
                _node("brief", "Brief", "input", (90, 315), "actor", "file"),
                _node("think", "Think", "reason", (300, 315), "agent", "agent"),
                _node("operate", "Operate", "review", (510, 315), "source", "operator"),
                _node("execute", "Execute", "run", (720, 315), "tool", "tool"),
                _node("deliver", "Deliver", "confirm", (930, 315), "output", "output"),
            ],
            _chain(["brief", "think", "operate", "execute", "deliver"], "handoff", "straight"),
            [_group("semantic-flow", "Structured Semantic Flow", (55, 245, 1095, 210), "neutral")],
            _motion("subtle", "draw", "fade", "soft-reveal", "fade", intensity=0.65),
        ),
        "sketch-board": _flow_case(
            "sketch-board",
            "Attention Teaching Flow",
            "tokens, attention, alignment, and output as a staged lesson",
            [
                _node("tokens", "Tokens", "input words", (105, 210), "source", "token"),
                _node("embed", "Embed", "meaning", (325, 210), "memory", "database"),
                _node("attend", "Attend", "mix signals", (545, 315), "agent", "agent"),
                _node("align", "Aligned?", "mask + context", (765, 315), "risk", "shield"),
                _node("softmax", "Softmax", "scores", (985, 210), "tool", "tool"),
                _node("output", "Output", "next token", (985, 430), "output", "output"),
            ],
            [
                _edge("tokens", "embed", "encode", "source", "straight", effect="flow-dot"),
                _edge("embed", "attend", "context", "memory", "orthogonal", effect="ghost-flow"),
                _edge("attend", "align", "score", "agent", "straight", effect="flow-arrow"),
                _edge("align", "softmax", "yes", "output", "orthogonal"),
                _edge("align", "output", "predict", "output", "orthogonal", effect="glow-line"),
                _edge("output", "attend", "feedback", "memory", "orthogonal", effect="dynamic-dash"),
            ],
            [
                _group("input", "Source Tokens", (65, 155, 455, 175), "source"),
                _group("core", "Transformer Core", (515, 155, 670, 410), "agent"),
            ],
            _motion("teaching", "ghost-flow", "icon-pulse", "border-scan", "handwrite-reveal", sequence="staged", intensity=1.15),
        ),
    }
    return {
        style_name: apply_public_showcase_contract(
            spec,
            layout=STYLE_SHOWCASE_LAYOUTS[style_name],
        )
        for style_name, spec in specs.items()
    }


def build_showcase(spec_dir: Path, outdir: Path, quality: bool) -> Dict[str, Any]:
    catalog_styles = _catalog_styles()
    specs = style_showcase_specs()
    missing = [style for style in catalog_styles if style not in specs]
    extra = [style for style in specs if style not in catalog_styles]
    if missing or extra:
        raise SystemExit(json.dumps({"missing": missing, "extra": extra}, indent=2))

    spec_dir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)
    cards = []
    summaries = {}
    for style_name in catalog_styles:
        spec = specs[style_name]
        spec_path = spec_dir / f"{style_name}.diagram.json"
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        scene = compile_scene(spec)
        style = load_style(ROOT / "styles" / f"{style_name}.json")
        svg_path = outdir / f"{style_name}.svg"
        html_path = outdir / f"{style_name}.html"
        write_svg(scene, style, svg_path)
        write_html(scene, style, html_path)
        report = quality_report(scene)
        if quality:
            write_quality(scene, style, outdir / f"{style_name}.quality.json")
        cards.append((style_name, spec["title"]["text"], spec["title"]["subtitle"], svg_path.name, html_path.name))
        summaries[style_name] = report["summary"]
    write_index(outdir, cards)
    write_preview_assets(outdir)
    return {"ok": True, "styles": catalog_styles, "spec_dir": str(spec_dir.resolve()), "outdir": str(outdir.resolve()), "quality": summaries}


def write_index(outdir: Path, cards: Iterable[Tuple[str, str, str, str, str]]) -> None:
    body = "\n".join(
        '      <article>' + live_preview(svg, html, f'{style} style showcase') +
        f"<h2>{style}</h2><h3>{title}</h3><p>{subtitle}</p></article>"
        for style, title, subtitle, svg, html in cards
    )
    (outdir / "index.html").write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AniDiagram Style Showcase</title>
  {preview_head()}
  <link rel="icon" href="data:,">
  <style>
    body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: #f8fafc; color: #111827; }}
    main {{ max-width: 1220px; margin: 0 auto; padding: 28px; }}
    h1 {{ font-size: 32px; margin: 0 0 8px; }}
    .intro {{ color: #4b5563; margin: 0 0 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
    article {{ border: 1px solid #e5e7eb; border-radius: 8px; background: #ffffff; overflow: hidden; }}
    img {{ display: block; width: 100%; height: auto; }}
    h2 {{ font-size: 18px; margin: 12px 14px 2px; }}
    h3 {{ font-size: 15px; margin: 0 14px 4px; font-weight: 600; color: #1f2937; }}
    p {{ margin: 0 14px 14px; color: #4b5563; }}
    @media (max-width: 760px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <h1>AniDiagram Style Showcase</h1>
    {preview_controls()}
    <p class="intro">One generated clean-room case for every bundled style. Click a card to open the high-fidelity HTML output.</p>
    <section class="grid">
{body}
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


def _catalog_styles() -> List[str]:
    catalog = json.loads((ROOT / "styles" / "catalog.json").read_text(encoding="utf-8"))
    return list(catalog["styles"])


def _flow_case(
    style: str,
    title: str,
    subtitle: str,
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    motion: Dict[str, Any],
) -> Spec:
    return {
        "version": "0.3",
        "canvas": {"width": 1280, "height": 720},
        "style": style,
        "title": {"text": title, "subtitle": subtitle},
        "motion": motion,
        "groups": groups,
        "nodes": nodes,
        "edges": edges,
    }


def _motion(
    profile: str,
    edge: str,
    node: str,
    group: str,
    title: str,
    sequence: str = "step-stagger",
    intensity: float = 1.0,
) -> Dict[str, Any]:
    return {
        "profile": profile,
        "sequence": sequence,
        "ease": "spring" if profile in {"expressive", "teaching"} else "calm",
        "stagger": 0.12,
        "duration_scale": 1.0,
        "intensity": intensity,
        "edge": {"preset": edge, "particle": "soft-arrow" if edge == "flow-arrow" else "soft-dot", "trail": edge in {"ghost-flow", "comet-flow", "comet"}},
        "node": {"preset": node, "accent": "ripple" if node in {"icon-pulse", "pulse"} else "glow"},
        "group": {"preset": group},
        "title": {"preset": title},
        "reduced_motion": "subtle",
    }


def _node(
    node_id: str,
    label: str,
    caption: str,
    position: Point,
    role: str,
    icon: str,
    size: Size = (180, 84),
) -> Dict[str, Any]:
    return {
        "id": node_id,
        "label": label,
        "caption": caption,
        "position": list(position),
        "size": list(size),
        "role": role,
        "icon": icon,
    }


def _edge(
    source: str,
    target: str,
    label: str,
    role: str,
    route: str,
    effect: str = "",
) -> Dict[str, Any]:
    edge: Dict[str, Any] = {"from": source, "to": target, "label": label, "role": role, "route": route}
    if effect:
        edge["effect"] = {"preset": effect, "particle": "soft-arrow" if effect == "flow-arrow" else "soft-dot", "trail": effect in {"ghost-flow", "comet-flow", "comet"}}
    return edge


def _chain(node_ids: List[str], label: str, route: str) -> List[Dict[str, Any]]:
    return [_edge(node_ids[index], node_ids[index + 1], label, "process", route) for index in range(len(node_ids) - 1)]


def _group(group_id: str, label: str, bounds: Tuple[int, int, int, int], role: str) -> Dict[str, Any]:
    return {"id": group_id, "label": label, "bounds": list(bounds), "role": role}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one AniDiagram showcase case for every bundled style.")
    parser.add_argument("--spec-dir", default="examples/style-showcase", help="Directory for generated DiagramScript specs.")
    parser.add_argument("--outdir", default="gallery/styles", help="Directory for generated showcase assets.")
    parser.add_argument("--quality", action="store_true", help="Also write quality report JSON files.")
    args = parser.parse_args()

    result = build_showcase(Path(args.spec_dir), Path(args.outdir), args.quality)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
