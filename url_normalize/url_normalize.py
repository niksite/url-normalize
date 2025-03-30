"""URL normalize main module."""

from __future__ import annotations

import re

import idna

from .tools import (
    deconstruct_url,
    force_unicode,
    quote,
    reconstruct_url,
    unquote,
)

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
DEFAULT_CHARSET = "utf-8"
DEFAULT_SCHEME = "https"


def provide_url_scheme(url: str, default_scheme: str = DEFAULT_SCHEME) -> str:
    """Make sure we have valid url scheme.

    Params:
        url : string : the URL
        default_scheme : string : default scheme to use, e.g. 'https'

    Returns:
        string : updated url with validated/attached scheme

    """
    has_scheme = ":" in url[:7]
    is_universal_scheme = url.startswith("//")
    is_file_path = url == "-" or (url.startswith("/") and not is_universal_scheme)
    if not url or has_scheme or is_file_path:
        return url
    if is_universal_scheme:
        return default_scheme + ":" + url
    return default_scheme + "://" + url


def generic_url_cleanup(url: str) -> str:
    """Cleanup the URL from unnecessary data and convert to final form.

    Converts shebang urls to final form, removed unnecessary data from the url.

    Params:
        url : string : the URL

    Returns:
        string : update url

    """
    url = url.replace("#!", "?_escaped_fragment_=")
    url = re.sub(r"utm_source=[^&]+&?", "", url)
    return url.rstrip("&? ")


def normalize_scheme(scheme: str) -> str:
    """Normalize scheme part of the url.

    Params:
        scheme : string : url scheme, e.g., 'https'

    Returns:
        string : normalized scheme data.

    """
    return scheme.lower()


def normalize_userinfo(userinfo: str) -> str:
    """Normalize userinfo part of the url.

    Params:
        userinfo : string : url userinfo, e.g., 'user@'

    Returns:
        string : normalized userinfo data.

    """
    if userinfo in ["@", ":@"]:
        return ""
    return userinfo


def normalize_host(host: str, charset: str = DEFAULT_CHARSET) -> str:
    """Normalize host part of the url.

    Lowercase and strip of final dot.
    Also, handle IDN domains using IDNA2008 with UTS46 transitional processing.

    Params:
        host : string : url host, e.g., 'site.com'
        charset : string : encoding charset

    Returns:
        string : normalized host data.

    """
    host = force_unicode(host, charset)
    host = host.lower()
    host = host.strip(".")

    # Split domain into parts to handle each label separately
    parts = host.split(".")
    try:
        # Process each label separately to handle mixed unicode/ascii domains
        parts = [
            idna.encode(p, uts46=True, transitional=True).decode(charset)
            for p in parts
            if p
        ]
        return ".".join(parts)
    except idna.IDNAError:
        # Fallback to direct encoding if IDNA2008 processing fails
        return host.encode("idna").decode(charset)


def normalize_port(port: str, scheme: str) -> str:
    """Normalize port part of the url.

    Remove mention of default port number

    Params:
        port : string : url port, e.g., '8080'
        scheme : string : url scheme, e.g., 'http'

    Returns:
        string : normalized port data.

    """
    if not port.isdigit():
        return port
    port = str(int(port))
    if DEFAULT_PORT.get(scheme) == port:
        return ""
    return port


def normalize_path(path: str, scheme: str) -> str:
    """Normalize path part of the url.

    Remove mention of default path number

    Params:
        path : string : url path, e.g., '/section/page.html'
        scheme : string : url scheme, e.g., 'http'

    Returns:
        string : normalized path data.

    """
    # Only perform percent-encoding where it is essential.
    # Always use uppercase A-through-F characters when percent-encoding.
    # All portions of the URI must be utf-8 encoded NFC from Unicode strings
    path = quote(unquote(path), "~:/?#[]@!$&'()*+,;=")
    # Prevent dot-segments appearing in non-relative URI paths.
    if scheme in ["", "http", "https", "ftp", "file"]:
        output: list[str] = []
        for part in path.split("/"):
            if part == "":
                if not output:
                    output.append(part)
            elif part == ".":
                pass
            elif part == "..":
                if len(output) > 1:
                    output.pop()
            else:
                output.append(part)
        # The part variable is used in the final check
        last_part = part
        if last_part in ["", ".", ".."]:
            output.append("")
        path = "/".join(output)
    # For schemes that define an empty path to be equivalent to a path of "/",
    # use "/".
    if not path and scheme in ["http", "https", "ftp", "file"]:
        path = "/"
    return path


def normalize_fragment(fragment: str) -> str:
    """Normalize fragment part of the url.

    Params:
        fragment : string : url fragment, e.g., 'fragment'

    Returns:
        string : normalized fragment data.

    """
    return quote(unquote(fragment), "~")


def normalize_query(query: str, *, sort_query_params: bool = True) -> str:
    """Normalize query part of the url.

    Params:
        query : string : url query, e.g., 'param1=val1&param2=val2'
        sort_query_params : bool : whether to sort query parameters

    Returns:
        string : normalized query data.

    """
    param_arr = [
        "=".join(
            [quote(unquote(t), "~:/?#[]@!$'()*+,;=") for t in q.split("=", 1)],
        )
        for q in query.split("&")
        if q
    ]
    if sort_query_params:
        param_arr = sorted(param_arr)
    return "&".join(param_arr)


def url_normalize(
    url: str | None,
    charset: str = DEFAULT_CHARSET,
    default_scheme: str = DEFAULT_SCHEME,
    *,
    sort_query_params: bool = True,
) -> str | None:
    """URI normalization routine.

    Sometimes you get an URL by a user that just isn't a real
    URL because it contains unsafe characters like ' ' and so on.
    This function can fix some of the problems in a similar way
    browsers handle data entered by the user:

    >>> url_normalize('http://de.wikipedia.org/wiki/Elf (Begriffsklärung)')
    'http://de.wikipedia.org/wiki/Elf%20%28Begriffskl%C3%A4rung%29'

    Params:
        url : str | None : URL to normalize
        charset : str : optional
            The target charset for the URL if the url was given as unicode string
        default_scheme : str : default scheme to use if none present
        sort_query_params : bool : whether to sort query parameters

    Returns:
        str | None : a normalized url

    """
    if not url:
        return url
    url = provide_url_scheme(url, default_scheme)
    url = generic_url_cleanup(url)
    url_elements = deconstruct_url(url)
    url_elements = url_elements._replace(
        scheme=normalize_scheme(url_elements.scheme),
        userinfo=normalize_userinfo(url_elements.userinfo),
        host=normalize_host(url_elements.host, charset),
        query=normalize_query(url_elements.query, sort_query_params=sort_query_params),
        fragment=normalize_fragment(url_elements.fragment),
    )
    url_elements = url_elements._replace(
        port=normalize_port(url_elements.port, url_elements.scheme),
        path=normalize_path(url_elements.path, url_elements.scheme),
    )
    return reconstruct_url(url_elements)
