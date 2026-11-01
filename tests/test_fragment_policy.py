"""Public fragment syntax contracts independent of normalization equality."""

from urllib.parse import urlsplit

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
