"""Address line splitting helpers."""

from .format import primary_line, unit_line
from .models import AddressLines
from .parser import parse


def split_lines(text: str, *, strict: bool = False) -> AddressLines:
    """Split an address into mailing-style line fields.

    This is a formatter built on top of :func:`addrforge.parse`; it does not
    validate deliverability or infer missing components.
    """

    parsed = parse(text, strict=strict)
    line1 = primary_line(parsed)
    line2 = unit_line(parsed)
    return AddressLines(
        raw=text,
        line1=line1,
        line2=line2,
        city=parsed.city,
        state=parsed.state,
        zip_code=parsed.zip_code,
        standardized=parsed.standardized,
    )
