"""Shared parameter-name and domain matching for explicit query rules."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from typing import TypeAlias

from .normalize_host import normalize_host

# Separate name collections from mappings so invalid domain values cannot pass
# type checking merely because their dictionary has string keys.
_ParamNames: TypeAlias = str | Sequence[str] | AbstractSet[str]
_ParamRules: TypeAlias = _ParamNames | Mapping[str, _ParamNames]


def _normalize_domain(host: str) -> str:
    """Canonicalize a rule domain without its port or www prefix."""
    if host.startswith("[") and "]" in host:
        host = host.partition("]")[0] + "]"
    else:
        host = host.partition(":")[0]
    return normalize_host(host).removeprefix("www.")


def _parameter_names(names: _ParamNames) -> set[str]:
    """Treat a string as one parameter name rather than a sequence of characters."""
    return {names} if isinstance(names, str) else set(names)


def get_params(host: str | None, rules: _ParamRules | None) -> set[str]:
    """Select names from an explicit global or domain rule, without fallback rules."""
    if isinstance(rules, str | Sequence | AbstractSet):
        return _parameter_names(rules)

    if rules is None or not host:
        return set()

    domain = _normalize_domain(host)

    # A key still starting with www. is itself an alias for a different domain.
    # Otherwise prefer an exact canonical key, even when its rule is empty.
    if domain in rules and not domain.startswith("www."):
        return _parameter_names(rules[domain])
    for key, params in rules.items():
        try:
            key_domain = _normalize_domain(key)
        except UnicodeError:
            continue
        if key_domain == domain:
            return _parameter_names(params)
    return set()
