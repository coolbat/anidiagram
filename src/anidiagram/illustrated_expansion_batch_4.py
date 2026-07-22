"""Approved Illustrated 2.4.0 expansion definitions.

The four definitions reuse the approved geometry and color vocabulary from the
2.3.0 baseline. Their static, motion, and real-case review evidence is archived
separately from the current public registry.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .illustrated_character_icons import CharacterIconDefinition, CharacterPrimitive


ILLUSTRATED_EXPANSION_BATCH_4_METADATA = {
    "batch": "illustrated-expansion-batch-4",
    "status": "approved",
    "human_visual_acceptance": "confirmed",
    "static_approved_at": "2026-07-21",
    "baseline_version": "2.3.0",
    "target_version": "2.4.0",
    "token_version": "2.4.0",
    "public_registry_changed": True,
    "motion_status": "approved",
    "public_motion_contract": "illustrated-performance-v5",
    "review_motion_contract": "illustrated-performance-v5-review",
    "icons": ("vector-database", "knowledge-base", "gateway", "container"),
    "selection_rationale": {
        "vector-database": "separate semantic retrieval storage from a generic database",
        "knowledge-base": "represent curated connected knowledge without reusing file or folder",
        "gateway": "represent admission and mediation without reusing the API card",
        "container": "represent packaged isolated workloads without reusing the server rack",
    },
    "accessory_policy": {
        "one_dominant_subject": True,
        "integrated_semantic_cues": True,
        "outer_arrows": False,
        "generic_checkmarks": False,
        "status_badges": False,
        "triangle_cues": False,
    },
}


def _p(kind: str, part: str, **attrs: str) -> CharacterPrimitive:
    return CharacterPrimitive(kind=kind, part=part, attrs=attrs)


ILLUSTRATED_EXPANSION_BATCH_4: Dict[str, CharacterIconDefinition] = {
    "vector-database": CharacterIconDefinition(
        icon="vector-database",
        semantic_role="vector-embed-index-retrieve",
        parts=(
            "root",
            "wash",
            "vector-store-body",
            "vector-store-top",
            "vector-field",
            "vector-links",
            "vector-points",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p(
                "path",
                "vector-store-body",
                d="M23 37v49c0 11 17 19 37 19s37-8 37-19V37Z",
                fill="sky",
                stroke="ink",
            ),
            _p("ellipse", "vector-store-top", cx="60", cy="37", rx="37", ry="15", fill="lavender", stroke="ink"),
            _p(
                "path",
                "vector-field",
                d="M31 59c8 6 18 9 29 9s22-3 29-9v27c0 7-13 13-29 13S31 93 31 86Z",
                fill="paper",
                stroke="ink",
                stroke_width="2.8",
            ),
            _p(
                "path",
                "vector-links",
                d="M43 74 59 60l19 13-16 15-19-14m16-14 3 28",
                fill="none",
                stroke="violet",
                stroke_width="2.8",
            ),
            _p(
                "path",
                "vector-points",
                d="M43 74h0M59 60h0M78 73h0M62 88h0",
                fill="none",
                stroke="teal-dark",
                stroke_width="7",
            ),
        ),
    ),
    "knowledge-base": CharacterIconDefinition(
        icon="knowledge-base",
        semantic_role="knowledge-curate-connect-reference",
        parts=(
            "root",
            "wash",
            "book-left",
            "book-right",
            "book-spine",
            "knowledge-links",
            "knowledge-points",
            "reference-lines",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p(
                "path",
                "book-left",
                d="M11 31c18-6 35-4 49 8v65c-14-10-31-13-49-7Z",
                fill="paper",
                stroke="ink",
            ),
            _p(
                "path",
                "book-right",
                d="M109 31c-18-6-35-4-49 8v65c14-10 31-13 49-7Z",
                fill="lavender",
                stroke="ink",
            ),
            _p("path", "book-spine", d="M60 39v65", fill="none", stroke="ink", stroke_width="3"),
            _p(
                "path",
                "knowledge-links",
                d="M28 56 43 68 31 82m15-31-3 17m34-12-14 12 15 13m-15-13 13 0",
                fill="none",
                stroke="violet",
                stroke_width="2.6",
            ),
            _p(
                "path",
                "knowledge-points",
                d="M28 56h0M43 68h0M31 82h0M77 56h0M63 68h0M78 81h0",
                fill="none",
                stroke="teal-dark",
                stroke_width="6.5",
            ),
            _p("path", "reference-lines", d="M23 91h22M75 91h22", fill="none", stroke="coral", stroke_width="3"),
        ),
    ),
    "gateway": CharacterIconDefinition(
        icon="gateway",
        semantic_role="traffic-admit-route-mediate",
        parts=(
            "root",
            "wash",
            "gateway-shell",
            "gateway-opening",
            "policy-window",
            "traffic-rails",
            "request-token",
            "response-token",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("rect", "gateway-shell", x="17", y="14", width="86", height="93", rx="21", fill="lavender", stroke="ink"),
            _p(
                "path",
                "gateway-opening",
                d="M34 106V55c0-16 11-27 26-27s26 11 26 27v51Z",
                fill="paper",
                stroke="ink",
            ),
            _p("rect", "policy-window", x="46", y="36", width="28", height="10", rx="5", fill="sun", stroke="ink", stroke_width="2.5"),
            _p("path", "traffic-rails", d="M45 57v36M75 57v36", fill="none", stroke="lavender-dark", stroke_width="3"),
            _p("path", "request-token", d="M45 63h0M45 84h0", fill="none", stroke="coral", stroke_width="9"),
            _p("path", "response-token", d="M75 72h0M75 93h0", fill="none", stroke="mint", stroke_width="9"),
        ),
    ),
    "container": CharacterIconDefinition(
        icon="container",
        semantic_role="workload-package-isolate-run",
        parts=(
            "root",
            "wash",
            "container-shell",
            "container-lid",
            "container-side",
            "container-ribs",
            "isolation-frame",
            "app-module",
            "runtime-slots",
            "container-feet",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("path", "container-shell", d="M12 36h80v61H12Z", fill="sky", stroke="ink"),
            _p("path", "container-lid", d="m12 36 16-15h80L92 36Z", fill="lavender", stroke="ink"),
            _p("path", "container-side", d="m92 36 16-15v61L92 97Z", fill="teal", stroke="ink"),
            _p("path", "container-ribs", d="M24 44v45M34 44v45M80 44v45", fill="none", stroke="teal-dark", stroke_width="3"),
            _p("rect", "isolation-frame", x="40", y="47", width="34", height="38", rx="8", fill="paper", stroke="ink", stroke_width="3"),
            _p("rect", "app-module", x="46", y="56", width="22", height="20", rx="6", fill="mint", stroke="ink", stroke_width="2.8"),
            _p("path", "runtime-slots", d="M51 66h0M57 66h0M63 66h0", fill="none", stroke="violet", stroke_width="5"),
            _p("path", "container-feet", d="M25 97v7m55-7v7", fill="none", stroke="ink", stroke_width="4"),
        ),
    ),
}


def expansion_batch_4_definition(icon: str) -> CharacterIconDefinition | None:
    return ILLUSTRATED_EXPANSION_BATCH_4.get(icon)


def expansion_batch_4_icon_ids() -> Tuple[str, ...]:
    return tuple(ILLUSTRATED_EXPANSION_BATCH_4)
