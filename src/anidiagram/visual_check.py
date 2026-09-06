"""Capture immutable HTML at known viewports and write auditable visual evidence."""

from html import escape
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .artifact_bundle import commit_bundle
from .delivery import canonical_json_bytes, digest_bytes
from .resources import resource_path

DEFAULT_VIEWPORTS = "1440x900,1600x1000,1920x1080,2048x1320"


def parse_viewports(value):
    result = []
    for item in value.split(","):
        match = re.fullmatch(r"(\d+)x(\d+)", item.strip())
        if not match:
            raise ValueError("viewports must be comma-separated WIDTHxHEIGHT pairs")
        width, height = map(int, match.groups())
        if not (320 <= width <= 4096 and 320 <= height <= 4096):
            raise ValueError("viewport dimensions must be between 320 and 4096 pixels")
        viewport = {"width": width, "height": height}
        if viewport in result:
            raise ValueError("viewports must be unique")
        result.append(viewport)
    if not 1 <= len(result) <= 8:
        raise ValueError("provide between one and eight viewports")
    return result


def visual_check(artifact, *, outdir=None, viewports=DEFAULT_VIEWPORTS):
    artifact = Path(artifact).resolve()
    sizes = parse_viewports(viewports)
    content = artifact.read_bytes()
    if not content or b"<svg" not in content.lower():
        raise ValueError("visual-check expects standalone HTML containing an SVG")
    directory = Path(outdir).absolute() if outdir else artifact.parent
    directory.mkdir(parents=True, exist_ok=True)
    prefix = artifact.stem + ".visual"
    with tempfile.TemporaryDirectory(prefix=".anidiagram-visual-", dir=directory) as temporary:
        stage = Path(temporary)
        frozen = stage / "snapshot.html"
        frozen.write_bytes(content)
        node = shutil.which("node")
        if node is None:
            receipt = {"status": "skipped", "reason": "Node.js is unavailable", "checks": [], "captures": []}
        else:
            try:
                process = subprocess.run([node, str(resource_path("runtime", "visual-check.mjs")), str(frozen), str(stage), json.dumps(sizes)],
                                         capture_output=True, text=True, timeout=max(60, len(sizes) * 55), check=False)
                if process.returncode:
                    raise ValueError(process.stderr.strip() or "browser evidence process failed")
                receipt = json.loads(process.stdout)
            except (ValueError, subprocess.TimeoutExpired) as error:
                receipt = {"status": "failed", "reason": str(error), "checks": [], "captures": []}
        receipt.update({"schema": {"name": "AniDiagramVisualCheck", "version": "0.1"},
                        "artifact": {"path": artifact.name, **digest_bytes(content)},
                        "visual_review": "pending", "capture_mode": "frozen-html-reduced-motion",
                        "theme_scope": "browser-color-scheme-preference; authored diagram style is preserved"})
        if artifact.read_bytes() != content:
            receipt["status"] = "failed"
            receipt["reason"] = "The input artifact changed during capture; evidence covers the frozen hash only."
        files = {}
        for capture in receipt["captures"]:
            captured = (stage / capture["path"]).read_bytes()
            name = prefix + "." + Path(capture["path"]).name
            files[directory / name] = captured
            capture.update({"path": name, **digest_bytes(captured)})
        sheet = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Visual evidence</title><style>body{font:16px system-ui;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}figure{margin:0}img{width:100%;border:1px solid #ccc}</style><h1>Visual review pending</h1><p>Browser color-scheme preference does not replace the authored style. Automated containment is not visual approval.</p><main>'
        for capture in receipt["captures"]:
            name = escape(capture["path"], quote=True)
            sheet += f'<figure><a href="{name}"><img src="{name}" alt="{name}"></a><figcaption>{name}</figcaption></figure>'
        sheet += '</main></html>'
        sheet_path = directory / (prefix + ".html")
        files[sheet_path] = sheet.encode()
        receipt["contact_sheet"] = {"path": sheet_path.name, **digest_bytes(files[sheet_path])}
        receipt_path = directory / (prefix + ".json")
        files[receipt_path] = canonical_json_bytes(receipt)
        commit_bundle(files, inputs=(artifact,))
    return {"ok": receipt["status"] == "passed", "status": receipt["status"], "receipt": str(receipt_path),
            "contact_sheet": str(sheet_path), "visual_review": "pending", "captures": len(receipt["captures"])}
