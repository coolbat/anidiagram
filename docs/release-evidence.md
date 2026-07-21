# Release Evidence

## Evidence Ledger

### Evidence E-M0-01

- Milestone: M0
- Attempt number: 1
- Recorded at: 2026-07-13 11:27:08 CST
- Changed assumptions: current dirty feature branch is the approved single writer.
- Command or observation: `PYTHONPATH=src python3 -m unittest discover -s tests && node --check runtime/anidiagram-runtime.js && git diff --check` in `/Users/coolbat/anidiagram`.
- Result: exit 0; 64 tests passed; runtime syntax and diff checks passed.
- Artifact or output: terminal output; scoped ledger in `Documentation.md`.
- Known failure: none.
- Blocker class: none.
- Verdict: pass.
- Residual risk: 107 dirty status entries require path-scoped editing and review.
- Next action: execute M1 with test-first stage-motion changes.
- Synchronized status: `Plan.md=M0 done, M1 runnable`; `Documentation.md=Attempt 1`; `agent-loop-state.md=2026-07-13 11:27:08 CST`.

### Evidence E-M1-01

- Milestone: M1
- Attempt number: 2
- Recorded at: 2026-07-13 11:36:12 CST
- Changed assumptions: dynamic SVG particle filters removed after Chromium compositor evidence.
- Command or observation: M1 validation command in `/Users/coolbat/anidiagram`; browser screenshots for Default, Deep Tech, Teaching Sketch, and fixed Readable mode.
- Result: exit 0; 66 tests; character rest 13/13; reduced motion 13/13 and 8/8; stage modes verified with 8 characters, 7 edges, 2 readable packets.
- Artifact or output: `outputs/illustrated-character-v1-flow/checkpoint-a-expressive.png`, `checkpoint-a-readable-fixed.png`, `outputs/theme-deep-tech-checkpoint-a.png`, `outputs/theme-teaching-sketch-checkpoint-a.png`.
- Known failure: F-M1-01, F-M1-02, F-M1-03 repaired.
- Blocker class: none after repo-local repair.
- Verdict: pass.
- Residual risk: theme/gallery rollout remains unverified until M2.
- Next action: execute M2.
- Synchronized status: `Plan.md=M1 done, M2 runnable`; `Documentation.md=Attempt 2`; `agent-loop-state.md=2026-07-13 11:36:12 CST`.

### Evidence E-M2-01

- Milestone: M2
- Attempt number: 3
- Recorded at: 2026-07-13 11:46:34 CST
- Changed assumptions: legacy demos explicitly use `semantic-line-v1`; quality writers pass resolved styles.
- Command or observation: M2 gate, 25-demo manifest audit, 3 supported-theme stage/reduced checks, 5 candidate quality/visual reviews.
- Result: exit 0; 69 tests; showcase reports 25 performances and 3 character themes; all 27 demo quality reports clean.
- Artifact or output: `gallery/runtime-motion.html`, `gallery/character-themes.html`, `outputs/character-theme-comparison-page.png`, `docs/illustrated-character-theme-compatibility.md`.
- Known failure: F-M2-01 repaired.
- Blocker class: none after repo-local repair.
- Verdict: pass.
- Residual risk: representative examples and full gallery migration remain M3.
- Next action: execute M3.
- Synchronized status: `Plan.md=M2 done, M3 runnable`; `Documentation.md=Attempt 3`; `agent-loop-state.md=2026-07-13 11:46:34 CST`.

### Evidence E-M3-01

- Milestone: M3
- Attempt number: 4
- Recorded at: 2026-07-13 12:02:32 CST
- Changed assumptions: authored representative motion fits its focused budget; runtime clamping is not treated as clean source quality.
- Command or observation: showcase rebuild, 71-test suite, JavaScript syntax checks, six representative browser mode checks, gallery local-link audit, and scoped generated-diff review.
- Result: exit 0; all six representative examples have clean quality reports; gallery reports 12 styles, 14 layouts, 25 performances, and 3 character themes.
- Artifact or output: `outputs/representative-character-examples/`, `outputs/loop-engineering-architecture/`, `gallery/showcase_manifest.json`, and rebuilt `gallery/` surfaces.
- Known failure: F-M3-01 through F-M3-04 recorded; repo-local failures repaired.
- Blocker class: none after repo-local repair.
- Verdict: pass.
- Residual risk: headless Chromium can capture a transient unpainted compositor frame immediately after GSAP cleanup; M4 must verify captured animated frames and settling behavior.
- Next action: execute M4 export matrix, documentation synchronization, and final verification.
- Synchronized status: `Plan.md=M3 done, M4 runnable`; `Documentation.md=Attempt 4`; `agent-loop-state.md=2026-07-13 12:02:32 CST`.

### Evidence E-M4-01

- Milestone: M4
- Attempt number: 5
- Recorded at: 2026-07-13 12:11:50 CST
- Changed assumptions: none; the F-M3-04 capture-settling risk was exercised against real browser-owned exports.
- Command or observation: final 72-test suite; runtime syntax; 13-icon rest; 13-icon and 8-icon reduced motion; stage modes; showcase rebuild; light/dark export and frame audits; diff and contract checks.
- Result: exit 0; each theme wrote SVG, HTML, PNG, WebP, GIF, APNG, MP4, PDF, frame-based Lottie, and clean quality output. GIF/WebP/APNG, MP4, and Lottie each contain 24 distinct frames at 12 FPS.
- Artifact or output: `outputs/release-evidence/character-v1/light/result.json`, `outputs/release-evidence/character-v1/dark/result.json`, their sibling artifacts, `gallery/character-themes.html`, and the canonical representative examples.
- Known failure: F-M4-01 corrected; no remaining blocker.
- Blocker class: none.
- Verdict: pass.
- Residual risk: the runtime still loads GSAP from a CDN; future causal timeline/choreographer, event-driven, state-machine, interactive, and hybrid modes remain unshipped roadmap items.
- Next action: human review of the explicit unstaged handoff on `codex/illustrated-character-v1`.
- Synchronized status: `Plan.md=M4 done`; `Documentation.md=Attempt 5`; `agent-loop-state.md=2026-07-13 12:11:50 CST`.

## Current Composition and Icon-System Closeout

This record closes the current composition-v1 and public icon-system stage. It
records the exact uncommitted worktree that was independently verified; it does
not claim that the changes have already been committed or published.

### Evidence E-COMP-01 — passed

- Milestone: composition-v1 defaults and Illustrated 2.3.0 public v4 closeout.
- Attempt number: 1 final integrated run.
- Recorded at: 2026-07-20 23:14:51 CST.
- Source state: branch `main`, base commit
  `017f635fc49a3ca554acf18475dff13f2e5a2347`; 27 task-scoped modified or
  untracked paths, no commit created by this closeout.
- Changed assumptions: DiagramPlan v0.2 / DiagramScript v0.4 defaults are
  `diagram-core-v1` plus `showcase-v1`; DiagramScript v0.1-v0.3 and legacy style
  omission retain `illustrated-character-v1` plus `expressive`; direct v0.4
  without `composition_policy` uses Diagram Core plus `expressive` for manual
  authoring compatibility; `illustrated` 2.3.0 is an explicit non-default
  system with sixteen public v4 performances.
- Resolved composition omission: icon system `diagram-core-v1/default`, style
  `minimal-light/fallback`, layout `layered/fallback`, motion
  `showcase-v1/default`. The compiled budget is
  `motion_policy.profile=unrestricted`, `motion_area=unrestricted`, and
  `pulse_mode=all`.
- Commands executed:
  - `PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --strict --json`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `node --check runtime/anidiagram-runtime.js`
  - `node scripts/verify_character_motion_rest.mjs outputs/illustrated-2.3-showcase/illustrated-2.3-showcase.html 16 illustrated`
  - `node scripts/verify_character_reduced_motion.mjs outputs/illustrated-2.3-showcase/illustrated-2.3-showcase.html 16 illustrated`
  - `node scripts/verify_stage_motion_modes.mjs outputs/illustrated-2.3-showcase/illustrated-2.3-showcase.html`
  - `node scripts/verify_stage_motion_modes.mjs outputs/composition-v1-edge-stage/production-request-path.html`
  - `PYTHONPATH=src python3 scripts/build_icon_system_release_evidence.py`
  - `PYTHONPATH=src python3 scripts/build_icon_system_release_evidence.py --verify`
  - `git diff --check` and an immutable-archive digest check.
- Result: 176/176 Python tests passed; all 14 layouts produced distinct clean
  geometry; Diagram Core strict reported 56 catalog entries, 56 SVGs, 56
  manifests, 56 approved, 4 contrast checks, zero planned/visual-review,
  zero warnings, and zero errors.
- Public coverage: Gallery and runtime report Diagram Core 56/56 and Illustrated
  2.3.0 16/16, each with zero quality issues. Illustrated rest and reduced
  motion returned 16/16; its stage modes returned characters=16, edges=0. The
  separate composition-v1 request-path proof returned characters=4, edges=3,
  readable=2, so data-flow mode switching has nonzero edge coverage.
- Export evidence: two systems x ten formats at browser 24 FPS, 108 frames, and
  2x scale. GIF, WebP, APNG, MP4, and Lottie each contained 108 distinct whole
  frames for both systems. Exact catalog/manifest identity passed. Per-icon
  Lottie crop audit reported a minimum of 3 distinct states for Diagram Core
  and 45 for Illustrated; issues were empty.
- Artifact or output:
  `outputs/release-evidence/icon-systems/public-icon-system-export-evidence.json`
  (13,238 bytes, SHA-256
  `7c4aa14a0fe2eefc10dcdf440f5d26449132936495d544887c8a72d48fa70ebc`),
  `gallery/icon-systems/index.html`,
  `outputs/composition-v1-edge-stage/production-request-path.html`, and browser
  review captures under `outputs/playwright/`.
- Browser proof: public index plus both release runtime pages loaded over HTTP;
  Diagram Core exposed all 56 accessible icon labels, Illustrated exposed all
  16, toolbar mode/zoom controls worked, and all checked consoles contained
  zero warnings and zero errors.
- Immutable authority digests remained unchanged:
  Diagram Core v1 release
  `5a594cbb155a421a7f820d594c52abeee1ecad9aa8aef6c8212f2328e0d9005e`;
  Illustrated 2.3 release
  `54851a06e6cf446c058d47b5aac563d399134bfc9e25cb409ba51f82e2cc8aed`;
  Illustrated acceptance
  `86b255c6a0b9c6c41c17811eecfbd1fc3c0725ff092c7c7786769d5f2ddc05f5`.
- Known failure: the first ad hoc 14-layout audit passed style id
  `minimal-light` where `load_style` required `styles/minimal-light.json`; the
  corrected command passed all 14 layouts. No product code was changed for
  this command-only error.
- Blocker class: none.
- Verdict: passed; no implementation or validation stage remains open in the
  current scope.
- Residual risk: the large binary export matrix is intentionally ignored local
  evidence rather than a tracked release payload. The tracked builder and
  evidence hashes make it reproducible, but distribution or CI retention is a
  separate release operation.
- Next action: commit and push this verified worktree only when explicitly
  requested.

Current icon-system status and immutable boundaries are indexed in
[`icon-system-release-status.md`](./icon-system-release-status.md).

## Failure History

### Failure F-M1-01

- Milestone: M1
- Attempt number: 2
- Command or observation: focused stage runtime contract test.
- Result: expected RED failure.
- Error: missing `EDGE_PACKET_COUNT` and mode contract.
- Hypothesis: current runtime still used class-only Readable and multi-packet loops.
- Repair attempted: implemented explicit stage/icon timeline stores and mode rebuilding.
- Blocker class: repo_fixable.
- Affected acceptance: Tasks 2-5.
- Resume condition: focused and full tests pass.

### Failure F-M1-02

- Milestone: M1
- Attempt number: 2
- Command or observation: browser screenshot after Expressive to Readable switch.
- Result: visual failure.
- Error: black rectangular compositor artifacts over the SVG stage.
- Hypothesis: removed/recreated paths with `particle-glow` filters left stale Chromium layers.
- Repair attempted: added failing source regression and removed filters from runtime edge paths.
- Blocker class: repo_fixable.
- Affected acceptance: readable browser quality and stable mode switching.
- Resume condition: fixed screenshot is visually clean.

### Failure F-M1-03

- Milestone: M1
- Attempt number: 2
- Command or observation: one-line Node screenshot command.
- Result: exit 1.
- Error: missing closing brace in `newPage` options caused a JavaScript syntax error.
- Hypothesis: command construction typo, unrelated to product code.
- Repair attempted: corrected command and reran successfully.
- Blocker class: repo_fixable.
- Affected acceptance: screenshot evidence only.
- Resume condition: screenshot command exits 0.

### Failure F-M2-01

- Milestone: M2
- Attempt number: 3
- Command or observation: `PYTHONPATH=src python3 scripts/build_showcase.py --quality`.
- Result: exit 1.
- Error: `write_quality()` missing the resolved style argument after exporter API evolution.
- Hypothesis: gallery scripts retained the old two-argument call signature.
- Repair attempted: added failing source regression and updated all gallery/batch quality writers to pass style.
- Blocker class: repo_fixable.
- Affected acceptance: deterministic clean-quality gallery generation.
- Resume condition: showcase build and gallery tests pass.

### Failure F-M3-01

- Milestone: M3
- Attempt number: 4
- Command or observation: representative-example gallery regression test.
- Result: expected RED failure after initial migration.
- Error: four examples declared 5-6 active particle edges above their focused limits.
- Hypothesis: relying on renderer clamping leaves noisy authored intent and correctly triggers quality warnings.
- Repair attempted: retained four primary animated paths and made non-key branches intentionally static.
- Blocker class: repo_fixable.
- Affected acceptance: clean representative quality and focused motion budgets.
- Resume condition: all six representative summaries report zero errors and warnings.

### Failure F-M3-02

- Milestone: M3
- Attempt number: 4
- Command or observation: one focused unittest command.
- Result: exit 1.
- Error: test class was typed as `ShowcaseGalleryTests` instead of `ShowcaseGalleryTest`.
- Hypothesis: command-only class-name typo, unrelated to product code.
- Repair attempted: corrected the class name and reran successfully.
- Blocker class: repo_fixable.
- Affected acceptance: focused verification only.
- Resume condition: focused and module tests pass.

### Failure F-M3-03

- Milestone: M3
- Attempt number: 4
- Command or observation: first full test run after representative migration.
- Result: 3 failures.
- Error: assertions retained the old 12-edge budget, single-line `Planner Agent` serialization, and unclamped legacy database motion expectation.
- Hypothesis: fixtures changed intentionally while their behavioral assertions remained on the pre-migration baseline.
- Repair attempted: updated assertions to the focused budget, split SVG tspans, and policy-clamped legacy fallback behavior.
- Blocker class: repo_fixable.
- Affected acceptance: full-suite regression gate.
- Resume condition: all 71 tests pass.

### Failure F-M3-04

- Milestone: M3
- Attempt number: 4
- Command or observation: Playwright screenshots during active animation and immediately after switching Off.
- Result: intermittent transient black/unpainted SVG regions; DOM state, computed visibility, and canonical rest assertions remained correct.
- Error: screenshot could race Chromium SVG compositor invalidation before the next stable paint.
- Hypothesis: immediate headless capture after nested SVG transform cleanup can precede compositor repaint; waiting for settling produced clean screenshots without source mutation.
- Repair attempted: no product workaround applied in M3; evidence isolated the capture timing boundary for M4 exporter validation.
- Blocker class: verification_environment.
- Affected acceptance: browser-frame animated export reliability, owned by Task 13.
- Resume condition: M4 export matrix proves nonempty, visibly different, non-corrupt frames for light and dark themes.

### Failure F-M4-01

- Milestone: M4
- Attempt number: 5
- Command or observation: git environment and status audit.
- Result: command-only failure.
- Error: sequential `cd` commands left the shell inside `.git`, so later status and roadmap checks reported “must be run in a work tree” and a missing relative path.
- Hypothesis: the diagnostic command changed its own working directory; repository state was unaffected.
- Repair attempted: isolated each directory lookup in a subshell and reran the audit successfully.
- Blocker class: repo_fixable.
- Affected acceptance: handoff diagnostics only.
- Resume condition: git directory, branch, merge-base, status counts, and roadmap audit print successfully.

## Morning Handoff Evidence

- Stop reason and limits reached: none.
- Completed: M0 / E-M0-01; M1 / E-M1-01; M2 / E-M2-01; M3 / E-M3-01; M4 / E-M4-01.
- Blocked: none.
- Needs decision: none.
- Evidence: E-M0-01; E-M1-01; E-M2-01; E-M3-01; E-M4-01.
- Known failures: F-M1-01 through F-M4-01 recorded; all repaired or resolved by final evidence.
- Changed assumptions: current dirty feature branch is the approved single writer; dynamic SVG packet filters removed; legacy demo systems explicit.
- Risks: overlapping dirty files; optional export tooling; human-visible motion
  balance.
- Next runnable: none; human review is next.
