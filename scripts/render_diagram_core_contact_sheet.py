#!/usr/bin/env python3
"""Render the deterministic Agent benchmark and its static review page."""

from __future__ import annotations

import argparse
import hashlib
import html
import os
import re
from pathlib import Path
from typing import Dict, Mapping, Tuple

from anidiagram.diagram_core.adapter import render_preview_icon
from anidiagram.diagram_core.tokens import token_css


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets" / "diagram-core"
ICON_ID = "agent"
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
_HEX_COLOR = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_RGB_COLOR = re.compile(
    r"^rgb\(\s*(\d{1,3})(?:\s*,\s*|\s+)(\d{1,3})"
    r"(?:\s*,\s*|\s+)(\d{1,3})\s*\)$",
    re.IGNORECASE,
)
_SIMPLE_VAR = re.compile(r"^var\(\s*(--[a-z0-9-]+)\s*\)$")


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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render the static Agent Diagram Core benchmark."
    )
    parser.add_argument("--icons", required=True, choices=(ICON_ID,))
    parser.add_argument("--output", required=True)
    parser.add_argument("--html-output", required=True)
    parser.add_argument("--recognition", action="store_true", required=True)
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

    contact_sheet = render_contact_sheet()
    contact_bytes = contact_sheet.encode("utf-8")
    digest = hashlib.sha256(contact_bytes).hexdigest()
    reference = os.path.relpath(
        output.absolute(),
        html_output.parent.absolute(),
    ).replace(os.sep, "/")
    defaults, _ = _context_tokens(token_css())
    review_page = render_review_html(reference, digest, defaults)

    output.parent.mkdir(parents=True, exist_ok=True)
    html_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(contact_bytes)
    html_output.write_text(review_page, encoding="utf-8")
    print(
        "icons=1 cells=72 unique=72 sizes=48,64,96 "
        "contexts=blue,dark,warm,green states=6"
    )
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
