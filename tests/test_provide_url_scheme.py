"""Tests for provide_url_scheme function."""

import pytest

from url_normalize.url_normalize import provide_url_scheme


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("", ""),
        ("-", "-"),
        ("/file/path", "/file/path"),
        ("//site/path", "https://site/path"),
        ("ftp://site/", "ftp://site/"),
        ("site/page", "https://site/page"),
    ],
)
def test_provide_url_scheme_result_is_expected(url: str, expected: str) -> None:
    """Assert we got expected results from the provide_url_scheme function."""
    result = provide_url_scheme(url)
    assert result == expected, url


def test_provide_url_scheme_accept_default_scheme_param() -> None:
    """Assert we could provide default_scheme param other than https."""
    url = "//site/path"
    expected = "http://site/path"

    actual = provide_url_scheme(url, default_scheme="http")

    assert actual == expected
