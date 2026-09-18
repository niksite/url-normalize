"""Tests for normalize_path function."""

import pytest

from url_normalize.url_normalize import normalize_path, url_normalize


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
