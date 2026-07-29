"""Versioned browser-runtime dependency rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


GSAP_VERSION = "3.15.0"
GSAP_CDN_URL = f"https://cdn.jsdelivr.net/npm/gsap@{GSAP_VERSION}/dist/gsap.min.js"
RUNTIME_DEPENDENCY_MODES = {"cdn", "inline", "none"}


def runtime_dependency_markup(
    runtime: str,
    mode: str = "cdn",
    source: Optional[Path] = None,
) -> str:
    if runtime != "gsap":
        return ""
    if mode not in RUNTIME_DEPENDENCY_MODES:
        raise ValueError(f"runtime dependency mode must be one of: {', '.join(sorted(RUNTIME_DEPENDENCY_MODES))}")
    if mode == "none":
        return ""
    if mode == "cdn":
        return f'<script src="{GSAP_CDN_URL}" crossorigin="anonymous"></script>'
    if source is None:
        raise ValueError("inline runtime dependency mode requires a GSAP source path")
    path = Path(source)
    if not path.is_file():
        raise ValueError(f"GSAP source does not exist: {path}")
    javascript = path.read_text(encoding="utf-8").replace("</script", "<\\/script")
    return f'<script data-runtime-dependency="gsap@{GSAP_VERSION}">\n{javascript}\n</script>'
