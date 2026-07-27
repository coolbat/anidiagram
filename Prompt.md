# Diagram Core v1 Full Catalog Goal Contract

## Background

The 56-id `diagram-core-v1` catalog, asset/manifest contracts, four benchmark
SVGs, and one expressive `showcase` Presentation Profile already exist on the
isolated `codex/diagram-core-v1-phase-0-1` worktree. Coolbat approved the visual
and motion direction for Agent, Database, API, and Server on 2026-07-17 and
requested that all remaining icons be implemented in batches, internally tested
and accepted, then presented once for final human visual acceptance.

## Goal

Implement the remaining 52 Diagram Core icons as canonical, theme-aware,
accessible SVG assets with matching Icon Asset Manifests and differentiated
showcase performances. Execute the approved compatibility batch first, then six
seven-icon expansion batches. Produce deterministic static and live review
surfaces, pass every batch gate and the final full regression gate, complete an
independent review, and only then request coolbat's final visual acceptance.

## Non-goals

- Do not implement `idle / active / processing / success / warning / error`.
- Do not model `showcase` as a State or Domain Action.
- Do not switch `DEFAULT_ICON_SYSTEM` from `illustrated-character-v1`.
- Do not promote any new asset from `visual-review` to `approved` before the
  user's final visual acceptance.
- Do not add React/SDK components, third-party icon geometry, a second runtime,
  or a second hand-maintained geometry source.
- Do not deploy, push, merge, open a pull request, or publish.

## Deliverables

- Exactly 56 canonical SVGs and 56 matching manifests under
  `assets/diagram-core/`.
- Catalog entries with implemented prototypes, parts, actions, revisions, and
  `visual-review` status while semantic states remain empty.
- One maintainable data-driven showcase contract for new icons while preserving
  the four approved benchmark performances unchanged.
- Batch contact sheets and a final categorized 56-icon live showcase.
- Static safety, manifest parity, part identity, repeated-instance, recognition,
  motion amplitude, reset, reduced-motion, no-GSAP, clipping, and performance
  evidence.
- Synchronized plan, documentation, loop state, and release evidence.

## Constraints

- Canonical SVG plus Icon Asset Manifest remain the asset source of truth.
- Every SVG uses `viewBox="0 0 96 96"`, semantic `data-part` groups, repository
  tokens with fallbacks, no scripts/animation/raster/external resources, and no
  connection anchors.
- Preserve the approved family language: dark rounded outline, warm surface,
  purple primary accent, teal secondary accent, clear silhouette, restrained
  internal detail, and meaningful 48 px recognition.
- Use the shared `file-shell` skeleton for the file/content family without
  making the exported SVGs dependent on another asset.
- Each showcase performance moves only meaningful public Parts, returns to the
  authored rest pose, remains unclipped, and has a scene-controlled quiet gap.
- Use test-driven development for behavior changes and verify each batch before
  selecting the next.
- Preserve all unrelated user changes and the current four-file showcase diff.

## Done Conditions

- Catalog/manifests/assets report 56/56 implemented visual-review icons and zero
  semantic states.
- Compatibility batch and all six expansion batches have fresh passing S0/S1
  evidence and independent review findings are closed.
- The final 56-icon gallery is deterministic, recognizable in static contexts,
  network-free, and functional with Showcase/Pause/Replay/Off controls.
- Full unittest, asset validator, JavaScript syntax, browser motion, fallback,
  repeated-instance, performance, generated-artifact, and `git diff --check`
  gates pass from the final source state.
- No default-system switch, approval promotion, delivery, or cleanup occurs.

## Human-owned Decisions

- Final visual acceptance of the 52 new icons and their showcase performances.
- Promotion from `visual-review` to `approved` and any default-system switch.
- Phase 2 lifecycle/state semantics and all external delivery actions.

## Forbidden Actions

- Do not copy third-party icon assets or geometry.
- Do not infer approval from automated tests.
- Do not weaken validators, lower quality thresholds, or hide failed batches.
- Do not reset, clean, discard, broadly stage, or delete the isolated worktree.
