"""Deconstruct url tests."""

import pytest

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
