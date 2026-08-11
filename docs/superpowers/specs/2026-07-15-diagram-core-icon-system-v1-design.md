# AniDiagram Diagram Core Icon System v1.0 — Engineering Design

## Status

- Design decision: approved
- Written-spec review: approved
- Written-spec approved on: 2026-07-16
- Approved on: 2026-07-15
- Public system name: `AniDiagram Diagram Core Icon System v1.0`
- Canonical system id: `diagram-core-v1`
- Planned node-icon catalog: 56 icons
- Default-promotion gate: all existing 13 DiagramScript icon semantics plus
  `server` render in the new visual language without fallback
- Product and visual source: approved maintainer PRD
  `AniDiagram-Diagram-Core-Icon-System-v1.0.md` (not bundled)

This document defines the repository integration contract. The source PRD owns
the visual language, icon taxonomy, icon-specific concepts, and reference art.
This repository document owns asset boundaries, compatibility, runtime data
flow, failure behavior, rollout gates, and automated acceptance.

## Goal

Replace AniDiagram's visually inconsistent semantic-icon implementations with
one coherent, illustrated, theme-aware, motion-ready system while preserving the
existing DiagramScript, renderer, runtime, export, and quality-report contracts.

The new visual system is authoritative for icon appearance. Existing AniDiagram
architecture remains authoritative for scene layout, node geometry, connectors,
motion policy, export behavior, and runtime orchestration.

## First principles

1. **An icon identifies a node before it decorates it.** Its static silhouette
   must remain recognizable at 48, 64, and 96 px.
2. **Motion explains change.** It must communicate a state transition or a
   technical action; it must not exist only to keep the screen moving.
3. **One semantic asset has one source of truth.** Python, browser runtime, and
   future React adapters must not maintain independent geometry.
4. **A scene owns layout; an icon owns its internals.** Connection routing and
   node anchors stay outside icon SVG assets.
5. **Static output is first-class.** SVG remains complete and readable without
   JavaScript, GSAP, animation, or network access.
6. **Compatibility precedes catalog expansion.** Existing valid DiagramScript
   scenes must keep rendering throughout the migration.
7. **Public naming stays simple.** Draft labels and legacy implementation ids do
   not become user-facing product versions.

## Scope

### In scope

- One canonical 56-icon node catalog.
- Four benchmark icons: `agent`, `database`, `api`, and `server`.
- Stable SVG part semantics and instance-safe DOM identity.
- Existing style-token integration.
- Icon asset manifests and compilation into the existing scene Motion Manifest.
- State, action, and performance semantics.
- Reduced-motion, static fallback, quality checks, and visual regression.
- Compatibility aliases for existing icon-system ids during migration.

### Out of scope for the first implementation plan

- Hand-authoring 56 finished icons in one pass.
- A standalone React icon package.
- A new layout engine or connector router.
- Replacing DiagramScript or Scene IR.
- Camera choreography, narration, or a full animation editor.
- Treating payloads, status elements, and connectors as part of the 56 node
  icons.

## Public identity and compatibility

The only public icon-system identity is:

```text
AniDiagram Diagram Core Icon System v1.0
```

The only new canonical runtime/configuration id is:

```text
diagram-core-v1
```

Existing ids are compatibility inputs, not additional public product versions:

| Existing id | Migration behavior |
| --- | --- |
| `illustrated-character-v1` | Retained as a legacy alias until the default-promotion gate passes, then kept for explicit legacy rendering during the deprecation window. |
| `illustrated-character-v2` | Experimental concepts are absorbed into Diagram Core v1; the id remains readable only for existing examples until those examples migrate. |
| `illustrated-v1` | Preserved as an explicit legacy renderer mode. |
| `semantic-line-v1` | Preserved as an explicit legacy renderer and fallback mode. |

`Draft A`, `Draft B`, `Draft D`, and similar labels are design-history labels.
They must not appear in public configuration, catalog ids, or current reference
art after the specification-freeze checkpoint.

Minor asset corrections do not create new icon-system versions. The catalog
records a `catalog_revision`, and individual assets record an internal
`asset_revision`. A new public system version is reserved for an incompatible
manifest, semantic, or rendering contract.

## Catalog contract

The node catalog contains the 48 planned PRD icons plus the eight existing
AniDiagram semantics that were absent from that list.

### Exact 56-icon inventory

| Category | Count | IDs |
| --- | ---: | --- |
| Actors | 7 | `user`, `developer`, `operator`, `agent`, `agent-team`, `assistant`, `human-reviewer` |
| AI & Models | 8 | `ai-model`, `llm`, `neural-network`, `reasoning`, `embedding`, `memory`, `tool`, `token` |
| Data & Knowledge | 7 | `database`, `vector-database`, `data-warehouse`, `document-store`, `knowledge-base`, `dataset`, `search` |
| Files & Content | 9 | `file`, `folder`, `document`, `pdf`, `image`, `audio`, `video`, `code-file`, `output` |
| Network & Interfaces | 7 | `api`, `webhook`, `http-request`, `gateway`, `load-balancer`, `message-queue`, `shield` |
| Compute & Runtime | 6 | `server`, `server-cluster`, `cloud`, `container`, `function`, `edge-node` |
| Development & Delivery | 6 | `source-code`, `git-repository`, `branch`, `pull-request`, `ci-cd`, `deployment` |
| Operations & Observability | 6 | `task`, `scheduler`, `monitoring`, `logs`, `alert`, `debug` |

The list has 56 unique ids. The existing 13 DiagramScript icons are a subset:

```text
agent api cloud database file folder memory operator output
search shield token tool
```

Semantic distinctions that must not be collapsed:

- `file` is a generic file container; `document` is textual document content.
- `operator` is a human operating a system; `developer` is a software-development
  role; `human-reviewer` is an approval/review role.
- `token` may be a node icon when tokenization or model intent is itself a node;
  `payload.token` is a separate small connector payload.
- `output` is a result or delivery node; it is not an alias of `document`.

Each catalog entry must declare:

```text
id
category
semantic_kind
structural_prototype
aliases
parts
supported_states
supported_actions
status
asset_revision
```

`structural_prototype` is the reuse boundary for family consistency. Examples
include `actor-character`, `ai-core`, `stacked-storage`, `file-card`,
`interface-module`, `compute-device`, `pipeline-tool`, and
`observability-panel`. Shared prototypes may share construction helpers, but
each exported icon remains a complete independent asset.

Catalog `status` is one of `planned`, `visual-review`, `approved`, or
`deprecated`. The catalog may describe all 56 planned ids from Phase 0, but a
new id becomes valid DiagramScript input only after its asset reaches
`approved`. Existing 13 DiagramScript ids remain valid throughout migration and
continue through their current renderer until a Diagram Core asset is approved.

## Canonical asset architecture

The canonical source is vendor-neutral SVG plus machine-readable manifests:

```text
assets/diagram-core/
├── catalog.json
├── tokens.css
├── icons/
│   ├── agent.svg
│   ├── database.svg
│   ├── api.svg
│   └── server.svg
├── manifests/
│   ├── agent.json
│   ├── database.json
│   ├── api.json
│   └── server.json
└── previews/
```

Repository consumers are adapters around that source:

```text
canonical SVG + icon manifest
        |
        +--> Python asset loader --> SVG renderer and static exports
        |
        +--> scene manifest compiler --> existing HTML/GSAP runtime
        |
        +--> future generator --> React component package
```

No adapter may contain a second hand-maintained copy of icon paths.

### Runtime ownership

- The Python core owns catalog validation, asset loading, instance namespacing,
  style-token resolution, scene compilation, fallback behavior, and exports.
- The existing Scene Motion Manifest owns resolved node instances, scene timing,
  motion profile, concurrency policy, and edge/stage coordination.
- The browser runtime owns DOM resolution and performance playback.
- A future React adapter owns component ergonomics only. It does not own paths,
  themes, or performance definitions.

## SVG visual contract

### Geometry

- Authoring viewBox: `0 0 96 96`.
- Safe zone: 8 px.
- Recommended subject bounds: 72–80 px.
- Required review sizes: 48, 64, and 96 px.
- Outer authored stroke: 2.0–2.25 px at the 96 px grid.
- Internal authored stroke: 1.25–1.5 px.
- Round caps and joins.
- Six to twelve major visual shapes by default.
- Three to five public motion groups by default.
- No embedded raster images, external resources, runtime text dependency, or
  complex filters.

Strokes scale naturally with the SVG by default. The system must not apply
`vector-effect="non-scaling-stroke"` globally. An optical-size exception may be
introduced only after the 48 px review proves that natural scaling fails, and
the exception must be recorded in the icon manifest.

### Theme tokens

Icon SVG uses CSS custom properties with static fallbacks:

```css
fill: var(--icon-surface-main, #fffaf2);
stroke: var(--icon-stroke, #14213d);
```

The existing AniDiagram style system maps canvas, role, and state colors into
the icon token set. `blue`, `dark`, `warm`, and `green` are validation contexts,
not a second independent style architecture.

Meaningful graphical boundaries and state indicators must reach at least 3:1
contrast against adjacent colors. State meaning must remain understandable
without hue alone through shape, position, rhythm, or a visible mark.

### Static fallback

- The SVG must render correctly when CSS variables are unsupported by using the
  declared fallback values.
- Runtime-only effects such as particles, halos, scan lines, and travelling
  payloads do not live in the canonical SVG.
- Shadows are optional consumption-layer effects and never carry semantics.
- Removing all animation must not change layout, bounds, labels, or connectors.

## Part identity and instance safety

Stable public identity is expressed through `data-part`, not a global DOM id:

```xml
<g data-icon="database">
  <g data-part="shell">...</g>
  <g data-part="core">...</g>
  <g data-part="mechanism">...</g>
  <g data-part="indicator">...</g>
</g>
```

At scene render time, any required DOM id is namespaced:

```text
{instance-id}__{icon-id}__{part-name}
```

Rules:

- `data-part` names remain stable across instances and asset revisions.
- Runtime resolution is scoped to the current icon root.
- Manifests never store global selectors such as `#database__shell`.
- The same icon may appear any number of times without duplicate ids or selector
  collisions.
- Fine-grained private parts may exist but are not public performance targets.

## Anchors, ports, and effect attachments

Connection anchors remain owned by AniDiagram node geometry and layout. They are
not embedded in icon SVG and are not repeated in every icon asset manifest.

Icons such as `api`, `gateway`, and `load-balancer` may render visual port parts:

```text
port-input
port-output
```

Those parts are visual affordances only. Edges still terminate at node-level
layout anchors, allowing horizontal, vertical, orthogonal, and bidirectional
layouts without changing the icon.

Runtime effects use icon-local attachment coordinates:

```json
{
  "attachments": {
    "receive": {"x": 8, "y": 48},
    "send": {"x": 88, "y": 48},
    "status": {"x": 48, "y": 78}
  }
}
```

Attachments replace empty `effect-slot` groups. They define targets for payloads
and injected effects without becoming visible connection anchors.

## Motion semantics

Motion is divided into three layers.

### State

A persistent condition:

```text
idle active processing success warning error paused offline waiting
```

### Action

A discrete external event understood by the scene or choreographer:

```text
enter receive process send retry sync approve reject exit
```

Additional domain actions such as `read`, `write`, `search`, `index`, `generate`,
`reason`, `stream`, `queue`, `deploy`, and `scale` are allowed capabilities, not
replacement names for persistent states.

### Performance

The icon-specific implementation of an action:

```text
agent.process             -> agent.think-v1
database.write            -> database.write-v1
api.process               -> api.request-response-v1
server.process            -> server.compute-v1
```

Every performance follows the same semantic lifecycle:

```text
prepare -> action -> confirm -> settle
```

Every performance definition declares:

```text
id
action
required_parts
optional_parts
initial_state
final_state
duration
repeat_policy
cancel_behavior
reduced_motion_behavior
parameters
```

### Motion rules

- The icon shell and node layout remain stable.
- A performance moves one to three meaningful parts whenever possible.
- `idle` is a state, not a mandatory infinite animation.
- Ambient repetition is enabled only by a scene motion profile such as
  `runtime-loop`; it is not hard-coded inside the asset.
- Scene motion policy owns concurrency and focus. Icons do not independently
  decide to animate at the same time.
- One-shot success, warning, and error feedback must settle into the declared
  final state.
- Cancellation restores declared rest transforms and opacities.
- With `prefers-reduced-motion: reduce`, the browser creates no transform,
  particle, travelling-payload, or repeating icon timeline. State changes apply
  immediately or through a restrained opacity/color transition.

Recommended timing ranges:

```text
micro feedback: 120–220 ms
state transition: 220–420 ms
semantic action: 600–1200 ms
full prepare-to-settle performance: 900–1800 ms
optional ambient interval: 2400–5000 ms
error shake, when motion is allowed: 260–420 ms
```

## Manifest model

### Icon Asset Manifest

The per-icon manifest describes stable asset capabilities and contains no scene
instance selectors:

```json
{
  "id": "database",
  "system": "diagram-core-v1",
  "asset_revision": 1,
  "viewBox": "0 0 96 96",
  "category": "data-knowledge",
  "semantic_kind": "storage",
  "structural_prototype": "stacked-storage",
  "parts": ["shell", "core", "mechanism", "indicator"],
  "attachments": {
    "receive": {"x": 48, "y": 8},
    "send": {"x": 88, "y": 48},
    "status": {"x": 48, "y": 78}
  },
  "states": ["idle", "active", "processing", "success", "warning", "error"],
  "actions": ["receive", "read", "write", "search", "index", "send"],
  "status": "approved"
}
```

### Scene Motion Manifest

The existing scene compiler combines:

```text
node instance
+ icon asset manifest
+ selected action/performance
+ scene motion profile
+ motion policy
= resolved scene Motion Manifest entry
```

The scene entry contains the instance root, resolved part references, timing,
intensity, repeat policy, and reduced-motion policy. The asset manifest remains
portable and unchanged.

## Failure and fallback behavior

- Unknown icon ids remain DiagramScript validation errors.
- A new catalog id with `planned` or `visual-review` status returns an explicit
  `icon_not_implemented` validation error; it does not silently render a generic
  fallback.
- During Phases 1–2, an existing valid DiagramScript icon without an approved
  Diagram Core asset continues through its existing renderer. If
  `diagram-core-v1` is explicitly requested for that icon, the scene uses the
  existing fallback and emits one explicit quality warning.
- Missing required parts prevent that performance from starting, preserve the
  static icon, and emit a runtime diagnostic containing icon id, instance id,
  performance id, and missing parts.
- Missing optional parts skip only the optional motion track.
- Invalid manifests fail catalog validation before rendering.
- Missing GSAP preserves the complete static scene.
- An unsupported theme token resolves to the SVG fallback value.
- A runtime cancellation or mode switch must restore the authored rest state.

## Rollout and promotion gates

### Phase 0 — Specification freeze

- Adopt the public name and `diagram-core-v1` id.
- Correct or replace the non-authoritative `v2 — Draft D` title in reference
  art.
- Freeze the 56 unique catalog ids and category placement.
- Freeze the SVG and Icon Asset Manifest schemas.
- Record legacy id behavior.

### Phase 1 — Four static benchmark icons

- Implement `agent`, `database`, `api`, and `server` as canonical SVG assets.
- Validate 48, 64, and 96 px in blue, dark, warm, and green contexts.
- Approve static silhouette, visual weight, family consistency, and token
  behavior before starting icon performances.

### Phase 2 — Four-icon motion proof

- Compile asset manifests into the existing Scene Motion Manifest.
- Implement state/action/performance separation.
- Prove instance-safe repeated icons, cancellation, reset, static fallback, and
  reduced motion.
- Produce an Agent Runtime Flow proof using the four benchmark icons.

### Phase 3 — Existing-system compatibility closure

Implement the ten remaining current semantics:

```text
cloud file folder memory operator output search shield token tool
```

At completion, the new visual system covers the existing 13 DiagramScript icons
plus `server`, for 14 approved assets. The default changes to `diagram-core-v1`
only when:

- all existing valid icon scenes render without fallback;
- the existing export matrix remains functional;
- quality reports are clean;
- static, runtime, and reduced-motion browser checks pass;
- compatibility examples are updated.

### Phase 4 — Catalog completion

Implement the remaining 42 icons in six batches of seven. Each batch groups
icons by structural prototype where possible and repeats the same static,
manifest, motion, and visual-regression gates. A new id enters the generated
DiagramScript schema only when its catalog status changes to `approved`.

### Phase 5 — SDK adapters

Generate React components and any future SDK adapters from the canonical assets.
No adapter is approved if it introduces independently maintained paths or
performance definitions.

## Acceptance criteria

### Catalog and compatibility

- The catalog contains exactly 56 unique ids.
- All existing 13 DiagramScript icon ids are present.
- Catalog, schema, renderer coverage, gallery coverage, and quality checks agree
  on the implemented set.
- Phase 3 has no icon fallback for any previously valid built-in scene.

### Visual

- Benchmark icons remain distinguishable at 48 px with their node labels hidden
  during the recognition review.
- All icons remain readable with accent color removed.
- Blue, dark, warm, and green contexts preserve silhouette and hierarchy.
- Essential state indicators reach 3:1 contrast against adjacent colors.
- A benchmark contact sheet is manually approved before motion work begins.

### SVG and asset quality

- Every asset uses `viewBox="0 0 96 96"`.
- Stable `data-part` names match the asset manifest.
- Repeated instances produce no duplicate DOM ids.
- No anonymous public parts, embedded raster data, external resources, or
  complex filters exist.
- A benchmark icon contains at most 24 rendered SVG elements unless its manifest
  records an approved exception.
- A benchmark source SVG targets at most 12 KB uncompressed and 6 KB gzip unless
  its manifest records an approved exception.
- Standalone SVG rendering succeeds without runtime JavaScript.

### Motion and runtime

- Every performance declares required parts, lifecycle, duration, final state,
  cancellation, and reduced-motion behavior.
- Closing or cancelling a performance restores the authored rest state.
- `prefers-reduced-motion: reduce` creates no GSAP icon timeline.
- A repeated-icon test proves that two instances of the same icon animate only
  their own parts.
- A fixed browser performance fixture with 20 animated icons has no icon-runtime
  long task over 50 ms during the measured five-second window and targets a p95
  frame time no worse than 33.3 ms.

### Visual regression

The four-icon benchmark matrix covers:

```text
4 icons
x 3 sizes
x 4 validation contexts
x 6 persistent states: idle / active / processing / success / warning / error
= 288 static cells
```

Cells may be combined into deterministic contact sheets. Browser, viewport,
device scale factor, fonts, animation state, and screenshot timing are locked.
Automated pixel comparison uses a maximum one-percent differing-pixel ratio,
while every baseline update still requires human visual approval.

## Documentation ownership

- The Cbrain PRD remains the complete product and visual specification.
- This file remains the repository engineering contract.
- `docs/diagram-script.md` documents user-facing icon ids and compatibility.
- `docs/html-runtime.md` documents resolved performances and runtime limits.
- Generated galleries and contact sheets provide visual evidence; they are not
  normative specifications.
- README examples change only after the Phase 3 default-promotion gate passes.

## Resolved decisions

- The public name is unified as Diagram Core Icon System v1.0.
- Reference-board theme decoration is non-authoritative; icon geometry and visual
  language are authoritative.
- The catalog contains 56 node icons.
- Canonical SVG and manifests are the single asset source.
- React is a generated later adapter, not a Phase 1 requirement.
- Stable part identity uses `data-part`; scene ids are instance-scoped.
- Layout owns connection anchors; manifests own only effect attachments.
- State, action, and performance are separate concepts.
- Static approval precedes motion implementation.
- The default changes after the 14-asset compatibility gate, not after all 56
  icons are complete.
