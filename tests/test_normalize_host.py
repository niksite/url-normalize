"""Tests for normalize_host function."""

from url_normalize.url_normalize import normalize_host

EXPECTED_DATA = {
    "site.com": "site.com",
    "SITE.COM": "site.com",
    "site.com.": "site.com",
    "пример.испытание": "xn--e1afmkfd.xn--80akhbyknj4f",
}


def test_normalize_host_result_is_expected():
    """Assert we got expected results from the normalize_host function."""
    for url, expected in EXPECTED_DATA.items():
        result = normalize_host(url)

        assert result == expected, url
