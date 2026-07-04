# DiagramScript

AniDiagram accepts DiagramScript JSON and compiles it into a typed Scene IR
before rendering or exporting.

## v0.1

`0.1` is the compatibility schema. It supports:

- `canvas`
- `title`
- `style`
- `groups`
- freeform `nodes`
- `edges`
- explicit edge `points`

Schema: `schemas/diagram-script-v0.1.schema.json`.

## v0.2

`0.2` adds the product-kernel fields used by the preset compiler and quality
checks:

- `preset`: source preset name when generated from a built-in preset.
- node `step`: visible step badge.
- edge `route`: `curved`, `straight`, `hv`, `vh`, `orthogonal`, or `points`.
- edge `step`: visible step badge near the edge label.
- edge `animated`: boolean motion toggle.
- tighter role validation for `actor`, `source`, `process`, `agent`, `memory`,
  `tool`, `output`, `risk`, and `neutral`.

Schema: `schemas/diagram-script-v0.2.schema.json`.

The Python validator also checks cross-field behavior that JSON Schema cannot
fully express here, including duplicate ids, edge references, route/points
requirements, and canvas bounds.
