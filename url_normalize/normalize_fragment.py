"""URL fragment normalization."""

from __future__ import annotations

import re

from ._encoding import quote, unquote

# Fragments can embed syntax parsed before percent-decoding, including
# unreserved ASCII characters (e.g. "-", "~" and the letters in "text=").
FRAGMENT_ASCII_ESCAPE_RE = re.compile(r"(%[0-7][0-9A-Fa-f])")


def normalize_fragment(fragment: str) -> str:
    """Normalize fragment part of the url.

    Params:
        fragment : string : url fragment, e.g., 'fragment'

    Returns:
        string : normalized fragment data.

    Notes:
        According to RFC 3986, the following characters are allowed in a fragment:
        fragment    = *( pchar / "/" / "?" )
        pchar       = unreserved / pct-encoded / sub-delims / ":" / "@"
        unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"
        sub-delims  = "!" / "$" / "&" / "'" / "(" / ")" / "*" / "+" / "," / ";" / "="
        Preserve these literal characters and existing ASCII escapes so embedded
        routing and text-directive syntax is not activated or deactivated.
        Non-ASCII text retains the usual UTF-8 and NFC normalization.

    """
    return "".join(
        part.upper() if index % 2 else quote(unquote(part), safe="~!$&'()*+,;=:@/?")
        for index, part in enumerate(FRAGMENT_ASCII_ESCAPE_RE.split(fragment))
    )
