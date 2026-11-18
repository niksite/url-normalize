"""Deconstruct url tests."""

import pytest

from url_normalize import url_normalize
from url_normalize._url import URL, deconstruct_url


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
                authority_present=True,
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
                authority_present=True,
                query_present=True,
                fragment_present=True,
            ),
        ),
    ],
)
def test_deconstruct_url_result_is_expected(url: str, expected: URL) -> None:
    """Assert we got expected results from the deconstruct_url function."""
    result = deconstruct_url(url)
    assert result == expected, url


@pytest.mark.parametrize(
    ("suffix", "query", "fragment", "query_present", "fragment_present"),
    [
        ("", "", "", False, False),
        ("?", "", "", True, False),
        ("#", "", "", False, True),
        ("?#", "", "", True, True),
        ("?q=1", "q=1", "", True, False),
        ("?q=1#", "q=1", "", True, True),
        ("?#end", "", "end", True, True),
        ("#?", "", "?", False, True),
        ("#x?y", "", "x?y", False, True),
        ("?q=%23", "q=%23", "", True, False),
        ("?q=why?#", "q=why?", "", True, True),
        ("#%3F", "", "%3F", False, True),
        ("%3F%23", "", "", False, False),
    ],
)
def test_deconstruct_url_tracks_component_presence(
    suffix, query, fragment, query_present, fragment_present
):
    """Distinguish absent components from empty ones at the actual URL boundaries."""
    parts = deconstruct_url(f"https://example.com/{suffix}")

    assert parts.query == query
    assert parts.fragment == fragment
    assert parts.query_present is query_present
    assert parts.fragment_present is fragment_present


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
        "http",
        userinfo,
        host,
        port,
        "/path",
        "q=1",
        "fragment",
        query_present=True,
        fragment_present=True,
        authority_present=True,
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
