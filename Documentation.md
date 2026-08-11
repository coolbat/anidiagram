# Current Project Record

## Current Implementation State

- Active milestone: none
- Current status: runnable
- Approved decisions in force: Complete all tasks in the 2026-07-11 Illustrated
  Character motion rollout roadmap; preserve the frozen character timing and
  ambient runtime boundary.
- Changed assumptions: The current dirty feature branch is the only safe write
  surface because the approved baseline is uncommitted.
- Known failures: none recorded for this run.
- Residual risks: overlapping dirty files, generated-gallery churn, optional
  exporter availability, and browser visual balance.

## Scoped Change Ledger

- Character registry/rendering: `src/anidiagram/illustrated_character_icons.py`,
  `src/anidiagram/renderer_illustrated_character.py`.
- Runtime and manifest: `runtime/anidiagram-runtime.js`,
  `runtime/motion-catalog.json`, `src/anidiagram/motion_manifest.py`,
  `src/anidiagram/renderer_html_runtime.py`.
- Motion policies/rendering: `src/anidiagram/schema.py`,
  `src/anidiagram/renderer_svg.py`, `src/anidiagram/quality.py`.
- Tests/verifiers: `tests/test_render_svg.py`,
  `tests/test_showcase_gallery.py`, `scripts/verify_character_motion_rest.mjs`,
  `scripts/verify_character_reduced_motion.mjs`, planned stage-mode verifier.
- Themes/examples/gallery/docs/exporters are in scope only when their matching
  roadmap milestone becomes active.
- All other dirty files are preserved unless a scoped diff proves they are a
  direct generated consequence of the active milestone.

## Per-Attempt Synchronization Record

### Attempt 1

- Milestone: M0
- Changed assumptions: none beyond the approved current-branch exception.
- Command or observation: `PYTHONPATH=src python3 -m unittest discover -s tests && node --check runtime/anidiagram-runtime.js && git diff --check` from the repository root.
- Result: exit 0; 64 tests passed; runtime syntax and diff checks passed.
- Known failure: none.
- Blocker class: none.
- Next action: mechanically release M1 and begin failing stage-motion tests.
- Synced surfaces: `Plan.md=M0 done, M1 runnable`; `agent-loop-state.md=Attempt 1`; `release-evidence.md=E-M0-01`.

### Attempt 2

- Milestone: M1
- Changed assumptions: dynamically removing SVG paths with `particle-glow` can leave black Chromium compositor rectangles; runtime packets now use their white halo and colored core without SVG filters.
- Command or observation: 66-test suite, runtime syntax, character rest/reduced-motion verifiers, stage-mode verifier, and Default/Deep Tech/Teaching Sketch browser screenshots.
- Result: exit 0; Expressive/Readable/Off behavior verified; no duplicate packets or filter artifacts.
- Known failure: expected initial RED failure; F-M1-02 black filter artifact; F-M1-03 malformed one-line screenshot command, corrected immediately.
- Blocker class: repo_fixable; repaired.
- Next action: mechanically release M2.
- Synced surfaces: `Plan.md=M1 done, M2 runnable`; `agent-loop-state.md=Attempt 2`; `release-evidence.md=E-M1-01`.

### Attempt 3

- Milestone: M2
- Changed assumptions: old v2 demos must explicitly render with `semantic-line-v1`; quality-writer scripts required the resolved style argument.
- Command or observation: full tests, showcase build, catalog-manifest audit, three supported-theme browser checks, and five candidate-theme quality/visual checks.
- Result: exit 0; Character v1 and legacy v2 separated; three-theme comparison reviewed; four candidates passed and `aurora-orb` marked Tune.
- Known failure: F-M2-01 exporter signature drift, repaired with a failing regression test.
- Blocker class: repo_fixable; repaired.
- Next action: mechanically release M3.
- Synced surfaces: `Plan.md=M2 done, M3 runnable`; `agent-loop-state.md=Attempt 3`; `release-evidence.md=E-M2-01`.

### Attempt 4

- Milestone: M3
- Changed assumptions: representative examples must reduce authored continuous motion to the declared focused budget, not merely rely on runtime clamping.
- Command or observation: failing gallery regression test after migrating six representative examples to the default Character v1 icon system.
- Result: exit 0; 71 tests; all six representative examples clean; six browser mode checks pass; gallery link audit and diff check pass.
- Known failure: F-M3-01 through F-M3-04 recorded; repo-local failures repaired, headless capture settling risk carried into M4 export validation.
- Blocker class: none after repo-local repair.
- Next action: mechanically release M4 and execute the full export matrix.
- Synced surfaces: `Plan.md=M3 done, M4 runnable`; `agent-loop-state.md=Attempt 4`; `release-evidence.md=E-M3-01`.

### Attempt 5

- Milestone: M4
- Changed assumptions: browser-frame exports must explicitly guard the transient compositor settling boundary identified in F-M3-04.
- Command or observation: M4 selected after the long-horizon checker released its M3 dependency.
- Result: exit 0; 72 tests; all runtime verifiers and showcase build pass; light and dark matrices each write all 10 required formats with 24/24 distinct animated frames.
- Known failure: F-M4-01 command-only working-directory mistake, corrected; F-M3-04 capture-settling risk disproved for written exports by frame/luminance audits.
- Blocker class: none.
- Next action: preserve the branch and present the explicit unstaged handoff.
- Synced surfaces: `Plan.md=M4 done`; `agent-loop-state.md=Attempt 5`; `release-evidence.md=E-M4-01`.

## Explicit Unstaged Handoff

- Branch: `codex/illustrated-character-v1`; normal repository, not a linked worktree.
- Base candidate: `main` merge-base `6253bb9d93975c3e3fa9154038ffaf20eca9cc65`.
- Handoff mode: intentionally unstaged. The approved baseline already contained overlapping uncommitted Character v1 implementation and generated files, so broad staging or retrospective commit splitting would risk absorbing user-owned work.
- Review clusters: runtime/schema/renderers; catalog/themes; representative examples/gallery; exporters/tests/docs/control evidence.
- Intentional generated surfaces: `gallery/`, `examples/showcase/`, and ignored release proof under `outputs/release-evidence/character-v1/`.
- Explicit exclusion: `.playwright-mcp/` remains unrelated and must not be staged as part of this rollout.
- No deploy, publish, push, merge, PR, cleanup, or destructive operation was performed.

## Morning Handoff

- Stop reason and limits reached: none.
- Completed: M0 / E-M0-01; M1 / E-M1-01; M2 / E-M2-01; M3 / E-M3-01; M4 / E-M4-01.
- Blocked: none.
- Needs decision: none.
- Evidence: E-M0-01; E-M1-01; E-M2-01; E-M3-01; E-M4-01; browser proof under `outputs/`.
- Known failures: F-M1-01 through F-M1-03 and F-M2-01, repaired.
- Changed assumptions: current branch replaces the normally required clean
  worktree because the approved implementation baseline is uncommitted.
- Risks: preserve unrelated changes; do not publish or broadly stage.
- Next runnable: none; implementation complete and preserved for human review.
