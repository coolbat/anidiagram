# ADR-001: Separate semantic content from presentation systems

## Status

Accepted and implemented

## Date

2026-07-19

Amended 2026-07-26 to promote Illustrated 2.5 as the composition-v1 default.

## Context

AniDiagram needs a stable contract that can survive independent changes to icon
art, color templates, layout algorithms, and motion runtimes. The current
DiagramPlan v0.1 is useful as an LLM planning surface, but it mixes semantic
content with presentation decisions such as `style`, `layout_strategy`,
`motion_profile`, node `icon`, node `shape`, and per-element `effect`.

That coupling creates four problems:

- Changing an icon system can require rewriting content plans.
- A model-selected color template can accidentally select an icon renderer.
- Layout and motion optimization can change the meaning-bearing graph.
- Re-rendering an `auto` choice can produce a different result unless the
  resolved choice is recorded.

Diagram Core v1 has also been visually accepted as the next default direction,
while existing DiagramScript v0.3 documents still resolve omitted icon-system
configuration to Illustrated Character v1. Changing that legacy default in
place would silently alter existing diagrams.

## Decision

AniDiagram adopts a five-layer composition model:

1. Semantic content
2. Icon system
3. Visual style
4. Layout
5. Motion

Semantic content is authoritative. The other four systems are independent
presentation axes that consume the semantic graph and must not redefine it.

The accepted pipeline is:

```text
User brief or source material
  -> DiagramPlan v0.2 semantic contract
  -> presentation resolver
  -> resolved DiagramScript v0.4
  -> Scene IR
  -> SVG / HTML runtime / media exporters
```

DiagramPlan v0.2 contains sibling `semantic` and `presentation` objects. The
`semantic` object is free of coordinates, sizes, colors, icon asset ids, motion
presets, and renderer-specific values. The `presentation` object contains only
selection requests for the four presentation axes.

The normative contract is documented in
[`docs/diagram-composition-contract.md`](../diagram-composition-contract.md),
with a machine-readable planning schema in
[`schemas/diagram-plan-v0.2.schema.json`](../../schemas/diagram-plan-v0.2.schema.json).

### Resolution policy v1

- `icon_system`: explicit user value, otherwise `illustrated` (implementation
  version 2.5.0).
- `style`: explicit user value, otherwise model selection from the 13 public
  catalog styles, otherwise `minimal-light`.
- `layout`: explicit coordinates, otherwise explicit layout, otherwise model
  selection from the current layout catalog, otherwise `layered`.
- `motion`: explicit user value, otherwise `showcase-v1`.

Every non-explicit choice must be resolved once and serialized into the
generated DiagramScript or result metadata. Renderers do not repeat model
selection.

### Compatibility policy

- DiagramPlan v0.1 and DiagramScript v0.1-v0.3 remain valid.
- DiagramScript v0.3 keeps its current icon-system resolution behavior,
  including legacy style-bound icon-system settings.
- The new top-level independent `icon_system` field belongs to DiagramScript
  v0.4 or a later explicit schema version. DiagramPlan v0.2 compiled through
  `composition-v1` defaults to Illustrated 2.5. Direct manually authored
  DiagramScript v0.4 documents without `composition_policy` retain the
  `diagram-core-v1` omission default for compatibility.
- For the v0.4 resolution path, a scene-level explicit icon system wins.
  Style-level icon-system settings are compatibility metadata only and cannot
  override an explicit scene selection.
- Existing examples must be pinned to an explicit icon system before any
  default migration if exact visual reproduction is required.

### Showcase motion contract

`showcase-v1` enables all available semantic icon performances, data-flow edge
effects, group treatments, and title entry effects. In Expressive mode, every
eligible edge remains visibly in motion; different cycle durations prevent a
rigid synchronized rhythm. Readable may still narrow the stage to key paths.

Reduced-motion preference, Off mode, missing runtime dependencies, cancellation,
and restart must settle on the authored static rest pose.

## Alternatives Considered

### Keep DiagramPlan v0.1 unchanged

- Pros: no new schema surface.
- Cons: semantic meaning remains coupled to the first renderer and template
  choice; future icon and motion systems continue to leak into content plans.
- Rejected: it prevents the independent optimization requested for the four
  presentation systems.

### Put all choices directly into DiagramScript v0.3

- Pros: fewer named artifacts.
- Cons: changes the meaning and defaults of an existing schema version and
  makes old diagrams visually unstable.
- Rejected: schema-versioned defaults are safer than a silent global migration.

### Create a second unrelated semantic format

- Pros: a clean start.
- Cons: duplicates the existing purpose of DiagramPlan and introduces another
  conversion boundary.
- Rejected: evolve DiagramPlan instead of creating competing semantic models.

## Consequences

- Icon systems can expand without changing the semantic graph schema.
- The 13 public visual styles remain an independent catalog.
- The existing 14 layout presets remain usable while layout strategies evolve.
- Motion systems can map semantic intent onto system-specific SVG parts without
  putting part ids into content documents.
- Model-selected style and layout choices become reproducible because their
  resolved ids are recorded.
- DiagramScript v0.4, both 56-icon public systems, the Illustrated 2.5
  composition-v1 default, `showcase-v1`, and DiagramPlan v0.2 CLI compilation
  are implemented. Further work can optimize each system behind these stable
  boundaries.
