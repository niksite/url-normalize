"""URL input cleanup, component representation, parsing and reconstruction."""

from __future__ import annotations

import re
from typing import NamedTuple
from urllib.parse import SplitResult, urlsplit, urlunsplit

# Limit zone handling to a bracketed host in the authority, after any userinfo.
_SCOPED_HOST = re.compile(
    r"(?:[A-Za-z][A-Za-z0-9+.-]*:)?//(?P<authority>(?:[^/?#]*@)?"
    r"\[[A-Fa-f0-9:.]+%)(?P<zone>[^][/?#@]+)\]"
)


def _split_url(url: str) -> SplitResult:
    """Validate URL syntax without asking ipaddress to decode zone escapes."""
    scoped = _SCOPED_HOST.match(url) if "%" in url and "[" in url else None
    parser_input = url
    if scoped:
        # ipaddress permits a single scope separator. Mask only further %HH
        # markers inside the zone, keeping all other parser checks and offsets.
        start, end = scoped.span("zone")
        zone = re.sub(r"%(?=[0-9A-Fa-f]{2})", "_", scoped["zone"])
        parser_input = url[:start] + zone + url[end:]
    try:
        parts = urlsplit(parser_input)
    except ValueError:
        # Parser messages may contain the complete authority, including credentials.
        msg = "Invalid URL authority"
        raise ValueError(msg) from None
    if scoped:
        start = scoped.start("authority")
        parts = parts._replace(netloc=url[start : start + len(parts.netloc)])
    return parts


def cleanup_url_input(url: str) -> str:
    """Remove parser-ignored characters before URL classification."""
    # Match urlsplit's C0/tab/newline cleanup, retaining Unicode whitespace support.
    url = re.sub(r"^[\x00-\x20\s]+", "", url)
    return url.replace("\t", "").replace("\r", "").replace("\n", "")


class URL(NamedTuple):
    """URL components tuple.

    A named tuple containing the parsed components of a URL:
    scheme, userinfo, host, port, path, query, and fragment.
    Flags record the presence of the authority, query and fragment delimiters.
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
    authority_present: bool = False


def deconstruct_url(url: str) -> URL:
    """Transform the url into URL structure.

    Params:
        url : string : the URL

    Returns:
        URL

    """
    scheme, auth, path, query, fragment = _split_url(url)
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
        authority_present=url.startswith("//", len(scheme) + 1 if scheme else 0),
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
    if url.authority_present and not auth:
        scheme_prefix = f"{url.scheme}:" if url.scheme else ""
        result = f"{scheme_prefix}//{url.path}"
    else:
        result = urlunsplit((url.scheme, auth, url.path, "", ""))
    if url.query or url.query_present:
        result += "?" + url.query
    if url.fragment or url.fragment_present:
        result += "#" + url.fragment
    return result
