"""URL input cleanup, component representation, parsing and reconstruction."""

from __future__ import annotations

import re
from typing import NamedTuple
from urllib.parse import urlsplit, urlunsplit


def cleanup_url_input(url: str) -> str:
    """Remove parser-ignored characters before URL classification."""
    # Match urlsplit's C0/tab/newline cleanup, retaining Unicode whitespace support.
    url = re.sub(r"^[\x00-\x20\s]+", "", url)
    return url.replace("\t", "").replace("\r", "").replace("\n", "")


class URL(NamedTuple):
    """URL components tuple.

    A named tuple containing the parsed components of a URL:
    scheme, userinfo, host, port, path, query, and fragment.
    Presence flags distinguish absent queries/fragments from empty ones.
    """

    scheme: str
    userinfo: str
    host: str
    port: str
    path: str
    query: str
    fragment: str
    query_present: bool = False
    fragment_present: bool = False


def deconstruct_url(url: str) -> URL:
    """Transform the url into URL structure.

    Params:
        url : string : the URL

    Returns:
        URL

    """
    scheme, auth, path, query, fragment = urlsplit(url)
    before_fragment, fragment_separator, _ = url.partition("#")
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
        query_present="?" in before_fragment,
        fragment_present=bool(fragment_separator),
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
    result = urlunsplit((url.scheme, auth, url.path, "", ""))
    if url.query or url.query_present:
        result += "?" + url.query
    if url.fragment or url.fragment_present:
        result += "#" + url.fragment
    return result
