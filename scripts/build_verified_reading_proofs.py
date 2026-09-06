"""Reproduce repository evidence, typed examples, reader and comparison artifacts."""
import io
import json
from pathlib import Path
from contextlib import redirect_stdout

from anidiagram.cli import main
from anidiagram.compare import deliver_comparison

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/archify-followups"
OUT.mkdir(parents=True, exist_ok=True)
results = []
for source in sorted((ROOT / "examples/verified-reading").glob("*.plan.json")):
    name = source.name.removesuffix(".plan.json")
    args = ["--plan", str(source), "--outdir", str(OUT), "--basename", name,
            "--formats", "svg,html,quality", "--spec-out", str(OUT / (name + ".diagram.json")),
            "--runtime-dependency", "inline", "--runtime-source", str(ROOT / "node_modules/gsap/dist/gsap.min.js"), "--deliver"]
    if name == "repository-reader":
        args += ["--repo-root", str(ROOT)]
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        main(args)
    results.append(json.loads(stdout.getvalue()))
base_path = ROOT / "examples/verified-reading/repository-reader.plan.json"
head = json.loads(base_path.read_text())
head["semantic"]["relations"][2]["label"] = "产物、哈希与验证结果"
head["presentation"]["style"] = "deep-tech"
head_path = OUT / "repository-reader-after.plan.json"
head_path.write_text(json.dumps(head, ensure_ascii=False, indent=2) + "\n")
comparison = deliver_comparison(base_path, head_path, OUT / "repository-delta.html", repo_root=ROOT)
receipt = {"artifacts": results, "comparison": comparison}
(OUT / "proof-index.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"ok": True, "diagrams": len(results), "comparison": comparison, "index": str(OUT / "proof-index.json")}, ensure_ascii=False, indent=2))
