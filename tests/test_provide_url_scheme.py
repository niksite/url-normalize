"""Tests for provide_url_scheme function."""

import pytest

from url_normalize.url_normalize import provide_url_scheme, url_normalize


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


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("git+ssh://example.com/repo", "git+ssh://example.com/repo"),
        ("postgresql://example.com/db", "postgresql://example.com/db"),
        ("custom-long.scheme:opaque", "custom-long.scheme:opaque"),
        ("TEL:123", "TEL:123"),
        ("custom:123", "custom:123"),
        ("//x:443/", "https://x:443/"),
        ("//[::1]:443/", "https://[::1]:443/"),
        ("x.co:8080/path", "https://x.co:8080/path"),
        ("example.com:8080/path", "https://example.com:8080/path"),
        ("localhost:8080/path", "https://localhost:8080/path"),
        ("127.0.0.1:8080/", "https://127.0.0.1:8080/"),
        ("[::1]:8080/", "https://[::1]:8080/"),
        ("site/path:part", "https://site/path:part"),
        ("1abc:thing", "https://1abc:thing"),
        ("http:example.com", "http://example.com"),
    ],
)
def test_provide_url_scheme_distinguishes_schemes_and_authorities(url, expected):
    """Recognize schemes of any length without confusing host ports or paths."""
    assert provide_url_scheme(url) == expected


@pytest.mark.parametrize("prefix", [" ", "\t", "\r\n", "\u00a0", "  \t\n"])
@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://example.com/path ", "http://example.com/path "),
        ("https://example.com/?q=x ", "https://example.com/?q=x "),
        ("//x:443/path ", "https://x:443/path "),
        ("example.com/path ", "https://example.com/path "),
        ("git+ssh://example.com/repo ", "git+ssh://example.com/repo "),
        ("mailto:person@example.com", "mailto:person@example.com"),
        ("/path ", "/path "),
        ("-", "-"),
        ("", ""),
    ],
)
def test_provide_url_scheme_ignores_only_leading_whitespace(prefix, url, expected):
    """Remove leading whitespace before classifying the URL."""
    assert provide_url_scheme(prefix + url) == expected


@pytest.mark.parametrize("host", ["example.com", "localhost", "127.0.0.1"])
@pytest.mark.parametrize("whitespace", [" ", "\u00a0", " \t\r\n"])
@pytest.mark.parametrize("suffix", ["", "/path ", "?q=x ", "#part "])
def test_provide_url_scheme_accepts_whitespace_after_bare_port(
    host, whitespace, suffix
):
    """Recognize a bare authority with padding after its numeric port."""
    value = f"{host}:443{whitespace}{suffix}"
    assert provide_url_scheme(value) == f"https://{value}"
    path_suffix = suffix if suffix.startswith("/") else "/" + suffix
    expected = f"https://{host}{path_suffix.replace(' ', '%20')}"
    assert url_normalize(value) == expected
    assert url_normalize(expected) == expected
