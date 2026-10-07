"""Shared deterministic text measurement for render and quality gates."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import List, Optional, Tuple


LABEL_LINE_HEIGHT = 18
CAPTION_LINE_HEIGHT = 17
TEXT_VERTICAL_PADDING = 10


def visual_units(text: str) -> float:
    """Approximate browser text width while accounting for CJK glyphs."""

    return sum(
        2.0 if unicodedata.east_asian_width(character) in {"W", "F"} else 1.0
        for character in str(text or "")
    )


def fitted_text_length(text: str, max_width: float, font_size: float) -> Optional[float]:
    """Return a deterministic SVG text length only when a line needs fitting.

    System sans-serif metrics differ across operating systems. Lines that are
    comfortably short keep their natural glyph metrics; lines near the layout
    boundary receive an explicit width so Linux and macOS stay inside the same
    authored text region.
    """

    limit = max(1.0, float(max_width) - 8.0)
    estimated = visual_units(text) * float(font_size) * 0.58
    return limit if estimated > limit else None


def wrap_text(text: str, max_units: int) -> List[str]:
    value = str(text or "").strip()
    if not value:
        return []
    max_units = max(1, int(max_units))
    tokens = value.split()
    if len(tokens) > 1:
        lines: List[str] = []
        current = tokens[0]
        for token in tokens[1:]:
            candidate = f"{current} {token}"
            if visual_units(candidate) <= max_units:
                current = candidate
            else:
                lines.extend(_split_token(current, max_units))
                current = token
        lines.extend(_split_token(current, max_units))
        return lines
    return _split_token(value, max_units)


def _split_token(value: str, max_units: int) -> List[str]:
    if visual_units(value) <= max_units:
        return [value]
    if not any(unicodedata.east_asian_width(character) in {"W", "F"} for character in value):
        return [value]
    lines: List[str] = []
    current = ""
    for character in value:
        if current and visual_units(current + character) > max_units:
            lines.append(current)
            current = character
        else:
            current += character
    if current:
        lines.append(current)
    return lines


def node_text_region(
    width: float,
    *,
    icon_system: str,
    has_icon: bool,
    decision: bool = False,
) -> Tuple[float, float]:
    """Return horizontal text offset and width using renderer-owned rules."""

    if decision:
        return width * 0.28, max(24.0, width * 0.44)
    if not has_icon:
        return 12.0, max(42.0, width - 24.0)
    if icon_system == "diagram-core-v1":
        offset = min(116.0, max(90.0, width * 0.40))
    elif icon_system == "illustrated":
        offset = min(150.0, max(112.0, width * 0.48))
    elif icon_system in {"illustrated-character-v1", "illustrated-character-v2"}:
        offset = min(86.0, max(68.0, width * 0.40))
    else:
        offset = min(68.0, max(54.0, width * 0.36))
    return offset, max(42.0, width - offset - 12.0)


@dataclass(frozen=True)
class TextBlockLayout:
    label_lines: Tuple[str, ...]
    caption_lines: Tuple[str, ...]
    all_label_lines: int
    all_caption_lines: int
    caption_truncated: bool
    first_baseline: float
    total_height: float


def text_block_layout(label: str, caption: str, width: float, height: float) -> TextBlockLayout:
    all_label_lines = wrap_text(label, max(8, int(width / 9)))
    all_caption_lines = wrap_text(caption, max(10, int(width / 7)))
    label_lines = ellipsized_lines(all_label_lines, 2, max(8, int(width / 9)))
    available_caption_height = max(
        0.0,
        height - TEXT_VERTICAL_PADDING * 2 - len(label_lines) * LABEL_LINE_HEIGHT,
    )
    caption_limit = max(0, min(2, int(available_caption_height // CAPTION_LINE_HEIGHT)))
    caption_lines = ellipsized_lines(all_caption_lines, caption_limit, max(10, int(width / 7)), truncate_long=True)
    total_height = len(label_lines) * LABEL_LINE_HEIGHT + len(caption_lines) * CAPTION_LINE_HEIGHT
    usable_height = max(0.0, height - TEXT_VERTICAL_PADDING * 2)
    top = TEXT_VERTICAL_PADDING + max(0.0, (usable_height - total_height) / 2.0)
    first_baseline = top + 12.0
    return TextBlockLayout(
        label_lines=label_lines,
        caption_lines=caption_lines,
        all_label_lines=len(all_label_lines),
        all_caption_lines=len(all_caption_lines),
        caption_truncated=tuple(all_caption_lines) != caption_lines,
        first_baseline=first_baseline,
        total_height=total_height,
    )


def ellipsized_lines(lines, limit, max_units, truncate_long=False):
    visible = list(lines[:limit])
    if truncate_long:
        for index, line in enumerate(visible):
            if visual_units(line) > max_units:
                while line and visual_units(line + "…") > max_units:
                    line = line[:-1]
                visible[index] = line.rstrip() + "…"
    if visible and len(lines) > limit:
        last = visible[-1].rstrip()
        while last and visual_units(last + "…") > max_units:
            last = last[:-1]
        visible[-1] = last.rstrip() + "…"
    return tuple(visible)


def node_text_vertical_region(height, decision=False):
    """Decision text occupies the center band below its separate icon zone."""
    return (height * 0.31, height * 0.52) if decision else (0.0, height)
