# Changelog

## 0.2.0 - 2026-07-29

- Added a standalone wheel build that packages runtime, schema, style, and icon
  resources; CI smoke-renders the installed wheel outside the source checkout
  on Python 3.9, 3.11, and 3.14.
- Added semantically equivalent Chinese and English brief planning with
  localized labels and descriptions.
- Added shared CJK-aware text layout for rendering and quality validation,
  centered caption fitting, improved icon/text space allocation, and browser
  checks for node-surface containment and edge-label collisions.
- Added exact GSAP dependency modes: pinned `cdn`, user-supplied `inline`, and
  dependency-free static `none`. GSAP remains outside the Python wheel.
- Added localized, keyboard-focusable runtime controls, live status, visible
  dependency warnings, and accessible stage/toolbar semantics.
- Added opt-in Choreographer v1 `timeline` and `hybrid` modes with causal
  source/edge/target steps and start/previous/next controls. Ambient remains the
  compatibility default and the frozen legacy runtime files remain unchanged.
- Reduced the eight committed README animated WebPs from about 15 MiB to about
  3 MiB while preserving 24-frame motion, and added repository asset budgets.
- Added a safe dry-run output-pruning helper that preserves release evidence
  unless an explicit bounded deletion is requested.
- Added 281-test local coverage plus browser, packaging, asset-budget, and
  Choreographer CI gates.

## 2026-07-06

- Added the optional `html-runtime` export target for high-fidelity browser
  animation while preserving the default SVG/SMIL and HTML viewer outputs.
- Added `--export-renderer browser` so PNG, GIF, PDF, WebP, MP4, APNG, and
  frame-based Lottie can be captured from the high-fidelity HTML runtime
  instead of the lightweight Python preview renderer.
- Added Motion Manifest generation so the HTML runtime selects stable SVG icon
  parts instead of guessing DOM structure from classes.
- Added stable semantic icon part IDs and runtime-only parts for the first eight
  v2 icon performances: `agent-think-act-v2`, `api-request-response-v2`,
  `search-discover-v2`, `database-write-v2`, `memory-commit-v2`,
  `tool-run-v2`, `token-intent-v2`, and `output-reveal-v2`.
- Refined semantic icon styling with softer low-saturation fills, stronger
  `agent` and `api` semantics, and dedicated static icons for `memory`, `tool`,
  `token`, and `output` instead of the generic fallback.
- Refined the `agent` icon into an asymmetric brain/head circuit and updated
  `agent-think-act-v2` so lines draw outward before node dots grow in.
- Added `runtime/anidiagram-runtime.js` with GSAP timeline performances plus
  pause, resume, restart, reduced-motion, zoom, pan, and SVG download handling.
- Added `examples/high-fidelity-runtime.diagram.json` and regression tests for
  html-runtime CLI output, valid manifests, matching selectors, and default SVG
  compatibility.
- Added a clean-room AniDiagram system architecture DiagramScript example and
  rendered it through the project CLI for SVG, HTML, and quality verification.
- Refined the system architecture example with a calmer motion profile, fewer
  active edge effects, and reduced visual clutter.
- Added DiagramScript v0.3 `motion_policy` budgets for active flow edges,
  particle edges, per-edge particle/trail density, pulse nodes, and scanning
  group borders.
- Added renderer-side motion clamping so over-budget edges/nodes/groups degrade
  into draw, fade, or soft-reveal behavior instead of all animating at once.
- Added quality-report `motion_overload` warnings for configured effects that
  exceed the selected motion policy.
- Updated the brief planner to emit focused motion by default: a few animated
  main-path edges, single-particle arrows, fade nodes, and calm groups.
- Added runtime-loop motion primitives: `signal-dot`, `signal-arrow`,
  `dash-flow`, node `icon-breathe`, title `breathe`, and the
  `readable-runtime` motion policy profile.
- Added optional `motion_policy.motion_area` support, starting with micro-scale
  particle sizing for low-area runtime motion.
- Added a `runtime-loop-motion` example using the existing minimal-light style
  to validate motion rhythm independent of visual style changes.
- Added `icon-semantic` node motion with `icon_motion` hints so semantic icons
  can use local micro-motions such as database writes, file-line reveals,
  API pings, search sweeps, shield checks, agent orbits, tool taps, and output
  checks without moving the whole node frame.
- Added a `semantic-icon-motion` example to validate icon-specific motion
  against the readable runtime motion policy.
- Refined the `file-lines` icon motion with contrast-aware page fill, a
  lower-left page entrance, slight scale overshoot, an animated folded corner,
  and faster content-line reveal timing.
- Increased the `file-lines` playback pace so the page entrance, folded-corner
  motion, and content-line reveal read more immediately.
- Amplified semantic icon motion so icon-local actions use larger sizes,
  stronger translations, wider sweeps, larger ping rings, bolder checkmarks,
  and more visible tool/folder/orbit movement while node frames remain static.
- Completed the semantic icon detail pass with contrast-aware icon fills and
  icon-local database top bounce/layer flashes, folder file-line reveals,
  cloud transfer dots, search light points, shield protection pulses, agent
  core glow, tool sparks, output line reveals, and token ticks.
- Increased light-theme semantic icon fill contrast so large SVG previews keep
  the same filled-icon readability that thumbnails implied.
- Fixed semantic icon fill rendering by removing the global `fill: none` CSS
  override and marking filled icon bodies with `icon-filled`.

## 2026-07-05

- Added DiagramScript v0.3 support for structured motion effect objects.
- Added the first motion effect registry layer for edge, node, group, and title
  channels while preserving legacy string motion values.
- Added semantic node icons and per-element `effect` overrides for nodes, edges,
  and groups.
- Added edge presets for dynamic dashes, flow dots, flow arrows, ghost flow, and
  glow lines.
- Added group border-scan motion and title handwrite/highlight reveal.
- Added the `teaching` motion profile and `sketch-board` style profile.
- Added the clean-room `teaching-transformer` example and v0.3 schema file.
- Added a motion effects feature plan covering edge, node, group, title, and
  semantic icon effect presets.
- Documented clean-room compatibility rules for richer teaching-diagram motion
  targets, including style-token based motion and raster/video fallbacks.
- Linked the motion effects plan from README and DiagramScript docs.
- Expanded the GitHub README with complete style, layout preset, routing, and
  motion effect reference tables.
- Added a generated style showcase with one clean-room DiagramScript case,
  SVG preview, HTML viewer, and quality report for every bundled visual style.
- Added an independent Simplified Chinese README and linked it from the main
  README homepage.
- Added DiagramPlan v0.1 as the brief/LLM-to-layout contract.
- Added a deterministic brief planner and `explainer-board` freeform compiler
  for complex diagrams that should not be forced into a fixed preset.
- Added CLI support for `--brief`, `--text`, `--plan-out`, and `--spec-out`.
- Added DiagramScript v0.3 `node.shape` support with `rect` and `decision`
  nodes across SVG and raster rendering.
- Added prompt-to-diagram flow documentation and a clean-room loop engineering
  brief example.

## 2026-07-04

- Fixed raster animation exports so GIF, WebP, APNG, and MP4 frames render visible moving edge particles instead of static duplicate frames.
- Added AniDiagram-native motion profiles inspired by timeline/stagger animation systems: `off`, `subtle`, `normal`, and `expressive`.
- Added scene-level motion controls for sequencing, easing labels, stagger, duration scale, intensity, node motion, edge motion, group motion, and reduced-motion policy.
- Added HTML viewer controls for full/subtle/off motion intensity.
- Added the `aurora-orb` style profile with soft gradient node fills, clipped color bands, grain texture, and low-contrast canvas treatment.
- Improved SVG/HTML motion with staggered node entry, glow breathing, burst rings, draw-on edges, flow dashes, multi-particle edge motion, animated group boundaries, restart controls, and reduced-motion handling.
- Added clean-room motion research notes based on open-source animation libraries without importing third-party code or assets.
- Added DiagramScript v0.2, JSON schema files, and dedicated schema documentation.
- Added route-aware edges, step badges, stricter roles, preset metadata, and canvas bounds validation.
- Added exporters for HTML, PNG, GIF, PDF, WebP, MP4, APNG, Lottie, and quality reports.
- Added HTML viewer controls for play/pause, zoom, drag pan, reset, and SVG download.
- Added quality checks for node bounds, overlaps, text fit, and explicit edge path collisions.
- Added clean-room preset compilers for 14 diagram types.
- Added seven more style profiles, style validation, and a style catalog.
- Added a `$anidiagram` Skill entrypoint, batch gallery generator, GitHub Actions CI, and optional raster packaging metadata.
- Added a committed preset gallery and README case showcase.
- Added a typed internal Scene IR for `Scene`, `Node`, `Edge`, `Group`, `Style`, and `Motion`.
- Added DiagramScript v0.1 validation with structured path-level error reports.
- Updated the CLI to emit structured success and validation-error result JSON.
- Added fixture-based renderer stability and validation tests.
- Renamed the project from `animated-diagram` to `AniDiagram`.
- Renamed the repository directory to `/Users/coolbat/anidiagram`, the Python package to `anidiagram`, and the CLI command to `anidiagram`.
- Created a new clean-room `AniDiagram` project outside the existing fork.
- Added an independent JSON scene model named DiagramScript.
- Added a standard-library Python renderer that outputs animated SVG and a self-contained HTML viewer.
- Added style profiles, example specs, tests, MIT license, and reference attribution docs.
