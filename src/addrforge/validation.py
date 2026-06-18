"""Optional external lookup providers for address geocodability checks."""

import json
from typing import Any, Callable, Dict, Optional, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen as default_urlopen

from .models import ParsedAddress, ValidationResult
from .parser import parse

Urlopen = Callable[..., Any]


class ValidationProvider(Protocol):
    """Protocol implemented by optional validation providers."""

    name: str

    def validate(self, text: str, *, timeout: float = 5.0) -> ValidationResult:
        """Validate or geocode an address string."""


class CensusGeocoderProvider:
    """US Census Geocoder provider.

    This checks whether an address can be matched to Census MAF/TIGER address
    ranges. It is not USPS delivery validation and does not prove mailability.
    """

    name = "census"

    def __init__(
        self,
        *,
        benchmark: str = "Public_AR_Current",
        base_url: str = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress",
        urlopen: Optional[Urlopen] = None,
    ) -> None:
        self.benchmark = benchmark
        self.base_url = base_url
        self._urlopen = urlopen or default_urlopen

    def validate(self, text: str, *, timeout: float = 5.0) -> ValidationResult:
        parsed = parse(text)
        if not parsed.is_us:
            return _skipped_result(text, self.name, parsed, "non_us_address")

        params = urlencode({"address": text, "benchmark": self.benchmark, "format": "json"})
        url = f"{self.base_url}?{params}"
        try:
            payload = _load_json(url, self._urlopen, timeout=timeout)
        except Exception as exc:  # pragma: no cover - exact urllib failures vary
            return _error_result(text, self.name, parsed, exc)

        matches = (((payload or {}).get("result") or {}).get("addressMatches") or [])
        if not matches:
            return ValidationResult(
                raw=text,
                provider=self.name,
                parsed=parsed,
                is_valid=False,
                is_deliverable=None,
                match_level="unknown",
                confidence=0.2,
                warnings=("no_census_match", "not_delivery_validation"),
                metadata={"query_url": url},
            )

        match = matches[0]
        coords = match.get("coordinates") or {}
        matched_address = match.get("matchedAddress")
        return ValidationResult(
            raw=text,
            provider=self.name,
            parsed=parsed,
            is_valid=True,
            is_deliverable=None,
            match_level="exact-ish",
            confidence=0.9,
            matched_address=matched_address,
            latitude=_float_or_none(coords.get("y")),
            longitude=_float_or_none(coords.get("x")),
            warnings=("not_delivery_validation",),
            metadata={
                "benchmark": self.benchmark,
                "address_components": match.get("addressComponents") or {},
                "tiger_line": match.get("tigerLine") or {},
            },
        )


class NominatimProvider:
    """OpenStreetMap Nominatim provider.

    Public Nominatim usage requires a real identifying User-Agent or Referer,
    clear attribution, caching where appropriate, and low request volume.
    """

    name = "nominatim"

    def __init__(
        self,
        *,
        user_agent: str = "addrforge/0.1",
        base_url: str = "https://nominatim.openstreetmap.org/search",
        urlopen: Optional[Urlopen] = None,
    ) -> None:
        self.user_agent = user_agent
        self.base_url = base_url
        self._urlopen = urlopen or default_urlopen

    def validate(self, text: str, *, timeout: float = 5.0) -> ValidationResult:
        parsed = parse(text)
        if not parsed.is_us:
            return _skipped_result(text, self.name, parsed, "non_us_address")

        params = urlencode(
            {
                "q": text,
                "format": "jsonv2",
                "addressdetails": "1",
                "limit": "1",
                "countrycodes": "us",
            }
        )
        url = f"{self.base_url}?{params}"
        request = Request(url, headers={"User-Agent": self.user_agent})
        try:
            payload = _load_json(request, self._urlopen, timeout=timeout)
        except Exception as exc:  # pragma: no cover - exact urllib failures vary
            return _error_result(text, self.name, parsed, exc)

        results = payload if isinstance(payload, list) else []
        if not results:
            return ValidationResult(
                raw=text,
                provider=self.name,
                parsed=parsed,
                is_valid=False,
                is_deliverable=None,
                match_level="unknown",
                confidence=0.2,
                warnings=("no_nominatim_match", "not_delivery_validation"),
                metadata={"query_url": url},
            )

        result = results[0]
        address = result.get("address") or {}
        is_us = (address.get("country_code") or "").lower() == "us"
        has_street = bool(address.get("road") or address.get("pedestrian"))
        has_number = bool(address.get("house_number"))
        confidence = _nominatim_confidence(result, is_us=is_us, has_street=has_street, has_number=has_number)
        return ValidationResult(
            raw=text,
            provider=self.name,
            parsed=parsed,
            is_valid=is_us,
            is_deliverable=None,
            match_level="partial" if is_us else "unknown",
            confidence=confidence,
            matched_address=result.get("display_name"),
            latitude=_float_or_none(result.get("lat")),
            longitude=_float_or_none(result.get("lon")),
            warnings=("not_delivery_validation", "requires_osm_attribution"),
            metadata={
                "osm_type": result.get("osm_type"),
                "osm_id": result.get("osm_id"),
                "address": address,
                "has_house_number": has_number,
                "has_street": has_street,
            },
        )


def validate(text: str, provider: Any = "census", *, timeout: float = 5.0) -> ValidationResult:
    """Run an optional external geocodability check.

    ``provider`` may be ``"census"``, ``"nominatim"``, or an object with a
    ``validate(text, timeout=...)`` method. Results are not proof of USPS
    deliverability.
    """

    selected = get_provider(provider)
    return selected.validate(text, timeout=timeout)


def get_provider(provider: Any) -> ValidationProvider:
    """Return a provider instance for a provider name or provider object."""

    if isinstance(provider, str):
        key = provider.lower()
        if key == "census":
            return CensusGeocoderProvider()
        if key == "nominatim":
            return NominatimProvider()
        raise ValueError(f"unknown validation provider: {provider}")
    if hasattr(provider, "validate"):
        return provider
    raise TypeError("provider must be a provider name or validation provider object")


def _load_json(request: Any, opener: Urlopen, *, timeout: float) -> Any:
    response = opener(request, timeout=timeout)
    with response:
        data = response.read().decode("utf-8")
    return json.loads(data)


def _skipped_result(text: str, provider: str, parsed: ParsedAddress, reason: str) -> ValidationResult:
    return ValidationResult(
        raw=text,
        provider=provider,
        parsed=parsed,
        is_valid=False,
        is_deliverable=None,
        match_level="unknown",
        confidence=0.0,
        warnings=(reason,),
    )


def _error_result(text: str, provider: str, parsed: ParsedAddress, exc: Exception) -> ValidationResult:
    return ValidationResult(
        raw=text,
        provider=provider,
        parsed=parsed,
        is_valid=False,
        is_deliverable=None,
        match_level="unknown",
        confidence=0.0,
        warnings=("provider_error",),
        error=str(exc),
    )


def _nominatim_confidence(result: Dict[str, Any], *, is_us: bool, has_street: bool, has_number: bool) -> float:
    if not is_us:
        return 0.0
    confidence = 0.45
    if has_street:
        confidence += 0.2
    if has_number:
        confidence += 0.2
    try:
        confidence += min(float(result.get("importance") or 0), 0.1)
    except (TypeError, ValueError):
        pass
    return round(min(confidence, 0.9), 2)


def _float_or_none(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
