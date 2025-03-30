"""URL query normalization."""

from __future__ import annotations

from .tools import quote, unquote


def normalize_query(query: str) -> str:
    """Normalize query part of the url.

    Params:
        query : string : url query, e.g., 'param1=val1&param2=val2'

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
    return "&".join(param_arr)
