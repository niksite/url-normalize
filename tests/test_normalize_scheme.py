"""Tests for normalize_scheme function."""

from url_normalize.url_normalize import normalize_scheme

EXPECTED_DATA = {"http": "http", "HTTP": "http"}


def test_normalize_scheme_result_is_expected():
    """Assert we got expected results from the normalize_scheme function."""
    for url, expected in EXPECTED_DATA.items():
        result = normalize_scheme(url)

        assert result == expected, url
