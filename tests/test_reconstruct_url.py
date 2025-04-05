"""Reconstruct url tests."""

from __future__ import annotations

import pytest

from url_normalize.tools import URL, reconstruct_url


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
