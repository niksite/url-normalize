# -*- coding: utf-8 -*-
"""Integrations tests."""
from url_normalize import url_normalize


EXPECTED_RESULTS = {
    "/../foo": "/foo",  # was: '/../foo',
    "/./../foo": "/foo",  # was: '/../foo',
    "/./foo": "/foo",
    "/./foo/.": "/foo/",
    "//www.foo.com/": "https://www.foo.com/",
    "/foo/../bar": "/bar",
    "/foo/./bar": "/foo/bar",
    "/foo//": "/foo/",
    "/foo///bar//": "/foo/bar/",
    "/foo/bar/..": "/foo/",
    "/foo/bar/../..": "/",
    "/foo/bar/../../../../baz": "/baz",
    "/foo/bar/../../../baz": "/baz",  # was: '/../baz',
    "/foo/bar/../../": "/",
    "/foo/bar/../../baz": "/baz",
    "/foo/bar/../": "/foo/",
    "/foo/bar/../baz": "/foo/baz",
    "/foo/bar/.": "/foo/bar/",
    "/foo/bar/./": "/foo/bar/",
    "http://:@example.com/": "http://example.com/",
    "http://@example.com/": "http://example.com/",
    "http://127.0.0.1:80/": "http://127.0.0.1/",
    "http://example.com:081/": "http://example.com:81/",
    "http://example.com:80/": "http://example.com/",
    "http://example.com": "http://example.com/",
    "http://example.com/?b&a": "http://example.com/?a&b",
    "http://example.com/?q=%5c": "http://example.com/?q=%5C",
    "http://example.com/?q=%C7": "http://example.com/?q=%EF%BF%BD",
    "http://example.com/?q=C%CC%A7": "http://example.com/?q=%C3%87",
    "http://EXAMPLE.COM/": "http://example.com/",
    "http://example.com/%7Ejane": "http://example.com/~jane",
    "http://example.com/a/../a/b": "http://example.com/a/b",
    "http://example.com/a/./b": "http://example.com/a/b",
    "http://lifehacker.com/#!5753509/hello-world-this-is-the-new-lifehacker": "http://lifehacker.com/?_escaped_fragment_=5753509/hello-world-this-is-the-new-lifehacker",
    "http://USER:pass@www.Example.COM/foo/bar": "http://USER:pass@www.example.com/foo/bar",
    "http://www.example.com./": "http://www.example.com/",
    "http://www.foo.com:80/foo": "http://www.foo.com/foo",
    "http://www.foo.com.:81/foo": "http://www.foo.com:81/foo",
    "http://www.foo.com./foo/bar.html": "http://www.foo.com/foo/bar.html",
    "http://www.foo.com/%7Ebar": "http://www.foo.com/~bar",
    "http://www.foo.com/%7ebar": "http://www.foo.com/~bar",
    "пример.испытание/Служебная:Search/Test": "https://xn--e1afmkfd.xn--80akhbyknj4f/%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F:Search/Test",
}

NO_CHANGES_EXPECTED = (
    "-",
    "",
    "/..foo",
    "/.foo",
    "/foo..",
    "/foo.",
    "ftp://user:pass@ftp.foo.net/foo/bar",
    "http://127.0.0.1/",
    "http://example.com:8080/",
    "http://example.com/?a&b",
    "http://example.com/?q=%5C",
    "http://example.com/?q=%C3%87",
    "http://example.com/?q=%E2%85%A0",
    "http://example.com/",
    "http://example.com/~jane",
    "http://example.com/a/b",
    "http://user:password@example.com/",
    "http://www.foo.com:8000/foo",
    # from rfc2396bis
    "ftp://ftp.is.co.za/rfc/rfc1808.txt",
    "http://www.ietf.org/rfc/rfc2396.txt",
    "ldap://[2001:db8::7]/c=GB?objectClass?one",
    "mailto:John.Doe@example.com",
    "news:comp.infosystems.www.servers.unix",
    "tel:+1-816-555-1212",
    "telnet://192.0.2.16:80/",
    "urn:oasis:names:specification:docbook:dtd:xml:4.1.2",
)


def test_url_normalize_changes():
    """Assert url_normalize do not change URI if not required.

    http://www.intertwingly.net/wiki/pie/PaceCanonicalIds
    """
    for value in NO_CHANGES_EXPECTED:
        assert url_normalize(value) == value


def test_url_normalize_results():
    """Assert url_normalize return expected results."""
    for value, expected in EXPECTED_RESULTS.items():
        assert expected == url_normalize(value), value
