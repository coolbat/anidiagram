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

In runtime-stage mode, the SVG stage is static. It keeps geometry and stable
part IDs, but it does not emit SVG/SMIL animation tags such as `<animate>`,
`<animateMotion>`, or `<animateTransform>`. This avoids mixed ownership where
SMIL, CSS keyframes, and GSAP all try to animate the same visual surface.

Unsupported runtime icons stay static in the HTML runtime. Static is preferable
to mixing a SMIL fallback with a GSAP performance.

Gallery cards can use SVG fallback previews, but a README hero should use
browser-captured runtime media. GitHub repository file views show `.html` files
as source code; they do not execute the GSAP runtime. For GitHub README
presentation, use an animated WebP or GIF captured from `diagram.html`, and link
the preview to an MP4 or to a hosted runtime page.

For interactive HTML links, serve the generated gallery through a static host
such as GitHub Pages. A repository link like
`https://github.com/.../blob/main/gallery/hero/agent-runtime-flow.html` is a code
view, not the runtime experience.

## Current Performances

P0 runtime performances:

| Icon | Performance |
| --- | --- |
| `agent` | `agent-think-act-v2` |
| `api` | `api-request-response-v2` |
| `search` | `search-discover-v2` |
| `database` | `database-write-v2` |

Additional experimental runtime performances:

| Icon | Performance |
| --- | --- |
| `memory` | `memory-commit-v2` |
| `tool` | `tool-run-v2` |
| `token` | `token-intent-v2` |
| `output` | `output-reveal-v2` |

The agent performance uses these stable parts:

```text
#icon-agent-root
#icon-agent-shell
#icon-agent-core
#icon-agent-thought-1
#icon-agent-thought-2
#icon-agent-thought-3
#icon-agent-decision-token
```

The performance rhythm is:

```text
thought dots idle
-> thought dots gather into the core
-> core pulses as a decision
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
  --export-frames 36
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

## Limits

- Standalone SVG cannot display GSAP high-fidelity runtime motion.
- The runtime currently loads GSAP from the CDN.
- The Motion Manifest is icon-performance focused; it does not yet model camera
  choreography, edge-triggered node performances, or step mode.
- Video and animated image export require browser capture. MP4 also requires
  ffmpeg.
- The legacy viewer remains useful for SVG fallback debugging, but it is not the
  main product experience.
