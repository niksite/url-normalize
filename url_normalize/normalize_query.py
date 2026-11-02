"""URL query normalization."""

from __future__ import annotations

from .param_allowlist import get_allowed_params
from .param_filter import get_params
from .tools import RESERVED_CHARACTERS, normalize_component

QUERY_PARAM_SAFE_CHARS = "~:/?[]@!$'()*+,;"


def process_query_param(param: str) -> str:
    """Process a single query parameter.

    Keep existing reserved-character escapes distinct from literal punctuation.
    Decode unreserved escapes, normalize Unicode to NFC, and use UTF-8 encoding.

    Params:
        param: The query parameter to process.

    Returns:
        str: The normalized query parameter.

    """
    if not param:
        return ""
    return normalize_component(param, QUERY_PARAM_SAFE_CHARS, RESERVED_CHARACTERS)


def normalize_query(
    query: str,
    *,  # Force keyword-only arguments
    host: str | None = None,
    filter_params: bool = False,
    param_allowlist: list | dict | str | None = None,
    param_denylist: list | dict | str | None = None,
) -> str:
    """Normalize query while preserving parameter order.

    Params:
        query: URL query string (e.g. 'param1=val1&param2')
        host: Domain for allowlist checks
        filter_params: Enable built-in allowlist filtering when no custom rule
            is supplied
        param_allowlist: Optional name, list of names or domain map overriding
            the default allowlist. Any value other than None enables filtering,
            including an empty collection, regardless of filter_params.
        param_denylist: Optional name, list of names or domain map to remove.
            Applied without filter_params; denied names override allowed names.

    Returns:
        Normalized query string with original parameter order

    """
    if not query:
        return ""

    allowed_params = (
        {
            process_query_param(param)
            for param in get_allowed_params(host, param_allowlist)
        }
        if filter_params or param_allowlist is not None
        else None
    )
    denied_params = {
        process_query_param(param) for param in get_params(host, param_denylist)
    }
    processed = []
    for param in query.split("&"):
        if not param:
            continue
        key, separator, value = param.partition("=")
        key = process_query_param(key)
        if (
            allowed_params is not None and key not in allowed_params
        ) or key in denied_params:
            continue
        value = process_query_param(value)
        processed.append(f"{key}{separator}{value}")

    return "&".join(processed)
