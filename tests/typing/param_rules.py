"""Check accepted rule interfaces and reject malformed filter configuration."""

from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from types import MappingProxyType
from typing import assert_type

from url_normalize import url_humanize, url_normalize


def check_interfaces(
    sequence: Sequence[str],
    names: AbstractSet[str],
    domains: Mapping[str, str | Sequence[str] | AbstractSet[str]],
) -> None:
    """Accept read-only interfaces without requiring concrete mutable containers."""
    value = "https://example.com/?id=1&drop=2"
    assert_type(url_normalize(value, param_allowlist=sequence), str)
    assert_type(url_humanize(value, param_allowlist=names), str)
    assert_type(url_normalize(value, param_allowlist=domains), str)
    assert_type(url_humanize(value, param_denylist=domains), str)
    assert_type(url_normalize(None, param_denylist=names), None)
    assert_type(url_humanize(None, param_denylist=sequence), None)
    assert_type(url_normalize(value, param_allowlist=("id",)), str)
    assert_type(url_humanize(value, param_denylist=frozenset({"drop"})), str)
    assert_type(url_normalize(value, param_allowlist={"id": None}.keys()), str)
    assert_type(
        url_humanize(value, param_allowlist=MappingProxyType({"example.com": {"id"}})),
        str,
    )


def check_invalid_rules() -> None:
    """Require each suppression to match an actual rejected call."""
    # unused-ignore-comment is an error: these checks fail if a bad call is accepted.
    value = "https://example.com/?id=1"
    url_normalize(value, param_allowlist=[1])  # ty: ignore[no-matching-overload]
    url_humanize(value, param_denylist={1: "id"})  # ty: ignore[no-matching-overload]
    url_normalize(value, param_allowlist={"example.com": 1})  # ty: ignore[no-matching-overload]
    url_humanize(value, param_denylist={"example.com": [1]})  # ty: ignore[no-matching-overload]
    url_normalize(value, param_denylist=b"id")  # ty: ignore[no-matching-overload]
    url_humanize(value, param_allowlist={1})  # ty: ignore[no-matching-overload]
    url_normalize(None, param_allowlist=iter(["id"]))  # ty: ignore[no-matching-overload]
    url_humanize(None, param_denylist=(1,))  # ty: ignore[no-matching-overload]
