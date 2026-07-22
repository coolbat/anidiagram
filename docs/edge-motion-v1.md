# Edge Motion v1

Status: frozen approved release `1.0.0` (human visual acceptance confirmed on
2026-07-22).

Edge Motion v1 is the canonical connection-line contract for new AniDiagram
output. It applies only to edges between nodes. Arrow-like parts inside an icon
remain owned by that icon system's performance contract.

## Canonical effects

| Preset | Meaning | Visual recipe |
| --- | --- | --- |
| `none` | Motion explicitly disabled | Authored edge only |
| `static` | Static relation | Authored edge and endpoint marker only |
| `draw` | Structural or contextual relation | One source-to-target reveal, then rest |
| `packet-flow` | Discrete data, command, event, or result | One role-colored solid dot moves on a static arrow |
| `comet-flow` | Explicitly emphasized burst or high-priority transfer | One leading solid dot with three shrinking fading echoes moves on a static arrow |
| `stream-flow` | Continuous, repeated, or cyclic flow | One moving dashed stroke, with no particle |

`packet-flow` has one length-invariant, borderless packet. It never adds a
moving dash track. `stream-flow` never adds a particle. This prevents two
motion layers from communicating the same transfer.

`comet-flow` has one length-invariant, borderless leading packet plus three
borderless echoes. The echoes progressively shrink and fade; the recipe never
adds a moving dash track. It is opt-in emphasis, not the automatic default for
every event-driven relation.

## Semantic selection

- `flow.repeat: loop` resolves to `stream-flow`.
- Primary and supporting relations resolve to `packet-flow`.
- Explicit burst or high-priority transfer emphasis resolves to `comet-flow`.
- Context relations resolve to `draw`.
- Disabled and reduced-motion output keeps authored arrows static.

Expressive mode enables every eligible edge. Readable mode first covers
distinct semantic flows, then fills remaining slots by importance, step, and
authored order. Off mode creates no edge-motion elements.

## Legacy aliases

Older DiagramScript remains valid. Renderers normalize these names before
drawing:

| Legacy preset | Edge Motion v1 |
| --- | --- |
| `pulse`, `trace`, `dynamic-dash`, `dash-flow`, `glow-line` | `stream-flow` |
| `flow-dot`, `flow-arrow`, `signal-dot`, `signal-arrow` | `packet-flow` |
| `ghost-flow`, `comet` | `comet-flow` |

The frozen public Illustrated 2.3 runtime and manifest remain unchanged. New
HTML output uses `motion-manifest-0.2` plus the additive
`edge-motion-v1-runtime.js`; candidate runtimes implement the same recipes.
The Edge Motion release does not promote the separate Illustrated 2.4 icon
candidate or its review-only motion contract.
