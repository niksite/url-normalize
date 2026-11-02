"""Reuse query rules without requiring mutable lists and dictionaries."""

from collections import UserDict, UserList
from types import MappingProxyType

import pytest

from url_normalize import url_humanize, url_normalize


@pytest.mark.parametrize(
    "names",
    [
        ("tag", "id"),
        {"tag", "id"},
        frozenset({"tag", "id"}),
        UserList(["tag", "id"]),
        {"tag": None, "id": None}.keys(),
    ],
)
def test_reusable_global_names(names):
    """Choose names without letting collection order change query order."""
    value = "https://example.com/?id=1&tag=red&id=2&drop=3#details"
    expected = "https://example.com/?id=1&tag=red&id=2#details"
    for api in (url_normalize, url_humanize):
        assert api(value, param_allowlist=names) == expected
        assert api(expected, param_allowlist=names) == expected
        assert api(value, param_denylist=names) == (
            "https://example.com/?drop=3#details"
        )
    assert set(names) == {"tag", "id"}


@pytest.mark.parametrize("names", [(), set(), frozenset()])
def test_empty_collections_keep_existing_activation_policy(names):
    """An empty allowlist removes everything; an empty denylist removes nothing."""
    value = "https://example.com/?id=1#details"
    assert url_normalize(value, param_allowlist=names) == (
        "https://example.com/#details"
    )
    assert url_normalize(value, param_denylist=names) == value


@pytest.mark.parametrize("mapping", [dict, UserDict, MappingProxyType])
def test_domain_mappings_preserve_precedence_and_rule_values(mapping):
    """Select a domain's values, including canonical empty rules, without mutation."""
    original = {"EXAMPLE.COM.": ("id", "tag"), "example.com": frozenset()}
    rules = mapping(original)
    value = "https://www.example.com:443/?id=1&tag=red&drop=2"
    assert url_normalize(value, param_allowlist=rules) == "https://www.example.com/"
    assert url_normalize(value, param_denylist=rules) == (
        "https://www.example.com/?id=1&tag=red&drop=2"
    )
    assert url_normalize(value, param_allowlist=mapping({"EXAMPLE.COM.": ("id",)})) == (
        "https://www.example.com/?id=1"
    )
    assert url_normalize(value, param_denylist=mapping({"EXAMPLE.COM.": {"tag"}})) == (
        "https://www.example.com/?id=1&drop=2"
    )
    assert dict(rules) == original


def test_collections_on_relative_references_and_unicode_display():
    """Apply both filters without a hostname and retain humanization behavior."""
    value = "../search?keep=caf%C3%A9&drop=1&extra=2"  # codespell:ignore caf
    allowed = ("keep", "drop")
    denied = frozenset({"drop"})
    assert url_normalize(value, param_allowlist=allowed, param_denylist=denied) == (
        "../search?keep=caf%C3%A9"  # codespell:ignore caf
    )
    assert url_humanize(value, param_allowlist=allowed, param_denylist=denied) == (
        "../search?keep=café"
    )
