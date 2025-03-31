"""Tests for normalize_query function."""

import pytest

from url_normalize.url_normalize import normalize_query


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("", ""),
        ("&&&", ""),
        ("param1=val1&param2=val2", "param1=val1&param2=val2"),
        ("Ç=Ç", "%C3%87=%C3%87"),
        ("%C3%87=%C3%87", "%C3%87=%C3%87"),
        ("q=C%CC%A7", "q=%C3%87"),
        ("q=%23test", "q=%23test"),  # Preserve encoded # in value, #31
        ("where=code%3D123", "where=code%3D123"),  # Preserve encoded = in value, #25
    ],
)
def test_normalize_query_result_is_expected(query, expected):
    """Assert we got expected results from the normalize_query function."""
    result = normalize_query(query)
    assert result == expected, query
