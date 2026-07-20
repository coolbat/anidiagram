"""Current public registry for the Illustrated icon system.

The 2.0.0 baseline remains frozen in ``illustrated_character_v2_icons``.
Illustrated 2.1.0 composes that baseline with the first human-approved
coverage expansion without rewriting the archived 2.0.0 source snapshot.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .icon_system import ILLUSTRATED_ICON_SYSTEM, ILLUSTRATED_ICON_SYSTEM_VERSION
from .illustrated_character_icons import CharacterIconDefinition
from .illustrated_character_v2_icons import ILLUSTRATED_CHARACTER_V2_CONCEPTS
from .illustrated_expansion_batch_1 import ILLUSTRATED_EXPANSION_BATCH_1


ILLUSTRATED_SYSTEM_METADATA = {
    "id": ILLUSTRATED_ICON_SYSTEM,
    "display_name": "Illustrated",
    "display_name_zh": "插画",
    "version": ILLUSTRATED_ICON_SYSTEM_VERSION,
    "static_status": "approved",
    "motion_status": "approved",
    "motion_contract": "illustrated-performance-v2",
}

ILLUSTRATED_DEFINITIONS: Dict[str, CharacterIconDefinition] = {
    **ILLUSTRATED_CHARACTER_V2_CONCEPTS,
    **ILLUSTRATED_EXPANSION_BATCH_1,
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
