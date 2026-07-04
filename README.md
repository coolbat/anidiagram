# Animated Diagram

Clean-room JSON-to-animated-SVG renderer for architecture diagrams.

This repository is not a GitHub fork and does not copy source code, documents,
images, generated assets, or repository history from the projects listed in
[REFERENCES.md](./REFERENCES.md).

## What It Does

- Reads a structured DiagramScript JSON file.
- Applies a visual style profile.
- Renders a deterministic animated SVG.
- Optionally writes a self-contained HTML viewer.
- Uses only the Python standard library.

## Quick Start

```bash
python3 -m animated_diagram.cli \
  --spec examples/agent-memory.diagram.json \
  --style styles/blueprint.json \
  --outdir outputs \
  --basename agent-memory \
  --html
```

For local development without installing the package:

```bash
PYTHONPATH=src python3 -m animated_diagram.cli \
  --spec examples/agent-memory.diagram.json \
  --style styles/deep-tech.json \
  --outdir outputs \
  --basename agent-memory \
  --html
```

## DiagramScript

The initial schema is intentionally small:

```json
{
  "version": "0.1",
  "canvas": {"width": 1200, "height": 720},
  "style": "blueprint",
  "title": {"text": "Agent Memory System", "subtitle": "request, tools, memory, response"},
  "groups": [
    {"id": "runtime", "label": "Runtime", "bounds": [300, 150, 360, 370], "role": "process"}
  ],
  "nodes": [
    {"id": "user", "label": "User", "caption": "asks", "position": [80, 310], "size": [150, 82], "role": "actor"}
  ],
  "edges": [
    {"from": "user", "to": "agent", "label": "request", "role": "control"}
  ]
}
```

## Style Profiles

Style profiles are visual grammar files, not only palettes. A profile defines:

- canvas colors
- role colors
- node radius and stroke width
- edge width and animation timing
- title treatment

Bundled starter styles:

- `styles/minimal-light.json`
- `styles/deep-tech.json`
- `styles/blueprint.json`

## Clean-Room Boundary

The project can reference prior art at the concept level, but its code,
schema, assets, examples, and documentation are authored independently.

If code or assets are ever copied from MIT-licensed references, this project
must add their original license notices before release.
