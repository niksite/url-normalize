"""Tests for normalize_userinfo function."""

import pytest

from url_normalize.url_normalize import normalize_userinfo


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
