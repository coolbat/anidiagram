"""Approved static Illustrated 2.2.0 expansion slice.

The four assets passed human static review at 64, 96, and 120 pixels and are
promoted without rewriting the frozen 2.0.0 or 2.1.0 definitions. Their motion
performances passed human review and are public under
``illustrated-performance-v3``.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .illustrated_character_icons import CharacterIconDefinition, CharacterPrimitive


ILLUSTRATED_EXPANSION_BATCH_2_METADATA = {
    "batch": "illustrated-expansion-batch-2",
    "status": "approved",
    "human_visual_acceptance": "confirmed",
    "static_approved_at": "2026-07-20",
    "baseline_version": "2.1.0",
    "target_version": "2.2.0",
    "public_registry_changed": True,
    "motion_status": "approved",
    "motion_human_acceptance": "confirmed",
    "motion_approved_at": "2026-07-20",
    "cloud_arrow_variant": "a-open-stroke",
    "icons": ("file", "folder", "cloud", "shield"),
    "deferred_icons": {
        "token": "semantic-ambiguity-llm-access-or-data-unit",
    },
    "accessory_policy": {
        "check_reserved_for": ("human-confirmation", "final-acceptance"),
        "default": "integrated-semantic-cue",
        "decoration_only_accessories": False,
        "repeated_status_badges": False,
    },
}


def _p(kind: str, part: str, **attrs: str) -> CharacterPrimitive:
    return CharacterPrimitive(kind=kind, part=part, attrs=attrs)


ILLUSTRATED_EXPANSION_BATCH_2: Dict[str, CharacterIconDefinition] = {
    "file": CharacterIconDefinition(
        icon="file",
        semantic_role="document-content-attach-reference",
        parts=(
            "root",
            "wash",
            "page",
            "paperclip",
            "content-lines",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("rect", "page", x="29", y="17", width="62", height="86", rx="8", fill="paper", stroke="ink"),
            _p("path", "paperclip", d="M45 35v38c0 13 18 13 18 0V44c0-8-11-8-11 0v27c0 5 6 5 6 0V49", fill="none", stroke="violet", stroke_width="4"),
            _p("path", "content-lines", d="M68 49h12M68 64h12", fill="none", stroke="teal-dark", stroke_width="3"),
        ),
    ),
    "folder": CharacterIconDefinition(
        icon="folder",
        semantic_role="collection-store-index-organize",
        parts=(
            "root",
            "wash",
            "folder-back",
            "folder-tab",
            "document",
            "folder-front",
            "index-label",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p("path", "folder-back", d="M18 43h31l9 9h44v45H18Z", fill="lavender", stroke="ink"),
            _p("path", "folder-tab", d="M18 43h31l9 9H18Z", fill="sun", stroke="ink", stroke_width="3"),
            _p("rect", "document", x="50", y="35", width="31", height="40", rx="5", fill="paper", stroke="ink", stroke_width="3"),
            _p("path", "folder-front", d="M18 60h86l-8 37H27Z", fill="sun", stroke="ink"),
            _p("rect", "index-label", x="44", y="70", width="34", height="15", rx="7.5", fill="mint", stroke="ink", stroke_width="2.5"),
        ),
    ),
    "cloud": CharacterIconDefinition(
        icon="cloud",
        semantic_role="data-upload-download-sync",
        parts=(
            "root",
            "wash",
            "cloud-shell",
            "upload-arrow",
            "download-arrow",
        ),
        primitives=(
            _p("circle", "wash", cx="58", cy="63", r="49", fill="sky-wash", stroke="none"),
            _p("path", "cloud-shell", d="M28 91c-16 0-21-20-7-29-1-17 18-27 32-17 9-14 31-10 34 6 17-1 23 21 7 32Z", fill="sky", stroke="ink"),
            _p("path", "upload-arrow", d="M44 80V49M34 59l10-10 10 10", fill="none", stroke="violet", stroke_width="4"),
            _p("path", "download-arrow", d="M76 47v31M66 68l10 10 10-10", fill="none", stroke="teal-dark", stroke_width="4"),
        ),
    ),
    "shield": CharacterIconDefinition(
        icon="shield",
        semantic_role="security-lock-protect",
        parts=(
            "root",
            "wash",
            "shield-shell",
            "inner-field",
            "lock-shackle",
            "security-lock",
            "keyhole",
        ),
        primitives=(
            _p("circle", "wash", cx="61", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("path", "shield-shell", d="M60 15l35 14v28c0 22-14 37-35 47-21-10-35-25-35-47V29Z", fill="lavender", stroke="ink"),
            _p("path", "inner-field", d="M60 29l22 9v18c0 14-9 24-22 31-13-7-22-17-22-31V38Z", fill="paper", stroke="ink", stroke_width="3"),
            _p("path", "lock-shackle", d="M49 59v-8c0-15 22-15 22 0v8", fill="none", stroke="teal-dark", stroke_width="4"),
            _p("rect", "security-lock", x="44", y="57", width="32", height="28", rx="7", fill="mint", stroke="ink", stroke_width="3"),
            _p("path", "keyhole", d="M60 66a4 4 0 1 0 .1 0M60 70v7", fill="none", stroke="ink", stroke_width="3"),
        ),
    ),
}


def expansion_batch_2_definition(icon: str) -> CharacterIconDefinition | None:
    return ILLUSTRATED_EXPANSION_BATCH_2.get(icon)


def expansion_batch_2_icon_ids() -> Tuple[str, ...]:
    return tuple(ILLUSTRATED_EXPANSION_BATCH_2)
