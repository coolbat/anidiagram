# Runtime Motion Roadmap

AniDiagram's current high-fidelity HTML runtime defaults to **ambient runtime**
mode with the **expressive** motion profile.

## Current Default: Ambient Runtime

Ambient runtime means:

- each supported semantic icon owns its local micro-performance;
- every built-in semantic icon has a runtime performance in expressive mode;
- expressive runtime also generates GSAP-owned edge flow particles and title
  sweep in the browser;
- icon performances loop independently with a small staggered delay;
- the SVG stage stays static in `runtime-stage` mode;
- the runtime does not choreograph the whole graph as a causal timeline;
- edge arrival, camera movement, step mode, hover replay, and node state
  machines are not part of the default runtime.

This is the only runtime mode supported by default in the current release. Other
runtime modes must be explicitly introduced later and must not change the
default `html` behavior.

## Planned Modes

The following modes are roadmap items, not current product capabilities.

| Mode | Status | Intent |
| --- | --- | --- |
| `timeline` / `choreographer` | Planned | Play the whole diagram as a staged explanation with causality and optional narration beats. |
| `event-driven` | Planned | Trigger node performances when edge signals arrive instead of using fixed global time offsets. |
| `state-machine` | Planned | Give nodes explicit `idle`, `active`, `complete`, and `error` states driven by a runtime scheduler. |
| `interactive` | Planned | Allow hover, click, replay, inspect, or step actions to trigger local performances. |
| `hybrid` | Planned | Default to ambient motion, then enter timeline or step mode only when the user explicitly starts an explanation. |

## Product Rule

`diagram.html` should remain the best high-fidelity output, but it should not
silently switch into a new scheduling model. If a future release adds timeline,
event-driven, state-machine, interactive, or hybrid behavior, it should require
an explicit option in the manifest, CLI, or scene spec.

The current expressive ambient runtime is a frozen baseline documented in
`runtime/motion-catalog.json` and reviewed through `gallery/runtime-motion.html`.
Any change to timing, intensity, icon semantics, stable part IDs, stage effects,
default profile/mode, or runtime scheduling should be confirmed before code
changes begin.

The current manifest mode is:

```json
{
  "mode": "ambient",
  "sequence": "independent-icon-loops"
}
```

`scene_sequence` may preserve the source DiagramScript `motion.sequence` value
for debugging, but it does not drive runtime scheduling in ambient mode. The
current ambient stage effects are local loops, not a diagram-wide causal
timeline.
