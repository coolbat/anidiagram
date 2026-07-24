"""Current public registry for the 56-icon Illustrated 2.5.0 system.

The 2.0.0 baseline and the 2.1.0 through 2.4.0 snapshots remain frozen.  The
current registry composes their public definitions with the six approved 2.5
expansion batches, then applies the twelve convention-alignment revisions.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .icon_system import ILLUSTRATED_ICON_SYSTEM, ILLUSTRATED_ICON_SYSTEM_VERSION
from .illustrated_character_icons import CharacterIconDefinition
from .illustrated_character_v2_icons import ILLUSTRATED_CHARACTER_V2_CONCEPTS
from .illustrated_expansion_batch_1 import ILLUSTRATED_EXPANSION_BATCH_1
from .illustrated_expansion_batch_2 import ILLUSTRATED_EXPANSION_BATCH_2
from .illustrated_expansion_batch_3 import ILLUSTRATED_EXPANSION_BATCH_3
from .illustrated_expansion_batch_4 import ILLUSTRATED_EXPANSION_BATCH_4
from .illustrated_expansion_batch_5 import ILLUSTRATED_EXPANSION_BATCH_5
from .illustrated_expansion_batches_6_10 import ILLUSTRATED_EXPANSION_BATCHES_6_10
from .illustrated_convention_alignment_review import ILLUSTRATED_CONVENTION_ALIGNMENT_DEFINITIONS


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

ILLUSTRATED_DEFINITIONS: Dict[str, CharacterIconDefinition] = {
    **ILLUSTRATED_CHARACTER_V2_CONCEPTS,
    **ILLUSTRATED_EXPANSION_BATCH_1,
    **ILLUSTRATED_EXPANSION_BATCH_2,
    **ILLUSTRATED_EXPANSION_BATCH_3,
    **ILLUSTRATED_EXPANSION_BATCH_4,
    **ILLUSTRATED_EXPANSION_BATCH_5,
    **ILLUSTRATED_EXPANSION_BATCHES_6_10,
    **ILLUSTRATED_CONVENTION_ALIGNMENT_DEFINITIONS,
}

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
