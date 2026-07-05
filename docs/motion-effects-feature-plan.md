# Motion Effects Feature Plan

This document defines the clean-room direction for richer AniDiagram motion
effects. The goal is to support complex teaching and architecture diagrams with
clear, style-compatible motion across SVG, HTML, GIF, WebP, APNG, and MP4.

## Goals

- Provide reusable motion presets for edges, nodes, groups, titles, and semantic
  icons.
- Keep style and motion separate: styles provide visual tokens, effects decide
  how elements move.
- Allow scene-level defaults and per-element overrides.
- Preserve dependency-free SVG/HTML output as the primary render path.
- Provide simplified but visible raster/video equivalents for GIF, WebP, APNG,
  and MP4.
- Keep the project clean-room. Reference materials can guide product direction,
  but code, documents, images, generated assets, and repository history are not
  copied.

## Current Implementation Status

The first implementation slice is available in DiagramScript v0.3:

- structured `motion.edge`, `motion.node`, `motion.group`, and `motion.title`
  effect objects;
- per-node, per-edge, and per-group `effect` overrides;
- semantic node `icon` primitives;
- edge presets for `dynamic-dash`, `flow-dot`, `flow-arrow`, `ghost-flow`,
  `glow-line`, and legacy `comet-flow`;
- group `border-scan` and existing moving boundary effects;
- node `icon-pulse` plus existing glow/burst behavior;
- `teaching` motion profile and `sketch-board` style;
- a clean-room teaching example at
  `examples/teaching-transformer.diagram.json`.

## Non-Goals

- Do not import animation runtimes such as GSAP, Lottie Web, or Anime.js into
  the core renderer by default.
- Do not copy old project renderer code, presets, examples, GIFs, MP4s, or
  image assets.
- Do not make every effect available in every export format at full fidelity.
  SVG/HTML is the highest-fidelity target; raster/video exports may use a
  compatible simplified effect.

## Design Model

AniDiagram should evolve from string-only motion channels:

```json
{
  "motion": {
    "profile": "expressive",
    "edge": "comet-flow",
    "node": "pop",
    "group": "marching-ants"
  }
}
```

to an effect registry that accepts both legacy strings and structured presets:

```json
{
  "motion": {
    "profile": "teaching",
    "sequence": "staged",
    "edge": {
      "preset": "ghost-flow",
      "line": "glow",
      "particle": "soft-arrow",
      "trail": true
    },
    "node": {
      "preset": "icon-pulse",
      "entry": "pop",
      "accent": "ripple"
    },
    "group": {
      "preset": "border-scan"
    },
    "title": {
      "preset": "handwrite-reveal"
    }
  }
}
```

Individual elements should be able to override scene defaults:

```json
{
  "from": "encoder",
  "to": "attention",
  "label": "tokens",
  "effect": {
    "line": "dynamic-dash",
    "particle": "soft-dot",
    "trail": "ghost"
  }
}
```

## Effect Registry

The renderer should add an internal effect registry, likely in
`src/anidiagram/effects.py`, with small render functions for each channel.
The registry should return SVG markup for SVG/HTML and a raster strategy for
frame-based exporters.

Recommended channels:

- `edge`: line styling, flow particles, arrow particles, dash motion, trace
  motion, glow.
- `node`: entry animation, pulse, ripple, glow, status blink, icon accent.
- `group`: reveal, moving dash, border scan, corner pulse.
- `title`: fade, type-in, handwrite reveal, highlight sweep.
- `icon`: semantic glyph shape plus optional icon-local motion.

Recommended edge presets:

| Preset | Description |
| --- | --- |
| `static` | No edge motion. |
| `draw` | Path draws on once. |
| `dynamic-dash` | Moving dashed stroke. |
| `flow-dot` | One or more soft circles travel along the path. |
| `flow-arrow` | Semi-transparent arrow particles travel along the path. |
| `ghost-flow` | Particle trail with translucent echoes. |
| `glow-line` | Low-frequency glow pulse along the line. |
| `comet` | Bright leading particle with fading tail. |

Recommended node presets:

| Preset | Description |
| --- | --- |
| `fade` | Simple opacity reveal. |
| `pop` | Scale/opacity entry with mild bounce. |
| `float` | Slow vertical drift. |
| `pulse` | Stroke or glow breathing. |
| `ripple` | Expanding rings around important nodes. |
| `status-blink` | Low-duty status indicator for active tools. |
| `icon-pulse` | Semantic icon accent pulse. |

Recommended group presets:

| Preset | Description |
| --- | --- |
| `static` | No group motion. |
| `soft-reveal` | Group fades in before child nodes. |
| `marching-dash` | Existing moving dash boundary. |
| `border-scan` | Light sweep around a panel border. |
| `corner-pulse` | Corner ticks pulse to frame a section. |

Recommended semantic icons:

| Icon | Use |
| --- | --- |
| `database` | Memory, SQL stores, vector stores. |
| `file` | Documents, papers, artifacts. |
| `folder` | Collections and reusable assets. |
| `api` | API/service endpoints. |
| `cloud` | Remote services or hosted systems. |
| `search` | Retrieval, web search, inspection. |
| `shield` | policy, safety, validation. |
| `agent` | autonomous or assistant components. |
| `token` | token/source/embedding examples. |

## Style Compatibility

Effects must use style tokens instead of hard-coded visual values. A style can
define default effect choices and intensity caps.

Recommended style defaults:

| Style | Default Motion Direction |
| --- | --- |
| `minimal-light` | Fade, draw, very low particle opacity. |
| `openai-minimal` | Low-intensity draw and sparse flow dots. |
| `notion-clean` | Subtle fade and thin line motion only. |
| `blueprint` | Dynamic dashes, border scan, technical trace lines. |
| `dark-terminal` | Scan line, cursor-like blink, green low glow. |
| `aurora-orb` | Soft glow, ghost-flow, gradient-tinted particles. |
| `dark-luxury` | Slow gold border sweep and restrained glow. |
| `sketch-board` | Handwritten reveal, soft shadow, ghost dots, rough borders. |

The renderer should resolve effects in this order:

1. Per-element `effect` override.
2. Scene-level `motion.<channel>` setting.
3. Style-level compatible defaults.
4. Built-in conservative fallback.

## Teaching Diagram Target

Complex educational visuals, such as transformer architecture walkthroughs, need
more than generic architecture blocks. A clean-room AniDiagram implementation
should support:

- staged title and subtitle reveal;
- large section panels with animated borders;
- icon-based nodes for search, shield, database, file, token, and cube-like
  concepts;
- residual or feedback paths with moving dashed lines;
- attention/focus paths with soft particles and ghost trails;
- callout cards with subtle pulse;
- global reduced-motion fallback.

These are product and interaction targets only. Any old GIF/MP4 outputs or fork
assets remain reference material and are not implementation inputs.

## Export Behavior

SVG/HTML should render the full effect vocabulary with SMIL where practical.

Raster/video exporters should render simplified equivalents:

- edge flow: moving dots or arrows along sampled paths;
- dynamic dash: phase-shifted dash segments;
- border scan: moving highlight point or segment around the rectangle;
- node pulse: changing stroke/glow radius;
- icon pulse: small highlight overlay on the icon.

Quality reports should eventually flag effects that may obscure labels, exceed
canvas bounds, or create excessive contrast/flicker.

## Implementation Phases

### Phase 1: Effect Registry Foundation

- Add typed effect config objects while preserving current string values.
- Add `effects.py` with edge/node/group/title/icon registries.
- Add schema support for structured `motion` channel objects.
- Add tests for legacy string compatibility.

### Phase 2: Edge and Group Effects

- Implement `static`, `draw`, `dynamic-dash`, `flow-dot`, `flow-arrow`,
  `ghost-flow`, and `glow-line`.
- Implement `border-scan` and `corner-pulse`.
- Add SVG and raster frame tests that assert visible frame differences.

### Phase 3: Semantic Icons

- Add clean-room built-in SVG icon primitives for database, file, folder, API,
  cloud, search, shield, agent, and token.
- Add role-aware icon defaults.
- Add icon sizing and text collision checks.

### Phase 4: Sketch Board Style

- Add a new `sketch-board` style profile with paper-like background, soft
  shadows, rough-border-compatible tokens, and teaching-diagram defaults.
- Add an original example scene that exercises transformer-style educational
  flow without copying old assets or layouts.

### Phase 5: Docs and Gallery

- Document DiagramScript v0.3 effect configuration.
- Add gallery cases for edge effects, group effects, icon nodes, and teaching
  diagrams.
- Keep `CHANGELOG.md` updated for each feature slice.

## Acceptance Criteria

- Existing DiagramScript v0.1/v0.2 specs continue to render.
- New structured effect configs validate with path-level errors.
- SVG/HTML output exposes full effects.
- GIF/WebP/APNG/MP4 outputs show visible frame changes for animated effects.
- `quality` reports remain clean for bundled examples.
- README and gallery demonstrate at least one complex teaching diagram.
- No code, docs, or generated assets are copied from the old fork.
