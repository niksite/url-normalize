"""Tests for generic_url_cleanup function."""

from __future__ import annotations

import pytest

from url_normalize.url_normalize import generic_url_cleanup


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("//site/#!fragment", "//site/?_escaped_fragment_=fragment"),
        ("//site/page", "//site/page"),
        ("//site/?& ", "//site/"),
    ],
)
def test_generic_url_cleanup_result_is_expected(url: str, expected: str) -> None:
    """Assert we got expected results from the generic_url_cleanup function."""
    result = generic_url_cleanup(url)
    assert result == expected
