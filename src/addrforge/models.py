"""Data models used by addrforge."""

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class ParsedAddress:
    """Structured result returned by :func:`addrforge.parse`."""

    raw: str
    kind: str = "unknown"
    number: Optional[str] = None
    predir: Optional[str] = None
    street_name: Optional[str] = None
    suffix: Optional[str] = None
    postdir: Optional[str] = None
    unit_type: Optional[str] = None
    unit_id: Optional[str] = None
    route: Optional[str] = None
    po_box: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    confidence: float = 0.0
    match_level: str = "unknown"
    components_missing: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
    parse_notes: Tuple[str, ...] = ()
    is_complete_for_mailing: bool = False
    is_us: bool = True
    reject_reason: Optional[str] = None
    standardized: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dictionary."""

        return asdict(self)

    def to_json(self, *, indent: Optional[int] = None) -> str:
        """Return a JSON string representation."""

        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


@dataclass(frozen=True)
class AddressLines:
    """US mailing-style line split derived from a parsed address."""

    raw: str
    line1: str = ""
    line2: str = ""
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    standardized: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dictionary."""

        return asdict(self)

    def to_json(self, *, indent: Optional[int] = None) -> str:
        """Return a JSON string representation."""

        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


@dataclass(frozen=True)
class ValidationResult:
    """Result from an optional external address lookup provider."""

    raw: str
    provider: str
    parsed: ParsedAddress
    is_valid: bool = False
    is_deliverable: Optional[bool] = None
    match_level: str = "unknown"
    confidence: float = 0.0
    matched_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    warnings: Tuple[str, ...] = ()
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dictionary."""

        return asdict(self)

    def to_json(self, *, indent: Optional[int] = None) -> str:
        """Return a JSON string representation."""

        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)
