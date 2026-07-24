# AniDiagram

Language: English | [简体中文](./README.zh-CN.md)

Clean-room DiagramScript renderer for animated architecture visuals.

This repository is not a GitHub fork and does not copy source code, documents,
images, generated assets, or repository history from the projects listed in
[REFERENCES.md](./REFERENCES.md).

## Showcase

AniDiagram uses two complementary galleries:

- **Style Showcase**: 13 signature cases, one for every public visual style. This
  answers "how can it look?"
- **Layout Showcase**: 14 teaching cases, one for every clean-room layout
  preset. This answers "when should I use this layout?"

Gallery source: `gallery/index.html`
Machine-readable manifest: [gallery/showcase_manifest.json](./gallery/showcase_manifest.json)
Runtime motion management: [gallery/runtime-motion.html](./gallery/runtime-motion.html)
Catalog source of truth: [runtime/motion-catalog.json](./runtime/motion-catalog.json)

The README hero uses a browser-captured animated preview from the GSAP runtime,
so the first viewport can show the high-fidelity motion directly on GitHub.
The style and layout grids keep lightweight SVG previews for readability and
page weight. Interactive `.html` runtime pages need to be served by a static
host such as GitHub Pages, or opened through a local static server.

### Hero Demo

| Agent Runtime Flow |
| --- |
| [![Agent Runtime Flow](./gallery/previews/agent-runtime-flow.webp)](./gallery/previews/agent-runtime-flow.mp4)<br>Browser-captured `illustrated-character-v1` runtime preview: a focal agent branches into retrieval/memory, policy verification, and tool/API paths before converging on the output.<br>[GIF](./gallery/previews/agent-runtime-flow.gif) · [APNG](./gallery/previews/agent-runtime-flow.apng) · Runtime HTML: `gallery/hero/agent-runtime-flow.html` |

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

| `minimal-light` | `deep-tech` |
| --- | --- |
| [![minimal-light style showcase](./gallery/styles/minimal-light.svg)](./gallery/styles/minimal-light.svg)<br>Customer Support Triage | [![deep-tech style showcase](./gallery/styles/deep-tech.svg)](./gallery/styles/deep-tech.svg)<br>Realtime AI Ops Mesh |

| `blueprint` | `flat-icon` |
| --- | --- |
| [![blueprint style showcase](./gallery/styles/blueprint.svg)](./gallery/styles/blueprint.svg)<br>MCP Server Architecture | [![flat-icon style showcase](./gallery/styles/flat-icon.svg)](./gallery/styles/flat-icon.svg)<br>Feature Priority Board |

| `dark-terminal` | `notion-clean` |
| --- | --- |
| [![dark-terminal style showcase](./gallery/styles/dark-terminal.svg)](./gallery/styles/dark-terminal.svg)<br>Incident Response Runbook | [![notion-clean style showcase](./gallery/styles/notion-clean.svg)](./gallery/styles/notion-clean.svg)<br>Product Discovery Workflow |

| `glassmorphism` | `claude-warm` |
| --- | --- |
| [![glassmorphism style showcase](./gallery/styles/glassmorphism.svg)](./gallery/styles/glassmorphism.svg)<br>AI Growth Funnel | [![claude-warm style showcase](./gallery/styles/claude-warm.svg)](./gallery/styles/claude-warm.svg)<br>Research Reasoning Loop |

| `openai-minimal` | `dark-luxury` |
| --- | --- |
| [![openai-minimal style showcase](./gallery/styles/openai-minimal.svg)](./gallery/styles/openai-minimal.svg)<br>Evaluation Pipeline | [![dark-luxury style showcase](./gallery/styles/dark-luxury.svg)](./gallery/styles/dark-luxury.svg)<br>Executive Signal Network |

| `aurora-orb` | `sketch-board` |
| --- | --- |
| [![aurora-orb style showcase](./gallery/styles/aurora-orb.svg)](./gallery/styles/aurora-orb.svg)<br>Creative Agent Studio | [![sketch-board style showcase](./gallery/styles/sketch-board.svg)](./gallery/styles/sketch-board.svg)<br>Attention Teaching Flow |

Additional public style: [`illustrated-semantic` — Semantic Delivery Pipeline](./gallery/styles/illustrated-semantic.svg).

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

The high-fidelity runtime now covers every built-in semantic icon. The core
performances are:

Review the frozen baseline through [gallery/runtime-motion.html](./gallery/runtime-motion.html).
It embeds a live runtime overview, lists the stage effects and stable icon
parts, and links to the machine-readable catalog. Changes to visual timing,
intensity, icon semantics, stable part IDs, stage effects, default mode/profile,
or runtime scheduling must be confirmed before implementation.

| Performance | Semantic beat |
| --- | --- |
| `agent-think-act-v2` | brain circuit draws, nodes light, decision token exits |
| `search-discover-v2` | scan, discover results, lock target |
| `api-request-response-v2` | request travels out, response returns, status resolves |
| `database-write-v2` | write token lands, storage reacts, commit flash resolves |
| `memory-commit-v2` | context token lands, memory cards settle, traces commit |
| `tool-run-v2` | tool chip presses, connector fires, sparks resolve |
| `token-intent-v2` | token shell pops, intent ticks draw, halo releases |
| `output-reveal-v2` | output card settles, lines reveal, check completes |
| `file-lines-v2` | document lands, fold reacts, lines draw in |
| `folder-open-v2` | folder opens, token enters, file line reveals |
| `cloud-upload-v2` | upload arrow rises, transfer dots pulse, status ring resolves |
| `shield-check-v2` | shield scans, check draws, protection pulse resolves |

## What It Does

- Validates DiagramScript `0.1` through `0.4`.
- Compiles natural-language briefs into semantic-first DiagramPlan v0.2 and
  resolved DiagramScript v0.4. The v0.1 -> v0.3 planner remains available as
  an explicit legacy path.
- Compiles JSON specs or presets into a typed Scene IR.
- Renders portable animated SVG and high-fidelity HTML runtime output.
- Uses richer motion layers: staggered entry, line drawing, flow particles,
  node glow, burst rings, and animated group boundaries.
- Uses `showcase-v1` for composition-v1 output. Direct DiagramScript that omits
  motion retains the compatibility default `expressive`; lower-motion profiles
  such as `off`, `subtle`, and `normal` remain available.
- Supports structured motion effect objects for line flow, arrow particles,
  dynamic dashes, border scans, icon pulses, and title reveal effects.
- Supports `motion_policy` budgets so generated diagrams can keep a few focused
  animated paths without turning every element on at once.
- Exports optional PNG, GIF, PDF, WebP, MP4, APNG, and Lottie files.
- Produces quality reports for bounds, overlaps, text fit, and explicit paths.
- Includes 14 clean-room preset compilers and 13 public visual styles.

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

Compile an authored DiagramPlan v0.2 into resolved DiagramScript v0.4:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --plan examples/contracts/production-request-path.plan.json \
  --spec-out outputs/production-request-path.diagram.json \
  --outdir outputs \
  --basename production-request-path \
  --formats svg,html,quality
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
- [schemas/diagram-script-v0.4.schema.json](./schemas/diagram-script-v0.4.schema.json) — composition-v1 resolved output
- [schemas/diagram-plan-v0.1.schema.json](./schemas/diagram-plan-v0.1.schema.json)
- [schemas/diagram-plan-v0.2.schema.json](./schemas/diagram-plan-v0.2.schema.json) — implemented semantic-first composition contract
- [schemas/style-profile-v0.1.schema.json](./schemas/style-profile-v0.1.schema.json)

v0.2 adds route types, step badges, preset metadata, and stricter role
validation. v0.3 adds structured effect objects, semantic icons, and node
shapes. v0.4 adds an independent top-level icon system, resolved presentation
provenance, the Diagram Core default, and `showcase-v1`. See
[docs/diagram-script.md](./docs/diagram-script.md).

DiagramPlan v0.2 is the default higher-level brief/LLM contract; v0.1 remains
available for legacy `explainer-board` compilation. The planner and compiler are documented in
[docs/prompt-to-diagram-flow.md](./docs/prompt-to-diagram-flow.md).
The implemented composition contract separates semantic content from icon,
style, layout, and motion selection; see
[docs/diagram-composition-contract.md](./docs/diagram-composition-contract.md)
and [ADR-001](./docs/decisions/ADR-001-separate-semantic-content-from-presentation.md).

Current defaults are scoped by input contract:

| Input path | Default icon system | Default motion |
| --- | --- | --- |
| DiagramPlan v0.2 compiled through `composition-v1` to DiagramScript v0.4 | `diagram-core-v1` | `showcase-v1` |
| Direct DiagramScript v0.4 without `composition_policy` | `diagram-core-v1` | `expressive` when `motion` is omitted |
| Legacy DiagramScript v0.1-v0.3 or a style that omits `icon_system` | `illustrated-character-v1` | `expressive` when scene motion is omitted |

`illustrated` is an explicit, non-default public icon-system choice. Its current
implementation version is 2.5.0 and its 56 icons use the approved
`illustrated-performance-v6` contract automatically under `showcase-v1`. See
[the icon-system release status](./docs/icon-system-release-status.md) for the
current/default/legacy matrix.

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
| `illustrated-semantic` | Warm off-white canvas, low-saturation semantic fills, quiet framing | clear illustrated workflows and technical explainers |
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
| `normal` | Balanced compatibility motion with glow-breathe nodes, comet-flow edges, and marching group boundaries. |
| `expressive` | Compatibility high-fidelity default with pop nodes, comet-flow edges, title sweep, and animated group borders. |
| `teaching` | Staged teaching motion with icon pulses, ghost-flow edges, border scans, and title reveal. |
| `runtime-loop` | Static structure with looping signal flow, icon breathing, static groups, and breathing title. |
| `showcase-v1` | Composition-v1 default: every eligible icon performance and data-flow edge is enabled, with authored rest poses and reduced-motion support. |

`expressive` remains the compatibility default when a direct DiagramScript
omits `motion`. New DiagramPlan v0.2 work resolves `showcase-v1` explicitly.

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
| `expressive` | Direct or legacy DiagramScript high-fidelity runtime diagrams. |

For composition-v1, `showcase-v1` is `motion.profile`, not a
`motion_policy.profile`. The compiler pairs it with the unrestricted budget:
`motion_policy.profile=unrestricted`, `motion_area=unrestricted`, and
`pulse_mode=all`.

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
| `packet-flow` | One borderless solid packet moves along a static arrow. |
| `comet-flow` | One borderless leading packet moves with three shrinking fading echoes. |
| `stream-flow` | One moving dashed stroke communicates a continuous or cyclic flow. |

The former edge presets remain valid input aliases and normalize to these
non-overlapping recipes. Edge Motion v1.0.0 is the frozen, human-approved
connection-line contract. See [Edge Motion v1](docs/edge-motion-v1.md).

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
| `agent` | `agent-think-act-v2`: brain-circuit lines draw outward, nodes light up, a decision pulse resolves, then a decision token exits the agent. |
| `api` | `api-request-response-v2`: endpoints react, a request token travels out, a response returns, and status pops. |
| `search` | `search-discover-v2`: lens tilts, scan light sweeps, result dots pop, and a target is selected. |
| `database` | `database-write-v2`: write token lands, the lid squashes, layers commit, and a success flash settles. |
| `memory` | `memory-commit-v2`: a context token lands, memory cards settle, trace lines light, and a commit flash resolves. |
| `tool` | `tool-run-v2`: the function chip presses, connector dot fires, sparks draw, and a flash resolves. |
| `token` | `token-intent-v2`: the token shell pops in, the core pulses, ticks draw, and a halo releases. |
| `output` | `output-reveal-v2`: the result card settles, lines reveal, the check draws, and a final flash resolves. |
| `file` | `file-lines-v2`: the document lands, the folded corner reacts, lines draw in, and a flash resolves. |
| `folder` | `folder-open-v2`: the folder opens, an input token enters, a file line reveals, and a flash resolves. |
| `cloud` | `cloud-upload-v2`: the upload arrow rises, transfer dots pulse, and the status ring resolves. |
| `shield` | `shield-check-v2`: the shield scans, the check draws in, and a protection pulse resolves. |

The runtime is driven by a `<script type="application/json"
id="anidiagram-motion-manifest">` block. Each entry points to stable SVG part
IDs such as `#icon-agent-outline-left` or `#icon-api-request-token`; the JavaScript
runtime does not infer semantics from arbitrary paths or classes.
The current default runtime mode is `ambient`. A direct DiagramScript that
omits motion uses the compatibility profile `expressive`; new composition-v1
output resolves `showcase-v1`. In the runtime's Expressive toolbar mode, icon
performances loop independently with small staggered delays, while the browser
runtime generates GSAP-owned edge flow particles and title sweep. Whole-diagram timeline,
event-driven, state-machine, interactive, and hybrid modes are future roadmap
items, not default behavior. See [docs/html-runtime.md](./docs/html-runtime.md)
and [docs/runtime-motion-roadmap.md](./docs/runtime-motion-roadmap.md).

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
    "profile": "expressive",
    "edge": {"preset": "signal-arrow", "particle": "soft-dot", "trail": true, "particle_count": 1},
    "node": {"preset": "icon-performance", "icon_motion": "database-write-v2"},
    "group": {"preset": "border-scan"},
    "title": {"preset": "highlight-sweep"}
  },
  "motion_policy": {
    "profile": "expressive",
    "max_active_flow_edges": 8,
    "max_particle_edges": 8,
    "particle_count_per_edge": 1,
    "flow_trail_count": 1,
    "max_active_pulse_nodes": 8,
    "max_scanning_groups": 2
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

## Illustrated 2.5.0

`illustrated` is the stable public id for the current Illustrated icon system.
It is not the composition-v1 default; select it explicitly when the illustration
language is wanted. Version 2.5.0 contains 56 approved icons with one-to-one
semantic coverage of Diagram Core v1. All 13 public templates adapt only the
approved Illustrated color tokens; geometry, part ids, and semantic roles stay
unchanged.

Public `showcase-v1` diagrams automatically use the approved 56-item
`illustrated-performance-v6` contract. The v6/v7 review contracts are archived
human-review evidence and are never emitted by new diagrams. The former
`illustrated-performance-v5` contract remains the immutable 2.4.0 archive. The input
alias `illustrated-character-v2` resolves to `illustrated`; new plans and
resolved output use the stable public id.

## Legacy: Illustrated Character v1

For DiagramScript v0.1-v0.3 and legacy styles that omit `icon_system`, the
compatibility default remains `illustrated-character-v1`: a clean-room set
covering all 13 legacy schema icons (`agent`, `operator`, `search`, `tool`, `api`,
`memory`, `output`, `file`, `folder`, `cloud`, `shield`, `token`, and
`database`). Its quiet GSAP performances are `brain-think-pulse-v1`,
`operator-type-focus-v1`, `search-scout-find-v1`, `tool-kit-action-v1`,
`api-signal-return-v1`, `memory-index-commit-v1`, `output-envelope-reveal-v1`,
`file-note-write-v1`, `folder-file-store-v1`, `cloud-uplink-ready-v1`,
`shield-guard-confirm-v1`, `token-intent-ready-v1`, and
`bucket-ingest-confirm-v1`. Use `styles/illustrated-character.json` with the
`icons` and `flow` examples to preview it. `illustrated-v1` and
`semantic-line-v1` remain explicit compatibility modes.

Character v1 uses Motion Coordination v1.2 in HTML. `Expressive` keeps the
character performances primary, gives each active edge a continuously moving
low-opacity track plus one logical packet with no quiet gap, and plays the
title highlight once on entry. Group frames stay on `soft-reveal` unless a scanning preset is
explicitly requested. `Readable` keeps the semantic character actions but
reduces stage motion to at most two key edges and removes decorative title and
group effects. `Off` and operating-system reduced motion show the canonical
static scene with no GSAP timelines.

The supported Character v1 themes are `illustrated-character`, `deep-tech`, and
`teaching-sketch-character`. Review identical content across all three in
[gallery/character-themes.html](./gallery/character-themes.html). Canonical
architecture examples include [Agent Memory](./examples/agent-memory.diagram.json),
[High Fidelity Runtime](./examples/high-fidelity-runtime.diagram.json), and
[Loop Engineering](./outputs/loop-engineering-architecture/loop-engineering-architecture.diagram.json).

Release evidence for the browser-owned SVG, HTML, PNG, WebP, GIF, APNG, MP4,
PDF, and frame-based Lottie matrix is under
[`outputs/release-evidence/character-v1/`](./outputs/release-evidence/character-v1/).
