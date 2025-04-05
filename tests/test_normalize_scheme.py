"""Tests for normalize_scheme function."""

import pytest

from url_normalize.url_normalize import normalize_scheme


@pytest.mark.parametrize(
    ("scheme", "expected"),
    [
        ("http", "http"),
        ("HTTP", "http"),
    ],
)
def test_normalize_scheme_result_is_expected(scheme: str, expected: str) -> None:
    """Assert we got expected results from the normalize_scheme function."""
    result = normalize_scheme(scheme)
    assert result == expected, scheme
