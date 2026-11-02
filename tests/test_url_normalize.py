"""Integrations tests."""

from __future__ import annotations

import pytest

from url_normalize import url_humanize, url_normalize


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
def test_public_api_rejects_removed_charset_argument(transform):
    """Reject the removed option instead of silently ignoring an encoding request."""
    with pytest.raises(TypeError, match="unexpected keyword argument 'charset'"):
        transform("https://example.com/é", charset="iso-8859-1")


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            "HTTP://User:PaSS@Example.COM:080/socket?b=2&a=1#end",
            "http://User:PaSS@example.com/socket?b=2&a=1#end",
        ),
        ("HTTPS://Example.COM:0443/socket", "https://example.com/socket"),
        ("WS://Example.COM:080/socket", "ws://example.com/socket"),
        ("WSS://[2001:DB8::1]:0443/socket", "wss://[2001:db8::1]/socket"),
        ("http://example.com:443/socket", "http://example.com:443/socket"),
        ("https://example.com:80/socket", "https://example.com:80/socket"),
        ("ws://example.com:443/socket", "ws://example.com:443/socket"),
        ("wss://example.com:80/socket", "wss://example.com:80/socket"),
        ("https://example.com:065536/", "https://example.com:65536/"),
    ],
)
def test_public_api_normalizes_scheme_specific_ports(transform, value, expected):
    """Normalize ports without changing credentials or unrelated components."""
    assert transform(value) == expected
    assert transform(expected) == expected


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    "value",
    [
        "http://example.com:abc/",
        "http://EXAMPLE.COM:\uff18\uff10/",
        "http://[::1]:²/",
        "https://User:PaSS@EXAMPLE.COM:٠٤٤٣/path?b=2&a=1#end",
        "//example.com:%38%30/path",
        "custom://example.com:-1/path",
    ],
)
def test_public_api_rejects_invalid_port_syntax(transform, value):
    """Reject malformed ports in explicit and inferred URL authorities."""
    with pytest.raises(ValueError, match=r"^Port must contain only ASCII digits$"):
        transform(value)


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
def test_public_api_rejects_invalid_default_domain_port(transform):
    """Apply the same port syntax check to an injected default authority."""
    with pytest.raises(ValueError, match=r"^Port must contain only ASCII digits$"):
        transform("/path", default_domain="example.com:abc")


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    "value", ["mailto:user:abc@example.com", "./example.com:abc/path"]
)
def test_public_api_preserves_colons_outside_authorities(transform, value):
    """Keep opaque payloads and explicit relative paths outside port validation."""
    assert transform(value) == value
    assert transform(transform(value)) == value


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
def test_public_api_normalizes_long_padded_port(transform):
    """Remove a heavily padded default port while retaining Unicode and policies."""
    value = "http://[::1]:" + "0" * 5000 + "80/%C3%A9?#"
    path = "é" if transform is url_humanize else "%C3%A9"
    expected = f"http://[::1]/{path}?#"
    assert transform(value, keep_empty_components=True) == expected
    assert transform(expected, keep_empty_components=True) == expected


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("WS://Example.COM", "ws://example.com/"),
        ("WSS://Example.COM", "wss://example.com/"),
        ("ws://example.com:080?b=2&a=1", "ws://example.com/?b=2&a=1"),
        ("wss://example.com:443?b=2&a=1", "wss://example.com/?b=2&a=1"),
        ("ws://[2001:DB8::1]:443", "ws://[2001:db8::1]:443/"),
        ("wss://example.com:80", "wss://example.com:80/"),
    ],
)
def test_public_api_normalizes_empty_websocket_paths(transform, value, expected):
    """Use a root path while preserving WebSocket query order and non-default ports."""
    assert transform(value) == expected
    assert transform(expected) == expected


@pytest.mark.parametrize(
    "value",
    [
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
        "http://example.com/FOO",
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
        # Issue #36: Fragment with '=' should not be encoded
        "https://docs.google.com/spreadsheets/d/abcd/edit#gid=1234",
    ],
)
def test_url_normalize_no_changes_expected(value: str) -> None:
    """Assert url_normalize do not change URI if not required.

    http://www.intertwingly.net/wiki/pie/PaceCanonicalIds
    """
    assert url_normalize(value) == value


@pytest.mark.parametrize("separator", [".", "\u3002", "\uff0e", "\uff61"])
def test_url_normalize_trailing_idna_separator_is_idempotent(separator):
    """Canonicalize equivalent trailing host dots in one normalization pass."""
    value = f"https://Example.COM{separator}:443/path?q=1#section"
    normalized = url_normalize(value)
    assert normalized == "https://example.com/path?q=1#section"
    assert url_normalize(normalized) == normalized


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://.example.com/", "https://.example.com/"),
        ("https://a..example.com/", "https://a..example.com/"),
        ("https://example.com../", "https://example.com../"),
        ("https://example.com\u3002./", "https://example.com../"),
        ("https://./", "https://./"),
        ("https://../", "https://../"),
        ("https://159.189.213../", "https://159.189.213../"),
        (".example.com/page", "https://.example.com/page"),
        ("a..example.com/path", "https://a..example.com/path"),
        ("//a..example.com/path", "https://a..example.com/path"),
        ("custom://a..example.com/path", "custom://a..example.com/path"),
        (
            "https://User:PaSS@a..EXAMPLE.COM:8443/path?q=1#end",
            "https://User:PaSS@a..example.com:8443/path?q=1#end",
        ),
    ],
)
def test_public_api_preserves_empty_host_labels(transform, value, expected):
    """Preserve unusual host boundaries through both public entry points."""
    assert transform(value) == expected
    assert transform(expected) == expected
    assert url_normalize(url_humanize(value)) == expected


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
def test_public_api_preserves_empty_labels_in_default_domain(transform):
    """Apply host policy to an explicitly supplied default domain too."""
    assert (
        transform("/path", default_domain="a..example.com")
        == "https://a..example.com/path"
    )


def test_host_label_preservation_allows_unicode_humanization():
    """Decode safe Unicode without merging labels or dropping empty delimiters."""
    value = "https://.BÜCHER..de../%C3%A9?#"
    normalized = "https://.xn--bcher-kva..de../%C3%A9?#"
    displayed = "https://.bücher..de../é?#"

    assert url_normalize(value, keep_empty_components=True) == normalized
    assert url_humanize(value, keep_empty_components=True) == displayed
    assert url_normalize(displayed, keep_empty_components=True) == normalized


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("/../foo", "/foo"),
        ("/./../foo", "/foo"),
        ("/./foo", "/foo"),
        ("/./foo/.", "/foo/"),
        ("//www.foo.com/", "https://www.foo.com/"),
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
        ("http://:@example.com/", "http://example.com/"),
        ("http://@example.com/", "http://example.com/"),
        ("http://127.0.0.1:80/", "http://127.0.0.1/"),
        ("http://example.com:081/", "http://example.com:81/"),
        ("http://example.com:80/", "http://example.com/"),
        ("http://example.com", "http://example.com/"),
        ("http://example.com/?b&a", "http://example.com/?b&a"),
        ("http://example.com/?q=%5c", "http://example.com/?q=%5C"),
        ("http://example.com/?q=%C7", "http://example.com/?q=%C7"),
        ("http://example.com/?q=C%CC%A7", "http://example.com/?q=%C3%87"),
        ("http://EXAMPLE.COM/", "http://example.com/"),
        ("http://example.com/%7Ejane", "http://example.com/~jane"),
        ("http://example.com/a/../a/b", "http://example.com/a/b"),
        ("http://example.com/a/./b", "http://example.com/a/b"),
        (
            "http://example.com/#!5753509/hello-world",
            "http://example.com/#!5753509/hello-world",
        ),
        (
            "http://USER:pass@www.Example.COM/foo/bar",
            "http://USER:pass@www.example.com/foo/bar",
        ),
        ("http://www.example.com./", "http://www.example.com/"),
        ("http://www.foo.com:80/foo", "http://www.foo.com/foo"),
        ("http://www.foo.com.:81/foo", "http://www.foo.com:81/foo"),
        ("http://www.foo.com./foo/bar.html", "http://www.foo.com/foo/bar.html"),
        ("http://www.foo.com/%7Ebar", "http://www.foo.com/~bar"),
        ("http://www.foo.com/%7ebar", "http://www.foo.com/~bar"),
        (
            "пример.испытание/Служебная:Search/Test",
            "https://xn--e1afmkfd.xn--80akhbyknj4f/%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F:Search/Test",
        ),
        # Issue #19: http:example.com
        ("http:example.com", "http://example.com/"),
        ("http:example.com/path", "http://example.com/path"),
        ("ftp:test.com/files", "ftp://test.com/files"),
        ("https:www.example.com", "https://www.example.com/"),
    ],
)
def test_url_normalize_expected_changes(value: str, expected: str) -> None:
    """Assert url_normalize return expected results."""
    assert url_normalize(value) == expected


def test_url_normalize_filtered() -> None:
    """Assert url_normalize return expected results."""
    url = "/?a&b"
    expected = "/"

    actual = url_normalize(url, filter_params=True)

    assert actual == expected


def test_url_normalize_with_http_scheme() -> None:
    """Assert we could use http scheme as default."""
    url = "//www.foo.com/"
    expected = "http://www.foo.com/"

    actual = url_normalize(url, default_scheme="http")

    assert actual == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("/foo.png", "https://example.com/foo.png"),
        ("//google.com", "https://google.com/"),
        ("//example.com:80/foo.png", "https://example.com:80/foo.png"),
        ("//example.com/foo.png?foo=bar", "https://example.com/foo.png?foo=bar"),
        ("http://google.com", "http://google.com/"),
    ],
)
def test_url_normalize_with_default_domain(url: str, expected: str) -> None:
    """Assert we could use default_domain parameter."""
    actual = url_normalize(url, default_domain="example.com")

    assert actual == expected


def test_url_normalize_with_default_domain_and_scheme() -> None:
    """Assert we can use both default_domain and default_scheme together."""
    url = "/foo.png"
    expected = "http://example.com/foo.png"

    actual = url_normalize(url, default_scheme="http", default_domain="example.com")

    assert actual == expected


@pytest.mark.parametrize("component", ["/{value}", "/?q={value}", "/#{value}"])
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("%ff", "%FF"),
        ("%C7", "%C7"),
        ("%E0%A4%A", "%E0%A4%25A"),
        ("%FFe%CC%81", "%FF%C3%A9"),
        ("e%CC%81", "%C3%A9"),
        ("%EF%BF%BD", "%EF%BF%BD"),
    ],
)
def test_url_normalize_preserves_invalid_utf8_octets(component, value, expected):
    """Preserve invalid octets while normalizing valid Unicode to NFC."""
    prefix = "https://example.com"
    normalized = prefix + component.format(value=expected)
    assert url_normalize(prefix + component.format(value=value)) == normalized
    assert url_normalize(normalized) == normalized


@pytest.mark.parametrize("prefix", [" ", "\t", "\r\n", "\u00a0"])
@pytest.mark.parametrize("default_domain", [None, "default.example"])
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("http://example.com/path ", "http://example.com/path%20"),
        ("//x:443/path ", "https://x/path%20"),
        ("example.com/?q=x ", "https://example.com/?q=x%20"),
        ("/path ", "/path%20"),
        ("", ""),
        ("-", "-"),
    ],
)
def test_url_normalize_strips_leading_whitespace_before_defaults(
    prefix, default_domain, value, expected
):
    """Ignore leading whitespace before default-domain and scheme selection."""
    if default_domain and value.startswith("/") and not value.startswith("//"):
        expected = f"https://{default_domain}{expected}"
    actual = url_normalize(prefix + value, default_domain=default_domain)
    assert actual == expected
    assert url_normalize(actual, default_domain=default_domain) == expected
