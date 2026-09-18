# Copyright (c) 2023. All rights reserved.
"""URL query parameter allowlist module."""

from __future__ import annotations

from .normalize_host import normalize_host

DEFAULT_ALLOWLIST = {
    "google.com": ["q", "ie"],
    "baidu.com": ["wd", "ie"],
    "bing.com": ["q"],
    "youtube.com": ["v", "search_query"],
}


def _normalize_domain(host: str) -> str:
    """Canonicalize an allowlist domain without its port or www prefix."""
    if host.startswith("[") and "]" in host:
        host = host.partition("]")[0] + "]"
    else:
        host = host.partition(":")[0]
    return normalize_host(host).removeprefix("www.")


def get_allowed_params(
    host: str | None = None,
    allowlist: dict | list | None = None,
) -> set[str]:
    """Get allowed parameters for a given domain.

    Params:
        host: Domain name to check (e.g. 'google.com')
        allowlist: Optional override for default allowlist
            If provided as a list, it will be used as is.
            If provided as a dictionary, it should map domain names to
            lists of allowed parameters.
            If None, the default allowlist will be used.

    Returns:
        Set of allowed parameter names for the domain

    """
    if isinstance(allowlist, list):
        return set(allowlist)

    if not host:
        return set()

    domain = _normalize_domain(host)

    # Use default allowlist if none provided
    if allowlist is None:
        allowlist = DEFAULT_ALLOWLIST

    # Preserve exact canonical-key precedence, including an empty allowlist.
    if domain in allowlist:
        return set(allowlist[domain])
    for key, params in allowlist.items():
        try:
            key_domain = _normalize_domain(key)
        except UnicodeError:
            continue
        if key_domain == domain:
            return set(params)
    return set()
