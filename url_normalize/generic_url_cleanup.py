"""URL generic cleanup operations."""

from __future__ import annotations

from .tools import quote, unquote


def generic_url_cleanup(url: str) -> str:
    """Cleanup the URL from unnecessary data and convert to final form.

    Converts shebang urls to final form, removed unnecessary data from the url.

    Params:
        url : string : the URL

    Returns:
        string : update url

    """
    base, fragment_separator, fragment = url.partition("#")
    path, _, query = base.partition("?")
    query = "&".join(param for param in query.split("&") if param)
    if fragment.startswith("!"):
        payload = quote(unquote(fragment[1:]), safe="/")
        query += ("&" if query else "") + f"_escaped_fragment_={payload}"
        fragment_separator = fragment = ""
    return path + (f"?{query}" if query else "") + fragment_separator + fragment
