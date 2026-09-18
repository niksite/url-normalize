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


@pytest.mark.parametrize("charset", ["utf-8", "utf-16", "utf-32", "iso-8859-1"])
@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("пример.рф", "xn--e1afmkfd.xn--p1ai"),
        ("EXAMPLE.COM", "example.com"),
        ("under_score.example", "under_score.example"),
        ("[2001:DB8::1]", "[2001:db8::1]"),
    ],
)
def test_normalize_host_decodes_idna_output_as_ascii(host, expected, charset):
    """Decode ASCII IDNA output independently of the input byte encoding."""
    assert normalize_host(host, charset) == expected
    assert normalize_host(expected.encode(charset), charset) == expected
