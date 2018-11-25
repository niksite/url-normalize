"""Deconstruct url tests."""
from url_normalize.tools import deconstruct_url, URL

EXPECTED_DATA = {
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


def test_deconstruct_url_result_is_expected():
    """Assert we got expected results from the deconstruct_url function."""
    for url, expected in EXPECTED_DATA.items():

        result = deconstruct_url(url)

        assert result == expected, url
