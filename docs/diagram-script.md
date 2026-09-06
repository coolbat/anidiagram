# DiagramScript

AniDiagram accepts DiagramScript JSON and compiles it into a typed Scene IR
before rendering or exporting.

## Composition contract

DiagramScript v0.4 implements the independent icon system, visual style,
layout, and motion contract. DiagramScript v0.1-v0.3 remain supported and keep
their previous default behavior; v0.3 is not silently changed.

See [the composition contract](./diagram-composition-contract.md) and
[ADR-001](./decisions/ADR-001-separate-semantic-content-from-presentation.md).

Plan 0.2 / Script 0.4 also support opt-in repository evidence, typed semantics,
and an authored-topology reader. See [verified reading](./verified-reading.md)
for the contracts, comparison command, chapters, share cards, and visual receipts.
These extensions do not change legacy defaults or create a second renderer.

## v0.1

`0.1` is the compatibility schema. It supports:

- `canvas`
- `title`
- `style`
- `groups`
- freeform `nodes`
- `edges`
- explicit edge `points`

Schema: `schemas/diagram-script-v0.1.schema.json`.

## v0.2

`0.2` adds the product-kernel fields used by the preset compiler and quality
checks:

- `preset`: source preset name when generated from a built-in preset.
- node `step`: visible step badge.
- edge `route`: `curved`, `straight`, `hv`, `vh`, `orthogonal`, or `points`.
- edge `step`: visible step badge near the edge label.
- edge `animated`: boolean motion toggle.
- top-level `motion`: scene-level motion profile and sequencing controls.
- tighter role validation for `actor`, `source`, `process`, `agent`, `memory`,
  `tool`, `output`, `risk`, and `neutral`.

Schema: `schemas/diagram-script-v0.2.schema.json`.

The Python validator also checks cross-field behavior that JSON Schema cannot
fully express here, including duplicate ids, edge references, route/points
requirements, and canvas bounds.

## v0.3

`0.3` adds the first version of AniDiagram's effect registry syntax:

- `motion.profile`: adds `teaching`.
- `motion.sequence`: adds `staged`.
- `motion.edge`, `motion.node`, `motion.group`, and `motion.title`: accept
  either the legacy string form or a structured effect object.
- node `icon`: semantic icon id for built-in clean-room SVG primitives.
- node `shape`: `rect` or `decision`.
- node, edge, and group `effect`: per-element effect override.
- effect `icon_motion`: icon-local motion hint for `icon-semantic` nodes.
- top-level `motion_policy`: budget controls for how many edges, particles,
  nodes, and group borders may be actively animated.
- effect `particle_count` and `trail_count`: per-effect density controls.
- `runtime-loop` profile: looping runtime-state motion with static structure,
  signal edges, icon breathing, static groups, and breathing title.

Schema: `schemas/diagram-script-v0.3.schema.json`.

## v0.4

`0.4` adds `composition-v1` output fields:

- top-level `locale` (`auto`, `en`, or `zh-CN`) for accessible language
  metadata and locale-aware font fallback selection;
- top-level `icon_system`, independent from the style profile;
- `composition_policy: "composition-v1"`;
- `resolved_presentation`, recording the concrete icon, style, layout, and
  motion values plus `explicit`, `default`, `model`, `fallback`, or `legacy`
  provenance; icon systems such as `illustrated` MAY also record a separate
  semantic version;
- `showcase-v1`, which enables every eligible performance from the resolved icon
  system, data-flow edge, group treatment, and title entry while preserving
  rest poses and reduced-motion behavior;
- the approved 56-icon `illustrated` 2.5.0 catalog as the composition-v1 default.

Schema: `schemas/diagram-script-v0.4.schema.json`.

Structured effect object example:

```json
{
  "preset": "icon-semantic",
  "icon_motion": "database-write"
}
```

Legacy v0.3 semantic icons:

`database`, `file`, `folder`, `api`, `cloud`, `search`, `shield`, `agent`,
`token`, `memory`, `tool`, `output`.

Supported node shapes:

- `rect`: default rounded rectangle node.
- `decision`: diamond-shaped decision node for branches and quality gates.

DiagramPlan v0.2 is the default higher-level brief/LLM contract and compiles to
resolved DiagramScript v0.4. DiagramPlan v0.1 remains available for explicit
legacy `explainer-board` output to v0.3. See
[prompt-to-diagram-flow.md](./prompt-to-diagram-flow.md).

## Motion Profiles

`motion` is AniDiagram's clean-room animation vocabulary inspired by timeline
and stagger concepts from mature animation tools. It does not require a
third-party runtime.

```json
{
  "motion": {
    "profile": "expressive",
    "sequence": "layered",
    "ease": "spring",
    "stagger": 0.16,
    "duration_scale": 0.9,
    "intensity": 1.25,
    "node": "pop",
    "edge": "comet-flow",
    "group": "marching-ants",
    "reduced_motion": "subtle"
  }
}
```

Profiles:

- `off`: static SVG with no active motion.
- `subtle`: restrained entry and draw-on edges.
- `normal`: default balanced motion.
- `expressive`: layered sequence with stronger node and edge motion.
- `teaching`: staged teaching motion with semantic icons, line flow, and title
  reveal defaults.
- `runtime-loop`: static structure with looping signal flow and restrained icon
  breathing.
- `showcase-v1`: composition-v1 default with every eligible icon performance
  and data-flow edge enabled.

`expressive` remains the compatibility default when a direct DiagramScript
omits `motion`. DiagramPlan v0.2 compilation resolves `showcase-v1` explicitly.

Motion channels:

- `sequence`: `simultaneous`, `step-stagger`, `layered`, `staged`, or `loop`.
- `node`: `none`, `fade`, `float`, `glow-breathe`, `pop`, `pulse`,
  `ripple`, `status-blink`, `icon-pulse`, `icon-breathe`, `icon-semantic`,
  `icon-performance`, or `micro-icon`.
- `edge`: new output uses `none`, `static`, `draw`, `packet-flow`,
  `comet-flow`, or `stream-flow`. The legacy names `pulse`, `trace`,
  `dynamic-dash`, `dash-flow`, `flow-dot`, `flow-arrow`, `signal-dot`,
  `signal-arrow`, `ghost-flow`, `glow-line`, and `comet` remain accepted and
  normalize to the Edge Motion v1 recipes documented in
  [`edge-motion-v1.md`](edge-motion-v1.md).
- `group`: `none`, `static`, `soft-reveal`, `marching-ants`, `border-scan`,
  or `corner-pulse`.
- `title`: `none`, `fade`, `breathe`, `handwrite-reveal`, or
  `highlight-sweep`.
- `reduced_motion`: `static`, `subtle`, or `pause`.

## Motion Policy

`motion_policy` is a separate budget layer. It does not change what an effect
means; it limits how many resolved effects are allowed to remain active. This
keeps generated diagrams readable when many elements ask for motion.

```json
{
  "motion_policy": {
    "profile": "focused",
    "motion_area": "small",
    "max_active_flow_edges": 4,
    "max_particle_edges": 3,
    "particle_count_per_edge": 1,
    "flow_trail_count": 1,
    "max_active_pulse_nodes": 1,
    "pulse_mode": "rotate",
    "max_scanning_groups": 1
  }
}
```

Profiles:

- `unrestricted`: no built-in clamp.
- `readable`: sparse movement for dense architecture diagrams.
- `focused`: a few active paths for explainer and teaching diagrams.
- `expressive`: higher limits for showcase output.
- `readable-runtime`: larger edge count but micro-sized motion for runtime-loop
  diagrams.

When the configured effects exceed the policy, SVG and raster renderers clamp
extras into calmer draw/fade/soft-reveal behavior. Quality reports emit a
`motion_overload` warning so generated specs can be tuned upstream.

Runtime-loop example:

```json
{
  "motion": {
    "profile": "runtime-loop",
    "sequence": "loop",
    "edge": {"preset": "signal-dot", "particle_count": 1, "trail_count": 0},
    "node": {"preset": "icon-breathe"},
    "group": {"preset": "static"},
    "title": {"preset": "breathe"}
  },
  "motion_policy": {
    "profile": "readable-runtime",
    "motion_area": "micro"
  }
}
```

## Actionable quality diagnostics

Quality issues keep the stable `code`, `severity`, `path`, and `message`
fields and also expose three repair-oriented fields:

- `subject`: stable node or edge identities affected by the issue;
- `evidence`: measured rectangles, segments, widths, limits, or other facts;
- `supported_fixes`: bounded repair operations understood by the current
  authoring contract.

For example, `edge_node_collision` identifies the edge, blocking node, and
first intersecting segment when an authored waypoint enters a node. New checks
that reveal compatibility-sensitive legacy output live in the separate
non-blocking `advisories` array: `edge_segment_node_collision` detects a route
segment crossing a node even when both waypoints are outside, and
`edge_label_hidden` reports the available and required width before the
renderer would omit a cramped straight-edge label. Advisories do not change
`ok`, `score`, or the existing error/warning summary. These diagnostics are
guidance, not automatic mutation: update the DiagramPlan or DiagramScript,
then rerender and require a clean quality report.

## Atomic delivery receipt

Use `--deliver` when the rendered files are acceptance or release artifacts:

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --plan examples/contracts/production-request-path.plan.json \
  --spec-out outputs/production/production-request-path.diagram.json \
  --outdir outputs/production \
  --basename production-request-path \
  --formats svg,html,quality \
  --deliver
```

The delivery path freezes the exact source bytes and the resolved in-memory
DiagramScript, validates quality before touching public targets, writes every
format into a same-filesystem private directory, rejects skipped, missing, or
empty artifacts, and commits targets with same-directory `os.replace` plus
rollback. The generated `.delivery.json` receipt follows
[`delivery-receipt-v0.1.schema.json`](../schemas/delivery-receipt-v0.1.schema.json)
and identifies itself as `AniDiagramDeliveryReceipt` v0.1. It records:

- the source kind, optional absolute source path, SHA-256, and byte count;
- canonical resolved DiagramScript and style SHA-256 values;
- render options and the quality summary, including advisory count;
- final absolute path, SHA-256, and byte count for each committed artifact.

Generated `--plan-out` and `--spec-out` files participate in the transaction
when they are in `--outdir`. A blocking quality error, skipped exporter,
missing staged output, or replacement failure produces exit code 3 and one
structured JSON error on stderr. Previously published targets remain unchanged
or are restored from the private transaction backup. If the operating system
also prevents rollback, the error exposes `delivery.recovery_path` and retains
the private backup for manual recovery.

## Effect Objects

DiagramScript v0.3 keeps the existing string motion channels as compatibility
syntax and adds structured effect objects for richer line, node, group, title,
and semantic icon behavior.

`icon-semantic` keeps node frames still and animates only local icon parts.
Default icon motions are:

| Icon | Default motion |
| --- | --- |
| `database` | `database-write` |
| `memory` | stacked memory cards |
| `file` | `file-lines`: page entrance, scale overshoot, folded-corner motion, and fast content-line reveal |
| `folder` | `folder-open` |
| `api` | `api-ping` |
| `cloud` | `cloud-upload` |
| `search` | `search-sweep` |
| `shield` | `shield-check` |
| `agent` | `agent-orbit` |
| `tool` | `tool-tap` |
| `output` | `output-check` |
| `token` | `token-pulse` |

`icon-performance` is a runtime-ready node preset. Standalone SVG cannot play
the high-fidelity JavaScript runtime performances, so `icon-performance`
degrades to lightweight SVG/SMIL icon motion in standalone SVG. Use
`--formats html --html-runtime gsap` for the Motion Manifest and browser
runtime path. `html-runtime` is accepted as a legacy alias for `html`. When
those performances need to survive raster, video, PDF, or Lottie export, use
`--export-renderer browser`; PNG, GIF, PDF, WebP, MP4, APNG, and frame-based
Lottie are then captured from the real `html` page instead of the lightweight
Python preview renderer. The legacy high-fidelity semantic runtime
performances are:

| Icon | Runtime performance |
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

The runtime manifest maps each performance to stable SVG part IDs such as
`#icon-agent-outline-left`, `#icon-api-request-token`, and
`#icon-search-result-1`.
See [html-runtime.md](./html-runtime.md) for the runtime ownership model and
current limitations.

## Illustrated and legacy character icons

`illustrated-character-v1` remains the legacy v0.1-v0.3 default when a style
omits `icon_system`. It clean-room covers all 13 legacy schema icons: `agent`, `operator`,
`search`, `tool`, `api`, `memory`, `output`, `file`, `folder`, `cloud`,
`shield`, `token`, and `database`. Set `icon_system` explicitly to
`illustrated-v1` for the previous bubble treatment or `semantic-line-v1` for
the original line-icon system.

`illustrated` is the public id for the approved static Illustrated system. Its
current implementation version is `2.5.0`, recorded separately in
`resolved_presentation.icon_system.version`. Its 56 structured semantic
illustrations have exact id parity with Diagram Core v1. It is the
composition-v1 default; `diagram-core-v1` remains an explicit option. All 56 icons emit approved public
`illustrated-performance-v6` runtime performances under `showcase-v1`. The
v6/v7 review contracts are immutable archived human-review sources and are not
emitted by new diagrams. The former `illustrated-performance-v5` public
contract remains the immutable twenty-icon 2.4.0 archive. The former
`illustrated-performance-v4` public contract and its v4-review source remain
2.3.0 archives. The `illustrated-performance-v3` public contract and
`illustrated-performance-v3-review` review contract remain 2.2.0 archives, and
`illustrated-performance-v2` remains the immutable eight-icon 2.1.0 archive,
and `illustrated-performance-v1` remains the immutable four-icon 2.0.0 archive.
Uncovered icons use the existing fallback and produce a quality
warning. The legacy id
`illustrated-character-v2` remains an input alias. The old
[`illustrated-semantic-v2-structured.diagram.json`](../examples/illustrated-semantic-v2-structured.diagram.json)
example and its review style are historical design evidence, not current
adoption guidance or a second public style.

Illustrated 2.5.0 visual constants live in
[`assets/illustrated/tokens-2.5.0.json`](../assets/illustrated/tokens-2.5.0.json). A style
can explicitly override approved colors with an `illustrated_tokens` object,
for example `{"ink": "#172033", "paper": "#fffaf0"}`. The renderer rejects
unknown token names and non-hex values. Geometry, paths, part ids, and semantic
roles are not template-owned and remain frozen within version 2.5.0. All 13
public styles contain approved Illustrated token mappings. They preserve
semantic accent distinctions instead of applying one monochrome tint.

The 13 quiet semantic performances are `brain-think-pulse-v1`,
`operator-type-focus-v1`, `search-scout-find-v1`, `tool-kit-action-v1`,
`api-signal-return-v1`, `memory-index-commit-v1`,
`output-envelope-reveal-v1`, `file-note-write-v1`, `folder-file-store-v1`,
`cloud-uplink-ready-v1`, `shield-guard-confirm-v1`, `token-intent-ready-v1`,
and `bucket-ingest-confirm-v1`. Each valid schema icon is covered by the
default system; invalid icon names remain schema errors.

For Character v1 diagrams, use a `focused`, `readable`, or `readable-runtime`
motion policy when the scene is dense. Author only the primary paths as
animated; set non-key edges to `"animated": false` instead of depending on
runtime clamping to hide an overloaded source specification. HTML Readable mode
then narrows the stage further to at most two key edge packets.

The supported theme combinations are `illustrated-character`, `deep-tech`, and
`teaching-sketch-character`. See
[the three-theme comparison](../gallery/character-themes.html) and the
representative `agent-memory`, `high-fidelity-runtime`, pipeline, layered, and
sequence examples for current default behavior. Explicit legacy demonstrations
must set `icon_system` to `illustrated-v1` or `semantic-line-v1`.

See [icon-system-release-status.md](./icon-system-release-status.md) for the
current/default/legacy matrix and immutable release boundaries.

The broader feature plan is documented in
[motion-effects-feature-plan.md](./motion-effects-feature-plan.md).
