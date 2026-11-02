"""Generated HTTP(S) and explicit-reference checks, alongside exact examples."""

from string import ascii_letters, digits
from urllib.parse import urlsplit

from hypothesis import given, settings
from hypothesis import strategies as st

from url_normalize import url_humanize, url_normalize

PROPERTY_SETTINGS = settings(
    max_examples=200, derandomize=True, deadline=None, suppress_health_check=()
)

TEXT = st.text(alphabet=ascii_letters + digits + "-._~+é中\u0301", max_size=12)
ESCAPES = st.sampled_from(
    [
        "%2f",
        "%3b",
        "%3F",
        "%5C",
        "%25",
        "%26",
        "%3D",
        "%2B",
        "%20",
        "%E9",
        "%zz",
        "%%41",
        "%2%45",
    ]
)
COMPONENT_TEXT = st.lists(st.one_of(TEXT, ESCAPES), max_size=3).map("".join)
PATH_SEGMENT = st.one_of(st.sampled_from(["", ".", ".."]), COMPONENT_TEXT)
QUERY_FIELD = st.one_of(
    COMPONENT_TEXT,
    st.builds(lambda key, value: f"{key}={value}", COMPONENT_TEXT, COMPONENT_TEXT),
)
FRAGMENT_TEXT = st.one_of(
    COMPONENT_TEXT,
    st.sampled_from(
        [
            "!/route?x=1&x=2",
            "/a//../b",
            ":~:text=prefix-,start,end,-suffix",
            ":~:text=%C3%A9%2Dtest%2C%26text=second",
            "%3A~%3Atext=hello",
            ":%7e:text=hello",
            ":~:te%78t=hello",  # codespell:ignore te
            ":~:text%3dhello",
            ":~:text=%252D%252C%2526",
        ]
    ),
)


@st.composite
def http_urls(draw):
    """Compose URLs from valid authorities and bounded component spellings."""
    scheme = draw(st.sampled_from(["http", "https"]))
    host = draw(
        st.sampled_from(
            [
                "example.com",
                "EXAMPLE.COM",
                "bücher.example",
                "faß.example",
                ".EXAMPLE.COM",
                "bücher..example",
                "example.com..",
                "[2001:DB8::1]",
                "[2001:0DB8:0:0:0:0:0:1]",
                "[::FFFF:C000:280]",
                "[fe80::1%25Eth0]",
            ]
        )
    )
    port = draw(st.sampled_from(["", ":80", ":443", ":8080", ":080", ":0443"]))
    userinfo = draw(
        st.sampled_from(["", "User:PaSS@", "user%40name:pa%3Ass@", "user%5Cname@"])
    )
    path = draw(
        st.one_of(
            st.just(""),
            st.lists(PATH_SEGMENT, max_size=6).map(lambda parts: "/" + "/".join(parts)),
        )
    )
    query = draw(
        st.one_of(
            st.just(""),
            st.lists(QUERY_FIELD, max_size=6).map(
                lambda fields: "?" + "&".join(fields)
            ),
        )
    )
    fragment = draw(st.one_of(st.just(""), FRAGMENT_TEXT.map(lambda text: "#" + text)))
    return f"{scheme}://{userinfo}{host}{port}{path}{query}{fragment}"


@st.composite
def relative_references(draw):
    """Compose explicit path, query and fragment references without an authority."""
    path = draw(
        st.one_of(
            st.sampled_from(["", ".", ".."]),
            st.builds(
                lambda prefix, segments: prefix + "/".join(segments),
                st.sampled_from(["./", "../"]),
                st.lists(PATH_SEGMENT, max_size=6),
            ),
        )
    )
    query = draw(st.one_of(st.just(""), QUERY_FIELD.map(lambda text: "?" + text)))
    fragment = draw(st.one_of(st.just(""), FRAGMENT_TEXT.map(lambda text: "#" + text)))
    return path + query + fragment


def assert_component_presence(original, result, *, keep_empty_components):
    """Check delimiter policy independently of normalization equality."""
    parts = urlsplit(result)
    query_present = (
        "?" in original.split("#", 1)[0] if keep_empty_components else bool(parts.query)
    )
    fragment_present = (
        "#" in original if keep_empty_components else bool(parts.fragment)
    )
    assert ("?" in result.split("#", 1)[0]) == query_present
    assert ("#" in result) == fragment_present


@PROPERTY_SETTINGS
@given(
    value=relative_references(),
    collapse_slashes=st.booleans(),
    remove_trailing_slash=st.booleans(),
    keep_empty_components=st.booleans(),
)
def test_relative_references_remain_stable_without_an_authority(
    value, collapse_slashes, remove_trailing_slash, keep_empty_components
):
    """Apply path policy without inventing an authority or losing relative context."""
    options = {
        "collapse_slashes": collapse_slashes,
        "remove_trailing_slash": remove_trailing_slash,
        "keep_empty_components": keep_empty_components,
    }
    normalized = url_normalize(value, **options)
    humanized = url_humanize(value, **options)
    parts = urlsplit(normalized)
    assert not parts.scheme
    assert not parts.netloc
    assert not parts.path.startswith("/")
    if urlsplit(value).path:
        assert parts.path
        assert parts.path in {".", ".."} or parts.path.startswith(("./", "../"))
    if collapse_slashes:
        assert "//" not in parts.path
    if remove_trailing_slash:
        assert not parts.path.endswith("/")
    assert url_normalize(normalized, **options) == normalized
    assert url_normalize(humanized, **options) == normalized
    assert_component_presence(
        value, normalized, keep_empty_components=keep_empty_components
    )


@PROPERTY_SETTINGS
@given(
    value=http_urls(),
    collapse_slashes=st.booleans(),
    remove_trailing_slash=st.booleans(),
    keep_empty_components=st.booleans(),
)
def test_normalization_is_idempotent(
    value, collapse_slashes, remove_trailing_slash, keep_empty_components
):
    """Reach a fixed point after one normalization of a supported URL."""
    options = {
        "collapse_slashes": collapse_slashes,
        "remove_trailing_slash": remove_trailing_slash,
        "keep_empty_components": keep_empty_components,
    }
    normalized = url_normalize(value, **options)

    assert isinstance(normalized, str)
    assert url_normalize(normalized, **options) == normalized
    assert_component_presence(
        value, normalized, keep_empty_components=keep_empty_components
    )


@PROPERTY_SETTINGS
@given(
    value=http_urls(),
    collapse_slashes=st.booleans(),
    remove_trailing_slash=st.booleans(),
    keep_empty_components=st.booleans(),
)
def test_humanization_normalizes_back_to_the_same_url(
    value, collapse_slashes, remove_trailing_slash, keep_empty_components
):
    """Keep normalized output stable when rendering a URL for display."""
    options = {
        "collapse_slashes": collapse_slashes,
        "remove_trailing_slash": remove_trailing_slash,
        "keep_empty_components": keep_empty_components,
    }
    humanized = url_humanize(value, **options)

    assert isinstance(humanized, str)
    assert url_normalize(humanized, **options) == url_normalize(value, **options)
    assert_component_presence(
        value, humanized, keep_empty_components=keep_empty_components
    )
