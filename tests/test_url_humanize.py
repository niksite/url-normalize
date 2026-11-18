"""Tests for URL humanization."""

from __future__ import annotations

from unittest.mock import patch
from urllib.parse import quote

import pytest

import url_normalize as package


@pytest.mark.parametrize(
    ("normalized", "expected"),
    [
        (
            (
                "https://xn--e1afmkfd.xn--80akhbyknj4f/"
                "%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F:Search/Test"
            ),
            "https://пример.испытание/Служебная:Search/Test",
        ),
        (
            "https://xn--fa-hia.de/%C3%BCber?q=%C3%87#%D0%BF%D1%80%D0%B8%D0%BC%D0%B5%D1%80",
            "https://faß.de/über?q=Ç#пример",
        ),
        (
            "https://example.com/?q=%23test&where=code%3D123",
            "https://example.com/?q=%23test&where=code%3D123",
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


@pytest.mark.parametrize("param_count", [0, 25, 200])
def test_url_humanize_readable_url_needs_one_normalization(param_count):
    """Keep whole-URL normalization cost constant for already-readable queries."""
    value = "https://example.com/path"
    if param_count:
        value += "?" + "&".join(f"key{i}=value{i}" for i in range(param_count))

    with patch(
        "url_normalize.url_humanize.url_normalize", wraps=package.url_normalize
    ) as normalize:
        assert package.url_humanize(value) == value

    assert normalize.call_count == 1


def test_url_humanize_only_rechecks_changed_query_values():
    """Validate a decoded value without rechecking every unchanged field."""
    expected_normalizations = 2  # Initial normalization and one round trip.
    query = "&".join(f"key{i}=value{i}" for i in range(100))
    value = f"https://example.com/path?{query}&title=%C3%A9"
    expected = f"https://example.com/path?{query}&title=é"

    with patch(
        "url_normalize.url_humanize.url_normalize", wraps=package.url_normalize
    ) as normalize:
        assert package.url_humanize(value) == expected

    assert normalize.call_count == expected_normalizations


@pytest.mark.parametrize("param_count", [2, 100])
@pytest.mark.parametrize("prefix", ["", "keep=%2541&"])
def test_url_humanize_checks_readable_query_changes_together(param_count, prefix):
    """Bound whole-URL work as the number of decodable keys and values grows."""
    value = f"https://example.com/search?{prefix}" + "&".join(
        f"%C3%A9{i}=%E4%B8%AD" for i in range(param_count)
    )
    expected = f"https://example.com/search?{prefix}" + "&".join(
        f"é{i}=中" for i in range(param_count)
    )
    max_normalizations = 2  # Initial normalization plus one combined round trip.
    with patch(
        "url_normalize.url_humanize.url_normalize", wraps=package.url_normalize
    ) as normalize:
        assert package.url_humanize(value) == expected

    assert normalize.call_count <= max_normalizations


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("bad=%2541&ok=%C3%A9&ok=%E4%B8%AD", "bad=%2541&ok=é&ok=中"),
        ("%2541=%C3%A9&%E4%B8%AD=%2542", "%2541=é&中=%2542"),
    ],
)
def test_url_humanize_failed_combined_query_keeps_independent_decoding(query, expected):
    """A rejected percent escape must not block other readable keys or values."""
    value = f"https://example.com/search?{query}"
    humanized = package.url_humanize(value)
    assert humanized == f"https://example.com/search?{expected}"
    assert package.url_normalize(humanized) == value


def test_url_humanize_combined_query_preserves_selected_policies():
    """Keep duplicate order, flags, reserved escapes and path/fragment policies."""
    value = "../a//b?tag=%C3%A9%2F&drop=1&tag=%E4%B8%AD&flag=&flag#"
    expected = "../a//b?tag=é%2F&tag=中&flag=&flag#"
    assert (
        package.url_humanize(
            value,
            collapse_slashes=False,
            keep_empty_components=True,
            filter_params=True,
            param_allowlist=["tag", "flag"],
        )
        == expected
    )


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
        == "https://example.com/?letter=Ç&equals=a%3Db&ключ=value"
    )


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("%C3%A9%2f%C3%B1=%C3%A9%3b%C3%B1", "é%2Fñ=é%3Bñ"),
        ("q=%C3%A9%3d%26%23%3f%40%5b%5d", "q=é%3D%26%23%3F%40%5B%5D"),
        ("q=%C3%A9%21%24%27%28%29%2a%2b%2c%3a", "q=é%21%24%27%28%29%2A%2B%2C%3A"),
        ("q=%C3%A9%20test%2F&x=%E2%80%AE%2F", "q=é test%2F&x=%E2%80%AE%2F"),
        ("q=%C3%A9%2F%FF", "q=é%2F%FF"),
    ],
)
def test_url_humanize_decodes_text_around_reserved_query_escapes(query, expected):
    """Expose readable Unicode without turning encoded punctuation into syntax."""
    value = f"https://example.com/?{query}"
    humanized = package.url_humanize(value)
    assert humanized == f"https://example.com/?{expected}"
    assert package.url_normalize(humanized) == package.url_normalize(value)
    assert package.url_humanize(humanized) == humanized


def test_url_humanize_keeps_malformed_percent_encoding_normalized() -> None:
    """Assert malformed UTF-8 escapes are not rendered with replacement text."""
    value = "https://example.com/%E0%A4%A?bad=%E0%A4%A#%E0%A4%A"
    normalized = package.url_normalize(value)

    assert package.url_humanize(value) == normalized


def test_url_humanize_preserves_encoded_slash() -> None:
    """Keep encoded slashes distinct from path segment boundaries."""
    value = "https://example.com/a%2Fb"
    humanized = package.url_humanize(value)

    assert humanized == value
    assert package.url_normalize(humanized) == package.url_normalize(value)


def test_url_humanize_handles_idna_error() -> None:
    """Assert IDNA decoding fallback gracefully handles bad IDNA labels."""
    value = "https://xn--bad-label.com/"
    assert package.url_humanize(value) == "https://xn--bad-label.com/"


def test_url_humanize_skips_failed_round_trip() -> None:
    """Assert parts that break round-trip normalizations are kept as is."""
    value = "https://example.com/a%3Fb"
    assert package.url_humanize(value) == value


@pytest.mark.parametrize(
    "userinfo",
    [
        "user%5B",
        "user%5D",
        "user:%5B",
        "user:%5D",
        "us%EF%BC%A0er",
        "user:p%EF%BC%9Ass",
    ],
)
def test_url_humanize_keeps_escaped_authority_syntax(userinfo):
    """Keep bracket escapes and reject Unicode decodes that break authority parsing."""
    value = f"https://{userinfo}@example.com/"
    assert package.url_humanize(value) == value
    assert package.url_normalize(package.url_humanize(value)) == value


@pytest.mark.parametrize(
    "component",
    ["/{value}", "/?{value}=x", "/?q={value}", "/#{value}", "//{value}@example.com/"],
)
@pytest.mark.parametrize(
    "escaped", ["%00", "%09", "%0A", "%0D", "%1B", "%7F", "%C2%85"]
)
def test_url_humanize_keeps_control_characters_encoded(component, escaped):
    """Keep C0, DEL, and C1 controls encoded in every humanized component."""
    suffix = component.format(value=f"a{escaped}b")
    value = (
        f"https:{suffix}" if suffix.startswith("//") else f"https://example.com{suffix}"
    )
    assert package.url_humanize(value) == value


@pytest.mark.parametrize("literal_input", [False, True], ids=["escaped", "literal"])
@pytest.mark.parametrize(
    "template",
    [
        "https://example.com/a{value}b",
        "https://example.com/?a{value}b=x",
        "https://example.com/?q=a{value}b",
        "https://example.com/#a{value}b",
        "https://a{value}b@example.com/",
        "https://user:a{value}b@example.com/",
    ],
    ids=["path", "query-key", "query-value", "fragment", "username", "password"],
)
@pytest.mark.parametrize(
    ("character", "escaped"),
    [
        pytest.param("\u061c", "%D8%9C", id="arabic-letter-mark"),
        pytest.param("\u200e", "%E2%80%8E", id="left-to-right-mark"),
        pytest.param("\u200f", "%E2%80%8F", id="right-to-left-mark"),
        pytest.param("\u202a", "%E2%80%AA", id="left-to-right-embedding"),
        pytest.param("\u202b", "%E2%80%AB", id="right-to-left-embedding"),
        pytest.param("\u202c", "%E2%80%AC", id="pop-directional-formatting"),
        pytest.param("\u202d", "%E2%80%AD", id="left-to-right-override"),
        pytest.param("\u202e", "%E2%80%AE", id="right-to-left-override"),
        pytest.param("\u2066", "%E2%81%A6", id="left-to-right-isolate"),
        pytest.param("\u2067", "%E2%81%A7", id="right-to-left-isolate"),
        pytest.param("\u2068", "%E2%81%A8", id="first-strong-isolate"),
        pytest.param("\u2069", "%E2%81%A9", id="pop-directional-isolate"),
        pytest.param("\u2028", "%E2%80%A8", id="line-separator"),
        pytest.param("\u2029", "%E2%80%A9", id="paragraph-separator"),
    ],
)
def test_url_humanize_keeps_display_controls_encoded(
    character, escaped, template, literal_input
):
    """Keep bidi controls and Unicode line breaks encoded in display URLs."""
    value = template.format(value=character if literal_input else escaped)
    expected = template.format(value=escaped)

    humanized = package.url_humanize(value)

    assert humanized == expected
    assert character not in humanized
    assert package.url_normalize(humanized) == package.url_normalize(value)


@pytest.mark.parametrize(
    "text",
    ["שלום", "مرحبا", "می\u200cروم", "👩\u200d💻"],
    ids=["hebrew", "arabic", "persian-non-joiner", "emoji-joiner"],
)
def test_url_humanize_preserves_readable_multilingual_text(text):
    """Decode ordinary RTL text and join controls used for text shaping."""
    value = f"https://example.com/{quote(text)}"

    assert package.url_humanize(value) == f"https://example.com/{text}"


@pytest.mark.parametrize("scheme", ["http", "https", "ftp"])
@pytest.mark.parametrize(
    "suffix",
    [
        "//evil.example%5C@trusted.example/",
        "//name:evil.example%5C@trusted.example/",
        "//trusted.example/a%5Cb",
        "//trusted.example/?a%5Cb=x",
        "//trusted.example/?q=a%5Cb",
        "//trusted.example/#a%5Cb",
    ],
)
def test_url_humanize_keeps_backslashes_encoded(scheme, suffix):
    """Keep backslashes encoded because browsers can treat them as separators."""
    value = f"{scheme}:{suffix}"
    assert package.url_humanize(value) == value
    assert package.url_normalize(package.url_humanize(value)) == value
