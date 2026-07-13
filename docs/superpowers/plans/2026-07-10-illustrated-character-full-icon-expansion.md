# Illustrated Character v1 Full Icon Expansion Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cover every valid DiagramScript semantic icon with a clean-room `illustrated-character-v1` object and a quiet, semantic GSAP performance.

**Architecture:** Extend the data-only character registry with the ten uncovered icons, then make that registry the single source of SVG part selectors for the character Motion Manifest branch. A dedicated 13-entry character performance mapping selects runtime behavior while the existing legacy icon systems and line fallback remain untouched. Browser tests verify the quiet resting state and reduced-motion behavior.

**Tech Stack:** Python 3, SVG strings, JSON DiagramScript, GSAP runtime JavaScript, Node Playwright, `unittest`.

---

## File structure

- `src/anidiagram/illustrated_character_icons.py` — normalized clean-room icon definitions and stable part names.
- `src/anidiagram/motion_manifest.py` — character performance IDs and registry-derived selector map.
- `runtime/anidiagram-runtime.js` — one guarded GSAP performer per character icon, plus exact rest behavior.
- `tests/test_render_svg.py` — registry/manifest/runtime source/example unit coverage.
- `scripts/verify_character_motion_rest.mjs` — browser-level rest-state verification for all icon timelines.
- `examples/illustrated-character-v1-icons.diagram.json` — all 13 icons, exactly once.
- `examples/illustrated-character-v1-flow.diagram.json` — covered-icon narrative flow without fallback text.
- `docs/diagram-script.md`, `docs/html-runtime.md`, `README.md`, `README.zh-CN.md` — full-coverage and performance documentation.

## Chunk 1: Registry and manifest contract

### Task 1: Add failing full-coverage registry and manifest tests

**Files:**
- Modify: `tests/test_render_svg.py:33-125`
- Test: `src/anidiagram/illustrated_character_icons.py`
- Test: `src/anidiagram/motion_manifest.py`

- [ ] **Step 1: Write failing tests for all schema icons**

Add imports for `KNOWN_ICONS`, `character_definition`, and
`CHARACTER_ICON_PERFORMANCES`. Add a gallery scene helper that creates one
node for each sorted icon. Add tests equivalent to:

```python
def test_character_registry_covers_every_schema_icon(self):
    self.assertEqual(KNOWN_ICONS, set(character_icon_ids()))
    for icon in KNOWN_ICONS:
        definition = character_definition(icon)
        self.assertIsNotNone(definition)
        self.assertEqual("root", definition.parts[0])
        self.assertEqual(len(definition.parts), len(set(definition.parts)))

def test_character_manifest_uses_registry_parts_as_the_single_source(self):
    scene = self._scene_with_icons(sorted(KNOWN_ICONS))
    html = render_html_runtime(scene, load_style(), runtime="gsap")
    manifest = self._manifest_from_html(html)
    self.assertEqual("illustrated-character-v1", manifest["icon_system"])
    self.assertEqual(set(KNOWN_ICONS), {entry["icon"] for entry in manifest["icons"]})
    for entry in manifest["icons"]:
        definition = character_definition(entry["icon"])
        self.assertEqual(set(definition.parts), set(entry["parts"]))
        self.assertEqual(CHARACTER_ICON_PERFORMANCES[entry["icon"]], entry["performance"])
        for selector in entry["parts"].values():
            self.assertEqual(1, html.count(f'id="{selector[1:]}"'))
```

Make `_scene_with_icons()` explicit about the runtime conditions it tests:
`motion.profile` is `expressive` and `motion.node.preset` is
`icon-performance`; do not rely on default motion behavior.

- [ ] **Step 2: Run the focused tests and confirm red**

Run:

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_render_svg.SvgRendererTest.test_character_registry_covers_every_schema_icon \
  tests.test_render_svg.SvgRendererTest.test_character_manifest_uses_registry_parts_as_the_single_source
```

Expected: FAIL because only three registry definitions and mappings exist.

### Task 2: Add ten data-only illustrated character definitions

**Files:**
- Modify: `src/anidiagram/illustrated_character_icons.py:32-85`
- Modify: `src/anidiagram/motion_manifest.py:34-143`
- Test: `tests/test_render_svg.py`

- [ ] **Step 1: Define normalized object primitives and stable parts**

Add `CharacterIconDefinition` entries matching the approved exact parts:

```python
"search": ("root", "lens", "scan", "marker", "spark"),
"tool": ("root", "bucket", "lid", "wrench", "spark"),
"api": ("root", "interface", "request", "receipt", "status"),
"memory": ("root", "back-card", "front-card", "bookmark", "key-line"),
"output": ("root", "envelope", "card", "check", "spark"),
"file": ("root", "page", "corner", "line-1", "line-2", "line-3", "dot"),
"folder": ("root", "folder", "tab", "sheet", "seal"),
"cloud": ("root", "cloud", "kite", "data-dot", "ready-light"),
"shield": ("root", "shell", "core", "scan", "check"),
"token": ("root", "shell", "core", "tick-left", "tick-right", "tick-top", "tick-bottom"),
```

Use only the existing palette tokens (`ink`, `paper`, `mint`, `lavender`,
`violet`, `peach`, `sky`, `teal`, `orange`, `sun`) and 100×100 primitives.
Do not add generic decoration with no semantic role.

- [ ] **Step 2: Add all 13 explicit character performance IDs**

Set `CHARACTER_ICON_PERFORMANCES` to the exact table in the approved design
spec, including the existing `agent`, `operator`, and `database` values. Keep
legacy `ICON_PERFORMANCE_V2` unchanged.

- [ ] **Step 3: Make the character manifest use registry parts**

In `build_motion_manifest`, resolve `character = character_definition(node.icon)`
for the character icon-system branch and set:

```python
if character is not None:
    part_names = character.parts
```

Use `PERFORMANCE_PARTS` only for legacy systems. Do not duplicate character
part tuples there. Keep `semantic_role` on character entries.

- [ ] **Step 4: Update default and legacy runtime regressions**

Change existing default-runtime tests that hard-code legacy `*-v2` IDs to use
`CHARACTER_ICON_PERFORMANCES` when the style omits `icon_system`. Preserve the
legacy assertions by explicitly merging `{"icon_system": "semantic-line-v1"}`
into their style fixture; this proves old v2 behavior is still available only
when requested.

- [ ] **Step 5: Run focused tests and full suite**

Run:

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_render_svg.SvgRendererTest.test_character_registry_covers_every_schema_icon \
  tests.test_render_svg.SvgRendererTest.test_character_manifest_uses_registry_parts_as_the_single_source
PYTHONPATH=src python3 -m unittest discover -s tests
```

Expected: PASS.

- [ ] **Step 6: Commit registry and manifest contract**

```bash
git add src/anidiagram/illustrated_character_icons.py src/anidiagram/motion_manifest.py tests/test_render_svg.py
git commit -m "feat: cover all illustrated character icons"
```

## Chunk 2: Runtime behavior and browser proof

### Task 3: Add failing runtime registration and canonical-rest tests

**Files:**
- Modify: `tests/test_render_svg.py`
- Create: `scripts/verify_character_motion_rest.mjs`
- Test: `runtime/anidiagram-runtime.js`

- [ ] **Step 1: Add source-level performance registration test**

Add a test that loops over `CHARACTER_ICON_PERFORMANCES.values()` and verifies
each ID maps to exactly one function in an explicit Python expectation table:

```python
CHARACTER_RUNTIME_CONTRACT = {
    "brain-think-pulse-v1": ("playBrainThinkPulse", ("brain-left", "brain-right", "chip", "signal", "spark")),
    # the other 12 entries mirror the approved complete performance contract
}
```

For each entry, extract that JavaScript function body from `function <name>` to
the next function declaration, assert its exact required-part literals,
`hasParts(parts, required)`, and `setInitial(parts, gsap)`, then assert the
dispatch object has the exact `"<performance>": <function>` entry. Do not use
a whole-file substring test.

- [ ] **Step 2: Add the browser rest-state verifier before runtime changes**

Create a Node Playwright script that accepts a generated HTML file, waits for
the runtime, then samples every character timeline at an explicit deterministic
rest time. Add a `CHARACTER_REST_AT` mapping in `motion_manifest.py`, serialize
each character entry's `rest_at`, and attach
`{ nodeId, performance, restAt }` metadata to the corresponding performer
timeline in `playIcon`. The verifier filters `window.__ANIDIAGRAM_TIMELINES__`
to timelines with this metadata (thereby excluding stage timelines), pauses each
one, seeks it to its own `restAt`, and then validates the matching icon's DOM.
It must exit nonzero unless every selector in that icon entry has a zero GSAP
animation delta and an opacity matching `data-rest-opacity`. It must compare
`gsap.getProperty(element, "x")`, `"y"`, `"rotation"`, `"scaleX"`, and
`"scaleY"` with canonical values (`0`, `0`, `0`, `1`, `1`) rather than require
`getComputedStyle(element).transform` to be identity: the root SVG group has a
permanent node-local SVG transform. Add the rest metadata to every character
primitive **and the root group** (source opacity defaults to `1`). The script
must close Chromium in `finally`.

Use this exact, nonzero `rest_at` contract (seconds):

```python
CHARACTER_REST_AT = {
    "agent": 1.50, "operator": 1.35, "database": 1.55,
    "search": 1.30, "tool": 1.40, "api": 1.35, "memory": 1.45,
    "output": 1.40, "file": 1.35, "folder": 1.35, "cloud": 1.40,
    "shield": 1.35, "token": 1.35,
}
```

Each performer uses its value as an explicit final `.set(...)` position,
restores all affected parts there, and adds a no-op `0.01 s` hold after it so
the first-cycle `duration()` is strictly greater than `rest_at`. Source and
browser tests assert every value is positive, `rest_at < timeline.duration()`,
and restoration occurs before the timeline's `repeatDelay`.

- [ ] **Step 3: Run source test and rest verifier to confirm red**

Run the source test and, after rendering the current gallery HTML, run:

```bash
node scripts/verify_character_motion_rest.mjs outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html
```

Expected: FAIL because the new performance IDs/functions and rest metadata do
not exist; the three current performers leave confirmation opacity dimmed.

### Task 4: Implement all character GSAP performances and exact rest behavior

**Files:**
- Modify: `runtime/anidiagram-runtime.js:426-769`
- Modify: `src/anidiagram/renderer_illustrated_character.py:26-62`
- Test: `tests/test_render_svg.py`
- Test: `scripts/verify_character_motion_rest.mjs`

- [ ] **Step 1: Serialize source resting opacity metadata**

Emit `data-rest-opacity="1"` on each character primitive and on the character
root group unless an element defines an explicit source opacity. This attribute
is verification metadata; it does not change visual output.

- [ ] **Step 2: Tighten existing three performances**

Change the final quiet tween in `playBrainThinkPulse`, `playOperatorTypeFocus`,
and `playBucketIngestConfirm` to restore all temporarily hidden confirmation
parts to opacity `1`, and zero `x`, `y`, `scale`, and `rotate` before the
timeline enters `repeatDelay`.

- [ ] **Step 3: Add ten guarded semantic performers**

Implement functions and dispatch entries exactly named by the design spec.
For each function:

```javascript
function playExample({ parts, gsap }) {
  const required = ["..."];
  if (!hasParts(parts, required)) return null;
  setInitial(parts, gsap);
  const tl = gsap.timeline({ repeat: -1, repeatDelay: CHARACTER_REPEAT_DELAY });
  // prepare → semantic action → confirmation
  // final tween restores opacity: 1 and x/y/scale/rotate to canonical rest
  return tl;
}
```

Use the exact actions in the approved table: lens scan, wrench action, signal
return, bookmark commit, envelope reveal, note writing, folder storage, cloud
uplink, guard scan, and token readiness. Do not add GSAP plugins.

- [ ] **Step 4: Attach per-icon rest metadata for browser verification**

After each character performer is created in `playIcon`, attach only
non-enumerable or private runtime metadata such as:

```javascript
tl.__anidiagramCharacter = {
  nodeId: iconConfig.node_id,
  performance: iconConfig.performance,
  restAt: iconConfig.rest_at,
};
```

The verifier uses this metadata to seek one icon timeline at a time. Do not
attach it to ambient stage timelines or legacy performances.

- [ ] **Step 5: Run runtime and browser verification**

Run:

```bash
node --check runtime/anidiagram-runtime.js
node --check scripts/verify_character_motion_rest.mjs
PYTHONPATH=src python3 -m unittest tests.test_render_svg.SvgRendererTest.test_all_character_runtime_performances_are_registered
node scripts/verify_character_motion_rest.mjs outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html
node scripts/verify_character_reduced_motion.mjs outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html 13
```

Expected: all commands exit 0.

- [ ] **Step 6: Commit runtime expansion**

```bash
git add runtime/anidiagram-runtime.js src/anidiagram/renderer_illustrated_character.py scripts/verify_character_motion_rest.mjs tests/test_render_svg.py
git commit -m "feat: animate all illustrated character icons"
```

## Chunk 3: Examples, docs, and end-to-end evidence

### Task 5: Make examples prove full coverage and no fallback

**Files:**
- Modify: `examples/illustrated-character-v1-icons.diagram.json`
- Modify: `examples/illustrated-character-v1-flow.diagram.json`
- Modify: `tests/test_render_svg.py`

- [ ] **Step 1: Write failing example coverage tests**

Add tests that compile both examples. Assert the gallery icon set equals
`KNOWN_ICONS`, its manifest has 13 entries, and its quality report has zero
errors/warnings. Assert the flow's quality report has zero fallback warnings
and its JSON text does not contain `fallback`.

- [ ] **Step 2: Run the focused tests and confirm red**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_render_svg.SvgRendererTest.test_illustrated_character_examples_cover_all_icons_without_fallback
```

Expected: FAIL because the gallery contains three icons and the flow contains
the explicit API fallback demonstration.

- [ ] **Step 3: Expand gallery and replace fallback flow**

Make the gallery a readable 13-node grid using all known icons exactly once.
Make the flow a covered-character narrative (for example agent → operator →
search → tool → output → memory → database) and remove the `api` fallback
caption. Keep node spacing and motion policy readable.

- [ ] **Step 4: Run example checks and generate full artifact bundles**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_render_svg.SvgRendererTest.test_illustrated_character_examples_cover_all_icons_without_fallback
PYTHONPATH=src python3 -m anidiagram.cli --spec examples/illustrated-character-v1-icons.diagram.json --style styles/illustrated-character.json --outdir outputs/illustrated-character-v1-icons --basename illustrated-character-v1-icons --formats svg,html,webp,quality --export-renderer browser --export-fps 20 --export-frames 60 --result outputs/illustrated-character-v1-icons/result.json
PYTHONPATH=src python3 -m anidiagram.cli --spec examples/illustrated-character-v1-flow.diagram.json --style styles/illustrated-character.json --outdir outputs/illustrated-character-v1-flow --basename illustrated-character-v1-flow --formats svg,html,webp,quality --export-renderer browser --export-fps 20 --export-frames 60 --result outputs/illustrated-character-v1-flow/result.json
node scripts/verify_character_motion_rest.mjs outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html
node scripts/verify_character_reduced_motion.mjs outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html 13
node scripts/verify_character_reduced_motion.mjs outputs/illustrated-character-v1-flow/illustrated-character-v1-flow.html 8
test -s outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.svg
test -s outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html
test -s outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.webp
test -s outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.quality.json
test -s outputs/illustrated-character-v1-flow/illustrated-character-v1-flow.svg
test -s outputs/illustrated-character-v1-flow/illustrated-character-v1-flow.html
test -s outputs/illustrated-character-v1-flow/illustrated-character-v1-flow.webp
test -s outputs/illustrated-character-v1-flow/illustrated-character-v1-flow.quality.json
PYTHONPATH=src python3 -c 'import json, sys; paths = sys.argv[1:]; [(_ for _ in ()).throw(SystemExit(f"invalid export: {path}")) if json.loads(open(path, encoding="utf-8").read())["outputs"]["webp"].get("renderer") != "browser" or json.loads(open(path, encoding="utf-8").read())["outputs"]["webp"].get("status") != "written" else None for path in paths]' outputs/illustrated-character-v1-icons/result.json outputs/illustrated-character-v1-flow/result.json
PYTHONPATH=src python3 -c 'import json, sys; [(_ for _ in ()).throw(SystemExit(f"quality not clean: {path}")) if json.loads(open(path, encoding="utf-8").read())["summary"] != {"errors": 0, "warnings": 0, "issues": 0} else None for path in sys.argv[1:]]' outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.quality.json outputs/illustrated-character-v1-flow/illustrated-character-v1-flow.quality.json
```

Expected: all commands exit 0; both quality reports have zero warnings.

### Task 6: Document the full system and complete regression verification

**Files:**
- Modify: `docs/diagram-script.md`
- Modify: `docs/html-runtime.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Test: `tests/test_render_svg.py`

- [ ] **Step 1: Document all 13 performance IDs and full coverage**

Replace documentation that describes v1 as a three-icon subset with a concise
mapping to all 13 icons. Document that fallback warnings are reserved for
future schema extensions, and retain explicit legacy `illustrated-v1` and
`semantic-line-v1` instructions.

- [ ] **Step 2: Run complete verification and inspect browser artifacts**

Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
node --check runtime/anidiagram-runtime.js
node --check scripts/verify_character_motion_rest.mjs
git diff --check
```

Open both generated WebP outputs. Confirm visual consistency with the approved
AI brain, operator, and data bucket: dark outline, flat pastel regions, compact
semantic prop, no clipping, and no fallback line icons.

- [ ] **Step 3: Commit examples and documentation**

```bash
git add examples/illustrated-character-v1-icons.diagram.json examples/illustrated-character-v1-flow.diagram.json docs/diagram-script.md docs/html-runtime.md README.md README.zh-CN.md tests/test_render_svg.py
git commit -m "docs: showcase full illustrated character system"
```
