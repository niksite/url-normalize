"""Public path policy checks shared by normalization and humanization."""

from urllib.parse import urlsplit

import pytest

from url_normalize import url_humanize, url_normalize


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
def test_default_path_policy_collapses_slashes(transform):
    """Collapse literal slash runs when the caller supplies no path option."""
    value = "https://example.com/a//b///"
    expected = "https://example.com/a/b/"
    assert transform(value) == expected
    assert transform(value, remove_trailing_slash=False) == expected
    assert transform(value, collapse_slashes=False) == value


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("collapse_slashes", [False, True])
@pytest.mark.parametrize(
    ("value", "preserved", "collapsed"),
    [
        (
            "https://EXAMPLE.com/a//b///",
            "https://example.com/a//b///",
            "https://example.com/a/b/",
        ),
        (
            "https://example.com/a//../b",
            "https://example.com/a/b",
            "https://example.com/a/b",
        ),
        (
            "https://example.com/a/..//b",
            "https://example.com//b",
            "https://example.com/b",
        ),
        (
            "WS://Example.COM:80/a///../b",
            "ws://example.com/a//b",
            "ws://example.com/a/b",
        ),
        (
            "wss://[2001:DB8::1]:443/a/./b",
            "wss://[2001:db8::1]/a/b",
            "wss://[2001:db8::1]/a/b",
        ),
        (
            "https://example.com/a%2f//b?q=a//b",
            "https://example.com/a%2F//b?q=a//b",
            "https://example.com/a%2F/b?q=a//b",
        ),
        ("file:///a/..//b", "file:////b", "file:///b"),
        ("/a/..//b", "/.//b", "/b"),
        ("/a//b///", "/a//b///", "/a/b/"),
    ],
)
def test_public_path_policy(transform, collapse_slashes, value, preserved, collapsed):
    """Collapse by default and retain empty segments when explicitly disabled."""
    expected = collapsed if collapse_slashes else preserved
    result = transform(value, collapse_slashes=collapse_slashes)
    assert result == expected
    assert transform(result, collapse_slashes=collapse_slashes) == expected
    assert url_normalize(result, collapse_slashes=collapse_slashes) == expected
    if collapse_slashes:
        assert transform(value) == expected


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("collapse_slashes", [False, True])
@pytest.mark.parametrize(
    ("value", "preserved", "collapsed"),
    [
        ("https://example.com/a/", "https://example.com/a", "https://example.com/a"),
        ("https://example.com/a///", "https://example.com/a", "https://example.com/a"),
        (
            "https://example.com/a//b///",
            "https://example.com/a//b",
            "https://example.com/a/b",
        ),
        ("https://example.com", "https://example.com/", "https://example.com/"),
        ("https://example.com///", "https://example.com/", "https://example.com/"),
        (
            "https://example.com/a//../b///",
            "https://example.com/a/b",
            "https://example.com/a/b",
        ),
        (
            "https://example.com/a%2f/",
            "https://example.com/a%2F",
            "https://example.com/a%2F",
        ),
        (
            "https://example.com/a%2f",
            "https://example.com/a%2F",
            "https://example.com/a%2F",
        ),
        ("WS://Example.COM:80/a/", "ws://example.com/a", "ws://example.com/a"),
        ("wss://example.com/", "wss://example.com/", "wss://example.com/"),
        ("ftp://example.com/a/", "ftp://example.com/a", "ftp://example.com/a"),
        ("file:///a/", "file:///a", "file:///a"),
        ("/a/..//b///", "/.//b", "/b"),
        ("/a/../", "/", "/"),
    ],
)
def test_public_trailing_slash_policy(
    transform, collapse_slashes, value, preserved, collapsed
):
    """Remove trailing runs independently of internal slash collapsing."""
    expected = collapsed if collapse_slashes else preserved
    options = {"collapse_slashes": collapse_slashes, "remove_trailing_slash": True}
    result = transform(value, **options)
    assert result == expected
    assert transform(result, **options) == expected
    assert url_normalize(result, **options) == expected


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("value", [None, ""])
def test_path_policy_preserves_empty_input(transform, value):
    """Keep the established empty-input contract with the new option."""
    assert transform(value, collapse_slashes=True, remove_trailing_slash=True) == value


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("collapse_slashes", [False, True])
@pytest.mark.parametrize("remove_trailing_slash", [False, True])
@pytest.mark.parametrize(
    "value",
    ["mailto:a//../b/", "custom:a//../b/", "custom://example.com/a//../b/"],
)
def test_path_policy_leaves_other_schemes_alone(
    transform, collapse_slashes, remove_trailing_slash, value
):
    """Keep path cleanup scoped to schemes with a defined policy."""
    assert transform(value) == value
    assert (
        transform(
            value,
            collapse_slashes=collapse_slashes,
            remove_trailing_slash=remove_trailing_slash,
        )
        == value
    )


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize(
    ("collapse_slashes", "remove_trailing_slash", "expected_path"),
    [(True, False, "/a/b/"), (False, True, "/a//b"), (True, True, "/a/b")],
)
def test_path_policy_changes_only_the_path(
    transform, collapse_slashes, remove_trailing_slash, expected_path
):
    """Keep credentials, query and fragment at their baseline normalized values."""
    value = "https://User:PaSS@bücher.de:8443/a//b//?q=a//b#c//d"
    baseline = urlsplit(transform(value))
    result = urlsplit(
        transform(
            value,
            collapse_slashes=collapse_slashes,
            remove_trailing_slash=remove_trailing_slash,
        )
    )
    assert result.path == expected_path
    assert result._replace(path=baseline.path) == baseline


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("collapse_slashes", [False, True])
@pytest.mark.parametrize("remove_trailing_slash", [False, True])
def test_path_policy_combines_with_existing_options(
    transform, collapse_slashes, remove_trailing_slash
):
    """Apply the same path policy when adding a domain and filtering queries."""
    value = "/a//é///?keep=é&drop=2"
    expected_path = {
        (False, False): "/a//é///",
        (True, False): "/a/é/",
        (False, True): "/a//é",
        (True, True): "/a/é",
    }[collapse_slashes, remove_trailing_slash]
    if transform is url_normalize:
        expected_path = expected_path.replace("é", "%C3%A9")
    expected_query = "keep=é" if transform is url_humanize else "keep=%C3%A9"
    options = {
        "default_domain": "example.com",
        "default_scheme": "http",
        "filter_params": True,
        "param_allowlist": ["keep"],
        "collapse_slashes": collapse_slashes,
        "remove_trailing_slash": remove_trailing_slash,
    }
    result = transform(value, **options)
    assert result == f"http://example.com{expected_path}?{expected_query}"
    assert url_normalize(result, **options) == url_normalize(value, **options)


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
def test_preservation_options_combine_with_humanization(transform):
    """Preserve slashes and empty components while rendering safe Unicode."""
    value = "https://xn--bcher-kva.de/a//%C3%A9///?#"
    host, segment = (
        ("bücher.de", "é")
        if transform is url_humanize
        else ("xn--bcher-kva.de", "%C3%A9")
    )
    options = {"collapse_slashes": False, "keep_empty_components": True}

    result = transform(value, **options)

    assert result == f"https://{host}/a//{segment}///?#"
    assert url_normalize(result, **options) == value
