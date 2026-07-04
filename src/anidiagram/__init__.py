"""AniDiagram clean-room animated diagram renderer."""

from .model import Canvas, Edge, Group, Motion, Node, Scene, Style, Title
from .presets import compile_preset, preset_names
from .quality import quality_report
from .schema import DiagramScriptValidationError, ValidationIssue, compile_scene, validate_scene

__version__ = "0.1.0"

__all__ = [
    "Canvas",
    "DiagramScriptValidationError",
    "Edge",
    "Group",
    "Motion",
    "Node",
    "Scene",
    "Style",
    "Title",
    "ValidationIssue",
    "__version__",
    "compile_preset",
    "compile_scene",
    "preset_names",
    "quality_report",
    "validate_scene",
]
