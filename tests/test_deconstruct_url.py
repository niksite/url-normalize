"""Deconstruct url tests."""

import pytest

from url_normalize import url_normalize
from url_normalize.tools import URL, deconstruct_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "http://site.com",
            URL(
                fragment="",
                host="site.com",
                path="",
                port="",
                query="",
                scheme="http",
                userinfo="",
            ),
        ),
        (
            "http://user@www.example.com:8080/path/index.html?param=val#fragment",
            URL(
                fragment="fragment",
                host="www.example.com",
                path="/path/index.html",
                port="8080",
                query="param=val",
                scheme="http",
                userinfo="user@",
            ),
        ),
    ],
)
def test_deconstruct_url_result_is_expected(url: str, expected: URL) -> None:
    """Assert we got expected results from the deconstruct_url function."""
    result = deconstruct_url(url)
    assert result == expected, url


@pytest.mark.parametrize(
    ("authority", "userinfo", "host", "port", "normalized_authority"),
    [
        ("[2001:DB8::1]:080", "", "[2001:DB8::1]", "080", "[2001:db8::1]"),
        ("[2001:DB8::1]:0081", "", "[2001:DB8::1]", "0081", "[2001:db8::1]:81"),
        ("[::1]", "", "[::1]", "", "[::1]"),
        ("[::1]:", "", "[::1]", "", "[::1]"),
        ("user:pass@[::1]:080", "user:pass@", "[::1]", "080", "user:pass@[::1]"),
        ("EXAMPLE.com:080", "", "EXAMPLE.com", "080", "example.com"),
        ("127.0.0.1:0081", "", "127.0.0.1", "0081", "127.0.0.1:81"),
    ],
)
def test_deconstruct_url_separates_bracketed_host_and_port(
    authority, userinfo, host, port, normalized_authority
):
    """Parse the entire bracketed host before considering a port separator."""
    url = f"http://{authority}/path?q=1#fragment"
    assert deconstruct_url(url) == URL(
        "http", userinfo, host, port, "/path", "q=1", "fragment"
    )
    assert url_normalize(url) == f"http://{normalized_authority}/path?q=1#fragment"


@pytest.mark.parametrize("whitespace", [" ", "\u00a0", " \t\r\n"])
@pytest.mark.parametrize("suffix", ["", "/path ", "?q=x ", "#part "])
@pytest.mark.parametrize(
    ("authority", "normalized"),
    [
        ("EXAMPLE.com", "example.com"),
        ("example.com:443", "example.com"),
        ("user:pass@example.com:443", "user:pass@example.com"),
        ("[FE80::1%25ethA]:443", "[fe80::1%25ethA]"),
    ],
)
def test_deconstruct_url_trims_authority_whitespace_only(
    authority, normalized, whitespace, suffix
):
    """Trim the authority without deleting whitespace from other components."""
    value = f"https://{authority}{whitespace}{suffix}"
    assert deconstruct_url(value) == deconstruct_url(f"https://{authority}{suffix}")
    path_suffix = suffix if suffix.startswith("/") else "/" + suffix
    assert (
        url_normalize(value) == f"https://{normalized}{path_suffix.replace(' ', '%20')}"
    )
