"""URL port normalization."""

from __future__ import annotations

from ._schemes import DEFAULT_PORT


def normalize_port(port: str, scheme: str) -> str:
    """Normalize port part of the url.

    Remove leading zeroes and scheme defaults from ASCII decimal port numbers.
    Reject other nonempty port text without validating the numeric range.

    Params:
        port : string : url port, e.g., '8080'
        scheme : string : url scheme, e.g., 'http'

    Returns:
        string : normalized port data.

    Raises:
        ValueError: A nonempty port contains characters outside ASCII digits.

    """
    if not port:
        return port
    if not port.isascii() or not port.isdigit():
        msg = "Port must contain only ASCII digits"
        raise ValueError(msg)
    port = port.lstrip("0") or "0"
    if DEFAULT_PORT.get(scheme) == port:
        return ""
    return port
