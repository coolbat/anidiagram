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

This remains the only runtime mode selected by default. Choreographer modes are
available only through an explicit CLI/runtime option and do not change the
default `html` behavior.

## Mode Status

AniDiagram 0.2.0 ships the first bounded causal scheduler while keeping more
dynamic scheduling modes on the roadmap.

| Mode | Status | Intent |
| --- | --- | --- |
| `timeline` / `choreographer` | Shipped, opt-in | Play authored edges as ordered source -> edge -> target explanation steps with start/previous/next controls. |
| `event-driven` | Planned | Trigger node performances when edge signals arrive instead of using fixed global time offsets. |
| `state-machine` | Planned | Give nodes explicit `idle`, `active`, `complete`, and `error` states driven by a runtime scheduler. |
| `interactive` | Planned | Allow hover, click, replay, inspect, or step actions to trigger local performances. |
| `hybrid` | Shipped, opt-in | Start in ambient motion, then enter the same causal step mode only when the user explicitly starts an explanation. |

## Product Rule

`diagram.html` remains the best high-fidelity output and must not silently
switch scheduling models. Timeline and hybrid require `--runtime-mode`; future
event-driven, state-machine, or interactive behavior must likewise require an
explicit manifest, CLI, or scene-spec option.

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

The opt-in timeline manifest uses:

```json
{
  "mode": "timeline",
  "sequence": "causal-edge-steps",
  "choreographer": {
    "version": "choreographer-v1",
    "steps": [
      {"source": "request", "edge": "request-to-agent", "target": "agent"}
    ]
  }
}
```

Steps preserve authored edge order. Choreographer v1 deliberately does not
infer asynchronous arrival events, camera moves, or node state machines.
