"""Experimental clean-room registry for structured illustrated v2 concepts.

Draft B removes mascot treatment.  Each icon is composed from one dominant
semantic object, one action cue, and one outcome cue with deliberate negative
space between them.  The stable illustrated-character-v1 registry remains the
product default while this direction is reviewed.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .illustrated_character_icons import CharacterIconDefinition, CharacterPrimitive


def _p(kind: str, part: str, **attrs: str) -> CharacterPrimitive:
    return CharacterPrimitive(kind=kind, part=part, attrs=attrs)


ILLUSTRATED_CHARACTER_V2_CONCEPTS: Dict[str, CharacterIconDefinition] = {
    "agent": CharacterIconDefinition(
        icon="agent",
        semantic_role="input-reason-result",
        parts=(
            "root",
            "wash",
            "brain-left",
            "brain-right",
            "brain-detail",
            "processor",
            "processor-core",
            "input-nodes",
            "input-path",
            "output-path",
            "result",
        ),
        primitives=(
            _p("circle", "wash", cx="59", cy="61", r="49", fill="lavender-wash", stroke="none"),
            _p("path", "brain-left", d="M57 27C45 18 30 25 31 38c-11 4-12 19-2 25-5 12 7 23 18 18 3 8 10 9 15 3V38c-1-5-2-8-5-11Z", fill="mint", stroke="ink"),
            _p("path", "brain-right", d="M63 27c12-9 27-2 26 11 11 4 12 19 2 25 5 12-7 23-18 18-3 8-10 9-15 3V38c1-5 2-8 5-11Z", fill="lavender", stroke="ink"),
            _p("path", "brain-detail", d="M43 35c-5 4-3 9 1 11m-8 13c7-1 7 6 12 8m29-32c5 4 3 9-1 11m8 13c-7-1-7 6-12 8", fill="none", stroke="ink", stroke_width="2.6", opacity="0.68"),
            _p("rect", "processor", x="45", y="43", width="30", height="27", rx="6", fill="paper", stroke="ink"),
            _p("rect", "processor-core", x="54", y="51", width="12", height="11", rx="3", fill="sun", stroke="ink", stroke_width="2.5"),
            _p("path", "input-nodes", d="M8 45h12v12H8Zm0 26h12V59H8Z", fill="coral", stroke="ink"),
            _p("path", "input-path", d="M20 51h9m-9 14h7c4 0 5-3 5-7", fill="none", stroke="violet", stroke_width="3"),
            _p("path", "output-path", d="M90 54h10c5 0 7-3 7-7V35", fill="none", stroke="violet", stroke_width="3"),
            _p("path", "result", d="M107 16l3 8 8 3-8 3-3 8-3-8-8-3 8-3Z", fill="sun", stroke="ink", stroke_width="2.7"),
        ),
    ),
    "operator": CharacterIconDefinition(
        icon="operator",
        semantic_role="person-operate-status",
        parts=(
            "root",
            "wash",
            "body",
            "head",
            "hair",
            "glasses",
            "laptop",
            "screen",
            "laptop-base",
            "input-cursor",
            "status",
            "status-check",
        ),
        primitives=(
            _p("circle", "wash", cx="58", cy="61", r="49", fill="sky-wash", stroke="none"),
            _p("path", "body", d="M31 80c2-17 13-27 28-27 16 0 27 10 29 27Z", fill="sky", stroke="ink"),
            _p("circle", "head", cx="59", cy="36", r="18", fill="peach", stroke="ink"),
            _p("path", "hair", d="M41 36c-3-15 8-25 21-23 12 1 19 11 16 24l-9-5-6 4-9-5-7 6Z", fill="violet", stroke="ink"),
            _p("path", "glasses", d="M43 38h13c0 6-3 9-7 9s-6-3-6-9Zm19 0h13c0 6-3 9-7 9s-6-3-6-9Zm-6 1h6", fill="paper", stroke="ink", stroke_width="2.7"),
            _p("path", "laptop", d="M26 70h68l-6 31H32Z", fill="paper", stroke="ink"),
            _p("rect", "screen", x="50", y="78", width="21", height="13", rx="3", fill="mint", stroke="ink", stroke_width="2.5"),
            _p("path", "laptop-base", d="M20 102h80l-7 7H27Z", fill="lavender", stroke="ink"),
            _p("path", "input-cursor", d="M18 64l13 6-6 3-3 7Z", fill="sun", stroke="ink", stroke_width="2.6"),
            _p("circle", "status", cx="98", cy="29", r="13", fill="mint", stroke="ink"),
            _p("path", "status-check", d="M91 29l5 5 10-12", fill="none", stroke="ink", stroke_width="3.2"),
        ),
    ),
    "tool": CharacterIconDefinition(
        icon="tool",
        semantic_role="tool-action-complete",
        parts=(
            "root",
            "wash",
            "toolbox",
            "toolbox-lid",
            "handle",
            "wrench",
            "wrench-hole",
            "target",
            "action-path",
            "completion",
        ),
        primitives=(
            _p("circle", "wash", cx="59", cy="61", r="49", fill="sun-wash", stroke="none"),
            _p("path", "toolbox", d="M20 54h77l-7 46H27Z", fill="teal", stroke="ink"),
            _p("path", "toolbox-lid", d="M18 48h81v15H18Z", fill="lavender", stroke="ink"),
            _p("path", "handle", d="M38 48c0-19 40-19 40 0", fill="none", stroke="ink", stroke_width="4"),
            _p("path", "wrench", d="M84 15c9-4 17 2 17 10l-10 4 8 9-36 36-11-11 36-36-7-8Z", fill="sun", stroke="ink"),
            _p("circle", "wrench-hole", cx="58", cy="67", r="4", fill="paper", stroke="ink", stroke_width="2.5"),
            _p("path", "target", d="M11 79l5-9 10 1 5 10-6 9-10-1Z", fill="coral", stroke="ink"),
            _p("path", "action-path", d="M31 76c9-1 14-5 20-11", fill="none", stroke="violet", stroke_width="3"),
            _p("path", "completion", d="M99 73l3 7 7 3-7 3-3 7-3-7-7-3 7-3Z", fill="mint", stroke="ink", stroke_width="2.6"),
        ),
    ),
    "output": CharacterIconDefinition(
        icon="output",
        semantic_role="document-send-confirm",
        parts=(
            "root",
            "wash",
            "card",
            "card-lines",
            "envelope",
            "envelope-fold",
            "send-path",
            "check-badge",
            "check",
        ),
        primitives=(
            _p("circle", "wash", cx="58", cy="61", r="49", fill="mint-wash", stroke="none"),
            _p("rect", "card", x="39", y="10", width="44", height="50", rx="7", fill="paper", stroke="ink"),
            _p("path", "card-lines", d="M49 24h24m-24 10h18m-18 10h13", fill="none", stroke="lavender-dark", stroke_width="3"),
            _p("path", "envelope", d="M15 48h83v52H15Z", fill="sky", stroke="ink"),
            _p("path", "envelope-fold", d="M17 51l40 30 39-30M17 98l28-31m51 31L69 67", fill="none", stroke="ink", stroke_width="3"),
            _p("path", "send-path", d="M101 61c8-5 11-13 9-22", fill="none", stroke="violet", stroke_width="3"),
            _p("circle", "check-badge", cx="105", cy="27", r="13", fill="mint", stroke="ink"),
            _p("path", "check", d="M98 27l5 5 10-12", fill="none", stroke="ink", stroke_width="3.2"),
        ),
    ),
}


def character_v2_definition(icon: str) -> CharacterIconDefinition | None:
    return ILLUSTRATED_CHARACTER_V2_CONCEPTS.get(icon)


def character_v2_icon_ids() -> Tuple[str, ...]:
    return tuple(ILLUSTRATED_CHARACTER_V2_CONCEPTS)
