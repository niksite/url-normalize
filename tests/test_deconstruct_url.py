"""Deconstruct url tests."""

from __future__ import annotations

from typing import Final

from url_normalize.tools import URL, deconstruct_url

EXPECTED_DATA: Final[dict[str, URL]] = {
    "http://site.com": URL(
        fragment="",
        host="site.com",
        path="",
        port="",
        query="",
        scheme="http",
        userinfo="",
    ),
    "http://user@www.example.com:8080/path/index.html?param=val#fragment": URL(
        fragment="fragment",
        host="www.example.com",
        path="/path/index.html",
        port="8080",
        query="param=val",
        scheme="http",
        userinfo="user@",
    ),
}


def test_deconstruct_url_result_is_expected() -> None:
    """Assert we got expected results from the deconstruct_url function."""
    for url, expected in EXPECTED_DATA.items():
        result = deconstruct_url(url)
        assert result == expected, url
