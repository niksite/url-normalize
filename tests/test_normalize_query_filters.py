"""URL parameter filtering test module."""

from __future__ import annotations

import pytest

from url_normalize import url_normalize


def test_param_filtering_disabled_by_default():
    """Test that parameter filtering is disabled by default."""
    url = "https://www.google.com/search?q=test&utm_source=test"
    assert url_normalize(url) == url


def test_empty_query():
    """Test handling empty query strings."""
    assert url_normalize("https://example.com/page?") == "https://example.com/page"


def test_custom_allowlist():
    """Test custom allowlist functionality with preserved order."""
    custom_allowlist = {"example.com": ["page", "id"], "google.com": ["q", "lang"]}

    # Order should match input query string order
    assert (
        url_normalize(
            "https://example.com/search?page=1&id=123&utm_source=test",
            filter_params=True,
            param_allowlist=custom_allowlist,
        )
        == "https://example.com/search?page=1&id=123"
    )

    assert (
        url_normalize(
            "https://google.com/search?q=test&ie=utf8&lang=en",
            filter_params=True,
            param_allowlist=custom_allowlist,
        )
        == "https://google.com/search?q=test&lang=en"
    )


def test_custom_list_allowlist():
    """Test custom list allowlist functionality."""
    assert (
        url_normalize(
            "https://google.com/search?qq=test&ie=utf8&utm_source=test",
            filter_params=True,
            param_allowlist=["ie", "qq"],
        )
        == "https://google.com/search?qq=test&ie=utf8"
    )


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        # Basic parameter filtering
        (
            "https://www.google.com/search?q=test&utm_source=test",
            "https://www.google.com/search?q=test",
        ),
        (
            "https://www.youtube.com/watch?v=12345&utm_source=share",
            "https://www.youtube.com/watch?v=12345",
        ),
        # With www subdomain
        (
            "https://www.google.com/search?q=test&ref=test",
            "https://www.google.com/search?q=test",
        ),
        # With port number
        (
            "https://google.com:8080/search?q=test&ref=test",
            "https://google.com:8080/search?q=test",
        ),
        # Default allowlist cases
        (
            "https://www.google.com/search?q=test&utm_source=test&ie=utf8",
            "https://www.google.com/search?q=test&ie=utf8",
        ),
        (
            "https://www.baidu.com/s?wd=test&utm_source=test&ie=utf8",
            "https://www.baidu.com/s?wd=test&ie=utf8",
        ),
        (
            "https://youtube.com/watch?v=12345&utm_source=test&search_query=test",
            "https://youtube.com/watch?v=12345&search_query=test",
        ),
        # Non-allowlisted domain
        ("https://example.org/page?a=1&b=2", "https://example.org/page"),
    ],
)
def test_parameter_filtering(url: str, expected: str):
    """Test URL parameter filtering functionality with various scenarios."""
    assert url_normalize(url, filter_params=True) == expected
