"""Tests for normalize_path function."""

import pytest

from url_normalize import url_normalize
from url_normalize.normalize_path import normalize_path


@pytest.mark.parametrize("collapse_slashes", [False, True])
@pytest.mark.parametrize("remove_trailing_slash", [False, True])
@pytest.mark.parametrize(
    ("path", "expected"),
    [(".", "."), ("..", ".."), ("./a", "./a"), ("a/../b", "./b")],
)
def test_normalize_path_preserves_document_relative_context(
    path, expected, collapse_slashes, remove_trailing_slash
):
    """Resolve internal dots without introducing an authority or losing parents."""
    assert (
        normalize_path(
            path,
            "",
            collapse_slashes=collapse_slashes,
            remove_trailing_slash=remove_trailing_slash,
        )
        == expected
    )


@pytest.mark.parametrize("scheme", ["ws", "wss"])
def test_normalize_path_websocket_empty_path(scheme):
    """Use the root resource for an empty WebSocket path (RFC 6455 section 3)."""
    assert normalize_path("", scheme) == "/"


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("..", "/"),
        ("", "/"),
        ("/../foo", "/foo"),
        ("/..foo", "/..foo"),
        ("/./../foo", "/foo"),
        ("/./foo", "/foo"),
        ("/./foo/.", "/foo/"),
        ("/.foo", "/.foo"),
        ("/", "/"),
        ("/foo..", "/foo.."),
        ("/foo.", "/foo."),
        ("/FOO", "/FOO"),
        ("/foo/../bar", "/bar"),
        ("/foo/./bar", "/foo/bar"),
        ("/foo//", "/foo/"),
        ("/foo///bar//", "/foo/bar/"),
        ("/foo/bar/..", "/foo/"),
        ("/foo/bar/../..", "/"),
        ("/foo/bar/../../../../baz", "/baz"),
        ("/foo/bar/../../../baz", "/baz"),
        ("/foo/bar/../../", "/"),
        ("/foo/bar/../../baz", "/baz"),
        ("/foo/bar/../", "/foo/"),
        ("/foo/bar/../baz", "/foo/baz"),
        ("/foo/bar/.", "/foo/bar/"),
        ("/foo/bar/./", "/foo/bar/"),
        # Issue #25: we should preserve ? in the path
        ("/More+Tea+Vicar%3F/discussion", "/More+Tea+Vicar%3F/discussion"),
    ],
)
def test_normalize_path_result_is_expected(path: str, expected: str) -> None:
    """Assert we got expected results from the normalize_path function."""
    result = normalize_path(path, "http")
    assert result == expected, path


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        # RFC 3986 section 5.2.4 examples, then empty-segment boundaries.
        ("/a/b/c/./../../g", "/a/g"),
        ("mid/content=5/../6", "mid/6"),
        ("./a", "a"),
        ("../a", "a"),
        ("a/../b", "/b"),
        (".", "/"),
        ("/a//../b", "/a/b"),
        ("/a///../b", "/a//b"),
        ("/a//../../b", "/b"),
        ("/a/.//b", "/a//b"),
        ("/a//.", "/a//"),
        ("/a///..", "/a//"),
        ("/a/..//b", "//b"),
        ("//a///b//", "//a///b//"),
        ("/../../a", "/a"),
        ("/a/%2e%2E//b", "//b"),
        ("/a%2f%2f//b", "/a%2F%2F//b"),
        ("/a/%252e%252e//b", "/a/%252e%252e//b"),
    ],
)
def test_normalize_path_resolves_dots_with_empty_segments(path, expected):
    """Resolve dots against actual segments, including empty ones."""
    assert normalize_path(path, "https", collapse_slashes=False) == expected
    assert normalize_path(expected, "https", collapse_slashes=False) == expected


@pytest.mark.parametrize("scheme", ["http", "https", "ftp", "file", "ws", "wss"])
def test_normalize_path_applies_dot_rules_across_schemes(scheme):
    """Apply dot removal to each supported scheme without collapsing empty segments."""
    assert (
        normalize_path("/a//../%2e/b///", scheme, collapse_slashes=False) == "/a/b///"
    )


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/a//b///", "/a/b/"),
        ("/a//../b", "/a/b"),
        ("/a///../b", "/a/b"),
        ("/a/..//b", "/b"),
        ("/a%2f%2f//b", "/a%2F%2F/b"),
        ("///", "/"),
    ],
)
def test_normalize_path_collapses_only_after_resolving_dots(path, expected):
    """Collapse literal slashes after dot removal, retaining a trailing slash."""
    assert normalize_path(path, "https") == expected
    assert normalize_path(path, "https", collapse_slashes=True) == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("", "/"),
        ("/", "/"),
        ("///", "/"),
        ("/a/", "/a"),
        ("/a///", "/a"),
        ("/a//b///", "/a//b"),
        ("/a/../", "/"),
        ("/a//../b///", "/a/b"),
        ("/a/.", "/a"),
        ("/a/%2f/", "/a/%2F"),
        ("/a%2f", "/a%2F"),
    ],
)
def test_normalize_path_removes_trailing_slash_runs(path, expected):
    """Remove only trailing literal slashes after resolving dots, keeping root."""
    assert (
        normalize_path(
            path, "https", collapse_slashes=False, remove_trailing_slash=True
        )
        == expected
    )


@pytest.mark.parametrize("character", ":/?#[]@!$&'()*+,;=")
def test_normalize_path_preserves_encoded_reserved_characters(character):
    """Keep escaped delimiters distinct from literal path syntax."""
    escaped = f"%{ord(character):02X}"
    path = f"/a{escaped.lower()}b/%7e/e%CC%81/%25/%zz"
    expected = f"/a{escaped}b/~/%C3%A9/%25/%25zz"
    assert normalize_path(path, "https") == expected
    url = f"https://example.com{expected}?x=1#end"
    assert url_normalize(f"https://example.com{path}?x=1#end") == url
    assert url_normalize(url) == url
    literal = "%23" if character == "#" else "%3F" if character == "?" else character
    assert normalize_path(f"/a{character}b", "https") == f"/a{literal}b"
