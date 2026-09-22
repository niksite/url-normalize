"""URL parameter filtering test module."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from url_normalize import url_normalize
from url_normalize.param_allowlist import get_allowed_params


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


@pytest.mark.parametrize(
    ("host", "canonical", "allowlist"),
    [
        ("www.google.com.", "www.google.com", None),
        ("WWW.GOOGLE.COM.", "www.google.com", None),
        ("www。google.com", "www.google.com", None),
        ("google.com", "google.com", None),
        ("пример.рф", "xn--e1afmkfd.xn--p1ai", {"xn--e1afmkfd.xn--p1ai": ["q"]}),
        (
            "xn--e1afmkfd.xn--p1ai.",
            "xn--e1afmkfd.xn--p1ai",
            {"xn--e1afmkfd.xn--p1ai": ["q"]},
        ),
        ("EXAMPLE.COM.", "example.com", ["q"]),
    ],
)
def test_parameter_filtering_uses_normalized_host(host, canonical, allowlist):
    """Use the output host's canonical spelling when choosing an allowlist."""
    assert (
        url_normalize(
            f"https://{host}/?q=test&utm_source=x",
            filter_params=True,
            param_allowlist=allowlist,
        )
        == f"https://{canonical}/?q=test"
    )


@pytest.mark.parametrize("port", ["", ":8080"])
def test_parameter_filtering_preserves_bracketed_host(port):
    """Keep IPv6 address colons intact when looking up a canonical host."""
    assert (
        url_normalize(
            f"https://[2001:DB8::1]{port}/?q=test&utm_source=x",
            filter_params=True,
            param_allowlist={"[2001:db8::1]": ["q"]},
        )
        == f"https://[2001:db8::1]{port}/?q=test"
    )


@pytest.mark.parametrize("host", ["пример.рф", "xn--e1afmkfd.xn--p1ai", "ПРИМЕР.РФ."])
@pytest.mark.parametrize(
    "key",
    [
        "пример.рф",
        "xn--e1afmkfd.xn--p1ai",
        "ПРИМЕР.РФ.",
        "www。пример.рф",
        "пример.рф:8080",
    ],
)
def test_custom_allowlist_normalizes_mapping_keys(host, key):
    """Match equivalent domain spellings on both sides of an allowlist."""
    allowlist = {key: ["q"]}
    result = url_normalize(
        f"https://{host}/?q=1&utm_source=x",
        filter_params=True,
        param_allowlist=allowlist,
    )
    assert result == "https://xn--e1afmkfd.xn--p1ai/?q=1"
    assert allowlist == {key: ["q"]}


@pytest.mark.parametrize("key", ["[2001:DB8::1]", "[2001:DB8::1]:8080"])
def test_custom_allowlist_normalizes_bracketed_keys(key):
    """Preserve IPv6 colons when normalizing dictionary keys."""
    assert (
        url_normalize(
            "https://[2001:db8::1]/?q=1&drop=2",
            filter_params=True,
            param_allowlist={key: ["q"]},
        )
        == "https://[2001:db8::1]/?q=1"
    )


@pytest.mark.parametrize("allowed", [[], ["q"]])
@pytest.mark.parametrize("reverse", [False, True])
def test_custom_allowlist_canonical_key_takes_precedence(allowed, reverse):
    """Keep canonical rules authoritative instead of merging conflicting aliases."""
    entries = [("пример.рф", ["other"]), ("xn--e1afmkfd.xn--p1ai", allowed)]
    allowlist = dict(reversed(entries) if reverse else entries)
    expected = "https://xn--e1afmkfd.xn--p1ai/" + ("?q=1" if allowed else "")
    assert (
        url_normalize(
            "https://пример.рф/?q=1&other=2",
            filter_params=True,
            param_allowlist=allowlist,
        )
        == expected
    )


def test_custom_allowlist_ignores_unrelated_invalid_domain():
    """Keep a malformed unrelated key from breaking a valid domain lookup."""
    assert (
        url_normalize(
            "https://пример.рф/?q=1",
            filter_params=True,
            param_allowlist={"a" * 64 + ".example": [], "пример.рф": ["q"]},
        )
        == "https://xn--e1afmkfd.xn--p1ai/?q=1"
    )


@pytest.mark.parametrize("host", ["target.example", "unlisted.example"])
def test_filtering_resolves_domain_rules_once_per_url(host):
    """Bound domain lookups independently of how many parameters are supplied."""
    allowlist = {f"d{index}.example": ["q"] for index in range(20)}
    allowlist["TARGET.EXAMPLE."] = ["q"]
    query = "&".join(f"q={index}&drop={index}" for index in range(50))
    with patch(
        "url_normalize.normalize_query.get_allowed_params", wraps=get_allowed_params
    ) as lookup:
        result = url_normalize(
            f"https://{host}/?{query}", filter_params=True, param_allowlist=allowlist
        )
    expected = f"https://{host}/"
    if host == "target.example":
        expected += "?" + "&".join(f"q={index}" for index in range(50))
    assert result == expected
    lookup.assert_called_once_with(host, allowlist)
