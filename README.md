# addrforge

`addrforge` is a lightweight, dependency-free Python package for parsing and standardizing messy US address strings. It returns structured components, USPS-like uppercase normalized strings, mailing-style address lines, and optional geocodability checks through free public providers.

The local parser is offline and dependency-free. Optional validation providers may call external public APIs, but they still do not prove USPS deliverability.

## Install

```bash
pip install addrforge
```

For editable local development:

```bash
pip install -e .
```

## Quickstart

```python
from addrforge import explain, parse, split_lines, standardize, validate

parsed = parse("123 north main street apartment 4b")
print(parsed.kind)          # street
print(parsed.number)        # 123
print(parsed.predir)        # N
print(parsed.suffix)        # ST
print(parsed.unit_type)     # APT
print(parsed.standardized)  # 123 N MAIN ST APT 4B
print(parsed.confidence)    # 0.99
print(parsed.parse_notes)   # ('missing_place_tail',)
print(parsed.match_level)   # partial

print(standardize("PO Box 41, Springfield, OR 97477"))
# PO BOX 41 Springfield OR 97477

print(explain("Main Street"))
# ('missing_house_number', 'missing_place_tail')

lines = split_lines("742 Evergreen Terrace, Springfield OR 97477")
print(lines.line1)          # 742 Evergreen TR

result = validate("1600 Pennsylvania Ave NW, Washington DC 20500", provider="census")
print(result.is_valid)      # True when Census returns an address-range match
print(result.is_deliverable)  # None; this is not USPS delivery validation
```

For strict parsing:

```python
parse("Main Street", strict=True).kind
# unknown
```

For JSON:

```python
print(parse("123 Main St").to_json(indent=2))
```

From the command line:

```bash
addrforge "123 north main street apartment 4b"
addrforge --json "123 Main St, Springfield OR 97477"
addrforge --lines "123 Main St Apt 4B, Springfield OR 97477"
```

## Supported Patterns

- Standard street addresses such as `123 Main Street`, `123 N Main St`, `12-14 W Elm Rd`, and `1600 Pennsylvania Avenue NW`
- Named streets without a house number such as `42nd Street`
- Unit and subaddress designators including `Apt`, `Apartment`, `Suite`, `Ste`, `Unit`, `Room`, `Floor`, `Bldg`, `Lot`, `No. 4`, `#200`, and unit-before-street forms such as `Suite 200 123 Main Street`
- Highway and route forms including `I-95`, `US 29`, `State Route 7`, `County Road 12`, `Farm to Market Road 1960`, and `Route 66`
- PO Box forms including `PO Box 45`, `P.O. Box 45`, and `Post Office Box 45`
- Rural, highway contract, and military mailbox forms such as `RR 2 Box 152`, `HC 67 Box 12`, `PSC 123 Box 456 APO AE 09012`, and `CMR 123 Box 456`
- Optional city, state, and ZIP tails such as `Springfield, OR 97477`, `Arlington VA 22201`, and `Washington, DC 20001-1234`
- Obvious non-US addresses are rejected cleanly with `is_us=False` and `reject_reason`

Parsed results include:

- `confidence`: heuristic score from `0.0` to `0.99`
- `match_level`: `exact-ish`, `partial`, `weak`, or `unknown`
- `components_missing`: component names still needed for mailing-style completeness
- `warnings`: machine-readable warning codes
- `parse_notes`: explanation codes for partial or ambiguous parses
- `is_complete_for_mailing`: whether the parsed components include a primary line, city, state, and ZIP

These are heuristics for caller triage, not proof that an address is real.

## Optional Validation Providers

`addrforge.validate()` supports two no-registration providers:

- `provider="census"` uses the US Census Geocoder. It can indicate whether an address is geocodable against Census address-range data.
- `provider="nominatim"` uses OpenStreetMap Nominatim. It can indicate whether OSM found a US place/address-like result.

Both providers use only the Python standard library. Both may be free to call without registration, but they are external services with their own usage policies. Nominatim requires a real identifying User-Agent and low request volume. Neither provider is a USPS/CASS/DPV deliverability validator.

## Non-Goals

- USPS/CASS/DPV deliverability checks
- Misspelling correction
- International address parsing
- Replacing specialized address parsers for every edge case

## Development

Run the test suite with:

```bash
PYTHONPATH=src python -m unittest discover
```

The library targets Python 3.9+ and uses only the Python standard library.
