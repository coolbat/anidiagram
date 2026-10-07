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
| `event-driven` | Shipped, opt-in | Trigger node performances when edge signals arrive instead of using fixed global time offsets. |
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


## 2026-10-07 P0 presentation revision

The user authorized implementation of the reviewed October optimization plan.
Ambient/expressive remains the default scheduler/profile; no automatic mode
switch, event-driven scheduler, icon recipe, or stable part ID changed.

HTML now fits and centers on load and reset (explicit readable-label mode keeps
its native-size scroll contract). Its one-shot entrance reveals groups first,
then nodes with at most 50ms stagger, then edges only after both endpoints are
visible. Large diagrams compress the stagger; the entrance finishes within
1060ms. Off/reduced-motion, missing-GSAP, print, and browser exports retain a
complete scene. Timeline mode starts directly in its authored explanation.

Portable SVG is complete without entrance playback. Group haze is retired;
authored border scans use a thin, one-shot stroke, and the runtime title highlight
fully disappears after 800ms. Icon loops and edge packet recipes are unchanged.
These are implementation changes with regression evidence, not a claim of user
visual acceptance. See [implementation evidence](optimization-implementation-2026-10-07.md).


## 2026-10-07 P1–P3 revision

The user explicitly authorized completing P1–P3. Ambient/expressive remains the
initial mode. Event-driven is opt-in (`--runtime-mode event-driven`); diagrams
with more than 12 nodes receive a Readable suggestion and retain user choice.

Default ambient budgets are three primary edges and two icon sites. Secondary
signals and icons play on hover while a resident site is suspended. Explicit
authored budget limits, including public icon showcases, remain effective.
Cycles align to a four-second beat or a whole-number multiple for long routes.
Signals use 180 SVG units per second: synchronous dots with short echoes,
asynchronous dashed signals with a 350ms wait, streams, and red failure bounce.
Arrival feedback lasts 150ms. Event-driven mode then runs the target's existing
icon performance before advancing downstream; cycles receive a bounded traversal.
It is an illustrative schedule derived from authored topology, not a system trace.

Timeline and Hybrid explanation now dim unrelated elements to 25%, focus the
camera, and show the relation label, condition, and supplied source links. Each
step includes a dwell. Left/Right, previous/next, and progress dots navigate;
Pause/Resume include manual-step tweening. Reduced motion and missing GSAP keep
manual text steps without animated camera movement. Reader filters are suspended
while explaining and restored on exit.

`runtime/modules.json` declares assembly order. Icon performances, stage effects,
scheduling, viewer controls, viewport, entrance, edge signals, and explanation
are separate sources assembled into the standalone HTML. Historical public
contracts retain their original bytes in explicit snapshots; this revision does
not rewrite prior release acceptance. Current browser/geometry evidence is in
[the implementation record](optimization-implementation-2026-10-07.md), and does
not substitute for user visual acceptance.
