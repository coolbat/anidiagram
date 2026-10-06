"""Progressively enhanced previews of existing, unmodified diagram HTML."""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from html import escape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVG_NS = "http://www.w3.org/2000/svg"


def preview_head(prefix: str = "") -> str:
    return (f'<link rel="stylesheet" href="{prefix}preview-motion.css">\n'
            f'  <script defer src="{prefix}preview-motion.js"></script>')


def preview_controls() -> str:
    return ('<div class="preview-controls"><button type="button" data-preview-toggle '
            'aria-pressed="true" hidden>Pause previews</button>'
            '<span>Live icon motion in visible cards. Open HTML for full-size details.</span></div>')


def live_preview(svg: str, html: str, title: str, poster: str | None = None) -> str:
    poster_attribute = f' data-preview-poster="{escape(poster, quote=True)}"' if poster else ""
    poster = poster or str(Path(svg).with_suffix(".preview.svg"))
    return (f'<figure class="motion-preview"><a href="{escape(html, quote=True)}" '
            f'data-preview-url="{escape(html, quote=True)}"{poster_attribute}>'
            f'<img loading="lazy" src="{escape(poster, quote=True)}" '
            f'alt="{escape(title, quote=True)}"></a>'
            '<figcaption class="preview-status" hidden>Animation unavailable; open HTML or view the static preview.</figcaption>'
            '</figure>')


def write_static_poster(source: Path, target: Path) -> None:
    """Settle authored entrance fades; retain icon rest geometry and all labels."""
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    svg = ET.fromstring(source.read_bytes())
    for parent in svg.iter():
        for child in list(parent):
            kind = child.tag.rsplit("}", 1)[-1]
            if kind not in {"animate", "animateMotion", "animateTransform", "set"}:
                continue
            if child.get("fill") == "freeze" and kind in {"animate", "set"}:
                attribute = child.get("attributeName")
                final = child.get("to") or child.get("values", "").split(";")[-1]
                if attribute and final:
                    parent.set(attribute, final)
            parent.remove(child)
    style = ET.SubElement(svg, f"{{{SVG_NS}}}style")
    style.text = """
* { animation: none !important; transition: none !important; }
.edge-flow, .edge-particle, .edge-arrow-particle, .node-burst, .node-glow,
.icon-breathe-halo, #title-highlight { display: none !important; }
"""
    svg.set("data-motion-profile", "off")
    target.write_text(ET.tostring(svg, encoding="unicode") + "\n", encoding="utf-8")


class _Previews(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "data-preview-url" in values:
            self.targets.append((values["data-preview-url"], values.get("data-preview-poster")))


def write_preview_assets(outdir: Path) -> dict:
    """Only new posters/index metadata are written; source diagrams stay intact."""
    outdir = outdir.resolve()
    targets = {}
    for page in sorted(outdir.rglob("*.html")):
        content = page.read_text(encoding="utf-8")
        if "data-preview-url=" not in content:
            continue
        parser = _Previews()
        parser.feed(content)
        for target, existing_poster in parser.targets:
            path = (page.parent / target).resolve()
            path.relative_to(outdir)  # Reject targets outside the gallery.
            poster = (page.parent / existing_poster).resolve() if existing_poster else None
            if poster:
                poster.relative_to(outdir)
            if path in targets and targets[path] != poster:
                raise ValueError(f"Conflicting posters for {path}")
            targets[path] = poster
        def reserve_image_space(match):
            source = (page.parent / match[1].replace(".preview.svg", ".svg")).resolve()
            source.relative_to(outdir)
            view_box = ET.fromstring(source.read_bytes()).get("viewBox").split()
            tag = re.sub(r'\s(?:width|height)="[^"]*"', "", match[0])
            return tag[:-1] + f' width="{view_box[2]}" height="{view_box[3]}">'
        # Native lazy-loading needs a reserved aspect ratio: otherwise cards can
        # collapse, shift and briefly start many off-screen runtimes on load.
        content = re.sub(r'<img\b[^>]*src="([^"]+\.svg)"[^>]*>', reserve_image_space, content)
        page.write_text(content, encoding="utf-8")
    entries = []
    for html in sorted(targets):
        source = html.with_suffix(".svg")
        poster = targets[html] or html.with_suffix(".preview.svg")
        if targets[html] is None:
            write_static_poster(source, poster)
        entries.append({
            "html": html.relative_to(outdir).as_posix(),
            "svg": source.relative_to(outdir).as_posix(),
            "poster": poster.relative_to(outdir).as_posix(),
            **{name + "_sha256": hashlib.sha256(path.read_bytes()).hexdigest()
               for name, path in (("html", html), ("svg", source), ("poster", poster))},
        })
    for suffix in ("js", "css"):
        (outdir / f"preview-motion.{suffix}").write_bytes(
            (ROOT / "runtime" / f"gallery-preview.{suffix}").read_bytes())
    report = {"version": 1, "mode": "visible-only-live-html", "previews": entries}
    (outdir / "preview-manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"previews": len(entries), "manifest": str(outdir / "preview-manifest.json")}
