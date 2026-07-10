# Illustrated Character v1 Design

## Goal

Make `illustrated-character-v1` the default semantic icon system for AniDiagram.
It provides clean-room, layered vector character icons with local semantic motion
in the existing SVG + Motion Manifest + GSAP pipeline. The first release ships
an AI brain (`agent`), a laptop operator (`operator`), and a data bucket
(`database`).

The visual contract is the approved C direction: dark indigo hand-drawn outline,
flat pastel color blocks, restrained paper/sticker accents, and no imported
third-party art or runtime code. The motion contract is the approved B direction:
`prepare -> semantic action -> confirm -> quiet`.

## Non-goals

- Do not import Lottie, Pixel2Motion, or any other third-party runtime/source.
- Do not add image tracing or prompt-to-illustration generation.
- Do not implement freeform path morphing in v1.
- Do not change the existing ambient runtime scheduler into a diagram-wide
  timeline.

## Icon System Resolution

`style.icon_system` resolves as follows:

| Requested value | Result |
| --- | --- |
| omitted | `illustrated-character-v1` |
| `illustrated-character-v1` | new layered character icon registry |
| `illustrated-v1` | existing bubble/backplate icon system |
| `semantic-line-v1` | existing line-icon rendering without illustrated treatment |

`styles/illustrated-bubble.json` keeps its explicit `illustrated-v1` value.

The v1 character registry covers `agent`, `operator`, and `database`. Any other
semantic icon resolves to `semantic-line-v1` for that icon only. The quality
report records a `character_icon_fallback` warning with the node id and icon,
so mixed output is visible rather than silent. A missing character definition
must never make a scene fail to render.

## Data Model

Add `src/anidiagram/illustrated_character_icons.py`.

`CharacterIconDefinition` uses a normalized `0..100` coordinate system and
contains:

- icon id and semantic role;
- a tuple of drawing primitives (`path`, `rect`, `circle`, `ellipse`, `line`,
  and text) with a stable part name;
- palette-token references for fill, stroke, and opacity;
- optional parent/anchor information for transform origins;
- a named runtime performance.

The renderer maps normalized geometry into the icon box and creates existing
stable DOM ids through `icon_part_id(node_id, part_name)`. This keeps illustration
geometry independent of node size and allows the same parts to feed SVG, HTML,
and future Lottie output.

## Three v1 Characters

| Diagram icon | Character form | Stable action parts | Runtime performance |
| --- | --- | --- | --- |
| `agent` | split-color AI brain with centre chip | left/right lobe, chip, signal, spark | `brain-think-pulse-v1` |
| `operator` | person with glasses and laptop | head, glasses, hand left/right, laptop, cursor | `operator-type-focus-v1` |
| `database` | data bucket with lid and liquid | lid, bucket, handle, data bead, liquid, confirm | `bucket-ingest-confirm-v1` |

All retain a stable outer silhouette. Interior action occurs over roughly one
cycle, then returns to the quiet resting state. The HTML runtime owns the full
performance; standalone SVG receives a small compatible fallback only.

## Renderer and Runtime Integration

1. Add a `resolve_icon_system(style)` helper with the default above.
2. In `render_semantic_icon`, choose character geometry for a covered icon when
   the resolved system is `illustrated-character-v1`; otherwise preserve current
   `illustrated-v1` or line-icon behavior.
3. Extend Motion Manifest generation with the new performance id and all stable
   part selectors.
4. Add three GSAP performance functions to `runtime/anidiagram-runtime.js`.
   Each must be self-contained, loop safely, honor runtime pause/restart and
   reduced motion, and return to its canonical resting state.
5. Keep the runtime stage static. Existing ambient edge flow and title effects
   continue to work unchanged.

## Style and Demonstrations

Add `styles/illustrated-character.json` to encode the approved C direction.
It should be explicit, although omission still resolves to this icon system.

Add two clean-room examples:

- `examples/illustrated-character-v1-icons.diagram.json`: a close-up three-icon
  gallery for visual review.
- `examples/illustrated-character-v1-flow.diagram.json`: an `agent -> operator
  -> database` architecture flow that proves the icons remain legible in context.

Generate SVG/HTML/quality output for each. Browser-captured WebP or GIF is a
review artifact, not a committed dependency on a new runtime.

## Quality, Errors, and Tests

Tests are written first and must prove:

- omitted `icon_system` resolves to `illustrated-character-v1`;
- explicit `illustrated-v1` keeps the current bubble treatment;
- the three character definitions expose their expected stable part ids and
  named performances;
- an unsupported icon renders as a line icon and emits exactly one
  `character_icon_fallback` quality warning;
- the HTML manifest contains the matching performance and selectors;
- reduced-motion HTML does not start character timelines.

Verification also renders both examples, runs the entire Python test suite,
checks JavaScript syntax, runs `git diff --check`, and captures browser previews
of both examples. The visual review checks outline consistency, silhouette
readability at node scale, no clipped motion, and a quiet end state.

## Acceptance Criteria

- `illustrated-character-v1` is the default while `illustrated-v1` remains
  explicit-only.
- The three v1 icons read as intentionally drawn characters rather than generic
  line icons on a bubble background.
- Each icon performs one semantic micro-performance and returns to rest.
- Existing scenes with unsupported icon ids still render deterministically and
  report their fallback.
- No third-party runtime, source code, or visual asset is added.
