"""Public path policy checks shared by normalization and humanization."""

from urllib.parse import urlsplit

import pytest

from url_normalize import url_humanize, url_normalize


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
def test_default_path_policy_preserves_slashes(transform):
    """Keep empty segments when the caller supplies no path option."""
    value = "https://example.com/a//b///"
    assert transform(value) == value


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
    """Preserve empty path segments unless the caller opts into collapsing."""
    expected = collapsed if collapse_slashes else preserved
    result = transform(value, collapse_slashes=collapse_slashes)
    assert result == expected
    assert transform(result, collapse_slashes=collapse_slashes) == expected
    assert url_normalize(result, collapse_slashes=collapse_slashes) == expected


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("value", [None, ""])
def test_path_policy_preserves_empty_input(transform, value):
    """Keep the established empty-input contract with the new option."""
    assert transform(value, collapse_slashes=True) == value


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("collapse_slashes", [False, True])
@pytest.mark.parametrize(
    "value",
    ["mailto:a//../b", "custom:a//../b", "custom://example.com/a//../b"],
)
def test_path_policy_leaves_other_schemes_alone(transform, collapse_slashes, value):
    """Keep path cleanup scoped to schemes with a defined policy."""
    assert transform(value, collapse_slashes=collapse_slashes) == value


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
def test_path_policy_changes_only_the_path(transform):
    """Keep credentials, query and fragment at their baseline normalized values."""
    value = "https://User:PaSS@bücher.de:8443/a//b//?q=a//b#c//d"
    baseline = urlsplit(transform(value))
    collapsed = urlsplit(transform(value, collapse_slashes=True))
    assert collapsed.path == "/a/b/"
    assert collapsed._replace(path=baseline.path) == baseline


@pytest.mark.parametrize("transform", [url_normalize, url_humanize])
@pytest.mark.parametrize("collapse_slashes", [False, True])
def test_path_policy_combines_with_existing_options(transform, collapse_slashes):
    """Apply the same path policy when adding a domain and filtering queries."""
    value = "/a//é///?keep=é&drop=2"
    expected_path = "/a/é/" if collapse_slashes else "/a//é///"
    if transform is url_normalize:
        expected_path = expected_path.replace("é", "%C3%A9")
    expected_query = "keep=é" if transform is url_humanize else "keep=%C3%A9"
    options = {
        "default_domain": "example.com",
        "default_scheme": "http",
        "filter_params": True,
        "param_allowlist": ["keep"],
        "collapse_slashes": collapse_slashes,
    }
    result = transform(value, **options)
    assert result == f"http://example.com{expected_path}?{expected_query}"
    assert url_normalize(result, **options) == url_normalize(value, **options)
