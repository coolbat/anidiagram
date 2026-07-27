# Diagram Core v1 Full Catalog Release Evidence

## Policy Snapshot

- Workspace isolation: existing isolated worktree
- Worktree: `/Users/coolbat/anidiagram/.worktrees/diagram-core-v1-phase-0-1`
- Branch: `codex/diagram-core-v1-phase-0-1`
- Delivery scope: local_only
- Required levels: S0 and S1 per batch; S2 and S3 not authorized or required
- Needs-decision count/limit: 0/2
- Target environment: local generated artifacts and pinned Chromium
- Closure: awaiting-confirmation; Search circular-wobble automated acceptance complete

## Failure F-M0-01

- Milestone: M0
- Attempt: 1
- Command: `python3 /Users/coolbat/long-horizon-task-skill/skills/long-horizon-task/scripts/check_task_contract.py --project /Users/coolbat/anidiagram/.worktrees/diagram-core-v1-phase-0-1 --json`
- Working directory: `/Users/coolbat/anidiagram/.worktrees/diagram-core-v1-phase-0-1`
- Result: exit 1.
- Failure: eight required execution-policy fields were missing from Implement.md;
  all milestones belonged to an older completed Illustrated Character rollout.
- Hypothesis: canonical root truth surfaces were not switched when the Diagram
  Core linked worktree was created.
- Repair: replace all six truth surfaces with the approved 52-icon expansion
  scope, exact batch queue, local-only policy, and S0/S1 gates.
- Blocker class: repo_fixable.
- Affected acceptance: long-horizon preflight and safe milestone selection.
- Next action: rerun checker and M0 validation; preserve this failure record.

## Existing Benchmark Evidence Carried Into M0

- Observation: four benchmark showcase revision verified after Database layer
  wave correction.
- Result: 6/6 focused showcase tests; 306/306 full tests; browser verifier
  reported four expressive isolated timelines, Database top-to-bottom layers,
  horizontal layer displacement 0, clean rest, zero reduced/no-GSAP timelines,
  and 20-icon p95 25.40 ms.
- Review: independent subagent closed with no P0/P1/P2 findings.
- Status: historical input only; M0 still requires a fresh baseline after control
  reconciliation.

## Next Evidence

- E-M0-01 pending fresh task checker, exact inventory audit, full baseline,
  runtime syntax, browser verifier, and diff check.

## Failure F-M0-02

- Milestone: M0
- Attempt: 2
- Command: full M0 validation command from Plan.md.
- Result: exit 2 after 306/306 tests and the browser verifier passed.
- Failure: `git diff --check` reported one trailing blank line at EOF in each of
  the six reconciled control files.
- Hypothesis: Add File patches retained an extra terminal blank line.
- Repair: remove only the reported terminal blank lines and rerun the full gate.
- Blocker class: repo_fixable.
- Affected acceptance: clean final diff.
- Resume condition: complete M0 command exits 0.

## Evidence E-M0-01

- Milestone: M0
- Attempt: 3
- Recorded at: 2026-07-17 23:35:30 CST
- Commands: full M0 Validation command in Plan.md; final task checker; isolated
  branch/worktree audit.
- Working directory: `/Users/coolbat/anidiagram/.worktrees/diagram-core-v1-phase-0-1`
- Result: exit 0; 306/306 tests; JavaScript syntax clean; four expressive
  isolated showcase timelines; Database layers top-to-bottom with x=0; clean
  rest; reduced/no-GSAP zero timelines; 20-icon p95 26.10 ms; diff clean.
- Inventory: PRD and Catalog contain the same 56 ordered, categorized canonical
  ids; 4 benchmarks implemented and 52 remaining ids assigned exactly once to
  two five-icon and six seven-icon slices.
- Artifact: `gallery/diagram-core/showcase.html` and the six canonical control
  surfaces.
- Known failures: F-M0-01 and F-M0-02 repaired; retained above.
- Blocker class: none.
- Verdict: pass; M0 done and M1 mechanically runnable.
- Residual risk: the four-icon generator/runtime verifier must be made
  data-driven before safely scaling to 56.
- Next action: select M1 and begin its first TDD slice.

## Failure F-M1-01

- Milestone: M1
- Attempt: 4
- Failure: an early declarative Operator performance used endpoint/back easing
  combinations that could exceed the approved expressive amplitude bound.
- Repair: replace the overshooting endpoint/ease with bounded `power2` motion
  and verify authored rest plus runtime reset.
- Blocker class: repo_fixable; repaired.

## Failure F-M1-02

- Milestone: M1
- Attempt: 4
- Failure: the first Tool silhouette read as cat ears/robot and the first
  Operator read as a terminal/device at 48 px.
- Repair: redesign Tool as a handled pipeline mechanism and Operator as a
  neutral human head-and-shoulders behind a foreground console; add regression
  contracts before replacing the SVGs.
- Blocker class: repo_fixable; repaired.

## Failure F-M1-03

- Milestone: M1
- Attempt: 4
- Failure: adversarial recipes could use malformed, foreign, prototype-like, or
  duplicate selectors to throw or escape an icon instance.
- Repair: use null-prototype part maps, own-property checks, dangerous-name and
  duplicate-target rejection, guarded `Element` lookup, and same-root
  presentation containment; adversarial browser tests now fail closed.
- Blocker class: repo_fixable; repaired.

## Failure F-M1-04

- Milestone: M1
- Attempt: 4
- Failure: the initial written milestone gate omitted validator `--review` mode
  and the two compatibility slice contract modules.
- Repair: correct M1-M8/S1 validator invocations and include both slice modules
  in the exact M1/S0 command before rerunning all gates.
- Blocker class: repo_fixable; repaired.

## Evidence E-M1-01

- Milestone: M1
- Attempt: 4
- Recorded at: 2026-07-18 00:16:12 CST
- Commands: exact M1 Validation command in Plan.md; `PYTHONPATH=src python3 -m
  unittest discover -s tests`; deterministic contact-sheet generation/capture
  for both five-icon slices; independent implementation and control review.
- Working directory: `/Users/coolbat/anidiagram/.worktrees/diagram-core-v1-phase-0-1`
- Result: exit 0; validator reports 56 catalog ids, 14 visual-review, 42
  planned, 14 SVGs, 14 manifests, and zero errors; exact gate 152/152; full
  suite 328/328; JavaScript syntax clean; diff clean.
- Browser: 14 icons and 14 isolated expressive timelines; recipe properties
  allowlisted and fail-closed; targets unique and instance-scoped; Database
  layer x displacement 0; authored rest clean; reduced/no-GSAP zero timelines;
  repeated instances isolated; fixed 20-icon p95 16.60 ms over 404 frames.
- Static artifacts: `build/diagram-core/m1-compat-a.final.*` and
  `build/diagram-core/m1-compat-b.*`; 60 cells each at 3 sizes by 4 contexts;
  generation hashes repeat exactly; captures use DPR 1 with zero requests and
  zero active animations.
- Visual verdict: Operator and Tool redesigns remove the blocking ambiguity;
  File, Folder, Output, Shield, Cloud, Memory, Token, and Search remain clear at
  review sizes. Tool has a residual P3 visual risk of reading as an instrument/camera,
  to be reassessed in the final 56-icon family surface.
- Known failures: F-M1-01 through F-M1-04 repaired and retained above.
- Blocker class: none.
- Verdict: pass; M1 done and M2 mechanically runnable.
- Next action: select M2 and observe its failing seven-icon batch contract.

## M2 Attempt 5 Start

- Milestone: M2
- Attempt: 5
- Preconditions: M1 independently closed with P0/P1/P2 at zero; task checker
  ready; M2 was the single runnable milestone.
- Action: mark M2 in progress before any actor/model source changes.
- Current result: expected RED batch contract recorded as R-M2-01.
- Next action: delegate implementation against the frozen contract.

## Failure F-M2-01

- Milestone: M2
- Attempt: 5
- Failure: the initial Agent motion-definition hash was produced with compact
  JavaScript serialization while the Python assertion used spaced JSON output.
- Repair: replace the expected hash with the current Python-serialized baseline;
  the isolated benchmark assertion then passes before M2 implementation.
- Blocker class: repo_fixable; repaired.

## RED Evidence R-M2-01

- Milestone: M2
- Attempt: 5
- Recorded at: 2026-07-18 00:23:47 CST
- Command: `PYTHONPATH=src python3 -m unittest
  tests.test_diagram_core_m2_actor_model_batch`
- Result: expected failure from the unchanged implementation; 15 missing asset
  or manifest errors and three missing SVG/motion/inventory failures. The Agent
  benchmark stability assertion passes separately.
- Required implementation: exactly seven visual-review assets/manifests and
  bounded authored-rest presentations, producing 21 implemented and 35 planned
  entries without modifying the Agent benchmark.

## Failure F-M2-02

- Milestone: M2
- Attempt: 5
- Failure: the shared catalog test still used newly implemented User and LLM as
  examples of planned icons, causing two failures after the M2 assets turned
  green.
- Repair: replace those stale examples with neural-network, PDF, and Scheduler,
  which remain planned; rerun the focused and full suites.
- Blocker class: repo_fixable; repaired.

## Failure F-M2-03

- Milestone: M2
- Attempt: 5
- Failure: the first written M2 Validation/S0 gate did not explicitly include
  the new M2 batch contract module.
- Repair: add `tests.test_diagram_core_m2_actor_model_batch` to the exact M2 and
  persistent S0 routes before fresh closure verification.
- Blocker class: repo_fixable; repaired.

## Evidence E-M2-01

- Milestone: M2
- Attempt: 5
- Recorded at: 2026-07-18 00:41:27 CST
- Commands: exact corrected M2 Validation command from Plan.md; `PYTHONPATH=src
  python3 -m unittest discover -s tests`; deterministic 84-cell generation and
  capture; independent visual review; root image inspection.
- Working directory: `/Users/coolbat/anidiagram/.worktrees/diagram-core-v1-phase-0-1`
- Inventory: 56 catalog ids, 21 visual-review, 35 planned, 21 SVGs, 21 manifests,
  zero validator errors or warnings, all states empty, and no default-system
  promotion.
- Test result: exact gate 147/147 and full suite 334/334; diff clean.
- Browser: 21 icons and 21 isolated timelines; allowlisted fail-closed recipes;
  unique instance-scoped targets; clean authored rest; reduced/no-GSAP zero;
  repeated instances isolated; fixed 20-icon p95 27.00 ms over 419 frames.
- Static artifact: `build/diagram-core/m2-actor-model.png`, 2184 by 416, 84
  cells at 3 sizes by 4 contexts, DPR 1, zero requests, zero animations, SHA256
  `3369fb2a1a54742b3964d135e593d33ad85d8c7a2df05e711b7e6156a0b8751e`;
  source SVG/HTML/recognition/index generation hashes repeated exactly.
- Visual verdict: User, Developer, Agent Team, Assistant, Human Reviewer, AI
  Model, and LLM remain distinct from each other and Agent/Operator/Search/
  Memory/API/Token; independent P0/P1/P2 at zero.
- Residual risk: LLM without its node label may first read as language/context
  bands; recorded as non-blocking P3 and consistent with its non-text contract.
- Known failures: F-M2-01 through F-M2-03 repaired; R-M2-01 resolved.
- Blocker class: none.
- Verdict: pass; M2 done and M3 mechanically runnable.
- Next action: select M3 and observe its failing reasoning/knowledge batch
  contract.

## M3 Attempt 6 Start

- Milestone: M3
- Attempt: 6
- Preconditions: M2 independently closed with P0/P1/P2 at zero; checker ready;
  M3 was the single runnable milestone.
- Action: mark M3 in progress before reasoning/knowledge source changes.
- Current result: expected RED batch contract recorded as R-M3-01.
- Next action: delegate implementation against the frozen contract.

## RED Evidence R-M3-01

- Milestone: M3
- Attempt: 6
- Recorded at: 2026-07-18 00:49:10 CST
- Command: `PYTHONPATH=src python3 -m unittest
  tests.test_diagram_core_m3_reasoning_knowledge_batch`
- Result: expected failure from the unchanged implementation; 14 missing asset
  or manifest errors and three missing SVG/motion/inventory failures. The
  Database SVG, manifest, and motion-definition stability assertion passes.
- Required implementation: exactly seven visual-review assets/manifests and
  bounded authored-rest presentations, producing 28 implemented and 28 planned
  entries without modifying the Database benchmark.

## Failure F-M3-01

- Milestone: M3
- Attempt: 6
- Failure: the shared catalog test froze Neural Network as a planned example and
  failed after its intended M3 promotion.
- Repair: derive all planned ids dynamically from the catalog so later batch
  promotions cannot stale the fixture.
- Blocker class: repo_fixable; repaired.

## Failure F-M3-02

- Milestone: M3
- Attempt: 6
- Failure: the M2 batch validator contract froze the global 21/35 inventory and
  failed after M3 correctly reached 28/28.
- Repair: make M2 and M3 batch contracts assert batch inclusion, asset/manifest
  parity, and invariant total 56 instead of freezing later global counts.
- Blocker class: repo_fixable; repaired.

## Evidence E-M3-01

- Milestone: M3
- Attempt: 6
- Recorded at: 2026-07-18 01:09:55 CST
- Commands: exact M3 Validation command; full unittest discovery; deterministic
  84-cell generation/capture; independent visual review; root image inspection.
- Inventory: 56 catalog ids, 28 visual-review, 28 planned, 28 SVGs/manifests,
  zero validator errors or warnings, empty states, no default promotion.
- Test result: exact gate 147/147; full suite 340/340; diff clean.
- Browser: 28 icons/timelines; allowlisted fail-closed recipes; unique
  instance-scoped targets; clean rest; reduced/no-GSAP zero; repeated instances
  isolated; fixed 20-icon p95 26.80 ms over 404 frames.
- Static artifact: `build/diagram-core/m3-reasoning-knowledge.png`, 2184 by 416,
  84 cells, DPR 1, zero requests/animations, SHA256
  `6746d073612d41bf14226190aad8653d55763e038c43e3bb27fe8d156c7e3365`;
  SVG/HTML/recognition/index hashes repeat exactly.
- Visual verdict: all seven are distinct from each other and Database/Memory/
  Token/Search; P0/P1/P2 at zero.
- Residual risk: Vector Database may first suggest a server rack at 48 px;
  recorded P3, with points and vertical scanner providing the intended reading.
- Known failures: F-M3-01 and F-M3-02 repaired; R-M3-01 resolved.
- Blocker class: none.
- Verdict: pass; M3 done and M4 mechanically runnable.
- Next action: select M4 and observe its failing content/file batch contract.

## M4 Attempt 7 Start

- Milestone: M4
- Attempt: 7
- Preconditions: M3 independently closed with P0/P1/P2 at zero; checker ready;
  M4 was the single runnable milestone.
- Action: mark M4 in progress before content/file source changes.
- Current result: expected RED batch contract recorded as R-M4-01.
- Next action: delegate implementation against the frozen contract.

## RED Evidence R-M4-01

- Milestone: M4
- Attempt: 7
- Recorded at: 2026-07-18 01:15:25 CST
- Command: `PYTHONPATH=src python3 -m unittest
  tests.test_diagram_core_m4_content_file_batch`
- Result: expected failure from unchanged implementation; 14 missing asset or
  manifest errors and three missing SVG/motion/inventory failures. The canonical
  File SVG, manifest, and motion stability assertion passes.
- Required implementation: seven visual-review file/content assets and bounded
  authored-rest presentations, producing at least 35 implemented assets while
  preserving total inventory 56 and File baseline.

## Failure F-M4-01

- Milestone: M4
- Attempt: 7
- Failure: the first Document Store silhouette read primarily as a printer due
  to a curved feed slot, upright paper pair, and power-like corner indicator.
- Repair: remove the feed arc; use a straight single cabinet, rectangular label
  drawer with short handle, and two offset/fanned inserted document cards;
  preserve public Parts, manifest, and motion contract; regenerate 84 cells.
- Blocker class: repo_fixable; repaired. Final independent P2 closed.

## Evidence E-M4-01

- Milestone: M4
- Attempt: 7
- Recorded at: 2026-07-18 01:41:20 CST
- Commands: exact M4 Validation command; full unittest discovery; deterministic
  84-cell generation/capture; independent visual review; root image inspection.
- Inventory: 56 ids, 35 visual-review, 21 planned, 35 SVGs/manifests, zero
  validator errors/warnings, empty states, no default promotion.
- Test result: exact gate 147/147; full suite 346/346; diff clean.
- Browser: 35 icons/timelines; fail-closed allowlisted recipes; unique scoped
  targets; clean rest; reduced/no-GSAP zero; repeated instances isolated; fixed
  20-icon p95 27.10 ms over 394 frames.
- Static artifact: `build/diagram-core/m4-content-file.png`, 84 cells at 3 sizes
  by 4 contexts, DPR 1, zero requests/animations, SHA256
  `36ba565a4f34db3c9061ef8684c8e8c10e04e9c8e36e364b42e131a275571255`;
  second generation matches source and PNG byte-for-byte.
- Visual verdict: all seven are distinct from one another and File/Folder/
  Memory/Warehouse/Dataset; P0/P1/P2 at zero after F-M4-01 repair.
- Residual risks: PDF reads as bound/paginated document without text; Code badge
  can weakly suggest version control; Document Store retains slight isolated
  office-device association. All are non-blocking P3.
- Known failures: F-M4-01 repaired; R-M4-01 resolved.
- Blocker class: none.
- Verdict: pass; M4 done and M5 mechanically runnable.
- Next action: select M5 and observe its failing network/runtime batch contract.

## M5 Attempt 8 Start

- Milestone: M5
- Attempt: 8
- Preconditions: M4 independently closed with P0/P1/P2 at zero; checker ready;
  M5 was the single runnable milestone.
- Action: mark M5 in progress before network/runtime source changes.
- Current result: expected RED batch contract recorded as R-M5-01.
- Next action: delegate implementation against frozen contract.

## RED Evidence R-M5-01

- Milestone: M5
- Attempt: 8
- Recorded at: 2026-07-18 01:45:16 CST
- Command: `PYTHONPATH=src python3 -m unittest
  tests.test_diagram_core_m5_network_runtime_batch`
- Result: expected failure from unchanged implementation; 14 missing asset or
  manifest errors and three missing SVG/motion/inventory failures. API and
  Server SVG/manifest/motion stability assertions pass.
- Required implementation: seven visual-review assets and bounded authored-rest
  presentations, at least 42 implemented total, total inventory 56, no API or
  Server regression.

## Failure F-M5-01

- Milestone: M5
- Attempt: 8
- Failure: three process invocations were malformed during subagent verification:
  showcase generator omitted `--output`, contact generator used unsupported
  `--recognition` placement, and one validator JSON pipe had invalid shell quotes.
- Repair: rerun each command with documented arguments; no product source was
  changed for these command errors; all final gates and deterministic outputs pass.
- Blocker class: repo_fixable; repaired and retained as process evidence.

## Evidence E-M5-01

- Milestone: M5
- Attempt: 8
- Recorded at: 2026-07-18 02:04:26 CST
- Commands: exact M5 Validation; full unittest discovery; deterministic 84-cell
  generation/capture; independent visual review; root image inspection.
- Inventory: 56 ids, 42 visual-review, 14 planned, 42 SVGs/manifests, zero
  validator errors/warnings, empty states, no default promotion.
- Test result: exact gate 147/147; full suite 352/352; diff clean.
- Browser: 42 icons/timelines; fail-closed allowlisted recipes; unique scoped
  targets; clean rest; reduced/no-GSAP zero; repeated instances isolated; fixed
  20-icon p95 16.70 ms over 454 frames.
- Static artifact: `build/diagram-core/m5-network-runtime.png`, 84 cells, DPR 1,
  zero requests/animations, SHA256
  `9a8913c0997c4cf81a17683b0fead379c882b78412c0811ffc67ed516f5d594a`;
  second generation matches source and PNG byte-for-byte.
- Visual verdict: seven roles distinct from one another and API/Server; internal
  distribution routes terminate inside explicit outlet boxes; P0/P1/P2 zero.
- Residual risks: Webhook outer shell and Container dashed boundary add mild
  48 px noise; recorded non-blocking P3.
- Known failures: F-M5-01 repaired; R-M5-01 resolved.
- Blocker class: none.
- Verdict: pass; M5 done and M6 mechanically runnable.
- Next action: select M6 and observe failing compute/delivery batch contract.

## M6 Attempt 9 Start

- Milestone: M6
- Attempt: 9
- Preconditions: M5 independently closed with P0/P1/P2 at zero; checker ready;
  M6 was the single runnable milestone.
- Action: mark M6 in progress before compute/delivery source changes.
- Current result: expected RED batch contract recorded as R-M6-01.
- Next action: delegate implementation against frozen contract.

## RED Evidence R-M6-01

- Milestone: M6
- Attempt: 9
- Recorded at: 2026-07-18 02:08:44 CST
- Command: `PYTHONPATH=src python3 -m unittest
  tests.test_diagram_core_m6_compute_delivery_batch`
- Result: expected failure from unchanged implementation; 14 missing asset or
  manifest errors and three missing SVG/motion/inventory failures. Code File and
  Reasoning SVG/manifest/motion stability assertions pass.
- Required implementation: seven visual-review assets and bounded authored-rest
  presentations, at least 49 implemented total, inventory 56, no baseline drift.

## Failure F-M6-01

- Milestone: M6
- Attempt: 9
- Failure: first Function core resembled `t/f` lettering and a battery capsule;
  Branch included a line segment beyond its branch commit.
- Repair: replace Function with a pure geometric two-input transform core and
  terminate Branch exactly at commit-b; preserve Parts/manifests/motion targets.
- Blocker class: repo_fixable; repaired pending final matrix evidence.

## Failure F-M6-02

- Milestone: M6
- Attempt: 9
- Command: `npm run verify:diagram-core-showcase` at 49 implemented icons.
- Result: stable failure in repeated-instance isolation result return with
  `Cannot serialize result: object reference chain is too long` near verifier
  line 571; focused contracts and validator pass before this transport failure.
- Hypothesis: page evaluation returns a 49-item object graph whose reference
  chain exceeds Playwright serialization limits; not an asset recipe failure.
- Repair: add failing scale/transport regression; discard the complex return
  from runtime `play()`, stringify isolation results in-page, parse in Node,
  assert result count equals icon count, and retain every per-icon assertion.
- Blocker class: repo_fixable; repaired.

## Evidence E-M6-01

- Milestone: M6
- Attempt: 9
- Recorded at: 2026-07-18 02:31:09 CST
- Commands: exact M6 Validation; full unittest discovery; deterministic 84-cell
  generation/capture; independent visual review; root image inspection.
- Inventory: 56 ids, 49 visual-review, 7 planned, 49 SVGs/manifests, zero
  validator errors/warnings, empty states, no default promotion.
- Test result: exact gate 148/148; full suite 359/359; diff clean.
- Browser: 49 icons/timelines; fail-closed allowlisted recipes; unique scoped
  targets; clean rest; reduced/no-GSAP zero; 49 repeated-instance results
  transferred as JSON and all isolated; fixed 20-icon p95 17.40 ms/433 frames.
- Static artifact: `build/diagram-core/m6-compute-delivery.png`, 84 cells, DPR 1,
  zero requests/animations, SHA256
  `28ad4832c23c689fb6ea6d48d3b6792994cdb7c5e0fdbb5796f7d3f58f306adc`;
  generation repeats byte-for-byte.
- Visual verdict: all seven distinct from Code File/Reasoning/Container/Output;
  no brand/text or path-to-anchor ambiguity; P0/P1/P2 zero.
- Known failures: F-M6-01/F-M6-02 repaired; R-M6-01 resolved.
- Blocker class: none.
- Verdict: pass; M6 done and M7 mechanically runnable.
- Next action: select M7 and observe failing operations/observability contract.

## M7 Attempt 10 Start

- Milestone: M7
- Attempt: 10
- Preconditions: M6 independently closed with P0/P1/P2 at zero; checker ready;
  M7 was the single runnable milestone.
- Action: mark M7 in progress before operations/observability source changes.
- Current result: expected RED recorded as R-M7-01.
- Next action: implement only the frozen M7 batch before rerunning the contract.

## Regression R-M7-01

- Milestone: M7
- Attempt: 10
- Recorded at: 2026-07-18 02:42:10 CST
- Command: `PYTHONPATH=src python3 -m unittest tests.test_diagram_core_m7_operations_batch`
- Result: expected RED before implementation: 14 missing-manifest/asset errors
  and 3 failures for absent SVG prototypes, authored-rest motion recipes, and
  the incomplete 56-icon review inventory; Deployment/Search hashes passed.
- Expected repair: add exactly ci-cd, task, scheduler, monitoring, logs, alert,
  and debug with empty states and brand-neutral non-text identity cues.
- Blocker class: repo_fixable; resolved by E-M7-01.

## Failure F-M7-01

- Milestone: M7
- Attempt: 10
- Failure: exact showcase consistency failed after adding and later repairing
  the seven source assets because the committed generated showcase was stale.
- Repair: regenerate `gallery/diagram-core/showcase.html` after each final source
  change and rerun its self-contained generator equality contract.
- Blocker class: repo_fixable; repaired.

## Failure F-M7-02

- Milestone: M7
- Attempt: 10
- Failure: the 365-test suite raised `StopIteration` because an old fail-closed
  test assumed the production catalog would always contain a planned icon.
- Repair: keep the fail-closed assertion but provide an isolated synthetic
  planned catalog entry, allowing the completed zero-planned catalog.
- Blocker class: repo_fixable; repaired.

## Failure F-M7-03

- Milestone: M7
- Attempt: 10
- Failure: independent 48 px review found Logs scroll/highlight and Alert base
  intersecting their indicator, creating node-connector ambiguity (P2=2).
- Repair: stop Logs scroll at y=61 and move its highlight dot to x=61; constrain
  the centered Alert base to x<=64. Independent re-review: P0/P1/P2 zero.
- Blocker class: repo_fixable; repaired.

## Evidence E-M7-01

- Milestone: M7
- Attempt: 10
- Recorded at: 2026-07-18 03:13:18 CST
- Commands: exact M7 Validation; full unittest discovery; deterministic 84-cell
  generation/capture; four-mode 48 px recognition capture; independent visual
  review and repair re-review.
- Inventory: 56 ids, 56 visual-review, 0 planned, 56 SVGs/manifests, zero
  validator errors/warnings, all states empty, no default promotion.
- Test result: exact gate 148/148; full suite 365/365; diff clean.
- Browser: 56 icons/timelines; fail-closed allowlisted recipes; unique scoped
  targets; clean rest; reduced/no-GSAP zero; all repeated instances isolated;
  fixed 20-icon p95 16.90 ms.
- Static artifact: `build/diagram-core/m7-operations.png`, 84 cells, DPR 1,
  zero requests/animations, SHA256
  `b23cddc3d93cfb4a5c1b302326cd55e97f4e0e54c17bb9d5e69e85657688ac07`;
  deterministic SVG regenerated byte-for-byte.
- Recognition artifact: `build/diagram-core/m7-operations.recognition.png`,
  label-hidden/accent-off/grayscale/node-context, SHA256
  `10d50b0b9824c7f7eaeea6cb830321749b4675aa446c9a5abd58ab9ae5c436d4`.
- Visual verdict: Logs/Alert P2 findings repaired; final P0/P1/P2 zero. Debug
  48 px grayscale ambiguity retained as non-blocking P3.
- Known failures: R-M7-01 resolved; F-M7-01/F-M7-02/F-M7-03 repaired.
- Blocker class: none.
- Verdict: pass; M7 done and M8 mechanically runnable.
- Next action: select M8 and run final 56-icon acceptance.

## M8 Attempt 11 Start

- Milestone: M8
- Attempt: 11
- Preconditions: M7 independently closed with P0/P1/P2 at zero; task checker
  ready; M8 was the single runnable milestone.
- Action: mark M8 in progress before final acceptance generation/verification.
- Current result: final evidence pending.
- Next action: generate all-catalog surfaces and execute the declared final gate.

## Evidence E-M8-01

- Milestone: M8
- Attempt: 11
- Recorded at: 2026-07-18 03:20:57 CST
- Working directory: `/Users/coolbat/anidiagram/.worktrees/diagram-core-v1-phase-0-1`
- Command: `PYTHONPATH=src python3 -m unittest discover -s tests &&
  PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --review &&
  node --check runtime/anidiagram-runtime.js &&
  npm run verify:diagram-core-showcase && git diff --check`.
- Test result: 365/365; validator catalog/SVG/manifests/visual-review all 56,
  planned 0, errors 0, warnings 0; runtime syntax and diff clean.
- Browser: 56 icons/timelines; allowlisted fail-closed recipes; unique scoped
  targets; clean rest; reduced/no-GSAP zero; all repeated instances isolated;
  Database layers remain top > middle > bottom with x=0; root p95 16.70 ms over
  452 frames. Independent rerun p95 18.00 ms over 436 frames.
- Contract: 56 authored-rest presentations, all 56 catalog/manifests have empty
  states, SVG text count zero, no default runtime or approval promotion.
- Full static artifact: `build/diagram-core/final-56.png`, 672 cells (56 icons x
  3 sizes x 4 contexts), 17472 x 416, DPR 1, zero requests/animations, SHA256
  `3d4492faca92d2255c633fb0651a92cd39342e9a12ca184ad05c2e5b4ac05bf9`;
  second capture is byte-identical.
- Categorized artifacts: actors, ai-models, data-knowledge, files-content,
  network-interfaces, compute-runtime, development-delivery, and
  operations-observability; 672 cells total across eight reviewable surfaces.
- Independent visual verdict: P0=0, P1=0, P2=0, P3=9. P3 observations are Tool
  instrument/camera association, abstract LLM, Vector DB/server association,
  PDF/bound document, Code File/generic source/VCS, Document Store/office
  equipment, Webhook and Container 48 px noise, and Debug grayscale proximity.
- Local preview: `http://127.0.0.1:8765/gallery/diagram-core/showcase.html`;
  server returned 56 cards and retained both Agent ears.
- Delivery: local_only; no stage, commit, push, PR, merge, deploy, promotion, or
  worktree cleanup performed.
- Known failures: all prior failure/regression records repaired or resolved;
  no M8 blocker.
- Blocker class: none.
- Verdict: pass; M8 done. Stop for human visual acceptance.

## M8 Attempt 12 Start

- Milestone: M8
- Attempt: 12
- Recorded at: 2026-07-18 08:09:55 CST
- User finding F-M8-01: Search currently separates lens and handle during its
  showcase motion; requested choreography is one whole-magnifier shake and
  return, then a clockwise 360-degree center-cross rotation, while retaining
  the current two upper-right circle scale pulse.
- Scope: Search presentation contract, declarative recipe, generated showcase,
  and task evidence only; SVG geometry, manifest, catalog, states, other icon
  recipes, default renderer, approval, and delivery remain frozen.
- Action: reopen M8 before source changes and require RED before implementation.
- RED command: `PYTHONPATH=src python3 -m unittest
  tests.test_diagram_core_showcase.DiagramCoreShowcaseTests.test_search_showcase_keeps_the_magnifier_together_before_scan_and_dot_pulses`.
- RED result: expected failure at 2026-07-18 08:14:00 CST. Existing track order
  is lens, handle, scan, target, indicator; required order begins with one body
  track and contains no separate lens/handle tracks.
- Blocker class: repo_fixable.
- Next action: update the Search recipe and bounded full-turn validation, then
  regenerate the live showcase and run focused verification.

## Evidence E-M8-02

- Milestone: M8.
- Attempt: 12.
- Recorded at: 2026-07-18 08:20:20 CST.
- Working directory: `/Users/coolbat/anidiagram/.worktrees/diagram-core-v1-phase-0-1`.
- Repair: replace separate Search lens/handle tracks with one body shake that
  returns at 0.58 s; rotate scan clockwise through 180 then 360 degrees; start
  the existing target/indicator 1.45x scale pulses only after the full turn.
- Safety boundary: 360-degree declarative rotation is allowed only for the
  Search scan track; every other track retains the 14-degree cap. Runtime still
  restores the exact authored transform at `rest_at`.
- Final command: `PYTHONPATH=src python3 -m unittest discover -s tests &&
  PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --review &&
  node --check runtime/anidiagram-runtime.js && node --check
  scripts/verify_diagram_core_showcase_motion.mjs && npm run
  verify:diagram-core-showcase && git diff --check`.
- Result: 367/367 tests; validator catalog/SVG/manifests/visual-review all 56,
  planned 0, errors 0, warnings 0; runtime/verifier syntax and diff clean.
- Browser: 56/56 timelines; fail-closed allowlist, unique scoped targets, clean
  rest, reduced/no-GSAP zero, repeat isolation all pass; fixed 20-icon p95
  27.20 ms over 344 frames.
- Regression boundary: Search SVG and manifest hashes are unchanged; only its
  intentional presentation hash and generated showcase changed.
- Local preview: `http://127.0.0.1:8765/gallery/diagram-core/showcase.html`;
  HTTP server PID 51804 remains live.
- Delivery: local_only; no stage, commit, push, PR, merge, deploy, promotion, or
  cleanup performed.
- Known failures: F-M8-01 repaired; no repository blocker remains.
- Verdict: automated pass; M8 done and awaiting human visual acceptance.

## M8 Attempt 13 Start

- Milestone: M8.
- Attempt: 13.
- Recorded at: 2026-07-18 08:54:06 CST.
- User finding F-M8-02: Search's whole-body first stage should trace a small
  clockwise circle around the authored lens-center position and return, not use
  the current left/right translate-and-rotate wobble.
- Scope: Search body recipe, focused contract/hash, generated showcase, and task
  evidence only. Search SVG/manifest, scan full turn, target/indicator pulses,
  all other recipes, states, default renderer, approval, and delivery remain frozen.
- Action: reopen M8 before test or production changes and require focused RED.
- RED command: `PYTHONPATH=src python3 -m unittest
  tests.test_diagram_core_showcase.DiagramCoreShowcaseTests.test_search_showcase_traces_a_clockwise_whole_body_circle_before_scan_and_dot_pulses`.
- RED result: expected assertion failure at 2026-07-18 08:55:36 CST. Existing
  body offsets are four left/right x/rotate steps; required offsets form a
  clockwise ten-point whole-body circle and authored-rest return.
- Blocker class: repo_fixable.
- Next action: update only the Search body recipe and regenerate the showcase.

## Evidence E-M8-03

- Milestone: M8.
- Attempt: 13.
- Recorded at: 2026-07-18 08:58:56 CST.
- Working directory: `/Users/coolbat/anidiagram/.worktrees/diagram-core-v1-phase-0-1`.
- Repair: replace Search's first-stage left/right x/rotate wobble with one rigid
  body path through top, upper-right, right, lower-right, bottom, lower-left,
  left, upper-left, and top before returning to authored rest. The 4 px radius
  keeps the complete magnifier together and preserves its orientation.
- Frozen behavior: scan still rotates clockwise through 180/360 after body rest;
  target/indicator retain the prior 1.45x staggered scale pulse. SVG, manifest,
  states, other icon recipes, and default renderer are unchanged.
- Final command: `PYTHONPATH=src python3 -m unittest discover -s tests &&
  PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --review &&
  node --check runtime/anidiagram-runtime.js && node --check
  scripts/verify_diagram_core_showcase_motion.mjs && npm run
  verify:diagram-core-showcase && git diff --check`.
- Result: 367/367 tests; validator catalog/SVG/manifests/visual-review all 56,
  planned 0, errors 0, warnings 0; runtime/verifier syntax and diff clean.
- Browser: all ten Search body samples matched the clockwise circular contract;
  body rotation stayed zero and lens/handle owned no independent transform.
  All 56 timelines, rest/fallback/repeat isolation gates passed; fixed 20-icon
  p95 27.10 ms over 349 frames.
- Regression boundary: Search SVG and manifest hashes remain unchanged; only
  its intentional presentation hash, generated showcase, path contract, and
  browser verifier evidence changed.
- Local preview: `http://127.0.0.1:8765/gallery/diagram-core/showcase.html`.
- Delivery: local_only; no stage, commit, push, PR, merge, deploy, promotion, or
  cleanup performed.
- Known failures: F-M8-02 repaired; no repository blocker remains.
- Verdict: automated pass; M8 done and awaiting human visual acceptance.
