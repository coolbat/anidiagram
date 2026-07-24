"""Illustrated 2.5.0 expansion Batch 5 static-review candidates.

These six definitions are intentionally isolated from the public registry until
their static composition is accepted.  Motion work starts only after that gate.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .illustrated_character_icons import CharacterIconDefinition, CharacterPrimitive


ILLUSTRATED_EXPANSION_BATCH_5_METADATA = {
    "batch": "illustrated-expansion-batch-5",
    "semantic_family": "people-and-agent-intelligence",
    "status": "approved",
    "human_visual_acceptance": "confirmed",
    "static_approved_at": "2026-07-22",
    "baseline_version": "2.4.0",
    "target_version": "2.5.0",
    "public_registry_changed": False,
    "motion_status": "approved",
    "motion_approved_at": "2026-07-23",
    "review_motion_contract": "illustrated-performance-v6-review",
    "icons": (
        "developer",
        "agent-team",
        "assistant",
        "human-reviewer",
        "llm",
        "reasoning",
    ),
    "accessory_policy": {
        "one_dominant_subject": True,
        "maximum_external_accessories": 2,
        "generic_checkmarks": False,
        "generic_arrows": False,
        "generic_triangles": False,
        "generic_status_badges": False,
    },
}


def _p(kind: str, part: str, **attrs: str) -> CharacterPrimitive:
    return CharacterPrimitive(kind=kind, part=part, attrs=attrs)


ILLUSTRATED_EXPANSION_BATCH_5: Dict[str, CharacterIconDefinition] = {
    "developer": CharacterIconDefinition(
        icon="developer",
        semantic_role="person-code-build-deliver",
        parts=(
            "root",
            "wash",
            "body",
            "head",
            "hair",
            "code-console",
            "console-header",
            "code-glyphs",
            "hands",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("path", "body", d="M31 75c3-17 14-26 29-26s26 9 29 26Z", fill="sky", stroke="ink"),
            _p("circle", "head", cx="60", cy="36", r="17", fill="peach", stroke="ink"),
            _p(
                "path",
                "hair",
                d="M43 37c-3-15 5-23 18-23 12 0 20 8 16 23l-8-7-8 5-10-6-5 8Z",
                fill="violet",
                stroke="ink",
            ),
            _p("rect", "code-console", x="18", y="63", width="84", height="42", rx="9", fill="paper", stroke="ink"),
            _p("path", "console-header", d="M19 76h82M28 70h0m8 0h0", fill="none", stroke="coral", stroke_width="5.5"),
            _p(
                "path",
                "code-glyphs",
                d="m38 86-7 6 7 6m20-12 7 6-7 6m-5-15-7 18M75 87h14m-14 9h10",
                fill="none",
                stroke="violet",
                stroke_width="2.8",
            ),
            _p("path", "hands", d="M29 64c3-5 10-5 13 0m36 0c3-5 10-5 13 0", fill="peach", stroke="ink", stroke_width="3"),
        ),
    ),
    "agent-team": CharacterIconDefinition(
        icon="agent-team",
        semantic_role="agents-coordinate-delegate-synthesize",
        parts=(
            "root",
            "wash",
            "collaboration-field",
            "team-links",
            "lead-agent",
            "lead-core",
            "member-left",
            "member-right",
            "member-cores",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("ellipse", "collaboration-field", cx="60", cy="63", rx="48", ry="38", fill="paper", stroke="ink"),
            _p("path", "team-links", d="M60 54 34 77m26-23 26 23M34 77h52", fill="none", stroke="teal-dark", stroke_width="3.2"),
            _p("rect", "lead-agent", x="42", y="23", width="36", height="34", rx="11", fill="violet", stroke="ink"),
            _p(
                "path",
                "lead-core",
                d="M49 47l4-14 4 14m-6.5-5h5M62 33h8m-4 0v14m-4 0h8",
                fill="none",
                stroke="paper",
                stroke_width="2.5",
            ),
            _p("rect", "member-left", x="16", y="69", width="36", height="32", rx="11", fill="sky", stroke="ink"),
            _p("rect", "member-right", x="68", y="69", width="36", height="32", rx="11", fill="mint", stroke="ink"),
            _p(
                "path",
                "member-cores",
                d="M26 85h0m8 0h0m8 0h0M78 85h0m8 0h0m8 0h0",
                fill="none",
                stroke="ink",
                stroke_width="5.5",
            ),
        ),
    ),
    "assistant": CharacterIconDefinition(
        icon="assistant",
        semantic_role="assistant-listen-guide-respond",
        parts=(
            "root",
            "wash",
            "assistant-shell",
            "face-panel",
            "eyes",
            "smile",
            "headset",
            "earpieces",
            "response-panel",
            "response-lines",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("rect", "assistant-shell", x="22", y="20", width="76", height="84", rx="30", fill="sky", stroke="ink"),
            _p("rect", "face-panel", x="34", y="33", width="52", height="36", rx="16", fill="paper", stroke="ink"),
            _p("path", "eyes", d="M46 49h0m28 0h0", fill="none", stroke="teal-dark", stroke_width="7"),
            _p("path", "smile", d="M50 57c5 6 15 6 20 0", fill="none", stroke="violet", stroke_width="2.8"),
            _p("path", "headset", d="M28 51V43c0-19 13-31 32-31s32 12 32 31v8", fill="none", stroke="violet", stroke_width="4"),
            _p("path", "earpieces", d="M22 48h12v18H22Zm64 0h12v18H86Z", fill="lavender", stroke="ink"),
            _p("rect", "response-panel", x="37", y="77", width="46", height="17", rx="7", fill="paper", stroke="ink", stroke_width="2.8"),
            _p("path", "response-lines", d="M46 85h12m6 0h10", fill="none", stroke="teal-dark", stroke_width="2.8"),
        ),
    ),
    "human-reviewer": CharacterIconDefinition(
        icon="human-reviewer",
        semantic_role="human-inspect-decide-annotate",
        parts=(
            "root",
            "wash",
            "body",
            "head",
            "hair",
            "glasses",
            "review-sheet",
            "review-lines",
            "decision-signals",
            "hands",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p("path", "body", d="M23 103c2-25 17-39 37-39s35 14 37 39Z", fill="mint", stroke="ink"),
            _p("circle", "head", cx="60", cy="37", r="18", fill="peach", stroke="ink"),
            _p("path", "hair", d="M42 37c-2-15 6-23 18-23 13 0 21 8 18 23l-8-6-9 4-10-5-6 7Z", fill="lavender", stroke="ink"),
            _p("path", "glasses", d="M43 40h13m8 0h13M56 40h8", fill="none", stroke="ink", stroke_width="2.8"),
            _p("rect", "review-sheet", x="31", y="61", width="58", height="46", rx="7", fill="paper", stroke="ink"),
            _p("path", "review-lines", d="M43 73h31M43 84h25M43 95h31", fill="none", stroke="violet", stroke_width="2.6"),
            _p("path", "decision-signals", d="M78 73h0M72 84h0M78 95h0", fill="none", stroke="coral", stroke_width="7"),
            _p("path", "hands", d="M31 91c-7-1-10 5-6 10m64-10c7-1 10 5 6 10", fill="peach", stroke="ink", stroke_width="3"),
        ),
    ),
    "llm": CharacterIconDefinition(
        icon="llm",
        semantic_role="language-context-transform-generate",
        parts=(
            "root",
            "wash",
            "context-back",
            "context-mid",
            "model-shell",
            "model-mark",
            "token-lines",
            "completion-dots",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("rect", "context-back", x="25", y="16", width="76", height="70", rx="14", fill="sky", stroke="ink"),
            _p("rect", "context-mid", x="18", y="24", width="76", height="70", rx="14", fill="lavender", stroke="ink"),
            _p("path", "model-shell", d="M12 31h76c8 0 14 6 14 14v50H67l-10 12-2-12H26c-8 0-14-6-14-14Z", fill="paper", stroke="ink"),
            _p(
                "path",
                "model-mark",
                d="M30 45v20h11M47 45v20h11M64 65V45l8 11 8-11v20",
                fill="none",
                stroke="violet",
                stroke_width="3.2",
            ),
            _p("path", "token-lines", d="M29 76h44M29 84h32", fill="none", stroke="teal-dark", stroke_width="2.8"),
            _p("path", "completion-dots", d="M72 84h0m9 0h0m9 0h0", fill="none", stroke="coral", stroke_width="5.5"),
        ),
    ),
    "reasoning": CharacterIconDefinition(
        icon="reasoning",
        semantic_role="premise-connect-infer-conclude",
        parts=(
            "root",
            "wash",
            "reasoning-shell",
            "thought-field",
            "reasoning-path",
            "premise-points",
            "conclusion-point",
            "insight-base",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p(
                "path",
                "reasoning-shell",
                d="M60 13c-24 0-40 16-40 38 0 15 8 25 21 33v11h38V84c13-8 21-19 21-34 0-21-17-37-40-37Z",
                fill="paper",
                stroke="ink",
            ),
            _p("circle", "thought-field", cx="60", cy="51", r="29", fill="lavender", stroke="ink", stroke_width="2.8"),
            _p(
                "path",
                "reasoning-path",
                d="M40 40h16v12H45v14h15V57h18V42h-9v-8",
                fill="none",
                stroke="paper",
                stroke_width="3.2",
            ),
            _p("path", "premise-points", d="M40 40h0M45 66h0M69 34h0", fill="none", stroke="teal-dark", stroke_width="8"),
            _p("circle", "conclusion-point", cx="78", cy="42", r="6", fill="sun", stroke="ink", stroke_width="2.4"),
            _p("rect", "insight-base", x="39", y="93", width="42", height="12", rx="5", fill="sky", stroke="ink", stroke_width="2.8"),
        ),
    ),
}


def expansion_batch_5_definition(icon: str) -> CharacterIconDefinition | None:
    return ILLUSTRATED_EXPANSION_BATCH_5.get(icon)


def expansion_batch_5_icon_ids() -> Tuple[str, ...]:
    return tuple(ILLUSTRATED_EXPANSION_BATCH_5)
