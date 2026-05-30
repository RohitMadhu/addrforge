"""Compiled regular expressions for addrforge."""

import re

from .data import DIRECTIONALS, STREET_SUFFIXES, UNIT_TYPES

_DIRECTIONAL_PATTERN = "|".join(sorted((re.escape(k) for k in DIRECTIONALS), key=len, reverse=True))
_SUFFIX_PATTERN = "|".join(sorted((re.escape(k) for k in STREET_SUFFIXES), key=len, reverse=True))
_UNIT_PATTERN = "|".join(sorted((re.escape(k) for k in UNIT_TYPES), key=len, reverse=True))

CITY_STATE_ZIP_RE = re.compile(
    r"""
    ^(?P<body>.*?)
    (?:,\s*|\s+)
    (?P<city>[A-Za-z][A-Za-z .'-]*?)
    ,?\s+
    (?P<state>[A-Za-z]{2})
    (?:\s+(?P<zip>\d{5}(?:-\d{4})?))?
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

STATE_ZIP_RE = re.compile(
    r"""
    ^(?P<body>.*?)
    ,?\s+
    (?P<state>[A-Za-z]{2})
    (?:\s+(?P<zip>\d{5}(?:-\d{4})?))?
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

PO_BOX_RE = re.compile(
    r"""
    ^\s*
    (?P<po_box>
        (?:
            P\s*O\s+BOX
            | POST\s+OFFICE\s+BOX
        )
        \s+[A-Za-z0-9-]+
    )
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

MAILBOX_ROUTE_RE = re.compile(
    r"""
    ^\s*
    (?P<po_box>
        (?:
            RR|RURAL\s+ROUTE
        )
        \s+\d+[A-Za-z]?
        \s+BOX\s+[A-Za-z0-9-]+
        |
        (?:
            HC|HIGHWAY\s+CONTRACT
        )
        \s+\d+[A-Za-z]?
        \s+BOX\s+[A-Za-z0-9-]+
        |
        (?:
            PSC|CMR
        )
        \s+\d+[A-Za-z]?
        \s+BOX\s+[A-Za-z0-9-]+
        |
        UNIT\s+\d+[A-Za-z]?
        \s+BOX\s+[A-Za-z0-9-]+
    )
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

ROUTE_RE = re.compile(
    r"""
    ^\s*
    (?P<route>
        I[-\s]?\d+[A-Za-z]?
        | US[-\s]?\d+[A-Za-z]?
        | U\s*S\s+HIGHWAY\s+\d+[A-Za-z]?
        | STATE\s+(?:ROUTE|ROAD|HIGHWAY)\s+\d+[A-Za-z]?
        | COUNTY\s+(?:ROAD|HIGHWAY|ROUTE)\s+\d+[A-Za-z]?
        | FARM\s+TO\s+MARKET\s+ROAD\s+\d+[A-Za-z]?
        | RANCH\s+TO\s+MARKET\s+ROAD\s+\d+[A-Za-z]?
        | ROUTE\s+\d+[A-Za-z]?
    )
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

UNIT_RE = re.compile(
    rf"""
    (?P<prefix>.*?)
    (?:\s+|\s*,\s*|^)
    (?:
        (?P<unit_type>{_UNIT_PATTERN})\s+
        | \#\s*
    )
    (?P<unit_id>[A-Za-z0-9][A-Za-z0-9-]*)
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

UNIT_FIRST_RE = re.compile(
    rf"""
    ^\s*
    (?:
        (?P<unit_type>{_UNIT_PATTERN})\s+
        | \#\s*
    )
    (?P<unit_id>[A-Za-z0-9][A-Za-z0-9-]*)
    \s+
    (?P<body>.+?)
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

STREET_RE = re.compile(
    rf"""
    ^\s*
    (?:(?P<number>\d+[A-Za-z]?(?:-\d+[A-Za-z]?)?)\s+)?
    (?:(?P<predir>{_DIRECTIONAL_PATTERN})\s+)?
    (?P<street_name>.*?)
    (?:\s+(?P<suffix>{_SUFFIX_PATTERN}))?
    (?:\s+(?P<postdir>{_DIRECTIONAL_PATTERN}))?
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)
