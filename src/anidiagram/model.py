"""Typed intermediate representation for AniDiagram scenes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


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
class EffectConfig:
    preset: str = "none"
    explicit: bool = False
    line: Optional[str] = None
    particle: Optional[str] = None
    trail: Optional[str] = None
    particle_count: Optional[int] = None
    trail_count: Optional[int] = None
    entry: Optional[str] = None
    accent: Optional[str] = None
    icon: Optional[str] = None
    icon_motion: Optional[str] = None


@dataclass(frozen=True)
class MotionPolicy:
    profile: str = "unrestricted"
    motion_area: str = "auto"
    max_active_flow_edges: Optional[int] = None
    max_particle_edges: Optional[int] = None
    particle_count_per_edge: Optional[int] = None
    flow_trail_count: Optional[int] = None
    max_active_pulse_nodes: Optional[int] = None
    pulse_mode: str = "all"
    max_scanning_groups: Optional[int] = None


@dataclass(frozen=True)
class SceneMotion:
    profile: str = "expressive"
    sequence: str = "layered"
    ease: str = "spring"
    stagger: float = 0.16
    duration_scale: float = 0.9
    intensity: float = 1.25
    node: str = "pop"
    edge: str = "packet-flow"
    group: str = "marching-ants"
    reduced_motion: str = "subtle"
    edge_effect: EffectConfig = field(default_factory=lambda: EffectConfig("packet-flow"))
    node_effect: EffectConfig = field(default_factory=lambda: EffectConfig("pop"))
    group_effect: EffectConfig = field(default_factory=lambda: EffectConfig("marching-ants"))
    title_effect: EffectConfig = field(default_factory=lambda: EffectConfig("highlight-sweep"))


@dataclass(frozen=True)
class Node:
    node_id: str
    label: str
    caption: str
    position: Point
    size: Point
    shape: str = "rect"
    role: str = "neutral"
    step: Optional[int] = None
    radius: Optional[float] = None
    fill: Optional[str] = None
    stroke: Optional[str] = None
    stroke_width: Optional[float] = None
    icon: Optional[str] = None
    semantic_kind: Optional[str] = None
    icon_resolution: Optional[str] = None
    importance: Optional[str] = None
    state: Dict[str, str] = field(default_factory=dict)
    effect: EffectConfig = field(default_factory=EffectConfig)


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    label: str = ""
    role: str = "neutral"
    direction: str = "forward"
    route: str = "curved"
    step: Optional[int] = None
    points: Tuple[Point, ...] = field(default_factory=tuple)
    stroke: Optional[str] = None
    width: Optional[float] = None
    semantic_relation_id: Optional[str] = None
    semantic_kind: Optional[str] = None
    importance: Optional[str] = None
    condition: Optional[str] = None
    protocol: Optional[str] = None
    flow_id: Optional[str] = None
    flow_importance: Optional[str] = None
    flow_repeat: Optional[str] = None
    motion: Motion = field(default_factory=Motion)
    effect: EffectConfig = field(default_factory=EffectConfig)


@dataclass(frozen=True)
class Group:
    group_id: str
    label: str
    bounds: Bounds
    role: str = "neutral"
    fill: Optional[str] = None
    stroke: Optional[str] = None
    semantic_kind: Optional[str] = None
    importance: Optional[str] = None
    parent: Optional[str] = None
    effect: EffectConfig = field(default_factory=EffectConfig)
    members: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Scene:
    version: str
    canvas: Canvas
    title: Title
    style: Style
    nodes: List[Node]
    edges: List[Edge]
    groups: List[Group]
    locale: str = "en"
    icon_system: Optional[str] = None
    composition_policy: Optional[str] = None
    resolved_presentation: Dict[str, Any] = field(default_factory=dict)
    motion: SceneMotion = field(default_factory=SceneMotion)
    motion_policy: MotionPolicy = field(default_factory=MotionPolicy)
    preset: Optional[str] = None
    layout: Optional[str] = None
    source_evidence: Dict[str, Any] = field(default_factory=dict)
    reader: Dict[str, Any] = field(default_factory=dict)
    type_semantics: Dict[str, Any] = field(default_factory=dict)
    planning: Dict[str, Any] = field(default_factory=dict)

    def stats(self) -> dict:
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "groups": len(self.groups),
        }
