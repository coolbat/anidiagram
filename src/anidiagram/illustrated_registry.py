"""Current public registry for the 56-icon Illustrated 2.5.0 system.

The 2.0.0 baseline and the 2.1.0 through 2.4.0 snapshots remain frozen.  The
current registry composes their public definitions with the six approved 2.5
expansion batches, then applies the twelve convention-alignment revisions.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .icon_system import ILLUSTRATED_ICON_SYSTEM, ILLUSTRATED_ICON_SYSTEM_VERSION
from .illustrated_character_icons import CharacterIconDefinition
from .illustrated_sources import compose_static_definitions, source_value

# Keep historical imported names available to downstream review tooling.
ILLUSTRATED_CHARACTER_V2_CONCEPTS = source_value("character-v2", "definitions")
ILLUSTRATED_EXPANSION_BATCH_1 = source_value("expansion-1", "definitions")
ILLUSTRATED_EXPANSION_BATCH_2 = source_value("expansion-2", "definitions")
ILLUSTRATED_EXPANSION_BATCH_3 = source_value("expansion-3", "definitions")
ILLUSTRATED_EXPANSION_BATCH_4 = source_value("expansion-4", "definitions")
ILLUSTRATED_EXPANSION_BATCH_5 = source_value("expansion-5", "definitions")
ILLUSTRATED_EXPANSION_BATCHES_6_10 = source_value("expansion-6-10", "definitions")
ILLUSTRATED_CONVENTION_ALIGNMENT_DEFINITIONS = source_value("convention-alignment", "definitions")


ILLUSTRATED_SYSTEM_METADATA = {
    "id": ILLUSTRATED_ICON_SYSTEM,
    "display_name": "Illustrated",
    "display_name_zh": "插画",
    "version": ILLUSTRATED_ICON_SYSTEM_VERSION,
    "static_status": "approved",
    "motion_status": "approved",
    "motion_contract": "illustrated-performance-v6",
    "previous_motion_contract": "illustrated-performance-v5",
    "archived_motion_review_contract": "illustrated-performance-v7-review",
    "previous_archived_motion_review_contract": "illustrated-performance-v6-review",
}

ILLUSTRATED_DEFINITIONS: Dict[str, CharacterIconDefinition] = compose_static_definitions()

ILLUSTRATED_ICON_STATUSES = {icon_id: "approved" for icon_id in ILLUSTRATED_DEFINITIONS}


def illustrated_definition(icon: str) -> CharacterIconDefinition | None:
    return ILLUSTRATED_DEFINITIONS.get(icon)


def illustrated_icon_ids() -> Tuple[str, ...]:
    return tuple(ILLUSTRATED_DEFINITIONS)


def illustrated_icon_status(icon: str) -> str | None:
    return ILLUSTRATED_ICON_STATUSES.get(icon)


# Compatibility aliases for internal callers that still use the old v2 name.
character_v2_definition = illustrated_definition
character_v2_icon_ids = illustrated_icon_ids
