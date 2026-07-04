# Changelog

## 2026-07-04

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
