"""Resolve canonical resources in a checkout or an installed wheel."""

from __future__ import annotations

from pathlib import Path


_PACKAGE_ROOT = Path(__file__).resolve().parent
_CHECKOUT_ROOT = _PACKAGE_ROOT.parents[1]
_PACKAGED_ROOT = _PACKAGE_ROOT / "_resources"


def resource_root(name: str) -> Path:
    """Return a resource directory without assuming a repository checkout."""

    checkout = _CHECKOUT_ROOT / name
    if checkout.is_dir():
        return checkout
    packaged = _PACKAGED_ROOT / name
    if packaged.is_dir():
        return packaged
    raise FileNotFoundError(
        f"AniDiagram resource directory {name!r} is unavailable; "
        "reinstall the package from a complete wheel"
    )


def resource_path(name: str, *parts: str) -> Path:
    return resource_root(name).joinpath(*parts)
