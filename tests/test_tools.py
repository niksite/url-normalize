"""Tools module tests."""

from __future__ import annotations

from url_normalize.tools import force_unicode


def test_force_unicode_with_bytes() -> None:
    """Test force_unicode handles bytes input correctly."""
    test_bytes = b"hello world"
    result = force_unicode(test_bytes)
    assert result == "hello world"
