"""Public contracts for absent and present-empty URL components."""

import pytest

from url_normalize import url_humanize, url_normalize


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("keep_empty_components", [False, True])
@pytest.mark.parametrize(
    ("suffix", "cleaned"),
    [
        ("", ""),
        ("?", ""),
        ("#", ""),
        ("?#", ""),
        ("?q=1#", "?q=1"),
        ("?#end", "#end"),
        ("#?", "#?"),
        ("?q=%23#", "?q=%23"),
        ("?flag=", "?flag="),
        ("?flag=&flag", "?flag=&flag"),
    ],
)
def test_public_api_empty_component_policy(
    transform, suffix, cleaned, keep_empty_components
):
    """Distinguish absent, empty and populated components under either policy."""
    base = "https://example.com/"
    value = base + suffix
    expected = base + (suffix if keep_empty_components else cleaned)
    options = {"keep_empty_components": keep_empty_components}

    assert transform(value, **options) == expected
    assert transform(expected, **options) == expected
    assert url_normalize(url_humanize(value, **options), **options) == expected
    if not keep_empty_components:
        assert transform(value) == expected


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("keep_empty_components", [False, True])
@pytest.mark.parametrize(
    "base",
    [
        "ws://[::1]/",
        "file:///tmp/document",
        "sqlite:///notes.db",
        "sqlite:////tmp/notes.db",
        "unix:///tmp/service.sock",
        "unix:/tmp/service.sock",
        "custom://",
        "custom:",
        "mailto:user@example.com",
        "urn:example:document",
        "/path",
    ],
)
def test_empty_component_policy_across_url_forms(
    transform, base, keep_empty_components
):
    """Apply delimiter policy to authority, file, opaque and path-only URLs."""
    expected = base + ("?#" if keep_empty_components else "")

    assert (
        transform(base + "?#", keep_empty_components=keep_empty_components) == expected
    )
    if not keep_empty_components:
        assert transform(base + "?#") == expected


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("keep_empty_components", [False, True])
@pytest.mark.parametrize(
    ("suffix", "cleaned"),
    [("?", ""), ("#", ""), ("?#", ""), ("?q=1#", "?q=1"), ("?#end", "#end")],
)
def test_component_presence_with_other_normalization(
    transform, suffix, cleaned, keep_empty_components
):
    """Apply the chosen delimiter policy while normalizing authority and path text."""
    value = f"HTTP://User@EXAMPLE.COM:080/a/../%C3%A9{suffix}"
    path = "é" if transform is url_humanize else "%C3%A9"
    expected_suffix = suffix if keep_empty_components else cleaned

    assert transform(value, keep_empty_components=keep_empty_components) == (
        f"http://User@example.com/{path}{expected_suffix}"
    )


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("keep_empty_components", [False, True])
@pytest.mark.parametrize("suffix", ["?", "#", "?#"])
def test_component_presence_with_domain_and_path_options(
    transform, suffix, keep_empty_components
):
    """Apply the delimiter policy when adding a domain and cleaning path slashes."""
    result = transform(
        f"/a//b///{suffix}",
        default_domain="example.com",
        default_scheme="http",
        collapse_slashes=True,
        remove_trailing_slash=True,
        keep_empty_components=keep_empty_components,
    )

    expected_suffix = suffix if keep_empty_components else ""
    assert result == f"http://example.com/a/b{expected_suffix}"


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("keep_empty_components", [False, True])
@pytest.mark.parametrize(
    ("suffix", "cleaned", "kept"),
    [
        ("", "", ""),
        ("?", "", "?"),
        ("#", "", "#"),
        ("?#", "", "?#"),
        ("?drop=1", "", "?"),
        ("?drop=1#", "", "?#"),
        ("?drop=1#section", "#section", "?#section"),
        ("?keep=&drop=x#", "?keep=", "?keep=#"),
        ("?keep&drop=x?", "?keep", "?keep"),
        ("?drop=1&keep=2&keep=3#", "?keep=2&keep=3", "?keep=2&keep=3#"),
        ("?&&", "", "?"),
        ("?&&#", "", "?#"),
    ],
)
def test_query_filtering_uses_empty_component_policy(
    transform, suffix, cleaned, kept, keep_empty_components
):
    """Keep or drop an emptied query according to the selected delimiter policy."""
    base = "https://example.com/"
    options = {
        "param_allowlist": ["keep"],
        "keep_empty_components": keep_empty_components,
    }
    expected = kept if keep_empty_components else cleaned

    result = transform(base + suffix, **options)

    assert result == base + expected
    assert transform(result, **options) == result


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("keep_empty_components", [False, True])
@pytest.mark.parametrize(
    ("suffix", "cleaned", "kept"),
    [
        ("?&&", "", "?"),
        ("?&&#", "", "?#"),
        ("?&a&&b&#", "?a&b", "?a&b#"),
        (
            "?&&flag&empty=&q=a%26b&#part&&?",
            "?flag&empty=&q=a%26b#part&&?",
            "?flag&empty=&q=a%26b#part&&?",
        ),
    ],
)
def test_empty_field_cleanup_uses_component_policy(
    transform, suffix, cleaned, kept, keep_empty_components
):
    """Apply delimiter policy independently of existing empty-field cleanup."""
    expected = kept if keep_empty_components else cleaned
    assert (
        transform(
            f"https://example.com/{suffix}", keep_empty_components=keep_empty_components
        )
        == f"https://example.com/{expected}"
    )


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("keep_empty_components", [False, True])
@pytest.mark.parametrize("suffix", ["%3F", "%23", "%3F%23", "#%3F", "#x?y"])
def test_encoded_delimiters_and_fragment_data_do_not_create_a_query(
    transform, suffix, keep_empty_components
):
    """Keep encoded path separators and question marks after the fragment boundary."""
    value = f"https://example.com/{suffix}"

    assert transform(value, keep_empty_components=keep_empty_components) == value


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("keep_empty_components", [False, True])
@pytest.mark.parametrize("value", ["", None])
def test_empty_component_policy_preserves_empty_input(
    transform, value, keep_empty_components
):
    """Keep the existing empty-input contract with either delimiter policy."""
    assert transform(value, keep_empty_components=keep_empty_components) == value


@pytest.mark.parametrize("keep_empty_components", [False, True])
@pytest.mark.parametrize(
    ("suffix", "cleaned", "kept"),
    [("?x=%C3%A9#", "?x=é", "?x=é#"), ("?#%C3%A9", "#é", "?#é")],
)
def test_humanization_uses_component_policy_for_every_candidate(
    suffix, cleaned, kept, keep_empty_components
):
    """Decode all display components using the same policy as initial normalization."""
    value = f"https://us%C3%A9r@xn--bcher-kva.de/%C3%A9{suffix}"
    expected_suffix = kept if keep_empty_components else cleaned

    result = url_humanize(value, keep_empty_components=keep_empty_components)

    assert result == f"https://usér@bücher.de/é{expected_suffix}"
