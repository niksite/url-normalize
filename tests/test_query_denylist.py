"""Explicit query removal without enumerating every parameter to retain."""

import pytest

from url_normalize import url_humanize, url_normalize


@pytest.mark.parametrize("api", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    "rule",
    ["utm_source", ["utm_source"], {"EXAMPLE.COM.": "utm_source"}],
)
def test_denylist_preserves_other_parameters(api, rule):
    """Remove all matching occurrences, retaining unknown names and their syntax."""
    # Adapt the removal/duplicate cases from w3lib 2.5.0's test_url_query_cleaner:
    # https://github.com/scrapy/w3lib/blob/v2.5.0/tests/test_url.py
    value = (
        "https://example.com/products?id=123&utm_source=newsletter&variant=blue"
        "&id=456&flag&empty=&utm_source=second#details"
    )
    expected = (
        "https://example.com/products?id=123&variant=blue&id=456&flag&empty=#details"
    )
    assert api(value, param_denylist=rule) == expected
    assert api(expected, param_denylist=rule) == expected


@pytest.mark.parametrize("rule", [None, [], {}, {"other.example": "id"}])
def test_denylist_without_matching_names_retains_query(rule):
    """Do not activate built-in allowlists or invent a fallback domain rule."""
    value = "https://google.com/?id=123&q=hello&utm_source=newsletter"
    assert url_normalize(value, param_denylist=rule) == value


@pytest.mark.parametrize(
    ("query", "rule", "expected"),
    [
        ("%75tm_source=x&id=1", "utm_source", "id=1"),
        ("Id=1&id=2", "id", "Id=1"),
        ("caf%C3%A9=1&keep=2", "cafe\u0301", "keep=2"),  # codespell:ignore caf
        ("a%2Fb=1&a/b=2", "a/b", "a%2Fb=1"),
        ("a%2Fb=1&a/b=2", "a%2fb", "a/b=2"),
        ("a+b=1&a%20b=2&a%2Bb=3", "a+b", "a%20b=2&a%2Bb=3"),
        ("page,id=1&page=2&id=3", "page,id", "page=2&id=3"),
        ("=empty&id=1", "", "id=1"),
    ],
)
def test_denylist_uses_normalized_literal_names(query, rule, expected):
    """Use the same case-sensitive Unicode and escape rules as an allowlist."""
    assert (
        url_normalize(f"https://example.com/?{query}", param_denylist=rule)
        == f"https://example.com/?{expected}"
    )


@pytest.mark.parametrize("api", [url_normalize, url_humanize])
def test_denylist_wins_allowlist_overlap(api):
    """Apply both explicitly requested rules, including overlap and empty lists."""
    value = "https://example.com/?id=1&tag=red&id=2&drop=3"
    rules = {"example.com": ["id", "tag"]}
    assert api(value, param_allowlist=rules, param_denylist="tag") == (
        "https://example.com/?id=1&id=2"
    )
    assert api(value, param_allowlist=rules, param_denylist=[]) == (
        "https://example.com/?id=1&tag=red&id=2"
    )
    assert api(value, param_allowlist=[], param_denylist="tag") == (
        "https://example.com/"
    )
    assert rules == {"example.com": ["id", "tag"]}


def test_denylist_narrows_builtin_rules():
    """Remove an unwanted built-in name without copying the built-in allowlist."""
    assert (
        url_normalize(
            "https://google.com/search?q=hello&ie=UTF-8&utm_source=newsletter",
            filter_params=True,
            param_denylist="ie",
        )
        == "https://google.com/search?q=hello"
    )


@pytest.mark.parametrize("keep_empty", [False, True])
def test_denylist_removing_last_name_uses_empty_component_policy(keep_empty):
    """Preserve an emptied query delimiter only when requested."""
    expected = "https://example.com/?#" if keep_empty else "https://example.com/"
    assert (
        url_normalize(
            "https://example.com/?drop=1#",
            param_denylist="drop",
            keep_empty_components=keep_empty,
        )
        == expected
    )


@pytest.mark.parametrize("api", [url_normalize, url_humanize])
def test_denylist_on_relative_reference(api):
    """Keep relative and slash policies while removing a query name."""
    assert (
        api(
            "../a//b?keep=1&drop=2#",
            param_denylist="drop",
            collapse_slashes=False,
            keep_empty_components=True,
        )
        == "../a//b?keep=1#"
    )


def test_denylist_humanizes_retained_unicode():
    """Retain readable Unicode after filtering and preserve the normalized value."""
    value = "https://example.com/?keep=caf%C3%A9&drop=1"  # codespell:ignore caf
    assert url_humanize(value, param_denylist="drop") == (
        "https://example.com/?keep=café"
    )
    assert url_normalize(url_humanize(value, param_denylist="drop")) == (
        url_normalize(value, param_denylist="drop")
    )


def test_denylist_domain_rules_are_reusable():
    """Share canonical-domain precedence without mutating caller-owned rules."""
    rules = {"example.com": [], "EXAMPLE.COM.": "id", "other.example": ["id"]}
    value = "https://www.example.com:443/?id=1&keep=2"
    assert url_normalize(value, param_denylist=rules) == (
        "https://www.example.com/?id=1&keep=2"
    )
    assert url_normalize(
        "https://other.example/?id=1&keep=2", param_denylist=rules
    ) == ("https://other.example/?keep=2")
    assert rules == {"example.com": [], "EXAMPLE.COM.": "id", "other.example": ["id"]}
