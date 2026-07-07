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
- node `shape`: `rect` or `decision`.
- node, edge, and group `effect`: per-element effect override.
- effect `icon_motion`: icon-local motion hint for `icon-semantic` nodes.
- top-level `motion_policy`: budget controls for how many edges, particles,
  nodes, and group borders may be actively animated.
- effect `particle_count` and `trail_count`: per-effect density controls.
- `runtime-loop` profile: looping runtime-state motion with static structure,
  signal edges, icon breathing, static groups, and breathing title.

Schema: `schemas/diagram-script-v0.3.schema.json`.

Structured effect object example:

```json
{
  "preset": "icon-semantic",
  "icon_motion": "database-write"
}
```

Supported semantic icons:

`database`, `file`, `folder`, `api`, `cloud`, `search`, `shield`, `agent`,
`token`, `memory`, `tool`, `output`.

Supported node shapes:

- `rect`: default rounded rectangle node.
- `decision`: diamond-shaped decision node for branches and quality gates.

DiagramPlan v0.1 is the higher-level brief/LLM contract that can compile into
freeform DiagramScript v0.3. See
[prompt-to-diagram-flow.md](./prompt-to-diagram-flow.md).

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
- `teaching`: staged teaching motion with semantic icons, line flow, and title
  reveal defaults.

Motion channels:

- `sequence`: `simultaneous`, `step-stagger`, `layered`, `staged`, or `loop`.
- `node`: `none`, `fade`, `float`, `glow-breathe`, `pop`, `pulse`,
  `ripple`, `status-blink`, `icon-pulse`, `icon-breathe`, `icon-semantic`,
  `icon-performance`, or `micro-icon`.
- `edge`: `none`, `static`, `draw`, `pulse`, `comet-flow`, `trace`,
  `dynamic-dash`, `dash-flow`, `flow-dot`, `flow-arrow`, `signal-dot`,
  `signal-arrow`, `ghost-flow`, `glow-line`, or `comet`.
- `group`: `none`, `static`, `soft-reveal`, `marching-ants`, `border-scan`,
  or `corner-pulse`.
- `title`: `none`, `fade`, `breathe`, `handwrite-reveal`, or
  `highlight-sweep`.
- `reduced_motion`: `static`, `subtle`, or `pause`.

## Motion Policy

`motion_policy` is a separate budget layer. It does not change what an effect
means; it limits how many resolved effects are allowed to remain active. This
keeps generated diagrams readable when many elements ask for motion.

```json
{
  "motion_policy": {
    "profile": "focused",
    "motion_area": "small",
    "max_active_flow_edges": 4,
    "max_particle_edges": 3,
    "particle_count_per_edge": 1,
    "flow_trail_count": 1,
    "max_active_pulse_nodes": 1,
    "pulse_mode": "rotate",
    "max_scanning_groups": 1
  }
}
```

Profiles:

- `unrestricted`: no built-in clamp.
- `readable`: sparse movement for dense architecture diagrams.
- `focused`: a few active paths for explainer and teaching diagrams.
- `expressive`: higher limits for showcase output.
- `readable-runtime`: larger edge count but micro-sized motion for runtime-loop
  diagrams.

When the configured effects exceed the policy, SVG and raster renderers clamp
extras into calmer draw/fade/soft-reveal behavior. Quality reports emit a
`motion_overload` warning so generated specs can be tuned upstream.

Runtime-loop example:

```json
{
  "motion": {
    "profile": "runtime-loop",
    "sequence": "loop",
    "edge": {"preset": "signal-dot", "particle_count": 1, "trail_count": 0},
    "node": {"preset": "icon-breathe"},
    "group": {"preset": "static"},
    "title": {"preset": "breathe"}
  },
  "motion_policy": {
    "profile": "readable-runtime",
    "motion_area": "micro"
  }
}
```

## Effect Objects

DiagramScript v0.3 keeps the existing string motion channels as compatibility
syntax and adds structured effect objects for richer line, node, group, title,
and semantic icon behavior.

`icon-semantic` keeps node frames still and animates only local icon parts.
Default icon motions are:

| Icon | Default motion |
| --- | --- |
| `database` | `database-write` |
| `memory` | stacked memory cards |
| `file` | `file-lines`: page entrance, scale overshoot, folded-corner motion, and fast content-line reveal |
| `folder` | `folder-open` |
| `api` | `api-ping` |
| `cloud` | `cloud-upload` |
| `search` | `search-sweep` |
| `shield` | `shield-check` |
| `agent` | `agent-orbit` |
| `tool` | `tool-tap` |
| `output` | `output-check` |
| `token` | `token-pulse` |

`icon-performance` is a runtime-ready node preset. Standalone SVG cannot play
the high-fidelity JavaScript runtime performances, so `icon-performance`
degrades to lightweight SVG/SMIL icon motion in standalone SVG. Use
`--formats html --html-runtime gsap` for the Motion Manifest and browser
runtime path. `html-runtime` is accepted as a legacy alias for `html`. When
those performances need to survive raster, video, PDF, or Lottie export, use
`--export-renderer browser`; PNG, GIF, PDF, WebP, MP4, APNG, and frame-based
Lottie are then captured from the real `html` page instead of the lightweight
Python preview renderer. The first runtime
performances are:

| Icon | Runtime performance |
| --- | --- |
| `agent` | `agent-think-act-v2` |
| `api` | `api-request-response-v2` |
| `search` | `search-discover-v2` |
| `database` | `database-write-v2` |
| `memory` | `memory-commit-v2` |
| `tool` | `tool-run-v2` |
| `token` | `token-intent-v2` |
| `output` | `output-reveal-v2` |

The runtime manifest maps each performance to stable SVG part IDs such as
`#icon-agent-thought-1`, `#icon-api-request-token`, and
`#icon-search-result-1`.
See [html-runtime.md](./html-runtime.md) for the runtime ownership model and
current limitations.

The broader feature plan is documented in
[motion-effects-feature-plan.md](./motion-effects-feature-plan.md).
