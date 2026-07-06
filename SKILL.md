---
name: anidiagram
description: Create, validate, render, and quality-check AniDiagram DiagramScript scenes. Use when the user asks to produce animated architecture diagrams, generate clean-room diagram presets, export SVG/HTML/PNG/GIF/PDF/WebP/MP4/APNG/Lottie assets, or maintain the AniDiagram project.
---

# AniDiagram

Use AniDiagram for clean-room animated architecture visuals.

## Workflow

1. Write or update a DiagramScript JSON spec.
2. For complex diagrams, set a `motion_policy` such as `focused` or `readable`
   so only key paths, nodes, and borders animate continuously.
3. Validate with `PYTHONPATH=src python3 -m anidiagram.cli --spec <file> --outdir outputs --basename <name> --quality`.
4. Render the requested formats with `--formats svg,html,png,gif,pdf,webp,mp4,apng,lottie,quality` or `--all`.
5. Inspect the CLI result JSON for skipped optional exports. Optional raster/video exports depend on Pillow and, for MP4, ffmpeg.
6. Run `PYTHONPATH=src python3 -m unittest discover -s tests` before considering code changes complete.

## Presets

Use `--preset <name>` for built-in clean-room templates:

`pipeline`, `loop`, `hub-spoke`, `layered`, `swimlane`, `compare`, `matrix`,
`timeline`, `stack`, `funnel`, `sequence`, `er`, `network`, `agent-memory`.

Example:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --preset agent-memory \
  --style styles/blueprint.json \
  --outdir outputs \
  --basename agent-memory \
  --formats svg,html,quality
```

## Gallery

Generate the gallery with:

```bash
PYTHONPATH=src python3 scripts/batch_render.py --outdir gallery --quality
```

Do not reuse files from `/Users/coolbat/animated-diagram`. Treat that project
only as product validation context, never as implementation or asset source.
