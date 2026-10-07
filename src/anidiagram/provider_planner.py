"""Opt-in provider-neutral subprocess protocol; no shell or bundled credentials."""
from __future__ import annotations

import json
import math
import subprocess
from typing import Any, Dict, List, Optional

from .composition import compile_plan_v02
from .localization import resolve_locale
from .planning import subprocess_diagnostics



def _json_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('duplicate JSON object key')
        value[key] = item
    return value


def _invalid_constant(value):
    raise ValueError('non-finite JSON constant')


def subprocess_to_plan(brief: str, title: str, style: Optional[str], language: str,
                       command: Optional[List[str]], timeout: float) -> Dict[str, Any]:
    if not isinstance(brief, str) or not isinstance(title, str) or (style is not None and not isinstance(style, str)):
        raise ValueError('Planner brief, title, and optional style must be text')
    if not isinstance(command, list) or not command or any(not isinstance(arg, str) or not arg or '\x00' in arg for arg in command):
        raise ValueError('subprocess planner requires a non-empty argv array via --planner-command')
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0 or timeout > 300:
        raise ValueError('planner timeout must be greater than 0 and at most 300 seconds')
    request = {'protocol': 'anidiagram-planner-v1', 'brief': brief, 'title': title, 'style': style or 'auto',
               'language': resolve_locale(language, (title, brief)), 'output_schema': 'diagram-plan-v0.2'}
    try:
        result = subprocess.run(command, input=json.dumps(request, ensure_ascii=False), capture_output=True,
                                text=True, encoding='utf-8', timeout=timeout, check=False, shell=False)
    except subprocess.TimeoutExpired:
        raise ValueError('Planner command timed out; provider output and stderr were withheld.') from None
    except (OSError, UnicodeError):
        raise ValueError('Planner command could not execute or returned invalid UTF-8; command details were withheld.') from None
    if result.returncode:
        raise ValueError('Planner command failed with exit code ' + str(result.returncode) + '; provider stderr was withheld.')
    if len(result.stdout.encode("utf-8")) > 2_000_000:
        raise ValueError('Planner output exceeds the 2 MB JSON limit.')
    try:
        plan = json.loads(result.stdout, object_pairs_hook=_json_object, parse_constant=_invalid_constant)
        if not isinstance(plan, dict) or plan.get('version') != '0.2':
            raise ValueError('wrong plan version')
        # Validate the original provider response before adding truthful local diagnostics.
        compile_plan_v02(plan)
        plan['planning'] = subprocess_diagnostics()
        if title:
            plan['semantic']['title'] = title
        if style:
            plan.setdefault('presentation', {})['style'] = style
        if language != 'auto':
            plan['semantic']['language'] = language
        sources = plan['semantic'].setdefault('sources', [])
        source_id = 'planner-input-brief'
        all_ids = {item['id'] for key in ('entities', 'relations', 'flows', 'sources', 'groups') for item in plan['semantic'].get(key, [])}
        while source_id in all_ids:
            source_id += '-source'
        sources.append({'id': source_id, 'type': 'brief', 'title': 'Original planner input', 'note': brief})
        compile_plan_v02(plan)
    except (ValueError, TypeError, KeyError, RecursionError):
        raise ValueError('Planner returned invalid DiagramPlan v0.2 JSON; provider output was withheld.') from None
    return plan
