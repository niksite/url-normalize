"""Tests for generic_url_cleanup function."""

from __future__ import annotations

from typing import Final

from url_normalize.url_normalize import generic_url_cleanup

EXPECTED_DATA: Final[dict[str, str]] = {
    "//site/#!fragment": "//site/?_escaped_fragment_=fragment",
    "//site/?utm_source=some source&param=value": "//site/?param=value",
    "//site/?utm_source=some source": "//site/",
    "//site/?param=value&utm_source=some source": "//site/?param=value",
    "//site/page": "//site/page",
    "//site/?& ": "//site/",
}


def test_generic_url_cleanup_result_is_expected() -> None:
    """Assert we got expected results from the generic_url_cleanup function."""
    for url, expected in EXPECTED_DATA.items():
        result = generic_url_cleanup(url)
        assert result == expected, url
