# Diagram Core Phase 1 Approval Record

## Checkpoint A — Agent family baseline

- Decision: approved
- Reviewer: coolbat
- Approval date: 2026-07-16
- System: `diagram-core-v1`
- Asset status after approval: `visual-review`
- Reviewed artifact: `assets/diagram-core/previews/agent-contact-sheet.svg`
- Review page: `gallery/diagram-core/agent-review.html`
- Candidate commit: `0ab0f07c9df3be717f825987c89e9d04e464cef7`
- User-requested ear-cap revision: `39d972b8fd0c76c8fb2a5acf2b0d319a3d9a0448`

### Reviewed digests

| Artifact | SHA-256 |
| --- | --- |
| `assets/diagram-core/icons/agent.svg` | `3b869f780e44a016063af79ff8c71b5f41d4b9711ec7b27e1c60be6c1e447eed` |
| `assets/diagram-core/manifests/agent.json` | `d2d29272b88cbd79b7d98151315271a77a5ae1b9bf3d3fad71ddad9af12b99eb` |
| `assets/diagram-core/tokens.css` | `4e88e990a1093451e002d9f14f47c1a86ebab0fa90f7e629ba8a49b74a3c5269` |
| `assets/diagram-core/previews/agent-contact-sheet.svg` | `0ae04b7cbf269139115f1f591fa6a26fdf98b41f9e70bf70b3f539626c10feb8` |
| `gallery/diagram-core/agent-review.html` | `b8452417565d1692072accecb8c8d987f291f3f3940671a041c2a9ab65c6a952` |

### Human review result

The reviewer accepted the Agent silhouette, visual weight, face readability,
four review contexts, six geometric state marks, accent-off recognition, and
grayscale recognition after requesting two attached side ear caps. The ear
caps are private `shell` details rather than public parts, ports, anchors, or
motion targets.

### Scope of this approval

Checkpoint A authorizes Database, API, and Server to use Agent as the static
family baseline. It does not:

- promote Agent or any other benchmark to `approved`;
- add Server to DiagramScript validation;
- change `DEFAULT_ICON_SYSTEM` from `illustrated-character-v1`;
- authorize Phase 2 motion performances or runtime animation.

Final lifecycle promotion remains gated by Checkpoint B and the approved
four-icon contact sheet plus locked browser baseline.

## 2026-07-17 Scope Amendment — Showcase presentation revision

- Decision: approved product-scope change
- Reviewer: coolbat
- Effect: partially supersedes the state-mark portion of Checkpoint A and the
  unapproved 288-cell Checkpoint B candidate
- Public system version: unchanged (`diagram-core-v1` / Diagram Core v1.0)

The reviewer changed the first-release target after inspecting the six-state
matrix. The current release no longer implements `idle`, `active`, `processing`,
`success`, `warning`, or `error` icon variants. Those semantics are deferred
until Phase 2 defines the combined runtime-stage and execution-result flow.

Checkpoint A remains authoritative for:

- Agent silhouette and visual weight;
- the two attached side ear caps;
- face, antenna, core, outline, and family style;
- use of Agent as the visual baseline for Database, API, and Server.

Checkpoint A is superseded for:

- the six geometric state marks;
- any claim that benchmark manifests currently support six states;
- the old 72-cell Agent and 288-cell four-icon state matrices.

The replacement first-release review contract is:

```text
48-cell authored-rest matrix
+ one showcase Presentation Profile
+ four icon-specific showcase presentation performances
+ no-GSAP and reduced-motion authored-rest fallback
```

All four assets remain `visual-review`. The new Checkpoint B requires explicit
human approval of both the authored-rest family and the live showcase motion
before asset promotion, Server validation, or later renderer integration.
