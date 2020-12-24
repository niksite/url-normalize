# -*- coding: utf-8 -*-
"""Tests for normalize_fragment function."""
from url_normalize.url_normalize import normalize_fragment

EXPECTED_DATA = {
    "": "",
    "fragment": "fragment",
    "пример": "%D0%BF%D1%80%D0%B8%D0%BC%D0%B5%D1%80",
    "!fragment": "%21fragment",
    "~fragment": "~fragment",
}


def test_normalize_fragment_result_is_expected():  # type: () -> None
    """Assert we got expected results from the normalize_fragment function."""
    for url, expected in EXPECTED_DATA.items():

        result = normalize_fragment(url)

        assert result == expected, url
