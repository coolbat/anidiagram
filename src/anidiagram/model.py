"""Typed intermediate representation for AniDiagram scenes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


Point = Tuple[float, float]
Bounds = Tuple[float, float, float, float]


@dataclass(frozen=True)
class Canvas:
    width: int = 1200
    height: int = 720


@dataclass(frozen=True)
class Title:
    text: str = "AniDiagram"
    subtitle: str = ""


@dataclass(frozen=True)
class Style:
    name: Optional[str] = None


@dataclass(frozen=True)
class Motion:
    duration: Optional[str] = None
    delay: float = 0.0
    enabled: bool = True


@dataclass(frozen=True)
class Node:
    node_id: str
    label: str
    caption: str
    position: Point
    size: Point
    role: str = "neutral"
    step: Optional[int] = None
    radius: Optional[float] = None
    fill: Optional[str] = None
    stroke: Optional[str] = None
    stroke_width: Optional[float] = None


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    label: str = ""
    role: str = "neutral"
    route: str = "curved"
    step: Optional[int] = None
    points: Tuple[Point, ...] = field(default_factory=tuple)
    stroke: Optional[str] = None
    width: Optional[float] = None
    motion: Motion = field(default_factory=Motion)


@dataclass(frozen=True)
class Group:
    group_id: str
    label: str
    bounds: Bounds
    role: str = "neutral"
    fill: Optional[str] = None
    stroke: Optional[str] = None


@dataclass(frozen=True)
class Scene:
    version: str
    canvas: Canvas
    title: Title
    style: Style
    nodes: List[Node]
    edges: List[Edge]
    groups: List[Group]
    preset: Optional[str] = None

    def stats(self) -> dict:
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "groups": len(self.groups),
        }
