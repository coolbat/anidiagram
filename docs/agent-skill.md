# Install and use AniDiagram as an Agent Skill

AniDiagram ships both an Agent Skill and a Python CLI. The Skill guides source
analysis, evidence, planning and acceptance; the CLI implements compilation and
rendering. Installing the Skill does not certify an agent's understanding of code.

## Install into your agent

With Node.js/npm and Git available, run this **inside the project you want to
analyze**, not inside the AniDiagram checkout:

```bash
# Inspect the available Skill without installing it.
npx skills add coolbat/anidiagram --list

# Pick the agent you will use. Project-local is the default.
npx skills add coolbat/anidiagram --skill anidiagram -a claude-code
# Or:
npx skills add coolbat/anidiagram --skill anidiagram -a codex
npx skills add coolbat/anidiagram --skill anidiagram -a cursor
```

Add `-g` only if you want a user-wide installation. Do not overwrite an existing
development symlink without choosing that deliberately. `--copy` can be used
where symlinks are unsuitable. The installer owns the host-specific paths; use
the printed installation path or the path shown by your agent. These commands
follow the [official Skills CLI](https://github.com/vercel-labs/skills) contract.

Install the **whole directory**, including `scripts/`, `src/`, `assets/`,
`runtime/`, `styles/` and `schemas/`. It is a bundled engine, not just a prompt.
The current root-Skill distribution also includes repository documentation and
examples; it is not a minimal-size package. A host that only imports SKILL.md
cannot run its helpers. ZIP/manual installations must retain the same structure.
No Codex-specific API, MCP server, API key or hosted service is required for local
SVG/HTML generation. The agent must be able to read local files and run Python.

To test local changes before publishing, substitute the absolute path of a
**clean copy** of the AniDiagram directory for `coolbat/anidiagram`. Avoid pointing
a recursive installer at a development tree containing node_modules, virtual
environments or generated outputs. The reproducible installer test below stages
only Git-visible files and never touches user-global skills.

## First use from any project directory

Set `SKILL_DIR` to the absolute directory containing the installed `SKILL.md`.
This is not the project you are analyzing. The portable launcher leaves the
current directory unchanged and resolves the bundled engine itself.

```bash
SKILL_DIR="/absolute/path/from/the/installer/anidiagram"
python3 -I "$SKILL_DIR/scripts/run_anidiagram.py" --doctor

# Small synthetic smoke test, no pip installation or browser dependencies.
python3 -I "$SKILL_DIR/scripts/run_anidiagram.py" \
  --preset agent-memory --formats svg,html,quality \
  --runtime-dependency none --outdir outputs/anidiagram-smoke --deliver
```

This writes SVG, static HTML, quality JSON and a delivery receipt under the
**current project's** `outputs/anidiagram-smoke/`, not the installed Skill.
Basic mode needs Python **3.9+**, with no third-party Python packages. `-I`
prevents caller PYTHONPATH or project-local modules from overriding the engine.
You may use an isolated virtualenv's Python executable instead of `python3`.
Do not put an actual username or a fixed Codex path into reusable prompts.

PowerShell equivalent (use whichever Python 3.9+ executable is installed):

```powershell
$SKILL_DIR = "C:\path\to\installed\anidiagram"
py -3 -I "$SKILL_DIR/scripts/run_anidiagram.py" --doctor
py -3 -I "$SKILL_DIR/scripts/run_anidiagram.py" --preset agent-memory --formats svg,html,quality --runtime-dependency none --outdir outputs/anidiagram-smoke --deliver
```

Discovery/refresh depends on the host: explicitly select the Skill or open a
new conversation if an existing conversation has not loaded it. Do not infer
failure merely because a host uses a different invocation syntax.

## Optional dependencies — install only with approval

`--doctor` is read-only and checks availability, not successful browser launch.
It never installs, upgrades, fetches source repositories or modifies config.
The doctor reports absolute dependency paths: Node can reuse packages from an
ancestor directory, so availability is not a promise of dependency isolation.
Use `--doctor --require browser` (also `core`, `repository_evidence`,
`inline_html`, `raster`, `video`) for an exit code: 0 available, 2 missing.

| Capability | Needed |
| --- | --- |
| Basic SVG / static HTML / plans / quality | Python 3.9+ and complete Skill files |
| Fixed-commit source evidence / Python fact checks | Git and the target repository with the referenced commits present |
| Self-contained animated HTML | Local GSAP source (otherwise default HTML uses a pinned CDN) |
| Strict browser acceptance / browser exports | Node.js, Playwright, Chromium; additional tools depend on format |
| Python raster exports | Pillow in the Python interpreter used by the launcher |
| Browser MP4 exports | Browser dependencies and FFmpeg; actual codec support must be tested |

For offline animation and browser checks, install into the Skill directory,
**not the target project's package.json**. Node 20+ is the CI baseline:

```bash
npm ci --prefix "$SKILL_DIR" --ignore-scripts
node "$SKILL_DIR/node_modules/playwright/cli.js" install chromium
python3 -I "$SKILL_DIR/scripts/run_anidiagram.py" --doctor --require browser
```

On Linux, Chromium may need OS packages (`playwright install --with-deps chromium`
requires permission to alter the OS); Chinese diagrams also need a CJK font,
such as Noto Sans CJK. Follow the [Playwright installation instructions](https://playwright.dev/docs/browsers).
Offline or restricted machines can supply preinstalled dependencies; do not
label a skipped browser check as successful.

Render portable animation and check its actual browser output:

```bash
python3 -I "$SKILL_DIR/scripts/run_anidiagram.py" \
  --spec "$SKILL_DIR/tests/fixtures/accuracy/detour-label.diagram.json" \
  --readable-labels --formats svg,html,quality \
  --runtime-dependency inline \
  --runtime-source "$SKILL_DIR/node_modules/gsap/dist/gsap.min.js" \
  --outdir outputs/anidiagram-readable --deliver
python3 -I "$SKILL_DIR/scripts/run_anidiagram.py" visual-check \
  outputs/anidiagram-readable/diagram.html --strict-labels
```

For Pillow, use a user-approved isolated environment outside the target project:
`python3 -m venv /chosen/venv`, then `/chosen/venv/bin/python -m pip install Pillow`.
Invoke the launcher with that environment's Python (Windows: `Scripts/python.exe`).
FFmpeg installation is OS-specific and is never attempted by the Skill.

## Give another agent this test request

```text
Use the installed AniDiagram skill to analyze the current project, not AniDiagram's
own installation directory. Do not modify the project's source or dependencies.
First run the Skill doctor. Identify the real entry point, major modules, calls,
returned data, conditions and failure paths for one core flow. Record the source
revision, scope, exclusions and unknowns. Write the plan, facts, diagram and
reports under outputs/anidiagram-test/. Use readable SVG/HTML labels and a relation
table. Run the source-fact preflight and strict browser check when available.
Do not fabricate independent review or report unresolved facts as verified.
Ask before installing missing dependencies. Report separately: source references,
semantic review, visual fidelity, and facts/files not covered.
```

For a fair comparison, use the same target commit, scoped task, model settings
and time/tool budget. Do not give one agent the other agent's answer. Compare
facts and omissions against a separately reviewed source oracle before visual
polish. See [accuracy contracts and limits](accuracy-loop.md). Non-GitHub origins
are outside the current repository-evidence verifier; report that limitation,
never rewrite the target origin to get a check to pass.

## Reproducible packaging checks

From the AniDiagram development checkout:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p test_skill_launcher.py
python3 scripts/verify_skill_install.py
# Optional: explicitly permit temporary npm setup and Chromium cache installation.
python3 scripts/verify_skill_install.py --with-browser --outdir outputs/skill-install
```

The installer test uses an isolated temporary directory, Skills CLI 1.5.24 and
project-local Codex / Claude Code / Cursor discovery paths. It renders from a
different directory, validates receipts, and tests both copy and symlink modes.
It does not launch those agents' models or prove their semantic understanding.
Network access to npm is needed on a cold cache. No user-global skills are changed.
`--outdir` retains logs and artifact copies, while the actual test installations
stay outside the checkout and are cleaned up. `--with-browser` additionally
checks one installed copy with inline GSAP and strict browser labels; automated
acceptance still leaves human visual review pending. Windows commands above are
usage guidance, not a claim that the packaging matrix was tested on Windows.
Existing CLI installation remains unchanged; see the main README for that path.
