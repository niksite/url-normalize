"""URL query normalization."""

from __future__ import annotations

from .tools import quote, unquote


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
