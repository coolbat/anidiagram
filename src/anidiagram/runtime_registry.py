"""Resolve historical runtime contracts through the shared module inventory."""
from __future__ import annotations

import json
from pathlib import PurePosixPath

from .resources import resource_path


def archived_runtime_source(contract: str) -> str:
    inventory = json.loads(resource_path('runtime', 'modules.json').read_text(encoding='utf-8'))
    filename = inventory.get('archived', {}).get(contract)
    if not isinstance(filename, str):
        raise ValueError('Unknown archived runtime contract: ' + contract)
    if PurePosixPath(filename).name != filename or '\\' in filename or not filename.endswith('.js'):
        raise ValueError('Invalid archived runtime filename for contract: ' + contract)
    return resource_path('runtime', filename).read_text(encoding='utf-8')
