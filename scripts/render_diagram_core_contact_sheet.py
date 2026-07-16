#!/usr/bin/env python3
"""Render deterministic Diagram Core static review surfaces."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Optional, Sequence, Tuple
from xml.etree import ElementTree

from anidiagram.diagram_core.adapter import render_preview_icon
from anidiagram.diagram_core.tokens import token_css


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets" / "diagram-core"
ICON_ID = "agent"
BENCHMARK_ICONS = ("agent", "database", "api", "server")
SIZES = (48, 64, 96)
CONTEXTS = ("blue", "dark", "warm", "green")
STATES = ("idle", "active", "processing", "success", "warning", "error")
ASSET_LOCAL_TOKENS = frozenset({"--icon-surface-contrast"})
SHEET_WIDTH = 1120
SHEET_HEIGHT = 2496
CELL_X = 40
CELL_STEP_X = 174
CELL_WIDTH = 158
CELL_HEIGHT = 146
MAIN_Y = 128
ROW_STEP_Y = 160
BENCHMARK_COLUMNS = len(BENCHMARK_ICONS) * len(SIZES)
BENCHMARK_ROWS = len(CONTEXTS) * len(STATES)
BENCHMARK_CELL_SIZE = 104
BENCHMARK_WIDTH = BENCHMARK_COLUMNS * BENCHMARK_CELL_SIZE
BENCHMARK_HEIGHT = BENCHMARK_ROWS * BENCHMARK_CELL_SIZE
_HEX_COLOR = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_RGB_COLOR = re.compile(
    r"^rgb\(\s*(\d{1,3})(?:\s*,\s*|\s+)(\d{1,3})"
    r"(?:\s*,\s*|\s+)(\d{1,3})\s*\)$",
    re.IGNORECASE,
)
_SIMPLE_VAR = re.compile(r"^var\(\s*(--[a-z0-9-]+)\s*\)$")


@dataclass(frozen=True)
class ContactSheetCell:
    ordinal: int
    column: int
    row: int
    icon_id: str
    size: int
    context: str
    state: str
    cell_id: str
    instance_id: str


@dataclass(frozen=True)
class _OutputRecord:
    target: Path
    payload: bytes
    resolved_key: str
    parent_identity: Tuple[int, int]
    target_signature: Optional[Tuple[int, int, int, int, int]]
    original_bytes: Optional[bytes]
    mode: int

    @property
    def existed(self) -> bool:
        return self.target_signature is not None


def _declarations(source: str, selector: str) -> Dict[str, str]:
    match = re.search(re.escape(selector) + r"\s*\{([^{}]*)\}", source)
    if match is None:
        raise ValueError("tokens.css is missing selector " + selector)
    declarations: Dict[str, str] = {}
    for statement in match.group(1).split(";"):
        if ":" not in statement:
            continue
        name, value = statement.split(":", 1)
        name = name.strip()
        if name.startswith("--icon-"):
            declarations[name] = value.strip()
    if not declarations:
        raise ValueError("tokens.css selector has no icon declarations: " + selector)
    return declarations


def _context_tokens(source: str) -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
    defaults = _declarations(source, ":root")
    contexts: Dict[str, Dict[str, str]] = {}
    for context in CONTEXTS:
        resolved = dict(defaults)
        resolved.update(
            _declarations(source, '[data-icon-theme="' + context + '"]')
        )
        contexts[context] = resolved
    return defaults, contexts


def _resolved_reference(value: str, tokens: Mapping[str, str]) -> str:
    match = _SIMPLE_VAR.fullmatch(value)
    if match is None:
        return value
    referenced = match.group(1)
    if referenced not in tokens:
        raise ValueError("unresolved token reference: " + referenced)
    resolved = tokens[referenced]
    if _SIMPLE_VAR.fullmatch(resolved):
        return _resolved_reference(resolved, tokens)
    return resolved


def _accent_off_tokens(
    source: str,
    base_tokens: Mapping[str, str],
) -> Dict[str, str]:
    resolved = dict(base_tokens)
    overrides = _declarations(source, '[data-icon-accent="off"]')
    for token, value in overrides.items():
        resolved[token] = _resolved_reference(value, resolved)
    return resolved


def _rgb_channels(color: str) -> Tuple[int, int, int]:
    match = _HEX_COLOR.fullmatch(color)
    if match is not None:
        value = match.group(1)
        if len(value) == 3:
            value = "".join(channel * 2 for channel in value)
        return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))
    match = _RGB_COLOR.fullmatch(color)
    if match is None:
        raise ValueError("unsupported review color: " + color)
    channels = tuple(int(value) for value in match.groups())
    if any(value > 255 for value in channels):
        raise ValueError("review rgb channels must be at most 255")
    return channels


def _grayscale_tokens(tokens: Mapping[str, str]) -> Dict[str, str]:
    grayscale = {}
    for token, color in tokens.items():
        red, green, blue = _rgb_channels(color)
        gray = round(0.2126 * red + 0.7152 * green + 0.0722 * blue)
        grayscale[token] = "#{0:02x}{0:02x}{0:02x}".format(gray)
    return grayscale


def _escaped(value: object) -> str:
    return html.escape(str(value), quote=True)


def _asset_local_style(tokens: Mapping[str, str]) -> str:
    local_tokens = {
        token: value
        for token, value in tokens.items()
        if token in ASSET_LOCAL_TOKENS
    }
    if set(local_tokens) != ASSET_LOCAL_TOKENS:
        raise ValueError("tokens.css is missing an asset-local review token")
    return ";".join(
        "{0}:{1}".format(token, local_tokens[token])
        for token in sorted(local_tokens)
    )


def _preview(
    instance_id: str,
    state: str,
    size: int,
    x: float,
    y: float,
    tokens: Mapping[str, str],
) -> str:
    adapter_tokens = {
        token: value
        for token, value in tokens.items()
        if token not in ASSET_LOCAL_TOKENS
    }
    return render_preview_icon(
        ICON_ID,
        instance_id,
        state=state,
        size=size,
        x=x,
        y=y,
        tokens=adapter_tokens,
        asset_root=ASSET_ROOT,
    )


def _main_cell(
    size: int,
    context: str,
    state: str,
    column: int,
    row: int,
    tokens: Mapping[str, str],
) -> str:
    x = CELL_X + column * CELL_STEP_X
    y = MAIN_Y + row * ROW_STEP_Y
    icon_x = x + (CELL_WIDTH - size) / 2
    icon_y = y + 36
    cell_id = "agent-{0}-{1}-{2}".format(size, context, state)
    label = "{0}px · {1} · {2}".format(size, context, state)
    preview = _preview(
        "contact.main.{0}.{1}.{2}".format(size, context, state),
        state,
        size,
        icon_x,
        icon_y,
        tokens,
    )
    return """  <g data-cell-kind="main" data-cell-id="{cell_id}" data-icon-id="agent" data-size="{size}" data-context="{context}" data-state="{state}" style="{local_style}">
    <rect x="{x}" y="{y}" width="{width}" height="{height}" rx="14" fill="{surface}" stroke="{stroke}" stroke-width="1"/>
    <text x="{label_x}" y="{label_y}" fill="{stroke}" font-size="11" font-weight="650">{label}</text>
{preview}
  </g>""".format(
        cell_id=_escaped(cell_id),
        size=size,
        context=_escaped(context),
        state=_escaped(state),
        local_style=_escaped(_asset_local_style(tokens)),
        x=x,
        y=y,
        width=CELL_WIDTH,
        height=CELL_HEIGHT,
        surface=_escaped(tokens["--icon-surface-main"]),
        stroke=_escaped(tokens["--icon-stroke"]),
        label_x=x + 12,
        label_y=y + 21,
        label=_escaped(label),
        preview=preview,
    )


def _recognition_row(
    mode: str,
    row_y: int,
    tokens: Mapping[str, str],
) -> str:
    cells = []
    compact_mode = "off" if mode == "accent-off" else "gray"
    for column, state in enumerate(STATES):
        x = CELL_X + column * CELL_STEP_X
        size = 48
        icon_x = x + (CELL_WIDTH - size) / 2
        icon_y = row_y + 38
        cell_id = "agent-recognition-{0}-{1}".format(mode, state)
        preview = _preview(
            "contact.recognition.{0}.{1}".format(mode, state),
            state,
            size,
            icon_x,
            icon_y,
            tokens,
        )
        cells.append(
            """    <g data-cell-kind="recognition" data-cell-id="{cell_id}" data-icon-id="agent" data-recognition-mode="{mode}" data-size="48" data-context="blue" data-state="{state}" style="{local_style}">
      <rect x="{x}" y="{y}" width="{width}" height="{height}" rx="14" fill="{surface}" stroke="{stroke}" stroke-width="1"/>
      <text x="{label_x}" y="{label_y}" fill="{stroke}" font-size="11" font-weight="650">{label}</text>
{preview}
    </g>""".format(
                cell_id=_escaped(cell_id),
                mode=_escaped(mode),
                state=_escaped(state),
                local_style=_escaped(_asset_local_style(tokens)),
                x=x,
                y=row_y,
                width=CELL_WIDTH,
                height=CELL_HEIGHT,
                surface=_escaped(tokens["--icon-surface-main"]),
                stroke=_escaped(tokens["--icon-stroke"]),
                label_x=x + 12,
                label_y=row_y + 21,
                label=_escaped("48px · {0} · {1}".format(compact_mode, state)),
                preview=preview,
            )
        )
    return """  <g data-recognition-row="{mode}">
{cells}
  </g>""".format(mode=_escaped(mode), cells="\n".join(cells))


def render_contact_sheet() -> str:
    source = token_css()
    defaults, contexts = _context_tokens(source)
    state_rules = "\n".join(
        '[data-icon-state="{0}"] [data-state-mark="{0}"] {{ display: inline; }}'.format(
            state
        )
        for state in STATES
    )
    cells = []
    for context_index, context in enumerate(CONTEXTS):
        for size_index, size in enumerate(SIZES):
            row = context_index * len(SIZES) + size_index
            for column, state in enumerate(STATES):
                cells.append(
                    _main_cell(
                        size,
                        context,
                        state,
                        column,
                        row,
                        contexts[context],
                    )
                )

    accent_off = _accent_off_tokens(source, contexts["blue"])
    grayscale = _grayscale_tokens(contexts["blue"])
    recognition_rows = (
        _recognition_row("accent-off", 2116, accent_off),
        _recognition_row("grayscale", 2276, grayscale),
    )
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="Agent icon benchmark across sizes, contexts, states, accent-off, and grayscale recognition" data-icon-review="true" data-main-cell-count="72" data-recognition-cell-count="12">
  <title>Agent static icon benchmark contact sheet</title>
  <style>
[data-state-mark] {{ display: none; }}
{state_rules}
text {{ font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  </style>
  <rect x="0" y="0" width="{width}" height="{height}" fill="{background}"/>
  <text x="40" y="51" fill="{heading}" font-size="28" font-weight="750">Agent benchmark · 72-cell audit matrix</text>
  <text x="40" y="82" fill="{heading}" font-size="14">3 sizes × 4 token contexts × 6 geometric states · deterministic static output</text>
  <text x="40" y="2090" fill="{heading}" font-size="20" font-weight="700">48 px recognition checks · accent-off and grayscale</text>
{cells}
{recognition_rows}
</svg>
""".format(
        width=SHEET_WIDTH,
        height=SHEET_HEIGHT,
        background=_escaped(defaults["--icon-surface-secondary"]),
        heading=_escaped(defaults["--icon-stroke"]),
        state_rules=state_rules,
        cells="\n".join(cells),
        recognition_rows="\n".join(recognition_rows),
    )


def render_review_html(
    contact_reference: str,
    contact_digest: str,
    tokens: Mapping[str, str],
) -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent static icon review · AniDiagram</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: {page}; color: {text}; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.55; }}
    header, main {{ width: min(1180px, calc(100% - 40px)); margin-inline: auto; }}
    header {{ padding: 48px 0 24px; border-bottom: 1px solid {border}; }}
    main {{ padding: 28px 0 64px; }}
    section + section {{ margin-top: 32px; }}
    h1, h2, p {{ margin-top: 0; }}
    h1 {{ margin-bottom: 10px; font-size: clamp(2rem, 5vw, 3.5rem); line-height: 1.05; letter-spacing: -0.035em; }}
    h2 {{ margin-bottom: 12px; font-size: 1.3rem; }}
    .eyebrow {{ margin-bottom: 12px; color: {text}; font-size: 0.78rem; font-weight: 750; letter-spacing: 0.11em; text-transform: uppercase; }}
    .lede, figcaption, .scope {{ color: {text}; }}
    figure {{ margin: 0; }}
    img {{ display: block; width: 100%; height: auto; border: 1px solid {border}; border-radius: 18px; background: {card}; }}
    figcaption {{ margin-top: 10px; font-size: 0.92rem; }}
    ul {{ margin: 0; padding-left: 1.35rem; }}
    li + li {{ margin-top: 9px; }}
    code {{ overflow-wrap: anywhere; color: {text}; }}
  </style>
</head>
<body>
  <header>
    <p class="eyebrow">AniDiagram Diagram Core</p>
    <h1>Agent static icon review</h1>
    <p class="lede">A fixed, non-interactive audit surface for the first Diagram Core benchmark. The matrix does not animate and does not load network resources.</p>
  </header>
  <main>
    <section>
      <h2>Contact sheet</h2>
      <figure>
        <img src="{contact_reference}" alt="Agent robot icon shown at 48, 64, and 96 pixels in four color contexts and six geometric states, followed by accent-off and grayscale recognition rows.">
        <figcaption>72 primary cells plus two six-state recognition rows. Contact sheet SHA-256: <code>{contact_digest}</code>.</figcaption>
      </figure>
    </section>
    <section>
      <h2>Manual review checklist</h2>
      <ul>
        <li><strong>48 px recognition:</strong> the robot reads immediately without relying on the label.</li>
        <li><strong>Silhouette and visual weight:</strong> the capsule shell remains dominant and visually balanced.</li>
        <li><strong>Face readability:</strong> both eyes and the simple mouth remain distinct at the smallest size.</li>
        <li><strong>Accent-off recognition:</strong> identity survives when accent tokens collapse to neutral colors.</li>
        <li><strong>Four contexts:</strong> compare blue, dark, warm, and green token declarations.</li>
        <li><strong>Six state marks:</strong> idle, active, processing, success, warning, and error differ by geometry.</li>
      </ul>
    </section>
    <section>
      <h2>Review scope</h2>
      <p class="scope">Judge only the static Agent candidate and its recognition matrix. This page is generated from the canonical asset through the preview adapter; labels belong to the review surface, not the icon asset.</p>
    </section>
  </main>
</body>
</html>
""".format(
        page=_escaped(tokens["--icon-surface-secondary"]),
        card=_escaped(tokens["--icon-surface-main"]),
        text=_escaped(tokens["--icon-stroke"]),
        border=_escaped(tokens["--icon-surface-recessed"]),
        contact_reference=_escaped(contact_reference),
        contact_digest=_escaped(contact_digest),
    )


def build_contact_sheet_cells(
    icons: Sequence[str] = BENCHMARK_ICONS,
) -> Tuple[ContactSheetCell, ...]:
    """Return the locked row-major 12-column by 24-row benchmark matrix."""

    normalized_icons = tuple(icons)
    if normalized_icons != BENCHMARK_ICONS:
        raise ValueError(
            "benchmark icons must be agent,database,api,server in canonical order"
        )
    cells = []
    ordinal = 0
    for context_index, context in enumerate(CONTEXTS):
        for state_index, state in enumerate(STATES):
            row = context_index * len(STATES) + state_index
            for icon_index, icon_id in enumerate(normalized_icons):
                for size_index, size in enumerate(SIZES):
                    column = icon_index * len(SIZES) + size_index
                    cell_id = "{0}-{1}-{2}-{3}".format(
                        icon_id,
                        size,
                        context,
                        state,
                    )
                    cells.append(
                        ContactSheetCell(
                            ordinal=ordinal,
                            column=column,
                            row=row,
                            icon_id=icon_id,
                            size=size,
                            context=context,
                            state=state,
                            cell_id=cell_id,
                            instance_id="benchmark.{0}.{1}.{2}.{3}.{4}".format(
                                ordinal,
                                icon_id,
                                size,
                                context,
                                state,
                            ),
                        )
                    )
                    ordinal += 1
    return tuple(cells)


def _static_preview(
    icon_id: str,
    instance_id: str,
    state: str,
    size: int,
    x: float,
    y: float,
    tokens: Mapping[str, str],
) -> str:
    """Render through the adapter, then freeze the requested state as attributes."""

    adapter_tokens = {
        token: value
        for token, value in tokens.items()
        if token not in ASSET_LOCAL_TOKENS
    }
    fragment = render_preview_icon(
        icon_id,
        instance_id,
        state=state,
        size=size,
        x=x,
        y=y,
        tokens=adapter_tokens,
        asset_root=ASSET_ROOT,
    )
    root = ElementTree.fromstring(fragment)
    for element in root.iter():
        mark = element.attrib.get("data-state-mark")
        if mark is not None:
            element.set("display", "inline" if mark == state else "none")
    return ElementTree.tostring(
        root,
        encoding="unicode",
        short_empty_elements=True,
    )


def _benchmark_cell(
    cell: ContactSheetCell,
    tokens: Mapping[str, str],
) -> str:
    x = cell.column * BENCHMARK_CELL_SIZE
    y = cell.row * BENCHMARK_CELL_SIZE
    icon_x = x + (BENCHMARK_CELL_SIZE - cell.size) / 2
    icon_y = y + (BENCHMARK_CELL_SIZE - cell.size) / 2
    preview = _static_preview(
        cell.icon_id,
        cell.instance_id,
        cell.state,
        cell.size,
        icon_x,
        icon_y,
        tokens,
    )
    return """  <g data-cell-kind="regression" data-cell-id="{cell_id}" data-icon-id="{icon_id}" data-size="{size}" data-context="{context}" data-state="{state}" role="img" aria-label="{label}" style="{local_style}">
    <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{surface}" stroke="{border}" stroke-width="1"/>
{preview}
  </g>""".format(
        cell_id=_escaped(cell.cell_id),
        icon_id=_escaped(cell.icon_id),
        size=cell.size,
        context=_escaped(cell.context),
        state=_escaped(cell.state),
        label=_escaped(
            "{0} icon, {1} pixels, {2} context, {3} state".format(
                cell.icon_id,
                cell.size,
                cell.context,
                cell.state,
            )
        ),
        local_style=_escaped(_asset_local_style(tokens)),
        x=x,
        y=y,
        cell_size=BENCHMARK_CELL_SIZE,
        surface=_escaped(tokens["--icon-surface-main"]),
        border=_escaped(tokens["--icon-surface-recessed"]),
        preview=preview,
    )


def render_benchmark_contact_sheet(
    cells: Sequence[ContactSheetCell] = None,
    aria_labelledby: str = "",
) -> str:
    """Render the fixed, text-free locator used by the later pixel gate."""

    ordered_cells = (
        build_contact_sheet_cells() if cells is None else tuple(cells)
    )
    if len(ordered_cells) != BENCHMARK_COLUMNS * BENCHMARK_ROWS:
        raise ValueError("benchmark contact sheet requires exactly 288 cells")
    source = token_css()
    _, contexts = _context_tokens(source)
    rendered_cells = [
        _benchmark_cell(cell, contexts[cell.context]) for cell in ordered_cells
    ]
    labelledby = (
        ' aria-labelledby="{0}"'.format(_escaped(aria_labelledby))
        if aria_labelledby
        else ""
    )
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" id="diagram-core-regression-grid" role="img" aria-label="Diagram Core benchmark: four icons, three sizes, four contexts, and six static states"{labelledby} data-icon-review-region="true" data-grid-columns="{columns}" data-grid-rows="{rows}" data-cell-count="{count}">
{cells}
</svg>
""".format(
        width=BENCHMARK_WIDTH,
        height=BENCHMARK_HEIGHT,
        labelledby=labelledby,
        columns=BENCHMARK_COLUMNS,
        rows=BENCHMARK_ROWS,
        count=len(ordered_cells),
        cells="\n".join(rendered_cells),
    )


def render_cell_index(
    cells: Sequence[ContactSheetCell] = None,
) -> str:
    ordered_cells = (
        build_contact_sheet_cells() if cells is None else tuple(cells)
    )
    payload = {
        "version": 1,
        "grid": {
            "columns": BENCHMARK_COLUMNS,
            "rows": BENCHMARK_ROWS,
            "cells": len(ordered_cells),
        },
        "cells": [
            {
                "ordinal": cell.ordinal,
                "cell_id": cell.cell_id,
                "icon_id": cell.icon_id,
                "size": cell.size,
                "context": cell.context,
                "state": cell.state,
            }
            for cell in ordered_cells
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def _legend_items(values: Sequence[str]) -> str:
    return "\n".join("        <li>{0}</li>".format(_escaped(value)) for value in values)


def render_benchmark_review_html(
    contact_digest: str,
    tokens: Mapping[str, str],
    cells: Sequence[ContactSheetCell] = None,
) -> str:
    ordered_cells = (
        build_contact_sheet_cells() if cells is None else tuple(cells)
    )
    embedded_grid = render_benchmark_contact_sheet(
        ordered_cells,
        aria_labelledby="diagram-core-grid-title diagram-core-grid-description",
    ).rstrip()
    column_labels = [
        "{0} · {1} px".format(icon_id, size)
        for icon_id in BENCHMARK_ICONS
        for size in SIZES
    ]
    row_labels = [
        "{0} · {1}".format(context, state)
        for context in CONTEXTS
        for state in STATES
    ]
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Diagram Core static regression matrix · AniDiagram</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: {page}; color: {text}; font-family: ui-sans-serif, system-ui, sans-serif; line-height: 1.5; }}
    header, main {{ width: max-content; min-width: {width}px; margin-inline: auto; }}
    header {{ width: {width}px; padding: 40px 0 24px; }}
    h1, h2, p {{ margin-top: 0; }}
    h1 {{ margin-bottom: 8px; font-size: 36px; }}
    .legends {{ width: {width}px; display: grid; grid-template-columns: 1fr 1fr; gap: 32px; padding: 20px; border: 1px solid {border}; background: {card}; }}
    .legends ol {{ margin: 0; padding-left: 24px; columns: 2; }}
    .legends li {{ break-inside: avoid; margin-bottom: 4px; }}
    .grid-shell {{ width: {width}px; margin: 24px 0 64px; }}
    #diagram-core-regression-grid {{ display: block; width: {width}px; height: {height}px; }}
    code {{ overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <header>
    <h1 id="diagram-core-grid-title">Diagram Core static regression matrix</h1>
    <p id="diagram-core-grid-description">A fixed 12-column by 24-row, 288-cell visual review surface. The screenshot locator contains icon geometry only; all labels and legends remain outside it.</p>
    <p>Contact sheet SHA-256: <code>{digest}</code>.</p>
  </header>
  <main>
    <section class="legends" aria-label="Regression grid legends">
      <div>
        <h2>Column legend</h2>
        <ol data-grid-legend="columns">
{column_items}
        </ol>
      </div>
      <div>
        <h2>Row legend</h2>
        <ol data-grid-legend="rows">
{row_items}
        </ol>
      </div>
    </section>
    <section class="grid-shell" aria-label="Text-free regression crop">
{grid}
    </section>
  </main>
</body>
</html>
""".format(
        page=_escaped(tokens["--icon-surface-secondary"]),
        card=_escaped(tokens["--icon-surface-main"]),
        text=_escaped(tokens["--icon-stroke"]),
        border=_escaped(tokens["--icon-surface-recessed"]),
        width=BENCHMARK_WIDTH,
        height=BENCHMARK_HEIGHT,
        digest=_escaped(contact_digest),
        column_items=_legend_items(column_labels),
        row_items=_legend_items(row_labels),
        grid=embedded_grid,
    )


def _recognition_cell(
    mode: str,
    icon_id: str,
    state: str,
    tokens: Mapping[str, str],
) -> str:
    size = 48
    offset = (BENCHMARK_CELL_SIZE - size) / 2
    cell_id = "recognition-{0}-{1}-{2}".format(mode, icon_id, state)
    preview = _static_preview(
        icon_id,
        "recognition.{0}.{1}.{2}".format(mode, icon_id, state),
        state,
        size,
        offset,
        offset,
        tokens,
    )
    return """        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cell_size} {cell_size}" width="{cell_size}" height="{cell_size}" role="img" aria-label="{label}" data-cell-kind="recognition" data-cell-id="{cell_id}" data-icon-id="{icon_id}" data-recognition-mode="{mode}" data-size="48" data-context="blue" data-state="{state}" style="{local_style}">
          <rect x="0" y="0" width="{cell_size}" height="{cell_size}" fill="{surface}" stroke="{border}" stroke-width="1"/>
{preview}
        </svg>""".format(
        cell_size=BENCHMARK_CELL_SIZE,
        label=_escaped(
            "{0} icon, {1} state, {2} recognition view, 48 pixels".format(
                icon_id,
                state,
                mode,
            )
        ),
        cell_id=_escaped(cell_id),
        icon_id=_escaped(icon_id),
        mode=_escaped(mode),
        state=_escaped(state),
        local_style=_escaped(_asset_local_style(tokens)),
        surface=_escaped(tokens["--icon-surface-main"]),
        border=_escaped(tokens["--icon-surface-recessed"]),
        preview=preview,
    )


def render_recognition_html(
    token_source: str,
    contexts: Mapping[str, Mapping[str, str]],
) -> str:
    blue = contexts["blue"]
    modes = (
        ("label-hidden", blue),
        ("accent-off", _accent_off_tokens(token_source, blue)),
        ("grayscale", _grayscale_tokens(blue)),
        ("node-context", blue),
    )
    mode_groups = []
    for mode, tokens in modes:
        cells = [
            _recognition_cell(mode, icon_id, state, tokens)
            for state in STATES
            for icon_id in BENCHMARK_ICONS
        ]
        mode_groups.append(
            """      <div class="recognition-mode" role="group" aria-label="{label}" data-recognition-group="{mode}">
{cells}
      </div>""".format(
                label=_escaped(mode.replace("-", " ") + " recognition checks"),
                mode=_escaped(mode),
                cells="\n".join(cells),
            )
        )
    legend = _legend_items(
        (
            "label-hidden · normal blue-context silhouettes at 48 px",
            "accent-off · accent tokens collapsed to neutral roles",
            "grayscale · luminance-only recognition",
            "node-context · four icons in one fixed blue node context for visual-weight comparison",
        )
    )
    defaults, _ = _context_tokens(token_source)
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Diagram Core recognition review · AniDiagram</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: {page}; color: {text}; font-family: ui-sans-serif, system-ui, sans-serif; line-height: 1.5; }}
    header, main {{ width: 864px; margin-inline: auto; }}
    header {{ padding: 40px 0 20px; }}
    h1, h2, p {{ margin-top: 0; }}
    h1 {{ margin-bottom: 8px; font-size: 36px; }}
    .mode-legend {{ margin: 0 0 24px; padding: 20px 20px 20px 44px; border: 1px solid {border}; background: {card}; }}
    .review-grid {{ width: 864px; display: grid; grid-template-columns: repeat(2, 416px); gap: 32px; padding-bottom: 64px; }}
    .recognition-mode {{ display: grid; grid-template-columns: repeat(4, {cell_size}px); width: 416px; }}
    .recognition-mode svg {{ display: block; width: {cell_size}px; height: {cell_size}px; }}
  </style>
</head>
<body>
  <header>
    <h1 id="diagram-core-recognition-title">Diagram Core recognition review</h1>
    <p id="diagram-core-recognition-description">Four label-free 48 px review modes. Every cell has an accessible name while the review region contains no visible labels.</p>
    <h2>Mode legend</h2>
    <ul class="mode-legend" data-recognition-legend="modes">
{legend}
    </ul>
  </header>
  <main>
    <div id="diagram-core-recognition-grid" class="review-grid" role="group" aria-labelledby="diagram-core-recognition-title diagram-core-recognition-description" data-icon-review-region="true">
{groups}
    </div>
  </main>
</body>
</html>
""".format(
        page=_escaped(defaults["--icon-surface-secondary"]),
        card=_escaped(defaults["--icon-surface-main"]),
        text=_escaped(defaults["--icon-stroke"]),
        border=_escaped(defaults["--icon-surface-recessed"]),
        cell_size=BENCHMARK_CELL_SIZE,
        legend=legend,
        groups="\n".join(mode_groups),
    )


def _lexical_path_key(path: Path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def _resolved_path_key(path: Path) -> str:
    try:
        resolved = path.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise ValueError(
            "cannot resolve output path {0}: {1}".format(path, error)
        ) from error
    return os.path.normcase(os.path.abspath(os.fspath(resolved)))


def _lstat_or_none(path: Path):
    try:
        return path.lstat()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise ValueError(
            "cannot inspect output path {0}: {1}".format(path, error)
        ) from error


def _validated_target_info(path: Path):
    info = _lstat_or_none(path)
    if info is None:
        return None
    if stat.S_ISLNK(info.st_mode):
        raise ValueError("output targets must not be symbolic links: " + str(path))
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("output targets must be regular files: " + str(path))
    return info


def _validate_existing_parent(path: Path) -> None:
    candidate = path.parent
    while not os.path.lexists(os.fspath(candidate)):
        parent = candidate.parent
        if parent == candidate:
            raise ValueError("output path has no existing directory ancestor: " + str(path))
        candidate = parent
    try:
        info = candidate.stat()
    except OSError as error:
        raise ValueError(
            "cannot inspect output parent {0}: {1}".format(candidate, error)
        ) from error
    if not stat.S_ISDIR(info.st_mode):
        raise ValueError("output parent must be a directory: " + str(candidate))


def _validate_output_paths(paths: Sequence[Path]) -> Tuple[Path, ...]:
    targets = tuple(Path(path) for path in paths)
    if not targets:
        raise ValueError("at least one output path is required")

    lexical_keys = [_lexical_path_key(path) for path in targets]
    if len(set(lexical_keys)) != len(lexical_keys):
        raise ValueError("output files must use lexically distinct paths")

    target_infos = []
    resolved_keys = []
    for target in targets:
        _validate_existing_parent(target)
        target_infos.append(_validated_target_info(target))
        resolved_keys.append(_resolved_path_key(target))
    if len(set(resolved_keys)) != len(resolved_keys):
        raise ValueError("output files must resolve to distinct paths")

    for left_index, left in enumerate(targets):
        if target_infos[left_index] is None:
            continue
        for right_index in range(left_index + 1, len(targets)):
            if target_infos[right_index] is None:
                continue
            try:
                aliases = os.path.samefile(left, targets[right_index])
            except OSError as error:
                raise ValueError(
                    "cannot compare output identities: {0}".format(error)
                ) from error
            if aliases:
                raise ValueError("output files must not be hardlink aliases")
    return targets


def _stat_signature(info) -> Tuple[int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_size,
        info.st_mtime_ns,
    )


def _read_original_bytes(path: Path, expected_info) -> bytes:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(os.fspath(path), flags)
    try:
        handle = os.fdopen(descriptor, "rb")
        descriptor = -1
        with handle:
            before = os.fstat(handle.fileno())
            if _stat_signature(before) != _stat_signature(expected_info):
                raise RuntimeError("output changed while being snapshotted: " + str(path))
            payload = handle.read()
            after = os.fstat(handle.fileno())
            if _stat_signature(after) != _stat_signature(expected_info):
                raise RuntimeError("output changed while being snapshotted: " + str(path))
            return payload
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _snapshot_output(target: Path, payload: bytes) -> _OutputRecord:
    parent_info = target.parent.stat()
    if not stat.S_ISDIR(parent_info.st_mode):
        raise ValueError("output parent must be a directory: " + str(target.parent))
    target_info = _validated_target_info(target)
    if target_info is None:
        signature = None
        original_bytes = None
        mode = 0o644
    else:
        signature = _stat_signature(target_info)
        original_bytes = _read_original_bytes(target, target_info)
        mode = stat.S_IMODE(target_info.st_mode)
    return _OutputRecord(
        target=target,
        payload=payload,
        resolved_key=_resolved_path_key(target),
        parent_identity=(parent_info.st_dev, parent_info.st_ino),
        target_signature=signature,
        original_bytes=original_bytes,
        mode=mode,
    )


def _assert_output_unchanged(record: _OutputRecord) -> None:
    if _resolved_path_key(record.target) != record.resolved_key:
        raise RuntimeError("output path resolution changed before publish")
    parent_info = record.target.parent.stat()
    if (
        not stat.S_ISDIR(parent_info.st_mode)
        or (parent_info.st_dev, parent_info.st_ino) != record.parent_identity
    ):
        raise RuntimeError("output parent changed before publish")
    current = _validated_target_info(record.target)
    if record.target_signature is None:
        if current is not None:
            raise RuntimeError("new output appeared before publish: " + str(record.target))
    elif current is None or _stat_signature(current) != record.target_signature:
        raise RuntimeError("existing output changed before publish: " + str(record.target))


def _write_staged_file(
    target: Path,
    payload: bytes,
    mode: int,
    suffix: str,
    mtime_ns: Optional[int] = None,
) -> Tuple[Path, Tuple[int, int, int, int, int]]:
    descriptor, temp_name = tempfile.mkstemp(
        prefix=".{0}.".format(target.name),
        suffix=suffix,
        dir=os.fspath(target.parent),
    )
    temp_path = Path(temp_name)
    try:
        handle = os.fdopen(descriptor, "wb")
        descriptor = -1
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, mode)
        if mtime_ns is not None:
            os.utime(temp_path, ns=(mtime_ns, mtime_ns))
        info = temp_path.lstat()
        return temp_path, _stat_signature(info)
    except BaseException:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
        raise
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _cleanup_temp(path: Optional[Path]) -> None:
    if path is None:
        return
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _rollback_outputs(
    records: Sequence[_OutputRecord],
    backups: Dict[Path, Optional[Path]],
    staged_signatures: Mapping[Path, Tuple[int, int, int, int, int]],
) -> Tuple[str, ...]:
    def matches_snapshot(
        record: _OutputRecord,
        current,
        signature: Optional[Tuple[int, int, int, int, int]],
        payload: Optional[bytes],
    ) -> bool:
        if (
            current is None
            or signature is None
            or payload is None
            or not stat.S_ISREG(current.st_mode)
            or _stat_signature(current) != signature
        ):
            return False
        try:
            return _read_original_bytes(record.target, current) == payload
        except (OSError, RuntimeError, ValueError):
            return False

    def preserve_backup(record: _OutputRecord, reason: str) -> str:
        backup = backups.get(record.target)
        if backup is not None and os.path.lexists(os.fspath(backup)):
            backups[record.target] = None
            return "{0}; original backup preserved at {1}".format(reason, backup)
        return reason

    errors = []
    for record in reversed(tuple(records)):
        try:
            current = _lstat_or_none(record.target)
            original_matches = (
                current is None
                if not record.existed
                else matches_snapshot(
                    record,
                    current,
                    record.target_signature,
                    record.original_bytes,
                )
            )
            if original_matches:
                continue
            staged_matches = matches_snapshot(
                record,
                current,
                staged_signatures[record.target],
                record.payload,
            )
            if not staged_matches:
                errors.append(
                    "{0}: {1}".format(
                        record.target,
                        preserve_backup(
                            record,
                            "rollback conflict: current output is neither the original snapshot nor the staged payload",
                        ),
                    )
                )
                continue
            if record.existed:
                backup = backups.get(record.target)
                if backup is None or not os.path.lexists(os.fspath(backup)):
                    raise RuntimeError("rollback backup is missing")
                os.replace(os.fspath(backup), os.fspath(record.target))
                backups[record.target] = None
            else:
                record.target.unlink()
        except Exception as error:
            errors.append(
                "{0}: {1}".format(
                    record.target,
                    preserve_backup(record, str(error)),
                )
            )
    return tuple(errors)


def _publish_outputs(outputs: Sequence[Tuple[Path, bytes]]) -> None:
    ordered = []
    for target, payload in outputs:
        if not isinstance(payload, bytes):
            raise TypeError("published output payloads must be bytes")
        ordered.append((Path(target), payload))
    targets = _validate_output_paths(tuple(target for target, _ in ordered))
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
    _validate_output_paths(targets)
    records = tuple(
        _snapshot_output(target, payload) for target, payload in ordered
    )

    staged: Dict[Path, Optional[Path]] = {}
    staged_signatures: Dict[Path, Tuple[int, int, int, int, int]] = {}
    backups: Dict[Path, Optional[Path]] = {}
    attempted = []
    try:
        for record in records:
            staged_path, staged_signature = _write_staged_file(
                record.target,
                record.payload,
                record.mode,
                ".tmp",
            )
            staged[record.target] = staged_path
            staged_signatures[record.target] = staged_signature
        for record in records:
            if record.existed:
                backup_path, _ = _write_staged_file(
                    record.target,
                    record.original_bytes,
                    record.mode,
                    ".bak",
                    record.target_signature[4],
                )
                backups[record.target] = backup_path
            else:
                backups[record.target] = None

        for record in records:
            _assert_output_unchanged(record)
        for record in records:
            _assert_output_unchanged(record)
            staged_path = staged[record.target]
            if staged_path is None:
                raise RuntimeError("staged output disappeared before publish")
            attempted.append(record)
            os.replace(os.fspath(staged_path), os.fspath(record.target))
            staged[record.target] = None
    except BaseException as publish_error:
        rollback_errors = ()
        if attempted:
            rollback_errors = _rollback_outputs(
                attempted,
                backups,
                staged_signatures,
            )
        if rollback_errors:
            raise RuntimeError(
                "output publication failed and rollback was incomplete: "
                + "; ".join(rollback_errors)
            ) from publish_error
        raise
    finally:
        for path in staged.values():
            _cleanup_temp(path)
        for path in backups.values():
            _cleanup_temp(path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render static Diagram Core review surfaces."
    )
    parser.add_argument("--icons", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--html-output", required=True)
    parser.add_argument("--recognition", action="store_true")
    parser.add_argument("--recognition-output")
    parser.add_argument("--cell-index")
    return parser


def main() -> int:
    parser = _parser()
    arguments = parser.parse_args()
    output = Path(arguments.output)
    html_output = Path(arguments.html_output)
    if output.suffix.lower() != ".svg":
        parser.error("--output must end in .svg")
    if html_output.suffix.lower() != ".html":
        parser.error("--html-output must end in .html")
    if output.absolute() == html_output.absolute():
        parser.error("SVG and HTML outputs must be different files")

    if arguments.icons == ICON_ID:
        if not arguments.recognition:
            parser.error("Agent checkpoint generation requires --recognition")
        if arguments.recognition_output is not None or arguments.cell_index is not None:
            parser.error(
                "Agent checkpoint generation does not accept benchmark outputs"
            )
        try:
            _validate_output_paths((output, html_output))
        except ValueError as error:
            parser.error(str(error))

        contact_sheet = render_contact_sheet()
        contact_bytes = contact_sheet.encode("utf-8")
        digest = hashlib.sha256(contact_bytes).hexdigest()
        reference = os.path.relpath(
            output.absolute(),
            html_output.parent.absolute(),
        ).replace(os.sep, "/")
        defaults, _ = _context_tokens(token_css())
        review_page = render_review_html(reference, digest, defaults)

        _publish_outputs(
            (
                (output, contact_bytes),
                (html_output, review_page.encode("utf-8")),
            )
        )
        print(
            "icons=1 cells=72 unique=72 sizes=48,64,96 "
            "contexts=blue,dark,warm,green states=6"
        )
        print("OK")
        return 0

    canonical_icons = ",".join(BENCHMARK_ICONS)
    if arguments.icons != canonical_icons:
        parser.error(
            "--icons must be either agent or " + canonical_icons
        )
    if arguments.recognition:
        parser.error("benchmark generation uses --recognition-output")
    if arguments.recognition_output is None:
        parser.error("benchmark generation requires --recognition-output")
    if arguments.cell_index is None:
        parser.error("benchmark generation requires --cell-index")

    recognition_output = Path(arguments.recognition_output)
    cell_index = Path(arguments.cell_index)
    if recognition_output.suffix.lower() != ".html":
        parser.error("--recognition-output must end in .html")
    if cell_index.suffix.lower() != ".json":
        parser.error("--cell-index must end in .json")
    paths = (output, html_output, recognition_output, cell_index)
    try:
        _validate_output_paths(paths)
    except ValueError as error:
        parser.error(str(error))

    cells = build_contact_sheet_cells()
    contact_sheet = render_benchmark_contact_sheet(cells)
    contact_bytes = contact_sheet.encode("utf-8")
    digest = hashlib.sha256(contact_bytes).hexdigest()
    token_source = token_css()
    defaults, contexts = _context_tokens(token_source)
    review_page = render_benchmark_review_html(digest, defaults, cells)
    recognition_page = render_recognition_html(token_source, contexts)
    index_source = render_cell_index(cells)

    _publish_outputs(
        (
            (output, contact_bytes),
            (html_output, review_page.encode("utf-8")),
            (recognition_output, recognition_page.encode("utf-8")),
            (cell_index, index_source.encode("utf-8")),
        )
    )
    print(
        "icons=4 cells=288 unique=288 sizes=48,64,96 "
        "contexts=blue,dark,warm,green states=6"
    )
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
