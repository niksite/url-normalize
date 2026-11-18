"""Scheme-specific normalization rules, kept independent of each other."""

import re

DEFAULT_PORT = {
    "ftp": "21",
    "gopher": "70",
    "http": "80",
    "https": "443",
    "news": "119",
    "nntp": "119",
    "snews": "563",
    "snntp": "563",
    "telnet": "23",
    "ws": "80",
    "wss": "443",
}

# Schemes whose missing authority slashes are repaired during input handling.
AUTHORITY_SCHEMES = frozenset({"http", "https", "ftp", "ftps"})

# An empty scheme allows path references; document-relative paths retain parents.
PATH_NORMALIZATION_SCHEMES = frozenset(
    {"", "http", "https", "ftp", "file", "ws", "wss"}
)
EMPTY_PATH_SCHEMES = frozenset({"http", "https", "ftp", "file", "ws", "wss"})


def looks_like_host_port(scheme: str, rest: str) -> bool:
    """Identify a bare dotted host or localhost followed by a decimal port."""
    return ("." in scheme or scheme.lower() == "localhost") and bool(
        re.match(r"[0-9]+\s*(?:[/?#]|$)", rest)
    )
