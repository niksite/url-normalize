"""Unicode and percent-encoding primitives for URL components."""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import quote as quote_orig
from urllib.parse import unquote as unquote_orig

RESERVED_CHARACTERS = ":/?#[]@!$&'()*+,;="
RESERVED_ESCAPE_RE = re.compile(
    "(" + "|".join(f"%{ord(character):02X}" for character in RESERVED_CHARACTERS) + ")",
    re.IGNORECASE,
)
# Bidi_Control: https://www.unicode.org/Public/UCD/latest/ucd/PropList.txt
# Join_Control characters are separate.
BIDI_CONTROL_CHARACTERS = frozenset(
    "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
)


def has_display_controls(value: str) -> bool:
    """Identify terminal controls, bidi controls and Unicode line separators."""
    return any(
        unicodedata.category(character) in {"Cc", "Zl", "Zp"}
        or character in BIDI_CONTROL_CHARACTERS
        for character in value
    )


def force_unicode(string: str | bytes) -> str:
    """Decode UTF-8 bytes while leaving strings unchanged.

    Params:
        string : str | bytes : input text or UTF-8 bytes

    Returns:
        str

    """
    if isinstance(string, bytes):
        return string.decode("utf-8", "replace")
    return string


def unquote(string: str) -> str:
    """Unquote and normalize unicode string.

    Params:
        string : string to be unquoted

    Returns:
        string : an unquoted and normalized string

    """
    string = unquote_orig(string, errors="surrogateescape")
    return unicodedata.normalize("NFC", string)


def quote(string: str, safe: str = "/") -> str:
    """Quote string.

    Params:
        string : string to be quoted
        safe : string of safe characters

    Returns:
        string : quoted string

    """
    return quote_orig(string, safe, errors="surrogateescape")


def normalize_component(string: str, safe: str) -> str:
    """Normalize escapes and Unicode without decoding reserved delimiters."""
    return "".join(
        part.upper() if index % 2 else quote(unquote(part), safe)
        for index, part in enumerate(RESERVED_ESCAPE_RE.split(string))
    )
