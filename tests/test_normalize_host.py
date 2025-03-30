"""Tests for normalize_host function."""

from url_normalize.url_normalize import normalize_host

EXPECTED_DATA = {
    # Basic cases
    "site.com": "site.com",
    "SITE.COM": "site.com",
    "site.com.": "site.com",
    # Cyrillic domains
    "пример.испытание": "xn--e1afmkfd.xn--80akhbyknj4f",
    # Mixed case with Cyrillic
    "ExAmPle.РФ": "example.xn--p1ai",
    # IDNA2008 with UTS46
    "faß.de": "fass.de",  # Normalize using transitional rules
    # Edge cases
    "ドメイン.テスト": "xn--eckwd4c7c.xn--zckzah",  # Japanese
    "domain.café": "domain.xn--caf-dma",  # Latin with diacritic
    # Normalization tests
    "über.example": "xn--ber-goa.example",  # IDNA 2008 for umlaut
    "example。com": "example.com",  # Normalize full-width punctuation
}


def test_normalize_host_result_is_expected() -> None:
    """Assert we got expected results from the normalize_host function."""
    for url, expected in EXPECTED_DATA.items():
        result = normalize_host(url)
        assert result == expected, url
