"""Main parsing pipeline for addrforge."""

import re
from dataclasses import replace
from typing import Optional, Tuple

from .data import CANADIAN_PROVINCES, NON_US_COUNTRY_TERMS, STATE_ABBREVIATIONS
from .format import format_standardized
from .models import ParsedAddress
from .normalize import (
    collapse_spaces,
    normalize_city,
    normalize_directional,
    normalize_suffix,
    normalize_text,
    normalize_unit_type,
    normalize_zip,
    preprocess,
)
from .patterns import (
    CITY_STATE_ZIP_RE,
    MAILBOX_ROUTE_RE,
    PO_BOX_RE,
    ROUTE_RE,
    STATE_ZIP_RE,
    STREET_RE,
    UNIT_FIRST_RE,
    UNIT_RE,
)

_CANADIAN_POSTAL_RE = re.compile(
    r"\b[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z]\s?\d[ABCEGHJ-NPRSTV-Z]\d\b",
    re.IGNORECASE,
)


def parse(text: str, *, strict: bool = False) -> ParsedAddress:
    """Parse a US address string into structured components.

    The parser is intentionally forgiving: it returns a partial result with
    ``kind="unknown"`` when the input does not resemble a supported address.
    It does not validate existence or deliverability. Set ``strict=True`` to
    reject partial parses that are not complete enough for mailing workflows.
    """

    raw = text
    cleaned = preprocess(text or "")
    if not cleaned:
        return _finalize(ParsedAddress(raw=raw, standardized=""), strict=strict)

    non_us_reason = _detect_obvious_non_us(cleaned)
    if non_us_reason:
        return _finalize(
            ParsedAddress(
                raw=raw,
                kind="unknown",
                is_us=False,
                reject_reason=non_us_reason,
                warnings=("non_us_address",),
                parse_notes=("non_us_address",),
            ),
            strict=strict,
        )

    body, city, state, zip_code = _split_place_tail(cleaned)
    body, unit_type, unit_id = _split_trailing_unit(body)
    if unit_type is None:
        body, unit_type, unit_id = _split_leading_unit(body)

    parsed = _parse_po_box(raw, body) or _parse_mailbox_route(raw, body) or _parse_route(raw, body) or _parse_street(raw, body)
    if parsed is None:
        parsed = ParsedAddress(raw=raw, kind="unknown")

    parsed = replace(
        parsed,
        unit_type=unit_type,
        unit_id=unit_id,
        city=city,
        state=state,
        zip_code=zip_code,
    )
    return _finalize(parsed, strict=strict)


def standardize(text: str, *, strict: bool = False) -> str:
    """Return a USPS-like uppercase normalized address string."""

    return parse(text, strict=strict).standardized


def explain(text: str, *, strict: bool = False) -> Tuple[str, ...]:
    """Return parse notes explaining partial or ambiguous results."""

    return parse(text, strict=strict).parse_notes


def is_probably_address(text: str) -> bool:
    """Return True when *text* resembles a supported US address form."""

    parsed = parse(text)
    if parsed.kind != "unknown" and parsed.is_us:
        return True
    return bool(parsed.state and (parsed.city or parsed.zip_code))


def _split_place_tail(text: str) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
    for pattern in (CITY_STATE_ZIP_RE, STATE_ZIP_RE):
        match = pattern.match(text)
        if not match:
            continue
        state = normalize_text(match.group("state"))
        body = (match.group("body") or "").strip(" ,")
        if state not in STATE_ABBREVIATIONS or not body:
            continue
        city = normalize_city(match.groupdict().get("city"))
        zip_code = normalize_zip(match.groupdict().get("zip"))
        return body, city, state, zip_code
    return text, None, None, None


def _split_trailing_unit(text: str) -> Tuple[str, Optional[str], Optional[str]]:
    match = UNIT_RE.match(text)
    if not match:
        return text, None, None

    prefix = collapse_spaces((match.group("prefix") or "").strip(" ,"))
    if not prefix:
        return text, None, None

    unit_type = normalize_unit_type(match.group("unit_type")) or "UNIT"
    unit_id = normalize_text(match.group("unit_id"))
    return prefix, unit_type, unit_id


def _split_leading_unit(text: str) -> Tuple[str, Optional[str], Optional[str]]:
    match = UNIT_FIRST_RE.match(text)
    if not match:
        return text, None, None

    body = collapse_spaces((match.group("body") or "").strip(" ,"))
    if not body:
        return text, None, None
    if (normalize_text(body) or "").startswith("BOX "):
        return text, None, None

    unit_type = normalize_unit_type(match.group("unit_type")) or "UNIT"
    unit_id = normalize_text(match.group("unit_id"))
    return body, unit_type, unit_id


def _parse_po_box(raw: str, body: str) -> Optional[ParsedAddress]:
    match = PO_BOX_RE.match(body)
    if not match:
        return None
    phrase = normalize_text(match.group("po_box"))
    po_box = phrase
    for prefix in ("PO BOX ", "POST OFFICE BOX "):
        if phrase and phrase.startswith(prefix):
            po_box = phrase[len(prefix) :]
            break
    return ParsedAddress(raw=raw, kind="po_box", po_box=po_box)


def _parse_mailbox_route(raw: str, body: str) -> Optional[ParsedAddress]:
    match = MAILBOX_ROUTE_RE.match(body)
    if not match:
        return None
    po_box = _normalize_mailbox_phrase(match.group("po_box"))
    return ParsedAddress(raw=raw, kind="po_box", po_box=po_box)


def _parse_route(raw: str, body: str) -> Optional[ParsedAddress]:
    match = ROUTE_RE.match(body)
    if not match:
        return None
    return ParsedAddress(raw=raw, kind="route", route=_normalize_route(match.group("route")))


def _parse_street(raw: str, body: str) -> Optional[ParsedAddress]:
    match = STREET_RE.match(body)
    if not match:
        return None

    number = normalize_text(match.group("number"))
    predir = normalize_directional(match.group("predir"))
    street_name = normalize_text(match.group("street_name"))
    suffix = normalize_suffix(match.group("suffix"))
    postdir = normalize_directional(match.group("postdir"))

    if not street_name:
        return None
    if not (number or suffix or predir or postdir):
        return None
    if street_name in STATE_ABBREVIATIONS and not suffix:
        return None

    return ParsedAddress(
        raw=raw,
        kind="street",
        number=number,
        predir=predir,
        street_name=street_name,
        suffix=suffix,
        postdir=postdir,
    )


def _normalize_route(value: str) -> str:
    text = normalize_text(value) or ""
    text = text.replace("U S HIGHWAY", "US")
    text = text.replace("I ", "I-")
    text = text.replace("US-", "US ")
    text = text.replace("US ", "US ")
    return collapse_spaces(text)


def _normalize_mailbox_phrase(value: str) -> str:
    text = normalize_text(value) or ""
    text = text.replace("RURAL ROUTE", "RR")
    text = text.replace("HIGHWAY CONTRACT", "HC")
    return collapse_spaces(text)


def _finalize(address: ParsedAddress, *, strict: bool) -> ParsedAddress:
    enriched = _enrich(address)
    if strict and not enriched.is_complete_for_mailing:
        enriched = ParsedAddress(
            raw=address.raw,
            kind="unknown",
            is_us=address.is_us,
            reject_reason=address.reject_reason or "strict_incomplete_address",
            warnings=tuple(dict.fromkeys(enriched.warnings + ("strict_incomplete_address",))),
            parse_notes=tuple(dict.fromkeys(enriched.parse_notes + ("strict_incomplete_address",))),
        )
        enriched = _enrich(enriched)
    return replace(enriched, standardized=format_standardized(enriched))


def _enrich(address: ParsedAddress) -> ParsedAddress:
    missing = _components_missing(address)
    complete = address.kind != "unknown" and address.is_us and not missing
    score = _score(address)
    notes = _notes(address)
    warnings = _warnings(address, missing, complete, score)
    match_level = _match_level(address, complete, score)
    return replace(
        address,
        confidence=score,
        match_level=match_level,
        components_missing=missing,
        warnings=tuple(dict.fromkeys(address.warnings + warnings)),
        parse_notes=tuple(dict.fromkeys(address.parse_notes + notes)),
        is_complete_for_mailing=complete,
    )


def _score(address: ParsedAddress) -> float:
    if not address.is_us:
        return 0.0
    if address.kind == "unknown":
        return 0.2 if address.state else 0.0

    score = 0.55
    if address.kind == "po_box":
        score = 0.9 if address.po_box else 0.65
    elif address.kind == "route":
        score = 0.88 if address.route else 0.6
    elif address.kind == "street":
        score = 0.45
        if address.number:
            score += 0.2
        if address.street_name:
            score += 0.15
        if address.suffix:
            score += 0.15
        if address.predir or address.postdir:
            score += 0.05

    if address.unit_type and address.unit_id:
        score += 0.03
    if address.city and address.state:
        score += 0.04
    elif address.state:
        score += 0.02
    if address.zip_code:
        score += 0.03

    return round(min(score, 0.99), 2)


def _components_missing(address: ParsedAddress) -> Tuple[str, ...]:
    missing = []
    if not address.is_us:
        missing.append("us_address")
        return tuple(missing)
    if address.kind == "unknown":
        missing.append("primary_address")
        return tuple(missing)
    if address.kind == "street":
        if not address.number:
            missing.append("number")
        if not address.street_name:
            missing.append("street_name")
        if not address.suffix:
            missing.append("suffix")
    elif address.kind == "route" and not address.route:
        missing.append("route")
    elif address.kind == "po_box" and not address.po_box:
        missing.append("po_box")

    if not address.city:
        missing.append("city")
    if not address.state:
        missing.append("state")
    if not address.zip_code:
        missing.append("zip_code")
    return tuple(missing)


def _match_level(address: ParsedAddress, complete: bool, score: float) -> str:
    if address.kind == "unknown" or not address.is_us:
        return "unknown"
    if complete and score >= 0.9:
        return "exact-ish"
    if score >= 0.75:
        return "partial"
    return "weak"


def _warnings(address: ParsedAddress, missing: Tuple[str, ...], complete: bool, score: float) -> Tuple[str, ...]:
    warnings = []
    if not address.is_us:
        warnings.append("non_us_address")
    if address.kind == "unknown":
        warnings.append("unparsed_address")
    if missing and address.kind != "unknown" and not complete:
        warnings.append("not_complete_for_mailing")
    if address.kind != "unknown" and score < 0.8:
        warnings.append("low_confidence_parse")
    return tuple(warnings)


def _notes(address: ParsedAddress) -> Tuple[str, ...]:
    notes = []
    if not address.is_us:
        notes.append("non_us_address")
    if address.kind == "unknown":
        notes.append("no_supported_address_pattern")
    if address.kind == "street" and not address.number:
        notes.append("missing_house_number")
    if address.kind == "street" and not address.suffix:
        notes.append("missing_street_suffix")
    if address.kind != "unknown" and not (address.city or address.state or address.zip_code):
        notes.append("missing_place_tail")
    if address.state and not address.city:
        notes.append("state_without_city")
    return tuple(notes)


def _detect_obvious_non_us(text: str) -> Optional[str]:
    normalized = normalize_text(text) or ""
    for term in sorted(NON_US_COUNTRY_TERMS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(term)}\b", normalized):
            return "non_us_country"

    if _CANADIAN_POSTAL_RE.search(normalized):
        tokens = set(normalized.replace(",", " ").split())
        if tokens.intersection(CANADIAN_PROVINCES):
            return "canadian_postal_code"

    return None
