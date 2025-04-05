"""Tests for normalize_path function."""

import pytest

from url_normalize.url_normalize import normalize_path


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
