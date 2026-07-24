"""Shared constructor for Illustrated semantic motion specifications."""

from __future__ import annotations


def illustrated_motion_spec(sequence, recipe, prepare, action, result, rest_at):
    return {
        "sequence": tuple(sequence),
        "recipe": recipe,
        "prepare_parts": tuple(prepare),
        "action_parts": tuple(action),
        "result_parts": tuple(result),
        "rest_at": rest_at,
    }
