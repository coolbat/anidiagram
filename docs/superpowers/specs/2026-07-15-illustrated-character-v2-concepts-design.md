# Illustrated Semantic v2 Concept Slice — Draft B

## Goal

Test a clearer clean-room icon direction before changing AniDiagram's default
icon system or investing in another motion pass. Draft A's anthropomorphic
objects were rejected because faces, limbs, and props competed for limited icon
space.

The concept slice covers `agent`, `operator`, `tool`, and `output`. The stable
`illustrated-character-v1` system remains the default.

## Visual contract

- Do not add faces, arms, or legs to tools, containers, or documents.
- Each icon uses one dominant semantic object, one action cue, and one outcome
  cue with visible negative space between them.
- A human silhouette is allowed only when the role itself is a person, such as
  `operator`; it should remain a neutral pictogram rather than a mascot.
- Rounded dark outlines, warm surfaces, and restrained two-tone fills keep the
  four compositions recognizably related.
- The 120 by 120 authoring grid targets clear recognition at 80 to 118 pixels.
- Text inside the icon is avoided so small exports remain legible.
- Decorative particles, secondary props, and duplicate confirmation marks are
  removed unless they materially explain the semantic sequence.

## Concept roles

| Icon | Stable layer | Action layer | Outcome layer |
| --- | --- | --- | --- |
| `agent` | brain and processor | input nodes and path | one result spark |
| `operator` | neutral person and laptop | cursor and screen | one status check |
| `tool` | toolbox and wrench | target bolt and action path | one completion mark |
| `output` | document and envelope | send path | one check badge |

## Review boundary

This Draft B slice is intentionally static. `illustrated-character-v2` produces no
runtime icon-performance entry yet. Motion design starts only after the static
silhouettes, visual hierarchy, and family consistency are approved.

IconScout and other libraries remain motion-language references only. No
external source asset, animation JSON, or implementation code is included.

## Acceptance

- The v2 style is explicit and does not alter the default v1 resolution.
- The four concept icons render with unique, stable part IDs.
- Unsupported v2 icons fall back with a quality warning.
- SVG, HTML, WebP, and quality outputs are generated from
  `illustrated-semantic-v2-structured.diagram.json`.
- The quality summary is `0 errors`, `0 warnings`, `0 issues` for the concept
  scene, and the full unit-test suite passes.
