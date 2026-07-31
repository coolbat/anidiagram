"""Locale detection, viewer copy, and cross-platform font fallbacks."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


SUPPORTED_LOCALES = ("auto", "en", "zh-CN")
_CJK_PATTERN = re.compile(r"[\u3400-\u9fff]")

LATIN_FONT_STACK = (
    'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, '
    '"Segoe UI", sans-serif'
)
CJK_FONT_STACK = (
    '"Noto Sans CJK SC", "Noto Sans SC", "Source Han Sans SC", '
    '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", '
    '"WenQuanYi Micro Hei", ui-sans-serif, system-ui, sans-serif'
)


def contains_cjk(value: Any) -> bool:
    return _CJK_PATTERN.search(str(value or "")) is not None


def resolve_locale(requested: str = "auto", texts: Iterable[Any] = ()) -> str:
    if requested not in SUPPORTED_LOCALES:
        raise ValueError(f"unsupported locale {requested!r}; expected one of: {', '.join(SUPPORTED_LOCALES)}")
    if requested != "auto":
        return requested
    return "zh-CN" if any(contains_cjk(value) for value in texts) else "en"


def scene_locale(scene: Any, requested: str = "auto") -> str:
    if requested != "auto":
        return resolve_locale(requested)
    texts = [scene.title.text, scene.title.subtitle]
    texts.extend(value for node in scene.nodes for value in (node.label, node.caption))
    texts.extend(edge.label for edge in scene.edges)
    texts.extend(group.label for group in scene.groups)
    detected = resolve_locale("auto", texts)
    if detected == "zh-CN":
        return detected
    authored = getattr(scene, "locale", "auto")
    return resolve_locale(authored) if authored != "auto" else detected


def font_stack(locale: str) -> str:
    return CJK_FONT_STACK if locale.lower().startswith("zh") else LATIN_FONT_STACK


def viewer_labels(locale: str) -> Dict[str, str]:
    if locale.lower().startswith("zh"):
        return {
            "play": "播放", "pause": "暂停", "restart": "重新播放",
            "explain": "开始讲解", "previous": "上一步", "next": "下一步",
            "expressive": "表现模式", "readable": "易读模式", "off": "关闭动效",
            "full": "完整动效", "subtle": "轻量动效",
            "zoom_in": "放大", "zoom_out": "缩小", "reset": "重置视图",
            "download": "下载 SVG", "toolbar": "图表播放与视图控制",
            "stage": "可缩放和平移的动画图表", "ready": "图表已就绪",
            "restarted": "动画已重新播放", "runtime_suffix": "动画架构图",
            "dependency_warning": "GSAP 未加载，已降级为静态图表。",
        }
    return {
        "play": "Play", "pause": "Pause", "restart": "Restart",
        "explain": "Start Explanation", "previous": "Previous Step", "next": "Next Step",
        "expressive": "Expressive", "readable": "Readable", "off": "Motion Off",
        "full": "Full Motion", "subtle": "Subtle",
        "zoom_in": "Zoom In", "zoom_out": "Zoom Out", "reset": "Reset View",
        "download": "Download SVG", "toolbar": "Diagram playback and view controls",
        "stage": "Zoomable and pannable animated diagram", "ready": "Diagram ready",
        "restarted": "Animation restarted", "runtime_suffix": "Runtime",
        "dependency_warning": "GSAP did not load; showing the static diagram.",
    }


def raster_font_path(locale: str) -> Optional[Path]:
    """Find a local font for lightweight Pillow exports.

    Users can make output deterministic with ANIDIAGRAM_CJK_FONT. Browser/SVG
    exports use the CSS fallback stack above and do not require this helper.
    """

    configured = os.environ.get("ANIDIAGRAM_CJK_FONT")
    candidates = [Path(configured).expanduser()] if configured else []
    if locale.lower().startswith("zh"):
        candidates.extend(
            Path(value)
            for value in (
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Medium.ttc",
                "/Library/Fonts/Arial Unicode.ttf",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simhei.ttf",
            )
        )
    candidates.extend(
        Path(value)
        for value in (
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
        )
    )
    return next((path for path in candidates if path.is_file()), None)
