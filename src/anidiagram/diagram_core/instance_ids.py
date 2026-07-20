"""Collision-safe DOM identities for Diagram Core icon instances."""

from __future__ import annotations

import re
import unicodedata


_KEBAB_TOKEN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_NUMERIC_PREFIX = "_n"
_ESCAPE_PREFIX = "_u"


def _validated_instance_id(instance_id: str) -> str:
    if not isinstance(instance_id, str) or not instance_id:
        raise ValueError("instance_id must be a nonempty string")
    for character in instance_id:
        category = unicodedata.category(character)
        if category in {"Cc", "Cs"}:
            raise ValueError("instance_id must not contain controls or surrogates")
    return instance_id


def validated_kebab_token(value: str) -> str:
    """Return a strict kebab token or fail closed."""

    if not isinstance(value, str) or _KEBAB_TOKEN.fullmatch(value) is None:
        raise ValueError("expected a nonempty kebab-case token")
    return value


def instance_key(instance_id: str) -> str:
    """Encode an instance id as a reversible, separator-safe DOM key."""

    value = _validated_instance_id(instance_id)
    encoded = []
    for character in value:
        if character.isascii() and character.isalnum():
            encoded.append(character)
            continue
        hexadecimal = format(ord(character), "x")
        encoded.append(
            "{0}{1}x{2}".format(_ESCAPE_PREFIX, len(hexadecimal), hexadecimal)
        )
    key = "".join(encoded)
    if key[0].isdigit():
        key = _NUMERIC_PREFIX + key
    return key


def decode_instance_key(key: str) -> str:
    """Decode a canonical key produced by :func:`instance_key`."""

    if not isinstance(key, str) or not key or "__" in key:
        raise ValueError("expected a nonempty canonical instance key")
    encoded = key
    if encoded.startswith(_NUMERIC_PREFIX):
        encoded = encoded[len(_NUMERIC_PREFIX) :]
        if not encoded or not encoded[0].isdigit():
            raise ValueError("invalid numeric instance-key prefix")

    decoded = []
    index = 0
    while index < len(encoded):
        character = encoded[index]
        if character.isascii() and character.isalnum():
            decoded.append(character)
            index += 1
            continue
        if not encoded.startswith(_ESCAPE_PREFIX, index):
            raise ValueError("invalid instance-key escape")
        length_start = index + len(_ESCAPE_PREFIX)
        delimiter = encoded.find("x", length_start)
        if delimiter < 0:
            raise ValueError("unterminated instance-key escape")
        length_text = encoded[length_start:delimiter]
        if (
            not length_text
            or not length_text.isascii()
            or not length_text.isdigit()
            or length_text.startswith("0")
        ):
            raise ValueError("invalid instance-key escape length")
        hexadecimal_length = int(length_text)
        hexadecimal_start = delimiter + 1
        hexadecimal_end = hexadecimal_start + hexadecimal_length
        hexadecimal = encoded[hexadecimal_start:hexadecimal_end]
        if (
            len(hexadecimal) != hexadecimal_length
            or not hexadecimal
            or any(character not in "0123456789abcdef" for character in hexadecimal)
        ):
            raise ValueError("invalid instance-key code point")
        code_point = int(hexadecimal, 16)
        if code_point > 0x10FFFF:
            raise ValueError("instance-key code point is out of range")
        restored = chr(code_point)
        _validated_instance_id(restored)
        if restored.isascii() and restored.isalnum():
            raise ValueError("safe ASCII must not be escaped")
        decoded.append(restored)
        index = hexadecimal_end

    value = "".join(decoded)
    _validated_instance_id(value)
    if instance_key(value) != key:
        raise ValueError("instance key is not canonical")
    return value


def part_dom_id(instance_id: str, icon_id: str, part_name: str) -> str:
    """Build the exact instance-key/icon-id/part-name DOM identity."""

    return "__".join(
        (
            instance_key(instance_id),
            validated_kebab_token(icon_id),
            validated_kebab_token(part_name),
        )
    )


__all__ = [
    "decode_instance_key",
    "instance_key",
    "part_dom_id",
    "validated_kebab_token",
]
