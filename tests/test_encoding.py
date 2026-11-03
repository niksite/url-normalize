"""Encoding helper tests."""

from __future__ import annotations

from url_normalize._encoding import force_unicode


def test_force_unicode_with_bytes() -> None:
    """Test force_unicode handles bytes input correctly."""
    test_bytes = b"hello world"
    result = force_unicode(test_bytes)
    assert result == "hello world"
