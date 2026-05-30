"""Formatting helpers for standardized address strings."""

from typing import List, Optional

from .models import ParsedAddress
from .normalize import collapse_spaces


def _append(parts: List[str], value: Optional[str]) -> None:
    if value:
        parts.append(value)


def format_standardized(address: ParsedAddress) -> str:
    """Build an uppercase USPS-like address string from parsed components."""

    parts: List[str] = []

    if address.kind == "po_box":
        if address.po_box and _is_complete_mailbox_phrase(address.po_box):
            _append(parts, address.po_box)
        else:
            _append(parts, "PO BOX")
            _append(parts, address.po_box)
    elif address.kind == "route":
        _append(parts, address.route)
    elif address.kind == "street":
        _append(parts, address.number)
        _append(parts, address.predir)
        _append(parts, address.street_name)
        _append(parts, address.suffix)
        _append(parts, address.postdir)

    _append(parts, address.unit_type)
    _append(parts, address.unit_id)
    _append(parts, address.city)
    _append(parts, address.state)
    _append(parts, address.zip_code)

    return collapse_spaces(" ".join(parts).upper())


def primary_line(address: ParsedAddress) -> str:
    """Return only the primary delivery line."""

    return format_standardized(
        ParsedAddress(
            raw=address.raw,
            kind=address.kind,
            number=address.number,
            predir=address.predir,
            street_name=address.street_name,
            suffix=address.suffix,
            postdir=address.postdir,
            route=address.route,
            po_box=address.po_box,
        )
    )


def unit_line(address: ParsedAddress) -> str:
    """Return only the secondary unit line."""

    parts: List[str] = []
    _append(parts, address.unit_type)
    _append(parts, address.unit_id)
    return collapse_spaces(" ".join(parts).upper())


def _is_complete_mailbox_phrase(value: str) -> bool:
    return value.startswith(("RR ", "HC ", "PSC ", "CMR ", "UNIT "))
