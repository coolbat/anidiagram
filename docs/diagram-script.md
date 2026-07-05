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
- top-level `motion`: scene-level motion profile and sequencing controls.
- tighter role validation for `actor`, `source`, `process`, `agent`, `memory`,
  `tool`, `output`, `risk`, and `neutral`.

Schema: `schemas/diagram-script-v0.2.schema.json`.

The Python validator also checks cross-field behavior that JSON Schema cannot
fully express here, including duplicate ids, edge references, route/points
requirements, and canvas bounds.

## v0.3

`0.3` adds the first version of AniDiagram's effect registry syntax:

- `motion.profile`: adds `teaching`.
- `motion.sequence`: adds `staged`.
- `motion.edge`, `motion.node`, `motion.group`, and `motion.title`: accept
  either the legacy string form or a structured effect object.
- node `icon`: semantic icon id for built-in clean-room SVG primitives.
- node, edge, and group `effect`: per-element effect override.

Schema: `schemas/diagram-script-v0.3.schema.json`.

Structured effect object example:

```json
{
  "preset": "ghost-flow",
  "particle": "soft-dot",
  "trail": true
}
```

Supported semantic icons:

`database`, `file`, `folder`, `api`, `cloud`, `search`, `shield`, `agent`,
`token`, `memory`, `tool`, `output`.

## Motion Profiles

`motion` is AniDiagram's clean-room animation vocabulary inspired by timeline
and stagger concepts from mature animation tools. It does not require a
third-party runtime.

```json
{
  "motion": {
    "profile": "expressive",
    "sequence": "layered",
    "ease": "spring",
    "stagger": 0.16,
    "duration_scale": 0.9,
    "intensity": 1.25,
    "node": "pop",
    "edge": "comet-flow",
    "group": "marching-ants",
    "reduced_motion": "subtle"
  }
}
```

Profiles:

- `off`: static SVG with no active motion.
- `subtle`: restrained entry and draw-on edges.
- `normal`: default balanced motion.
- `expressive`: layered sequence with stronger node and edge motion.

Motion channels:

- `sequence`: `simultaneous`, `step-stagger`, or `layered`.
- `node`: `none`, `fade`, `float`, `glow-breathe`, or `pop`.
- `edge`: `none`, `draw`, `pulse`, `comet-flow`, or `trace`.
- `group`: `none`, `soft-reveal`, or `marching-ants`.
- `reduced_motion`: `static`, `subtle`, or `pause`.

## Effect Objects

DiagramScript v0.3 keeps the existing string motion channels as compatibility
syntax and adds structured effect objects for richer line, node, group, title,
and semantic icon behavior.

The broader feature plan is documented in
[motion-effects-feature-plan.md](./motion-effects-feature-plan.md).
