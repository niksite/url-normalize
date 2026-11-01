"""URL generic cleanup operations."""

from __future__ import annotations


def generic_url_cleanup(url: str) -> str:
    """Remove empty query fields without interpreting fragment content.

    Params:
        url : string : the URL

    Returns:
        string : update url

    """
    base, fragment_separator, fragment = url.partition("#")
    path, _, query = base.partition("?")
    query = "&".join(param for param in query.split("&") if param)
    return path + (f"?{query}" if query else "") + fragment_separator + fragment
