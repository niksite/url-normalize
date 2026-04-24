"""Tests for URL humanization."""

from __future__ import annotations

import pytest

import url_normalize as package


@pytest.mark.parametrize(
    ("normalized", "expected"),
    [
        (
            "https://xn--e1afmkfd.xn--80akhbyknj4f/"
            "%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F:Search/Test",
            "https://пример.испытание/Служебная:Search/Test",
        ),
        (
            "https://xn--fa-hia.de/%C3%BCber?q=%C3%87#%D0%BF%D1%80%D0%B8%D0%BC%D0%B5%D1%80",
            "https://faß.de/über?q=Ç#пример",
        ),
        (
            "https://example.com/?q=%23test&where=code%3D123",
            "https://example.com/?q=%23test&where=code=123",
        ),
    ],
)
def test_url_humanize_returns_readable_url_that_normalizes_back(
    normalized: str,
    expected: str,
) -> None:
    """Assert humanized URLs are readable without changing normalized meaning."""
    humanized = package.url_humanize(normalized)

    assert humanized == expected
    assert package.url_normalize(humanized) == normalized


@pytest.mark.parametrize("value", ["", None])
def test_url_humanize_preserves_empty_values(value: str | None) -> None:
    """Assert empty inputs match url_normalize behavior."""
    assert package.url_humanize(value) == value


@pytest.mark.parametrize(
    "value",
    [
        (
            "https://xn--e1afmkfd.xn--80akhbyknj4f/"
            "%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F:Search/Test"
        ),
        "https://faß.de/über?q=Ç#пример",
        "https://example.com/a%2Fb?equals=a%3Db&letter=%C3%87#%D1%84",
        "https://example.com/?hash=%23test&amp=a%26b&query=a%3Fb",
    ],
)
def test_url_humanize_round_trips_to_normalized_url(value: str) -> None:
    """Assert humanization never changes the canonical normalized URL."""
    humanized = package.url_humanize(value)

    assert package.url_normalize(humanized) == package.url_normalize(value)


def test_url_humanize_accepts_url_normalize_options() -> None:
    """Assert humanization can be combined with normalizer options."""
    humanized = package.url_humanize(
        "/%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F"
        "?utm_source=ignored&keep=%C3%87",
        default_domain="xn--e1afmkfd.xn--80akhbyknj4f",
        filter_params=True,
        param_allowlist=["keep"],
    )

    assert humanized == "https://пример.испытание/Служебная?keep=Ç"


def test_url_humanize_keeps_query_delimiters_encoded() -> None:
    """Assert humanization does not expose encoded query separators."""
    normalized = "https://example.com/?hash=%23test&amp=a%26b&key%3Dpart=value"

    assert package.url_humanize(normalized) == normalized


def test_url_humanize_decodes_safe_query_parts_independently() -> None:
    """Assert safe query key and value decoding is applied per component."""
    normalized = (
        "https://example.com/?letter=%C3%87&equals=a%3Db&%D0%BA%D0%BB%D1%8E%D1%87=value"
    )

    assert (
        package.url_humanize(normalized)
        == "https://example.com/?letter=Ç&equals=a=b&ключ=value"
    )


def test_url_humanize_keeps_malformed_percent_encoding_normalized() -> None:
    """Assert malformed UTF-8 escapes are not rendered with replacement text."""
    value = "https://example.com/%E0%A4%A?bad=%E0%A4%A#%E0%A4%A"
    normalized = package.url_normalize(value)

    assert package.url_humanize(value) == normalized


def test_url_humanize_documents_encoded_slash_normalization() -> None:
    """Assert encoded slashes follow url_normalize path semantics."""
    value = "https://example.com/a%2Fb"
    humanized = package.url_humanize(value)

    assert humanized == "https://example.com/a/b"
    assert package.url_normalize(humanized) == package.url_normalize(value)
