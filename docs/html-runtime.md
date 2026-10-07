# High-Fidelity HTML Runtime

AniDiagram's `html` output is the high-fidelity runtime target. It uses a static
SVG stage, stable icon part IDs, a Motion Manifest, and a JavaScript runtime
powered by GSAP.

The `svg` output remains portable and dependency-free. It may include lightweight
SVG/SMIL animation, but it does not include GSAP, the Motion Manifest, or the
AniDiagram JavaScript runtime.

## Output Targets

| Output | Purpose | Motion owner |
| --- | --- | --- |
| `diagram.svg` | Portable fallback for README, docs, Markdown, and static embeds. | SVG/SMIL |
| `diagram.html` | Main high-fidelity runtime showcase. | JS runtime / GSAP |
| `diagram.viewer.html` | Legacy/debug viewer around the SVG fallback. | SVG/SMIL |

`html-runtime` is accepted as a legacy format alias for `html`, but the product
meaning is now simple: `html` is the best motion experience and `svg` is the
portable fallback.

## How It Works

The runtime renderer builds:

1. A runtime-stage SVG with stable IDs on semantic icon parts.
2. A Motion Manifest in `#anidiagram-motion-manifest`.
3. A GSAP-powered JavaScript runtime from `runtime/anidiagram-runtime.js`.
4. Runtime-generated stage effects for expressive edge flow and title sweep.
5. An additive Choreographer v1 layer from
   `runtime/choreographer-v1-runtime.js` when `timeline` or `hybrid` is
   explicitly selected.

The default runtime mode is `ambient`. A direct DiagramScript that omits motion
uses the compatibility profile `expressive`; DiagramPlan v0.2 composition-v1
output resolves `showcase-v1`. In the runtime's Expressive toolbar mode, each
supported semantic icon plays its own local micro-performance loop with a small
staggered delay. Expressive runtime pages also generate GSAP-owned edge flow
particles and title sweep in the browser.

The runtime does not choreograph the whole diagram as a causal timeline by
default.

## Motion Coordination v1.2 controls

The toolbar exposes three behaviorally distinct modes:

- `Expressive` runs the local character performances and policy-approved stage
  effects. Each active edge owns a continuously moving low-opacity track plus
  one logical packet (a white halo and colored core) with no quiet interval.
  The title highlight is an entry-only accent. Character-theme group frames default to
  `soft-reveal`; scanning borders require an explicit, budgeted preset.
- `Readable` preserves semantic character performances but removes the
  decorative title treatment, relation fields, and scanning group effects. It
  limits edge packets to the policy-approved key paths, with a runtime ceiling
  of two.
- `Off` removes all GSAP-owned icon and stage timelines and restores every local
  part to its canonical rest state. `prefers-reduced-motion: reduce` starts in
  the same canonical state and creates no GSAP timelines.

Switching Expressive -> Readable -> Off -> Expressive rebuilds only the owned
stage effects, without duplicating generated elements or restarting characters
from an invalid pose. Verify this contract with:

```bash
node scripts/verify_stage_motion_modes.mjs \
  outputs/illustrated-character-v1-flow/illustrated-character-v1-flow.html
```

Default Character, Deep Tech, and Teaching Sketch Character are the supported
Character v1 theme combinations. Their shared review surface is
[`gallery/character-themes.html`](../gallery/character-themes.html).

In runtime-stage mode, the SVG stage is static. It keeps geometry and stable
part IDs, but it does not emit SVG/SMIL animation tags such as `<animate>`,
`<animateMotion>`, or `<animateTransform>`. This avoids mixed ownership where
SMIL, CSS keyframes, and GSAP all try to animate the same visual surface.

All built-in semantic icons currently have runtime performances. Unsupported
future or custom icons stay static in the HTML runtime. Static is preferable to
mixing a SMIL fallback with a GSAP performance.

Choreographer v1 ships as explicit `timeline` and `hybrid` runtime modes.
Timeline starts as a causal source -> edge -> target explanation; hybrid starts
with the familiar ambient overview and enters that explanation only when the
user selects Start Explanation. Both add start, previous, and next controls and
preserve the reduced-motion static contract. Explanation steps dim
non-focused elements, move the camera within the canvas bounds, and show a
narration card with the step, label, `source → target`, condition, and source
links; `←`/`→` and the progress dots navigate. `--runtime-mode event-driven`
is a separate opt-in scheduler where arrivals trigger target performances and
propagate downstream. Explicit node state machines and arbitrary hover/click
replay remain roadmap items. See
[runtime-motion-roadmap.md](./runtime-motion-roadmap.md).

## Runtime dependency ownership

The default `cdn` mode writes the exact
`https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js` URL. This keeps the
page small, but viewing animation requires network access.

For offline or self-hosted output, `inline` reads a user-provided local GSAP
file and embeds it in the generated HTML:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/high-fidelity-runtime.diagram.json \
  --outdir outputs/offline \
  --formats html,quality \
  --runtime-dependency inline \
  --runtime-source node_modules/gsap/dist/gsap.min.js
```

`none` omits GSAP and leaves the canonical static stage. AniDiagram does not
bundle GSAP in its Python wheel; the inline source remains the user's chosen
local dependency and license responsibility.

## Choreographer v1

Use `--runtime-mode timeline` for immediate causal playback, or
`--runtime-mode hybrid` for ambient-first playback:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --plan examples/contracts/production-request-path.plan.json \
  --outdir outputs/choreographer \
  --basename timeline \
  --formats html,quality \
  --runtime-mode timeline \
  --viewer-locale auto
```

The manifest stores `mode`, `sequence=causal-edge-steps`, and ordered steps
derived from authored scene edges. Each step activates its source, draws the
edge, and responds at the target. Auto locale chooses Chinese controls when the
scene title or subtitle contains CJK text; `--viewer-locale en|zh-CN` overrides
it. Toolbar and stage controls expose keyboard focus, accessible names, live
status, and a visible dependency warning when animation cannot start.

Verify the browser contract with:

```bash
node scripts/verify_choreographer.mjs outputs/choreographer/timeline.html timeline
```

Gallery cards can use SVG fallback previews, but a README hero should use
browser-captured runtime media. GitHub repository file views show `.html` files
as source code; they do not execute the GSAP runtime. For GitHub README
presentation, use an animated WebP or GIF captured from `diagram.html`. Link
the preview to an MP4 or hosted runtime page when one is published. If neither
exists yet, leave the inline animation unlinked and provide explicit local
runtime instructions; do not link it to a repository `.html` source view or a
static SVG that implies an interactive destination.

For interactive HTML links, serve the generated gallery through a static host
such as GitHub Pages. A repository link like
`https://github.com/.../blob/main/gallery/hero/agent-runtime-flow.html` is a code
view, not the runtime experience.

## Legacy semantic runtime performances

The original semantic-line and legacy illustrated runtime path maps these
twelve high-fidelity v2 performances. Diagram Core and current Illustrated use
their own versioned manifests instead of this table.

| Icon | Performance |
| --- | --- |
| `agent` | `agent-think-act-v2` |
| `api` | `api-request-response-v2` |
| `search` | `search-discover-v2` |
| `database` | `database-write-v2` |
| `memory` | `memory-commit-v2` |
| `tool` | `tool-run-v2` |
| `token` | `token-intent-v2` |
| `output` | `output-reveal-v2` |
| `file` | `file-lines-v2` |
| `folder` | `folder-open-v2` |
| `cloud` | `cloud-upload-v2` |
| `shield` | `shield-check-v2` |

## Runtime Motion Catalog

Current high-fidelity runtime effects are managed in:

- `runtime/motion-catalog.json`
- `examples/runtime-motion-catalog.diagram.json`
- `gallery/runtime-motion.html`
- `gallery/runtime-motion/overview.html`

`runtime/motion-catalog.json` is the source of truth for the frozen expressive
ambient runtime baseline. It lists the supported icon performances, stage
effects, stable parts/selectors, semantic phases, and change-control rule.

Use `gallery/runtime-motion.html` when reviewing or comparing the current
effects. It embeds a live overview runtime page and links back to the catalog
JSON.

Any future change that alters visual timing, intensity, icon semantics, stable
part IDs, stage effects, default profile/mode, or runtime scheduling must be
confirmed before implementation. Documentation-only typo fixes, tests that do
not change runtime behavior, and gallery regeneration from the same specs/code
can proceed without changing the baseline.

The agent performance uses these stable parts:

```text
#icon-agent-root
#icon-agent-outline-left
#icon-agent-outline-right
#icon-agent-center-line
#icon-agent-branch-left
#icon-agent-branch-right
#icon-agent-branch-lower
#icon-agent-node-top-left
#icon-agent-node-top-right
#icon-agent-node-left
#icon-agent-node-right
#icon-agent-node-center
#icon-agent-decision-token
#icon-agent-pulse
```

The performance rhythm is:

```text
brain/head outline draws outward
-> branch circuits draw in
-> circuit nodes light up
-> center node pulses as a decision
-> decision token exits the agent
-> quiet idle pause
```

## Run The Demo

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/high-fidelity-runtime.diagram.json \
  --style styles/deep-tech.json \
  --outdir outputs \
  --basename high-fidelity-runtime \
  --formats svg,html,quality \
  --html-runtime gsap
```

Open:

```text
outputs/high-fidelity-runtime.html
```

For browser-captured raster or video outputs:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/high-fidelity-runtime.diagram.json \
  --style styles/deep-tech.json \
  --outdir outputs \
  --basename high-fidelity-runtime-hq \
  --formats mp4,gif,apng,webp,quality \
  --html-runtime gsap \
  --export-renderer browser \
  --export-scale 2 \
  --export-fps 24 \
  --export-frames 48
```

For a README hero preview, keep the asset lighter:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/showcase/hero/agent-runtime-flow.diagram.json \
  --style styles/deep-tech.json \
  --outdir gallery/previews \
  --basename agent-runtime-flow \
  --formats gif,webp,mp4,apng \
  --html-runtime gsap \
  --export-renderer browser \
  --export-scale 1 \
  --export-fps 12 \
  --export-frames 24 \
  --export-loop-blend-frames 4 \
  --export-quality 65
```

Use the animated WebP or GIF as the inline README image. Use MP4 as the click
target when GitHub Pages is not enabled.

To preview the runtime HTML locally:

```bash
python3 -m http.server 8765
```

Then open:

```text
http://127.0.0.1:8765/gallery/hero/agent-runtime-flow.html
```

## Illustrated character performances

When `icon_system` resolves to `illustrated-character-v1`, the runtime covers
all 13 schema icons: `agent`, `operator`, `search`, `tool`, `api`, `memory`,
`output`, `file`, `folder`, `cloud`, `shield`, `token`, and `database`. Their
performances are `brain-think-pulse-v1`, `operator-type-focus-v1`,
`search-scout-find-v1`, `tool-kit-action-v1`, `api-signal-return-v1`,
`memory-index-commit-v1`, `output-envelope-reveal-v1`, `file-note-write-v1`,
`folder-file-store-v1`, `cloud-uplink-ready-v1`, `shield-guard-confirm-v1`,
`token-intent-ready-v1`, and `bucket-ingest-confirm-v1`. Each loop prepares,
performs one semantic action, confirms it, and settles back to rest. Browsers
that request reduced motion register no GSAP timelines. `illustrated-v1` and
`semantic-line-v1` remain explicit legacy icon-system modes.

`illustrated` version `2.5.0` contains 56 approved static icons. The separately
versioned `illustrated-performance-v6` contract supplies approved performances
for all 56 and public `showcase-v1` maps them automatically. The v6/v7 review
contracts remain immutable archived human-review sources and are not emitted by
new diagrams. `illustrated-performance-v5` remains the immutable twenty-icon
2.4.0 archive. `illustrated-performance-v4` and
its v4-review source remain immutable 2.3.0 archives. `illustrated-performance-v3`
remains the immutable twelve-icon 2.2.0 public-contract archive;
`illustrated-performance-v2` remains the immutable eight-icon 2.1.0 archive;
`illustrated-performance-v3-review` remains archived approval evidence. The
four-icon `illustrated-performance-v1` contract remains the immutable 2.0.0
archive. Static SVG, Off, cancel, and reduced-motion paths restore the authored
rest pose.

Character loops use a compact `0.8 s` repeat gap. During the handoff from the
semantic action to that gap, a dedicated inner shell performs a restrained
`1.2%` idle breath, so the icon stays alive without moving its authored anchor.

## Verify illustrated character runtime

After generating the illustrated-character examples, verify that the full
legacy gallery returns every character timeline to its declared rest state,
then verify the reduced-motion contract for the 13-icon gallery and 8-icon flow:

```bash
node scripts/verify_character_motion_rest.mjs outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html
node scripts/verify_character_reduced_motion.mjs outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html 13
node scripts/verify_character_reduced_motion.mjs outputs/illustrated-character-v1-flow/illustrated-character-v1-flow.html 8
```

For current Illustrated 2.5.0, verify all 56 public v6 performances and the
stage-mode rebuild contract:

```bash
node scripts/verify_character_motion_rest.mjs \
  outputs/illustrated-2.5-showcase/illustrated-2.5-showcase.html 56 illustrated
node scripts/verify_character_reduced_motion.mjs \
  outputs/illustrated-2.5-showcase/illustrated-2.5-showcase.html 56 illustrated
node scripts/verify_stage_motion_modes.mjs \
  outputs/illustrated-2.5-showcase/illustrated-2.5-showcase.html
```

Both character scripts validate the embedded Motion Manifest and fail if the
declared count or rendered roots are wrong. The optional fourth argument sets
the expected icon-system id; it defaults to `illustrated-character-v1`, while
current Illustrated verification passes `illustrated`. The rest-state verifier
defaults to 13 entries but accepts an explicit positive count. The scripts
resolve Playwright from a local project dependency first, then `npm root -g`;
`NODE_PATH` is not required.

See [icon-system-release-status.md](./icon-system-release-status.md) for the
current public contracts and immutable archive boundary.

## Limits

- Standalone SVG cannot display GSAP high-fidelity runtime motion.
- CDN mode requires network access. Inline mode requires a user-provided local
  GSAP source; AniDiagram intentionally does not redistribute it in the wheel.
- Choreographer v1 models authored edge order as source/edge/target steps. It
  does not yet model camera choreography, data-driven arrival events, node
  state machines, or arbitrary interactive replay.
- `illustrated` 2.5.0 freezes 56 approved static icons and 56 approved
  automatic `showcase-v1` performances.
- Video and animated image export require browser capture. MP4 requires
  ffmpeg; large APNG capture prefers ffmpeg's streaming encoder and large WebP
  capture prefers `img2webp`, with Pillow fallbacks when those tools are absent.
- Browser-captured PNG/PDF use a settled runtime frame; GIF, WebP, APNG, MP4,
  and frame-based Lottie seek the GSAP-owned timelines at the requested FPS.
  Each written browser export reports `renderer`, `status`, `frames`, `fps`,
  `scale`, and `path` in the CLI result JSON. Optional tooling failures are
  returned as `status: skipped` with a reason.
- The legacy viewer remains useful for SVG fallback debugging, but it is not the
  main product experience.
