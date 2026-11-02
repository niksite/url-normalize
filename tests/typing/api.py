"""Check the public return-type contract through the package exports with ty."""

from typing import assert_type

from url_normalize import url_humanize, url_normalize


class URLText(str):
    """Represent a caller's string subclass without promising subtype preservation."""

    __slots__ = ()


def check_return_types(value: str, optional: str | None, subclass: URLText) -> None:
    """Infer results from the input type, including unresolved optional values."""
    assert_type(url_normalize(value), str)
    assert_type(url_humanize(value), str)
    assert_type(url_normalize(None), None)
    assert_type(url_humanize(None), None)
    assert_type(url_normalize(optional), str | None)
    assert_type(url_humanize(optional), str | None)
    assert_type(url_normalize(subclass), str)
    assert_type(url_humanize(subclass), str)
    assert_type(url_normalize(""), str)
    assert_type(url_humanize(""), str)
    assert_type(url_normalize("#section", strip_fragment=True), str)
    assert_type(url_humanize("#section", strip_fragment=True), str)
    # Ordinary string consumers should not need a redundant None check or cast.
    assert_type(url_normalize(value).startswith("https://"), bool)
    assert_type(url_humanize(value).startswith("https://"), bool)


def check_options(value: str | None) -> None:
    """Keep every keyword available while resolving overloaded return types."""
    assert_type(
        url_normalize(
            value,
            default_scheme="https",
            default_domain="example.com",
            filter_params=False,
            param_allowlist={"example.com": ["a", "b"]},
            param_denylist="b",
            remove_tracking_params=True,
            sort_query=True,
            collapse_slashes=False,
            remove_trailing_slash=True,
            keep_empty_components=True,
            strip_fragment=True,
        ),
        str | None,
    )
    assert_type(
        url_humanize(
            value,
            default_scheme="https",
            default_domain="example.com",
            filter_params=False,
            param_allowlist="a",
            param_denylist={"example.com": ["b"]},
            remove_tracking_params=True,
            sort_query=True,
            collapse_slashes=False,
            remove_trailing_slash=True,
            keep_empty_components=True,
            strip_fragment=True,
        ),
        str | None,
    )


def check_narrowed_input(value: str | None) -> None:
    """Follow ordinary caller narrowing through both branches."""
    if value is None:
        assert_type(url_normalize(url=value), None)
        assert_type(url_humanize(url=value), None)
    else:
        assert_type(url_normalize(url=value), str)
        assert_type(url_humanize(url=value), str)
