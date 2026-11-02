"""Tests for normalize_query function."""

from urllib.parse import parse_qsl

import pytest

from url_normalize.normalize_query import normalize_query


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
        query, param_allowlist=["flag", ""] if filter_params else None
    )
    assert actual == query
    if query == "flag=":
        assert parse_qsl(actual, keep_blank_values=True, strict_parsing=True) == [
            ("flag", "")
        ]


@pytest.mark.parametrize(
    "escape",
    [
        "%3a",
        "%2f",
        "%3f",
        "%23",
        "%5b",
        "%5d",
        "%40",
        "%21",
        "%24",
        "%26",
        "%27",
        "%28",
        "%29",
        "%2a",
        "%2b",
        "%2c",
        "%3b",
        "%3d",
    ],
)
def test_normalize_query_preserves_reserved_escapes(escape):
    """Keep all RFC 3986 reserved escapes in keys and values, with uppercase hex."""
    query = f"a{escape}b=c{escape}d"
    expected = f"a{escape.upper()}b=c{escape.upper()}d"
    assert normalize_query(query) == expected


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("q=:/?[]@!$'()*+,;", "q=:/?[]@!$'()*+,;"),
        ("%71=%41%7a%30%2d%2e%5f%7e", "q=Az0-._~"),
        ("q=%252F&bad=%ff%2f%zz", "q=%252F&bad=%FF%2F%25zz"),
        # Nested URL idea from w3lib 2.5.0:
        # test_safe_url_string_preserve_nonfragment_hash
        # https://github.com/scrapy/w3lib/blob/v2.5.0/tests/test_url.py
        (
            "url=http%3a%2f%2fother.example%2fa%3fx%3d1%26y%3d2",
            "url=http%3A%2F%2Fother.example%2Fa%3Fx%3D1%26y%3D2",
        ),
    ],
)
def test_normalize_query_escape_boundaries(query, expected):
    """Retain literal punctuation and nested URLs while decoding unreserved text."""
    assert normalize_query(query) == expected


def test_normalize_query_preserves_semicolon_parameter_structure():
    """Do not expose a separator used by applications with semicolon queries."""
    encoded = normalize_query("q=a%3bb")
    literal = normalize_query("q=a;b")
    assert parse_qsl(encoded, separator=";", keep_blank_values=True) == [("q", "a;b")]
    assert parse_qsl(literal, separator=";", keep_blank_values=True) == [
        ("q", "a"),
        ("b", ""),
    ]
