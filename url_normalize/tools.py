"""URL normalization tools."""

from __future__ import annotations

import re
import unicodedata
from typing import NamedTuple
from urllib.parse import quote as quote_orig
from urllib.parse import unquote as unquote_orig
from urllib.parse import urlsplit, urlunsplit

RESERVED_CHARACTERS = ":/?#[]@!$&'()*+,;="


def cleanup_url_input(url: str) -> str:
    """Remove parser-ignored characters before URL classification."""
    # Match urlsplit's C0/tab/newline cleanup, retaining Unicode whitespace support.
    url = re.sub(r"^[\x00-\x20\s]+", "", url)
    return url.replace("\t", "").replace("\r", "").replace("\n", "")


class URL(NamedTuple):
    """URL components tuple.

    A named tuple containing the parsed components of a URL:
    scheme, userinfo, host, port, path, query, and fragment.
    """

    scheme: str
    userinfo: str
    host: str
    port: str
    path: str
    query: str
    fragment: str


def deconstruct_url(url: str) -> URL:
    """Transform the url into URL structure.

    Params:
        url : string : the URL

    Returns:
        URL

    """
    scheme, auth, path, query, fragment = urlsplit(url)
    userinfo, separator, host_port = auth.rstrip().rpartition("@")
    userinfo += separator
    if host_port.startswith("["):
        host, _, port = host_port.partition("]")
        host += "]"
        port = port.removeprefix(":")
    else:
        host, _, port = host_port.partition(":")
    return URL(
        fragment=fragment,
        host=host,
        path=path,
        port=port or "",
        query=query,
        scheme=scheme,
        userinfo=userinfo or "",
    )


def reconstruct_url(url: URL) -> str:
    """Reconstruct string url from URL.

    Params:
        url : URL object instance

    Returns:
        string : reconstructed url string

    """
    auth = (url.userinfo or "") + url.host
    if url.port:
        auth += ":" + url.port
    return urlunsplit((url.scheme, auth, url.path, url.query, url.fragment))


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


def normalize_component(string: str, safe: str, preserve: str) -> str:
    """Normalize escapes and Unicode without decoding protected delimiters."""
    protected = "|".join(f"%{ord(character):02X}" for character in preserve)
    parts = re.split(f"({protected})", string, flags=re.IGNORECASE)
    return "".join(
        part.upper() if index % 2 else quote(unquote(part), safe)
        for index, part in enumerate(parts)
    )
