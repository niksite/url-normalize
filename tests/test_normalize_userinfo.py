"""Tests for normalize_userinfo function."""

from url_normalize.url_normalize import normalize_userinfo

EXPECTED_DATA = {
    ":@": "",
    "": "",
    "@": "",
    "user:password@": "user:password@",
    "user@": "user@",
}


def test_normalize_userinfo_result_is_expected():
    """Assert we got expected results from the normalize_userinfo function."""
    for url, expected in EXPECTED_DATA.items():
        result = normalize_userinfo(url)

        assert result == expected, url
