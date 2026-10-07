"""One inventory for frozen Illustrated batches and their accepted composition.

Historical modules stay importable and byte-for-byte intact. Only explicitly
listed convention revisions may shadow an earlier icon's static definition.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


@dataclass(frozen=True)
class IllustratedSource:
    id: str
    module: str
    version: str
    definitions: Optional[str] = None
    metadata: Optional[str] = None
    motion_module: Optional[str] = None
    performances: Optional[str] = None
    rest_at: Optional[str] = None
    motion_specs: Optional[str] = None
    archived_contract: Optional[str] = None
    overrides: Tuple[str, ...] = ()


_CONVENTION_OVERRIDES = ('branch', 'ci-cd', 'data-warehouse', 'deployment', 'document-store', 'gateway',
                         'git-repository', 'memory', 'output', 'pull-request', 'token', 'webhook')

ILLUSTRATED_SOURCES = (
    IllustratedSource('character-v2', 'illustrated_character_v2_icons', '2.0.0',
                      'ILLUSTRATED_CHARACTER_V2_CONCEPTS', 'ILLUSTRATED_SYSTEM_METADATA'),
    IllustratedSource('expansion-1', 'illustrated_expansion_batch_1', '2.1.0',
                      'ILLUSTRATED_EXPANSION_BATCH_1', 'ILLUSTRATED_EXPANSION_BATCH_1_METADATA'),
    IllustratedSource('expansion-2', 'illustrated_expansion_batch_2', '2.2.0',
                      'ILLUSTRATED_EXPANSION_BATCH_2', 'ILLUSTRATED_EXPANSION_BATCH_2_METADATA'),
    IllustratedSource('expansion-3', 'illustrated_expansion_batch_3', '2.3.0',
                      'ILLUSTRATED_EXPANSION_BATCH_3', 'ILLUSTRATED_EXPANSION_BATCH_3_METADATA'),
    IllustratedSource('expansion-4', 'illustrated_expansion_batch_4', '2.4.0',
                      'ILLUSTRATED_EXPANSION_BATCH_4', 'ILLUSTRATED_EXPANSION_BATCH_4_METADATA',
                      'illustrated_expansion_batch_4_motion', 'ILLUSTRATED_V5_REVIEW_ICON_PERFORMANCES',
                      'ILLUSTRATED_V5_REVIEW_REST_AT', archived_contract='illustrated-performance-v5-review'),
    IllustratedSource('expansion-5', 'illustrated_expansion_batch_5', '2.5.0',
                      'ILLUSTRATED_EXPANSION_BATCH_5', 'ILLUSTRATED_EXPANSION_BATCH_5_METADATA',
                      'illustrated_expansion_batch_5_motion', 'ILLUSTRATED_V6_REVIEW_ICON_PERFORMANCES',
                      'ILLUSTRATED_V6_REVIEW_REST_AT', archived_contract='illustrated-performance-v6-review'),
    IllustratedSource('expansion-6-10', 'illustrated_expansion_batches_6_10', '2.5.0',
                      'ILLUSTRATED_EXPANSION_BATCHES_6_10', 'ILLUSTRATED_EXPANSION_6_10_METADATA',
                      'illustrated_expansion_batches_6_10_motion', 'ILLUSTRATED_V7_REVIEW_ICON_PERFORMANCES',
                      'ILLUSTRATED_V7_REVIEW_REST_AT', 'ILLUSTRATED_V7_REVIEW_MOTION_SPECS',
                      archived_contract='illustrated-performance-v7-review'),
    IllustratedSource('convention-alignment', 'illustrated_convention_alignment_review', '2.5.0',
                      'ILLUSTRATED_CONVENTION_ALIGNMENT_DEFINITIONS', 'CONVENTION_ALIGNMENT_METADATA',
                      overrides=_CONVENTION_OVERRIDES),
)


def source_value(source_id: str, field: str) -> Any:
    source = next((item for item in ILLUSTRATED_SOURCES if item.id == source_id), None)
    if source is None:
        raise ValueError('Unknown Illustrated source: ' + source_id)
    if field not in {'definitions', 'metadata', 'performances', 'rest_at', 'motion_specs'}:
        raise ValueError('Unknown Illustrated source field: ' + field)
    attribute = getattr(source, field)
    if attribute is None:
        raise ValueError('Illustrated source has no ' + field + ': ' + source_id)
    module = source.motion_module if field in {'performances', 'rest_at', 'motion_specs'} else source.module
    return getattr(import_module('.' + str(module), __package__), attribute)


def merge_registered_maps(entries: Iterable[Tuple[str, Mapping[str, Any], Tuple[str, ...]]]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    seen_sources = set()
    for source_id, values, overrides in entries:
        if source_id in seen_sources:
            raise ValueError('duplicate source registration: ' + source_id)
        seen_sources.add(source_id)
        unexpected = set(merged).intersection(values).difference(overrides)
        if unexpected:
            raise ValueError('duplicate Illustrated keys without approved overrides in ' + source_id + ': ' + ', '.join(sorted(unexpected)))
        merged.update(values)
    return merged


def compose_static_definitions() -> Dict[str, Any]:
    return merge_registered_maps((source.id, source_value(source.id, 'definitions'), source.overrides)
                                 for source in ILLUSTRATED_SOURCES if source.definitions)


def compose_motion_values(field: str, baseline: Mapping[str, Any]) -> Dict[str, Any]:
    """Preserve the approved public baseline followed by the 2.5 expansion slices."""
    return merge_registered_maps([
        ('public-2.4-baseline', baseline, ()),
        ('expansion-5', source_value('expansion-5', field), ()),
        ('expansion-6-10', source_value('expansion-6-10', field), ()),
    ])
