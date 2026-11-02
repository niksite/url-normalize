# Copyright (c) 2023. All rights reserved.
"""URL query parameter allowlist module."""

from __future__ import annotations

from .param_filter import _ParamRules, get_params

DEFAULT_ALLOWLIST = {
    "google.com": ["q", "ie"],
    "baidu.com": ["wd", "ie"],
    "bing.com": ["q"],
    "youtube.com": ["v", "search_query"],
}


def get_allowed_params(
    host: str | None = None,
    allowlist: _ParamRules | None = None,
) -> set[str]:
    """Get allowed parameters for a given domain.

    Params:
        host: Domain name to check (e.g. 'google.com')
        allowlist: Optional override for default allowlist
            A string is one complete parameter name, including commas or an
            empty name. A sequence or set provides multiple parameter names.
            If provided as a mapping, it should map domain names to
            single names, sequences or sets of allowed parameters.
            If None, the default allowlist will be used.

    Returns:
        Set of allowed parameter names for the domain

    """
    return get_params(host, DEFAULT_ALLOWLIST if allowlist is None else allowlist)
