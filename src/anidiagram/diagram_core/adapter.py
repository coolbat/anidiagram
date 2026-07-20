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


def _consume_css_comment(source: str, index: int) -> int:
    end = source.find("*/", index + 2)
    if end < 0:
        raise ValueError("unterminated CSS comment")
    return end + 2


def _consume_css_string(source: str, index: int) -> int:
    quote = source[index]
    cursor = index + 1
    while cursor < len(source):
        character = source[cursor]
        if character == "\\":
            if cursor + 1 >= len(source):
                raise ValueError("unterminated CSS string escape")
            cursor += 2
        elif character == quote:
            return cursor + 1
        elif character in {"\n", "\r", "\f"}:
            raise ValueError("unescaped newline in CSS string")
        else:
            cursor += 1
    raise ValueError("unterminated CSS string")


def _skip_css_trivia(source: str, index: int) -> int:
    while index < len(source):
        if source[index].isspace():
            index += 1
        elif source.startswith("/*", index):
            index = _consume_css_comment(source, index)
        else:
            break
    return index


def _is_css_name_character(character: str) -> bool:
    return (
        character.isalnum()
        or character in {"-", "_"}
        or ord(character) >= 0x80
        or character == "\\"
    )


def _find_css_rule_open(source: str, index: int) -> int:
    bracket_depth = 0
    parenthesis_depth = 0
    while index < len(source):
        if source.startswith("/*", index):
            index = _consume_css_comment(source, index)
            continue
        character = source[index]
        if character in {"'", '"'}:
            index = _consume_css_string(source, index)
            continue
        if character == "[":
            bracket_depth += 1
        elif character == "]":
            bracket_depth -= 1
            if bracket_depth < 0:
                raise ValueError("unbalanced CSS selector brackets")
        elif character == "(":
            parenthesis_depth += 1
        elif character == ")":
            parenthesis_depth -= 1
            if parenthesis_depth < 0:
                raise ValueError("unbalanced CSS selector parentheses")
        elif character == "{" and bracket_depth == 0 and parenthesis_depth == 0:
            return index
        elif character in {"{", "}"}:
            raise ValueError("ambiguous CSS selector block")
        elif character == ";" and bracket_depth == 0 and parenthesis_depth == 0:
            raise ValueError("unsupported CSS at-rule or statement")
        index += 1
    raise ValueError("CSS selector is missing a declaration block")


def _rewritten_css_selector(selector: str, id_mapping: Dict[str, str]) -> str:
    output = []
    index = 0
    bracket_depth = 0
    saw_selector = False
    while index < len(selector):
        if selector.startswith("/*", index):
            end = _consume_css_comment(selector, index)
            output.append(selector[index:end])
            index = end
            continue
        character = selector[index]
        if character in {"'", '"'}:
            end = _consume_css_string(selector, index)
            output.append(selector[index:end])
            saw_selector = True
            index = end
            continue
        if character == "[":
            bracket_depth += 1
            saw_selector = True
        elif character == "]":
            bracket_depth -= 1
            if bracket_depth < 0:
                raise ValueError("unbalanced CSS selector brackets")
        elif character == "\\":
            raise ValueError("CSS selector escapes are unsupported")
        elif character == "@" and bracket_depth == 0:
            raise ValueError("unsupported CSS at-rule")
        elif character == "#" and bracket_depth == 0:
            token_start = index + 1
            token_end = token_start
            while token_end < len(selector) and (
                selector[token_end].islower()
                or selector[token_end].isdigit()
                or selector[token_end] == "-"
            ):
                token_end += 1
            if token_end == token_start:
                raise ValueError("ambiguous CSS id selector")
            if token_end < len(selector) and _is_css_name_character(
                selector[token_end]
            ):
                raise ValueError("unsupported CSS id selector syntax")
            old_id = validated_kebab_token(selector[token_start:token_end])
            if old_id not in id_mapping:
                raise ValueError("unresolved CSS id selector: #{0}".format(old_id))
            output.append("#" + id_mapping[old_id])
            saw_selector = True
            index = token_end
            continue
        elif (
            character == ":"
            and bracket_depth == 0
            and selector.startswith(":root", index)
            and (
                index + len(":root") == len(selector)
                or not _is_css_name_character(selector[index + len(":root")])
            )
        ):
            output.append(":scope")
            saw_selector = True
            index += len(":root")
            continue
        elif not character.isspace():
            saw_selector = True
        output.append(character)
        index += 1
    if bracket_depth != 0:
        raise ValueError("unbalanced CSS selector brackets")
    if not saw_selector:
        raise ValueError("empty CSS selector")
    return "".join(output)


def _find_css_declaration_close(source: str, index: int) -> int:
    while index < len(source):
        if source.startswith("/*", index):
            index = _consume_css_comment(source, index)
            continue
        character = source[index]
        if character in {"'", '"'}:
            index = _consume_css_string(source, index)
            continue
        if character == "{":
            raise ValueError("nested CSS rules are unsupported")
        if character == "}":
            return index
        index += 1
    raise ValueError("unterminated CSS declaration block")


def _css_url_open(source: str, index: int) -> Optional[int]:
    if source[index : index + 3].lower() != "url":
        return None
    if index and _is_css_name_character(source[index - 1]):
        return None
    after_name = index + 3
    if after_name < len(source) and _is_css_name_character(source[after_name]):
        return None
    opening = _skip_css_trivia(source, after_name)
    return opening if opening < len(source) and source[opening] == "(" else None


def _rewritten_css_url(
    source: str,
    opening: int,
    id_mapping: Dict[str, str],
) -> tuple:
    index = _skip_css_trivia(source, opening + 1)
    quote = source[index] if index < len(source) and source[index] in {"'", '"'} else ""
    if quote:
        string_end = _consume_css_string(source, index)
        target = source[index + 1 : string_end - 1]
        if "\\" in target:
            raise ValueError("CSS url() escapes are unsupported")
        closing = _skip_css_trivia(source, string_end)
        if closing >= len(source) or source[closing] != ")":
            raise ValueError("malformed CSS url() reference")
    else:
        target_start = index
        while index < len(source) and source[index] != ")":
            if source.startswith("/*", index) or source[index] in {"'", '"', "\\", "("}:
                raise ValueError("ambiguous CSS url() reference")
            index += 1
        if index >= len(source):
            raise ValueError("unterminated CSS url() reference")
        closing = index
        target = source[target_start:closing].strip()
    rewritten = _rewritten_reference(target, id_mapping)
    normalized = "url(" + (quote + rewritten + quote if quote else rewritten) + ")"
    return normalized, closing + 1


def _rewritten_css_declarations(
    declarations: str,
    id_mapping: Dict[str, str],
) -> str:
    output = []
    cursor = 0
    index = 0
    while index < len(declarations):
        if declarations.startswith("/*", index):
            index = _consume_css_comment(declarations, index)
            continue
        character = declarations[index]
        if character in {"'", '"'}:
            index = _consume_css_string(declarations, index)
            continue
        opening = _css_url_open(declarations, index)
        if opening is None:
            index += 1
            continue
        rewritten_url, after_url = _rewritten_css_url(
            declarations,
            opening,
            id_mapping,
        )
        output.append(declarations[cursor:index])
        output.append(rewritten_url)
        cursor = after_url
        index = after_url
    output.append(declarations[cursor:])
    return "".join(output)


def _scoped_css(
    source: str,
    root_dom_id: str,
    id_mapping: Dict[str, str],
) -> str:
    body = []
    cursor = 0
    rule_count = 0
    while cursor < len(source):
        significant = _skip_css_trivia(source, cursor)
        if significant == len(source):
            body.append(source[cursor:])
            break
        opening = _find_css_rule_open(source, significant)
        rewritten_selector = _rewritten_css_selector(
            source[cursor:opening], id_mapping
        )
        closing = _find_css_declaration_close(source, opening + 1)
        body.append(rewritten_selector)
        body.append("{")
        body.append(
            _rewritten_css_declarations(source[opening + 1 : closing], id_mapping)
        )
        body.append("}")
        cursor = closing + 1
        rule_count += 1
    if rule_count == 0:
        raise ValueError("style element must contain a CSS rule")
    return "@scope (#{0}) {{{1}}}".format(root_dom_id, "".join(body))


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

    root_dom_id = clone.attrib["id"]
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
        if _local_name(element.tag).lower() == "style":
            element.text = _scoped_css(element.text or "", root_dom_id, old_to_new)
        elif element.text:
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
    state: Optional[str],
    size: Real,
    x: Real,
    y: Real,
    tokens: Optional[Mapping],
    asset_root,
    allowed_statuses: FrozenSet[str],
) -> str:
    validated_kebab_token(icon_id)
    instance_key(instance_id)
    if state is not None:
        validated_kebab_token(state)
    _validated_number(x, "x")
    _validated_number(y, "y")
    _validated_number(size, "size", positive=True)
    style = _resolved_token_style(tokens)

    asset = load_asset(icon_id, allowed_statuses, asset_root)
    if state is not None and state not in asset.manifest.states:
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
    if state is not None:
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
    state=None,
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
    state=None,
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
