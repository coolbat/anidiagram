"""Approved static assets for Illustrated Expansion Batch 3.

This slice targets four high-frequency architecture roles that cannot be
represented precisely by the twelve approved Illustrated 2.2.0 icons.  The
definitions entered the 2.3.0 public registry after human static review.
Their semantic motions were approved after separate human visual review.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .illustrated_character_icons import CharacterIconDefinition, CharacterPrimitive


ILLUSTRATED_EXPANSION_BATCH_3_METADATA = {
    "batch": "illustrated-expansion-batch-3",
    "status": "approved",
    "human_visual_acceptance": "confirmed",
    "static_approved_at": "2026-07-20",
    "baseline_version": "2.2.0",
    "target_version": "2.3.0",
    "public_registry_changed": True,
    "motion_status": "approved",
    "motion_human_acceptance": "confirmed",
    "motion_approved_at": "2026-07-20",
    "icons": ("user", "server", "ai-model", "message-queue"),
    "selection_rationale": {
        "user": "separate external requester from the operator role",
        "server": "separate deterministic compute from agent orchestration",
        "ai-model": "separate model inference from the agent that coordinates it",
        "message-queue": "represent asynchronous buffering without reusing tool or database",
    },
    "accessory_policy": {
        "check_reserved_for": ("human-confirmation", "final-acceptance"),
        "default": "integrated-semantic-cue",
        "decoration_only_accessories": False,
        "repeated_status_badges": False,
        "outer_arrows": False,
        "triangle_cues": False,
    },
}


def _p(kind: str, part: str, **attrs: str) -> CharacterPrimitive:
    return CharacterPrimitive(kind=kind, part=part, attrs=attrs)


ILLUSTRATED_EXPANSION_BATCH_3: Dict[str, CharacterIconDefinition] = {
    "user": CharacterIconDefinition(
        icon="user",
        semantic_role="external-person-request-interact",
        parts=(
            "root",
            "wash",
            "portrait-body",
            "portrait-neck",
            "portrait-head",
            "portrait-hair",
            "face",
            "conversation-card",
            "conversation-lines",
        ),
        primitives=(
            _p("circle", "wash", cx="58", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("path", "portrait-body", d="M21 101c2-23 16-36 37-36s35 13 37 36Z", fill="sky", stroke="ink"),
            _p("rect", "portrait-neck", x="51", y="56", width="15", height="17", rx="6", fill="peach", stroke="ink", stroke_width="2.6"),
            _p("circle", "portrait-head", cx="58", cy="42", r="22", fill="peach", stroke="ink"),
            _p("path", "portrait-hair", d="M37 43c-2-20 12-31 27-27 11 3 18 13 16 27l-8-8-9 4-10-6-9 8Z", fill="lavender", stroke="ink"),
            _p("path", "face", d="M48 47h2m15 0h2M51 56c5 4 10 4 15 0", fill="none", stroke="ink", stroke_width="2.8"),
            _p("path", "conversation-card", d="M80 20h27c5 0 8 3 8 8v21c0 5-3 8-8 8H96l-8 8v-8h-8c-5 0-8-3-8-8V28c0-5 3-8 8-8Z", fill="paper", stroke="ink", stroke_width="3"),
            _p("path", "conversation-lines", d="M83 34h20M83 43h14", fill="none", stroke="teal-dark", stroke_width="3"),
        ),
    ),
    "server": CharacterIconDefinition(
        icon="server",
        semantic_role="compute-host-run-service",
        parts=(
            "root",
            "wash",
            "rack-shell",
            "upper-bay",
            "middle-bay",
            "lower-bay",
            "rack-ports",
            "activity-lights",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("rect", "rack-shell", x="24", y="15", width="72", height="90", rx="14", fill="paper", stroke="ink"),
            _p("rect", "upper-bay", x="31", y="25", width="58", height="20", rx="6", fill="sky", stroke="ink", stroke_width="2.8"),
            _p("rect", "middle-bay", x="31", y="50", width="58", height="20", rx="6", fill="lavender", stroke="ink", stroke_width="2.8"),
            _p("rect", "lower-bay", x="31", y="75", width="58", height="20", rx="6", fill="sun", stroke="ink", stroke_width="2.8"),
            _p("path", "rack-ports", d="M40 35h17M40 60h17M40 85h17", fill="none", stroke="ink", stroke_width="3"),
            _p("path", "activity-lights", d="M77 35h0M77 60h0M77 85h0", fill="none", stroke="teal-dark", stroke_width="7"),
        ),
    ),
    "ai-model": CharacterIconDefinition(
        icon="ai-model",
        semantic_role="model-inference-transform-predict",
        parts=(
            "root",
            "wash",
            "model-card",
            "model-header",
            "network-links",
            "input-neurons",
            "hidden-neurons",
            "output-neuron",
            "inference-band",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("rect", "model-card", x="18", y="18", width="84", height="84", rx="18", fill="paper", stroke="ink"),
            _p("path", "model-header", d="M31 34h26M86 34h0", fill="none", stroke="violet", stroke_width="5"),
            _p("path", "network-links", d="M38 53 61 45m-23 8 23 16m-23 20 23-24m0-20 21 12M61 69l21-12M61 45l21 32M61 69l21 8", fill="none", stroke="lavender-dark", stroke_width="2.5", opacity="0.78"),
            _p("path", "input-neurons", d="M38 53h0M38 73h0", fill="none", stroke="coral", stroke_width="10"),
            _p("path", "hidden-neurons", d="M61 45h0M61 69h0", fill="none", stroke="violet", stroke_width="10"),
            _p("circle", "output-neuron", cx="82", cy="57", r="5", fill="mint", stroke="ink", stroke_width="2.4"),
            _p("path", "inference-band", d="M35 88h50", fill="none", stroke="teal-dark", stroke_width="6"),
        ),
    ),
    "message-queue": CharacterIconDefinition(
        icon="message-queue",
        semantic_role="async-buffer-order-deliver",
        parts=(
            "root",
            "wash",
            "queue-shell",
            "queue-rail",
            "message-one",
            "message-two",
            "message-three",
            "buffer-gates",
            "sequence-dots",
        ),
        primitives=(
            _p("circle", "wash", cx="60", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p("rect", "queue-shell", x="15", y="27", width="90", height="67", rx="18", fill="paper", stroke="ink"),
            _p("path", "queue-rail", d="M26 72h68", fill="none", stroke="ink", stroke_width="4"),
            _p("rect", "message-one", x="27", y="43", width="18", height="22", rx="6", fill="coral", stroke="ink", stroke_width="2.6"),
            _p("rect", "message-two", x="51", y="43", width="18", height="22", rx="6", fill="lavender", stroke="ink", stroke_width="2.6"),
            _p("rect", "message-three", x="75", y="43", width="18", height="22", rx="6", fill="mint", stroke="ink", stroke_width="2.6"),
            _p("path", "buffer-gates", d="M24 39v40M96 39v40", fill="none", stroke="teal-dark", stroke_width="4"),
            _p("path", "sequence-dots", d="M36 83h0M60 83h0M84 83h0", fill="none", stroke="violet", stroke_width="5"),
        ),
    ),
}


def expansion_batch_3_definition(icon: str) -> CharacterIconDefinition | None:
    return ILLUSTRATED_EXPANSION_BATCH_3.get(icon)


def expansion_batch_3_icon_ids() -> Tuple[str, ...]:
    return tuple(ILLUSTRATED_EXPANSION_BATCH_3)
