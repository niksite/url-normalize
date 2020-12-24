"""Tests for generic_url_cleanup function."""
from url_normalize.url_normalize import generic_url_cleanup

EXPECTED_DATA = {
    "//site/#!fragment": "//site/?_escaped_fragment_=fragment",
    "//site/?utm_source=some source&param=value": "//site/?param=value",
    "//site/?utm_source=some source": "//site/",
    "//site/?param=value&utm_source=some source": "//site/?param=value",
    "//site/page": "//site/page",
    "//site/?& ": "//site/",
}


def test_generic_url_cleanup_result_is_expected():  # type: () -> None
    """Assert we got expected results from the generic_url_cleanup function."""
    for url, expected in EXPECTED_DATA.items():

        result = generic_url_cleanup(url)

        assert result == expected, url
