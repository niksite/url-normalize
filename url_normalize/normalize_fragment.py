"""URL fragment normalization."""

from __future__ import annotations

from .tools import quote, unquote


def normalize_fragment(fragment: str) -> str:
    """Normalize fragment part of the url.

    Params:
        fragment : string : url fragment, e.g., 'fragment'

    Returns:
        string : normalized fragment data.

    """
    return quote(unquote(fragment), "~")
