# Diagram Core v1 Full Catalog Milestone Queue

## Milestone M0: Freeze batches and establish the approved baseline
Status: done
Priority: P0
Dependencies: none
Scope: Replace stale long-horizon control surfaces with the approved 52-icon expansion contract, freeze the 10-plus-42 batch inventory, preserve the four approved benchmark changes, and record a fresh baseline.
Acceptance: The task checker reports ready on the isolated worktree; exact batch membership totals 52 remaining icons; current four-icon showcase, full tests, syntax, and diff checks pass without changing product behavior.
Validation: python3 /Users/coolbat/long-horizon-task-skill/skills/long-horizon-task/scripts/check_task_contract.py --project /Users/coolbat/anidiagram/.worktrees/diagram-core-v1-phase-0-1 --json && PYTHONPATH=src python3 -m unittest discover -s tests && node --check runtime/anidiagram-runtime.js && npm run verify:diagram-core-showcase && git diff --check
Stop conditions: Stop before asset implementation if the checker is not ready, batch totals are not exactly 52, the current worktree is not the declared isolated writer, or the benchmark baseline fails.
Evidence: E-M0-01 at 2026-07-17 23:35:30 CST; task checker ready; exact 52-icon inventory; 306/306 tests; runtime syntax; four-icon browser verifier; isolated branch/worktree and diff checks passed

## Milestone M1: Implement the 10-icon legacy compatibility batch
Status: done
Priority: P0
Dependencies: M0
Scope: Implement cloud, file, folder, memory, operator, output, search, shield, token, and tool as two five-icon implementation slices with canonical SVGs, manifests, catalog capabilities, and differentiated showcase performances.
Acceptance: All 10 assets follow the approved family style, preserve their existing DiagramScript ids without changing the default renderer, remain visual-review with empty states, pass static and motion gates, and have an approved internal review report.
Validation: PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --review && PYTHONPATH=src python3 -m unittest tests.test_diagram_core_catalog tests.test_diagram_core_assets tests.test_diagram_core_adapter tests.test_diagram_core_showcase tests.test_diagram_core_m1_compat_slice_one tests.test_diagram_core_m1_compat_slice_two && node --check runtime/anidiagram-runtime.js && npm run verify:diagram-core-showcase && git diff --check
Stop conditions: Stop before changing legacy validity/default routing, adding semantic states, promoting approval, or accepting a generic fallback as an implemented icon.
Evidence: E-M1-01 at 2026-07-18 00:16:12 CST; 14 visual-review assets and 42 planned entries; 14 canonical SVGs/manifests; exact 152/152 milestone tests and 328/328 full tests; 14 isolated browser timelines at 16.60 ms p95; two deterministic 60-cell static review matrices; independent P1/P2 findings repaired

## Milestone M2: Expansion batch A - actors and model cores
Status: done
Priority: P1
Dependencies: M1
Scope: Implement user, developer, agent-team, assistant, human-reviewer, ai-model, and llm.
Acceptance: Seven distinct silhouettes and performances pass 48 px recognition, semantic Part, reset, fallback, and batch review gates without modifying the approved Agent benchmark.
Validation: PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --review && PYTHONPATH=src python3 -m unittest tests.test_diagram_core_catalog tests.test_diagram_core_assets tests.test_diagram_core_adapter tests.test_diagram_core_showcase tests.test_diagram_core_m2_actor_model_batch && npm run verify:diagram-core-showcase && git diff --check
Stop conditions: Stop before introducing portrait realism, text-dependent identity, copied character geometry, semantic states, or benchmark regressions.
Evidence: E-M2-01 at 2026-07-18 00:41:27 CST; 21 visual-review and 35 planned; 21 SVGs/manifests; exact 147/147 milestone tests and 334/334 full tests; 21 isolated browser timelines at 27.00 ms p95; deterministic 84-cell static matrix; independent visual P0/P1/P2 at zero

## Milestone M3: Expansion batch B - reasoning and knowledge systems
Status: done
Priority: P1
Dependencies: M2
Scope: Implement neural-network, reasoning, embedding, vector-database, data-warehouse, knowledge-base, and dataset.
Acceptance: Seven icons remain distinguishable from Database and from one another at 48 px, expose stable meaningful Parts, and pass all batch static/motion gates and internal review.
Validation: PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --review && PYTHONPATH=src python3 -m unittest tests.test_diagram_core_catalog tests.test_diagram_core_assets tests.test_diagram_core_adapter tests.test_diagram_core_showcase tests.test_diagram_core_m3_reasoning_knowledge_batch && npm run verify:diagram-core-showcase && git diff --check
Stop conditions: Stop before adding dense node graphs, anonymous paths, microtext, semantic states, or a second storage geometry source.
Evidence: E-M3-01 at 2026-07-18 01:09:55 CST; 28 visual-review and 28 planned; 28 SVGs/manifests; exact 147/147 milestone tests and 340/340 full tests; 28 isolated browser timelines at 26.80 ms p95; deterministic 84-cell matrix; independent visual P0/P1/P2 at zero

## Milestone M4: Expansion batch C - datasets and content files
Status: done
Priority: P1
Dependencies: M3
Scope: Implement document-store, document, pdf, image, audio, video, and code-file using the shared file-shell visual skeleton where applicable.
Acceptance: The six file variants share family proportions but remain recognizable without labels; Dataset remains a node rather than a file alias; all seven pass batch gates and internal review.
Validation: PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --review && PYTHONPATH=src python3 -m unittest tests.test_diagram_core_catalog tests.test_diagram_core_assets tests.test_diagram_core_adapter tests.test_diagram_core_showcase tests.test_diagram_core_m4_content_file_batch && npm run verify:diagram-core-showcase && git diff --check
Stop conditions: Stop before embedding text, raster previews, external symbols, or collapsing distinct catalog semantics into aliases.
Evidence: E-M4-01 at 2026-07-18 01:41:20 CST; 35 visual-review and 21 planned; 35 SVGs/manifests; exact 147/147 milestone tests and 346/346 full tests; 35 isolated browser timelines at 27.10 ms p95; deterministic 84-cell matrix; Document Store P2 repaired; independent visual P0/P1/P2 at zero

## Milestone M5: Expansion batch D - network and runtime distribution
Status: done
Priority: P1
Dependencies: M4
Scope: Implement webhook, http-request, gateway, load-balancer, message-queue, server-cluster, and container.
Acceptance: Interfaces and compute nodes remain distinct from API and Server, do not own diagram connection anchors, and pass batch static/motion/fallback/performance gates and internal review.
Validation: PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --review && PYTHONPATH=src python3 -m unittest tests.test_diagram_core_catalog tests.test_diagram_core_assets tests.test_diagram_core_adapter tests.test_diagram_core_showcase tests.test_diagram_core_m5_network_runtime_batch && npm run verify:diagram-core-showcase && git diff --check
Stop conditions: Stop before adding connection anchors to manifests, moving node geometry, semantic states, or unbounded queue/cluster elements.
Evidence: E-M5-01 at 2026-07-18 02:04:26 CST; 42 visual-review and 14 planned; 42 SVGs/manifests; exact 147/147 milestone tests and 352/352 full tests; 42 isolated browser timelines at 16.70 ms p95; deterministic 84-cell matrix; independent visual P0/P1/P2 at zero

## Milestone M6: Expansion batch E - compute and delivery flow
Status: done
Priority: P1
Dependencies: M5
Scope: Implement function, edge-node, source-code, git-repository, branch, pull-request, and deployment.
Acceptance: Seven icons communicate trigger, edge, code, history, branch, review/merge, and pipeline semantics through silhouette and meaningful motion, with clean batch evidence and review.
Validation: PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --review && PYTHONPATH=src python3 -m unittest tests.test_diagram_core_catalog tests.test_diagram_core_assets tests.test_diagram_core_adapter tests.test_diagram_core_showcase tests.test_diagram_core_m6_compute_delivery_batch && npm run verify:diagram-core-showcase && git diff --check
Stop conditions: Stop before using brand marks, text labels, semantic states, or turning line payloads into node-owned connectors.
Evidence: E-M6-01 at 2026-07-18 02:31:09 CST; 49 visual-review and 7 planned; 49 SVGs/manifests; exact 148/148 milestone tests and 359/359 full tests; 49 isolated browser timelines at 17.40 ms p95 after scale-safe JSON verifier transport; deterministic 84-cell matrix; visual P0/P1/P2 at zero

## Milestone M7: Expansion batch F - deployment and observability
Status: done
Priority: P1
Dependencies: M6
Scope: Implement ci-cd, task, scheduler, monitoring, logs, alert, and debug.
Acceptance: Seven operations icons remain visually distinct at rest and in motion, use non-text semantic cues, settle cleanly, and pass batch static/motion/performance gates and internal review.
Validation: PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --review && PYTHONPATH=src python3 -m unittest tests.test_diagram_core_catalog tests.test_diagram_core_assets tests.test_diagram_core_adapter tests.test_diagram_core_showcase tests.test_diagram_core_m7_operations_batch && npm run verify:diagram-core-showcase && git diff --check
Stop conditions: Stop before representing Phase 2 lifecycle states, relying on color alone, or using alert/error marks as catalog state capabilities.
Evidence: E-M7-01 at 2026-07-18 03:13:18 CST; 56 visual-review and 0 planned; 56 SVGs/manifests; exact 148/148 milestone tests and 365/365 full tests; 56 isolated browser timelines at 16.90 ms p95; deterministic 84-cell and four-mode recognition surfaces; Logs/Alert P2 spacing repaired; independent visual P0/P1/P2 at zero

## Milestone M8: Build the 56-icon acceptance surface and run final verification
Status: done
Priority: P0
Dependencies: M7
Scope: Generate categorized static/contact-sheet and live showcase surfaces for all 56 icons; run full static, runtime, fallback, determinism, repeated-instance, accessibility, performance, and regression gates; close independent review findings.
Acceptance: Exactly 56 assets/manifests/presentations render without fallback; all automated and browser gates pass from the final tree; no P0/P1/P2 review findings remain; the task stops at human visual acceptance.
Validation: PYTHONPATH=src python3 -m unittest discover -s tests && PYTHONPATH=src python3 scripts/validate_diagram_core_assets.py --review && node --check runtime/anidiagram-runtime.js && npm run verify:diagram-core-showcase && git diff --check
Stop conditions: Stop before promotion, default-system switching, push/PR/merge/deploy, worktree cleanup, or claiming human visual approval.
Evidence: E-M8-03 at 2026-07-18 08:58:56 CST; Search whole-body clockwise circular wobble and generated live page; 367/367 tests; validator 56/56 with zero errors/warnings; browser verified 10 circular samples and 56/56 timelines at 27.10 ms p95; clean rest, fallbacks, instance isolation, syntax, and diff checks passed; awaiting human visual acceptance

## Frozen Batch Inventory

- Compatibility slice 1: operator, memory, tool, token, search.
- Compatibility slice 2: file, folder, output, shield, cloud.
- Batch A: user, developer, agent-team, assistant, human-reviewer, ai-model, llm.
- Batch B: neural-network, reasoning, embedding, vector-database, data-warehouse, knowledge-base, dataset.
- Batch C: document-store, document, pdf, image, audio, video, code-file.
- Batch D: webhook, http-request, gateway, load-balancer, message-queue, server-cluster, container.
- Batch E: function, edge-node, source-code, git-repository, branch, pull-request, deployment.
- Batch F: ci-cd, task, scheduler, monitoring, logs, alert, debug.
