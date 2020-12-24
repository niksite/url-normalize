"""Url normalize tools (py27/py37 compatible)."""
import re
import unicodedata
from collections import namedtuple
from typing import Match, Union, cast

import six
from six.moves.urllib.parse import quote as quote_orig
from six.moves.urllib.parse import unquote as unquote_orig
from six.moves.urllib.parse import urlsplit, urlunsplit

URL = namedtuple(
    "URL", ["scheme", "userinfo", "host", "port", "path", "query", "fragment"]
)


def deconstruct_url(url):  # type: (str) -> URL
    """Transform the url into URL structure.

    Params:
        url : string : the URL

    Returns:
        URL

    """
    scheme, auth, path, query, fragment = urlsplit(url.strip())
    # cast: the regex matches anything
    (userinfo, host, port) = cast(Match[str], re.search("([^@]*@)?([^:]*):?(.*)", auth)).groups()
    return URL(
        fragment=fragment,
        host=host,
        path=path,
        port=port,
        query=query,
        scheme=scheme,
        userinfo=userinfo or "",
    )


def reconstruct_url(url):  # type: (URL) -> str
    """Reconstruct string url from URL.

    Params:
        url : URL object instance

    Returns:
        string : reconstructed url string

    """
    auth = (url.userinfo or "") + url.host
    if url.port:
        auth += ":" + url.port
    # cast: needed when checking as python 2.7, redundant with 3.6+
    return cast(str, urlunsplit((url.scheme, auth, url.path, url.query, url.fragment)))


def force_unicode(string, charset="utf-8"):  # type: (Union[bytes, str], str) -> str
    """Convert string to unicode if it is not yet unicode.

    Params:
        string : string/unicode : an input string
        charset : string : optional : output encoding

    Returns:
        unicode

    """
    if isinstance(string, six.text_type):  # Always True on Py3
        return string
    return string.decode(charset, "replace")  # Py2 only


def unquote(string, charset="utf-8"):  # type: (str, str) -> bytes
    """Unquote and normalize unicode string.

    Params:
        string : string to be unquoted
        charset : string : optional : output encoding

    Returns:
        string : an unquoted and normalized string

    """
    string = unquote_orig(string)
    string = force_unicode(string, charset)
    bstring = unicodedata.normalize("NFC", string).encode(charset)
    return bstring


def quote(string, safe="/"):  # type: (Union[bytes, str], Union[bytes, str]) -> str
    """Quote string.

    Params:
        string : string to be quoted
        safe : string of safe characters

    Returns:
        string : quoted string

    """
    string = quote_orig(string, safe)
    return string
