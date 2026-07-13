# Frozen Goal Contract

## Background

AniDiagram already contains an uncommitted `illustrated-character-v1` baseline
on branch `codex/illustrated-character-v1`: 13 clean-room semantic icons,
character-local GSAP performances, two theme trials, examples, and browser
verifiers. The approved follow-on roadmap is
`docs/superpowers/plans/2026-07-11-illustrated-character-motion-rollout-roadmap.md`.

## Goal

Complete all fifteen tasks in the approved roadmap and demonstrate, with fresh
automated and browser evidence, that motion coordination, mode behavior, theme
rollout, representative examples, the gallery, and the supported export matrix
meet the roadmap acceptance criteria.

## Non-goals

- Do not add timeline, choreographer, event-driven, state-machine, interactive,
  or hybrid runtime scheduling.
- Do not redesign the approved 13 character drawings or their semantic actions.
- Do not import third-party icon code, runtime packages, or visual assets.
- Do not deploy, publish, merge, push, or open a pull request.

## Deliverables

- Motion Coordination v1.1 implementation and browser verification.
- Character v1 motion catalog and three-theme comparison surface.
- Representative example migration and deterministic gallery rebuild.
- Supported export-matrix evidence and synchronized English/Chinese docs.
- Updated roadmap, execution state, and release evidence.

## Constraints

- Preserve existing unrelated dirty-worktree changes.
- Use the current `codex/illustrated-character-v1` branch as the only write
  surface because the approved baseline is uncommitted and cannot be reproduced
  safely in a clean worktree.
- Use test-driven development for behavior changes.
- Preserve explicit legacy `illustrated-v1` and `semantic-line-v1` behavior.
- Keep HTML runtime ownership GSAP-only and standalone SVG fallback ownership
  SMIL/static-only; do not mix them on the same runtime stage.

## Done Conditions

- All roadmap Tasks 1-15 and Checkpoints A-D are checked with fresh evidence.
- Full unit tests, runtime syntax checks, character and stage browser verifiers,
  gallery generation/tests, export checks, quality reports, and `git diff
  --check` pass from the final source state.
- Expressive, Readable, Off, and operating-system reduced-motion behavior are
  observably distinct and conform to the approved contract.
- No unrelated worktree changes are reverted or staged.

## Human-owned Decisions

- Deployment, publishing, pushing, merging, public release, and pull requests.
- Any product decision that changes the approved character visuals or runtime
  scheduling model.
- Approval of any theme beyond the three specified comparison themes.

## Forbidden Actions

- Do not deploy, publish, merge, send external messages, alter secrets, or make
  billing, auth, permission, legal, or destructive data changes without explicit
  approval.
- Do not expand scope, replace a missing decision, or invent work to consume
  time.
- Do not reset, clean, discard, or broadly stage the current dirty worktree.

## Approved Assumptions

- The request to complete every roadmap task authorizes implementation through
  its four checkpoints using automated and local browser evidence.
- Existing user-visible character timing (`0.8 s` repeat gap, `0.44 s` breath,
  `1.012` scale) is frozen.
- Optional export tools may report an explicit skipped state when genuinely
  unavailable; mandatory source, HTML, SVG, browser, and quality gates may not.
