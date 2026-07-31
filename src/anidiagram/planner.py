"""Brief-to-DiagramPlan helpers for freeform AniDiagram scenes."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .composition import compile_plan_v02
from .localization import contains_cjk, resolve_locale


PlanDict = Dict[str, Any]
SpecDict = Dict[str, Any]


_STOP_WORDS = {
    "about",
    "after",
    "agent",
    "agents",
    "also",
    "and",
    "architecture",
    "build",
    "content",
    "diagram",
    "flow",
    "from",
    "into",
    "layout",
    "make",
    "need",
    "needs",
    "process",
    "system",
    "that",
    "the",
    "this",
    "user",
    "with",
}

_MEMORY_TERMS = (
    "memory", "context", "remember", "knowledge", "notes",
    "记忆", "上下文", "知识", "知识库", "笔记",
)
_TOOL_TERMS = (
    "tool", "api", "browser", "search", "call", "execute",
    "工具", "接口", "浏览器", "搜索", "调用", "执行",
)
_SAFETY_TERMS = (
    "safe", "safety", "guard", "policy", "risk", "validate", "validation", "budget", "constraint", "review",
    "安全", "护栏", "策略", "风险", "校验", "验证", "预算", "约束", "审核",
)
_LOOP_TERMS = (
    "loop", "iterate", "feedback", "retry", "observe", "reflect",
    "循环", "迭代", "反馈", "重试", "观察", "反思", "回路",
)
_SEARCH_TERMS = ("search", "browser", "搜索", "浏览器")


def brief_to_plan(
    brief: str,
    title: str = "",
    style: Optional[str] = None,
    version: str = "0.2",
    language: str = "auto",
) -> PlanDict:
    """Create a deterministic plan; new calls default to composition-v1."""

    if version == "0.1":
        return _brief_to_plan_v01(brief, title=title, style=style or "sketch-board")
    if version != "0.2":
        raise ValueError("DiagramPlan version must be '0.1' or '0.2'")
    return _brief_to_plan_v02(brief, title=title, style=style, language=language)


def _brief_to_plan_v01(brief: str, title: str = "", style: str = "sketch-board") -> PlanDict:
    """Create a deterministic DiagramPlan v0.1 from a natural-language brief.

    This is intentionally model-free. A future LLM integration can replace the
    extraction step as long as it emits the same DiagramPlan contract.
    """

    cleaned = " ".join(brief.split())
    keywords = _keywords(cleaned)
    plan_title = title or _title_from_brief(cleaned, keywords)
    has_memory = _contains(cleaned, _MEMORY_TERMS)
    has_tools = _contains(cleaned, _TOOL_TERMS)
    has_safety = _contains(cleaned, _SAFETY_TERMS)
    has_loop = _contains(cleaned, _LOOP_TERMS)

    sections = [
        {"id": "inputs", "label": "Inputs", "role": "source"},
        {"id": "core", "label": "Agent Work Loop" if has_loop else "Core Flow", "role": "agent"},
        {"id": "memory", "label": "Memory", "role": "memory"},
        {"id": "guardrails", "label": "Guardrails", "role": "risk"},
        {"id": "tools", "label": "Tools", "role": "tool"},
    ]
    main_flow = [
        {
            "id": "clarify",
            "label": "Clarify",
            "caption": _caption("goal and limits", keywords, 0),
            "role": "agent",
            "icon": "search",
        },
        {
            "id": "plan",
            "label": "Plan",
            "caption": _caption("steps and layout", keywords, 1),
            "role": "process",
            "icon": "agent",
        },
        {
            "id": "act",
            "label": "Act",
            "caption": _caption("tools and edits", keywords, 2) if has_tools else "make the change",
            "role": "tool" if has_tools else "process",
            "icon": "tool" if has_tools else "api",
        },
        {
            "id": "observe",
            "label": "Observe",
            "caption": "check output and evidence",
            "role": "process",
            "icon": "search",
        },
        {
            "id": "done",
            "label": "Done?",
            "caption": "quality gate",
            "role": "risk" if has_safety else "neutral",
            "shape": "decision",
            "icon": "shield" if has_safety else None,
        },
        {
            "id": "output",
            "label": "Output",
            "caption": "verified result",
            "role": "output",
            "icon": "output",
        },
    ]
    support_panels = [
        {
            "id": "memory",
            "label": "Memory",
            "role": "memory",
            "items": [
                {"id": "working-memory", "label": "Working Memory", "caption": "current task state", "role": "memory", "icon": "memory"},
                {"id": "long-term-notes", "label": "Long-Term Notes", "caption": "prior decisions", "role": "memory", "icon": "database"},
            ],
        },
        {
            "id": "guardrails",
            "label": "Guardrails",
            "role": "risk",
            "items": [
                {"id": "validate", "label": "Validate", "caption": "schema and tests", "role": "risk", "icon": "shield"},
                {"id": "scope", "label": "Scope", "caption": "stay in bounds", "role": "neutral", "icon": "file"},
                {"id": "budget", "label": "Budget", "caption": "time and tokens", "role": "neutral", "icon": "token"},
                {"id": "replan", "label": "Replan", "caption": "fix failures", "role": "process", "icon": "agent"},
            ],
        },
        {
            "id": "tools",
            "label": "Tooling",
            "role": "tool",
            "items": [
                {"id": "tool-calls", "label": "Tool Calls", "caption": "search render test", "role": "tool", "icon": "tool"},
                {"id": "tool-results", "label": "Tool Results", "caption": "logs and files", "role": "output", "icon": "folder"},
            ],
        },
    ]
    inputs = [
        {"id": "brief", "label": "Brief", "caption": "request", "role": "source", "icon": "file"},
        {"id": "context", "label": "Context", "caption": "docs", "role": "memory" if has_memory else "source", "icon": "memory"},
        {"id": "events", "label": "Events", "caption": "signals", "role": "source", "icon": "api"},
        {"id": "policy", "label": "Policy", "caption": "rules", "role": "risk", "icon": "shield"},
    ]

    return {
        "version": "0.1",
        "title": plan_title,
        "subtitle": "Brief-derived DiagramPlan compiled to freeform DiagramScript.",
        "source_summary": _source_summary(cleaned),
        "style": style,
        "layout_strategy": "explainer-board",
        "motion_profile": "teaching",
        "motion_policy": _default_motion_policy(),
        "sections": sections,
        "inputs": inputs,
        "main_flow": main_flow,
        "support_panels": support_panels,
        "feedback_paths": [
            {"from": "done", "to": "plan", "label": "No: revise", "role": "risk"},
            {"from": "working-memory", "to": "plan", "label": "context", "role": "memory"},
            {"from": "act", "to": "tool-calls", "label": "dispatch", "role": "tool"},
            {"from": "tool-results", "to": "observe", "label": "results", "role": "output"},
        ],
        "emphasis": _emphasis(has_loop, has_memory, has_tools, has_safety),
    }


def _brief_to_plan_v02(
    brief: str,
    title: str = "",
    style: Optional[str] = None,
    language: str = "auto",
) -> PlanDict:
    """Extract a native semantic v0.2 plan without routing through v0.1 geometry."""

    cleaned = " ".join(brief.split())
    keywords = _keywords(cleaned)
    resolved_language = resolve_locale(language, (title, cleaned))
    is_chinese = resolved_language == "zh-CN"
    plan_title = title or _title_from_brief(cleaned, keywords, language=resolved_language)
    summary = _source_summary(cleaned)
    has_memory = _contains(cleaned, _MEMORY_TERMS)
    has_tools = _contains(cleaned, _TOOL_TERMS)
    has_safety = _contains(cleaned, _SAFETY_TERMS)
    has_loop = _contains(cleaned, _LOOP_TERMS)
    labels = {
        "request": "请求" if is_chinese else "Request",
        "agent": "智能体" if is_chinese else "Agent",
        "memory": "长期记忆" if is_chinese else "Memory",
        "tool": "搜索工具" if is_chinese and _contains(cleaned, _SEARCH_TERMS) else "工具" if is_chinese else "Tool",
        "guardrail": "安全校验" if is_chinese else "Guardrail",
        "output": "已验证输出" if is_chinese else "Verified output",
    }

    entities: List[Dict[str, Any]] = [
        {
            "id": "request",
            "label": labels["request"],
            "description": "输入需求" if is_chinese else _caption("input brief", keywords, 0),
            "kind": "http-request",
            "role": "source",
            "importance": "primary",
            "state": {"phase": "received"},
            "source_refs": ["input-brief"],
        },
        {
            "id": "agent",
            "label": labels["agent"],
            "description": "推理与协调" if is_chinese else _caption("reason and coordinate", keywords, 1),
            "kind": "agent",
            "role": "agent",
            "importance": "primary",
            "state": {"phase": "active", "result": "pending"},
            "source_refs": ["input-brief"],
        },
    ]
    if has_memory:
        entities.append(
            {
                "id": "memory",
                "label": labels["memory"],
                "description": "读取并更新工作上下文" if is_chinese else "read and update working context",
                "kind": "memory",
                "role": "memory",
                "importance": "supporting",
                "source_refs": ["input-brief"],
            }
        )
    if has_tools:
        entities.append(
            {
                "id": "tool",
                "label": labels["tool"],
                "description": "执行外部操作" if is_chinese else _caption("execute external action", keywords, 2),
                "kind": "search" if _contains(cleaned, _SEARCH_TERMS) else "tool",
                "role": "tool",
                "importance": "primary",
                "source_refs": ["input-brief"],
            }
        )
    if has_safety:
        entities.append(
            {
                "id": "guardrail",
                "label": labels["guardrail"],
                "description": "验证策略与约束" if is_chinese else "validate policy and constraints",
                "kind": "shield",
                "role": "risk",
                "importance": "supporting",
                "source_refs": ["input-brief"],
            }
        )
    entities.append(
        {
            "id": "output",
            "label": labels["output"],
            "description": "交付经过校验的结果" if is_chinese else "deliver the checked result",
            "kind": "output",
            "role": "output",
            "importance": "primary",
            "state": {"result": "verified"},
            "source_refs": ["input-brief"],
        }
    )

    relations: List[Dict[str, Any]] = []

    def add_relation(relation_id: str, source: str, target: str, kind: str, label: str, importance: str) -> str:
        relations.append(
            {
                "id": relation_id,
                "from": source,
                "to": target,
                "kind": kind,
                "label": label,
                "direction": "forward",
                "importance": importance,
                "source_refs": ["input-brief"],
            }
        )
        return relation_id

    relation_labels = {
        "request": "处理请求" if is_chinese else "request",
        "read_context": "读取上下文" if is_chinese else "read context",
        "return_context": "返回上下文" if is_chinese else "context",
        "dispatch": "调用工具" if is_chinese else "dispatch",
        "validate": "执行校验" if is_chinese else "validate",
        "result": "输出结果" if is_chinese else "verified result",
        "retry": "失败重试" if is_chinese else "retry",
    }
    primary_relations = [
        add_relation("request-agent", "request", "agent", "request", relation_labels["request"], "primary")
    ]
    if has_memory:
        primary_relations.extend(
            [
                add_relation("agent-memory", "agent", "memory", "context-read", relation_labels["read_context"], "supporting"),
                add_relation("memory-agent", "memory", "agent", "context-return", relation_labels["return_context"], "supporting"),
            ]
        )
    previous = "agent"
    if has_tools:
        primary_relations.append(
            add_relation("agent-tool", "agent", "tool", "tool-call", relation_labels["dispatch"], "primary")
        )
        previous = "tool"
    if has_safety:
        primary_relations.append(
            add_relation("result-guardrail", previous, "guardrail", "validation", relation_labels["validate"], "supporting")
        )
        previous = "guardrail"
    primary_relations.append(
        add_relation("result-output", previous, "output", "result", relation_labels["result"], "primary")
    )

    flows: List[Dict[str, Any]] = [
        {
            "id": "primary-flow",
            "label": "主请求流程" if is_chinese else "Primary request flow",
            "description": "根据输入需求提取的有序执行流程。" if is_chinese else "Ordered execution extracted directly from the brief.",
            "relation_ids": primary_relations,
            "importance": "primary",
            "repeat": "event-driven",
            "source_refs": ["input-brief"],
        }
    ]
    if has_loop:
        feedback_relation = add_relation(
            "output-feedback", "output", "agent", "feedback", relation_labels["retry"], "supporting"
        )
        flows.append(
            {
                "id": "feedback-loop",
                "label": "反馈重试循环" if is_chinese else "Feedback loop",
                "relation_ids": [feedback_relation],
                "importance": "supporting",
                "repeat": "loop",
                "source_refs": ["input-brief"],
            }
        )
    presentation = {
        "icon_system": "auto",
        "style": style or "auto",
        "layout": "auto",
        "motion": "showcase-v1",
    }
    return {
        "version": "0.2",
        "semantic": {
            "language": resolved_language,
            "title": plan_title,
            "subtitle": "由自然语言需求生成的语义优先架构图。" if is_chinese else "Semantic-first brief compiled with composition-v1.",
            "summary": summary,
            "intent": {
                "diagram_kind": "workflow",
                "primary_question": summary or plan_title,
                "audience": ["技术团队"] if is_chinese else ["technical"],
                "scope": "需求中明确或隐含的实体、关系、状态与执行流程。" if is_chinese else "Entities, relations, state, and execution flows stated or implied by the brief.",
                "exclusions": [],
            },
            "entities": entities,
            "relations": relations,
            "flows": flows,
            "sources": [
                {
                    "id": "input-brief",
                    "type": "brief",
                    "title": "输入需求" if is_chinese else "Input brief",
                    "note": summary,
                }
            ],
        },
        "presentation": presentation,
    }


def _semantic_kind(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")
    return normalized or "component"


def compile_plan(plan: Mapping[str, Any]) -> SpecDict:
    """Compile a supported DiagramPlan into resolved DiagramScript."""

    if plan.get("version") == "0.2":
        return compile_plan_v02(plan)

    if plan.get("version") != "0.1":
        raise ValueError("DiagramPlan version must be '0.1' or '0.2'")
    layout_strategy = str(plan.get("layout_strategy") or "explainer-board")
    if layout_strategy != "explainer-board":
        raise ValueError("only the 'explainer-board' layout_strategy is currently supported")

    inputs = _items(plan.get("inputs"), _default_inputs())
    main_flow = _items(plan.get("main_flow"), _default_main_flow())
    support_panels = _panels(plan.get("support_panels"), _default_support_panels())
    spec: SpecDict = {
        "version": "0.3",
        "preset": "brief-explainer",
        "canvas": {"width": 1280, "height": 960},
        "style": str(plan.get("style") or "sketch-board"),
        "title": {
            "text": str(plan.get("title") or "Brief to Diagram"),
            "subtitle": str(plan.get("subtitle") or "Compiled from DiagramPlan v0.1."),
        },
        "motion": {
            "profile": str(plan.get("motion_profile") or "teaching"),
            "sequence": "staged",
            "ease": "spring",
            "stagger": 0.13,
            "duration_scale": 0.92,
            "intensity": 0.92,
            "edge": {"preset": "draw"},
            "node": {"preset": "fade"},
            "group": {"preset": "soft-reveal"},
            "title": {"preset": "fade"},
            "reduced_motion": "subtle",
        },
        "motion_policy": deepcopy(plan.get("motion_policy"))
        if isinstance(plan.get("motion_policy"), Mapping)
        else _default_motion_policy(),
        "groups": _compile_groups(plan),
        "nodes": [],
        "edges": [],
    }
    spec["nodes"].extend(_compile_input_nodes(inputs))
    spec["nodes"].extend(_compile_main_nodes(main_flow))
    spec["nodes"].extend(_compile_support_nodes(support_panels))
    spec["edges"].extend(_compile_core_edges())
    spec["edges"].extend(_compile_feedback_edges(plan.get("feedback_paths")))
    node_ids = {str(node["id"]) for node in spec["nodes"]}
    spec["edges"] = [
        edge for edge in spec["edges"] if str(edge.get("from")) in node_ids and str(edge.get("to")) in node_ids
    ]
    return spec


def brief_to_diagram_script(
    brief: str,
    title: str = "",
    style: str = "sketch-board",
    language: str = "auto",
) -> SpecDict:
    """Convenience helper for callers that do not need the intermediate plan."""

    return compile_plan(brief_to_plan(brief, title=title, style=style, language=language))


def _keywords(text: str) -> List[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower())
    seen = set()
    result = []
    for word in words:
        normalized = word.strip("_-")
        if normalized in _STOP_WORDS or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
        if len(result) >= 6:
            break
    return result


def _contains(text: str, needles: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


def _contains_cjk(text: str) -> bool:
    return contains_cjk(text)


def _title_from_brief(text: str, keywords: List[str], language: str = "auto") -> str:
    if not text:
        return "中文架构图" if language == "zh-CN" else "Brief to Diagram Flow"
    if language == "zh-CN" or _contains_cjk(text):
        candidate = re.split(r"[：:，,。！？；;\n]", text.strip(), maxsplit=1)[0].strip()
        candidate = re.sub(r"^(?:请(?:帮我)?|帮我|构建|绘制|生成|创建|设计|输出|展示)", "", candidate).strip()
        return candidate[:28].rstrip() or "中文架构图"
    sentence = re.split(r"[.!?\n]", text.strip(), maxsplit=1)[0]
    sentence = sentence.strip()
    if 8 <= len(sentence) <= 52:
        return sentence[0].upper() + sentence[1:]
    if keywords:
        return " ".join(word.capitalize() for word in keywords[:4]) + " Flow"
    return "Brief to Diagram Flow"


def _caption(default: str, keywords: List[str], offset: int) -> str:
    if offset < len(keywords):
        return f"{default}: {keywords[offset]}"
    return default


def _source_summary(text: str) -> str:
    if len(text) <= 180:
        return text
    return text[:177].rstrip() + "..."


def _emphasis(has_loop: bool, has_memory: bool, has_tools: bool, has_safety: bool) -> List[str]:
    emphasis = []
    if has_loop:
        emphasis.append("visible feedback loop")
    if has_memory:
        emphasis.append("memory/context side panel")
    if has_tools:
        emphasis.append("tool call dispatch and result return")
    if has_safety:
        emphasis.append("guardrail validation path")
    return emphasis or ["brief-to-plan structure", "freeform layout components"]


def _items(value: Any, fallback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if isinstance(value, list) and value:
        return [dict(item) for item in value if isinstance(item, Mapping)]
    return deepcopy(fallback)


def _panels(value: Any, fallback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    panels = _items(value, fallback)
    return panels[:3] if len(panels) >= 3 else panels + deepcopy(fallback[len(panels):3])


def _compile_groups(plan: Mapping[str, Any]) -> List[Dict[str, Any]]:
    sections = {str(section.get("id", "")): section for section in _items(plan.get("sections"), [])}
    return [
        _group("inputs", sections, "Inputs", [390, 140, 500, 120], "source"),
        _group("core", sections, "Agent Work Loop", [55, 305, 1170, 315], "agent"),
        _group("memory", sections, "Memory", [45, 685, 300, 230], "memory"),
        _group("guardrails", sections, "Guardrails", [370, 685, 540, 230], "risk"),
        _group("tools", sections, "Tooling", [955, 685, 270, 230], "tool"),
    ]


def _group(group_id: str, sections: Mapping[str, Mapping[str, Any]], label: str, bounds: List[int], role: str) -> Dict[str, Any]:
    section = sections.get(group_id, {})
    return {
        "id": group_id,
        "label": str(section.get("label") or label),
        "bounds": bounds,
        "role": str(section.get("role") or role),
        "effect": {"preset": "soft-reveal"},
    }


def _compile_input_nodes(inputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    positions = [(420, 175), (540, 175), (660, 175), (780, 175)]
    nodes = []
    for item, position in zip((inputs + _default_inputs())[:4], positions):
        nodes.append(_node(item, position, (90, 66), item.get("id", "input"), step=None))
    return nodes


def _compile_main_nodes(main_flow: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    defaults = _default_main_flow()
    items = (main_flow + defaults)[:6]
    geometry = [
        ((95, 370), (190, 92)),
        ((360, 370), (190, 92)),
        ((625, 370), (190, 92)),
        ((890, 370), (190, 92)),
        ((600, 500), (170, 110)),
        ((1025, 500), (140, 92)),
    ]
    nodes = []
    for index, (item, (position, size)) in enumerate(zip(items, geometry), start=1):
        nodes.append(_node(item, position, size, item.get("id", f"step-{index}"), step=index))
    return nodes


def _compile_support_nodes(panels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    slots = {
        "memory": [((75, 755), (240, 66)), ((75, 835), (240, 66))],
        "guardrails": [((400, 755), (210, 66)), ((655, 755), (210, 66)), ((400, 835), (210, 66)), ((655, 835), (210, 66))],
        "tools": [((985, 755), (210, 66)), ((985, 835), (210, 66))],
    }
    nodes = []
    for panel, fallback in zip(panels[:3], _default_support_panels()):
        panel_id = str(panel.get("id") or fallback["id"])
        panel_slots = slots.get(panel_id, slots[fallback["id"]])
        items = _items(panel.get("items"), fallback["items"])
        for item, (position, size) in zip((items + fallback["items"])[: len(panel_slots)], panel_slots):
            nodes.append(_node(item, position, size, item.get("id", "panel-item"), step=None))
    return nodes


def _node(item: Mapping[str, Any], position: tuple[int, int], size: tuple[int, int], fallback_id: Any, step: Optional[int]) -> Dict[str, Any]:
    node = {
        "id": str(item.get("id") or fallback_id),
        "label": str(item.get("label") or fallback_id).strip()[:28],
        "caption": str(item.get("caption") or "").strip()[:44],
        "position": [position[0], position[1]],
        "size": [size[0], size[1]],
        "role": str(item.get("role") or "neutral"),
        "effect": item.get("effect") if isinstance(item.get("effect"), Mapping) else {"preset": "fade"},
    }
    if item.get("shape"):
        node["shape"] = str(item["shape"])
    if item.get("icon"):
        node["icon"] = str(item["icon"])
    if step is not None:
        node["step"] = step
    return node


def _compile_core_edges() -> List[Dict[str, Any]]:
    return [
        {"from": "brief", "to": "clarify", "label": "request", "role": "source", "route": "points", "points": [[465, 241], [465, 278], [190, 278], [190, 370]], "effect": {"preset": "draw"}},
        {"from": "context", "to": "clarify", "label": "context", "role": "memory", "route": "points", "points": [[585, 241], [585, 292], [250, 292], [250, 370]], "effect": {"preset": "draw"}},
        {"from": "clarify", "to": "plan", "label": "intent", "role": "agent", "route": "straight", "effect": {"preset": "packet-flow", "particle_count": 1}},
        {"from": "plan", "to": "act", "label": "steps", "role": "process", "route": "straight", "effect": {"preset": "draw"}},
        {"from": "act", "to": "observe", "label": "execute", "role": "tool", "route": "straight", "effect": {"preset": "packet-flow", "particle_count": 1}},
        {"from": "observe", "to": "done", "label": "evidence", "role": "process", "route": "vh", "effect": {"preset": "draw"}},
        {"from": "done", "to": "output", "label": "Yes", "role": "output", "route": "straight", "effect": {"preset": "packet-flow", "particle_count": 1}},
        {"from": "policy", "to": "done", "label": "rules", "role": "risk", "route": "points", "points": [[825, 241], [825, 278], [685, 278], [685, 500]], "effect": {"preset": "draw"}},
    ]


def _default_motion_policy() -> Dict[str, Any]:
    return {
        "profile": "focused",
        "max_active_flow_edges": 4,
        "max_particle_edges": 3,
        "particle_count_per_edge": 1,
        "flow_trail_count": 1,
        "max_active_pulse_nodes": 1,
        "pulse_mode": "rotate",
        "max_scanning_groups": 1,
    }


def _compile_feedback_edges(feedback_paths: Any) -> List[Dict[str, Any]]:
    configured = _items(feedback_paths, [])
    edge_overrides = {
        ("done", "plan"): {"route": "points", "points": [[685, 610], [685, 650], [300, 650], [300, 416], [360, 416]], "effect": {"preset": "stream-flow"}},
        ("working-memory", "plan"): {"route": "points", "points": [[315, 788], [330, 650], [455, 650], [455, 462]], "effect": {"preset": "draw"}},
        ("act", "tool-calls"): {"route": "points", "points": [[815, 416], [850, 650], [935, 650], [935, 788], [985, 788]], "effect": {"preset": "draw"}},
        ("tool-results", "observe"): {"route": "points", "points": [[985, 868], [930, 868], [930, 462]], "effect": {"preset": "draw"}},
        ("validate", "act"): {"route": "points", "points": [[505, 755], [505, 650], [720, 650], [720, 462]], "effect": {"preset": "draw"}},
        ("budget", "replan"): {"route": "straight", "effect": {"preset": "draw"}},
    }
    edges = []
    seen = set()
    for item in configured:
        source = str(item.get("from") or "")
        target = str(item.get("to") or "")
        if not source or not target:
            continue
        key = (source, target)
        seen.add(key)
        edge = {"from": source, "to": target, "label": str(item.get("label") or ""), "role": str(item.get("role") or "neutral")}
        edge.update(deepcopy(edge_overrides.get(key, {"route": "orthogonal", "effect": {"preset": "draw"}})))
        edges.append(edge)
    for key in (("validate", "act"), ("budget", "replan")):
        if key in seen:
            continue
        edge = {"from": key[0], "to": key[1], "label": "guard", "role": "risk"}
        edge.update(deepcopy(edge_overrides[key]))
        edges.append(edge)
    return edges


def _default_inputs() -> List[Dict[str, Any]]:
    return [
        {"id": "brief", "label": "Brief", "caption": "request", "role": "source", "icon": "file"},
        {"id": "context", "label": "Context", "caption": "docs", "role": "memory", "icon": "memory"},
        {"id": "events", "label": "Events", "caption": "signals", "role": "source", "icon": "api"},
        {"id": "policy", "label": "Policy", "caption": "rules", "role": "risk", "icon": "shield"},
    ]


def _default_main_flow() -> List[Dict[str, Any]]:
    return [
        {"id": "clarify", "label": "Clarify", "caption": "goal and limits", "role": "agent", "icon": "search"},
        {"id": "plan", "label": "Plan", "caption": "steps and layout", "role": "process", "icon": "agent"},
        {"id": "act", "label": "Act", "caption": "tools and edits", "role": "tool", "icon": "tool"},
        {"id": "observe", "label": "Observe", "caption": "check evidence", "role": "process", "icon": "search"},
        {"id": "done", "label": "Done?", "caption": "quality gate", "role": "risk", "shape": "decision", "icon": "shield"},
        {"id": "output", "label": "Output", "caption": "verified result", "role": "output", "icon": "output"},
    ]


def _default_support_panels() -> List[Dict[str, Any]]:
    return [
        {
            "id": "memory",
            "items": [
                {"id": "working-memory", "label": "Working Memory", "caption": "current task state", "role": "memory", "icon": "memory"},
                {"id": "long-term-notes", "label": "Long-Term Notes", "caption": "prior decisions", "role": "memory", "icon": "database"},
            ],
        },
        {
            "id": "guardrails",
            "items": [
                {"id": "validate", "label": "Validate", "caption": "schema and tests", "role": "risk", "icon": "shield"},
                {"id": "scope", "label": "Scope", "caption": "stay in bounds", "role": "neutral", "icon": "file"},
                {"id": "budget", "label": "Budget", "caption": "time and tokens", "role": "neutral", "icon": "token"},
                {"id": "replan", "label": "Replan", "caption": "fix failures", "role": "process", "icon": "agent"},
            ],
        },
        {
            "id": "tools",
            "items": [
                {"id": "tool-calls", "label": "Tool Calls", "caption": "search render test", "role": "tool", "icon": "tool"},
                {"id": "tool-results", "label": "Tool Results", "caption": "logs and files", "role": "output", "icon": "folder"},
            ],
        },
    ]
