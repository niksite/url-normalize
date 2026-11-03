"""URL query normalization."""

from __future__ import annotations

from ._encoding import normalize_component
from ._tracking import TRACKING_PARAMS
from .param_allowlist import get_allowed_params
from .param_filter import _ParamRules, get_params

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
    return normalize_component(param, QUERY_PARAM_SAFE_CHARS)


def normalize_query(  # noqa: PLR0913
    query: str,
    *,  # Force keyword-only arguments
    host: str | None = None,
    filter_params: bool = False,
    param_allowlist: _ParamRules | None = None,
    param_denylist: _ParamRules | None = None,
    remove_tracking_params: bool = False,
    sort_query: bool = False,
) -> str:
    """Normalize query, optionally sorting by key with stable duplicate order.

    Params:
        query: URL query string (e.g. 'param1=val1&param2')
        host: Domain for allowlist checks
        filter_params: Enable built-in allowlist filtering when no custom rule
            is supplied
        param_allowlist: Optional name, sequence, set or domain map overriding
            the default allowlist. Any value other than None enables filtering,
            including an empty collection, regardless of filter_params.
        param_denylist: Optional name, sequence or set of names or domain map to remove.
            Applied without filter_params; denied names override allowed names.
        remove_tracking_params: Remove the built-in set of exact tracker names
            in addition to custom filtering (False by default).
        sort_query: Sort by normalized, percent-encoded key after filtering,
            retaining equal-key order and value separators (False by default).

    Returns:
        Normalized query string with original order unless sorting is requested

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
    if remove_tracking_params:
        denied_params.update(TRACKING_PARAMS)
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

    if sort_query:
        processed.sort(key=lambda param: param.partition("=")[0])
    return "&".join(processed)
