# AniDiagram Composition Contract v1

## Status and scope

This is the implemented product contract for independently evolving semantic
content, icon systems, visual styles, layouts, and motion. DiagramPlan v0.2,
DiagramScript v0.4, `diagram-core-v1`, and `showcase-v1` are the current
composition-v1 path.

DiagramPlan v0.1 and DiagramScript v0.1-v0.3 remain supported through the
legacy compatibility path. Individual style, layout, icon, and motion systems
can continue to improve without changing this composition boundary.

Normative terms `MUST`, `SHOULD`, and `MAY` describe required, recommended, and
optional behavior.

## Composition model

```text
Semantic content
  -> icon system
  -> visual style
  -> layout
  -> motion
  -> renderer and exporters
```

The four presentation systems are sibling axes. An implementation MAY resolve
them in a different operational order, but one axis MUST NOT silently redefine
another axis.

## Layer 0: semantic content

The semantic content layer answers five questions:

1. What question should the diagram answer?
2. What entities exist?
3. How are the entities related?
4. Which boundaries and named flows organize the graph?
5. What is primary, supporting, or contextual?

It MUST NOT contain:

- coordinates, node sizes, route points, or canvas bounds;
- colors, font choices, strokes, shadows, or visual-style tokens;
- icon asset ids or SVG part selectors;
- animation presets, durations, easing, particles, or runtime selectors;
- renderer-specific markup.

### Semantic document shape

```json
{
  "version": "0.2",
  "semantic": {
    "title": "Production Kubernetes request path",
    "subtitle": "Ingress, control plane, workloads, and observability",
    "summary": "Show how an external request reaches a workload and how the platform observes it.",
    "intent": {
      "diagram_kind": "architecture",
      "primary_question": "How does a production request move through the cluster?",
      "audience": ["technical"],
      "scope": "Runtime request and operational feedback paths"
    },
    "entities": [
      {
        "id": "ingress",
        "label": "Ingress",
        "kind": "gateway",
        "role": "source",
        "importance": "primary"
      },
      {
        "id": "workload",
        "label": "Application workload",
        "kind": "service",
        "role": "process",
        "importance": "primary"
      }
    ],
    "relations": [
      {
        "id": "request",
        "from": "ingress",
        "to": "workload",
        "kind": "request-response",
        "label": "HTTP request",
        "direction": "forward",
        "importance": "primary"
      }
    ],
    "groups": [],
    "flows": [
      {
        "id": "request-path",
        "label": "Primary request path",
        "relation_ids": ["request"],
        "importance": "primary",
        "repeat": "event-driven"
      }
    ]
  },
  "presentation": {
    "icon_system": "auto",
    "style": "auto",
    "layout": "auto",
    "motion": "showcase-v1"
  }
}
```

### Intent

`intent` guides summarization and presentation selection without prescribing a
visual result.

- `diagram_kind`: recommended values include `architecture`, `process`,
  `data-flow`, `sequence`, `network`, `lifecycle`, `comparison`,
  `entity-relationship`, and `explainer`.
- `primary_question`: the single question a viewer should be able to answer.
- `audience`: one or more audience labels such as `technical`, `executive`,
  `mixed`, or `beginner`.
- `scope`: what the diagram includes. Exclusions MAY be recorded separately.

### Entities

An entity is a stable semantic node.

| Field | Requirement | Meaning |
| --- | --- | --- |
| `id` | MUST | Stable machine id; labels MAY change without breaking relations. |
| `label` | MUST | Human-readable name. |
| `kind` | MUST | Domain concept such as `service`, `database`, `queue`, `gateway`, `agent`, or `user`. |
| `role` | MUST | Structural role: `actor`, `source`, `process`, `agent`, `memory`, `tool`, `output`, `risk`, or `neutral`. |
| `description` | MAY | Additional semantic detail. |
| `importance` | SHOULD | `primary`, `supporting`, or `context`. |
| `tags` | MAY | Search and domain labels; not CSS classes. |
| `attributes` | MAY | Domain facts that a compiler or inspector may expose. |
| `state` | MAY | Orthogonal runtime dimensions for future state/result diagrams. |
| `source_refs` | MAY | Provenance ids for claims represented by the entity. |

`kind` and `role` are deliberately separate. `kind` says what an entity is;
`role` says how it participates in this particular diagram. An entity of kind
`database` can be a `source` in one diagram and `memory` in another.

The optional `state` object keeps runtime dimensions separate instead of
combining them into a fixed set of six visual states:

```json
{
  "phase": "running",
  "result": "pending",
  "availability": "online"
}
```

Future systems MAY standardize vocabularies for `phase`, `result`, and
`availability`. Presentation systems MUST NOT infer that these dimensions are
the same thing.

### Relations

A relation is the canonical semantic edge. It MUST reference valid entity ids.

Recommended `kind` values include `data-flow`, `control-flow`, `dependency`,
`trigger`, `feedback`, `request-response`, `event`, `ownership`,
`observability`, and `trust`.

`direction` is `forward`, `bidirectional`, or `undirected`. `condition`,
`protocol`, and `attributes` MAY carry domain detail. A relation's
`importance` guides visual emphasis but does not directly name an edge effect.

### Groups

A group defines semantic containment or a meaningful boundary. Recommended
`kind` values include `system`, `layer`, `zone`, `cluster`, `phase`,
`security-boundary`, and `ownership-boundary`.

Groups list entity or nested-group ids. They do not contain pixel bounds. The
layout system converts group membership into visual containers.

### Flows

A named flow is an ordered reference to canonical relation ids. It MUST NOT
duplicate edge definitions.

Flows identify primary request paths, feedback loops, deployment paths, data
pipelines, and other narratives. Layout uses order and loop semantics; motion
uses importance and repeat intent. Neither system changes the underlying
relations.

### Provenance

Documents MAY define `sources` and refer to them from entities and relations.
This distinguishes user-provided facts, source-backed facts, and model-inferred
structure without embedding citations into visible labels.

## Layer 1: icon system

Target input field:

```json
"icon_system": "illustrated"
```

Resolution policy:

1. Explicit user selection.
2. `illustrated` default under composition policy v1, currently implementation
   version `2.5.0`.

`auto` means use the versioned default; it does not ask a model to choose.

Icon systems map semantic `kind` and `role` values to system-specific asset ids.
The semantic document never stores SVG selectors. A missing mapping MUST
produce a declared fallback or a quality issue; it MUST NOT silently substitute
a semantically different icon.

The public illustrated system id is `illustrated`; its current implementation
version is recorded separately as `2.5.0` in the resolved icon-system axis.
`illustrated-character-v2` is a legacy input alias and MUST resolve to
`illustrated`. Fifty-six static assets are approved with exact semantic-id
parity with Diagram Core v1. The separately versioned
`illustrated-performance-v6` motion contract maps all 56 icons automatically
under public `showcase-v1`. The v6/v7 review contracts remain immutable archived
human-review evidence and are not emitted by new diagrams. The former public
v5 contract remains the immutable twenty-icon 2.4.0 archive;
`illustrated-performance-v4` and its v4-review source remain immutable 2.3.0 archives.
`illustrated-performance-v3`
remains the immutable twelve-icon 2.2.0 public-contract archive,
`illustrated-performance-v2` remains the immutable eight-icon 2.1.0 archive,
and `illustrated-performance-v3-review` remains archived approval evidence. The four-icon
`illustrated-performance-v1` contract remains the immutable 2.0.0 archive.

Illustrated 2.5.0 reads its canonical color and geometry values from
`assets/illustrated/tokens-2.5.0.json`. A style MAY override the declared color
tokens through an `illustrated_tokens` object. Unknown tokens and non-hex color
values are validation errors. View box, stroke width, line caps, line joins,
icon paths, semantic roles, and SVG part ids are version-locked and MUST NOT be
overridden by a style.

## Layer 2: visual style

Target input field:

```json
"style": "deep-tech"
```

The public catalog currently contains 13 styles. Resolution policy:

1. Explicit user selection.
2. Model selection from the public catalog using intent, audience, content
   density, and delivery context.
3. `minimal-light` deterministic fallback.

The resolved style id MUST be serialized before rendering. A renderer does not
call a model. Styles own canvas, typography-like spacing, node surfaces, edge
colors, and semantic role colors. They do not own the icon-system selection.
For the Illustrated system, styles may additionally map the approved visual
color tokens, but cannot change icon geometry or semantic structure.
All 13 public styles contain approved Illustrated 2.5.0 token mappings. Review
files must not become a second source of truth.

When a Skill or another model-facing planner resolves an `auto` style or layout
before compilation, it writes the concrete value and records `model` in the
optional top-level `presentation_sources` map. Concrete values without that
provenance are treated as explicit user choices. This preserves the precedence
chain without making the renderer infer who selected a value.

## Layer 3: layout

Target input field:

```json
"layout": "layered"
```

Resolution policy:

1. Explicit coordinates in an already-resolved DiagramScript.
2. Explicit layout selection.
3. Model selection from the supported layout catalog.
4. `layered` deterministic fallback.

The current 14 layout presets remain the initial catalog. Layout consumes
entities, relations, groups, flows, importance, and intent. It emits canvas
bounds, node positions and sizes, group bounds, and edge routes. It MUST NOT
change ids, labels, semantic kinds, roles, or relation direction.

## Layer 4: motion

Target input field:

```json
"motion": "showcase-v1"
```

`showcase-v1` is the composition-policy-v1 default. It means:

- enable every supported icon-system semantic performance;
- enable every eligible data-flow relation;
- enable group treatment and title entry effects;
- keep every eligible data-flow edge visibly moving in Expressive mode while
  varying cycle duration to avoid a rigid synchronized rhythm;
- return icons to authored rest poses between semantic performances;
- respect reduced motion and explicit Off mode;
- preserve the static rest pose when runtime animation is unavailable.

Motion consumes relation kind, named flows, importance, and optional semantic
state. It maps those semantics to icon-system-specific parts and runtime tracks.
Semantic documents never name GSAP selectors, SVG part ids, particles, easing,
or durations.

## Resolution record

Any generated DiagramScript or structured result MUST record concrete values
and why they were selected. Recommended metadata:

```json
{
  "composition_policy": "composition-v1",
  "resolved_presentation": {
    "icon_system": {"value": "illustrated", "version": "2.5.0", "source": "default"},
    "style": {"value": "deep-tech", "source": "model"},
    "layout": {"value": "layered", "source": "model"},
    "motion": {"value": "showcase-v1", "source": "default"}
  }
}
```

Allowed sources are `explicit`, `default`, `model`, `fallback`, and `legacy`.
This record is evidence, not a second source of configuration truth. The
resolved DiagramScript fields remain authoritative for rendering.

Systems whose identity no longer embeds a release number record it separately.
For example, an explicit Illustrated selection resolves as:

```json
"icon_system": {"value": "illustrated", "version": "2.5.0", "source": "explicit"}
```

## Compatibility and migration

- Current DiagramScript v0.3 behavior does not change under this contract.
- DiagramScript v0.3 omission continues to resolve through the current
  Illustrated Character v1 compatibility path.
- The independent top-level `icon_system`, Illustrated 2.5.0 default, resolved
  presentation record, and `showcase-v1` profile belong to DiagramScript v0.4
  or later.
- Existing diagrams that require pixel-stable reproduction SHOULD be pinned to
  explicit icon, style, layout, and motion values before migration.
- Style files MAY retain legacy icon-system declarations during migration, but
  those declarations MUST NOT override an explicit v0.4 scene selection.

## Validation invariants

A conforming semantic validator MUST check at least:

- unique ids across entities, relations, groups, flows, and sources;
- every relation endpoint exists;
- every group member exists and group nesting is acyclic;
- every flow relation exists and its ordered path is coherent;
- primary-question and title fields are non-empty;
- presentation requests use registered ids or `auto`;
- no renderer-specific presentation fields appear in `semantic`.

Presentation and quality validators SHOULD additionally report missing icon
mappings, unsupported style/icon combinations, layout collisions, text fit,
edge-node collisions, motion overload, and inaccessible reduced-motion behavior.
