# Prompt to Diagram Flow

AniDiagram now treats natural-language input, LLM summarization, freeform
layout, rendering, and quality checks as one staged product flow.

## Pipeline

1. **User brief**: raw user text, documents, notes, or a CLI `--brief` file.
2. **DiagramPlan v0.1**: a structured semantic plan that an LLM can produce or
   the local deterministic planner can scaffold.
3. **Emphasis and motion budget**: choose the main animated paths, calm
   supporting paths, and a `motion_policy` budget before concrete rendering.
4. **Layout strategy**: a named compiler target. The first implementation is
   `explainer-board`.
5. **Freeform DiagramScript v0.3**: concrete groups, nodes, coordinates, edge
   routes, semantic icons, shapes, and motion effects.
6. **Renderer/exporters**: SVG, HTML, raster/video/interchange outputs.
7. **Quality report**: bounds, overlap, text-fit, explicit path collision, and
   motion-overload checks.

## What Was Missing

Before this layer, AniDiagram already had DiagramScript, preset templates,
styles, motion effects, exports, quality checks, and freeform coordinates. The
missing piece was the middle layer between "user asks for a complex diagram"
and "someone manually writes exact DiagramScript JSON."

That gap made complex diagrams depend too much on fixed templates. It also
forced a future LLM to either choose a preset too early or invent low-level JSON
without a stable product contract.

## What Exists Now

- `DiagramPlan v0.1` schema:
  [schemas/diagram-plan-v0.1.schema.json](../schemas/diagram-plan-v0.1.schema.json)
- Local brief planner:
  `anidiagram.planner.brief_to_plan`
- Freeform compiler:
  `anidiagram.planner.compile_plan`
- CLI inputs:
  `--brief <file>` and `--text "..."`
- Debug outputs:
  `--plan-out <file>` and `--spec-out <file>`
- First layout strategy:
  `explainer-board`
- New DiagramScript node shape:
  `node.shape = "decision"`
- Motion budget controls:
  `motion_policy.profile`, `max_active_flow_edges`, `max_particle_edges`,
  `particle_count_per_edge`, `max_active_pulse_nodes`, and
  `max_scanning_groups`

## LLM Integration Contract

The recommended order is:

1. Let the LLM summarize messy user input into DiagramPlan.
2. Let the LLM mark the few paths that deserve active flow and keep supporting
   paths calm.
3. Validate or inspect DiagramPlan.
4. Compile DiagramPlan into freeform DiagramScript with `motion_policy`.
5. Render and run quality checks.
6. If quality fails, revise the DiagramPlan, emphasis, budget, or layout
   strategy.

The LLM should not need to write SVG, animation markup, or every coordinate by
hand. It should decide meaning: sections, flow steps, side panels, feedback
paths, emphasis, style direction, and motion density. AniDiagram then owns the
layout grammar, budget clamping, and rendering behavior.

## Current Layout Strategy

`explainer-board` is for complex explanatory architecture and teaching diagrams
that do not fit a rigid preset. It uses:

- input strip near the top,
- large central work-loop panel,
- lower support panels for memory, guardrails, and tooling,
- explicit point-routed feedback paths,
- role-based semantic icons,
- focused motion defaults with only a few active flow paths.

This is intentionally not a template preset. It is a compiler target for a
semantic plan, and future strategies can be added without changing the brief or
LLM contract.

## Example

```bash
PYTHONPATH=src python3 -m anidiagram.cli \
  --brief examples/briefs/loop-engineering.txt \
  --style styles/sketch-board.json \
  --outdir outputs \
  --basename loop-engineering \
  --formats svg,html,quality \
  --plan-out outputs/loop-engineering.plan.json \
  --spec-out outputs/loop-engineering.diagram.json \
  --result outputs/loop-engineering.result.json
```

The generated spec is normal DiagramScript v0.3. It can be edited, checked into
examples, rendered with other styles, or used as fixture input.

## Next Extensions

- Add more layout strategies such as `systems-map`, `research-board`, and
  `architecture-wall`.
- Add DiagramPlan validators with friendlier issue messages.
- Add LLM prompt templates that target DiagramPlan v0.1 instead of raw SVG.
- Add LLM prompt templates that choose emphasis and motion budget explicitly.
- Add layout repair passes that respond to quality report issues.
