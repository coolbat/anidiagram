# Executable Milestone Queue

## Milestone M0: Establish scoped baseline
Status: done
Priority: P0
Dependencies: none
Scope: Complete roadmap Task 1 by recording the dirty-worktree boundary, current branch and files, and a fresh baseline validation without changing product behavior.
Acceptance: The approved implementation can proceed on the current feature branch with a documented scoped ledger, no truth-surface conflict, and a passing baseline test suite.
Validation: PYTHONPATH=src python3 -m unittest discover -s tests && node --check runtime/anidiagram-runtime.js && git diff --check
Stop conditions: Stop before resetting, cleaning, reverting, broadly staging, or copying the uncommitted baseline into another worktree.
Evidence: 2026-07-13 11:27:08 CST; 64 unittest tests OK; runtime syntax exit 0; git diff check exit 0; branch codex/illustrated-character-v1; scoped ledger in Documentation.md

## Milestone M1: Complete Motion Coordination v1.1
Status: done
Priority: P0
Dependencies: M0
Scope: Complete roadmap Tasks 2-6: add failing mode/stage tests, implement real Readable behavior, simplify edge flow, make title sweep entry-only, and restrain character-theme group/node frames.
Acceptance: Expressive, Readable, Off, and reduced-motion contracts pass unit and browser tests while the approved 13 character timelines retain their frozen timing and canonical rest state.
Validation: PYTHONPATH=src python3 -m unittest discover -s tests && node --check runtime/anidiagram-runtime.js && node scripts/verify_character_motion_rest.mjs outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html && node scripts/verify_character_reduced_motion.mjs outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html 13 && node scripts/verify_stage_motion_modes.mjs outputs/illustrated-character-v1-flow/illustrated-character-v1-flow.html
Stop conditions: Stop before changing character geometry, semantic actions, the ambient runtime ownership model, or adding a third-party runtime dependency.
Evidence: 2026-07-13 11:36:12 CST; 66 unittest tests OK; character rest 13/13; reduced motion 13/13 and 8/8; stage modes Expressive-Readable-Off-Expressive verified; default/deep-tech/teaching screenshots reviewed; git diff check exit 0

## Milestone M2: Complete catalog and theme rollout
Status: done
Priority: P1
Dependencies: M1
Scope: Complete roadmap Tasks 7-10: freeze Character v1 in the motion catalog, support Deep Tech and Teaching Sketch Character, generate a three-theme comparison, and record compatibility decisions for five additional bundled themes.
Acceptance: Catalog and comparison surfaces accurately represent Character v1 and legacy v2, supported themes render clean artifacts, and candidate theme decisions are documented without forking icon geometry.
Validation: PYTHONPATH=src python3 -m unittest discover -s tests && PYTHONPATH=src python3 scripts/build_showcase.py --quality && PYTHONPATH=src python3 -m unittest tests.test_showcase_gallery
Stop conditions: Stop before promoting an additional theme without recorded evidence or altering shared character geometry for a theme-specific variant.
Evidence: 2026-07-13 11:46:34 CST; 69 unittest tests OK; showcase build OK with 25 runtime performances and 3 character themes; 27 demo assets clean; 25/25 demo manifests match icon systems; 5/5 candidate quality reports clean; 3/3 theme stage and reduced-motion browser checks passed

## Milestone M3: Migrate examples and rebuild gallery
Status: done
Priority: P1
Dependencies: M2
Scope: Complete roadmap Tasks 11-12 by migrating the named representative examples and rebuilding the gallery with explicit default and legacy icon-system labels.
Acceptance: Representative examples and gallery pages are readable at rest and in motion, have clean quality outputs, deterministic manifests, and no unintended broken links or generated churn.
Validation: PYTHONPATH=src python3 scripts/build_showcase.py --quality && PYTHONPATH=src python3 -m unittest discover -s tests && git diff --check
Stop conditions: Stop before overwriting unrelated generated assets or removing explicit legacy demonstrations.
Evidence: 2026-07-13 12:02:32 CST; 71 unittest tests OK; six representative HTML pages passed Expressive-Readable-Off-Expressive browser verification; showcase rebuilt with 12 styles, 14 layouts, 25 performances, and 3 character themes; gallery local-link audit and git diff check passed

## Milestone M4: Complete export, documentation, and final verification
Status: done
Priority: P1
Dependencies: M3
Scope: Complete roadmap Tasks 13-15: verify the supported export matrix, synchronize English and Chinese documentation, check all roadmap boxes, and produce a scoped version-control handoff without publishing.
Acceptance: Supported outputs have fresh renderer/status/quality evidence, documentation matches shipped behavior, all roadmap acceptance items are accounted for, and final full verification passes.
Validation: PYTHONPATH=src python3 -m unittest discover -s tests && node --check runtime/anidiagram-runtime.js && node scripts/verify_character_motion_rest.mjs outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html && node scripts/verify_character_reduced_motion.mjs outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html 13 && node scripts/verify_stage_motion_modes.mjs outputs/illustrated-character-v1-flow/illustrated-character-v1-flow.html && PYTHONPATH=src python3 scripts/build_showcase.py --quality && git diff --check
Stop conditions: Stop before deploy, publish, push, merge, PR creation, secret changes, destructive cleanup, or claiming unsupported optional exports as written.
Evidence: 2026-07-13 12:11:50 CST; 72 unittest tests OK; runtime and stage verifier syntax OK; character rest 13/13; reduced motion 13/13 and 8/8; stage modes verified; showcase 12 styles/14 layouts/25 performances/3 themes; light and dark 10-format matrices written with 24/24 distinct animated frames; clean quality and diff checks

## Queue Notes

- The 15 detailed tasks and four visual checkpoints remain defined in the
  approved roadmap; these five milestones are only the resumable execution
  queue.
- A `done` milestone requires fresh, non-pending evidence.
- Downstream milestones become `runnable` mechanically only after their declared
  dependency is `done` with evidence.
