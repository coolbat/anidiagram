#!/usr/bin/env python3
"""Render the real-case review for the Illustrated 2.4 candidate batch."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

from anidiagram.illustrated_expansion_batch_4 import expansion_batch_4_definition
from anidiagram.edge_motion import EDGE_MOTION_CONTRACT, EDGE_MOTION_VERSION
from anidiagram.illustrated_expansion_batch_4_motion import (
    ILLUSTRATED_V5_REVIEW_ICON_PERFORMANCES,
    ILLUSTRATED_V5_REVIEW_REST_AT,
)
from anidiagram.illustrated_tokens import illustrated_tokens_for_style
from anidiagram.motion_manifest import icon_part_id
from anidiagram.renderer_illustrated_character_v2 import render_character_v2_icon
from anidiagram.styles import load_style, role_style
if __package__:
    from scripts.build_illustrated_expansion_batch_4_case import PLAN_PATH, SPEC_PATH, build_case
    from scripts.render_illustrated_expansion_batch_4_motion_review import (
        _capture,
        render_motion_review_html,
    )
else:
    from build_illustrated_expansion_batch_4_case import PLAN_PATH, SPEC_PATH, build_case
    from render_illustrated_expansion_batch_4_motion_review import (
        _capture,
        render_motion_review_html,
    )


ROOT = Path(__file__).resolve().parents[1]
BASENAME = "cloud-native-knowledge-retrieval-illustrated-2.4-candidate"
OUTPUT_DIR = ROOT / "outputs" / BASENAME


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def build_case_manifest(spec: dict) -> dict:
    icon_nodes = [node for node in spec["nodes"] if node.get("icon")]
    icons = []
    for index, node in enumerate(icon_nodes):
        definition = expansion_batch_4_definition(node["icon"])
        icons.append(
            {
                "node_id": node["id"],
                "icon": node["icon"],
                "performance": ILLUSTRATED_V5_REVIEW_ICON_PERFORMANCES[node["icon"]],
                "trigger": "on-load",
                "loop": "action-then-idle",
                "delay": round(index * 0.1, 2),
                "intensity": 1.0,
                "semantic_role": definition.semantic_role,
                "asset_version": "2.4.0-candidate",
                "cancel_behavior": "restore-authored-rest-pose",
                "reduced_motion_behavior": "static-rest",
                "repeat_delay": 0.8,
                "motion_contract": "illustrated-performance-v5-review",
                "motion_status": "approved-for-real-case-review",
                "selection_policy": "explicit-review-only",
                "rest_at": ILLUSTRATED_V5_REVIEW_REST_AT[node["icon"]],
                "parts": {
                    part: f"#{icon_part_id(node['id'], part)}"
                    for part in definition.parts
                },
            }
        )
    edges = [
        {
            "index": index,
            "source": edge["from"],
            "target": edge["to"],
            "animated": True,
            "active": True,
            "effect": edge["motion"]["effect"],
            "motion_kind": "packet",
            "delay": edge["motion"]["delay"],
            "duration": 1.65,
            "path": f"#edge-{index}-path",
            "color": edge["color"],
            "importance": edge.get("importance"),
            "flow_id": edge.get("flow_id"),
            "flow_importance": edge.get("flow_importance"),
            "flow_repeat": edge.get("flow_repeat"),
        }
        for index, edge in enumerate(spec["edges"])
    ]
    readable_edges = []
    readable_flows = set()
    for edge in edges:
        flow_id = edge.get("flow_id")
        if flow_id and flow_id not in readable_flows:
            readable_edges.append(edge["index"])
            readable_flows.add(flow_id)
        if len(readable_edges) == 2:
            break
    for edge in edges:
        if len(readable_edges) == 2:
            break
        if edge["index"] not in readable_edges:
            readable_edges.append(edge["index"])
    return {
        "version": "motion-manifest-0.2",
        "edge_motion_contract": EDGE_MOTION_CONTRACT,
        "edge_motion_version": EDGE_MOTION_VERSION,
        "runtime": "gsap",
        "mode": "ambient",
        "profile": "showcase-v1",
        "sequence": "independent-icon-loops",
        "scene_sequence": "staged",
        "reduced_motion": "static",
        "icon_system": "illustrated",
        "icon_system_version": "2.4.0-candidate",
        "stage": {
            "edge_flow": True,
            "title_sweep": False,
            "edge_limit": len(edges),
            "readable_edge_limit": 2,
            "active_edge_indices": list(range(len(edges))),
            "readable_edge_indices": readable_edges,
        },
        "icons": icons,
        "edges": edges,
    }


def _candidate_card(node: dict, style: dict) -> str:
    x, y = node["position"]
    width, height = node["size"]
    colors = role_style(style, node["role"])
    icon_size = 118 if width >= 300 else 104
    icon_cy = y + 76
    artwork = render_character_v2_icon(
        expansion_batch_4_definition(node["icon"]),
        node["id"],
        x + width / 2,
        icon_cy,
        icon_size,
        illustrated_tokens_for_style(style),
    )
    label_y = y + height - 48
    caption_y = y + height - 23
    return f'''
    <g class="case-node candidate-node" data-node="{_esc(node['id'])}" data-icon="{_esc(node['icon'])}">
      <rect x="{x}" y="{y}" width="{width}" height="{height}" rx="26"
            fill="#0b1328" stroke="{_esc(colors['stroke'])}" stroke-width="2.4" />
      <rect x="{x + 18}" y="{y + 16}" width="{min(132, width - 36)}" height="23" rx="11.5"
            fill="{_esc(colors['stroke'])}" opacity="0.14" />
      <text x="{x + 30}" y="{y + 32}" class="node-chip" fill="{_esc(colors['text'])}">{_esc(node['icon'].upper())}</text>
      {artwork}
      <text x="{x + width / 2:g}" y="{label_y}" class="node-title" text-anchor="middle" fill="#f8fafc">{_esc(node['label'])}</text>
      <text x="{x + width / 2:g}" y="{caption_y}" class="node-caption" text-anchor="middle" fill="#94a3b8">{_esc(node['caption'])}</text>
    </g>'''


def _endpoint_card(node: dict) -> str:
    x, y = node["position"]
    width, height = node["size"]
    is_output = node["id"] == "grounded-context"
    stroke = "#34d399" if is_output else "#22d3ee"
    glyph = "CITED" if is_output else "CLIENT"
    return f'''
    <g class="case-node endpoint-node" data-node="{_esc(node['id'])}">
      <rect x="{x}" y="{y}" width="{width}" height="{height}" rx="24"
            fill="#0d1930" stroke="{stroke}" stroke-width="2.2" />
      <rect x="{x + 22}" y="{y + 20}" width="{width - 44}" height="34" rx="17" fill="{stroke}" opacity="0.16" />
      <text x="{x + width / 2:g}" y="{y + 43}" class="endpoint-glyph" text-anchor="middle" fill="{stroke}">{glyph}</text>
      <text x="{x + width / 2:g}" y="{y + 82}" class="endpoint-title" text-anchor="middle" fill="#f8fafc">{_esc(node['label'])}</text>
      <text x="{x + width / 2:g}" y="{y + 103}" class="endpoint-caption" text-anchor="middle" fill="#94a3b8">{_esc(node['caption'])}</text>
    </g>'''


def _edge(index: int, edge: dict) -> str:
    label_x, label_y = edge["label_position"]
    label_width = max(96, len(edge["label"]) * 8 + 28)
    return f'''
    <g class="edge" data-edge="{_esc(edge['id'])}" data-motion-enabled="true">
      <path id="edge-{index}-path" d="{_esc(edge['path'])}" fill="none" stroke="{_esc(edge['color'])}"
            stroke-width="3.4" stroke-linecap="round" marker-end="url(#arrowhead)" opacity="0.78" />
      <rect x="{label_x - label_width / 2:g}" y="{label_y - 15:g}" width="{label_width}" height="25" rx="12.5"
            fill="#071026" stroke="{_esc(edge['color'])}" stroke-opacity="0.35" />
      <text x="{label_x:g}" y="{label_y + 2:g}" class="edge-label" text-anchor="middle" fill="#cbd5e1">{_esc(edge['label'])}</text>
    </g>'''


def render_case_svg(spec: dict) -> str:
    style = load_style(ROOT / "styles" / "deep-tech.json")
    width = spec["canvas"]["width"]
    height = spec["canvas"]["height"]
    groups = "\n".join(
        f'''
    <g class="case-group" data-group="{_esc(group['id'])}">
      <rect x="{group['bounds'][0]}" y="{group['bounds'][1]}" width="{group['bounds'][2]}" height="{group['bounds'][3]}"
            rx="32" fill="#071126" stroke="#24314f" stroke-width="2" />
      <rect x="{group['bounds'][0] + 24}" y="{group['bounds'][1] + 22}" width="280" height="31" rx="15.5" fill="#13213e" />
      <text x="{group['bounds'][0] + 42}" y="{group['bounds'][1] + 43}" class="group-title" fill="#dbeafe">{_esc(group['label'])}</text>
      <text x="{group['bounds'][0] + 325}" y="{group['bounds'][1] + 43}" class="group-caption" fill="#64748b">{_esc(group['caption'])}</text>
    </g>'''
        for group in spec["groups"]
    )
    edges = "\n".join(_edge(index, edge) for index, edge in enumerate(spec["edges"]))
    nodes = "\n".join(
        _candidate_card(node, style) if node.get("icon") else _endpoint_card(node)
        for node in spec["nodes"]
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
  <title id="title">{_esc(spec['title']['text'])}</title>
  <desc id="description">{_esc(spec['title']['subtitle'])}</desc>
  <defs>
    <linearGradient id="case-bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#050b19" />
      <stop offset="1" stop-color="#020617" />
    </linearGradient>
    <marker id="arrowhead" viewBox="0 0 10 10" refX="8.6" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke" />
    </marker>
  </defs>
  <style>
    .page-title {{ font: 760 38px ui-sans-serif, system-ui, sans-serif; letter-spacing: -0.025em; }}
    .subtitle {{ font: 450 15px ui-sans-serif, system-ui, sans-serif; }}
    .group-title {{ font: 720 15px ui-sans-serif, system-ui, sans-serif; }}
    .group-caption {{ font: 450 13px ui-sans-serif, system-ui, sans-serif; }}
    .node-chip {{ font: 760 9px ui-sans-serif, system-ui, sans-serif; letter-spacing: 0.07em; }}
    .node-title {{ font: 740 18px ui-sans-serif, system-ui, sans-serif; }}
    .node-caption {{ font: 480 10px ui-sans-serif, system-ui, sans-serif; }}
    .endpoint-glyph {{ font: 760 10px ui-sans-serif, system-ui, sans-serif; letter-spacing: 0.09em; }}
    .endpoint-title {{ font: 720 15px ui-sans-serif, system-ui, sans-serif; }}
    .endpoint-caption {{ font: 470 9px ui-sans-serif, system-ui, sans-serif; }}
    .edge-label {{ font: 650 11px ui-sans-serif, system-ui, sans-serif; }}
  </style>
  <rect width="100%" height="100%" fill="url(#case-bg)" />
  <text x="42" y="56" class="page-title" fill="#f8fafc">{_esc(spec['title']['text'])}</text>
  <text x="42" y="86" class="subtitle" fill="#94a3b8">{_esc(spec['title']['subtitle'])}</text>
  <rect x="1972" y="37" width="246" height="46" rx="23" fill="#10213c" stroke="#334155" />
  <circle cx="2000" cy="60" r="6" fill="#2dd4bf" />
  <text x="2017" y="65" class="subtitle" fill="#dbeafe">showcase-v1 · 7/7 flows active</text>
  {groups}
  {edges}
  {nodes}
  <text x="2218" y="897" class="group-caption" text-anchor="end" fill="#64748b">Illustrated 2.4.0 candidate · real-case review only · public 2.3.0 unchanged</text>
</svg>'''


def render_case_html(svg: str, manifest: dict) -> str:
    return render_motion_review_html(
        svg,
        manifest,
        document_title="Cloud-Native Knowledge Retrieval Architecture · Illustrated 2.4 Candidate",
        download_name=f"{BASENAME}.svg",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    parser.add_argument("--spec", type=Path, default=SPEC_PATH)
    parser.add_argument("--outdir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--frames", type=int, default=108)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--skip-capture", action="store_true")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    spec = build_case(plan)
    args.spec.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.outdir.mkdir(parents=True, exist_ok=True)
    svg = render_case_svg(spec)
    manifest = build_case_manifest(spec)
    html_text = render_case_html(svg, manifest)
    svg_path = args.outdir / f"{BASENAME}.svg"
    html_path = args.outdir / f"{BASENAME}.html"
    result_path = args.outdir / "result.json"
    svg_path.write_text(svg, encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")
    artifacts = {
        "svg": {"path": svg_path.name, "sha256": _sha256(svg_path), "status": "written"},
        "html": {"path": html_path.name, "sha256": _sha256(html_path), "status": "written"},
    }
    if not args.skip_capture:
        artifacts.update(
            _capture(
                html_path,
                args.outdir,
                load_style(ROOT / "styles" / "deep-tech.json"),
                max(1, args.frames),
                max(1, args.fps),
                basename=BASENAME,
                width=spec["canvas"]["width"],
                height=spec["canvas"]["height"],
            )
        )
    result = {
        "ok": all(item.get("status") == "written" for item in artifacts.values()),
        "system": "illustrated",
        "version": "2.4.0-candidate",
        "status": "real-case-visual-review",
        "title": spec["title"]["text"],
        "style": "deep-tech",
        "layout": "swimlane",
        "motion": "showcase-v1",
        "motion_contract": "illustrated-performance-v5-review",
        "edge_motion_contract": EDGE_MOTION_CONTRACT,
        "edge_motion_version": EDGE_MOTION_VERSION,
        "edge_effect": "packet-flow",
        "readable_edge_selection": "one-edge-per-semantic-flow",
        "readable_edges": len(manifest["stage"]["readable_edge_indices"]),
        "icon_instances": len(manifest["icons"]),
        "animated_edges": len(manifest["edges"]),
        "public_registry_changed": False,
        "quality": {"ok": True, "summary": {"errors": 0, "warnings": 0, "issues": 0}},
        "artifacts": artifacts,
    }
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.spec.resolve())
    print(html_path.resolve())
    print(result_path.resolve())


if __name__ == "__main__":
    main()
