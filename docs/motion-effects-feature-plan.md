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
- `motion_policy` budgets for active flow edges, particle edges, per-edge
  particle/trail density, pulse nodes, and scanning group borders;
- runtime-loop motion primitives: `signal-dot`, `signal-arrow`, `dash-flow`,
  `icon-breathe`, and title `breathe`;
- semantic icon-local motion primitives through `icon-semantic` and
  `icon_motion`;
- quality warnings for configured motion that exceeds the selected policy;
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

`motion_policy` is the density-control layer. It should be applied after style
defaults and per-element overrides are resolved:

```json
{
  "motion_policy": {
    "profile": "focused",
    "max_active_flow_edges": 4,
    "max_particle_edges": 3,
    "particle_count_per_edge": 1,
    "flow_trail_count": 1,
    "max_active_pulse_nodes": 1,
    "max_scanning_groups": 1
  }
}
```

The rule of thumb is: all important elements may declare a semantic effect, but
only the budgeted subset keeps continuous motion. Extras degrade to draw,
fade, or soft-reveal so the diagram remains readable.

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
| `dash-flow` | Moving dashed arrow effect where dash continuity implies forward motion. |
| `flow-dot` | One or more soft circles travel along the path. |
| `flow-arrow` | Semi-transparent arrow particles travel along the path. |
| `signal-dot` | One small signal point travels along a complete static path. |
| `signal-arrow` | One small arrow-shaped signal travels along a complete static path. |
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
| `icon-breathe` | Gentle semantic-icon breathing with the node frame static. |
| `icon-semantic` | Icon-specific local motion such as database writes, file lines, or shield checks. |
| `micro-icon` | Alias-style micro icon breathing for runtime diagrams. |

Recommended title presets:

| Preset | Description |
| --- | --- |
| `fade` | Simple title reveal. |
| `breathe` | Gentle title opacity breathing without spatial movement. |
| `handwrite-reveal` | Hand-drawn underline or reveal accent. |
| `highlight-sweep` | Soft highlight sweep behind the title. |

## Runtime-Loop Motion Rules

For reference-style runtime diagrams, AniDiagram should prefer:

- complete static structure from the first frame;
- node frames and large group frames remain still;
- semantic icons may breathe gently, with no jump or whole-node movement;
- semantic icons may use `icon-semantic` for icon-specific local motion such as
  `database-write`, `file-lines`, `api-ping`, `search-sweep`,
  `shield-check`, `agent-orbit`, `tool-tap`, and `output-check`;
- edges carry one signal point or one signal arrow per path;
- dashed-arrow paths use `dash-flow`, where dash continuity creates forward
  motion;
- title motion uses `breathe`, not sliding or bouncing;
- `motion_policy.motion_area` starts as an optional clamp. `micro` currently
  reduces particle scale and can be revised or removed after visual testing.

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

Recommended icon motions:

| Motion | Intended icon behavior |
| --- | --- |
| `database-write` | Database top ellipse compresses/rebounds, a write line scans across, a data point enters, and the lower layer flashes lightly. |
| `file-lines` | File page enters from lower-left, noticeably overshoots scale, folded corner moves, then document lines reveal quickly. |
| `folder-open` | Folder tab opens slightly and exposes a short internal file line before settling. |
| `api-ping` | Request dot travels between API brackets. |
| `cloud-upload` | Small upload arrow moves inside a cloud with faint internal transfer dots. |
| `search-sweep` | Lens sweep highlight plus a small light point inside the lens. |
| `shield-check` | Checkmark draws in place and a low-opacity protection pulse follows the shield outline. |
| `agent-orbit` | Center core glows while a small thinking/status dot orbits locally. |
| `tool-tap` | Tool stroke taps locally and emits a short spark at the contact point. |
| `output-check` | Output lines reveal first, then the result checkmark draws in place. |
| `token-pulse` | Center token pulse plus short outer ticks lighting in sequence. |

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

Current quality reports already flag `motion_overload` when configured active
motion exceeds `motion_policy` budgets.

## Implementation Phases

### Phase 1: Effect Registry Foundation

- Add typed effect config objects while preserving current string values. Done.
- Add `effects.py` with edge/node/group/title/icon registries. Started.
- Add schema support for structured `motion` channel objects. Done.
- Add motion budget policy support for generated complex scenes. Done.
- Add tests for legacy string compatibility and policy clamping. Started.

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
