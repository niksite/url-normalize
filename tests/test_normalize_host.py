"""Tests for normalize_host function."""

import pytest

from url_normalize.url_normalize import normalize_host


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


@pytest.mark.parametrize("prefix", ["", "."])
@pytest.mark.parametrize("separator", ["\u3002", "\uff0e", "\uff61"])
def test_normalize_host_rejects_leading_unicode_separator(prefix, separator):
    """Keep rejecting leading Unicode label separators as before."""
    with pytest.raises(UnicodeError):
        normalize_host(prefix + separator + "example.com")


@pytest.mark.parametrize("prefix", [".", ".."])
def test_normalize_host_strips_leading_ascii_dots(prefix):
    """Retain the existing normalization of leading ASCII dots."""
    assert normalize_host(prefix + "example.com") == "example.com"


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("пример.рф", "xn--e1afmkfd.xn--p1ai"),
        ("EXAMPLE.COM", "example.com"),
        ("under_score.example", "under_score.example"),
        ("[2001:DB8::1]", "[2001:db8::1]"),
    ],
)
def test_normalize_host_accepts_text_and_utf8_bytes(host, expected):
    """Normalize text and UTF-8 bytes to the same ASCII hostname."""
    assert normalize_host(host) == expected
    assert normalize_host(host.encode("utf-8")) == expected


@pytest.mark.parametrize("zone", ["%25ethA", "%ethA", "%25Interface.10", "%25ETH0"])
def test_normalize_host_preserves_ipv6_zone_case(zone):
    """Lowercase the IPv6 address without changing its interface identifier."""
    host = f"[FE80::ABCD{zone}]"
    expected = f"[fe80::abcd{zone}]"
    assert normalize_host(host) == expected
    assert normalize_host(host.encode("utf-8")) == expected
