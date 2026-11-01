"""Tests for normalize_fragment function."""

import pytest

from url_normalize.normalize_fragment import normalize_fragment


@pytest.mark.parametrize(
    ("fragment", "expected"),
    [
        ("", ""),
        ("fragment", "fragment"),
        ("пример", "%D0%BF%D1%80%D0%B8%D0%BC%D0%B5%D1%80"),
        ("!fragment", "!fragment"),
        ("~fragment", "~fragment"),
        # Issue #36: Equal sign should not be encoded
        ("gid=1234", "gid=1234"),
        ("/route?x=1&x=2", "/route?x=1&x=2"),
        (":~:text=prefix-,start,end,-suffix", ":~:text=prefix-,start,end,-suffix"),
        ("AZaz09-._~!$&'()*+,;=:@/?", "AZaz09-._~!$&'()*+,;=:@/?"),
        ('#[]<>`{}|\\"', "%23%5B%5D%3C%3E%60%7B%7D%7C%5C%22"),
        ("a b", "a%20b"),
        ("e\u0301", "%C3%A9"),
        ("e%cc%81", "%C3%A9"),
        ("%c3%a9", "%C3%A9"),
        ("%e9%ff", "%E9%FF"),
        ("%E0%A4%A", "%E0%A4%25A"),
        ("%zz%%41%2%45", "%25zz%25%41%252%45"),
    ],
)
def test_normalize_fragment_result_is_expected(fragment: str, expected: str) -> None:
    """Assert we got expected results from the normalize_fragment function."""
    result = normalize_fragment(fragment)
    assert result == expected, fragment
