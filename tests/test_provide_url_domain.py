"""Tests for provide_url_domain function."""

import pytest

from url_normalize.provide_url_domain import provide_url_domain


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("", ""),
        ("-", "-"),
        ("http://example.com/", "http://example.com/"),
        ("/file/path", "//example.com/file/path"),
        ("site/page", "site/page"),  # No change for relative paths
    ],
)
def test_provide_url_domain_result_is_expected(url: str, expected: str) -> None:
    """Assert we get expected results from provide_url_domain function."""
    result = provide_url_domain(url, default_domain="example.com")
    assert result == expected


def test_provide_url_domain_accept_different_domains():
    """Assert we could provide different default_domain values."""
    url = "/file/path"
    expected = "//custom-domain.org/file/path"

    actual = provide_url_domain(url, default_domain="custom-domain.org")

    assert actual == expected
