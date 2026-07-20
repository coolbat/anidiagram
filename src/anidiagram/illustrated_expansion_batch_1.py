"""Approved Illustrated 2.1.0 expansion slice.

These four assets passed human static review at 64, 96, and 120 pixels and are
the approved coverage slice promoted into Illustrated 2.1.0. Their semantic
motion performances are approved by the public ``illustrated-performance-v2``
contract.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .illustrated_character_icons import CharacterIconDefinition, CharacterPrimitive


ILLUSTRATED_EXPANSION_BATCH_1_METADATA = {
    "batch": "illustrated-expansion-batch-1",
    "status": "approved",
    "human_visual_acceptance": "confirmed",
    "static_approved_at": "2026-07-20",
    "target_version": "2.1.0",
    "public_registry_changed": True,
    "motion_status": "approved",
    "motion_human_acceptance": "confirmed",
    "motion_approved_at": "2026-07-20",
    "icons": ("database", "api", "search", "memory"),
    "accessory_policy": {
        "check_reserved_for": ("human-confirmation", "final-acceptance"),
        "default": "integrated-semantic-cue",
        "decoration_only_accessories": False,
    },
}


def _p(kind: str, part: str, **attrs: str) -> CharacterPrimitive:
    return CharacterPrimitive(kind=kind, part=part, attrs=attrs)


ILLUSTRATED_EXPANSION_BATCH_1: Dict[str, CharacterIconDefinition] = {
    "database": CharacterIconDefinition(
        icon="database",
        semantic_role="data-ingest-store-persist",
        parts=(
            "root",
            "wash",
            "cylinder-body",
            "cylinder-top",
            "layer-top",
            "layer-bottom",
            "input-bead",
            "write-path",
            "commit-ripple",
            "stored-bead",
        ),
        primitives=(
            _p("circle", "wash", cx="59", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("path", "cylinder-body", d="M25 37v50c0 9 16 16 35 16s35-7 35-16V37Z", fill="sky", stroke="ink"),
            _p("ellipse", "cylinder-top", cx="60", cy="37", rx="35", ry="14", fill="lavender", stroke="ink"),
            _p("path", "layer-top", d="M25 58c0 9 16 16 35 16s35-7 35-16", fill="none", stroke="ink", stroke_width="3"),
            _p("path", "layer-bottom", d="M25 78c0 9 16 16 35 16s35-7 35-16", fill="none", stroke="ink", stroke_width="3"),
            _p("circle", "input-bead", cx="14", cy="23", r="6", fill="coral", stroke="ink", stroke_width="2.6"),
            _p("path", "write-path", d="M20 25c11-4 17 0 24 8m-7-1 7 1-3-7", fill="none", stroke="violet", stroke_width="3"),
            _p("ellipse", "commit-ripple", cx="60", cy="85", rx="13", ry="5", fill="none", stroke="teal", stroke_width="2.5"),
            _p("circle", "stored-bead", cx="60", cy="84", r="4.5", fill="mint", stroke="ink", stroke_width="2.2"),
        ),
    ),
    "api": CharacterIconDefinition(
        icon="api",
        semantic_role="request-route-response",
        parts=(
            "root",
            "wash",
            "gateway",
            "api-glyph",
            "request-path",
            "request-token",
            "response-path",
            "response-token",
        ),
        primitives=(
            _p("circle", "wash", cx="59", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("rect", "gateway", x="30", y="24", width="60", height="72", rx="16", fill="paper", stroke="ink"),
            _p("path", "api-glyph", d="M51 44 42 60l9 16m18-32 9 16-9 16M63 40l-7 40", fill="none", stroke="violet", stroke_width="3.4"),
            _p("path", "request-path", d="M10 45h27m-8-7 8 7-8 7", fill="none", stroke="teal", stroke_width="3"),
            _p("circle", "request-token", cx="12", cy="45", r="5", fill="coral", stroke="ink", stroke_width="2.4"),
            _p("path", "response-path", d="M110 76H83m8-7-8 7 8 7", fill="none", stroke="lavender-dark", stroke_width="3"),
            _p("circle", "response-token", cx="108", cy="76", r="5", fill="sun", stroke="ink", stroke_width="2.4"),
        ),
    ),
    "search": CharacterIconDefinition(
        icon="search",
        semantic_role="query-scan-discover",
        parts=(
            "root",
            "wash",
            "lens-glass",
            "lens",
            "handle",
            "scan-cross",
            "target-ring",
            "result-dot",
            "discovery",
        ),
        primitives=(
            _p("circle", "wash", cx="58", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("circle", "lens-glass", cx="49", cy="48", r="29", fill="paper", stroke="none"),
            _p("circle", "lens", cx="49", cy="48", r="30", fill="none", stroke="ink", stroke_width="5"),
            _p("path", "handle", d="M70 69l29 29", fill="none", stroke="ink", stroke_width="10"),
            _p("path", "scan-cross", d="M49 34v28M35 48h28", fill="none", stroke="violet", stroke_width="3"),
            _p("circle", "target-ring", cx="93", cy="24", r="11", fill="mint-wash", stroke="teal", stroke_width="3"),
            _p("circle", "result-dot", cx="93", cy="24", r="4", fill="mint", stroke="ink", stroke_width="2.2"),
            _p("path", "discovery", d="M20 79l3 8 8 3-8 3-3 8-3-8-8-3 8-3Z", fill="sun", stroke="ink", stroke_width="2.6"),
        ),
    ),
    "memory": CharacterIconDefinition(
        icon="memory",
        semantic_role="context-capture-index-recall",
        parts=(
            "root",
            "wash",
            "back-card",
            "front-card",
            "index-nodes",
            "trace",
            "input-token",
            "commit-path",
            "bookmark",
            "result",
        ),
        primitives=(
            _p("circle", "wash", cx="59", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("rect", "back-card", x="21", y="22", width="66", height="68", rx="12", fill="lavender", stroke="ink"),
            _p("rect", "front-card", x="30", y="31", width="66", height="68", rx="12", fill="paper", stroke="ink"),
            _p("path", "index-nodes", d="M45 53h9v9h-9Zm19-10h9v9h-9Zm12 25h9v9h-9Z", fill="mint", stroke="ink", stroke_width="2.3"),
            _p("path", "trace", d="M54 57l14-10m1 5 11 20", fill="none", stroke="violet", stroke_width="3"),
            _p("circle", "input-token", cx="14", cy="76", r="6", fill="coral", stroke="ink", stroke_width="2.6"),
            _p("path", "commit-path", d="M20 76h18m-7-7 7 7-7 7", fill="none", stroke="teal", stroke_width="3"),
            _p("path", "bookmark", d="M72 31v24l8-6 8 6V31Z", fill="sun", stroke="ink", stroke_width="2.7"),
            _p("path", "result", d="M102 79l3 7 7 3-7 3-3 7-3-7-7-3 7-3Z", fill="mint", stroke="ink", stroke_width="2.6"),
        ),
    ),
}


def expansion_batch_1_definition(icon: str) -> CharacterIconDefinition | None:
    return ILLUSTRATED_EXPANSION_BATCH_1.get(icon)


def expansion_batch_1_icon_ids() -> Tuple[str, ...]:
    return tuple(ILLUSTRATED_EXPANSION_BATCH_1)
