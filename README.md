# AniDiagram

Clean-room DiagramScript renderer for animated architecture visuals.

This repository is not a GitHub fork and does not copy source code, documents,
images, generated assets, or repository history from the projects listed in
[REFERENCES.md](./REFERENCES.md).

## Examples

| Pipeline | Agent Memory |
| --- | --- |
| ![Pipeline preset](./gallery/pipeline.svg) | ![Agent memory preset](./gallery/agent-memory.svg) |

| Swimlane | Network |
| --- | --- |
| ![Swimlane preset](./gallery/swimlane.svg) | ![Network preset](./gallery/network.svg) |

Full preset gallery: [gallery/index.html](./gallery/index.html)

## Style Showcase

Each bundled style has a clean-room example spec plus rendered SVG/HTML assets.
Click a preview to open its animated HTML viewer.

| `minimal-light` | `deep-tech` | `blueprint` |
| --- | --- | --- |
| [![minimal-light style showcase](./gallery/styles/minimal-light.svg)](./gallery/styles/minimal-light.html)<br>Customer Support Triage | [![deep-tech style showcase](./gallery/styles/deep-tech.svg)](./gallery/styles/deep-tech.html)<br>Realtime AI Ops Mesh | [![blueprint style showcase](./gallery/styles/blueprint.svg)](./gallery/styles/blueprint.html)<br>Cloud Deployment Blueprint |

| `flat-icon` | `dark-terminal` | `notion-clean` |
| --- | --- | --- |
| [![flat-icon style showcase](./gallery/styles/flat-icon.svg)](./gallery/styles/flat-icon.html)<br>Feature Priority Board | [![dark-terminal style showcase](./gallery/styles/dark-terminal.svg)](./gallery/styles/dark-terminal.html)<br>Incident Response Runbook | [![notion-clean style showcase](./gallery/styles/notion-clean.svg)](./gallery/styles/notion-clean.html)<br>Product Discovery Workflow |

| `glassmorphism` | `claude-warm` | `openai-minimal` |
| --- | --- | --- |
| [![glassmorphism style showcase](./gallery/styles/glassmorphism.svg)](./gallery/styles/glassmorphism.html)<br>Revenue Funnel | [![claude-warm style showcase](./gallery/styles/claude-warm.svg)](./gallery/styles/claude-warm.html)<br>Research Reasoning Loop | [![openai-minimal style showcase](./gallery/styles/openai-minimal.svg)](./gallery/styles/openai-minimal.html)<br>Evaluation Pipeline |

| `dark-luxury` | `aurora-orb` | `sketch-board` |
| --- | --- | --- |
| [![dark-luxury style showcase](./gallery/styles/dark-luxury.svg)](./gallery/styles/dark-luxury.html)<br>Executive Signal Network | [![aurora-orb style showcase](./gallery/styles/aurora-orb.svg)](./gallery/styles/aurora-orb.html)<br>Creative Agent Studio | [![sketch-board style showcase](./gallery/styles/sketch-board.svg)](./gallery/styles/sketch-board.html)<br>Attention Teaching Flow |

Full style showcase: [gallery/styles/index.html](./gallery/styles/index.html)

## What It Does

- Validates DiagramScript `0.1`, `0.2`, and `0.3`.
- Compiles JSON specs or presets into a typed Scene IR.
- Renders animated SVG and self-contained HTML viewers.
- Uses richer motion layers: staggered entry, line drawing, flow particles,
  node glow, burst rings, and animated group boundaries.
- Supports scene-level motion profiles for `off`, `subtle`, `normal`,
  `expressive`, and `teaching` animation behavior.
- Supports structured motion effect objects for line flow, arrow particles,
  dynamic dashes, border scans, icon pulses, and title reveal effects.
- Exports optional PNG, GIF, PDF, WebP, MP4, APNG, and Lottie files.
- Produces quality reports for bounds, overlaps, text fit, and explicit paths.
- Includes 14 clean-room preset compilers and 12 visual styles.

SVG, HTML, Lottie, and quality reports use the Python standard library. Raster
and video exports use optional Pillow support; MP4 also needs `ffmpeg`.

## Quick Start

Render a JSON spec:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/agent-memory.diagram.json \
  --style styles/blueprint.json \
  --outdir outputs \
  --basename agent-memory \
  --formats svg,html,quality
```

Render a clean-room preset:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --preset agent-memory \
  --outdir outputs \
  --basename agent-memory \
  --all
```

Install optional raster dependencies:

```bash
python3 -m pip install ".[raster]"
```

## CLI Result

Successful runs print structured JSON:

```json
{
  "ok": true,
  "schema": {"name": "DiagramScript", "version": "0.2"},
  "preset": "agent-memory",
  "style": "blueprint",
  "outputs": {
    "svg": {"format": "svg", "path": "/abs/agent-memory.svg", "status": "written"},
    "quality": {"format": "quality", "path": "/abs/agent-memory.quality.json", "status": "written"}
  },
  "stats": {"nodes": 6, "edges": 6, "groups": 2}
}
```

Validation failures are printed on stderr and exit with code `2`.

## DiagramScript

Schema files:

- [schemas/diagram-script-v0.1.schema.json](./schemas/diagram-script-v0.1.schema.json)
- [schemas/diagram-script-v0.2.schema.json](./schemas/diagram-script-v0.2.schema.json)
- [schemas/diagram-script-v0.3.schema.json](./schemas/diagram-script-v0.3.schema.json)
- [schemas/style-profile-v0.1.schema.json](./schemas/style-profile-v0.1.schema.json)

v0.2 adds route types, step badges, preset metadata, and stricter role
validation. v0.3 adds structured effect objects and semantic icons. See
[docs/diagram-script.md](./docs/diagram-script.md).

## Layout Presets

AniDiagram includes 14 clean-room layout presets. They are generated by the
preset compiler and can be used as starting points or as examples for hand-made
DiagramScript specs.

| Preset | Layout Shape | Best For | Default Style |
| --- | --- | --- | --- |
| `pipeline` | Left-to-right chain | ETL, build, review, release flows | `blueprint` |
| `loop` | Circular feedback loop | observe-decide-act-learn systems | `claude-warm` |
| `hub-spoke` | Central hub with radial dependencies | agents, coordinators, service hubs | `deep-tech` |
| `layered` | Horizontal architecture layers | UI/domain/data separation | `notion-clean` |
| `swimlane` | Owner lanes with handoffs | customer/team/system workflows | `minimal-light` |
| `compare` | Two framed option groups | tradeoffs and decision comparisons | `openai-minimal` |
| `matrix` | 2x2 quadrant board | prioritization and portfolio mapping | `flat-icon` |
| `timeline` | Milestones along a line | roadmap and release phases | `blueprint` |
| `stack` | Vertical dependency stack | infrastructure and runtime layers | `dark-terminal` |
| `funnel` | Narrowing vertical stages | qualification and conversion flows | `glassmorphism` |
| `sequence` | Ordered participant messages | request/response and call chains | `notion-clean` |
| `er` | Entity relationship graph | data models and ownership links | `openai-minimal` |
| `network` | Distributed graph with cross-links | systems, caches, workers, fanout | `dark-luxury` |
| `agent-memory` | Agent runtime plus knowledge panel | tool use, memory, retrieval, answers | `blueprint` |

List them with:

```bash
PYTHONPATH=src python3 -m anidiagram.cli --list-presets
```

DiagramScript also supports freeform layout controls:

| Field | Values | Use |
| --- | --- | --- |
| `node.position` | `[x, y]` | Absolute node placement. |
| `node.size` | `[width, height]` | Fixed node dimensions. |
| `group.bounds` | `[x, y, width, height]` | Framed layout regions. |
| `edge.route` | `curved`, `straight`, `hv`, `vh`, `orthogonal`, `points` | Edge routing style. |
| `edge.points` | list of `[x, y]` points | Explicit path geometry when `route` is `points`. |
| `node.step` / `edge.step` | integer | Visible step badges for ordered diagrams. |

## Styles

Bundled styles define color, typography-like spacing, node borders, group
treatment, and optional style-compatible motion defaults.

| Style | Visual Direction | Good Fit |
| --- | --- | --- |
| `minimal-light` | White canvas, quiet grid, restrained borders | neutral workflows and docs |
| `deep-tech` | Dark technical canvas with bright role colors | agent and infrastructure maps |
| `blueprint` | Navy grid, technical linework, high contrast | architecture and engineering diagrams |
| `flat-icon` | Light surface, strong role colors, simple icon-like blocks | matrices and product explainers |
| `dark-terminal` | Black terminal-like surface, compact borders | stacks, ops flows, CLI systems |
| `notion-clean` | White document surface, thin borders, muted palette | specs, process docs, product flows |
| `glassmorphism` | Soft translucent panels on a cool canvas | funnels and presentation-style flows |
| `claude-warm` | Warm paper tone with muted accents | reasoning loops and planning diagrams |
| `openai-minimal` | Stark white/black minimal style | clean product and system diagrams |
| `dark-luxury` | Black canvas with restrained premium accents | executive maps and high-level networks |
| `aurora-orb` | Rounded aurora color fills and soft canvas treatment | expressive previews and showcase diagrams |
| `sketch-board` | Teaching-board style with semantic icons and active motion defaults | educational walkthroughs |

Style catalog: [styles/catalog.json](./styles/catalog.json)

Style files live in [styles/](./styles/) and can define `motion_defaults`.
Scene-level motion still wins unless the scene uses the normal profile and the
style provides a compatible default.

## Gallery

Regenerate the committed gallery assets:

```bash
PYTHONPATH=src python3 scripts/batch_render.py --outdir gallery --quality
PYTHONPATH=src python3 scripts/build_style_showcase.py --quality
```

## Motion Design

The current renderer uses dependency-free SVG/SMIL motion inspired by common
open-source animation patterns: draw-on paths, staggered timelines, flow
particles, glow, and burst rings. Research notes live in
[docs/motion-research.md](./docs/motion-research.md).
The next feature direction for richer line, border, icon, and teaching-diagram
effects is tracked in
[docs/motion-effects-feature-plan.md](./docs/motion-effects-feature-plan.md).

Motion can be configured at the scene level and overridden per node, edge, or
group. DiagramScript v0.2 supports string motion channels. DiagramScript v0.3
also supports structured effect objects.

### Motion Profiles

| Profile | Default Behavior |
| --- | --- |
| `off` | Static output with inactive motion channels. |
| `subtle` | Step-staggered, calm motion with fade nodes, draw-on edges, and soft group reveal. |
| `normal` | Balanced default motion with glow-breathe nodes, comet-flow edges, and marching group boundaries. |
| `expressive` | Stronger layered motion with pop nodes, comet-flow edges, and animated group borders. |
| `teaching` | Staged teaching motion with icon pulses, ghost-flow edges, border scans, and title reveal. |

### Motion Sequencing

| Field | Supported Values |
| --- | --- |
| `motion.sequence` | `simultaneous`, `step-stagger`, `layered`, `staged` |
| `motion.ease` | `linear`, `calm`, `snappy`, `back-out`, `elastic`, `spring` |
| `motion.reduced_motion` | `static`, `subtle`, `pause` |

Numeric controls:

| Field | Use |
| --- | --- |
| `motion.stagger` | Delay between staged items. |
| `motion.duration_scale` | Multiplier for animation timing. |
| `motion.intensity` | Overall strength for glow, pulse, and particle effects. |

### Node Motion Types

| Value | Effect |
| --- | --- |
| `none` | No node motion. |
| `fade` | Opacity reveal. |
| `float` | Slow vertical drift. |
| `glow-breathe` | Soft glow pulse around the node. |
| `pop` | Scale and opacity entry. |
| `pulse` | Repeating stroke/glow emphasis. |
| `ripple` | Expanding emphasis rings. |
| `status-blink` | Low-duty active status indicator. |
| `icon-pulse` | Pulse focused on the node's semantic icon. |

### Edge Motion Types

| Value | Effect |
| --- | --- |
| `none` | No edge motion. |
| `static` | Static line, useful as an explicit non-moving override. |
| `draw` | Path draws on once. |
| `pulse` | Animated overlay pulse on the line. |
| `comet-flow` | Bright particle with a fading trail. |
| `trace` | Moving trace dash along the path. |
| `dynamic-dash` | Moving dashed stroke. |
| `flow-dot` | Soft circular particles move along the path. |
| `flow-arrow` | Semi-transparent arrow particles move along the path. |
| `ghost-flow` | Particle trail with translucent echoes. |
| `glow-line` | Low-frequency glow pulse on the line. |
| `comet` | Alias-style comet preset for bright leading flow. |

### Group Motion Types

| Value | Effect |
| --- | --- |
| `none` | No group motion. |
| `static` | Static group panel. |
| `soft-reveal` | Group fades in before child content. |
| `marching-ants` | Moving dashed panel boundary. |
| `border-scan` | Light sweep around the group border. |
| `corner-pulse` | Animated corner ticks frame the group. |

### Title Motion Types

| Value | Effect |
| --- | --- |
| `none` | No title motion. |
| `fade` | Subtle title reveal. |
| `handwrite-reveal` | Handwritten underline/reveal accent. |
| `highlight-sweep` | Soft highlight sweeps behind the title. |

### Semantic Icons

DiagramScript v0.3 nodes can set `icon` to one of:

`database`, `file`, `folder`, `api`, `cloud`, `search`, `shield`, `agent`,
`token`, `memory`, `tool`, `output`.

### Effect Object Fields

Structured effects can be used in `motion.edge`, `motion.node`,
`motion.group`, `motion.title`, or on individual `node.effect`, `edge.effect`,
and `group.effect`.

| Field | Use |
| --- | --- |
| `preset` | Main effect type for that channel. |
| `line` | Optional line treatment hint. |
| `particle` | Optional particle shape hint such as `soft-dot` or `soft-arrow`. |
| `trail` | Optional trail hint; boolean values are accepted. |
| `entry` | Optional node/title entry hint. |
| `accent` | Optional accent effect such as ripple. |
| `icon` | Optional icon-local treatment hint. |

String motion example:

```json
{
  "motion": {
    "profile": "expressive",
    "sequence": "layered",
    "edge": "comet-flow",
    "node": "pop",
    "group": "marching-ants",
    "reduced_motion": "subtle"
  }
}
```

Structured motion example:

```json
{
  "motion": {
    "profile": "teaching",
    "edge": {"preset": "ghost-flow", "particle": "soft-dot", "trail": true},
    "node": {"preset": "icon-pulse", "accent": "ripple"},
    "group": {"preset": "border-scan"},
    "title": {"preset": "handwrite-reveal"}
  }
}
```

Try the clean-room teaching example:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/teaching-transformer.diagram.json \
  --style styles/sketch-board.json \
  --outdir outputs \
  --basename teaching-transformer \
  --all
```

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Clean-Room Boundary

The project can reference prior art at the concept level, but its code,
schema, assets, examples, and documentation are authored independently.

If code or assets are ever copied from MIT-licensed references, this project
must add their original license notices before release.
