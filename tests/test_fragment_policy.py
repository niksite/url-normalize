"""Public fragment syntax contracts independent of normalization equality."""

from urllib.parse import urlsplit
from urllib.request import Request

import pytest

from url_normalize import url_humanize, url_normalize


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    "fragment",
    [
        "!/route?x=1&x=2",
        "/route//../next/",
        "!",
        "%21/route",
        "/a%2Fb?x=a%26b",
        ":~:text=hello",
        "anchor:~:text=prefix-,start,end,-suffix&text=second",
        ":~:text=one%2Ctwo%2Dthree%26four",
        "%3A~%3Atext=hello",
        ":%7E:text=hello",
        ":~:%74ext=hello",
        ":~:te%78t=hello",  # codespell:ignore te
        ":~:text%3Dhello",
        ":~:text=prefix%2D,start",
        ":~:text=start,%2Dsuffix",
        ":~:text=first%26text=second",
        ":~:text=hello%20world",
        ":~:text=%252D%252C%2526",
        "ordinary%23nested",
        "see:~:textbook",
        ":~:TEXT=hello",
        ":~:unknown=hello&text=world",
    ],
)
def test_public_api_preserves_fragment_syntax(transform, fragment):
    """Retain literal syntax and encoded data without changing the query."""
    base = "https://example.com/a?b=2&a=1&a=3&flag=&flag"
    value = f"{base}#{fragment}"

    result = transform(value)

    assert result == value
    assert urlsplit(result).fragment == fragment
    assert urlsplit(result).query == "b=2&a=1&a=3&flag=&flag"
    assert transform(result) == result


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("codepoint", range(128))
def test_public_api_keeps_ascii_fragment_escapes(transform, codepoint):
    """Keep ASCII escapes, including directive letters, alongside readable Unicode."""
    value = f"https://example.com/#%C3%A9%{codepoint:02x}%E4%B8%AD"
    prefix, suffix = (
        ("é", "中") if transform is url_humanize else ("%C3%A9", "%E4%B8%AD")
    )
    expected_fragment = f"{prefix}%{codepoint:02X}{suffix}"

    result = transform(value)

    assert result == f"https://example.com/#{expected_fragment}"
    assert urlsplit(result).fragment == expected_fragment
    assert url_normalize(result) == url_normalize(value)


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
def test_fragment_is_independent_of_query_and_path_policies(transform):
    """Filter and clean the URL without treating its route as a path or query."""
    value = "/a//b///?keep=1&drop=2#!/route//../next/?keep=3&drop=4"
    result = transform(
        value,
        default_domain="example.com",
        collapse_slashes=True,
        remove_trailing_slash=True,
        filter_params=True,
        param_allowlist=["keep"],
    )

    assert result == "https://example.com/a/b?keep=1#!/route//../next/?keep=3&drop=4"


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
def test_existing_escaped_fragment_parameter_is_ordinary_query_data(transform):
    """Retain a caller-supplied legacy parameter without adding another one."""
    value = "https://example.com/?_escaped_fragment_=/old&keep=1#!/new"

    assert transform(value) == value


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    "base",
    [
        "ftp://example.com/file",
        "file:///tmp/document",
        "mailto:user@example.com",
        "urn:example:document",
    ],
)
def test_fragment_policy_applies_across_schemes(transform, base):
    """Preserve fragment syntax independently of scheme-specific path policies."""
    value = f"{base}#anchor:~:text=hello%2Dworld"

    assert transform(value) == value


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
def test_nested_hash_is_fragment_data(transform):
    """Keep the first hash as the URL boundary and encode a subsequent hash."""
    value = "https://example.com/?keep=1#!a#!b"

    assert transform(value) == "https://example.com/?keep=1#!a%23!b"


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
def test_fragment_removal_is_opt_in(transform):
    """Keep fragment routes by default and remove them only on request."""
    value = "https://example.com/page?id=1#!/route?x=2"
    assert transform(value) == value
    assert transform(value, strip_fragment=False) == value
    assert transform(value, strip_fragment=True) == "https://example.com/page?id=1"


@pytest.mark.parametrize(
    "fragment",
    ["section", "!/route?x=1", "/route?x=1", "section:~:text=hello", "%23a#nested"],
)
def test_fragment_removal_discards_the_whole_component(fragment):
    """Remove anchors, routes and text directives without rewriting query fields."""
    # Adapt w3lib's test_remove_fragments and normalize-url's stripHash examples:
    # https://github.com/scrapy/w3lib/blob/v2.5.0/tests/test_url.py
    # https://github.com/sindresorhus/normalize-url/blob/v10.0.0/test.js
    base = "https://example.com/page?b=2&a=3&a=1&flag=&flag"
    value = f"{base}#{fragment}"
    for transform in (url_normalize, url_humanize):
        result = transform(value, strip_fragment=True)
        assert result == base
        assert transform(result, strip_fragment=True) == result


def test_fragment_removal_groups_document_fetches():
    """Match a client's fragment-free request target without making a request."""
    first = "https://example.com/article?id=1#intro"
    second = "https://example.com/article?id=1#details"
    assert url_normalize(first) != url_normalize(second)
    result = url_normalize(first, strip_fragment=True)
    assert result == url_normalize(second, strip_fragment=True)
    assert result == "https://example.com/article?id=1"
    assert Request(first).selector == Request(second).selector == "/article?id=1"


def test_fragment_removal_preserves_encoded_hashes_and_legacy_query_data():
    """A percent-encoded hash belongs to its component, not the fragment boundary."""
    base = "https://user:p%23ss@example.com/a%23b?x=%23keep&_escaped_fragment_=/old"
    for transform in (url_normalize, url_humanize):
        assert transform(base, strip_fragment=True) == base
        assert transform(f"{base}#!/new", strip_fragment=True) == base


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://example.com/page?#", "https://example.com/page?"),
        ("https://example.com/page?#route", "https://example.com/page?"),
        ("#section", ""),
        ("#", ""),
        ("?#section", "?"),
    ],
)
def test_fragment_removal_overrides_empty_fragment_preservation(value, expected):
    """Remove even an empty fragment delimiter, while retaining an empty query."""
    for transform in (url_normalize, url_humanize):
        assert (
            transform(value, strip_fragment=True, keep_empty_components=True)
            == expected
        )
        assert transform(value, strip_fragment=True) == expected.removesuffix("?")


@pytest.mark.parametrize(
    "value",
    [
        "https://[::1]/page?a=1",
        "../a//b?x=%23keep",
        "?b=2&a=1",
        "file:///tmp/a%23b",
        "mailto:user@example.com?subject=hello",
        "custom://example.com/path",
        "data:text/plain,a%23b",
    ],
)
def test_fragment_removal_respects_url_form(value):
    """Share existing parsing across relative, IPv6, opaque and file URLs."""
    for transform in (url_normalize, url_humanize):
        assert (
            transform(f"{value}#section", strip_fragment=True, collapse_slashes=False)
            == value
        )


@pytest.mark.parametrize(
    ("transform", "expected"),
    [
        (
            url_normalize,
            "https://example.com/a//caf%C3%A9?a=2&z=1",  # codespell:ignore caf
        ),
        (url_humanize, "https://example.com/a//café?a=2&z=1"),
    ],
)
def test_fragment_removal_combines_with_other_policies(transform, expected):
    """Keep humanization, path, filtering and sorting choices independent."""
    value = "/a//café///?z=1&utm_source=email&drop=3&a=2&extra=4#/route?x=5"
    options = {
        "default_domain": "example.com",
        "collapse_slashes": False,
        "remove_trailing_slash": True,
        "param_allowlist": ["z", "a", "drop", "utm_source"],
        "param_denylist": "drop",
        "remove_tracking_params": True,
        "sort_query": True,
        "strip_fragment": True,
        "keep_empty_components": True,
    }
    result = transform(value, **options)
    assert result == expected
    assert transform(result, **options) == result
    assert url_normalize(result, **options) == url_normalize(value, **options)


@pytest.mark.parametrize("value", [None, ""])
def test_fragment_removal_preserves_empty_input(value):
    """Keep both APIs' empty-input contract when fragment removal is requested."""
    assert url_normalize(value, strip_fragment=True) == value
    assert url_humanize(value, strip_fragment=True) == value
