"""AniDiagram clean-room animated diagram renderer."""

from .model import Canvas, Edge, Group, Motion, MotionPolicy, Node, Scene, SceneMotion, Style, Title
from .planner import brief_to_diagram_script, brief_to_plan, compile_plan
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
    "MotionPolicy",
    "Node",
    "Scene",
    "SceneMotion",
    "Style",
    "Title",
    "ValidationIssue",
    "__version__",
    "brief_to_diagram_script",
    "brief_to_plan",
    "compile_plan",
    "compile_preset",
    "compile_scene",
    "preset_names",
    "quality_report",
    "validate_scene",
]
