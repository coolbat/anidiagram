# Illustrated 2.5 Full Expansion Contract

## Objective

P3 and P4 complete the two missing dimensions of the Illustrated system:

- P3 adapts Illustrated colors to all 13 public templates without changing
  icon geometry, SVG part ids, semantic roles, or motion behavior.
- P4 expands the current 20-icon system to the same 56 semantic icons exposed
  by Diagram Core v1.

The target implementation version is `2.5.0`. This is an additive release: the
stable public id remains `illustrated`, and the frozen 2.0.0 through 2.4.0
releases and snapshots remain unchanged.

## P3: full template adaptation

The public template set is the exact 13-style catalog in
`styles/catalog.json`. The review candidate is
`assets/illustrated/reviews/template-matrix-2.5.0-candidate.json` and the
generated proof is
`outputs/illustrated-template-matrix-2.5/illustrated-template-matrix.html`.

Acceptance requires:

- an initial 13/13 x 20/20 candidate proof, followed by the final 13 x 56
  approved matrix with 728 rendered instances;
- complete overrides for all approved Illustrated color tokens;
- no geometry or semantic-structure override;
- at least 12 distinct colors in every template palette;
- identical SVG structure for every icon across all templates;
- explicit human visual acceptance before candidate palettes are copied into
  public style files;
- a final 13 x 56 template proof after P4 completes.

`deep-tech` retains its already approved ivory-outline palette. The other 12
template mappings begin at `visual-review` and cannot be marked `approved`
solely from automated checks.

## P4: 36-icon expansion

The missing icons are partitioned by semantic family. Every batch contains six
icons and must complete static review before motion work begins.

| Batch | Semantic family | Icons |
| --- | --- | --- |
| 5 | People and agent intelligence | `developer`, `agent-team`, `assistant`, `human-reviewer`, `llm`, `reasoning` |
| 6 | AI and data | `neural-network`, `embedding`, `token`, `data-warehouse`, `document-store`, `dataset` |
| 7 | Content and media | `document`, `pdf`, `image`, `audio`, `video`, `code-file` |
| 8 | Network and compute | `webhook`, `http-request`, `load-balancer`, `server-cluster`, `function`, `edge-node` |
| 9 | Source and delivery | `source-code`, `git-repository`, `branch`, `pull-request`, `ci-cd`, `deployment` |
| 10 | Runtime and operations | `task`, `scheduler`, `monitoring`, `logs`, `alert`, `debug` |

## Static visual rules

- Use the existing 120 x 120 view box, 3.4 default stroke width, round caps,
  and round joins.
- Preserve the friendly object-illustration language of the approved 20 icons.
- Put the semantic object inside the main silhouette. Use zero to two external
  accessories only when they improve recognition.
- Do not repeat checkmarks, arrows, triangles, sparkles, or the same peripheral
  badge as a generic completion decoration. These shapes are reserved for
  their actual meanings.
- Prefer domain-specific parts: review sheet, vector field, media waveform,
  repository tree, deployment rail, monitoring trace, or debug probe.
- Each icon needs a stable semantic role, two or three supported actions, and
  unique stable part names suitable for motion.
- Review each batch at 64 px, 96 px, and 120 px in a light and dark template.

## Motion rules

- Motion starts only after static visual approval for that batch.
- Every icon receives one semantic `showcase-v1` performance with a clear
  prepare, action, and settle sequence.
- The canonical rest pose must restore x/y/rotation/scale and source opacity.
- Reduced motion must render the same canonical rest pose without looping.
- Movement should be expressive enough for the default showcase while keeping
  the main silhouette readable throughout the cycle.
- The final public motion contract must cover exactly 56 icons with no missing
  or duplicate performance ids.

## Gates

Each static batch requires focused registry/render tests, a clean quality
report, unique SVG ids, and human visual approval. Each motion batch additionally
requires runtime syntax, rest-pose verification, reduced-motion verification,
and Expressive/Readable/Off mode checks.

The release gate requires:

- exact equality between the 56 Diagram Core ids and 56 Illustrated ids;
- 13 x 56 template coverage with unchanged icon structure;
- a 56-icon public showcase with automatic `showcase-v1` motion;
- at least one real architecture case with nonzero Edge Motion v1 coverage;
- the full Python suite and Diagram Core 56/56 strict validation;
- browser-owned SVG, HTML, PNG, WebP, GIF, APNG, MP4, PDF, Lottie, and quality
  evidence with zero issues;
- immutable 2.5.0 catalog, token, motion, acceptance, and release records.

## Release result

Illustrated 2.5.0 completed this contract on 2026-07-24:

- 56/56 public semantic icons and 56/56 automatic
  `illustrated-performance-v6` performances;
- 13/13 public templates and 728/728 rendered template instances;
- convention alignment approved for the 12 icons that have broadly recognized
  external visual conventions;
- a 13-node, 13-edge Governed RAG production case using Edge Motion v1;
- browser rest, reduced-motion, and Expressive/Readable/Off gates passed;
- two public systems x ten export formats passed at browser 24 FPS, 108 frames,
  and 2x scale, with at least three visible states per icon and zero issues.

The formal local export ledger is
`outputs/release-evidence/icon-systems/public-icon-system-export-evidence.json`
(SHA-256
`6b7f446cbb4941d7b8f1d3135285fc151871ab2c3c284178fa92fb8047b662cb`).
