"""Optional query sorting with stable duplicate order and retained syntax."""

from urllib.parse import parse_qs, urlsplit

import pytest

from url_normalize import url_humanize, url_normalize


@pytest.mark.parametrize("api", [url_normalize, url_humanize])
def test_query_sorting_is_opt_in(api):
    """Preserve input order by default, including repeated values."""
    value = "https://example.com/search?b=2&a=3&a=1"
    assert api(value) == value
    assert api(value, sort_query=False) == value
    assert api(value, sort_query=True) == ("https://example.com/search?a=3&a=1&b=2")


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("b=2&a=3&a=1", "a=3&a=1&b=2"),
        ("a=3&%61=2&b=0&a=1", "a=3&a=2&a=1&b=0"),
        (
            "z=1&flag=&flag&flag=x=y&=empty&flag=",
            "=empty&flag=&flag&flag=x%3Dy&flag=&z=1",
        ),
        ("b=1&A=2&a=3", "A=2&a=3&b=1"),
        ("z=1&é=2&e%CC%81=3&a=4", "%C3%A9=2&%C3%A9=3&a=4&z=1"),
        (
            "z=1&a/b=literal&a%2fb=escaped&a+b=plus&a%20b=space&a%2bb=encoded-plus",
            "a%20b=space&a%2Bb=encoded-plus&a%2Fb=escaped&a+b=plus&a/b=literal&z=1",
        ),
        (
            "z=1&x=%E9&x=%25ZZ&x=a%26b%3Dc&x=https://other.example/a?b=c",
            "x=%E9&x=%25ZZ&x=a%26b%3Dc&x=https://other.example/a?b%3Dc&z=1",
        ),
        ("z=1&%FF=bad&%25=percent&a=1", "%25=percent&%FF=bad&a=1&z=1"),
    ],
)
def test_query_sorting_uses_normalized_keys(query, expected):
    """Sort exact normalized keys without sorting values or re-encoding fields."""
    # Adapt the permutation/duplicate ideas, with our key and separator policy:
    # https://github.com/sindresorhus/normalize-url/blob/v10.0.0/test.js
    # https://github.com/scrapy/w3lib/blob/v2.5.0/tests/test_url.py
    value = f"https://example.com/search?{query}"
    result = url_normalize(value, sort_query=True)
    assert result == f"https://example.com/search?{expected}"
    assert url_normalize(result, sort_query=True) == result


def test_query_sorting_converges_permutations_without_reordering_values():
    """Build a common cache key while preserving a parser's repeated-value list."""
    first = "https://example.com/search?tag=red&page=2&tag=blue"
    second = "https://example.com/search?page=2&tag=red&tag=blue"
    assert url_normalize(first) != url_normalize(second)
    result = url_normalize(first, sort_query=True)
    assert result == url_normalize(second, sort_query=True) == second
    assert parse_qs(urlsplit(result).query)["tag"] == ["red", "blue"]
    # Reversing values remains a distinct URL, even when keys are sorted.
    reversed_values = "https://example.com/search?page=2&tag=blue&tag=red"
    assert url_normalize(reversed_values, sort_query=True) != result


@pytest.mark.parametrize("api", [url_normalize, url_humanize])
def test_query_sorting_composes_with_all_filter_rules(api):
    """Sort retained fields after custom and built-in removals."""
    assert (
        api(
            "https://example.com/search?z=1&utm_source=email&a=3&drop=2&a=1&extra=4",
            sort_query=True,
            param_allowlist=["z", "a", "drop", "utm_source"],
            param_denylist="drop",
            remove_tracking_params=True,
        )
        == "https://example.com/search?a=3&a=1&z=1"
    )


def test_query_sorting_composes_with_builtin_allowlist():
    """Order the existing domain rule's retained names without adding filters."""
    assert (
        url_normalize(
            "https://google.com/search?q=python&ie=UTF-8&utm_source=email",
            filter_params=True,
            sort_query=True,
        )
        == "https://google.com/search?ie=UTF-8&q=python"
    )


@pytest.mark.parametrize(
    ("value", "options", "expected"),
    [
        (None, {}, None),
        ("", {}, ""),
        ("https://example.com/?#", {}, "https://example.com/"),
        (
            "https://example.com/?#",
            {"keep_empty_components": True},
            "https://example.com/?#",
        ),
        (
            "https://example.com/?utm_source=email#",
            {"remove_tracking_params": True},
            "https://example.com/",
        ),
        (
            "https://example.com/?utm_source=email#",
            {"remove_tracking_params": True, "keep_empty_components": True},
            "https://example.com/?#",
        ),
    ],
)
def test_query_sorting_preserves_empty_input_and_component_policies(
    value, options, expected
):
    """Sorting cannot create query content or remove a requested empty delimiter."""
    assert url_normalize(value, sort_query=True, **options) == expected
    assert url_humanize(value, sort_query=True, **options) == expected


@pytest.mark.parametrize(
    ("api", "expected"),
    [
        (url_normalize, "../a//b?%C3%A9=caf%C3%A9&a=2&z=1#"),  # codespell:ignore caf
        (url_humanize, "../a//b?é=café&a=2&z=1#"),
    ],
)
def test_query_sorting_humanizes_using_normalized_key_order(api, expected):
    """Keep path and display options while sorting by encoded normalized names."""
    value = "../a//b?z=1&é=café&a=2#"
    options = {
        "sort_query": True,
        "collapse_slashes": False,
        "keep_empty_components": True,
    }
    result = api(value, **options)
    assert result == expected
    assert api(result, **options) == result
    assert url_normalize(result, **options) == url_normalize(value, **options)


@pytest.mark.parametrize("prefix", ["?", "custom://example.com/path?"])
def test_query_sorting_leaves_fragment_routes_untouched(prefix):
    """Apply query sorting to references and custom schemes, not fragment data."""
    value = f"{prefix}z=1&a=2#/route?z=3&a=4"
    assert url_normalize(value, sort_query=True) == (f"{prefix}a=2&z=1#/route?z=3&a=4")
