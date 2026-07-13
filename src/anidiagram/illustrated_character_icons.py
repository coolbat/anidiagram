"""Clean-room registry for the illustrated-character-v1 semantic icons.

Definitions use a 100 by 100 local coordinate system.  Renderers own SVG
serialization; this module supplies stable part names and semantic intent only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class CharacterPrimitive:
    kind: str
    part: str
    attrs: Dict[str, str]


@dataclass(frozen=True)
class CharacterIconDefinition:
    icon: str
    semantic_role: str
    parts: Tuple[str, ...]
    primitives: Tuple[CharacterPrimitive, ...]


def _p(kind: str, part: str, **attrs: str) -> CharacterPrimitive:
    return CharacterPrimitive(kind=kind, part=part, attrs=attrs)


ILLUSTRATED_CHARACTER_REGISTRY: Dict[str, CharacterIconDefinition] = {
    "agent": CharacterIconDefinition(
        icon="agent",
        semantic_role="think-decide-confirm",
        parts=("root", "brain-left", "brain-right", "chip", "signal", "spark"),
        primitives=(
            _p("path", "brain-left", d="M48 18C31 10 13 23 18 39C4 48 10 67 25 70C26 86 44 91 52 78L52 30C51 25 50 21 48 18Z", fill="mint"),
            _p("path", "brain-right", d="M52 18C69 10 87 23 82 39C96 48 90 67 75 70C74 86 56 91 48 78L48 30C49 25 50 21 52 18Z", fill="lavender"),
            _p("path", "brain-veins", d="M34 27c-5 6 4 9 1 16m-8 12c8-1 5 9 11 11m28-39c5 6-4 9-1 16m8 12c-8-1-5 9-11 11", fill="none"),
            _p("rect", "chip", x="31", y="33", width="38", height="32", rx="4", fill="paper"),
            _p("text", "chip-label", x="50", y="54", text="AI", fill="ink"),
            _p("path", "signal", d="M73 39h7m-7 7h10m-10 7h7", fill="none"),
            _p("path", "spark", d="M21 20l2 5 5 2-5 2-2 5-2-5-5-2 5-2z", fill="sun"),
        ),
    ),
    "operator": CharacterIconDefinition(
        icon="operator",
        semantic_role="focus-type-resolve",
        parts=("root", "hair", "face", "glasses", "hands", "laptop", "cursor"),
        primitives=(
            _p("path", "hair", d="M35 35c-6-13 4-22 16-22 12 0 21 8 16 23l-7-3-5 4-9-5-5 5z", fill="violet"),
            _p("circle", "face", cx="51", cy="39", r="15", fill="peach"),
            _p("path", "glasses", d="M37 39h9m10 0h9m-19 0h10m-2 0v2", fill="none"),
            _p("path", "body", d="M29 67c2-14 12-22 22-22s20 8 22 22", fill="sky"),
            _p("path", "hands", d="M38 64l7 8m19-8l-7 8", fill="none"),
            _p("rect", "laptop", x="27", y="62", width="48", height="26", rx="3", fill="paper"),
            _p("path", "laptop-base", d="M22 89h58l-5 5H27z", fill="lavender"),
            _p("path", "cursor", d="M70 53l7 4-5 2-2 5z", fill="sun"),
        ),
    ),
    "database": CharacterIconDefinition(
        icon="database",
        semantic_role="ingest-settle-confirm",
        parts=("root", "hat", "bucket", "liquid", "bead", "check"),
        primitives=(
            _p("path", "hat", d="M31 29c8-15 30-15 38 0l-4 8H35z", fill="orange"),
            _p("path", "hat-band", d="M34 35h32", fill="none"),
            _p("path", "bucket", d="M27 43h47l-5 43H32z", fill="teal"),
            _p("path", "handle", d="M34 45c0-18 33-18 33 0", fill="none"),
            _p("path", "liquid", d="M31 71c9-6 16 5 25 0 7-4 12 0 15 2l-2 13H32z", fill="orange"),
            _p("circle", "bead", cx="51", cy="24", r="4", fill="sun"),
            _p("path", "check", d="M47 56l5 5 10-11", fill="none"),
            _p("path", "spill", d="M25 86c8-2 15 2 23 0 9-2 17 4 29 1-2 10-14 11-25 9-14 3-27 0-27-10z", fill="orange"),
        ),
    ),
    "search": CharacterIconDefinition(
        icon="search",
        semantic_role="scout-scan-find",
        parts=("root", "lens", "scan", "marker", "spark"),
        primitives=(
            _p("circle", "lens", cx="45", cy="46", r="23", fill="sky"),
            _p("path", "lens-shine", d="M31 40c4-9 13-14 23-12", fill="none"),
            _p("path", "scan", d="M25 46h40", fill="none"),
            _p("path", "handle", d="M61 62l16 16", fill="none"),
            _p("path", "marker", d="M45 33c-6 0-10 4-10 10 0 8 10 17 10 17s10-9 10-17c0-6-4-10-10-10z", fill="peach"),
            _p("circle", "marker-dot", cx="45", cy="43", r="3", fill="paper"),
            _p("path", "spark", d="M77 22l2 5 5 2-5 2-2 5-2-5-5-2 5-2z", fill="sun"),
        ),
    ),
    "tool": CharacterIconDefinition(
        icon="tool",
        semantic_role="kit-act-confirm",
        parts=("root", "bucket", "lid", "wrench", "spark"),
        primitives=(
            _p("path", "bucket", d="M25 40h50l-5 43H30z", fill="teal"),
            _p("path", "lid", d="M29 39c5-12 37-12 42 0z", fill="lavender"),
            _p("path", "handle", d="M35 41c0-17 30-17 30 0", fill="none"),
            _p("path", "wrench", d="M55 28c6-5 13-2 15 3l-7 4 6 7-8 8-7-6-4 7c-6-2-9-9-5-15l5 4 6-6z", fill="sun"),
            _p("circle", "wrench-hole", cx="65", cy="31", r="3", fill="paper"),
            _p("path", "spark", d="M27 66l2 5 5 2-5 2-2 5-2-5-5-2 5-2z", fill="peach"),
        ),
    ),
    "api": CharacterIconDefinition(
        icon="api",
        semantic_role="signal-request-return",
        parts=("root", "interface", "request", "receipt", "status"),
        primitives=(
            _p("rect", "interface", x="19", y="27", width="62", height="46", rx="7", fill="paper"),
            _p("path", "interface-top", d="M20 39h60", fill="none"),
            _p("circle", "interface-dot", cx="28", cy="33", r="2", fill="peach"),
            _p("path", "request", d="M31 53h24m-7-7 7 7-7 7", fill="none"),
            _p("path", "receipt", d="M68 61H44m7-7-7 7 7 7", fill="none"),
            _p("circle", "status", cx="73", cy="28", r="7", fill="mint"),
        ),
    ),
    "memory": CharacterIconDefinition(
        icon="memory",
        semantic_role="index-commit-recall",
        parts=("root", "back-card", "front-card", "bookmark", "key-line"),
        primitives=(
            _p("rect", "back-card", x="25", y="24", width="47", height="50", rx="7", fill="lavender"),
            _p("rect", "front-card", x="33", y="33", width="44", height="48", rx="7", fill="paper"),
            _p("path", "bookmark", d="M62 33v19l-6-4-6 4V33z", fill="peach"),
            _p("path", "key-line", d="M43 59h24m-24 8h17", fill="none"),
            _p("circle", "memory-dot", cx="38", cy="29", r="4", fill="mint"),
        ),
    ),
    "output": CharacterIconDefinition(
        icon="output",
        semantic_role="reveal-deliver-confirm",
        parts=("root", "envelope", "card", "check", "spark"),
        primitives=(
            _p("path", "envelope", d="M19 34h62v42H19z", fill="sky"),
            _p("path", "envelope-fold", d="M20 36l30 23 30-23M20 75l19-19m42 19L62 56", fill="none"),
            _p("rect", "card", x="35", y="22", width="31", height="34", rx="4", fill="paper"),
            _p("path", "card-line", d="M41 32h18m-18 7h12", fill="none"),
            _p("path", "check", d="M43 46l5 5 10-11", fill="none"),
            _p("path", "spark", d="M77 22l2 5 5 2-5 2-2 5-2-5-5-2 5-2z", fill="sun"),
        ),
    ),
    "file": CharacterIconDefinition(
        icon="file",
        semantic_role="note-write-settle",
        parts=("root", "page", "corner", "line-1", "line-2", "line-3", "dot"),
        primitives=(
            _p("path", "page", d="M28 18h30l15 15v49H28z", fill="paper"),
            _p("path", "corner", d="M58 18v16h15", fill="lavender"),
            _p("path", "line-1", d="M38 48h25", fill="none"),
            _p("path", "line-2", d="M38 57h22", fill="none"),
            _p("path", "line-3", d="M38 66h16", fill="none"),
            _p("circle", "dot", cx="30", cy="74", r="5", fill="mint"),
        ),
    ),
    "folder": CharacterIconDefinition(
        icon="folder",
        semantic_role="file-store-ready",
        parts=("root", "folder", "tab", "sheet", "seal"),
        primitives=(
            _p("path", "folder", d="M17 36h27l7 8h32v37H17z", fill="sun"),
            _p("path", "tab", d="M18 36h25l7 8H18z", fill="orange"),
            _p("path", "sheet", d="M47 49h23v24H47z", fill="paper"),
            _p("path", "sheet-line", d="M52 58h12m-12 6h9", fill="none"),
            _p("circle", "seal", cx="75", cy="72", r="8", fill="mint"),
            _p("path", "seal-mark", d="M71 72l3 3 5-6", fill="none"),
        ),
    ),
    "cloud": CharacterIconDefinition(
        icon="cloud",
        semantic_role="uplink-send-ready",
        parts=("root", "cloud", "kite", "data-dot", "ready-light"),
        primitives=(
            _p("path", "cloud", d="M25 70c-13 0-16-18-3-22 1-14 20-18 27-7 10-8 27-1 25 12 12 4 8 17-3 17z", fill="sky"),
            _p("path", "kite", d="M53 24l13 13-13 13-13-13z", fill="lavender"),
            _p("path", "kite-tail", d="M53 50c3 5-4 8 0 13", fill="none"),
            _p("circle", "data-dot", cx="53", cy="61", r="4", fill="sun"),
            _p("circle", "ready-light", cx="73", cy="42", r="6", fill="mint"),
        ),
    ),
    "shield": CharacterIconDefinition(
        icon="shield",
        semantic_role="guard-scan-confirm",
        parts=("root", "shell", "core", "scan", "check"),
        primitives=(
            _p("path", "shell", d="M50 16l28 10v22c0 19-12 31-28 37-16-6-28-18-28-37V26z", fill="lavender"),
            _p("path", "core", d="M50 29l15 6v13c0 10-6 17-15 21-9-4-15-11-15-21V35z", fill="paper"),
            _p("path", "scan", d="M35 47h30", fill="none"),
            _p("path", "check", d="M42 50l6 6 12-14", fill="none"),
        ),
    ),
    "token": CharacterIconDefinition(
        icon="token",
        semantic_role="intent-orient-ready",
        parts=("root", "shell", "core", "tick-left", "tick-right", "tick-top", "tick-bottom"),
        primitives=(
            _p("circle", "shell", cx="50", cy="50", r="28", fill="teal"),
            _p("circle", "core", cx="50", cy="50", r="13", fill="paper"),
            _p("path", "tick-left", d="M17 50h12", fill="none"),
            _p("path", "tick-right", d="M71 50h12", fill="none"),
            _p("path", "tick-top", d="M50 17v12", fill="none"),
            _p("path", "tick-bottom", d="M50 71v12", fill="none"),
        ),
    ),
}


def character_definition(icon: str) -> CharacterIconDefinition | None:
    return ILLUSTRATED_CHARACTER_REGISTRY.get(icon)


def character_icon_ids() -> Tuple[str, ...]:
    return tuple(ILLUSTRATED_CHARACTER_REGISTRY)
