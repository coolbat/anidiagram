"""Canonical SVG instancing for Diagram Core preview and approved assets."""

from __future__ import annotations

import copy
import math
import re
from collections.abc import Mapping
from numbers import Real
from typing import Dict, FrozenSet, Optional
from xml.etree import ElementTree

from .asset_loader import load_asset
from .catalog import CATALOG_SYSTEM_ID
from .instance_ids import instance_key, part_dom_id, validated_kebab_token
from .tokens import relative_luminance


_SVG_NAMESPACE = "http://www.w3.org/2000/svg"
_XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
_URL_OPEN = re.compile(r"url\s*\(", re.IGNORECASE)
_TOKEN_KEYS: FrozenSet[str] = frozenset(
    {
        "--icon-surface-main",
        "--icon-surface-secondary",
        "--icon-surface-recessed",
        "--icon-stroke",
        "--icon-detail",
        "--icon-accent",
        "--icon-accent-secondary",
        "--icon-status-idle",
        "--icon-status-active",
        "--icon-status-success",
        "--icon-status-warning",
        "--icon-status-error",
    }
)

ElementTree.register_namespace("", _SVG_NAMESPACE)
ElementTree.register_namespace("xlink", _XLINK_NAMESPACE)


def _local_name(name: str) -> str:
    return name.rsplit("}", 1)[-1]


def _rewritten_reference(reference: str, id_mapping: Dict[str, str]) -> str:
    if not reference.startswith("#") or len(reference) == 1:
        raise ValueError("external SVG references are forbidden")
    target = reference[1:]
    if target not in id_mapping:
        raise ValueError("unresolved local SVG reference: #{0}".format(target))
    return "#" + id_mapping[target]


def _rewrite_url_calls(value: str, id_mapping: Dict[str, str]) -> str:
    output = []
    cursor = 0
    while True:
        match = _URL_OPEN.search(value, cursor)
        if match is None:
            output.append(value[cursor:])
            return "".join(output)
        output.append(value[cursor : match.start()])
        index = match.end()
        while index < len(value) and value[index].isspace():
            index += 1
        quote = value[index] if index < len(value) and value[index] in {"'", '"'} else ""
        if quote:
            target_start = index + 1
            target_end = value.find(quote, target_start)
            if target_end < 0:
                raise ValueError("unterminated quoted SVG url() reference")
            closing = target_end + 1
            while closing < len(value) and value[closing].isspace():
                closing += 1
            if closing >= len(value) or value[closing] != ")":
                raise ValueError("malformed SVG url() reference")
            target = value[target_start:target_end]
        else:
            target_start = index
            closing = value.find(")", target_start)
            if closing < 0:
                raise ValueError("unterminated SVG url() reference")
            target = value[target_start:closing].strip()
        rewritten = _rewritten_reference(target, id_mapping)
        output.append("url(")
        if quote:
            output.extend((quote, rewritten, quote))
        else:
            output.append(rewritten)
        output.append(")")
        cursor = closing + 1


def namespace_svg_instance(
    root: ElementTree.Element,
    instance_id: str,
    icon_id: str,
) -> ElementTree.Element:
    """Clone an SVG subtree and scope all DOM identities and local references."""

    if not ElementTree.iselement(root):
        raise ValueError("root must be an XML element")
    validated_kebab_token(icon_id)
    instance_key(instance_id)
    clone = copy.deepcopy(root)

    old_to_new: Dict[str, str] = {}
    assignments = []
    seen_old_ids = set()
    seen_new_ids = set()
    for element in clone.iter():
        old_id = element.attrib.get("id")
        part_name = element.attrib.get("data-part")
        if old_id is not None:
            validated_kebab_token(old_id)
            if old_id in seen_old_ids:
                raise ValueError("duplicate authored SVG id: {0}".format(old_id))
            seen_old_ids.add(old_id)
        if part_name is not None:
            validated_kebab_token(part_name)

        if element is clone:
            assigned_part = "root"
        elif part_name is not None:
            assigned_part = part_name
        else:
            assigned_part = old_id
        if assigned_part is None:
            continue
        new_id = part_dom_id(instance_id, icon_id, assigned_part)
        if new_id in seen_new_ids:
            raise ValueError("duplicate namespaced SVG id: {0}".format(new_id))
        seen_new_ids.add(new_id)
        assignments.append((element, new_id))
        if old_id is not None:
            old_to_new[old_id] = new_id

    for element, new_id in assignments:
        element.set("id", new_id)

    for element in clone.iter():
        for raw_name, value in tuple(element.attrib.items()):
            name = _local_name(raw_name).lower()
            if name == "id":
                continue
            if name == "href":
                element.set(raw_name, _rewritten_reference(value.strip(), old_to_new))
                continue
            if name in {"aria-labelledby", "aria-describedby"}:
                targets = value.split()
                if not targets:
                    raise ValueError("empty SVG ARIA id reference")
                try:
                    rewritten_targets = [old_to_new[target] for target in targets]
                except KeyError as error:
                    raise ValueError(
                        "unresolved SVG ARIA id reference: {0}".format(error.args[0])
                    ) from error
                element.set(raw_name, " ".join(rewritten_targets))
                continue
            element.set(raw_name, _rewrite_url_calls(value, old_to_new))
        if element.text:
            element.text = _rewrite_url_calls(element.text, old_to_new)
        if element.tail:
            element.tail = _rewrite_url_calls(element.tail, old_to_new)
    return clone


def _validated_number(value: Real, name: str, positive: bool = False) -> Real:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("{0} must be a finite number".format(name))
    try:
        numeric = float(value)
    except (OverflowError, TypeError, ValueError) as error:
        raise ValueError("{0} must be a finite number".format(name)) from error
    if not math.isfinite(numeric):
        raise ValueError("{0} must be a finite number".format(name))
    if positive and numeric <= 0:
        raise ValueError("{0} must be greater than zero".format(name))
    return value


def _number_text(value: Real) -> str:
    numeric = float(value)
    if numeric == 0:
        return "0"
    return format(numeric, ".15g")


def _resolved_token_style(tokens: Optional[Mapping]) -> Optional[str]:
    if tokens is None:
        return None
    if not isinstance(tokens, Mapping):
        raise ValueError("tokens must be a mapping")
    resolved = {}
    for token, value in tokens.items():
        if not isinstance(token, str) or token not in _TOKEN_KEYS:
            raise ValueError("unsupported Diagram Core icon token: {0}".format(token))
        relative_luminance(value)
        resolved[token] = value
    return ";".join(
        "{0}:{1}".format(token, resolved[token]) for token in sorted(resolved)
    )


def _render_icon(
    icon_id: str,
    instance_id: str,
    state: str,
    size: Real,
    x: Real,
    y: Real,
    tokens: Optional[Mapping],
    asset_root,
    allowed_statuses: FrozenSet[str],
) -> str:
    validated_kebab_token(icon_id)
    instance_key(instance_id)
    validated_kebab_token(state)
    _validated_number(x, "x")
    _validated_number(y, "y")
    _validated_number(size, "size", positive=True)
    style = _resolved_token_style(tokens)

    asset = load_asset(icon_id, allowed_statuses, asset_root)
    if state not in asset.manifest.states:
        raise ValueError(
            "unsupported state {0} for Diagram Core icon {1}".format(state, icon_id)
        )

    wrapper = ElementTree.Element("{{{0}}}g".format(_SVG_NAMESPACE))
    wrapper.set(
        "transform",
        "translate({0} {1}) scale({2})".format(
            _number_text(x),
            _number_text(y),
            _number_text(float(size) / 96.0),
        ),
    )
    wrapper.set("data-icon", icon_id)
    wrapper.set("data-icon-state", state)
    wrapper.set("data-icon-source", CATALOG_SYSTEM_ID)
    wrapper.set("data-asset-revision", str(asset.manifest.asset_revision))
    wrapper.set("aria-hidden", "true")
    if style is not None:
        wrapper.set("style", style)
    for child in asset.root:
        wrapper.append(copy.deepcopy(child))

    namespaced = namespace_svg_instance(wrapper, instance_id, icon_id)
    return ElementTree.tostring(namespaced, encoding="unicode", short_empty_elements=True)


def render_preview_icon(
    icon_id,
    instance_id,
    state="idle",
    size=96,
    x=0,
    y=0,
    tokens=None,
    asset_root=None,
):
    """Render a visual-review or approved canonical asset as an SVG fragment."""

    return _render_icon(
        icon_id,
        instance_id,
        state,
        size,
        x,
        y,
        tokens,
        asset_root,
        frozenset({"visual-review", "approved"}),
    )


def render_approved_icon(
    icon_id,
    instance_id,
    state="idle",
    size=96,
    x=0,
    y=0,
    tokens=None,
    asset_root=None,
):
    """Render only an approved canonical asset as an SVG fragment."""

    return _render_icon(
        icon_id,
        instance_id,
        state,
        size,
        x,
        y,
        tokens,
        asset_root,
        frozenset({"approved"}),
    )


__all__ = [
    "namespace_svg_instance",
    "render_approved_icon",
    "render_preview_icon",
]
