"""Tests for normalize_path function."""

from url_normalize.url_normalize import normalize_path

EXPECTED_DATA = {
    "..": "/",
    "": "/",
    "/../foo": "/foo",
    "/..foo": "/..foo",
    "/./../foo": "/foo",
    "/./foo": "/foo",
    "/./foo/.": "/foo/",
    "/.foo": "/.foo",
    "/": "/",
    "/foo..": "/foo..",
    "/foo.": "/foo.",
    "/FOO": "/FOO",
    "/foo/../bar": "/bar",
    "/foo/./bar": "/foo/bar",
    "/foo//": "/foo/",
    "/foo///bar//": "/foo/bar/",
    "/foo/bar/..": "/foo/",
    "/foo/bar/../..": "/",
    "/foo/bar/../../../../baz": "/baz",
    "/foo/bar/../../../baz": "/baz",
    "/foo/bar/../../": "/",
    "/foo/bar/../../baz": "/baz",
    "/foo/bar/../": "/foo/",
    "/foo/bar/../baz": "/foo/baz",
    "/foo/bar/.": "/foo/bar/",
    "/foo/bar/./": "/foo/bar/",
    # Issue #25: we should preserve ? in the path
    "/More+Tea+Vicar%3F/discussion": "/More+Tea+Vicar%3F/discussion",
}


def test_normalize_path_result_is_expected():
    """Assert we got expected results from the normalize_path function."""
    for url, expected in EXPECTED_DATA.items():
        result = normalize_path(url, "http")

        assert result == expected, url
