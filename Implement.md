# Diagram Core v1 Full Catalog Execution Rules

Workspace isolation: existing-isolated-worktree
Workspace isolation reason: all source changes are confined to the existing codex/diagram-core-v1-phase-0-1 linked worktree that already owns the approved benchmark diff
Delivery scope: local_only
S0 command: PYTHONPATH=src python3 -m unittest tests.test_diagram_core_catalog tests.test_diagram_core_assets tests.test_diagram_core_adapter tests.test_diagram_core_showcase tests.test_diagram_core_m1_compat_slice_one tests.test_diagram_core_m1_compat_slice_two tests.test_diagram_core_m2_actor_model_batch tests.test_diagram_core_m3_reasoning_knowledge_batch tests.test_diagram_core_m4_content_file_batch tests.test_diagram_core_m5_network_runtime_batch tests.test_diagram_core_m6_compute_delivery_batch tests.test_diagram_core_m7_operations_batch && node --check runtime/anidiagram-runtime.js && git diff --check
S1 command: PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --review && npm run verify:diagram-core-showcase
S2 command: none
S3 command: none
Needs-decision WIP limit: 2

## Selected Milestone

- Milestone: M8
- Approved scope boundary: 52 remaining canonical assets, manifests, catalog
  capabilities, showcase performances, generated review surfaces, tests, and
  task evidence only.
- Required gate: observe a failing Search choreography contract, then change
  only its showcase presentation and regenerated review/evidence surfaces.
- Stop conditions: the active milestone stop conditions plus Prompt.md forbidden
  actions.

## Execution Rules

- Resume the single valid `in_progress` milestone before selecting runnable work.
- Use test-driven development: write a batch contract test, observe the expected
  failure, implement only that batch, then run focused and affected-surface gates.
- Keep only one batch `in_progress`; mark downstream dependency release
  mechanically after fresh evidence.
- Use subagents for bounded implementation or review slices, but independently
  inspect their diffs and rerun all claimed gates.
- Preserve the four benchmark performance functions and geometry unless a
  failing regression proves an approved invariant is broken.
- New assets remain `visual-review`; states remain empty; no schema/default
  promotion occurs before human acceptance.
- After every attempt synchronize Plan.md, Documentation.md,
  docs/agent-loop-state.md, and docs/release-evidence.md.
- Stop when no safe runnable work remains or when the queue reaches a genuine
  decision/authority boundary.

## Attempt Record

### Attempt 1

- Selected milestone: M0.
- Changed assumptions: the previous control surfaces described an unrelated,
  already-finished Illustrated Character rollout and were not valid for the
  approved Diagram Core expansion.
- Action: ran the task checker, recorded its eight missing execution-policy
  errors, and replaced the six truth surfaces with the current approved scope.
- Result: initial checker exit 1; reconciliation pending fresh checker and
  baseline validation.
- Known failure: F-M0-01 stale control contract.
- Blocker class: repo_fixable.
- Next action: rerun checker and M0 validation.
- Synchronized status: Plan.md=M0 in_progress; Documentation.md=Attempt 1;
  agent-loop-state.md=Attempt 1; release-evidence.md=F-M0-01.

### Attempt 2

- Selected milestone: M0.
- Changed assumptions: none.
- Action: ran the full M0 validation command after contract reconciliation.
- Result: 306 tests and browser verification passed; final diff check failed on
  six trailing blank lines.
- Known failure: F-M0-02 documentation whitespace.
- Blocker class: repo_fixable.
- Next action: remove the trailing blank lines and rerun the complete M0 gate.
- Synchronized status: Plan.md=M0 in_progress; Documentation.md=Attempt 2;
  agent-loop-state.md=Attempt 2; release-evidence.md=F-M0-02.

### Attempt 3

- Selected milestone: M0.
- Changed assumptions: the 10 compatibility icons are implemented as two
  five-icon slices; the remaining 42 retain six seven-icon batches.
- Action: reran the full M0 gate, then rechecked the final inventory contract,
  clean diff, branch, and linked-worktree identity.
- Result: pass; 306 tests, runtime syntax, four-icon browser verifier, task
  checker, isolated worktree, and diff checks all exited 0.
- Known failures: F-M0-01 and F-M0-02 remain recorded and repaired.
- Blocker class: none.
- Next action: mechanically release M1 and begin its first TDD slice.
- Synchronized status: Plan.md=M0 done, M1 runnable;
  Documentation.md=Attempt 3; agent-loop-state.md=Attempt 3;
  release-evidence.md=E-M0-01.

### Attempt 4

- Selected milestone: M1.
- Changed assumptions: the live showcase and static review generators now derive
  implemented subsets from canonical catalog, manifest, and motion data rather
  than a fixed four-icon list.
- Action: implemented the two five-icon compatibility slices by TDD; generated
  canonical SVGs/manifests and declarative performances; added data-driven live
  and static batch review surfaces; independently reviewed visual identity,
  selector isolation, determinism, fallback, and control-plane completeness.
- Result: pass; 14 visual-review assets and 42 planned entries, 14 SVGs and
  manifests, 152/152 exact milestone tests, 328/328 full tests, 14/14 isolated
  browser timelines, two deterministic 60-cell matrices, and 16.60 ms p95.
- Known failures: F-M1-01 through F-M1-04 remain recorded and repaired.
- Blocker class: none.
- Next action: mechanically release M2, select it, and observe its failing
  seven-icon actor/model batch contract before implementation.
- Synchronized status: Plan.md=M1 done, M2 runnable;
  Documentation.md=Attempt 4; agent-loop-state.md=Attempt 4;
  release-evidence.md=E-M1-01.

### Attempt 5

- Selected milestone: M2.
- Changed assumptions: none; M1 independent review closed with P0/P1/P2 at zero
  and the recorded Tool ambiguity remaining P3/non-blocking.
- Action: selected the mechanically runnable seven-icon actor/model batch before
  source changes; recorded RED; delegated implementation; incorporated visual
  pre-review changes for User, Developer, Agent Team, Assistant, Reviewer, AI
  Model, and LLM; generated and reviewed the 84-cell matrix; reran exact and full
  gates from the final tree.
- Result: pass at 2026-07-18 00:41:27 CST; 21 visual-review and 35 planned,
  147/147 exact tests, 334/334 full tests, 21/21 isolated timelines, 27.00 ms
  p95, deterministic 84-cell capture, and independent P0/P1/P2 at zero.
- Known failures: F-M2-01 through F-M2-03 repaired; R-M2-01 resolved by the
  bounded implementation.
- Blocker class: none.
- Next action: mechanically release M3 and begin its reasoning/knowledge batch
  with a failing contract.
- Synchronized status: Plan.md=M2 done, M3 runnable;
  Documentation.md=Attempt 5; agent-loop-state.md=Attempt 5;
  release-evidence.md=E-M2-01.

### Attempt 6

- Selected milestone: M3.
- Changed assumptions: none; M2 independently closed with P0/P1/P2 at zero.
- Action: selected M3 before source changes; recorded RED; delegated the seven
  assets and performances; generated and reviewed the 84-cell matrix; repaired
  shared planned/count test drift; reran exact and full gates from the final
  tree.
- Result: pass at 2026-07-18 01:09:55 CST; 28 visual-review and 28 planned,
  147/147 exact tests, 340/340 full tests, 28/28 isolated timelines at 26.80 ms
  p95, deterministic 84-cell capture, independent P0/P1/P2 at zero.
- Known failures: F-M3-01 and F-M3-02 repaired; R-M3-01 resolved.
- Blocker class: none.
- Next action: mechanically release M4 and begin its file/content batch with a
  failing contract.
- Synchronized status: Plan.md=M3 done, M4 runnable;
  Documentation.md=Attempt 6; agent-loop-state.md=Attempt 6;
  release-evidence.md=E-M3-01.

### Attempt 7

- Selected milestone: M4.
- Changed assumptions: none; M3 independently closed with P0/P1/P2 at zero.
- Action: selected M4 before source changes; introduced reusable batch helpers;
  recorded RED; delegated seven assets/performances; repaired Document Store's
  printer-like geometry; reviewed deterministic 84-cell output; reran exact and
  full gates.
- Result: pass at 2026-07-18 01:41:20 CST; 35 visual-review and 21 planned,
  147/147 exact tests, 346/346 full tests, 35/35 isolated timelines at 27.10 ms
  p95, deterministic 84-cell capture, independent P0/P1/P2 at zero.
- Known failures: F-M4-01 repaired; R-M4-01 resolved.
- Blocker class: none.
- Next action: mechanically release M5 and begin its network/runtime batch with
  a failing contract.
- Synchronized status: Plan.md=M4 done, M5 runnable;
  Documentation.md=Attempt 7; agent-loop-state.md=Attempt 7;
  release-evidence.md=E-M4-01.

### Attempt 8

- Selected milestone: M5.
- Changed assumptions: none; M4 independently closed with P0/P1/P2 at zero.
- Action: selected M5 before source changes; recorded RED; delegated seven
  assets/performances; reviewed deterministic 84-cell output and connector-line
  containment; reran exact and full gates from final tree.
- Result: pass at 2026-07-18 02:04:26 CST; 42 visual-review and 14 planned,
  147/147 exact tests, 352/352 full tests, 42/42 isolated timelines at 16.70 ms
  p95, deterministic 84-cell capture, independent P0/P1/P2 at zero.
- Known failures: F-M5-01 repaired; R-M5-01 resolved.
- Blocker class: none.
- Next action: mechanically release M6 and begin its compute/delivery batch with
  a failing contract.
- Synchronized status: Plan.md=M5 done, M6 runnable;
  Documentation.md=Attempt 8; agent-loop-state.md=Attempt 8;
  release-evidence.md=E-M5-01.

### Attempt 9

- Selected milestone: M6.
- Changed assumptions: none; M5 independently closed with P0/P1/P2 at zero.
- Action: selected M6 before source changes; recorded RED; delegated assets and
  performances; repaired Function/Branch visuals; TDD-fixed 49-icon Playwright
  serialization without weakening per-icon isolation; reviewed 84 cells and
  reran exact/full gates.
- Result: pass at 2026-07-18 02:31:09 CST; 49 visual-review and 7 planned,
  148/148 exact tests, 359/359 full tests, 49/49 timelines at 17.40 ms p95,
  deterministic 84-cell, visual P0/P1/P2 zero.
- Known failures: F-M6-01 and F-M6-02 repaired; R-M6-01 resolved.
- Blocker class: none.
- Next action: mechanically release M7 and begin operations/observability with a
  failing contract.
- Synchronized status: Plan.md=M6 done, M7 runnable;
  Documentation.md=Attempt 9; agent-loop-state.md=Attempt 9;
  release-evidence.md=E-M6-01.

### Attempt 10

- Selected milestone: M7.
- Changed assumptions: none; M6 independently closed with P0/P1/P2 at zero.
- Action: selected M7 before operations/observability source changes; added and
  ran the frozen seven-icon contract before implementation; delegated the seven
  assets/performances; regenerated the 56-icon showcase; fixed the legacy
  planned-fixture test; repaired Logs/Alert indicator collisions; reran exact,
  full, static, recognition, browser, and independent visual gates.
- Result: pass at 2026-07-18 03:13:18 CST; 56 visual-review and 0 planned,
  148/148 exact tests, 365/365 full tests, 56/56 timelines at 16.90 ms p95,
  deterministic 84-cell and four-mode recognition evidence, P0/P1/P2 zero.
- Known failures: R-M7-01 resolved; F-M7-01, F-M7-02, and F-M7-03 repaired.
- Blocker class: none.
- Next action: mechanically release M8 and run final 56-icon acceptance.
- Synchronized status: Plan.md=M7 done, M8 runnable;
  Documentation.md=Attempt 10; agent-loop-state.md=Attempt 10;
  release-evidence.md=E-M7-01.

### Attempt 11

- Selected milestone: M8.
- Changed assumptions: none; M7 independently closed with P0/P1/P2 at zero.
- Action: selected M8 before final acceptance generation; produced one 672-cell
  all-catalog surface and eight categorized surfaces; repeated the full capture;
  ran the declared final gate and independent total-catalog review.
- Result: pass at 2026-07-18 03:20:57 CST; 365/365 tests, validator 56/56 with
  zero errors/warnings, 56/56 isolated browser timelines at 16.70 ms p95,
  repeat-identical 672-cell PNG, and independent P0/P1/P2 zero.
- Known failures: none for M8 yet.
- Blocker class: none.
- Next action: stop at user visual acceptance; do not promote, commit, push,
  merge, deploy, or change the default icon system.
- Synchronized status: Plan.md=M8 done;
  Documentation.md=Attempt 11; agent-loop-state.md=Attempt 11;
  release-evidence.md=E-M8-01.

### Attempt 12

- Selected milestone: M8.
- Changed assumptions: user visual review rejects Search lens/handle separation
  and specifies one whole-magnifier shake, a clockwise 360-degree center-cross
  rotation, and preservation of the two upper-right circle scale motion.
- Action: reopened M8 before source changes, froze the Search-only revision,
  added its choreography contract, and ran that contract against the unchanged
  presentation.
- Result: RED observed at 2026-07-18 08:14:00 CST on the expected separate
  lens/handle tracks, then repaired. Final gate passed at 2026-07-18 08:20:20
  CST: 367/367 tests, validator 56/56 with zero errors/warnings, 56/56 browser
  timelines at 27.20 ms p95, clean rest/fallback/isolation, syntax, and diff.
- Known failures: F-M8-01 repaired; full-turn permission is restricted to the
  Search scan track while all other declarative rotations retain the 14-degree
  limit.
- Blocker class: none.
- Next action: stop for user visual acceptance; do not promote, commit, push,
  merge, deploy, or change the default icon system.
- Synchronized status: Plan.md=M8 done;
  Documentation.md=Attempt 12; agent-loop-state.md=Attempt 12;
  release-evidence.md=E-M8-02.

### Attempt 13

- Selected milestone: M8.
- Changed assumptions: the requested whole-magnifier shake is not a horizontal
  translate/rotate wobble. The complete magnifier must keep its orientation and
  trace a small clockwise circle around the authored lens-center position,
  return to rest, then continue with the approved scan and circle pulses.
- Action: reopened M8 before test or production changes and froze the revision
  to the Search body choreography, its contract/hash, generated showcase, and
  synchronized evidence.
- Result: RED observed at 2026-07-18 08:55:36 CST on the old four-point
  x/rotate wobble, then repaired. Final gate passed at 2026-07-18 08:58:56 CST:
  367/367 tests, validator 56/56, browser verified all ten clockwise path points
  and 56/56 timelines at 27.10 ms p95, with clean rest/fallback/isolation,
  syntax, and diff.
- Known failures: F-M8-02 repaired; body owns all circular displacement while
  lens and handle retain zero independent transform.
- Blocker class: none.
- Next action: stop for user visual acceptance; do not promote, commit, push,
  merge, deploy, or change the default icon system.
- Synchronized status: Plan.md=M8 done;
  Documentation.md=Attempt 13; agent-loop-state.md=Attempt 13;
  release-evidence.md=E-M8-03.
