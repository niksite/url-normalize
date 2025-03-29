"""Tests for provide_url_scheme function."""

from url_normalize.url_normalize import provide_url_scheme

EXPECTED_DATA = {
    "": "",
    "-": "-",
    "/file/path": "/file/path",
    "//site/path": "https://site/path",
    "ftp://site/": "ftp://site/",
    "site/page": "https://site/page",
}


def test_provide_url_scheme_result_is_expected():
    """Assert we got expected results from the provide_url_scheme function."""
    for url, expected in EXPECTED_DATA.items():
        result = provide_url_scheme(url)

        assert result == expected, url


def test_provide_url_scheme_accept_default_scheme_param():
    """Assert we could provide default_scheme param other than https."""
    url = "//site/path"
    expected = "http://site/path"

    actual = provide_url_scheme(url, default_scheme="http")

    assert actual == expected
