"""Reconstruct url tests."""
from url_normalize.tools import reconstruct_url, URL

EXPECTED_DATA = (
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
)


def test_deconstruct_url_result_is_expected():  # type: () -> None
    """Assert we got expected results from the deconstruct_url function."""
    for url, expected in EXPECTED_DATA:

        result = reconstruct_url(url)

        assert result == expected, url
