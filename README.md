# AniDiagram

Language: English | [简体中文](./README.zh-CN.md)

Clean-room DiagramScript renderer for animated architecture visuals.

This repository is not a GitHub fork and does not copy source code, documents,
images, generated assets, or repository history from the projects listed in
[REFERENCES.md](./REFERENCES.md).

## Showcase

AniDiagram uses two complementary galleries:

- **Style Showcase**: 12 signature cases, one for every visual style. This
  answers "how can it look?"
- **Layout Showcase**: 14 teaching cases, one for every clean-room layout
  preset. This answers "when should I use this layout?"

Gallery source: `gallery/index.html`
Machine-readable manifest: [gallery/showcase_manifest.json](./gallery/showcase_manifest.json)

The README hero uses a browser-captured animated preview from the GSAP runtime,
so the first viewport can show the high-fidelity motion directly on GitHub.
The style and layout grids keep lightweight SVG previews for readability and
page weight. Interactive `.html` runtime pages need to be served by a static
host such as GitHub Pages, or opened through a local static server.

### Hero Demo

| Agent Runtime Flow |
| --- |
| [![Agent Runtime Flow](./gallery/previews/agent-runtime-flow.webp)](./gallery/previews/agent-runtime-flow.mp4)<br>Browser-captured runtime preview with agent think-act, search discover, API request/response, and memory commit motion.<br>[GIF](./gallery/previews/agent-runtime-flow.gif) · [APNG](./gallery/previews/agent-runtime-flow.apng) · Runtime HTML: `gallery/hero/agent-runtime-flow.html` |

To open the interactive runtime locally:

```bash
python3 -m http.server 8765
```

Then visit `http://127.0.0.1:8765/gallery/hero/agent-runtime-flow.html`.
When publishing with GitHub Pages, link README buttons to the Pages URL instead
of GitHub's `blob` file view.

### Style Showcase

Each bundled style has a clean-room signature case plus rendered SVG/HTML
assets. README cards link to portable SVG previews; serve `gallery/` locally or
through GitHub Pages to open the high-fidelity HTML runtime.

| `minimal-light` | `deep-tech` | `blueprint` |
| --- | --- | --- |
| [![minimal-light style showcase](./gallery/styles/minimal-light.svg)](./gallery/styles/minimal-light.svg)<br>Customer Support Triage | [![deep-tech style showcase](./gallery/styles/deep-tech.svg)](./gallery/styles/deep-tech.svg)<br>Realtime AI Ops Mesh | [![blueprint style showcase](./gallery/styles/blueprint.svg)](./gallery/styles/blueprint.svg)<br>MCP Server Architecture |

| `flat-icon` | `dark-terminal` | `notion-clean` |
| --- | --- | --- |
| [![flat-icon style showcase](./gallery/styles/flat-icon.svg)](./gallery/styles/flat-icon.svg)<br>Feature Priority Board | [![dark-terminal style showcase](./gallery/styles/dark-terminal.svg)](./gallery/styles/dark-terminal.svg)<br>Incident Response Runbook | [![notion-clean style showcase](./gallery/styles/notion-clean.svg)](./gallery/styles/notion-clean.svg)<br>Product Discovery Workflow |

| `glassmorphism` | `claude-warm` | `openai-minimal` |
| --- | --- | --- |
| [![glassmorphism style showcase](./gallery/styles/glassmorphism.svg)](./gallery/styles/glassmorphism.svg)<br>AI Growth Funnel | [![claude-warm style showcase](./gallery/styles/claude-warm.svg)](./gallery/styles/claude-warm.svg)<br>Research Reasoning Loop | [![openai-minimal style showcase](./gallery/styles/openai-minimal.svg)](./gallery/styles/openai-minimal.svg)<br>Evaluation Pipeline |

| `dark-luxury` | `aurora-orb` | `sketch-board` |
| --- | --- | --- |
| [![dark-luxury style showcase](./gallery/styles/dark-luxury.svg)](./gallery/styles/dark-luxury.svg)<br>Executive Signal Network | [![aurora-orb style showcase](./gallery/styles/aurora-orb.svg)](./gallery/styles/aurora-orb.svg)<br>Creative Agent Studio | [![sketch-board style showcase](./gallery/styles/sketch-board.svg)](./gallery/styles/sketch-board.svg)<br>Attention Teaching Flow |

Full style showcase source: `gallery/styles/index.html`

### Layout Showcase

Each layout preset has a concrete AI/product case that demonstrates when the
layout is useful.

| `pipeline` | `loop` |
| --- | --- |
| [![pipeline layout showcase](./gallery/layouts/pipeline.svg)](./gallery/layouts/pipeline.svg)<br>RAG Ingestion Pipeline | [![loop layout showcase](./gallery/layouts/loop.svg)](./gallery/layouts/loop.svg)<br>Agent Reflection Loop |

| `hub-spoke` | `layered` |
| --- | --- |
| [![hub-spoke layout showcase](./gallery/layouts/hub-spoke.svg)](./gallery/layouts/hub-spoke.svg)<br>Agent Tool Hub | [![layered layout showcase](./gallery/layouts/layered.svg)](./gallery/layouts/layered.svg)<br>LLM App Architecture Layers |

| `swimlane` | `compare` |
| --- | --- |
| [![swimlane layout showcase](./gallery/layouts/swimlane.svg)](./gallery/layouts/swimlane.svg)<br>Human-in-the-loop Approval Flow | [![compare layout showcase](./gallery/layouts/compare.svg)](./gallery/layouts/compare.svg)<br>RAG vs Agentic RAG |

| `matrix` | `timeline` |
| --- | --- |
| [![matrix layout showcase](./gallery/layouts/matrix.svg)](./gallery/layouts/matrix.svg)<br>AI Feature Priority Matrix | [![timeline layout showcase](./gallery/layouts/timeline.svg)](./gallery/layouts/timeline.svg)<br>AI Product Launch Roadmap |

| `stack` | `funnel` |
| --- | --- |
| [![stack layout showcase](./gallery/layouts/stack.svg)](./gallery/layouts/stack.svg)<br>AI Runtime Stack | [![funnel layout showcase](./gallery/layouts/funnel.svg)](./gallery/layouts/funnel.svg)<br>Lead-to-Agent Automation Funnel |

| `sequence` | `er` |
| --- | --- |
| [![sequence layout showcase](./gallery/layouts/sequence.svg)](./gallery/layouts/sequence.svg)<br>API Tool Calling Sequence | [![er layout showcase](./gallery/layouts/er.svg)](./gallery/layouts/er.svg)<br>Agent Memory Data Model |

| `network` | `agent-memory` |
| --- | --- |
| [![network layout showcase](./gallery/layouts/network.svg)](./gallery/layouts/network.svg)<br>Distributed Agent Runtime Mesh | [![agent-memory layout showcase](./gallery/layouts/agent-memory.svg)](./gallery/layouts/agent-memory.svg)<br>Personalized Agent Memory Flow |

Full layout showcase source: `gallery/layouts/index.html`

### Runtime Motion Showcase

The P0 high-fidelity runtime demonstrates four semantic icon performances:

| Performance | Semantic beat |
| --- | --- |
| `agent-think-act-v2` | think dots gather, core decides, decision token exits |
| `search-discover-v2` | scan, discover results, lock target |
| `api-request-response-v2` | request travels out, response returns, status resolves |
| `database-write-v2` | write token lands, storage reacts, commit flash resolves |

## What It Does

- Validates DiagramScript `0.1`, `0.2`, and `0.3`.
- Compiles natural-language briefs into DiagramPlan v0.1 and then freeform
  DiagramScript v0.3.
- Compiles JSON specs or presets into a typed Scene IR.
- Renders portable animated SVG and high-fidelity HTML runtime output.
- Uses richer motion layers: staggered entry, line drawing, flow particles,
  node glow, burst rings, and animated group boundaries.
- Supports scene-level motion profiles for `off`, `subtle`, `normal`,
  `expressive`, and `teaching` animation behavior.
- Supports structured motion effect objects for line flow, arrow particles,
  dynamic dashes, border scans, icon pulses, and title reveal effects.
- Supports `motion_policy` budgets so generated diagrams can keep a few focused
  animated paths without turning every element on at once.
- Exports optional PNG, GIF, PDF, WebP, MP4, APNG, and Lottie files.
- Produces quality reports for bounds, overlaps, text fit, and explicit paths.
- Includes 14 clean-room preset compilers and 12 visual styles.

SVG, debug viewer HTML, Lottie, and quality reports use the Python standard
library. The primary `html` export writes a high-fidelity runtime page with a
static SVG stage, named parts, a Motion Manifest, and a browser runtime; its
GSAP backend loads GSAP from a CDN and does not add a Python dependency. Raster,
video, PDF, and Lottie exports default to the lightweight Python renderer. For
highest-fidelity output, pass `--export-renderer browser` so PNG, GIF, PDF,
WebP, MP4, APNG, and Lottie are captured from the real HTML runtime with
Playwright/Chromium. Browser-captured Lottie is frame-based, so it is visually
faithful but larger than the default structured Lottie JSON. GIF/WebP/APNG
packaging still needs Pillow, and MP4 still needs `ffmpeg`.

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

Compile a natural-language brief into a complex freeform diagram:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --brief examples/briefs/loop-engineering.txt \
  --style styles/sketch-board.json \
  --outdir outputs \
  --basename loop-engineering \
  --formats svg,html,quality \
  --plan-out outputs/loop-engineering.plan.json \
  --spec-out outputs/loop-engineering.diagram.json
```

Render the high-fidelity HTML runtime demo:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/high-fidelity-runtime.diagram.json \
  --style styles/deep-tech.json \
  --outdir outputs \
  --basename high-fidelity-runtime \
  --formats svg,html,quality \
  --html-runtime gsap
```

Write the legacy debug viewer when needed:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/agent-memory.diagram.json \
  --outdir outputs \
  --basename agent-memory \
  --formats viewer
```

Export high-fidelity raster, video, PDF, and Lottie from the browser runtime:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/high-fidelity-runtime.diagram.json \
  --style styles/deep-tech.json \
  --outdir outputs \
  --basename high-fidelity-runtime-hq \
  --formats png,gif,webp,apng,mp4,pdf,lottie,quality \
  --html-runtime gsap \
  --export-renderer browser \
  --export-scale 2 \
  --export-fps 24 \
  --export-frames 48
```

Install optional raster dependencies:

```bash
python3 -m pip install ".[raster]"
```

Browser-rendered exports also require Node.js plus Playwright with Chromium
available to Node's module resolver.

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
- [schemas/diagram-plan-v0.1.schema.json](./schemas/diagram-plan-v0.1.schema.json)
- [schemas/style-profile-v0.1.schema.json](./schemas/style-profile-v0.1.schema.json)

v0.2 adds route types, step badges, preset metadata, and stricter role
validation. v0.3 adds structured effect objects, semantic icons, and node
shapes. See
[docs/diagram-script.md](./docs/diagram-script.md).

DiagramPlan v0.1 is the higher-level brief/LLM contract. The current local
planner and compiler are documented in
[docs/prompt-to-diagram-flow.md](./docs/prompt-to-diagram-flow.md).

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
| `node.shape` | `rect`, `decision` | Rectangle or diamond decision node. |

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
PYTHONPATH=src python3 scripts/build_showcase.py --quality
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
| `runtime-loop` | Static structure with looping signal flow, icon breathing, static groups, and breathing title. |

### Motion Sequencing

| Field | Supported Values |
| --- | --- |
| `motion.sequence` | `simultaneous`, `step-stagger`, `layered`, `staged`, `loop` |
| `motion.ease` | `linear`, `calm`, `snappy`, `back-out`, `elastic`, `spring` |
| `motion.reduced_motion` | `static`, `subtle`, `pause` |

Numeric controls:

| Field | Use |
| --- | --- |
| `motion.stagger` | Delay between staged items. |
| `motion.duration_scale` | Multiplier for animation timing. |
| `motion.intensity` | Overall strength for glow, pulse, and particle effects. |

### Motion Policy

`motion_policy` controls how much motion may be active after all scene-level and
per-element effects are resolved. This is useful for generated diagrams: the
spec can keep semantic effects on important elements, while the renderer clamps
extras into calmer draw/fade behavior.

| Field | Use |
| --- | --- |
| `profile` | `unrestricted`, `readable`, `focused`, `expressive`, or `readable-runtime` budget defaults. |
| `motion_area` | `auto`, `micro`, `small`, `medium`, or `unrestricted`; currently scales particle size for low-area motion. |
| `max_active_flow_edges` | Maximum number of continuously animated edges. |
| `max_particle_edges` | Maximum number of edges allowed to show moving particles/arrows. |
| `particle_count_per_edge` | Default particle count on each animated particle edge. |
| `flow_trail_count` | Maximum particle trail/echo count per edge. |
| `max_active_pulse_nodes` | Maximum number of nodes allowed to pulse/glow/float. |
| `pulse_mode` | `all` or `rotate`; current renderers use the value as policy metadata. |
| `max_scanning_groups` | Maximum number of animated group borders. |

Recommended defaults:

| Profile | Recommended Use |
| --- | --- |
| `readable` | Dense architecture diagrams where motion should be sparse. |
| `focused` | Teaching/explainer diagrams with a small number of active paths. |
| `expressive` | Showcase diagrams that can tolerate more visible motion. |

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
| `icon-breathe` | Gentle semantic-icon scale/halo breathing; node frame stays still. |
| `icon-semantic` | Icon-local motion matched to the semantic icon, such as database writes or shield checks. |
| `icon-performance` | Runtime-ready semantic icon performance. SVG uses lightweight SMIL fallback; `html` plays the high-fidelity micro-performance from the Motion Manifest. |
| `micro-icon` | Alias-style micro icon breathing for runtime diagrams. |

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
| `dash-flow` | Marching dashed arrow effect where the dash continuity appears to move forward. |
| `flow-dot` | Soft circular particles move along the path. |
| `flow-arrow` | Semi-transparent arrow particles move along the path. |
| `signal-dot` | One small signal point moves along a complete static path. |
| `signal-arrow` | One small arrow-like signal moves along a complete static path. |
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
| `breathe` | Gentle title opacity breathing without sliding or jumping. |
| `handwrite-reveal` | Handwritten underline/reveal accent. |
| `highlight-sweep` | Soft highlight sweeps behind the title. |

### Semantic Icons

DiagramScript v0.3 nodes can set `icon` to one of:

`database`, `file`, `folder`, `api`, `cloud`, `search`, `shield`, `agent`,
`token`, `memory`, `tool`, `output`.

`icon-semantic` maps common icons to local micro-motions:

| Icon | Default icon motion |
| --- | --- |
| `database` | `database-write`: top ellipse compresses/rebounds, a write line scans across, a data point enters, and the lower layer flashes lightly. |
| `memory` | Stacked memory cards with trace lines for context or agent memory. |
| `file` | `file-lines`: page enters from lower-left, overshoots scale, folds the corner, then draws content lines quickly. |
| `folder` | `folder-open`: folder tab opens and exposes a short internal file line. |
| `api` | `api-ping`: request point travels between brackets. |
| `cloud` | `cloud-upload`: upload arrow moves inside the cloud with faint transfer dots. |
| `search` | `search-sweep`: lens sweep highlight plus a small light point. |
| `shield` | `shield-check`: checkmark draws and a low-opacity protection pulse follows the shield outline. |
| `agent` | `agent-orbit`: brain-like circuit icon with a small local status pulse. |
| `tool` | `tool-tap`: short tool tap motion with a contact spark. |
| `output` | `output-check`: result lines reveal first, then the checkmark draws. |
| `token` | `token-pulse`: center pulse plus short outer ticks lighting in sequence. |

The primary `html` runtime currently maps these high-fidelity v2 performances:

| Icon | Runtime performance |
| --- | --- |
| `agent` | `agent-think-act-v2`: thought dots gather into the core, the core pulses as a decision, then a decision token exits the agent. |
| `api` | `api-request-response-v2`: endpoints react, a request token travels out, a response returns, and status pops. |
| `search` | `search-discover-v2`: lens tilts, scan light sweeps, result dots pop, and a target is selected. |
| `database` | `database-write-v2`: write token lands, the lid squashes, layers commit, and a success flash settles. |
| `memory` | `memory-commit-v2`: a context token lands, memory cards settle, trace lines light, and a commit flash resolves. |
| `tool` | `tool-run-v2`: the function chip presses, connector dot fires, sparks draw, and a flash resolves. |
| `token` | `token-intent-v2`: the token shell pops in, the core pulses, ticks draw, and a halo releases. |
| `output` | `output-reveal-v2`: the result card settles, lines reveal, the check draws, and a final flash resolves. |

The runtime is driven by a `<script type="application/json"
id="anidiagram-motion-manifest">` block. Each entry points to stable SVG part
IDs such as `#icon-agent-thought-1` or `#icon-api-request-token`; the JavaScript
runtime does not infer semantics from arbitrary paths or classes.
See [docs/html-runtime.md](./docs/html-runtime.md) for runtime ownership,
current performance coverage, and export notes.

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
| `particle_count` | Per-edge override for the number of moving particles. |
| `trail_count` | Per-edge override for the maximum trail/echo count. |
| `entry` | Optional node/title entry hint. |
| `accent` | Optional accent effect such as ripple. |
| `icon` | Optional icon-local treatment hint. |
| `icon_motion` | Optional icon-local motion id such as `database-write` or `shield-check`. |

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
    "edge": {"preset": "ghost-flow", "particle": "soft-dot", "trail": true, "particle_count": 1},
    "node": {"preset": "icon-semantic", "icon_motion": "database-write"},
    "group": {"preset": "border-scan"},
    "title": {"preset": "handwrite-reveal"}
  },
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

Try the clean-room teaching example:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/teaching-transformer.diagram.json \
  --style styles/sketch-board.json \
  --outdir outputs \
  --basename teaching-transformer \
  --all
```

Try the runtime-loop motion example:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/runtime-loop-motion.diagram.json \
  --style styles/minimal-light.json \
  --outdir outputs \
  --basename runtime-loop-motion \
  --formats svg,html,quality
```

Try the high-fidelity runtime example:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/high-fidelity-runtime.diagram.json \
  --style styles/deep-tech.json \
  --outdir outputs \
  --basename high-fidelity-runtime \
  --formats svg,html,quality \
  --html-runtime gsap
```

Try browser-captured high-fidelity exports:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/high-fidelity-runtime.diagram.json \
  --style styles/deep-tech.json \
  --outdir outputs \
  --basename high-fidelity-runtime-hq \
  --formats png,gif,webp,apng,mp4,pdf,lottie,quality \
  --html-runtime gsap \
  --export-renderer browser \
  --export-scale 2 \
  --export-fps 24 \
  --export-frames 48
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
