"""Fail-closed loading for canonical Diagram Core SVG assets."""

from __future__ import annotations

import gzip
import re
import xml.etree.ElementTree as ElementTree
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple

from ..resources import resource_path

from .catalog import (
    CATALOG_STATUSES,
    CatalogValidationError,
    catalog_entry,
    load_catalog,
)
from .manifest import (
    IconManifest,
    ManifestValidationError,
    load_manifest,
)


_DEFAULT_ASSET_ROOT = resource_path("assets", "diagram-core")
_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_TOKEN_PATTERN = re.compile(r"--[a-z][a-z0-9-]*")
_CSS_COMMENT_PATTERN = re.compile(r"/\*.*?\*/", re.DOTALL)
_URL_PATTERN = re.compile(r"url\s*\(\s*([^)]*?)\s*\)", re.IGNORECASE)
_FORBIDDEN_TAGS = frozenset(
    {
        "script",
        "foreignObject",
        "image",
        "text",
        "animate",
        "animateMotion",
        "animateTransform",
        "set",
        "discard",
        "filter",
    }
)
_ANIMATION_ATTRIBUTES = frozenset(
    {
        "begin",
        "dur",
        "end",
        "keyPoints",
        "keySplines",
        "keyTimes",
        "repeatCount",
        "repeatDur",
    }
)
_PAINTABLE_TAGS = frozenset(
    {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "use"}
)
_SVG_NAMESPACE = "http://www.w3.org/2000/svg"
_XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
_XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"
_RAW_SIZE_LIMIT = 12 * 1024
_GZIP_SIZE_LIMIT = 6 * 1024
_PAINTABLE_LIMIT = 24


@dataclass(frozen=True)
class AssetValidationIssue:
    path: str
    message: str


class AssetValidationError(ValueError):
    """Raised with every independently detectable asset issue."""

    def __init__(self, issues: Iterable[AssetValidationIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__(
            "; ".join(
                "{0}: {1}".format(issue.path, issue.message)
                for issue in self.issues
            )
        )


@dataclass(frozen=True)
class AssetMetrics:
    forbidden_elements: int
    paintable_elements: int
    total_dom_elements: int
    raw_size_bytes: int
    gzip_size_bytes: int


@dataclass(frozen=True)
class LoadedAsset:
    manifest: IconManifest
    svg_source: str
    root: ElementTree.Element
    public_parts: Tuple[str, ...]
    metrics: AssetMetrics


def _issue(issues: list, path: str, message: str) -> None:
    issues.append(AssetValidationIssue(path=path, message=message))


def _asset_root(asset_root: Optional[Path]) -> Path:
    return _DEFAULT_ASSET_ROOT if asset_root is None else Path(asset_root)


def _safe_icon_id(icon_id: str) -> None:
    if not isinstance(icon_id, str) or _IDENTIFIER_PATTERN.fullmatch(icon_id) is None:
        raise AssetValidationError(
            (AssetValidationIssue("$icon_id", "expected a kebab-case identifier"),)
        )


def _read_svg_bytes(icon_id: str, root: Path) -> Tuple[Path, bytes]:
    _safe_icon_id(icon_id)
    path = root / "icons" / (icon_id + ".svg")
    try:
        return path, path.read_bytes()
    except OSError as error:
        raise AssetValidationError(
            (AssetValidationIssue(str(path), "cannot read SVG: {0}".format(error)),)
        ) from error


def load_svg_source(icon_id: str, asset_root: Optional[Path] = None) -> str:
    """Read a canonical SVG as UTF-8 from a Diagram Core asset root."""

    path, source_bytes = _read_svg_bytes(icon_id, _asset_root(asset_root))
    try:
        return source_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AssetValidationError(
            (AssetValidationIssue(str(path), "SVG must be valid UTF-8"),)
        ) from error


def _qualified_name(name: str) -> Tuple[str, str]:
    if name.startswith("{") and "}" in name:
        namespace, local_name = name[1:].split("}", 1)
        return namespace, local_name
    return "", name


def _element_paths(root: ElementTree.Element) -> dict:
    paths = {root: "/" + _qualified_name(root.tag)[1]}

    def visit(parent: ElementTree.Element) -> None:
        children = list(parent)
        totals = Counter(_qualified_name(child.tag)[1] for child in children)
        locations = Counter()
        for child in children:
            local_name = _qualified_name(child.tag)[1]
            locations[local_name] += 1
            suffix = local_name
            if totals[local_name] > 1:
                suffix += "[{0}]".format(locations[local_name])
            paths[child] = paths[parent] + "/" + suffix
            visit(child)

    visit(root)
    return paths


def _skip_css_comment(source: str, index: int) -> int:
    end = source.find("*/", index + 2)
    return len(source) if end < 0 else end + 2


def _skip_css_string(source: str, index: int) -> int:
    quote = source[index]
    index += 1
    while index < len(source):
        if source[index] == "\\":
            index += 2
        elif source[index] == quote:
            return index + 1
        else:
            index += 1
    return len(source)


def _skip_css_spacing_and_comments(source: str, index: int) -> int:
    while index < len(source):
        if source[index].isspace():
            index += 1
        elif source.startswith("/*", index):
            index = _skip_css_comment(source, index)
        else:
            break
    return index


def _declared_tokens(source: str) -> frozenset:
    tokens = set()
    frames = [
        {
            "declarations": False,
            "at_boundary": False,
            "first": None,
        }
    ]
    index = 0
    while index < len(source):
        frame = frames[-1]
        if source.startswith("/*", index):
            index = _skip_css_comment(source, index)
            continue

        character = source[index]
        if character.isspace():
            index += 1
            continue
        if character in {"'", '"'}:
            if frame["first"] is None:
                frame["first"] = character
            if frame["declarations"] and frame["at_boundary"]:
                frame["at_boundary"] = False
            index = _skip_css_string(source, index)
            continue
        if character == "{":
            child_has_declarations = frame["first"] != "@"
            frame["first"] = None
            frame["at_boundary"] = False
            frames.append(
                {
                    "declarations": child_has_declarations,
                    "at_boundary": child_has_declarations,
                    "first": None,
                }
            )
            index += 1
            continue
        if character == "}":
            if len(frames) > 1:
                frames.pop()
            frames[-1]["first"] = None
            frames[-1]["at_boundary"] = False
            index += 1
            continue
        if character == ";":
            frame["first"] = None
            frame["at_boundary"] = frame["declarations"]
            index += 1
            continue

        if frame["first"] is None:
            frame["first"] = character
        if frame["declarations"] and frame["at_boundary"]:
            match = _TOKEN_PATTERN.match(source, index)
            if match is not None:
                colon = _skip_css_spacing_and_comments(source, match.end())
                if colon < len(source) and source[colon] == ":":
                    tokens.add(match.group(0))
                    frame["at_boundary"] = False
                    index = colon + 1
                    continue
            frame["at_boundary"] = False
        index += 1
    return frozenset(tokens)


def _var_expressions(value: str) -> Tuple[Tuple[str, str], ...]:
    expressions = []
    cursor = 0
    lower_value = value.lower()
    while True:
        match = re.search(r"\bvar\s*\(", lower_value[cursor:])
        if match is None:
            break
        start = cursor + match.start()
        open_parenthesis = cursor + match.end() - 1
        depth = 1
        quote = None
        index = open_parenthesis + 1
        while index < len(value) and depth:
            character = value[index]
            if quote is not None:
                if character == quote and value[index - 1] != "\\":
                    quote = None
            elif character in {"'", '"'}:
                quote = character
            elif character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
            index += 1
        if depth:
            expressions.append((value[start:], ""))
            break
        body = value[open_parenthesis + 1 : index - 1]
        comma = None
        inner_depth = 0
        inner_quote = None
        for body_index, character in enumerate(body):
            if inner_quote is not None:
                if character == inner_quote and (
                    body_index == 0 or body[body_index - 1] != "\\"
                ):
                    inner_quote = None
            elif character in {"'", '"'}:
                inner_quote = character
            elif character == "(":
                inner_depth += 1
            elif character == ")":
                inner_depth -= 1
            elif character == "," and inner_depth == 0:
                comma = body_index
                break
        if comma is None:
            expressions.append((body.strip(), ""))
        else:
            expressions.append((body[:comma].strip(), body[comma + 1 :].strip()))
        cursor = index
    return tuple(expressions)


def _validate_css_vars(
    value: str,
    path: str,
    declared_tokens: frozenset,
    issues: list,
) -> None:
    for token, fallback in _var_expressions(value):
        if _TOKEN_PATTERN.fullmatch(token) is None:
            _issue(issues, path, "CSS var reference has an invalid token name")
        elif token not in declared_tokens:
            _issue(
                issues,
                path,
                "CSS token {0} is not declared in tokens.css".format(token),
            )
        if not fallback:
            _issue(issues, path, "every CSS var reference requires a literal fallback")
        elif re.search(r"\b(?:var|env|attr|url)\s*\(", fallback, re.IGNORECASE):
            _issue(issues, path, "CSS var fallback must be literal")


def _reference_value(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1].strip()
    return stripped


def _inspect_reference(
    reference: str,
    path: str,
    issues: list,
    fragments: list,
    kind: str,
) -> None:
    lowered = reference.lower()
    if lowered.startswith("data:"):
        _issue(issues, path, "embedded data URI is forbidden")
    elif lowered.startswith("javascript:"):
        _issue(issues, path, "JavaScript URI is forbidden")
    elif reference.startswith("#") and len(reference) > 1:
        fragments.append((path, reference[1:]))
    elif kind == "href":
        _issue(issues, path, "external reference is forbidden")
    else:
        _issue(issues, path, "external URL is forbidden")


def _inspect_urls(value: str, path: str, issues: list, fragments: list) -> None:
    for match in _URL_PATTERN.finditer(value):
        _inspect_reference(
            _reference_value(match.group(1)),
            path,
            issues,
            fragments,
            "url",
        )


def _parse_svg(
    source: str,
    svg_path: Path,
) -> ElementTree.Element:
    if re.search(r"<\?xml-stylesheet\b", source, re.IGNORECASE):
        raise AssetValidationError(
            (
                AssetValidationIssue(
                    str(svg_path) + ":/document",
                    "stylesheet processing instructions are forbidden",
                ),
            )
        )
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", source, re.IGNORECASE):
        raise AssetValidationError(
            (
                AssetValidationIssue(
                    str(svg_path) + ":/document",
                    "DOCTYPE and entity declarations are forbidden",
                ),
            )
        )
    try:
        return ElementTree.fromstring(source)
    except ElementTree.ParseError as error:
        raise AssetValidationError(
            (
                AssetValidationIssue(
                    str(svg_path),
                    "invalid XML: {0}".format(error),
                ),
            )
        ) from error


def _validate_svg(
    icon_id: str,
    manifest: IconManifest,
    source: str,
    source_bytes: bytes,
    svg_path: Path,
    declared_tokens: frozenset,
) -> Tuple[ElementTree.Element, Tuple[str, ...], AssetMetrics, Tuple[AssetValidationIssue, ...]]:
    root = _parse_svg(source, svg_path)
    issues = []
    paths = _element_paths(root)
    root_namespace, root_name = _qualified_name(root.tag)
    root_path = str(svg_path) + ":/" + root_name
    if root_name != "svg" or root_namespace != _SVG_NAMESPACE:
        _issue(issues, root_path, "root must be svg in the canonical SVG namespace")
    for attribute, expected in (("role", "img"), ("focusable", "false")):
        if root.get(attribute) != expected:
            _issue(
                issues,
                root_path + "/@" + attribute,
                "expected {0}".format(expected),
            )
    aria_label = root.get("aria-label")
    if not isinstance(aria_label, str) or not aria_label.strip():
        _issue(issues, root_path + "/@aria-label", "expected a nonempty label")
    if root.get("data-icon") != icon_id:
        _issue(
            issues,
            root_path + "/@data-icon",
            "must match SVG filename {0}.svg".format(icon_id),
        )
    if root.get("viewBox") != manifest.view_box:
        _issue(
            issues,
            root_path + "/@viewBox",
            "must match manifest viewBox {0}".format(manifest.view_box),
        )

    public_parts = []
    part_locations = {}
    authored_ids = set()
    fragments = []
    non_scaling_locations = []
    variable_vector_effect_locations = []
    forbidden_count = 0
    paintable_count = 0
    all_elements = tuple(root.iter())
    for element in all_elements:
        element_namespace, tag = _qualified_name(element.tag)
        path = str(svg_path) + ":" + paths[element]
        if element_namespace != _SVG_NAMESPACE:
            _issue(issues, path, "foreign XML namespace is forbidden")
        if element_namespace == _SVG_NAMESPACE and tag in _PAINTABLE_TAGS:
            paintable_count += 1
        if tag in _FORBIDDEN_TAGS:
            forbidden_count += 1
            _issue(issues, path, "forbidden element <{0}>".format(tag))

        for raw_name, value in element.attrib.items():
            namespace, name = _qualified_name(raw_name)
            attribute_path = path + "/@" + name
            css_value = _CSS_COMMENT_PATTERN.sub("", value)
            if "\\" in value:
                _issue(
                    issues,
                    attribute_path,
                    "backslash escapes are forbidden in canonical SVG attributes",
                )
            if namespace not in {"", _XLINK_NAMESPACE, _XML_NAMESPACE}:
                _issue(issues, attribute_path, "foreign XML attribute namespace is forbidden")
            if name == "id":
                authored_ids.add(value)
                _issue(issues, attribute_path, "authored id attributes are forbidden")
            if name == "data-part" and namespace == "":
                if not value:
                    _issue(issues, attribute_path, "data-part must not be empty")
                elif value in part_locations:
                    _issue(
                        issues,
                        attribute_path,
                        "duplicate public data-part; first declared at {0}".format(
                            part_locations[value]
                        ),
                    )
                else:
                    part_locations[value] = attribute_path
                    public_parts.append(value)
            lowered_name = name.lower()
            if namespace == "" and lowered_name.startswith("on"):
                _issue(issues, attribute_path, "JavaScript event handler is forbidden")
            if name in _ANIMATION_ATTRIBUTES:
                _issue(issues, attribute_path, "animation attributes are forbidden")
            if lowered_name == "filter":
                _issue(issues, attribute_path, "filter effects are forbidden")
            if lowered_name == "href":
                _inspect_reference(
                    value.strip(),
                    attribute_path,
                    issues,
                    fragments,
                    "href",
                )
            elif "javascript:" in value.lower():
                _issue(issues, attribute_path, "JavaScript URI is forbidden")
            _inspect_urls(value, attribute_path, issues, fragments)
            _validate_css_vars(value, attribute_path, declared_tokens, issues)

            if lowered_name == "style" and re.search(
                r"(?:^|;)\s*(?:animation|transition)(?:-[a-z-]+)?\s*:",
                css_value,
                re.IGNORECASE,
            ):
                _issue(issues, attribute_path, "CSS animation declarations are forbidden")
            if lowered_name == "style" and re.search(
                r"(?:^|;)\s*filter\s*:",
                css_value,
                re.IGNORECASE,
            ):
                _issue(issues, attribute_path, "filter effects are forbidden")
            if (
                lowered_name == "vector-effect"
                and value.strip().lower() == "non-scaling-stroke"
            ):
                non_scaling_locations.append(attribute_path)
            if lowered_name == "vector-effect" and re.search(
                r"\bvar\s*\(", css_value, re.IGNORECASE
            ):
                variable_vector_effect_locations.append(attribute_path)
            if lowered_name == "style" and re.search(
                r"(?:^|;)\s*vector-effect\s*:\s*non-scaling-stroke\b",
                css_value,
                re.IGNORECASE,
            ):
                non_scaling_locations.append(attribute_path)
            if lowered_name == "style" and re.search(
                r"(?:^|;)\s*vector-effect\s*:\s*var\s*\(",
                css_value,
                re.IGNORECASE,
            ):
                variable_vector_effect_locations.append(attribute_path)

        if element.text:
            text_path = path + "/#text"
            css_text = _CSS_COMMENT_PATTERN.sub("", element.text)
            if tag == "style" and "\\" in element.text:
                _issue(
                    issues,
                    text_path,
                    "backslash escapes are forbidden in canonical SVG CSS",
                )
            _inspect_urls(element.text, text_path, issues, fragments)
            _validate_css_vars(element.text, text_path, declared_tokens, issues)
            if tag == "style" and re.search(
                r"@import\b", css_text, re.IGNORECASE
            ):
                _issue(issues, text_path, "CSS @import is forbidden")
            if tag == "style" and re.search(
                r"(?:^|[;{])\s*(?:animation|transition)(?:-[a-z-]+)?\s*:",
                css_text,
                re.IGNORECASE,
            ):
                _issue(issues, text_path, "CSS animation declarations are forbidden")
            if tag == "style" and re.search(
                r"(?:^|[;{])\s*filter\s*:", css_text, re.IGNORECASE
            ):
                _issue(issues, text_path, "filter effects are forbidden")
            if tag == "style" and re.search(
                r"(?:^|[;{])\s*vector-effect\s*:\s*non-scaling-stroke\b",
                css_text,
                re.IGNORECASE,
            ):
                non_scaling_locations.append(text_path)
            if tag == "style" and re.search(
                r"(?:^|[;{])\s*vector-effect\s*:\s*var\s*\(",
                css_text,
                re.IGNORECASE,
            ):
                variable_vector_effect_locations.append(text_path)
            if "javascript:" in element.text.lower():
                _issue(issues, text_path, "JavaScript URI is forbidden")

    for reference_path, fragment in fragments:
        if fragment not in authored_ids:
            _issue(
                issues,
                reference_path,
                "unresolved fragment #{0}".format(fragment),
            )

    public_parts_tuple = tuple(public_parts)
    if public_parts_tuple != manifest.parts:
        _issue(
            issues,
            str(svg_path) + ":/svg/@data-part",
            "public parts do not match manifest order and values",
        )

    exception_metrics = manifest.exception_metrics
    if non_scaling_locations and "non-scaling-stroke" not in exception_metrics:
        for location in non_scaling_locations:
            _issue(
                issues,
                location,
                "non-scaling-stroke requires an approved manifest exception",
            )
    if (
        variable_vector_effect_locations
        and "non-scaling-stroke" not in exception_metrics
    ):
        for location in variable_vector_effect_locations:
            _issue(
                issues,
                location,
                "variable vector-effect requires an approved "
                "non-scaling-stroke manifest exception",
            )

    raw_size = len(source_bytes)
    gzip_size = len(gzip.compress(source_bytes, compresslevel=9, mtime=0))
    if raw_size > _RAW_SIZE_LIMIT and "raw-size" not in exception_metrics:
        _issue(
            issues,
            str(svg_path),
            "raw-size budget exceeded: {0} > {1} bytes".format(
                raw_size,
                _RAW_SIZE_LIMIT,
            ),
        )
    if gzip_size > _GZIP_SIZE_LIMIT and "gzip-size" not in exception_metrics:
        _issue(
            issues,
            str(svg_path),
            "gzip-size budget exceeded: {0} > {1} bytes".format(
                gzip_size,
                _GZIP_SIZE_LIMIT,
            ),
        )
    if (
        paintable_count > _PAINTABLE_LIMIT
        and "paintable-elements" not in exception_metrics
    ):
        _issue(
            issues,
            str(svg_path) + ":/svg",
            "paintable-elements budget exceeded: {0} > {1}".format(
                paintable_count,
                _PAINTABLE_LIMIT,
            ),
        )

    metrics = AssetMetrics(
        forbidden_elements=forbidden_count,
        paintable_elements=paintable_count,
        total_dom_elements=len(all_elements),
        raw_size_bytes=raw_size,
        gzip_size_bytes=gzip_size,
    )
    return root, public_parts_tuple, metrics, tuple(issues)


def _read_tokens(root: Path) -> Tuple[Path, str]:
    path = root / "tokens.css"
    try:
        return path, path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise AssetValidationError(
            (AssetValidationIssue(str(path), "cannot read tokens.css: {0}".format(error)),)
        ) from error


def _manifest_error(error: ManifestValidationError, default_path: Path) -> AssetValidationError:
    source_path = default_path if error.source_path is None else error.source_path
    return AssetValidationError(
        AssetValidationIssue(
            "{0}:{1}".format(source_path, issue.path),
            issue.message,
        )
        for issue in error.issues
    )


def load_asset(
    icon_id: str,
    allow_statuses: Iterable[str],
    asset_root: Optional[Path] = None,
) -> LoadedAsset:
    """Validate catalog, manifest, token, SVG, status, and parity as one gate."""

    _safe_icon_id(icon_id)
    if isinstance(allow_statuses, str):
        raise AssetValidationError(
            (
                AssetValidationIssue(
                    "$allow_statuses",
                    "expected an iterable of catalog statuses, not a string",
                ),
            )
        )
    try:
        allowed = frozenset(allow_statuses)
    except TypeError as error:
        raise AssetValidationError(
            (AssetValidationIssue("$allow_statuses", "expected an iterable"),)
        ) from error
    invalid_statuses = allowed - CATALOG_STATUSES
    if invalid_statuses:
        raise AssetValidationError(
            (
                AssetValidationIssue(
                    "$allow_statuses",
                    "unknown statuses: " + ", ".join(sorted(invalid_statuses)),
                ),
            )
        )

    root = _asset_root(asset_root)
    catalog_path = root / "catalog.json"
    manifest_path = root / "manifests" / (icon_id + ".json")
    try:
        catalog = load_catalog(root)
    except CatalogValidationError as error:
        raise AssetValidationError(
            (AssetValidationIssue(str(catalog_path), str(error)),)
        ) from error
    entry = catalog_entry(icon_id, catalog)
    if entry is None:
        raise AssetValidationError(
            (
                AssetValidationIssue(
                    str(catalog_path) + ":$.icons",
                    "icon {0} is not cataloged".format(icon_id),
                ),
            )
        )
    try:
        manifest = load_manifest(icon_id, root)
    except ManifestValidationError as error:
        raise _manifest_error(error, manifest_path) from error

    svg_path, source_bytes = _read_svg_bytes(icon_id, root)
    try:
        svg_source = source_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AssetValidationError(
            (AssetValidationIssue(str(svg_path), "SVG must be valid UTF-8"),)
        ) from error
    _, tokens_source = _read_tokens(root)

    issues = []
    parity = (
        ("id", "id", entry.icon_id, manifest.icon_id),
        ("category", "category", entry.category, manifest.category),
        (
            "semantic_kind",
            "semantic_kind",
            entry.semantic_kind,
            manifest.semantic_kind,
        ),
        (
            "structural_prototype",
            "structural_prototype",
            entry.structural_prototype,
            manifest.structural_prototype,
        ),
        ("parts", "parts", entry.parts, manifest.parts),
        ("supported_states", "states", entry.supported_states, manifest.states),
        ("supported_actions", "actions", entry.supported_actions, manifest.actions),
        ("status", "status", entry.status, manifest.status),
        (
            "asset_revision",
            "asset_revision",
            entry.asset_revision,
            manifest.asset_revision,
        ),
    )
    entry_index = catalog.entries.index(entry)
    for catalog_field, manifest_field, catalog_value, manifest_value in parity:
        if catalog_value != manifest_value:
            _issue(
                issues,
                str(manifest_path) + ":$." + manifest_field,
                "must exactly match {0}:$.icons[{1}].{2}".format(
                    catalog_path,
                    entry_index,
                    catalog_field,
                ),
            )
    if manifest.status not in allowed:
        _issue(
            issues,
            str(manifest_path) + ":$.status",
            "status {0} is not in allow_statuses".format(manifest.status),
        )

    parsed_root, public_parts, metrics, svg_issues = _validate_svg(
        icon_id=icon_id,
        manifest=manifest,
        source=svg_source,
        source_bytes=source_bytes,
        svg_path=svg_path,
        declared_tokens=_declared_tokens(tokens_source),
    )
    issues.extend(svg_issues)
    if issues:
        raise AssetValidationError(issues)
    return LoadedAsset(
        manifest=manifest,
        svg_source=svg_source,
        root=parsed_root,
        public_parts=public_parts,
        metrics=metrics,
    )


__all__ = [
    "AssetMetrics",
    "AssetValidationError",
    "AssetValidationIssue",
    "LoadedAsset",
    "load_asset",
    "load_svg_source",
]
