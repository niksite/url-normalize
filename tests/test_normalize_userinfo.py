"""Tests for normalize_userinfo function."""

import pytest

from url_normalize.url_normalize import normalize_userinfo, url_normalize


@pytest.mark.parametrize(
    ("userinfo", "expected"),
    [
        (":@", ""),
        ("", ""),
        ("@", ""),
        ("user:password@", "user:password@"),
        ("user@", "user@"),
    ],
)
def test_normalize_userinfo_result_is_expected(userinfo: str, expected: str) -> None:
    """Assert we got expected results from the normalize_userinfo function."""
    result = normalize_userinfo(userinfo)
    assert result == expected, userinfo


@pytest.mark.parametrize(
    ("userinfo", "expected"),
    [
        ("us er:pa ss@", "us%20er:pa%20ss@"),
        ("e\u0301:пароль@", "%C3%A9:%D0%BF%D0%B0%D1%80%D0%BE%D0%BB%D1%8C@"),
        ("user:name:!$&'()*+,;=@", "user:name:!$&'()*+,;=@"),
        ("user%3aname:p%40ss@", "user%3Aname:p%40ss@"),
        ("us%65r:%ff@", "user:%FF@"),
        ("user:50%@", "user:50%25@"),
        ("user:p@ss@", "user:p%40ss@"),
        ('user:p"<>\\@', "user:p%22%3C%3E%5C@"),
    ],
)
def test_normalize_userinfo_encodes_component_data(userinfo, expected):
    """Encode unsafe data while preserving userinfo delimiters and escaped octets."""
    assert normalize_userinfo(userinfo) == expected
    assert (
        url_normalize(f"http://{userinfo}example.com/")
        == f"http://{expected}example.com/"
    )
    assert normalize_userinfo(expected) == expected
