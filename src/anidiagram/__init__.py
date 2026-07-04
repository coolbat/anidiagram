"""AniDiagram clean-room animated diagram renderer."""

from .model import Canvas, Edge, Group, Motion, Node, Scene, Style, Title
from .schema import DiagramScriptValidationError, ValidationIssue, compile_scene

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
    "compile_scene",
]
