"""Tests for normalize_query function."""

from urllib.parse import parse_qsl

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


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("q=C%2b%2B", "q=C%2B%2B"),
        ("C%2b%2B=value", "C%2B%2B=value"),
        ("q=C++", "q=C++"),
        ("q=C%20%2B+", "q=C%20%2B+"),
        ("q=%252B", "q=%252B"),
    ],
)
def test_normalize_query_preserves_form_plus_meaning(query, expected):
    """Distinguish encoded plus signs, literal plus signs, and spaces."""
    actual = normalize_query(query)
    assert actual == expected
    assert parse_qsl(actual) == parse_qsl(query)


@pytest.mark.parametrize("query", ["flag=&flag", "=", "=value", "flag=", "flag"])
@pytest.mark.parametrize("filter_params", [False, True])
def test_normalize_query_preserves_empty_value_separator(query, filter_params):
    """Keep explicit empty values distinct from parameters without a value."""
    actual = normalize_query(
        query, filter_params=filter_params, param_allowlist=["flag", ""]
    )
    assert actual == query
    if query == "flag=":
        assert parse_qsl(actual, keep_blank_values=True, strict_parsing=True) == [
            ("flag", "")
        ]
