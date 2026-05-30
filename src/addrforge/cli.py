"""Command line interface for addrforge."""

import argparse
import sys
from typing import Optional, Sequence, TextIO

from .lines import split_lines
from .parser import parse
from .validation import validate


def main(argv: Optional[Sequence[str]] = None, *, stdout: Optional[TextIO] = None) -> int:
    """Run the addrforge command line interface."""

    parser = argparse.ArgumentParser(prog="addrforge", description="Parse and standardize US address strings.")
    parser.add_argument("address", nargs="*", help="address text; stdin is used when omitted")
    parser.add_argument("--json", action="store_true", help="print JSON instead of plain text")
    parser.add_argument("--lines", action="store_true", help="split into mailing-style address lines")
    parser.add_argument("--strict", action="store_true", help="reject incomplete partial parses")
    parser.add_argument(
        "--validate",
        choices=("census", "nominatim"),
        help="run an optional external geocodability check",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="validation request timeout in seconds")

    args = parser.parse_args(argv)
    out = stdout or sys.stdout
    text = " ".join(args.address).strip() if args.address else sys.stdin.read().strip()

    if args.validate:
        result = validate(text, provider=args.validate, timeout=args.timeout)
        print(result.to_json(indent=2) if args.json else _validation_summary(result), file=out)
        return 0 if result.error is None else 2

    if args.lines:
        lines = split_lines(text, strict=args.strict)
        print(lines.to_json(indent=2) if args.json else _line_summary(lines), file=out)
        return 0

    parsed = parse(text, strict=args.strict)
    print(parsed.to_json(indent=2) if args.json else parsed.standardized, file=out)
    return 0


def _line_summary(lines: object) -> str:
    parts = [
        getattr(lines, "line1", ""),
        getattr(lines, "line2", ""),
        " ".join(
            part
            for part in (
                getattr(lines, "city", None),
                getattr(lines, "state", None),
                getattr(lines, "zip_code", None),
            )
            if part
        ),
    ]
    return "\n".join(part for part in parts if part)


def _validation_summary(result: object) -> str:
    matched = getattr(result, "matched_address", None) or ""
    status = "matched" if getattr(result, "is_valid", False) else "not matched"
    provider = getattr(result, "provider", "provider")
    return f"{provider}: {status}" + (f"\n{matched}" if matched else "")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
