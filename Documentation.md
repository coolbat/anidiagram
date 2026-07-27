# Diagram Core v1 Full Catalog Project Record

## Current Implementation State

- Active milestone: none; M8 Search circular-wobble revision is done
- Current status: awaiting human visual acceptance
- Branch/worktree: `codex/diagram-core-v1-phase-0-1` at
  `/Users/coolbat/anidiagram/.worktrees/diagram-core-v1-phase-0-1`
- Delivery: local-only; no stage, commit, push, PR, merge, or deploy authorized.
- Approved decisions: four benchmark visuals and showcase direction are the
  family baseline; implement the remaining 52 in batches and request user review
  only after internal gates all pass.
- Current asset state: 56 catalog ids; 56 canonical SVGs/manifests; 56 showcase
  presentations; 0 planned entries. Search now keeps one rigid orientation and
  traces a small clockwise circle around the authored lens-center position
  before the scan and dot pulses; geometry and semantic states remain unchanged.
- New asset lifecycle: `visual-review` with empty states until human approval.
- Known failures: F-M0-01, F-M0-02, F-M1-01 through F-M1-04, F-M2-01 through
  F-M2-03, F-M3-01 through F-M3-02, F-M4-01, and F-M5-01 are recorded and
  repaired; F-M6-01, F-M6-02, F-M7-01 through F-M7-03, F-M8-01, and F-M8-02
  are repaired; no repository blocker remains.

## Frozen Batch Strategy

The PRD's approved scaling path is preserved: implement the 10 legacy
compatibility semantics as two five-icon slices, then complete the remaining 42
as six batches of seven. The exact inventory is frozen in Plan.md and totals 52
without overlap. PRD and Catalog ids, order, categories, and semantic kinds are
identical; the implementation must atomically replace each planned placeholder
with its prototype, parts, actions, revision, SVG, manifest, and presentation.

## Implementation Direction

- Canonical SVG and manifest remain the single asset truth.
- Reuse visual prototypes and tokens, not external geometry or hidden fallbacks.
- Preserve the four approved hand-tuned benchmark performances.
- New showcase motion is data-driven while retaining icon-specific Part
  selection, allowlisted choreography, fail-closed target resolution, and the
  four approved hand-tuned benchmark performances.
- Generate batch review evidence and a final categorized 56-icon live gallery.

## Per-Attempt Synchronization

### Attempt 1

- Milestone: M0
- Observation: long-horizon checker reported eight missing execution-policy
  fields because root control files still belonged to the old rollout.
- Result: task contract replaced with the current Diagram Core full-catalog goal,
  10-plus-42 milestone queue, existing isolated worktree, local-only delivery,
  and explicit S0/S1 commands.
- Failure: F-M0-01; class repo_fixable.
- Next action: rerun checker, verify exact inventory, and execute fresh baseline.

## Residual Risks

- Visual sameness across 52 new icons if structural prototypes are not kept
  distinct.
- Hand-authored SVG churn and performance pressure when 56 timelines coexist.
- Tool's neutral mechanism avoids the rejected cat-ear silhouette but may still
  read as an instrument or camera at first glance; preserve its pipeline-tool
  semantics and reassess it in the final 56-icon family context.
- Each future seven-icon batch must exercise the dynamic 84-cell static review
  path as well as the live showcase before milestone closure.
- Automated recognition checks cannot replace the user's final visual judgment.

### Attempt 2

- Milestone: M0
- Command: full M0 validation command from Plan.md.
- Result: 306/306 tests and the four-icon browser verifier passed; `git diff
  --check` returned 2 for one trailing blank line in each reconciled control
  file.
- Failure: F-M0-02; class repo_fixable.
- Repair: remove only the reported trailing blank lines.
- Next action: rerun the entire M0 validation command from the corrected tree.

### Attempt 3

- Milestone: M0
- Commands: full M0 validation from Plan.md, followed by a final task checker,
  diff check, branch name, and worktree identity audit.
- Result: pass; 306 tests, runtime syntax, the approved four-icon browser
  verifier, checker, isolated worktree, and diff checks all exited 0.
- Evidence: E-M0-01.
- Next action: release M1 and begin the first five-icon compatibility slice with
  a failing batch contract test.

### Attempt 4

- Milestone: M1.
- Commands: exact M1 Validation command from Plan.md; full unittest discovery;
  deterministic generation and capture for both five-icon static matrices;
  independent implementation and final-control review.
- Result: pass; both compatibility slices are complete as visual-review assets,
  with empty states and no default-renderer promotion. Exact gate 152/152, full
  suite 328/328, 14/14 browser timelines, clean reset/reduced/no-GSAP/repeated
  instance behavior, and 16.60 ms 20-icon p95.
- Evidence: E-M1-01; static artifacts
  `build/diagram-core/m1-compat-a.final.*` and
  `build/diagram-core/m1-compat-b.*` each contain 60 reviewed cells.
- Repairs: bounded motion endpoints; redesigned Tool and Operator identity;
  same-root selector isolation and dangerous-key/duplicate-target rejection;
  corrected the validation mode and exact slice-test gate.
- Next action: select M2 and begin its seven actor/model icons with a failing
  batch contract test.

### Attempt 5

- Milestone: M2.
- Observation: M1 independent closeout reports P0/P1/P2 at zero; M2 is the only
  mechanically runnable milestone.
- Result: pass. Seven distinct non-text silhouettes and authored-rest
  performances are implemented as visual-review assets with empty states; Agent
  benchmark hashes remain stable. Exact gate 147/147, full suite 334/334,
  browser 21/21 with 27.00 ms p95, and the 84-cell capture is deterministic with
  zero requests and zero animations.
- Visual review: P0/P1/P2 at zero. LLM's label-free reading remains an accepted
  P3 abstraction as language/context bands; it is not interchangeable with AI
  Model, Memory, or Token.
- Evidence: E-M2-01 and `build/diagram-core/m2-actor-model.png`.
- Next action: release M3 and begin its reasoning/knowledge batch with a failing
  seven-icon contract.

### Attempt 6

- Milestone: M3.
- Observation: M2 control and visual review closed; M3 is the sole runnable
  milestone.
- Result: pass. The seven PRD silhouettes and authored-rest performances are
  visual-review with empty states; Database hashes remain stable. Exact gate
  147/147, full suite 340/340, browser 28/28 at 26.80 ms p95, and deterministic
  84-cell capture all pass.
- Visual review: P0/P1/P2 at zero. Vector Database has a non-blocking P3 rack
  association at 48 px, but points plus scanner distinguish it and avoid the
  more serious Database-cylinder collision.
- Evidence: E-M3-01 and `build/diagram-core/m3-reasoning-knowledge.png`.
- Next action: release M4 and begin the content/file batch with a failing
  seven-icon contract.

### Attempt 7

- Milestone: M4.
- Observation: M3 closed; M4 is the sole runnable milestone.
- Result: pass. Seven visual-review assets share a coherent folded-file family
  without text-dependent identity; File remains stable. Exact gate 147/147,
  full 346/346, browser 35/35 at 27.10 ms p95, and deterministic 84-cell pass.
- Visual review: the initial Document Store printer reading was repaired with a
  straight cabinet, labeled drawer/handle, and fanned inserted cards. Final
  P0/P1/P2 are zero. PDF/document, Code/VCS, and isolated office-equipment
  associations remain non-blocking P3 observations.
- Evidence: E-M4-01 and `build/diagram-core/m4-content-file.png`.
- Next action: release M5 and begin its network/runtime batch with a failing
  seven-icon contract.

### Attempt 8

- Milestone: M5.
- Observation: M4 closed; M5 is the sole runnable milestone.
- Result: pass. Seven visual-review network/runtime assets and authored-rest
  performances are distinct from API/Server and keep internal routes contained.
  Exact 147/147, full 352/352, browser 42/42 at 16.70 ms p95, deterministic
  84-cell; API/Server hashes stable.
- Visual review: P0/P1/P2 zero. Webhook's outer shell and Container's dashed
  isolation boundary retain small-size P3 visual noise only.
- Evidence: E-M5-01 and `build/diagram-core/m5-network-runtime.png`.
- Next action: release M6 and begin compute/delivery flow with failing contract.

### Attempt 9

- Milestone: M6.
- Observation: M5 closed; M6 is sole runnable milestone.
- Result: pass. Seven compute/delivery assets and authored-rest performances are
  brand-neutral and distinct; Code File/Reasoning baselines stable. Exact
  148/148, full 359/359, browser 49/49 at 17.40 ms p95, deterministic 84-cell.
- Repairs: Function replaced letter-like core with pure geometry; Branch path
  terminates at commit-b; browser verifier discards complex runtime returns and
  transports 49 isolation results as JSON while retaining count/per-icon checks.
- Visual review: P0/P1/P2 zero.
- Evidence: E-M6-01 and `build/diagram-core/m6-compute-delivery.png`.
- Next action: release M7 and begin operations/observability with failing contract.

### Attempt 10

- Milestone: M7.
- Observation: M6 closed; M7 is sole runnable milestone.
- Result: selected before source changes. Frozen ids are ci-cd, task, scheduler,
  monitoring, logs, alert, and debug; states remain empty.
- RED: `tests.test_diagram_core_m7_operations_batch` failed as expected at
  2026-07-18 02:42:10 CST with 14 missing-asset errors and 3 absent
  SVG/motion/inventory failures; Deployment and Search regression hashes passed.
- Result: pass. Seven operations assets complete the 56-icon catalog with empty
  states and distinct non-text identity. The first review found Logs scroll/
  highlight and Alert base collisions with their indicator; both were separated
  by 3-4 px and independently re-reviewed at P0/P1/P2 zero.
- Verification: exact 148/148, full 365/365, browser 56/56 at 16.90 ms p95,
  validator 56/56 with zero errors/warnings, deterministic 84-cell and four-mode
  recognition surfaces. Debug's 48 px grayscale reading remains non-blocking P3.
- Evidence: E-M7-01, `build/diagram-core/m7-operations.png`, and
  `build/diagram-core/m7-operations.recognition.png`.
- Next action: release M8 and run final 56-icon acceptance from the final tree.

### Attempt 11

- Milestone: M8.
- Observation: M7 closed; M8 is the sole runnable milestone.
- Result: pass. Final catalog contains exactly 56 visual-review icons,
  manifests, and authored-rest presentations; all states remain empty and the
  illustrated-character default runtime remains unchanged.
- Verification: full 365/365; validator 56/56 with zero errors/warnings; browser
  56/56 at 16.70 ms p95; all repeated instances isolated; clean rest and
  reduced/no-GSAP fallbacks; full 672-cell capture repeated byte-for-byte.
- Visual review: eight categorized surfaces independently reviewed at
  P0/P1/P2 zero. Nine known P3 associations remain suitable for a later visual
  refinement pass and do not block v1.
- Evidence: E-M8-01, `build/diagram-core/final-56.png`, categorized
  `build/diagram-core/final-*.png`, and the local live showcase.
- Next action: stop for user visual acceptance; no promotion or delivery action.

### Attempt 12

- Milestone: M8.
- Observation: user review rejects Search lens/handle separation and requests a
  whole-magnifier shake, clockwise full rotation of the center cross, and the
  existing two upper-right circle scale pulse.
- Result: focused RED was observed at 2026-07-18 08:14:00 CST on separate lens
  and handle tracks, then repaired with one body track, a positive 180/360 scan
  rotation, and the unchanged 1.45x target/indicator pulse. Full gate passed at
  2026-07-18 08:20:20 CST: 367/367 tests, validator 56/56, browser 56/56 at
  27.20 ms p95, clean rest/fallback/isolation, syntax, and diff checks.
- Failure: F-M8-01 repaired; class none.
- Evidence: E-M8-02 and the live generated showcase.
- Next action: user visual acceptance only; retain local worktree and make no
  delivery or default-system change.

### Attempt 13

- Milestone: M8.
- Observation: user clarified that the whole magnifier should keep together and
  trace a clockwise circular wobble around the authored lens-center position,
  rather than use the current left/right translate-and-rotate shake.
- Result: focused RED at 2026-07-18 08:55:36 CST found the old four-point
  x/rotate wobble, then passed after replacing it with a ten-point clockwise
  whole-body path and rest return. Final S0/S1 passed at 2026-07-18 08:58:56
  CST: 367/367 tests, validator 56/56, browser 56/56 at 27.10 ms p95, and ten
  Search path samples matched while lens/handle owned no independent transform.
- Failure: F-M8-02 repaired; class none.
- Evidence: E-M8-03 and the live generated showcase.
- Next action: user visual acceptance only; retain local worktree and make no
  delivery or default-system change.
