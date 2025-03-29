"""Tests for normalize_port function."""

from url_normalize.url_normalize import normalize_port

EXPECTED_DATA = {"8080": "8080", "": "", "80": "", "string": "string"}


def test_normalize_port_result_is_expected():
    """Assert we got expected results from the normalize_port function."""
    for url, expected in EXPECTED_DATA.items():
        result = normalize_port(url, "http")

        assert result == expected, url
