"""Component-level normalization helpers."""

import re
from typing import Optional

from .data import DIRECTIONALS, STREET_SUFFIXES, UNIT_TYPES

_SPACE_RE = re.compile(r"\s+")
_PUNCT_TO_SPACE_RE = re.compile(r"[;|]+")
_DOT_RE = re.compile(r"\.")


def collapse_spaces(text: str) -> str:
    """Return *text* with repeated whitespace collapsed."""

    return _SPACE_RE.sub(" ", text).strip()


def preprocess(text: str) -> str:
    """Normalize punctuation and spacing while preserving useful hyphens."""

    cleaned = _DOT_RE.sub("", text.strip())
    cleaned = _PUNCT_TO_SPACE_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\s*,\s*", ", ", cleaned)
    cleaned = re.sub(r"\s*#\s*", " #", cleaned)
    return collapse_spaces(cleaned.strip(" ,"))


def token_key(value: Optional[str]) -> Optional[str]:
    """Normalize a token for dictionary lookup."""

    if value is None:
        return None
    key = value.strip().upper().replace(".", "")
    return collapse_spaces(key)


def normalize_directional(value: Optional[str]) -> Optional[str]:
    """Normalize a directional token to USPS-style abbreviation."""

    key = token_key(value)
    return DIRECTIONALS.get(key or "")


def normalize_unit_type(value: Optional[str]) -> Optional[str]:
    """Normalize a unit designator."""

    key = token_key(value)
    return UNIT_TYPES.get(key or "")


def normalize_suffix(value: Optional[str]) -> Optional[str]:
    """Normalize a street suffix to a USPS-like abbreviation."""

    key = token_key(value)
    return STREET_SUFFIXES.get(key or "")


def normalize_text(value: Optional[str]) -> Optional[str]:
    """Uppercase and collapse whitespace for free-text components."""

    if value is None:
        return None
    normalized = collapse_spaces(value.strip(" ,").upper())
    return normalized or None


def normalize_city(value: Optional[str]) -> Optional[str]:
    """Normalize a city name without attempting validation."""

    return normalize_text(value)


def normalize_zip(value: Optional[str]) -> Optional[str]:
    """Normalize ZIP or ZIP+4 text."""

    return normalize_text(value)
