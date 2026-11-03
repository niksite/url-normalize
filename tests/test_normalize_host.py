"""Tests for normalize_host function."""

import pytest

from url_normalize.normalize_host import normalize_host


def test_normalize_host_rejects_display_controls_in_utf8_bytes():
    """Check display controls after decoding a byte hostname."""
    with pytest.raises(UnicodeError, match=r"^Host must not contain display controls$"):
        normalize_host("[fe80::1%eth0\u202e]".encode())


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        # Basic cases
        ("site.com", "site.com"),
        ("SITE.COM", "site.com"),
        ("site.com.", "site.com"),
        # Cyrillic domains
        ("пример.испытание", "xn--e1afmkfd.xn--80akhbyknj4f"),
        # Mixed case with Cyrillic
        ("ExAmPle.РФ", "example.xn--p1ai"),
        # IDNA2008 with UTS46
        ("faß.de", "xn--fa-hia.de"),
        # Edge cases
        ("ドメイン.テスト", "xn--eckwd4c7c.xn--zckzah"),  # Japanese
        ("domain.café", "domain.xn--caf-dma"),  # Latin with diacritic
        # Normalization tests
        ("über.example", "xn--ber-goa.example"),  # IDNA 2008 for umlaut
        ("example。com", "example.com"),  # Normalize full-width punctuation
        ("", ""),  # Path references and local file URLs have no hostname.
    ],
)
def test_normalize_host_result_is_expected(host: str, expected: str) -> None:
    """Assert we got expected results from the normalize_host function."""
    result = normalize_host(host)
    assert result == expected, host


@pytest.mark.parametrize("separator", [".", "\u3002", "\uff0e", "\uff61"])
@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("EXAMPLE.COM", "example.com"),
        ("faß.de", "xn--fa-hia.de"),
        ("under_score.example", "under_score.example"),
    ],
)
def test_normalize_host_strips_trailing_idna_separator(host, expected, separator):
    """Strip equivalent trailing label separators before IDNA conversion."""
    normalized = normalize_host(host + separator)
    assert normalized == expected
    assert normalize_host(normalized) == normalized


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        (".EXAMPLE.COM", ".example.com"),
        ("..example.com", "..example.com"),
        ("\u3002example.com", ".example.com"),
        ("\uff0eexample.com", ".example.com"),
        ("\uff61example.com", ".example.com"),
        (".\u3002example.com", "..example.com"),
        ("a..example.com", "a..example.com"),
        ("a\u3002\u3002example.com", "a..example.com"),
        ("a.\uff0eexample.com", "a..example.com"),
        ("a\uff61.example.com", "a..example.com"),
        ("example.com..", "example.com.."),
        ("example.com.\u3002", "example.com.."),
        ("example.com\uff0e\uff61", "example.com.."),
        ("example.com\u3002.", "example.com.."),
        ("example.com...", "example.com..."),
        ("159.189.213..", "159.189.213.."),
        (".", "."),
        ("..", ".."),
        ("\u3002", "."),
        (".example.com.", ".example.com"),
        ("a..bücher.de", "a..xn--bcher-kva.de"),
        (".under_score.example..", ".under_score.example.."),
        ("faß..under_score.de", "fass..under_score.de"),
    ],
)
def test_normalize_host_preserves_empty_labels(host, expected):
    """Keep unusual label boundaries while normalizing case and IDNA spelling."""
    assert normalize_host(host) == expected
    assert normalize_host(expected) == expected


def test_normalize_host_preserves_empty_labels_in_utf8_bytes():
    """Preserve label boundaries after decoding UTF-8 bytes."""
    assert normalize_host("a.\u3002example.com".encode()) == "a..example.com"


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("пример.рф", "xn--e1afmkfd.xn--p1ai"),
        ("EXAMPLE.COM", "example.com"),
        ("under_score.example", "under_score.example"),
        ("[2001:0DB8:0:0:0:0:0:1]", "[2001:db8::1]"),
    ],
)
def test_normalize_host_accepts_text_and_utf8_bytes(host, expected):
    """Normalize text and UTF-8 bytes to the same ASCII hostname."""
    assert normalize_host(host) == expected
    assert normalize_host(host.encode("utf-8")) == expected


@pytest.mark.parametrize("zone", ["%25ethA", "%ethA", "%25Interface.10", "%25ETH0"])
def test_normalize_host_preserves_ipv6_zone_case(zone):
    """Compress the IPv6 address without changing its interface identifier."""
    host = f"[FE80:0:0:0:0:0:0:ABCD{zone}]"
    expected = f"[fe80::abcd{zone}]"
    assert normalize_host(host) == expected
    assert normalize_host(host.encode("utf-8")) == expected


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("[2001:0DB8:0000:0000:0000:0000:0000:0001]", "[2001:db8::1]"),
        ("[2001:db8::0:1]", "[2001:db8::1]"),
        ("[2001:db8:0:1:1:1:1:1]", "[2001:db8:0:1:1:1:1:1]"),
        ("[2001:db8::1:1:1:1:1]", "[2001:db8:0:1:1:1:1:1]"),
        ("[2001:0:0:1:0:0:0:1]", "[2001:0:0:1::1]"),
        ("[2001:db8:0:0:1:0:0:1]", "[2001:db8::1:0:0:1]"),
        ("[0:0:0:0:0:0:0:0]", "[::]"),
        ("[0:0:0:0:0:0:0:1]", "[::1]"),
        ("[::FFFF:C000:280]", "[::ffff:192.0.2.128]"),
        ("[0:0:0:0:0:ffff:192.0.2.128]", "[::ffff:192.0.2.128]"),
        ("[::ffff:0:0]", "[::ffff:0.0.0.0]"),
        ("[2001:db8::192.0.2.128]", "[2001:db8::c000:280]"),
        ("[v1.FE80::A]", "[v1.fe80::a]"),
    ],
)
def test_normalize_host_canonicalizes_ipv6_literals(host, expected):
    """Apply RFC 5952 compression and mapped notation, retaining IPvFuture text."""
    assert normalize_host(host) == expected
    assert normalize_host(expected) == expected
