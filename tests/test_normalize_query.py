# -*- coding: utf-8 -*-
"""Tests for normalize_query function."""

from url_normalize.url_normalize import normalize_query

EXPECTED_DATA = {
    "": "",
    "param1=val1&param2=val2": "param1=val1&param2=val2",
    "Ç=Ç": "%C3%87=%C3%87",
    "%C3%87=%C3%87": "%C3%87=%C3%87",
    "q=C%CC%A7": "q=%C3%87",
}


def test_normalize_query_result_is_expected():  # type: () -> None
    """Assert we got expected results from the normalize_query function."""
    for url, expected in EXPECTED_DATA.items():

        result = normalize_query(url)

        assert result == expected, url
