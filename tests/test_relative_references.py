"""Explicit relative references retain the context needed for resolution."""

from urllib.parse import urljoin, urlsplit

import pytest

from url_normalize import url_humanize, url_normalize


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    "value",
    [
        ".",
        "..",
        "./",
        "../",
        "./a",
        "../images/a.png",
        "../../a",
        "./this:that",
        "./example.com:8080/a",
        "./?q=1",
        ".?q=1",
        "..?q=1",
        ".#section",
        "..#section",
        "?q=1",
        "?q=../a//b#section",
        "#section",
        "#!/users/42",
        "#:~:text=hello%20world",
        "#?q=1",
    ],
)
def test_explicit_references_stay_relative(transform, value):
    """Retain relative syntax instead of inventing an empty HTTPS authority."""
    result = transform(value)
    assert result == value
    assert not urlsplit(result).scheme
    assert not urlsplit(result).netloc
    assert transform(result) == result
    assert url_normalize(result) == value


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("prefix", [" \x00", "\t\r\n", "\u00a0"])
@pytest.mark.parametrize("value", ["../a", "./a", "?q=1", "#section"])
def test_relative_classification_follows_input_cleanup(transform, prefix, value):
    """Discard parser-ignored controls before detecting explicit references."""
    assert transform(prefix + value) == value


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("collapse_slashes", [False, True])
@pytest.mark.parametrize("remove_trailing_slash", [False, True])
@pytest.mark.parametrize("tail", ["b", "b//c"])
def test_relative_paths_apply_structural_cleanup(
    transform, collapse_slashes, remove_trailing_slash, tail
):
    """Resolve dots before slash cleanup while preserving unresolved parents."""
    value = f"../a//../{tail}///?q=1#section"
    options = {
        "collapse_slashes": collapse_slashes,
        "remove_trailing_slash": remove_trailing_slash,
    }
    expected_tail = tail.replace("//", "/") if collapse_slashes else tail
    path = f"../a/{expected_tail}" + (
        "" if remove_trailing_slash else "/" if collapse_slashes else "///"
    )
    expected = path + "?q=1#section"
    assert transform(value, **options) == expected
    assert transform(expected, **options) == expected
    if collapse_slashes and not remove_trailing_slash:
        assert transform(value) == expected


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("collapse_slashes", [False, True])
@pytest.mark.parametrize(
    ("value", "preserved", "collapsed"),
    [
        ("./a/../b", "./b", "./b"),
        ("../a/./b/../../c", "../c", "../c"),
        ("./a//../b/", "./a/b/", "./a/b/"),
        ("../a///../b", "../a//b", "../a/b"),
        ("./a/..//b", ".//b", "./b"),
        ("./a/..///b", ".///b", "./b"),
        (".///example.com/a", ".///example.com/a", "./example.com/a"),
        (
            "./https://example.com/a",
            "./https://example.com/a",
            "./https:/example.com/a",
        ),
        ("./a/../this:that", "./this:that", "./this:that"),
        ("../a/../../b", "../../b", "../../b"),
        ("./../../a", "../../a", "../../a"),
        ("../../../a/../b", "../../../b", "../../../b"),
        ("./a/%2e%2E/b", "./b", "./b"),
        ("../a%2fb//c///", "../a%2Fb//c///", "../a%2Fb/c/"),
        ("./a/%252e%252e//b", "./a/%252e%252e//b", "./a/%252e%252e/b"),
        ("./a/./", "./a/", "./a/"),
        ("./a/.//", "./a//", "./a/"),
        ("./a//.", "./a//", "./a/"),
        (".././a", "../a", "../a"),
    ],
)
def test_relative_path_boundaries(
    transform, collapse_slashes, value, preserved, collapsed
):
    """Keep parent traversal, relative prefixes and encoded separators distinct."""
    expected = collapsed if collapse_slashes else preserved
    options = {"collapse_slashes": collapse_slashes}
    result = transform(value, **options)
    assert result == expected
    assert transform(result, **options) == expected
    assert url_normalize(result, **options) == expected
    assert not urlsplit(result).scheme
    assert not urlsplit(result).netloc
    assert not urlsplit(result).path.startswith("/")


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("remove_trailing_slash", [False, True])
@pytest.mark.parametrize(
    ("value", "kept", "removed"),
    [
        (".", ".", "."),
        ("..", "..", ".."),
        ("./", "./", "."),
        ("../", "../", ".."),
        ("./a/..", "./", "."),
        ("../a/..", "../", ".."),
        ("./a/../..", "..", ".."),
        ("./..", "..", ".."),
        ("../..", "../..", "../.."),
        ("./.", "./", "."),
        ("../.", "../", ".."),
        ("./a/../.", "./", "."),
        ("./a/../", "./", "."),
        ("../a/../../", "../../", "../.."),
        (".//..", "./", "."),
        ("./a/..//..", "./", "."),
        ("./a/..///..", ".//", "."),
    ],
)
def test_relative_directory_results(
    transform, remove_trailing_slash, value, kept, removed
):
    """Keep a directory reference when dot removal consumes the entire path."""
    options = {
        "collapse_slashes": False,
        "remove_trailing_slash": remove_trailing_slash,
    }
    expected = removed if remove_trailing_slash else kept
    result = transform(value, **options)
    assert result == expected
    assert transform(result, **options) == expected


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("keep_empty_components", [False, True])
@pytest.mark.parametrize("remove_trailing_slash", [False, True])
def test_relative_cleanup_combines_with_display_and_empty_components(
    transform, keep_empty_components, remove_trailing_slash
):
    """Reuse the chosen path policy for humanization and empty delimiters."""
    value = "../a//../%C3%A9///?#"
    options = {
        "collapse_slashes": False,
        "remove_trailing_slash": remove_trailing_slash,
        "keep_empty_components": keep_empty_components,
    }
    segment = "é" if transform is url_humanize else "%C3%A9"
    suffix = ("" if remove_trailing_slash else "///") + (
        "?#" if keep_empty_components else ""
    )
    result = transform(value, **options)
    assert result == f"../a/{segment}{suffix}"
    assert url_normalize(result, **options) == f"../a/%C3%A9{suffix}"


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("value", ["../a", "./a", "?q=1", "#section"])
def test_default_domain_is_not_a_base_url(transform, value):
    """Apply default domains only to root-relative paths as before."""
    assert (
        transform(value, default_domain="example.com", default_scheme="http") == value
    )


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("keep_empty_components", [False, True])
@pytest.mark.parametrize("prefix", ["", ".", "..", "./a", "../a"])
@pytest.mark.parametrize("suffix", ["?", "#", "?#"])
def test_relative_empty_component_policy(
    transform, keep_empty_components, prefix, suffix
):
    """Apply delimiter policy without manufacturing a path or authority."""
    expected = prefix + (suffix if keep_empty_components else "")
    options = {"keep_empty_components": keep_empty_components}
    assert transform(prefix + suffix, **options) == expected
    assert transform(expected, **options) == expected


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("prefix", ["?", "./a?", "../a?"])
@pytest.mark.parametrize("keep_empty_components", [False, True])
def test_relative_query_filtering(transform, prefix, keep_empty_components):
    """Use an explicit allowlist for references that have no host to match."""
    value = prefix + "drop=1&keep=2#section"
    options = {
        "filter_params": True,
        "keep_empty_components": keep_empty_components,
    }
    assert transform(value, param_allowlist=["keep"], **options) == (
        prefix + "keep=2#section"
    )
    expected = prefix if keep_empty_components else prefix[:-1]
    assert transform(value, param_allowlist=[], **options) == expected + "#section"


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    ("value", "normalized", "humanized"),
    [
        ("../é", "../%C3%A9", "../é"),
        ("./a%2fb/%zz", "./a%2Fb/%25zz", "./a%2Fb/%25zz"),
        ("../a%3fb%23c", "../a%3Fb%23c", "../a%3Fb%23c"),
        ("./a/%2e%2e/b", "./b", "./b"),
        ("../%E2%80%AE", "../%E2%80%AE", "../%E2%80%AE"),
        ("?q=é", "?q=%C3%A9", "?q=é"),
        ("#é%2Dtest", "#%C3%A9%2Dtest", "#é%2Dtest"),
    ],
)
def test_relative_component_normalization(transform, value, normalized, humanized):
    """Normalize text while retaining encoded separators and display safeguards."""
    expected = humanized if transform is url_humanize else normalized
    result = transform(value)
    assert result == expected
    assert transform(result) == expected
    assert url_normalize(result) == normalized


@pytest.mark.parametrize(
    ("reference", "resolved"),
    [
        ("../g", "https://example.com/a/g"),
        ("./g", "https://example.com/a/b/g"),
        (".", "https://example.com/a/b/"),
        ("..", "https://example.com/a/"),
        ("./g/../h", "https://example.com/a/b/h"),
        ("?y", "https://example.com/a/b/page?y"),
        ("#s", "https://example.com/a/b/page?q=1#s"),
    ],
)
def test_relative_references_resolve_against_the_original_base(reference, resolved):
    """Retain RFC 3986 section 5.4 resolution semantics for these text examples."""
    base = "https://example.com/a/b/page?q=1"
    assert urljoin(base, reference) == resolved
    assert urljoin(base, url_normalize(reference)) == resolved
    assert url_normalize(urljoin(base, reference)) == resolved


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        ("./a/..//b", "https://example.com/one/two//b"),
        (".///example.com/a", "https://example.com/one/two///example.com/a"),
        ("../a//../b", "https://example.com/one/a/b"),
        ("../../../../a/../b", "https://example.com/b"),
        ("./a/../this:that", "https://example.com/one/two/this:that"),
        ("./a/..///..", "https://example.com/one/two//"),
    ],
)
def test_relative_dot_cleanup_retains_the_resolved_target(reference, expected):
    """Preserve resolution through empty segments, parent traversal and prefixes."""
    base_directory = "https://example.com/one/two/"
    normalized = url_normalize(reference, collapse_slashes=False)
    assert url_normalize(base_directory + reference, collapse_slashes=False) == expected
    assert (
        url_normalize(base_directory + normalized, collapse_slashes=False) == expected
    )


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("example.com/page", "https://example.com/page"),
        ("site/page", "https://site/page"),
        ("localhost:8080/page", "https://localhost:8080/page"),
        ("./.example.com/page", "./.example.com/page"),
        (".example.com/page", "https://.example.com/page"),
        ("//example.com/a/../b", "https://example.com/b"),
        ("/a/../b", "/b"),
        ("custom:../a", "custom:../a"),
        ("-", "-"),
    ],
)
def test_relative_detection_preserves_existing_input_categories(
    transform, value, expected
):
    """Keep bare-host inference, root paths, custom schemes and the dash marker."""
    assert transform(value) == expected
