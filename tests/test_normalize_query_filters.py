"""URL parameter filtering test module."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from url_normalize import url_humanize, url_normalize
from url_normalize.param_allowlist import get_allowed_params


def test_param_filtering_disabled_by_default():
    """Test that parameter filtering is disabled by default."""
    url = "https://www.google.com/search?q=test&utm_source=test"
    assert url_normalize(url) == url


def test_empty_query():
    """Remove an empty query delimiter by default."""
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


@pytest.mark.parametrize("api", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    "allowlist", ["id", {"example.com": "id"}, {"EXAMPLE.COM.": "id"}]
)
def test_single_name_allowlist_keeps_the_whole_name(api, allowlist):
    """Do not split a multi-character allowed name into individual characters."""
    # Single-name support also exists in w3lib 2.5.0's test_url_query_cleaner:
    # https://github.com/scrapy/w3lib/blob/v2.5.0/tests/test_url.py
    assert (
        api(
            "https://example.com/?id=123&i=456&d=789&id=987&drop=1",
            param_allowlist=allowlist,
        )
        == "https://example.com/?id=123&id=987"
    )


@pytest.mark.parametrize(
    ("name", "query", "expected"),
    [
        ("", "=empty&drop=1", "=empty"),
        ("page,id", "page,id=literal&page=1&id=2", "page,id=literal"),
        ("café", "caf%C3%A9=1&drop=2", "caf%C3%A9=1"),  # codespell:ignore caf
        ("a%2fb", "a%2Fb=1&a/b=2", "a%2Fb=1"),
    ],
)
def test_single_name_allowlist_preserves_name_boundaries(name, query, expected):
    """Use existing key normalization without inventing comma or empty-name rules."""
    assert (
        url_normalize(f"https://example.com/?{query}", param_allowlist=name)
        == f"https://example.com/?{expected}"
    )


@pytest.mark.parametrize("api", [url_normalize, url_humanize])
def test_single_name_allowlist_on_relative_reference(api):
    """Apply a global name without requiring an authority or losing path policies."""
    assert (
        api(
            "../a//b?id=1&drop=2#",
            param_allowlist="id",
            collapse_slashes=False,
            keep_empty_components=True,
        )
        == "../a//b?id=1#"
    )


@pytest.mark.parametrize("api", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    ("options", "expected_query"),
    [
        ({"param_allowlist": ["id"]}, "?id=1"),
        ({"param_allowlist": {"google.com": ["id"]}}, "?id=1"),
        ({"param_allowlist": ["id"], "filter_params": False}, "?id=1"),
        ({"param_allowlist": []}, ""),
        ({"param_allowlist": {}}, ""),
        ({"param_allowlist": {"other.example": ["id"]}}, ""),
        ({"param_allowlist": None}, "?id=1&q=hello&drop=2"),
        ({"param_allowlist": None, "filter_params": True}, "?q=hello"),
    ],
)
def test_explicit_allowlist_enables_filtering(api, options, expected_query):
    """Apply supplied rules, including empty ones, instead of built-in defaults."""
    value = "https://google.com/?id=1&q=hello&drop=2"
    assert api(value, **options) == f"https://google.com/{expected_query}"


def test_domain_allowlist_can_mix_single_names_and_lists():
    """Accept both rule forms without changing a caller-owned dictionary."""
    rules = {"one.example": "id", "two.example": ["q"]}
    assert get_allowed_params("one.example", rules) == {"id"}
    assert get_allowed_params("two.example", rules) == {"q"}
    assert get_allowed_params("other.example", rules) == set()
    assert rules == {"one.example": "id", "two.example": ["q"]}


@pytest.mark.parametrize("separator", [".", "\u3002", "\uff0e", "\uff61"])
def test_custom_allowlist_matches_trailing_idna_separator(separator):
    """Match custom domain keys with any IDNA trailing label separator."""
    assert (
        url_normalize(
            "https://example.com/?q=1&drop=2",
            filter_params=True,
            param_allowlist={f"example.com{separator}": ["q"]},
        )
        == "https://example.com/?q=1"
    )


@pytest.mark.parametrize("key", [".example.com", "example..com", "example.com.."])
def test_custom_allowlist_distinguishes_empty_host_labels(key):
    """Match unusual hostnames only to their own allowlist entries."""
    allowlist = {key: ["q"], "EXAMPLE.COM.": ["keep"]}
    assert (
        url_normalize(
            "https://example.com/?q=1&keep=2",
            filter_params=True,
            param_allowlist=allowlist,
        )
        == "https://example.com/?keep=2"
    )
    assert (
        url_normalize(
            f"https://{key}/?q=1&keep=2",
            filter_params=True,
            param_allowlist=allowlist,
        )
        == f"https://{key}/?q=1"
    )


@pytest.mark.parametrize(
    ("name", "query", "expected"),
    [
        ("café", "café=1", "caf%C3%A9=1"),  # codespell:ignore caf
        ("café", "caf%C3%A9=1", "caf%C3%A9=1"),  # codespell:ignore caf
        ("cafe\u0301", "caf%C3%A9=1", "caf%C3%A9=1"),  # codespell:ignore caf
        ("search term", "search%20term=1", "search%20term=1"),
    ],
)
@pytest.mark.parametrize("domain_specific", [False, True])
def test_custom_allowlist_normalizes_parameter_names(
    name, query, expected, domain_specific
):
    """Match parameter names using the same normalization as query keys."""
    allowlist = {"example.com": [name]} if domain_specific else [name]
    assert (
        url_normalize(
            f"https://example.com/?{query}&drop=2",
            filter_params=True,
            param_allowlist=allowlist,
        )
        == f"https://example.com/?{expected}"
    )
    assert allowlist == ({"example.com": [name]} if domain_specific else [name])


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("a+b", "a+b=1"),
        ("a%2Bb", "a%2Bb=2"),
        ("a b", "a%20b=3"),
        ("a%20b", "a%20b=3"),
    ],
)
@pytest.mark.parametrize("domain_specific", [False, True])
def test_custom_allowlist_keeps_plus_and_space_names_distinct(
    name, expected, domain_specific
):
    """Keep literal plus, encoded plus, and encoded space keys distinct."""
    allowlist = {"example.com": [name]} if domain_specific else [name]
    assert (
        url_normalize(
            "https://example.com/?a+b=1&a%2Bb=2&a%20b=3&drop=4",
            filter_params=True,
            param_allowlist=allowlist,
        )
        == f"https://example.com/?{expected}"
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


@pytest.mark.parametrize("reverse", [False, True])
def test_custom_allowlist_matches_equivalent_ipv6_spellings(reverse):
    """Match expanded and compressed IPv6 addresses on either side of filtering."""
    host, key = "[2001:0DB8:0:0:0:0:0:1]", "[2001:db8::1]"
    if reverse:
        host, key = key, host
    allowlist = {key: ["q"]}
    assert (
        url_normalize(
            f"https://{host}/?q=1&drop=2",
            filter_params=True,
            param_allowlist=allowlist,
        )
        == "https://[2001:db8::1]/?q=1"
    )
    assert allowlist == {key: ["q"]}


@pytest.mark.parametrize("reverse", [False, True])
def test_custom_allowlist_prefers_canonical_ipv6_key(reverse):
    """Keep the canonical rule authoritative when IPv6 spellings become aliases."""
    entries = [("[2001:0DB8:0:0:0:0:0:1]", ["q"]), ("[2001:db8::1]", ["keep"])]
    allowlist = dict(reversed(entries) if reverse else entries)
    assert (
        url_normalize(
            "https://[2001:0DB8:0:0:0:0:0:1]/?q=1&keep=2",
            filter_params=True,
            param_allowlist=allowlist,
        )
        == "https://[2001:db8::1]/?keep=2"
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


@pytest.mark.parametrize("invalid_domain", ["a" * 64 + ".example", "bad\x1bc.example"])
def test_custom_allowlist_ignores_unrelated_invalid_domain(invalid_domain):
    """Keep a malformed unrelated key from breaking a valid domain lookup."""
    assert (
        url_normalize(
            "https://пример.рф/?q=1",
            filter_params=True,
            param_allowlist={invalid_domain: [], "пример.рф": ["q"]},
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


@pytest.mark.parametrize("api", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    ("allowed", "expected"), [("a/b", "a/b=2"), ("a%2fb", "a%2Fb=1")]
)
def test_query_allowlist_distinguishes_reserved_escapes(api, allowed, expected):
    """Normalize escape case in allowlists without conflating literal punctuation."""
    assert (
        api(
            "https://example.com/?a%2Fb=1&a/b=2",
            filter_params=True,
            param_allowlist=[allowed],
        )
        == f"https://example.com/?{expected}"
    )
