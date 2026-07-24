"""Approved convention-aligned definitions plus their archived review context.

The reference metadata and baseline helpers preserve the human-review proof.
The aligned definitions themselves are public in Illustrated 2.5.0.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .illustrated_character_icons import CharacterIconDefinition, CharacterPrimitive
from .illustrated_character_v2_icons import character_v2_definition
from .illustrated_expansion_batch_1 import expansion_batch_1_definition
from .illustrated_expansion_batch_4 import expansion_batch_4_definition
from .illustrated_expansion_batches_6_10 import expansion_6_10_definition


ALIGNMENT_GROUPS = {
    "p1-industry-anchor": {
        "label": "P1 · Industry Anchor",
        "icons": ("token", "document-store", "webhook", "pull-request"),
    },
    "p2-semantic-alignment": {
        "label": "P2 · Semantic Alignment",
        "icons": (
            "output",
            "memory",
            "gateway",
            "data-warehouse",
            "git-repository",
            "branch",
            "ci-cd",
            "deployment",
        ),
    },
}

ALIGNMENT_REFERENCE_ANCHORS = {
    "token": {
        "title": "Tokenizer segments",
        "note": "从字词切分到 token 片段与预算轨道，不再使用硬币符号。",
        "references": (
            {"provider": "Google Material Symbols", "title": "Token", "url": "https://fonts.google.com/icons?icon.query=token"},
        ),
    },
    "document-store": {
        "title": "Database + document",
        "note": "用数据库圆柱承载文档卡片，区别于普通文件柜。",
        "references": (
            {"provider": "Lucide", "title": "Database", "url": "https://lucide.dev/icons/database"},
            {"provider": "Lucide", "title": "File Text", "url": "https://lucide.dev/icons/file-text"},
        ),
    },
    "webhook": {
        "title": "Event callback",
        "note": "采用事件、处理器、结果三节点回调闭环，避免字面化鱼钩。",
        "references": (
            {"provider": "Lucide", "title": "Webhook", "url": "https://lucide.dev/icons/webhook"},
        ),
    },
    "pull-request": {
        "title": "Git pull request",
        "note": "保留三节点拓扑和变更请求方向这两个标准识别点。",
        "references": (
            {"provider": "Primer Octicons", "title": "Git Pull Request", "url": "https://primer.style/octicons/icon/git-pull-request-16/"},
        ),
    },
    "output": {
        "title": "Delivered artifact",
        "note": "文件从交付托盘显露，不再依赖勾选徽章表示完成。",
        "references": (
            {"provider": "Lucide", "title": "File Output", "url": "https://lucide.dev/icons/file-output"},
        ),
    },
    "memory": {
        "title": "Indexed context + recall",
        "note": "卡片堆栈承载上下文索引，外部回忆轨道表达召回。",
        "references": (
            {"provider": "Lucide", "title": "Brain Circuit", "url": "https://lucide.dev/icons/brain-circuit"},
        ),
    },
    "gateway": {
        "title": "Network boundary",
        "note": "用边界设备、策略核心和双向流量通道替代建筑拱门。",
        "references": (
            {"provider": "Lucide", "title": "Router", "url": "https://lucide.dev/icons/router"},
        ),
    },
    "data-warehouse": {
        "title": "Warehouse + database",
        "note": "仓库轮廓提供业务隐喻，内部数据库圆柱提供技术锚点。",
        "references": (
            {"provider": "Lucide", "title": "Warehouse", "url": "https://lucide.dev/icons/warehouse"},
            {"provider": "Lucide", "title": "Database", "url": "https://lucide.dev/icons/database"},
        ),
    },
    "git-repository": {
        "title": "Repository + Git graph",
        "note": "文件夹语义保留，内部强化主线、分支和提交节点。",
        "references": (
            {"provider": "Lucide", "title": "Folder Git 2", "url": "https://lucide.dev/icons/folder-git-2"},
        ),
    },
    "branch": {
        "title": "Git branch graph",
        "note": "去除卡片外壳，让主线、分叉和提交节点成为绝对主体。",
        "references": (
            {"provider": "Primer Octicons", "title": "Git Branch", "url": "https://primer.style/octicons/icon/git-branch-16/"},
        ),
    },
    "ci-cd": {
        "title": "Continuous delivery loop",
        "note": "无限循环与三个阶段节点表达持续集成和持续交付。",
        "references": (
            {"provider": "Lucide", "title": "Infinity", "url": "https://lucide.dev/icons/infinity"},
        ),
    },
    "deployment": {
        "title": "Package into environment",
        "note": "发布包落入明确的服务器环境坞，不再是抽象平台。",
        "references": (
            {"provider": "Lucide", "title": "Package Open", "url": "https://lucide.dev/icons/package-open"},
            {"provider": "Lucide", "title": "Server Cog", "url": "https://lucide.dev/icons/server-cog"},
        ),
    },
}

_OFFICIAL_REFERENCE_URLS = tuple(
    dict.fromkeys(
        reference["url"]
        for anchor in ALIGNMENT_REFERENCE_ANCHORS.values()
        for reference in anchor["references"]
    )
)

CONVENTION_ALIGNMENT_METADATA = {
    "status": "approved",
    "target_version": "2.5.0",
    "public_registry_changed": True,
    "motion_contract_changed": True,
    "scope": "twelve approved convention-alignment definitions",
    "official_references": _OFFICIAL_REFERENCE_URLS,
    "reference_coverage": len(ALIGNMENT_REFERENCE_ANCHORS),
}


def _p(kind: str, part: str, **attrs: str) -> CharacterPrimitive:
    return CharacterPrimitive(kind=kind, part=part, attrs=attrs)


def _icon(icon: str, role: str, parts: tuple[str, ...], primitives: tuple[CharacterPrimitive, ...]) -> CharacterIconDefinition:
    return CharacterIconDefinition(icon=icon, semantic_role=role, parts=("root",) + parts, primitives=primitives)


ILLUSTRATED_CONVENTION_ALIGNMENT_DEFINITIONS: Dict[str, CharacterIconDefinition] = {
    "token": _icon(
        "token",
        "tokenize-count-budget-consume",
        ("wash", "tokenizer-shell", "context-strip", "token-segments", "segment-glyphs", "budget-rail", "budget-slots"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p("rect", "tokenizer-shell", x="14", y="23", width="92", height="74", rx="18", fill="paper", stroke="ink"),
            _p("path", "context-strip", d="M15 41h90V31c0-4-3-8-8-8H23c-5 0-8 4-8 8Z", fill="lavender", stroke="ink", stroke_width="2.8"),
            _p("path", "token-segments", d="M25 54h23v18H25Zm27 0h17v18H52Zm21 0h22v18H73Z", fill="mint", stroke="ink", stroke_width="2.4"),
            _p("path", "segment-glyphs", d="M31 63h11M57 63h7M79 63h10", fill="none", stroke="teal-dark", stroke_width="2.6"),
            _p("path", "budget-rail", d="M26 84h68", fill="none", stroke="lavender-dark", stroke_width="5"),
            _p("path", "budget-slots", d="M35 84h0m17 0h0m17 0h0m17 0h0", fill="none", stroke="coral", stroke_width="7"),
        ),
    ),
    "document-store": _icon(
        "document-store",
        "documents-ingest-index-retrieve",
        ("wash", "store-body", "store-top", "document-card", "document-corner", "record-lines", "index-points"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("path", "store-body", d="M19 39c0-10 18-18 41-18s41 8 41 18v48c0 10-18 18-41 18S19 97 19 87Z", fill="teal", stroke="ink"),
            _p("ellipse", "store-top", cx="60", cy="39", rx="41", ry="18", fill="paper", stroke="ink"),
            _p("path", "document-card", d="M46 45h27l13 13v36H46Z", fill="paper", stroke="ink", stroke_width="2.8"),
            _p("path", "document-corner", d="M73 45v14h13", fill="lavender", stroke="ink", stroke_width="2.4"),
            _p("path", "record-lines", d="M55 68h21M55 78h21M55 88h14", fill="none", stroke="violet", stroke_width="2.6"),
            _p("path", "index-points", d="M29 65h0m0 17h0", fill="none", stroke="sun", stroke_width="7"),
        ),
    ),
    "webhook": _icon(
        "webhook",
        "event-hook-receive-trigger",
        ("wash", "callback-field", "callback-arcs", "event-node", "handler-node", "result-node", "event-pulse"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("circle", "callback-field", cx="60", cy="60", r="43", fill="paper", stroke="ink"),
            _p("path", "callback-arcs", d="M37 43c9-15 33-19 47-4M88 49c8 17-1 38-18 45M58 96c-18 1-33-15-32-32", fill="none", stroke="violet", stroke_width="5"),
            _p("circle", "event-node", cx="34", cy="49", r="10", fill="coral", stroke="ink", stroke_width="2.8"),
            _p("circle", "handler-node", cx="88", cy="43", r="10", fill="sun", stroke="ink", stroke_width="2.8"),
            _p("circle", "result-node", cx="65", cy="94", r="10", fill="mint", stroke="ink", stroke_width="2.8"),
            _p("path", "event-pulse", d="M34 44v6l5 3", fill="none", stroke="paper", stroke_width="2.6"),
        ),
    ),
    "pull-request": _icon(
        "pull-request",
        "changes-propose-review-merge",
        ("wash", "source-rail", "request-path", "source-nodes", "target-node", "request-tip"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p("path", "source-rail", d="M34 28v64", fill="none", stroke="teal-dark", stroke_width="5"),
            _p("path", "request-path", d="M61 32h7c10 0 18 8 18 18v42", fill="none", stroke="violet", stroke_width="5"),
            _p("path", "source-nodes", d="M34 28h0m0 64h0", fill="none", stroke="mint", stroke_width="13"),
            _p("circle", "target-node", cx="86", cy="92", r="6.5", fill="sun", stroke="ink", stroke_width="3"),
            _p("path", "request-tip", d="m52 23 9 9-9 9", fill="none", stroke="coral", stroke_width="4"),
        ),
    ),
    "output": _icon(
        "output",
        "artifact-deliver-confirm",
        ("wash", "artifact-card", "artifact-corner", "artifact-lines", "emergence-track", "delivery-tray", "delivery-lip"),
        (
            _p("circle", "wash", cx="58", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("path", "artifact-card", d="M33 14h36l16 16v51H33Z", fill="paper", stroke="ink"),
            _p("path", "artifact-corner", d="M69 14v17h16", fill="lavender", stroke="ink", stroke_width="2.8"),
            _p("path", "artifact-lines", d="M44 43h29M44 55h29M44 67h20", fill="none", stroke="violet", stroke_width="3"),
            _p("path", "emergence-track", d="M59 79v17", fill="none", stroke="teal-dark", stroke_width="4"),
            _p("path", "delivery-tray", d="M13 75h29l8 10h18l8-10h29l-6 29H19Z", fill="sky", stroke="ink"),
            _p("path", "delivery-lip", d="M19 96h80M42 75l8 10h18l8-10", fill="none", stroke="ink", stroke_width="3"),
        ),
    ),
    "memory": _icon(
        "memory",
        "context-capture-index-recall",
        ("wash", "context-stack", "context-card", "context-nodes", "context-links", "recall-orbit", "recall-focus"),
        (
            _p("circle", "wash", cx="59", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("path", "context-stack", d="M19 31h66v65H19Zm7-8h66v65", fill="lavender", stroke="ink", stroke_width="2.8"),
            _p("rect", "context-card", x="33", y="16", width="66", height="65", rx="12", fill="paper", stroke="ink"),
            _p("path", "context-nodes", d="M49 39h0m18 12h0m17-15h0m-25 28h0", fill="none", stroke="teal-dark", stroke_width="9"),
            _p("path", "context-links", d="M49 39 67 51m0 0 17-15M67 51l-8 13", fill="none", stroke="violet", stroke_width="3"),
            _p("path", "recall-orbit", d="M46 91c9-10 26-11 37-2 6 5 8 11 7 18", fill="none", stroke="coral", stroke_width="4"),
            _p("circle", "recall-focus", cx="47", cy="91", r="7", fill="sun", stroke="ink", stroke_width="2.6"),
        ),
    ),
    "gateway": _icon(
        "gateway",
        "traffic-admit-route-mediate",
        ("wash", "boundary-appliance", "policy-core", "inbound-lanes", "outbound-lanes", "request-packets", "response-packets"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("rect", "boundary-appliance", x="35", y="15", width="50", height="91", rx="17", fill="paper", stroke="ink"),
            _p("path", "policy-core", d="M48 38h24v18H48Zm0 30h24v18H48Z", fill="lavender", stroke="ink", stroke_width="2.6"),
            _p("path", "inbound-lanes", d="M10 47h25M10 75h25", fill="none", stroke="teal-dark", stroke_width="4"),
            _p("path", "outbound-lanes", d="M85 47h25M85 75h25", fill="none", stroke="violet", stroke_width="4"),
            _p("path", "request-packets", d="M18 47h0m12 28h0", fill="none", stroke="coral", stroke_width="8"),
            _p("path", "response-packets", d="M91 47h0m12 28h0", fill="none", stroke="mint", stroke_width="8"),
        ),
    ),
    "data-warehouse": _icon(
        "data-warehouse",
        "data-land-organize-serve",
        ("wash", "warehouse-roof", "warehouse-body", "storage-cylinder", "storage-top", "storage-layers", "inventory-points"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p("path", "warehouse-roof", d="M12 44 60 16l48 28Z", fill="lavender", stroke="ink"),
            _p("path", "warehouse-body", d="M19 44h82v62H19Z", fill="paper", stroke="ink"),
            _p("path", "storage-cylinder", d="M34 62c0-6 12-11 26-11s26 5 26 11v29c0 7-12 12-26 12S34 98 34 91Z", fill="sky", stroke="ink", stroke_width="2.8"),
            _p("ellipse", "storage-top", cx="60", cy="62", rx="26", ry="11", fill="mint", stroke="ink", stroke_width="2.6"),
            _p("path", "storage-layers", d="M34 75c0 7 12 11 26 11s26-4 26-11M34 88c0 7 12 11 26 11s26-4 26-11", fill="none", stroke="violet", stroke_width="2.6"),
            _p("path", "inventory-points", d="M44 75h0m32 13h0", fill="none", stroke="coral", stroke_width="6"),
        ),
    ),
    "git-repository": _icon(
        "git-repository",
        "repository-store-version-share",
        ("wash", "repository-shell", "repository-tab", "git-main-rail", "git-branch-rail", "commit-nodes"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("path", "repository-shell", d="M13 35h35l9 10h50v61H13Z", fill="paper", stroke="ink"),
            _p("path", "repository-tab", d="M14 35h33l9 10H14Z", fill="lavender", stroke="ink", stroke_width="2.6"),
            _p("path", "git-main-rail", d="M42 58v34", fill="none", stroke="teal-dark", stroke_width="4"),
            _p("path", "git-branch-rail", d="M42 70c23 0 34 5 34 20V58", fill="none", stroke="violet", stroke_width="4"),
            _p("path", "commit-nodes", d="M42 58h0m0 34h0M76 58h0m0 34h0", fill="none", stroke="coral", stroke_width="10"),
        ),
    ),
    "branch": _icon(
        "branch",
        "branch-diverge-develop-rejoin",
        ("wash", "main-rail", "branch-rail", "main-nodes", "branch-nodes", "branch-focus"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("path", "main-rail", d="M39 20v80", fill="none", stroke="teal-dark", stroke_width="5"),
            _p("path", "branch-rail", d="M39 45c28 0 42 10 42 31v24", fill="none", stroke="violet", stroke_width="5"),
            _p("path", "main-nodes", d="M39 20h0m0 25h0m0 55h0", fill="none", stroke="mint", stroke_width="14"),
            _p("path", "branch-nodes", d="M81 76h0m0 24h0", fill="none", stroke="coral", stroke_width="14"),
            _p("circle", "branch-focus", cx="39", cy="45", r="11", fill="sun", stroke="ink", stroke_width="3"),
        ),
    ),
    "ci-cd": _icon(
        "ci-cd",
        "change-build-test-deliver",
        ("wash", "delivery-loop", "source-stage", "build-stage", "release-stage", "stage-cores"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("path", "delivery-loop", d="M18 61c0-19 22-31 38-15l8 8 8-8c16-16 38-4 38 15s-22 31-38 15l-8-8-8 8C40 92 18 80 18 61Z", fill="none", stroke="violet", stroke_width="6"),
            _p("circle", "source-stage", cx="27", cy="61", r="10", fill="lavender", stroke="ink", stroke_width="2.7"),
            _p("circle", "build-stage", cx="64", cy="61", r="10", fill="sun", stroke="ink", stroke_width="2.7"),
            _p("circle", "release-stage", cx="101", cy="61", r="10", fill="mint", stroke="ink", stroke_width="2.7"),
            _p("path", "stage-cores", d="M27 61h0m37 0h0m37 0h0", fill="none", stroke="coral", stroke_width="5"),
        ),
    ),
    "deployment": _icon(
        "deployment",
        "artifact-release-place-activate",
        ("wash", "release-package", "package-seam", "placement-track", "environment-dock", "server-bays", "runtime-lights"),
        (
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("path", "release-package", d="M38 16h44v35H38Zm0 0 22 12 22-12M60 28v23", fill="lavender", stroke="ink", stroke_width="2.8"),
            _p("path", "package-seam", d="M47 36h26", fill="none", stroke="violet", stroke_width="2.7"),
            _p("path", "placement-track", d="M60 51v17", fill="none", stroke="teal-dark", stroke_width="5"),
            _p("rect", "environment-dock", x="18", y="67", width="84", height="39", rx="12", fill="paper", stroke="ink"),
            _p("path", "server-bays", d="M29 78h26v17H29Zm36 0h26v17H65Z", fill="sky", stroke="ink", stroke_width="2.5"),
            _p("path", "runtime-lights", d="M37 86h0m11 0h0m25 0h0m11 0h0", fill="none", stroke="coral", stroke_width="5.5"),
        ),
    ),
}


def current_alignment_definition(icon: str) -> CharacterIconDefinition | None:
    """Return the pre-alignment baseline retained for review comparison."""

    public = (
        character_v2_definition(icon)
        or expansion_batch_1_definition(icon)
        or expansion_batch_4_definition(icon)
    )
    return public or expansion_6_10_definition(icon)


def current_alignment_status(icon: str) -> str | None:
    """Distinguish the 2.4 public baseline from accepted expansion baselines."""

    if (
        character_v2_definition(icon)
        or expansion_batch_1_definition(icon)
        or expansion_batch_4_definition(icon)
    ) is not None:
        return "public"
    if expansion_6_10_definition(icon) is not None:
        return "accepted-candidate"
    return None


def convention_alignment_definition(icon: str) -> CharacterIconDefinition | None:
    return ILLUSTRATED_CONVENTION_ALIGNMENT_DEFINITIONS.get(icon)


def convention_alignment_icon_ids() -> Tuple[str, ...]:
    return tuple(ILLUSTRATED_CONVENTION_ALIGNMENT_DEFINITIONS)


# Compatibility alias for the archived comparison renderer and review records.
ILLUSTRATED_CONVENTION_ALIGNMENT_CANDIDATES = ILLUSTRATED_CONVENTION_ALIGNMENT_DEFINITIONS
