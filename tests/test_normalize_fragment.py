"""Tests for normalize_fragment function."""

import pytest

from url_normalize.url_normalize import normalize_fragment


@pytest.mark.parametrize(
    ("fragment", "expected"),
    [
        ("", ""),
        ("fragment", "fragment"),
        ("пример", "%D0%BF%D1%80%D0%B8%D0%BC%D0%B5%D1%80"),
        ("!fragment", "%21fragment"),
        ("~fragment", "~fragment"),
        # Issue #36: Equal sign should not be encoded
        ("gid=1234", "gid=1234"),
    ],
)
def test_normalize_fragment_result_is_expected(fragment: str, expected: str) -> None:
    """Assert we got expected results from the normalize_fragment function."""
    result = normalize_fragment(fragment)
    assert result == expected, fragment
