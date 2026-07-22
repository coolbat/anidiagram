---
name: anidiagram
description: Create, validate, render, and quality-check semantic-first AniDiagram architecture diagrams. Use for animated architecture summaries, DiagramPlan/DiagramScript generation, SVG/HTML/PNG/GIF/PDF/WebP/MP4/APNG/Lottie export, or AniDiagram project maintenance.
---

# AniDiagram

Use AniDiagram for clean-room animated architecture visuals. New work follows
`composition-v1`: semantic content is independent from the icon system, visual
style, layout, and motion system.

## Default workflow

1. Read the source completely and extract a DiagramPlan v0.2. Keep only meaning
   in `semantic`: intent, entities, relations, groups, flows, importance,
   optional state, and source provenance. Do not place colors, SVG selectors,
   coordinates, easing, duration, or animation-part names in `semantic`.
2. Resolve the four presentation axes before rendering:
   - Honor every explicit user choice.
   - Use `icon_system: auto` when none was requested; it resolves to the
     versioned default `diagram-core-v1`.
   - Choose one concrete public style from the catalog when the user did not
     choose. Record `presentation_sources.style: model`. Use `minimal-light`
     only as the deterministic fallback.
   - Choose one concrete layout from the 14-layout catalog when the user did
     not choose. Record `presentation_sources.layout: model`. Use `layered`
     only as the deterministic fallback.
   - Use `motion: showcase-v1` unless the user explicitly requests another
     profile. Showcase enables every eligible icon performance and keeps every
     eligible data-flow edge visibly moving in Expressive mode, with authored
     rest poses and reduced-motion support.
   - New connection-line output follows `edge-motion-v1`: discrete transfers
     use one borderless `packet-flow` dot, loop/continuous relations use only
     `stream-flow` dashes, explicit burst/emphasis transfers use a borderless
     `comet-flow` head with three fading echoes, and contextual relations use
     one-shot `draw`.
     Legacy edge preset names are input aliases, not additional visual recipes.
3. Save the source plan as `<name>.plan.json`. Compile and validate it with:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --plan <name>.plan.json \
  --spec-out <name>.diagram.json \
  --outdir outputs \
  --basename <name> \
  --formats svg,html,quality
```

4. Inspect the structured CLI result and the rendered SVG/HTML. Quality must
   report zero errors. Resolve collisions, text fit, missing mappings, and
   runtime problems before presenting the work for acceptance.
5. Add requested export formats with
   `--formats svg,html,png,gif,pdf,webp,mp4,apng,lottie,quality` or `--all`.
   Browser-recorded animated exports use `--export-renderer browser` and may
   require Playwright and ffmpeg.
6. For code or contract changes, run:

```bash
PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --strict --json
PYTHONPATH=src python3 -m unittest discover -s tests
```

For Diagram Core changes, the strict validator must report all 56 approved
assets with zero errors and zero warnings. For Illustrated renderer, contract,
or runtime changes, first regenerate the public 2.4.0 showcase, then run the
twenty-item browser gates:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --spec examples/illustrated-2.4-showcase.diagram.json \
  --outdir outputs/illustrated-2.4-showcase \
  --basename illustrated-2.4-showcase \
  --formats svg,html,quality
node --check runtime/anidiagram-runtime.js
node scripts/verify_character_motion_rest.mjs \
  outputs/illustrated-2.4-showcase/illustrated-2.4-showcase.html 20 illustrated
node scripts/verify_character_reduced_motion.mjs \
  outputs/illustrated-2.4-showcase/illustrated-2.4-showcase.html 20 illustrated
node scripts/verify_stage_motion_modes.mjs \
  outputs/illustrated-2.4-showcase/illustrated-2.4-showcase.html
```

The regenerated quality report must contain zero errors. Do not replace an
archived release, review contract, acceptance record, or snapshot while running
these gates.

## Semantic layer

Treat the semantic layer as the stable explanation of what the diagram means:

- `intent`: diagram kind, primary question, audience, scope, exclusions;
- `entities`: stable id, label, semantic kind, role, importance, state, sources;
- `relations`: endpoints, relation kind, direction, label, condition, protocol;
- `groups`: semantic containment only, not visual rectangles;
- `flows`: ordered relation ids with once, loop, or event-driven behavior;
- `sources` and `source_refs`: provenance for claims and model-inferred structure.

The compiler serializes concrete coordinates and a
`resolved_presentation` record into DiagramScript v0.4. Renderers consume that
record; they do not choose a style, layout, icon system, or motion profile.

## Presentation catalogs

Public styles:

`minimal-light`, `deep-tech`, `blueprint`, `flat-icon`, `dark-terminal`,
`notion-clean`, `glassmorphism`, `claude-warm`, `openai-minimal`, `dark-luxury`,
`aurora-orb`, `illustrated-semantic`, `sketch-board`.

Choose by communication need: minimal styles for dense technical content;
`deep-tech`/`blueprint`/`dark-terminal` for infrastructure; warm or sketch
styles for teaching and narrative; glass, luxury, or aurora styles for
presentation-led work.

Layouts:

`pipeline`, `loop`, `hub-spoke`, `layered`, `swimlane`, `compare`, `matrix`,
`timeline`, `stack`, `funnel`, `sequence`, `er`, `network`, `agent-memory`.

Choose from semantic topology: ordered transformations use pipeline; feedback
uses loop; central orchestration uses hub-spoke; tiers use layered; ownership
uses swimlane; alternatives use compare; two dimensions use matrix; chronology
uses timeline or sequence; hierarchy uses stack; convergence uses funnel;
relationships use er or network; explicit memory interaction uses agent-memory.

Supported icon systems include `diagram-core-v1` (the composition-v1 default),
`illustrated-character-v1`, and `illustrated` (currently version `2.4.0`).
`illustrated-character-v2` remains accepted only as a legacy alias for
`illustrated`; new plans and resolved output use the stable `illustrated` id.
Illustrated templates may override only the approved colors through the
`illustrated_tokens` style field. They must not alter icon geometry, SVG part
ids, or semantic roles.
The public `deep-tech` style includes an approved multicolor mapping for
Illustrated 2.4.0; use that public style rather than a review-only duplicate.
Illustrated 2.4.0 contains twenty approved static icons. The approved
`illustrated-performance-v5` contract supplies public automatic `showcase-v1`
performances for all twenty icons. `illustrated-performance-v5-review` is
retained only as the archived human-review source and must not be emitted by new
diagrams. `illustrated-performance-v4` remains the immutable sixteen-icon 2.3.0
public-contract archive, while `illustrated-performance-v4-review` remains its
archived approval source. `illustrated-performance-v3` remains the immutable twelve-icon 2.2.0
public-contract archive, while `illustrated-performance-v3-review` remains its
archived approval source.
`illustrated-performance-v2` remains the immutable eight-icon 2.1.0 archive.
`illustrated-performance-v1` remains the immutable four-icon 2.0.0 archive.
Never let a style file override an explicit DiagramScript v0.4 icon system.

## Legacy compatibility

Use `--spec` for existing DiagramScript v0.1-v0.3 files and `--preset` for the
14 built-in clean-room preset compilers. Their legacy Illustrated Character v1
resolution remains unchanged. Do not silently migrate pixel-stable legacy
diagrams; create a separate v0.4 version unless the user asks to replace it.

## Gallery

Generate the legacy gallery with:

```bash
PYTHONPATH=src python3 scripts/batch_render.py --outdir gallery --quality
```

Do not reuse files from `/Users/coolbat/animated-diagram`. Treat that project
only as product validation context, never as implementation or asset source.
