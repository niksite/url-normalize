"""Reconstruct url tests."""

from __future__ import annotations

import pytest

from url_normalize._url import URL, deconstruct_url, reconstruct_url


@pytest.mark.parametrize(
    ("url_obj", "expected"),
    [
        (
            URL(
                fragment="",
                host="site.com",
                path="",
                port="",
                query="",
                scheme="http",
                userinfo="",
            ),
            "http://site.com",
        ),
        (
            URL(
                fragment="fragment",
                host="www.example.com",
                path="/path/index.html",
                port="8080",
                query="param=val",
                scheme="http",
                userinfo="user@",
            ),
            "http://user@www.example.com:8080/path/index.html?param=val#fragment",
        ),
    ],
)
def test_reconstruct_url_result_is_expected(url_obj: URL, expected: str) -> None:
    """Assert we got expected results from the reconstruct_url function."""
    result = reconstruct_url(url_obj)
    assert result == expected, url_obj


@pytest.mark.parametrize(
    ("query_present", "fragment_present", "suffix"),
    [(False, False, ""), (True, False, "?"), (False, True, "#"), (True, True, "?#")],
)
@pytest.mark.parametrize(
    ("parts", "base"),
    [
        (
            URL("https", "user@", "example.com", "8080", "/p", "", ""),
            "https://user@example.com:8080/p",
        ),
        (
            URL("mailto", "", "", "", "user@example.com", "", ""),
            "mailto:user@example.com",
        ),
        (URL("", "", "", "", "/path", "", ""), "/path"),
        (URL("", "", "", "", "", "", ""), ""),
    ],
)
def test_reconstruct_url_preserves_empty_components(
    parts, base, query_present, fragment_present, suffix
):
    """Serialize present-empty query and fragment components in the right order."""
    parts = parts._replace(
        query_present=query_present, fragment_present=fragment_present
    )

    assert reconstruct_url(parts) == base + suffix


def test_schemeless_empty_authority():
    """Preserve the authority delimiter when reconstructing a network reference."""
    assert reconstruct_url(deconstruct_url("///foo")) == "///foo"
