# AniDiagram

Clean-room JSON-to-animated-SVG renderer for animated architecture visuals.

This repository is not a GitHub fork and does not copy source code, documents,
images, generated assets, or repository history from the projects listed in
[REFERENCES.md](./REFERENCES.md).

## What It Does

- Reads a structured DiagramScript JSON file.
- Validates DiagramScript and compiles it to an internal Scene IR.
- Applies a visual style profile.
- Renders a deterministic animated SVG.
- Optionally writes a self-contained HTML viewer.
- Uses only the Python standard library.

## Quick Start

```bash
python3 -m anidiagram.cli \
  --spec examples/agent-memory.diagram.json \
  --style styles/blueprint.json \
  --outdir outputs \
  --basename agent-memory \
  --html
```

For local development without installing the package:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/agent-memory.diagram.json \
  --style styles/deep-tech.json \
  --outdir outputs \
  --basename agent-memory \
  --html
```

## DiagramScript

The current schema is `DiagramScript` v0.1. It is intentionally small and
freeform-layout first.

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

Required fields:

- `version`: currently `"0.1"`.
- `nodes`: non-empty array of node objects.
- each node: `id`, `position`, and `size`.
- each edge: `from` and `to`, both referencing existing node ids.

Optional fields:

- `canvas.width` and `canvas.height`, defaulting to `1200 x 720`.
- `style`, mapped to a JSON file under `styles/` when the CLI can resolve it.
- `title.text` and `title.subtitle`.
- `groups`, where each group has `id` and `bounds`.
- edge `points`, for explicit point-to-point line paths.
- visual overrides such as `role`, `fill`, `stroke`, `width`, `duration`, `delay`, and `animated`.

The CLI validates the spec before rendering. Validation failures are printed as
structured JSON on stderr and exit with code `2`:

```json
{
  "ok": false,
  "error": {
    "code": "diagram_script_validation_failed",
    "issues": [
      {"path": "$.edges[0].to", "message": "unknown node id 'missing'", "code": "reference"}
    ]
  }
}
```

Successful CLI runs print structured result JSON:

```json
{
  "ok": true,
  "schema": {"name": "DiagramScript", "version": "0.1"},
  "style": "blueprint",
  "outputs": {
    "svg": {"format": "svg", "path": "/absolute/path/to/agent-memory.svg"}
  },
  "stats": {"nodes": 6, "edges": 6, "groups": 2}
}
```

Internally, v0.1 compiles into a typed Scene IR made of `Scene`, `Node`,
`Edge`, `Group`, `Style`, and `Motion` objects before reaching the SVG renderer.

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
