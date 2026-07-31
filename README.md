# AniDiagram

Language: English | [简体中文](./README.zh-CN.md)

Clean-room DiagramScript renderer for animated architecture visuals. Current
package release: **0.2.0**.

This repository is not a GitHub fork and does not copy source code, documents,
images, generated assets, or repository history from the projects listed in
[REFERENCES.md](./REFERENCES.md).

## Showcase

The README uses eight approved cases from the Round 1 review surface. The full
13-style and 16-layout catalogs remain available in the gallery without making
the README itself exhaustive.

- **Hero Showcase**: three architecture stories, led by Loop Engineering.
- **Template Showcase**: one semantic diagram rendered through three styles.
- **Layout Showcase**: two topology-specific examples.

Gallery source: [gallery/index.html](./gallery/index.html) ·
[all styles](./gallery/styles/index.html) · [all layouts](./gallery/layouts/index.html) ·
[runtime motion](./gallery/runtime-motion.html)

### Hero Showcase

| Loop Engineering Operating Architecture |
| --- |
| ![Loop Engineering Operating Architecture](./gallery/readme-showcase/hero-loop-engineering.webp)<br>`illustrated` 2.5 · `minimal-light` · `layered-loop`<br>A governed engineering loop arranged as three operating layers with external state feeding the next cycle. |

| Governed RAG Production Architecture | Kubernetes Production Architecture |
| --- | --- |
| ![Governed RAG Production Architecture](./gallery/readme-showcase/hero-governed-rag.webp)<br>`illustrated` 2.5 · `minimal-light` · `layered` | ![Kubernetes Production Architecture](./gallery/readme-showcase/hero-kubernetes-three-layer.webp)<br>`diagram-core-v1` · `deep-tech` · three explicit layers |

To open the interactive runtime locally:

```bash
python3 -m http.server 8765
```

Then visit `http://127.0.0.1:8765/gallery/readme-showcase/readme-showcase-round-1.html`.
A hosted link can replace this local URL when a static host is enabled for the
repository.

### Template Showcase

The semantic content and geometry stay fixed while only the public style
changes, making the visual-system differences directly comparable.

| Minimal Light | Deep Tech | Claude Warm |
| --- | --- | --- |
| ![Production AI Agent Request Lifecycle in Minimal Light](./gallery/readme-showcase/template-agent-lifecycle-minimal-light.webp)<br>Quiet, documentation-first clarity | ![Production AI Agent Request Lifecycle in Deep Tech](./gallery/readme-showcase/template-agent-lifecycle-deep-tech.webp)<br>High-contrast technical presentation | ![Production AI Agent Request Lifecycle in Claude Warm](./gallery/readme-showcase/template-agent-lifecycle-claude-warm.webp)<br>Warm reasoning and teaching tone |

### Layout Showcase

| Enterprise RAG Ingestion Pipeline | MCP Tool Orchestration Hub |
| --- | --- |
| ![Enterprise RAG Ingestion Pipeline](./gallery/readme-showcase/layout-enterprise-rag-pipeline.webp)<br>`pipeline` · sequential transformation and retrieval | ![MCP Tool Orchestration Hub](./gallery/readme-showcase/layout-mcp-tool-hub.webp)<br>`hub-spoke` · one orchestrator coordinating multiple capabilities |

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
- Includes 16 clean-room preset compilers and 13 public visual styles.
- Produces semantically equivalent English and Chinese plans from matching
  briefs, including localized labels and descriptions.
- Keeps `ambient` as the compatibility default while offering opt-in
  `timeline` and `hybrid` Choreographer v1 playback.
- Ships checkout-independent assets inside the wheel; installed CLI renders do
  not depend on the source tree.

SVG, debug viewer HTML, Lottie, and quality reports use the Python standard
library. The primary `html` export writes a high-fidelity runtime page with a
static SVG stage, named parts, a Motion Manifest, and a browser runtime. Its
GSAP backend uses an exact `gsap@3.15.0` CDN URL by default; offline/self-hosted
pages can inline a user-provided local copy with `--runtime-dependency inline`.
GSAP is not bundled in the Python wheel. Raster,
video, PDF, and Lottie exports default to the lightweight Python renderer. For
highest-fidelity output, pass `--export-renderer browser` so PNG, GIF, PDF,
WebP, MP4, APNG, and Lottie are captured from the real HTML runtime with
Playwright/Chromium. Browser-captured Lottie is frame-based, so it is visually
faithful but larger than the default structured Lottie JSON. GIF packaging
needs Pillow. Large WebP capture streams through `img2webp` when available and
falls back to Pillow; APNG similarly prefers `ffmpeg`; MP4 needs `ffmpeg`.

## Quick Start

Build and install the standalone wheel:

```bash
python3 -m pip wheel . --no-deps --wheel-dir dist
python3 -m pip install dist/anidiagram-0.2.0-py3-none-any.whl
anidiagram --preset agent-memory --outdir outputs --formats svg,html,quality
```

The source-checkout examples below use `PYTHONPATH=src` so contributors can
test local changes without installing them first.

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

### Generate a Simplified Chinese architecture diagram

Chinese briefs resolve to `zh-CN` automatically. Use
`--diagram-locale zh-CN` to force localized titles, nodes, relations, flow
copy, and HTML controls:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --text "构建企业级智能体平台架构：请求经过 API 网关进入智能体，读取长期记忆和知识库，调用搜索工具，通过安全校验后输出结果，失败时反馈重试。" \
  --diagram-locale zh-CN \
  --viewer-locale auto \
  --outdir outputs/zh-CN \
  --basename enterprise-agent-platform \
  --formats svg,html,png,pdf,quality \
  --runtime-dependency none \
  --plan-out outputs/zh-CN/enterprise-agent-platform.plan.json \
  --spec-out outputs/zh-CN/enterprise-agent-platform.diagram.json
```

The authored Chinese example is
`examples/zh-CN/enterprise-agent-platform.plan.json`. SVG and HTML outputs
declare `lang="zh-CN"` and use a cross-platform CJK font stack. Lightweight
Python raster exports auto-discover a local Chinese font; set
`ANIDIAGRAM_CJK_FONT=/absolute/path/to/font.ttf` for a deterministic build.
Use `--export-renderer browser` for the highest-fidelity PNG/PDF output.

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

Render an offline, Chinese, causal walkthrough with a local GSAP copy:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --plan examples/contracts/production-request-path.plan.json \
  --outdir outputs/choreographer \
  --basename production-request-path \
  --formats html,quality \
  --runtime-mode timeline \
  --viewer-locale zh-CN \
  --runtime-dependency inline \
  --runtime-source node_modules/gsap/dist/gsap.min.js
```

Use `--runtime-mode hybrid` to keep the ambient overview until the user starts
the explanation. Use `--runtime-dependency none` for a static, dependency-free
HTML fallback.

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
provenance, and `showcase-v1`; composition-v1 output defaults to versioned
Illustrated. See
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
| DiagramPlan v0.2 compiled through `composition-v1` to DiagramScript v0.4 | `illustrated` (2.5.0) | `showcase-v1` |
| Direct DiagramScript v0.4 without `composition_policy` | `diagram-core-v1` | `expressive` when `motion` is omitted |
| Legacy DiagramScript v0.1-v0.3 or a style that omits `icon_system` | `illustrated-character-v1` | `expressive` when scene motion is omitted |

`illustrated` is the composition-v1 default public icon-system choice. Its current
implementation version is 2.5.0 and its 56 icons use the approved
`illustrated-performance-v6` contract automatically under `showcase-v1`. See
[the icon-system release status](./docs/icon-system-release-status.md) for the
current/default/legacy matrix. Select `diagram-core-v1` explicitly when the
technical line-icon language is preferred.

## Layout Presets

AniDiagram includes 16 clean-room layout presets. They are generated by the
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
| `agent-loop` | Trigger, cognitive loop, and three support domains | governed agent internals, memory, safety, tool execution | `sketch-board` |
| `layered-loop` | Serpentine operating layers with outer feedback | governed engineering loops, staged execution, verification and state | `minimal-light` |

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
python3 -m pip install -e ".[raster]"
PYTHONPATH=src python3 scripts/build_showcase.py --quality
```

This reuses the eight committed animated README WebP previews. To deliberately
record them again with the pinned `gsap@3.15.0` capture runtime, run:

```bash
PYTHONPATH=src python3 scripts/render_readme_showcase_round_1.py \
  --spec-root examples/readme-showcase-round-1 \
  --outdir gallery/readme-showcase
```

Re-recording requires the bundled Playwright/Chromium browser runtime and the
exact local `gsap@3.15.0` development dependency. The committed contract is 24
frames at 12 FPS, 1x scale, four loop-blend frames, and WebP quality 65.
Enforce its repository budgets with:

```bash
PYTHONPATH=src python3 scripts/check_asset_budget.py
```

The eight README WebPs must remain below 6 MiB total and 1 MiB each; the full
gallery must remain below 55 MiB. To inspect disposable generated outputs
without deleting evidence, run `PYTHONPATH=src python3 scripts/prune_outputs.py`.

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
runtime generates GSAP-owned edge flow particles and title sweep. Choreographer
v1 adds explicit `timeline` and `hybrid` modes: it sequences each source, edge,
and target as a causal step and exposes start/previous/next controls. Ambient
remains unchanged unless one of those modes is requested. Event-driven,
state-machine, and arbitrary node interaction remain roadmap items. See
[docs/html-runtime.md](./docs/html-runtime.md)
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
It is the composition-v1 default when a DiagramPlan uses `icon_system: auto` or
omits the presentation axis. Version 2.5.0 contains 56 approved icons with one-to-one
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
