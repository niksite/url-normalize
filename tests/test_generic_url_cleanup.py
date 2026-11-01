"""Tests for generic_url_cleanup function."""

from __future__ import annotations

from urllib.parse import urlsplit

import pytest

from url_normalize import url_normalize
from url_normalize.generic_url_cleanup import generic_url_cleanup


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("//site/#!fragment", "//site/#!fragment"),
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
        ("/#part&", "/#part&"),
        ("/#part?", "/#part?"),
        ("/#part ", "/#part%20"),
    ],
)
def test_generic_url_cleanup_preserves_component_data(suffix, normalized_suffix):
    """Preserve trailing punctuation and whitespace belonging to components."""
    url = f"https://example.com{suffix}"
    assert generic_url_cleanup(url) == url
    assert url_normalize(url) == f"https://example.com{normalized_suffix}"


@pytest.mark.parametrize(
    ("query", "cleaned_query"),
    [("", ""), ("?q=x", "q=x"), ("?q=x&", "q=x"), ("?q=why?", "q=why?")],
)
@pytest.mark.parametrize(
    "fragment",
    [
        "!/route",
        "!/route&a=b",
        "!/C++%2B%26%23",
        "!",
        "!a#!b",
        "part#!nested",
        "ordinary",
    ],
)
def test_generic_url_cleanup_leaves_fragments_in_place(query, cleaned_query, fragment):
    """Clean query fields without interpreting or moving fragment content."""
    url = f"https://example.com/{query}#{fragment}"
    parts = urlsplit(generic_url_cleanup(url))
    assert parts.query == cleaned_query
    assert parts.fragment == fragment
