"""Tests for generic_url_cleanup function."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlsplit

import pytest

from url_normalize.url_normalize import generic_url_cleanup, url_normalize


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("//site/#!fragment", "//site/?_escaped_fragment_=fragment"),
        ("//site/page", "//site/page"),
        ("//site/?&&", "//site/"),
        ("//site/?& ", "//site/? "),
    ],
)
def test_generic_url_cleanup_result_is_expected(url: str, expected: str) -> None:
    """Assert we got expected results from the generic_url_cleanup function."""
    result = generic_url_cleanup(url)
    assert result == expected


@pytest.mark.parametrize(
    ("suffix", "normalized_suffix"),
    [
        ("/a&", "/a&"),
        ("/a ", "/a%20"),
        ("/?q=why?", "/?q=why?"),
        ("/?q=x ", "/?q=x%20"),
        ("/#part&", "/#part%26"),
        ("/#part?", "/#part%3F"),
        ("/#part ", "/#part%20"),
    ],
)
def test_generic_url_cleanup_preserves_component_data(suffix, normalized_suffix):
    """Preserve trailing punctuation and whitespace belonging to components."""
    url = f"https://example.com{suffix}"
    assert generic_url_cleanup(url) == url
    assert url_normalize(url) == f"https://example.com{normalized_suffix}"


@pytest.mark.parametrize("query", ["", "?q=x", "?q=x&", "?q=why?"])
@pytest.mark.parametrize(
    ("fragment", "payload"),
    [
        ("!/route", "/route"),
        ("!/route&a=b", "/route&a=b"),
        ("!/C++%2B%26%23", "/C+++&#"),
        ("!", ""),
        ("!a#!b", "a#!b"),
        ("part#!nested", None),
        ("ordinary", None),
    ],
)
def test_generic_url_cleanup_encodes_hashbang_as_one_parameter(
    query, fragment, payload
):
    """Append the decoded hashbang payload as one value after existing parameters."""
    url = f"https://example.com/{query}#{fragment}"
    if payload is None:
        assert urlsplit(generic_url_cleanup(url)).fragment == fragment
        return
    expected = parse_qsl(query.removeprefix("?"), keep_blank_values=True)
    expected.append(("_escaped_fragment_", payload))
    for result in (generic_url_cleanup(url), url_normalize(url)):
        parts = urlsplit(result)
        assert parts.fragment == ""
        assert parse_qsl(parts.query, keep_blank_values=True) == expected
