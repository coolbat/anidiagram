# Execution Rules

## Selected Milestone

- Milestone: M0
- Approved scope boundary: Current repository files needed by the approved
  roadmap; preserve unrelated dirty changes and use only the current feature
  branch.
- Required validation gate: Use the exact `Validation:` command from the active
  milestone in `Plan.md`.
- Stop conditions: Use the active milestone's stop conditions plus all forbidden
  actions in `Prompt.md`.

## Decision Rules

- Resume the single valid `in_progress` milestone before selecting runnable work.
- Mark the selected milestone `in_progress` in `Plan.md` before modifying
  implementation files.
- Use test-driven development for every behavior change: failing test, observed
  expected failure, minimal implementation, passing focused and regression tests.
- Repair a failed gate only within approved scope. Record and classify a blocker
  before advancing.
- Continue independent runnable work only after synchronizing `Plan.md`,
  `Documentation.md`, `docs/agent-loop-state.md`, and
  `docs/release-evidence.md`.
- A human visual checkpoint may be satisfied by local browser inspection plus
  deterministic browser verifiers because the user explicitly requested every
  roadmap task be completed in this run.
- Stop when no safe runnable milestone remains. Do not create scope to use
  available time.

## Attempt Record

### Attempt 1

- Selected milestone: M0
- Changed assumptions: current dirty feature branch used as approved single writer.
- Action: baseline scope and validation.
- Command or observation: full unit, runtime syntax, and diff checks.
- Result: pass; 64 tests.
- Known failure: none.
- Blocker class: none.
- Next action: M1.
- Synchronized status: Plan.md=M0 done; Documentation.md=Attempt 1; agent-loop-state.md=Attempt 1; release-evidence.md=E-M0-01.

### Attempt 2

- Selected milestone: M1
- Changed assumptions: SVG particle filters are unsafe for dynamic mode switching in Chromium.
- Action: TDD implementation of stage modes, one-packet edge rhythm, title entry, canonical Off, and filter-free runtime packets.
- Command or observation: full M1 gate plus browser screenshots and mode verifier.
- Result: pass; 66 tests and all browser checks.
- Known failure: initial expected RED test; black filter-compositor artifact; one corrected screenshot command syntax error.
- Blocker class: repo_fixable; repaired within M1.
- Next action: M2 catalog and themes.
- Synchronized status: Plan.md=M1 done, M2 runnable; Documentation.md=Attempt 2; agent-loop-state.md=Attempt 2; release-evidence.md=E-M1-01.

### Attempt 3

- Selected milestone: M2
- Changed assumptions: legacy v2 demos require an explicit semantic-line icon system; gallery quality writers had drifted to an obsolete exporter signature.
- Action: froze Character v1 catalog, separated legacy demos, generated theme comparison and candidate evidence, and repaired quality-writer calls by TDD.
- Command or observation: M2 gate plus manifest-system audit and nine browser/quality theme checks.
- Result: pass; 69 tests, 25 performance demos, 3 supported themes, 5 candidate decisions.
- Known failure: F-M2-01 old `write_quality` call signature, repaired.
- Blocker class: repo_fixable; repaired.
- Next action: M3 representative examples and gallery rebuild.
- Synchronized status: Plan.md=M2 done, M3 runnable; Documentation.md=Attempt 3; agent-loop-state.md=Attempt 3; release-evidence.md=E-M2-01.
