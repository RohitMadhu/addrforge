"""Optional exceptions for callers that want explicit error handling."""


class AddrforgeError(Exception):
    """Base exception for addrforge errors."""


class ParseError(AddrforgeError):
    """Raised by future strict parsing APIs."""
