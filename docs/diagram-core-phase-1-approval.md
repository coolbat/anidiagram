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
