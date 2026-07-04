"""Clean-room preset compilers for DiagramScript v0.2."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


PRESET_NAMES = (
    "pipeline",
    "loop",
    "hub-spoke",
    "layered",
    "swimlane",
    "compare",
    "matrix",
    "timeline",
    "stack",
    "funnel",
    "sequence",
    "er",
    "network",
    "agent-memory",
)


def preset_names() -> List[str]:
    return list(PRESET_NAMES)


def compile_preset(name: str, title: str = "") -> Dict[str, Any]:
    normalized = name.strip().lower()
    if normalized not in PRESET_NAMES:
        raise ValueError(f"unknown preset {name!r}; expected one of: {', '.join(PRESET_NAMES)}")
    builder = globals()[f"_build_{normalized.replace('-', '_')}"]
    spec = builder()
    spec["preset"] = normalized
    if title:
        spec["title"]["text"] = title
    return spec


def _base(title: str, subtitle: str, style: str = "openai-minimal") -> Dict[str, Any]:
    return {
        "version": "0.2",
        "canvas": {"width": 1200, "height": 720},
        "style": style,
        "title": {"text": title, "subtitle": subtitle},
        "groups": [],
        "nodes": [],
        "edges": [],
    }


def _node(node_id: str, label: str, x: int, y: int, role: str = "process", step: int = 0, caption: str = "") -> Dict[str, Any]:
    node = {
        "id": node_id,
        "label": label,
        "caption": caption,
        "position": [x, y],
        "size": [160, 82],
        "role": role,
    }
    if step:
        node["step"] = step
    return node


def _edge(source: str, target: str, label: str = "", role: str = "process", route: str = "curved", step: int = 0) -> Dict[str, Any]:
    edge = {"from": source, "to": target, "label": label, "role": role, "route": route}
    if step:
        edge["step"] = step
    return edge


def _chain(ids: Iterable[str], label: str = "next", route: str = "straight") -> List[Dict[str, Any]]:
    items = list(ids)
    return [_edge(items[index], items[index + 1], label, route=route, step=index + 1) for index in range(len(items) - 1)]


def _build_pipeline() -> Dict[str, Any]:
    spec = _base("Pipeline", "linear work from input to output", "blueprint")
    nodes = [
        _node("input", "Input", 70, 320, "source", 1),
        _node("clean", "Clean", 275, 320, "process", 2),
        _node("model", "Model", 480, 320, "agent", 3),
        _node("review", "Review", 685, 320, "tool", 4),
        _node("ship", "Ship", 890, 320, "output", 5),
    ]
    spec["nodes"] = nodes
    spec["edges"] = _chain([node["id"] for node in nodes], "flow", "straight")
    return spec


def _build_loop() -> Dict[str, Any]:
    spec = _base("Loop", "observe, decide, act, learn", "claude-warm")
    spec["nodes"] = [
        _node("observe", "Observe", 510, 150, "source", 1),
        _node("decide", "Decide", 770, 300, "agent", 2),
        _node("act", "Act", 510, 455, "tool", 3),
        _node("learn", "Learn", 250, 300, "memory", 4),
    ]
    spec["edges"] = [
        _edge("observe", "decide", "signal", "source", "curved", 1),
        _edge("decide", "act", "plan", "agent", "curved", 2),
        _edge("act", "learn", "result", "tool", "curved", 3),
        _edge("learn", "observe", "feedback", "memory", "curved", 4),
    ]
    return spec


def _build_hub_spoke() -> Dict[str, Any]:
    spec = _base("Hub-Spoke", "central coordinator with connected capabilities", "deep-tech")
    spec["nodes"] = [
        _node("hub", "Coordinator", 520, 310, "agent", 1),
        _node("ingest", "Ingest", 260, 150, "source", 2),
        _node("search", "Search", 740, 150, "tool", 3),
        _node("memory", "Memory", 260, 475, "memory", 4),
        _node("policy", "Policy", 740, 475, "risk", 5),
    ]
    spec["edges"] = [
        _edge("hub", "ingest", "pull", "source", "straight"),
        _edge("hub", "search", "query", "tool", "straight"),
        _edge("hub", "memory", "store", "memory", "straight"),
        _edge("hub", "policy", "check", "risk", "straight"),
    ]
    return spec


def _build_layered() -> Dict[str, Any]:
    spec = _base("Layered", "separate interface, domain, and data layers", "notion-clean")
    spec["groups"] = [
        {"id": "ui", "label": "Interface", "bounds": [60, 170, 1080, 110], "role": "actor"},
        {"id": "domain", "label": "Domain", "bounds": [60, 310, 1080, 110], "role": "process"},
        {"id": "data", "label": "Data", "bounds": [60, 450, 1080, 110], "role": "memory"},
    ]
    spec["nodes"] = [
        _node("app", "App", 170, 190, "actor", 1),
        _node("api", "API", 520, 190, "tool", 2),
        _node("rules", "Rules", 350, 330, "process", 3),
        _node("worker", "Worker", 690, 330, "agent", 4),
        _node("db", "Database", 350, 470, "memory", 5),
        _node("queue", "Queue", 690, 470, "source", 6),
    ]
    spec["edges"] = [_edge("app", "api", "call", "tool", "straight"), _edge("api", "rules", "validate", "process", "vh"), _edge("rules", "db", "persist", "memory", "vh"), _edge("worker", "queue", "consume", "source", "vh")]
    return spec


def _build_swimlane() -> Dict[str, Any]:
    spec = _base("Swimlane", "handoffs across owners", "minimal-light")
    spec["groups"] = [
        {"id": "customer", "label": "Customer", "bounds": [60, 160, 1080, 120], "role": "actor"},
        {"id": "team", "label": "Team", "bounds": [60, 310, 1080, 120], "role": "agent"},
        {"id": "system", "label": "System", "bounds": [60, 460, 1080, 120], "role": "tool"},
    ]
    spec["nodes"] = [
        _node("request", "Request", 130, 185, "actor", 1),
        _node("triage", "Triage", 330, 335, "agent", 2),
        _node("automate", "Automate", 560, 485, "tool", 3),
        _node("approve", "Approve", 790, 335, "agent", 4),
        _node("notify", "Notify", 990, 185, "output", 5),
    ]
    spec["edges"] = _chain(["request", "triage", "automate", "approve", "notify"], "handoff", "orthogonal")
    return spec


def _build_compare() -> Dict[str, Any]:
    spec = _base("Compare", "two options with shared decision criteria", "openai-minimal")
    spec["groups"] = [
        {"id": "left", "label": "Option A", "bounds": [120, 170, 390, 390], "role": "process"},
        {"id": "right", "label": "Option B", "bounds": [690, 170, 390, 390], "role": "agent"},
    ]
    spec["nodes"] = [
        _node("a-cost", "Cost", 220, 235, "process", 1),
        _node("a-risk", "Risk", 220, 385, "risk", 2),
        _node("b-cost", "Cost", 790, 235, "agent", 3),
        _node("b-risk", "Risk", 790, 385, "risk", 4),
        _node("decision", "Decision", 520, 565, "output", 5),
    ]
    spec["edges"] = [_edge("a-risk", "decision", "tradeoff", "risk", "vh"), _edge("b-risk", "decision", "tradeoff", "risk", "vh")]
    return spec


def _build_matrix() -> Dict[str, Any]:
    spec = _base("Matrix", "two-by-two prioritization grid", "flat-icon")
    spec["groups"] = [{"id": "matrix", "label": "Impact x Effort", "bounds": [250, 155, 700, 440], "role": "neutral"}]
    spec["nodes"] = [
        _node("quick", "Quick Win", 330, 220, "output", 1),
        _node("major", "Major Bet", 690, 220, "agent", 2),
        _node("fill", "Fill-In", 330, 430, "tool", 3),
        _node("avoid", "Avoid", 690, 430, "risk", 4),
    ]
    return spec


def _build_timeline() -> Dict[str, Any]:
    spec = _base("Timeline", "milestones across a release window", "blueprint")
    nodes = [
        _node("plan", "Plan", 95, 330, "source", 1),
        _node("build", "Build", 300, 330, "process", 2),
        _node("test", "Test", 505, 330, "tool", 3),
        _node("launch", "Launch", 710, 330, "output", 4),
        _node("learn", "Learn", 915, 330, "memory", 5),
    ]
    spec["nodes"] = nodes
    spec["edges"] = _chain([node["id"] for node in nodes], "milestone", "straight")
    return spec


def _build_stack() -> Dict[str, Any]:
    spec = _base("Stack", "vertical dependency layers", "dark-terminal")
    spec["nodes"] = [
        _node("client", "Client", 520, 155, "actor", 1),
        _node("gateway", "Gateway", 520, 265, "tool", 2),
        _node("service", "Service", 520, 375, "process", 3),
        _node("storage", "Storage", 520, 485, "memory", 4),
    ]
    spec["edges"] = _chain(["client", "gateway", "service", "storage"], "depends", "vh")
    return spec


def _build_funnel() -> Dict[str, Any]:
    spec = _base("Funnel", "narrow broad input into qualified output", "glassmorphism")
    spec["nodes"] = [
        _node("traffic", "Traffic", 520, 155, "source", 1),
        _node("score", "Score", 520, 265, "process", 2),
        _node("qualify", "Qualify", 520, 375, "agent", 3),
        _node("convert", "Convert", 520, 485, "output", 4),
    ]
    spec["nodes"][0]["size"] = [240, 82]
    spec["nodes"][1]["size"] = [210, 82]
    spec["nodes"][2]["size"] = [180, 82]
    spec["nodes"][3]["size"] = [150, 82]
    spec["edges"] = _chain(["traffic", "score", "qualify", "convert"], "filter", "vh")
    return spec


def _build_sequence() -> Dict[str, Any]:
    spec = _base("Sequence", "ordered messages between participants", "notion-clean")
    spec["nodes"] = [
        _node("user", "User", 80, 250, "actor", 1),
        _node("app", "App", 320, 250, "tool", 2),
        _node("api", "API", 560, 250, "process", 3),
        _node("db", "DB", 800, 250, "memory", 4),
        _node("done", "Done", 980, 405, "output", 5),
    ]
    spec["edges"] = [
        _edge("user", "app", "submit", "actor", "straight", 1),
        _edge("app", "api", "request", "tool", "straight", 2),
        _edge("api", "db", "query", "memory", "straight", 3),
        _edge("db", "done", "result", "output", "orthogonal", 4),
    ]
    return spec


def _build_er() -> Dict[str, Any]:
    spec = _base("ER", "entities and relationships", "openai-minimal")
    spec["nodes"] = [
        _node("account", "Account", 210, 250, "actor", 1, "id, name"),
        _node("project", "Project", 520, 250, "process", 2, "id, owner"),
        _node("artifact", "Artifact", 830, 250, "memory", 3, "id, project"),
        _node("audit", "Audit Log", 520, 450, "source", 4, "event, actor"),
    ]
    spec["edges"] = [
        _edge("account", "project", "owns", "actor", "straight"),
        _edge("project", "artifact", "contains", "process", "straight"),
        _edge("project", "audit", "emits", "source", "vh"),
    ]
    return spec


def _build_network() -> Dict[str, Any]:
    spec = _base("Network", "distributed nodes with cross-links", "dark-luxury")
    spec["nodes"] = [
        _node("edge-a", "Edge A", 220, 180, "source", 1),
        _node("edge-b", "Edge B", 820, 180, "source", 2),
        _node("core", "Core", 520, 320, "agent", 3),
        _node("cache", "Cache", 220, 480, "memory", 4),
        _node("worker", "Worker", 820, 480, "tool", 5),
    ]
    spec["edges"] = [
        _edge("edge-a", "core", "sync", "source", "straight"),
        _edge("edge-b", "core", "sync", "source", "straight"),
        _edge("core", "cache", "read", "memory", "straight"),
        _edge("core", "worker", "dispatch", "tool", "straight"),
        _edge("cache", "worker", "fanout", "process", "hv"),
    ]
    return spec


def _build_agent_memory() -> Dict[str, Any]:
    spec = _base("Agent Memory", "planning, tools, memory, and grounded output", "blueprint")
    spec["groups"] = [
        {"id": "runtime", "label": "Runtime", "bounds": [280, 155, 375, 395], "role": "process"},
        {"id": "knowledge", "label": "Knowledge", "bounds": [700, 155, 315, 395], "role": "memory"},
    ]
    spec["nodes"] = [
        _node("user", "User", 80, 315, "actor", 1, "asks"),
        _node("agent", "Planner", 365, 235, "agent", 2, "routes"),
        _node("tools", "Tools", 365, 405, "tool", 3, "acts"),
        _node("memory", "Memory", 770, 235, "memory", 4, "recalls"),
        _node("store", "Store", 770, 405, "source", 5, "retrieves"),
        _node("answer", "Answer", 1030, 315, "output", 6, "responds"),
    ]
    spec["edges"] = [
        _edge("user", "agent", "request", "actor", "straight", 1),
        _edge("agent", "tools", "invoke", "tool", "vh", 2),
        _edge("agent", "memory", "read", "memory", "straight", 3),
        _edge("tools", "store", "retrieve", "source", "straight", 4),
        _edge("memory", "answer", "context", "memory", "straight", 5),
        _edge("store", "answer", "evidence", "source", "straight", 6),
    ]
    return spec
