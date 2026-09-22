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
    cleaned = value.replace("\t", "").replace("\r", "").replace("\n", "")
    assert provide_url_scheme(value) == f"https://{cleaned}"
    path_suffix = suffix if suffix.startswith("/") else "/" + suffix
    expected = f"https://{host}{path_suffix.replace(' ', '%20')}"
    assert url_normalize(value) == expected
    assert url_normalize(expected) == expected


@pytest.mark.parametrize("control", ["\t", "\r", "\n"])
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("ht{control}tps://example.com/path", "https://example.com/path"),
        ("https{control}://example.com/path", "https://example.com/path"),
        ("git+{control}ssh://example.com/repo", "git+ssh://example.com/repo"),
        ("mail{control}to:person@example.com", "mailto:person@example.com"),
        ("/{control}/example.com/path", "https://example.com/path"),
    ],
)
def test_scheme_detection_ignores_parser_control_characters(control, value, expected):
    """Keep the destination when urlsplit would discard tabs or line breaks."""
    value = value.format(control=control)
    assert provide_url_scheme(value) == expected
    assert url_normalize(value, default_domain="default.example") == expected


@pytest.mark.parametrize("prefix", ["\x00", "\x1f", "\x00\u00a0\x01 "])
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("http://example.com/path", "http://example.com/path"),
        ("//example.com/path", "https://example.com/path"),
        ("/path", "/path"),
        ("-", "-"),
        ("", ""),
    ],
)
def test_url_classification_ignores_leading_controls(prefix, value, expected):
    """Remove leading controls before applying either default domain or scheme."""
    assert provide_url_scheme(prefix + value) == expected
    assert url_normalize(prefix + value) == expected
    with_domain = "https://default.example/path" if value == "/path" else expected
    assert (
        url_normalize(prefix + value, default_domain="default.example") == with_domain
    )


def test_scheme_cleanup_preserves_encoded_controls_and_trailing_spaces():
    """Remove only raw parser controls, keeping escaped bytes and component data."""
    value = "ht\ntps://example.com/a%09b ?q=%0A%0D #part%00 "
    assert url_normalize(value) == (
        "https://example.com/a%09b%20?q=%0A%0D%20#part%00%20"
    )
