# Illustrated Character v1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `illustrated-character-v1` the default clean-room semantic-icon system, shipping animated agent, operator, and database characters with explicit legacy modes and visible fallback diagnostics.

**Architecture:** A small icon-system resolver owns the default/legacy precedence. A data-only character registry defines normalized vector primitives and named part ids; a focused SVG renderer serializes those definitions. Existing Scene/Manifest/GSAP layers consume stable parts, while quality reporting records valid semantic icons that fall back to line icons.

**Tech Stack:** Python 3 standard library, existing DiagramScript schema, SVG/SMIL, existing Motion Manifest, existing CDN GSAP runtime, `unittest`, Playwright browser capture.

---

## File Structure

- Create: `src/anidiagram/icon_system.py` — icon-system constants, strict resolver, and style-system predicates.
- Create: `src/anidiagram/illustrated_character_icons.py` — normalized primitive dataclasses and the three clean-room character definitions.
- Create: `src/anidiagram/renderer_illustrated_character.py` — converts character definitions to SVG using existing stable id conventions.
- Modify: `src/anidiagram/schema.py` and `schemas/diagram-script-v0.3.schema.json` — add the valid `operator` icon.
- Modify: `src/anidiagram/styles.py` — validate top-level and legacy icon-system fields.
- Modify: `src/anidiagram/renderer_svg.py` — choose the resolved icon system and delegate character rendering.
- Modify: `src/anidiagram/motion_manifest.py` — serialize resolved system, performance ids, and character selectors.
- Modify: `runtime/anidiagram-runtime.js` — add the three action-then-idle GSAP performances.
- Modify: `src/anidiagram/quality.py`, `src/anidiagram/exporters.py`, and `src/anidiagram/cli.py` — emit style-aware fallback `QualityIssue`s.
- Create: `styles/illustrated-character.json` — approved C visual token set.
- Create: `examples/illustrated-character-v1-icons.diagram.json` and `examples/illustrated-character-v1-flow.diagram.json` — close-up and in-context review scenes.
- Modify: `tests/test_render_svg.py` — all behavior, resolver, manifest, fallback, and rendering regression tests.
- Modify: `docs/diagram-script.md`, `docs/html-runtime.md`, `README.md`, and `README.zh-CN.md` — user-facing icon-system and fallback contract.

## Chunk 1: Resolution and Schema Contract

### Task 1: Test and implement strict icon-system resolution

**Files:**
- Create: `src/anidiagram/icon_system.py`
- Modify: `src/anidiagram/styles.py:57-130`
- Test: `tests/test_render_svg.py`

- [ ] **Step 1: Write failing resolver and style-validation tests**

```python
from anidiagram.icon_system import resolve_icon_system
from anidiagram.styles import validate_style_profile

def test_icon_system_defaults_to_illustrated_character_v1(self):
    self.assertEqual("illustrated-character-v1", resolve_icon_system({}))

def test_top_level_icon_system_overrides_legacy_effects_value(self):
    style = {"icon_system": "semantic-line-v1", "effects": {"icon_system": "illustrated-v1"}}
    self.assertEqual("semantic-line-v1", resolve_icon_system(style))

def test_invalid_icon_system_is_rejected_by_style_validation(self):
    issues = validate_style_profile({"icon_system": "unknown"})
    self.assertIn("$.icon_system", {issue.path for issue in issues})

def test_resolver_rejects_present_invalid_values_with_their_style_path(self):
    with self.assertRaisesRegex(ValueError, r"\$\.effects\.icon_system"):
        resolve_icon_system({"effects": {"icon_system": None}})
```

- [ ] **Step 2: Run the focused tests and confirm red**

Run: `PYTHONPATH=src python3 -m unittest tests.test_render_svg.SvgRendererTest.test_icon_system_defaults_to_illustrated_character_v1 tests.test_render_svg.SvgRendererTest.test_top_level_icon_system_overrides_legacy_effects_value tests.test_render_svg.SvgRendererTest.test_invalid_icon_system_is_rejected_by_style_validation tests.test_render_svg.SvgRendererTest.test_resolver_rejects_present_invalid_values_with_their_style_path`

Expected: FAIL because `icon_system.py` and validation support do not exist.

- [ ] **Step 3: Implement the minimal resolver**

```python
KNOWN_ICON_SYSTEMS = {"illustrated-character-v1", "illustrated-v1", "semantic-line-v1"}
DEFAULT_ICON_SYSTEM = "illustrated-character-v1"

def resolve_icon_system(style: Dict[str, Any]) -> str:
    if "icon_system" in style:
        value, path = style["icon_system"], "$.icon_system"
    elif isinstance(style.get("effects"), dict) and "icon_system" in style["effects"]:
        value, path = style["effects"]["icon_system"], "$.effects.icon_system"
    else:
        return DEFAULT_ICON_SYSTEM
    if not isinstance(value, str) or value not in KNOWN_ICON_SYSTEMS:
        raise ValueError(f"{path}: expected one of {sorted(KNOWN_ICON_SYSTEMS)}")
    return value
```

Validate top-level `$.icon_system` and legacy `$.effects.icon_system` as strings in the known set. Keep default style data free of an explicit icon system so omission exercises the new default.

- [ ] **Step 4: Run the focused tests and confirm green**

Run the Step 2 command.

Expected: PASS.

- [ ] **Step 5: Commit the resolver slice**

```bash
git add src/anidiagram/icon_system.py src/anidiagram/styles.py tests/test_render_svg.py
git commit -m "feat: default to illustrated character icons"
```

### Task 2: Add the operator icon to both DiagramScript schema surfaces

**Files:**
- Modify: `src/anidiagram/schema.py:63,521-530`
- Modify: `schemas/diagram-script-v0.3.schema.json:34`
- Test: `tests/test_render_svg.py`

- [ ] **Step 1: Write failing schema tests**

```python
def test_operator_is_a_valid_diagram_script_icon(self):
    scene = compile_scene({"version": "0.3", "nodes": [{"id": "operator", "position": [20, 20], "size": [160, 80], "icon": "operator"}]})
    self.assertEqual("operator", scene.nodes[0].icon)

def test_operator_is_listed_in_the_published_json_schema(self):
    schema = json.loads((ROOT / "schemas" / "diagram-script-v0.3.schema.json").read_text())
    self.assertIn("operator", schema["$defs"]["icon"]["enum"])
```

- [ ] **Step 2: Run the focused tests and confirm red**

Run: `PYTHONPATH=src python3 -m unittest tests.test_render_svg.SvgRendererTest.test_operator_is_a_valid_diagram_script_icon tests.test_render_svg.SvgRendererTest.test_operator_is_listed_in_the_published_json_schema`

Expected: FAIL because `operator` is absent from the Python and JSON schema enums.

- [ ] **Step 3: Implement the canonical schema addition**

Add `operator` to `KNOWN_ICONS` and the JSON-schema enum only. The line-icon geometry is implemented alongside the character renderer so schema, geometry, and fallback behavior remain independently testable.

- [ ] **Step 4: Run focused tests and confirm green**

Run the Step 2 command.

Expected: PASS.

- [ ] **Step 5: Commit the schema slice**

```bash
git add src/anidiagram/schema.py schemas/diagram-script-v0.3.schema.json tests/test_render_svg.py
git commit -m "feat: add operator diagram icon"
```

## Chunk 2: Character Geometry, Fallback Quality, and SVG Integration

### Task 3: Test and add normalized clean-room character definitions

**Files:**
- Create: `src/anidiagram/illustrated_character_icons.py`
- Test: `tests/test_render_svg.py`

- [ ] **Step 1: Write failing registry tests**

```python
from anidiagram.illustrated_character_icons import character_definition, character_icon_ids

def test_character_registry_has_three_v1_icons_with_named_performances(self):
    self.assertEqual({"agent", "operator", "database"}, character_icon_ids())
    self.assertEqual("brain-think-pulse-v1", character_definition("agent").performance)
    self.assertEqual("operator-type-focus-v1", character_definition("operator").performance)
    self.assertEqual("bucket-ingest-confirm-v1", character_definition("database").performance)
    self.assertTrue({"root", "leftLobe", "rightLobe", "chip", "signal", "spark"}.issubset(character_definition("agent").parts))
    self.assertTrue({"root", "head", "glasses", "laptop", "handLeft", "handRight", "cursor"}.issubset(character_definition("operator").parts))
    self.assertTrue({"root", "lid", "bucket", "handle", "liquid", "dataBead", "confirm"}.issubset(character_definition("database").parts))
```

- [ ] **Step 2: Run the focused test and confirm red**

Run: `PYTHONPATH=src python3 -m unittest tests.test_render_svg.SvgRendererTest.test_character_registry_has_three_v1_icons_with_named_performances`

Expected: FAIL because the registry module does not exist.

- [ ] **Step 3: Implement registry primitives and three definitions**

Use frozen dataclasses:

```python
@dataclass(frozen=True)
class CharacterPrimitive:
    part: str
    kind: str
    attrs: Mapping[str, str]
    fill: Optional[str] = None
    stroke: Optional[str] = None
    parent: Optional[str] = None

@dataclass(frozen=True)
class CharacterIconDefinition:
    icon: str
    semantic_role: str
    performance: str
    parts: Tuple[str, ...]
    primitives: Tuple[CharacterPrimitive, ...]
```

Use normalized `0..100` paths and primitives. The exact semantic parts are:

- agent: `leftLobe`, `rightLobe`, `chip`, `chipLabel`, `signal`, `spark`;
- operator: `head`, `hair`, `glasses`, `body`, `laptop`, `handLeft`, `handRight`, `cursor`;
- database: `lid`, `bucket`, `handle`, `liquid`, `dataBead`, `confirm`.

Give every definition a `root` part and approved C-style palette tokens (`ink`, `mint`, `lilac`, `orange`, `paper`, `gold`, `blue`).

- [ ] **Step 4: Run the focused test and confirm green**

Run the Step 2 command.

Expected: PASS.

- [ ] **Step 5: Commit registry-only slice**

```bash
git add src/anidiagram/illustrated_character_icons.py tests/test_render_svg.py
git commit -m "feat: define illustrated character icons"
```

### Task 4: Add style-aware fallback quality reporting after registry coverage exists

**Files:**
- Modify: `src/anidiagram/quality.py:59-75`
- Modify: `src/anidiagram/exporters.py:49-55`
- Modify: `src/anidiagram/cli.py:135-153`
- Test: `tests/test_render_svg.py`

- [ ] **Step 1: Write the failing fallback-quality test**

```python
def _scene_with_icon(icon: str):
    return compile_scene({
        "version": "0.3",
        "canvas": {"width": 240, "height": 160},
        "nodes": [{"id": icon, "position": [40, 40], "size": [160, 80], "icon": icon}],
    })

def test_character_default_reports_exactly_one_quality_issue_for_valid_uncovered_icon(self):
    scene = _scene_with_icon("api")
    report = quality_report(scene, {})
    fallbacks = [issue for issue in report["issues"] if issue["code"] == "character_icon_fallback"]
    self.assertEqual([{
        "code": "character_icon_fallback",
        "severity": "warning",
        "path": "$.nodes[0].icon",
        "message": "icon 'api' is not covered by illustrated-character-v1; rendered with semantic-line-v1",
    }], fallbacks)

def test_quality_export_and_cli_propagate_default_style_to_fallback_report(self):
    scene = _scene_with_icon("api")
    with tempfile.TemporaryDirectory() as tmp:
        quality_path = Path(tmp) / "api.quality.json"
        write_quality(scene, load_style(), quality_path)
        self.assertEqual("character_icon_fallback", json.loads(quality_path.read_text())["issues"][-1]["code"])
        spec_path = Path(tmp) / "api.diagram.json"
        spec_path.write_text(json.dumps({
            "version": "0.3",
            "canvas": {"width": 240, "height": 160},
            "nodes": [{"id": "api", "position": [40, 40], "size": [160, 80], "icon": "api"}],
        }))
        with redirect_stdout(io.StringIO()) as stdout:
            main(["--spec", str(spec_path), "--outdir", tmp, "--basename", "api", "--formats", "quality"])
        result = json.loads(stdout.getvalue())
        self.assertEqual(1, result["outputs"]["quality"]["summary"]["warnings"])
        cli_report = json.loads((Path(tmp) / "api.quality.json").read_text())
        self.assertEqual("character_icon_fallback", cli_report["issues"][-1]["code"])
```

- [ ] **Step 2: Run the focused test and confirm red**

Run: `PYTHONPATH=src python3 -m unittest tests.test_render_svg.SvgRendererTest.test_character_default_reports_exactly_one_quality_issue_for_valid_uncovered_icon tests.test_render_svg.SvgRendererTest.test_quality_export_and_cli_propagate_default_style_to_fallback_report`

Expected: FAIL because quality reporting does not accept style or consult registry coverage.

- [ ] **Step 3: Implement quality propagation**

Change `quality_report(scene, style=None)` to resolve the system only when a style is supplied; document that `style=None` preserves legacy direct-call behavior. For resolved `illustrated-character-v1`, append one `QualityIssue` for every valid node icon absent from `character_icon_ids()`. Update `write_quality(scene, style, path)` and the CLI quality branch to pass the already-loaded style. Keep `style=None` behavior unchanged for direct legacy callers.

- [ ] **Step 4: Run focused test and full Python suite**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_render_svg.SvgRendererTest.test_character_default_reports_exactly_one_quality_issue_for_valid_uncovered_icon tests.test_render_svg.SvgRendererTest.test_quality_export_and_cli_propagate_default_style_to_fallback_report
PYTHONPATH=src python3 -m unittest discover -s tests
```

Expected: PASS. Update only those old assertions whose intentionally style-aware reports now contain fallback warnings.

- [ ] **Step 5: Commit the quality slice**

```bash
git add src/anidiagram/quality.py src/anidiagram/exporters.py src/anidiagram/cli.py tests/test_render_svg.py
git commit -m "feat: report illustrated character fallbacks"
```

### Task 5: Render character definitions with stable SVG ids and preserve legacy modes

**Files:**
- Create: `src/anidiagram/renderer_illustrated_character.py`
- Modify: `src/anidiagram/renderer_svg.py:262-307,791-860,1704-1706`
- Modify: `src/anidiagram/illustrated_icons.py:208-212` only if it needs to call the shared resolver
- Test: `tests/test_render_svg.py`

- [ ] **Step 1: Write failing SVG rendering tests**

```python
def test_default_character_system_renders_agent_parts_with_stable_ids(self):
    scene = _scene_with_icon("agent")
    svg = render_svg(scene, load_style())
    self.assertIn('data-icon-system="illustrated-character-v1"', svg)
    self.assertIn('id="icon-agent-left-lobe"', svg)
    self.assertIn('id="icon-agent-chip"', svg)

def test_explicit_illustrated_v1_preserves_bubble_backplate(self):
    svg = render_svg(_scene_with_icon("agent"), {"icon_system": "illustrated-v1"})
    self.assertIn('class="illustrated-icon-backplate"', svg)
    self.assertNotIn('icon-agent-left-lobe', svg)

def test_valid_uncovered_icon_uses_semantic_line_fallback(self):
    svg = render_svg(_scene_with_icon("api"), load_style())
    self.assertIn('semantic-icon-api', svg)
    self.assertNotIn('illustrated-icon-backplate', svg)

def test_explicit_semantic_line_v1_renders_operator_line_geometry(self):
    svg = render_svg(_scene_with_icon("operator"), {"icon_system": "semantic-line-v1"})
    self.assertIn('semantic-icon-operator', svg)
    self.assertIn('id="icon-operator-laptop"', svg)
    self.assertNotIn('icon-operator-head', svg)
    self.assertNotIn('illustrated-icon-backplate', svg)
```

- [ ] **Step 2: Run the focused tests and confirm red**

Run: `PYTHONPATH=src python3 -m unittest tests.test_render_svg.SvgRendererTest.test_default_character_system_renders_agent_parts_with_stable_ids tests.test_render_svg.SvgRendererTest.test_explicit_illustrated_v1_preserves_bubble_backplate tests.test_render_svg.SvgRendererTest.test_valid_uncovered_icon_uses_semantic_line_fallback tests.test_render_svg.SvgRendererTest.test_explicit_semantic_line_v1_renders_operator_line_geometry`

Expected: FAIL because default rendering still uses line icons.

- [ ] **Step 3: Implement focused character SVG renderer and integration**

`renderer_illustrated_character.py` must map normalized primitive attributes into
the current icon box and call the existing `icon_part_id(node_id, part)` callback.
It must add `class="icon-runtime-part"` to animated parts and set
`transform-box: fill-box; transform-origin: center` through character-specific
CSS emitted by `renderer_svg.py`.

In `render_semantic_icon`, resolve once per style. For covered character icons,
return the delegated character SVG before the legacy line-icon branches. For
uncovered icons, continue into the existing line-icon renderer. For explicit
`illustrated-v1`, preserve the existing bubble renderer. Set the root SVG
`data-icon-system` from the shared resolver for every output.

- [ ] **Step 4: Run focused tests and full Python suite**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_render_svg.SvgRendererTest.test_default_character_system_renders_agent_parts_with_stable_ids tests.test_render_svg.SvgRendererTest.test_explicit_illustrated_v1_preserves_bubble_backplate tests.test_render_svg.SvgRendererTest.test_valid_uncovered_icon_uses_semantic_line_fallback tests.test_render_svg.SvgRendererTest.test_explicit_semantic_line_v1_renders_operator_line_geometry
PYTHONPATH=src python3 -m unittest discover -s tests
```

Expected: PASS.

- [ ] **Step 5: Commit SVG integration**

```bash
git add src/anidiagram/renderer_illustrated_character.py src/anidiagram/renderer_svg.py src/anidiagram/illustrated_icons.py tests/test_render_svg.py
git commit -m "feat: render illustrated character icons"
```

## Chunk 3: Runtime, Examples, and Evidence

### Task 6: Add Manifest support and GSAP micro-performances

**Files:**
- Modify: `src/anidiagram/motion_manifest.py:12-222`
- Modify: `runtime/anidiagram-runtime.js:1-715`
- Create: `scripts/verify_character_reduced_motion.mjs`
- Test: `tests/test_render_svg.py`

- [ ] **Step 1: Write failing manifest/runtime-source tests**

```python
def _manifest_from_html(html: str):
    marker = '<script type="application/json" id="anidiagram-motion-manifest">'
    start = html.index(marker) + len(marker)
    return json.loads(html[start:html.index("</script>", start)])

def test_character_manifests_use_their_performances_and_parts(self):
    for icon, performance, part_id in (
        ("agent", "brain-think-pulse-v1", "#icon-agent-chip"),
        ("operator", "operator-type-focus-v1", "#icon-operator-laptop"),
        ("database", "bucket-ingest-confirm-v1", "#icon-database-liquid"),
    ):
        html = render_html_runtime(_scene_with_icon(icon), load_style(), runtime="gsap")
        manifest = _manifest_from_html(html)
        entry = manifest["icons"][0]
        self.assertEqual("illustrated-character-v1", manifest["icon_system"])
        self.assertEqual(performance, entry["performance"])
        self.assertIn(part_id, entry["parts"].values())

def test_manifest_serializes_explicit_legacy_icon_systems(self):
    for icon_system in ("illustrated-v1", "semantic-line-v1"):
        html = render_html_runtime(_scene_with_icon("agent"), deep_merge(load_style(), {"icon_system": icon_system}), runtime="gsap")
        self.assertEqual(icon_system, _manifest_from_html(html)["icon_system"])

def test_character_runtime_registers_all_three_performances(self):
    source = (ROOT / "runtime" / "anidiagram-runtime.js").read_text(encoding="utf-8")
    for name in ("brain-think-pulse-v1", "operator-type-focus-v1", "bucket-ingest-confirm-v1"):
        self.assertIn(name, source)
```

Import `deep_merge` from `anidiagram.styles` alongside `load_style` in the test
module.

- [ ] **Step 2: Run focused tests and confirm red**

Run: `PYTHONPATH=src python3 -m unittest tests.test_render_svg.SvgRendererTest.test_character_manifests_use_their_performances_and_parts tests.test_render_svg.SvgRendererTest.test_manifest_serializes_explicit_legacy_icon_systems tests.test_render_svg.SvgRendererTest.test_character_runtime_registers_all_three_performances`

Expected: FAIL because no character performance mapping exists.

- [ ] **Step 3: Implement manifest and runtime functions**

Add character performance ids and exact parts to a dedicated mapping in
`motion_manifest.py`; do not overload `ICON_PERFORMANCE_V2`. Pass the resolved
icon system into performance selection so only covered character icons get the
new ids. Set `manifest["icon_system"]` for all systems.

Implement three GSAP functions using only `opacity`, `x/y`, `scale`, `rotate`,
and existing stroke-draw helpers. Each loop follows B motion:

- brain: lobes pulse, chip settles, signal moves, spark confirms;
- operator: eyes/glasses focus, hands type, cursor resolves, laptop settles;
- bucket: lid opens, data bead falls, liquid rises, check confirms.

All functions call `setInitial`, check required parts, use a repeat delay, and
end at canonical rest before the next cycle. Do not add GSAP plugins.

Create `scripts/verify_character_reduced_motion.mjs` using the already-required
Node Playwright. It receives an HTML file path, launches Chromium, calls
`page.emulateMedia({ reducedMotion: "reduce" })` before navigation, waits for the
runtime script, then exits non-zero unless
`(window.__ANIDIAGRAM_TIMELINES__ || []).length === 0`. It must close the browser in a
`finally` block and add no production dependency.

- [ ] **Step 4: Run focused tests, JS syntax check, and full suite**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_render_svg.SvgRendererTest.test_character_manifests_use_their_performances_and_parts tests.test_render_svg.SvgRendererTest.test_manifest_serializes_explicit_legacy_icon_systems tests.test_render_svg.SvgRendererTest.test_character_runtime_registers_all_three_performances
node --check runtime/anidiagram-runtime.js
PYTHONPATH=src python3 -m unittest discover -s tests
```

Expected: all commands exit 0.

- [ ] **Step 5: Commit runtime integration**

```bash
git add src/anidiagram/motion_manifest.py runtime/anidiagram-runtime.js scripts/verify_character_reduced_motion.mjs tests/test_render_svg.py
git commit -m "feat: animate illustrated character icons"
```

### Task 7: Add style, review examples, docs, and browser evidence

**Files:**
- Create: `styles/illustrated-character.json`
- Create: `examples/illustrated-character-v1-icons.diagram.json`
- Create: `examples/illustrated-character-v1-flow.diagram.json`
- Modify: `docs/diagram-script.md`, `docs/html-runtime.md`, `README.md`, `README.zh-CN.md`
- Modify: `tests/test_render_svg.py`

- [ ] **Step 1: Write failing example and style tests**

```python
def test_illustrated_character_examples_render_without_errors(self):
    for name in ("illustrated-character-v1-icons", "illustrated-character-v1-flow"):
        scene = compile_scene(json.loads((ROOT / "examples" / f"{name}.diagram.json").read_text()))
        style = load_style(ROOT / "styles" / "illustrated-character.json")
        self.assertIn('data-icon-system="illustrated-character-v1"', render_svg(scene, style))
```

- [ ] **Step 2: Run the focused test and confirm red**

Run: `PYTHONPATH=src python3 -m unittest tests.test_render_svg.SvgRendererTest.test_illustrated_character_examples_render_without_errors`

Expected: FAIL because files do not exist.

- [ ] **Step 3: Add approved C style and two examples**

The style sets `icon_system: "illustrated-character-v1"`, `ink: "#283047"`,
paper canvas colors, flat pastel role fills, and restrained accents. The gallery
example contains one node for each v1 character at large scale. The flow example
contains `agent -> operator -> database` plus one `api` node to demonstrate the
documented valid-icon fallback warning.

Document default resolution, explicit legacy modes, the three performance names,
and quality-report semantics in English and Chinese README/docs.

- [ ] **Step 4: Run static and browser verification**

Run:

```bash
PYTHONPATH=src python3 -m anidiagram.cli --spec examples/illustrated-character-v1-icons.diagram.json --style styles/illustrated-character.json --outdir outputs/illustrated-character-v1-icons --basename illustrated-character-v1-icons --formats svg,html,webp,quality --export-renderer browser --export-fps 20 --export-frames 60
PYTHONPATH=src python3 -m anidiagram.cli --spec examples/illustrated-character-v1-flow.diagram.json --style styles/illustrated-character.json --outdir outputs/illustrated-character-v1-flow --basename illustrated-character-v1-flow --formats svg,html,webp,quality --export-renderer browser --export-fps 20 --export-frames 60
node scripts/verify_character_reduced_motion.mjs outputs/illustrated-character-v1-icons/illustrated-character-v1-icons.html
node scripts/verify_character_reduced_motion.mjs outputs/illustrated-character-v1-flow/illustrated-character-v1-flow.html
node --check runtime/anidiagram-runtime.js
PYTHONPATH=src python3 -m unittest discover -s tests
git diff --check
```

Expected: both reports have no errors; the flow report has exactly one documented `character_icon_fallback` warning for `api`.

- [ ] **Step 5: Inspect browser artifacts**

Open the generated HTML and WebP artifacts. Confirm the three characters have
the approved C outline/fill treatment, the B semantic beat returns to quiet, no
part clips outside its node, and `api` remains a readable line-icon fallback.

- [ ] **Step 6: Commit review artifacts and documentation**

```bash
git add styles/illustrated-character.json examples/illustrated-character-v1-icons.diagram.json examples/illustrated-character-v1-flow.diagram.json docs/diagram-script.md docs/html-runtime.md README.md README.zh-CN.md tests/test_render_svg.py
git commit -m "feat: showcase illustrated character icons"
```
