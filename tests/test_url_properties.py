"""Generated checks for supported HTTP(S) URLs, alongside exact-output tests."""

from string import ascii_letters, digits

from hypothesis import given, settings
from hypothesis import strategies as st

from url_normalize import url_humanize, url_normalize

PROPERTY_SETTINGS = settings(
    max_examples=200, derandomize=True, deadline=None, suppress_health_check=()
)

TEXT = st.text(alphabet=ascii_letters + digits + "-._~+é中\u0301", max_size=12)
ESCAPES = st.sampled_from(
    ["%2f", "%5C", "%25", "%26", "%3D", "%2B", "%20", "%E9", "%zz", "%%41", "%2%45"]
)
COMPONENT_TEXT = st.lists(st.one_of(TEXT, ESCAPES), max_size=3).map("".join)
PATH_SEGMENT = st.one_of(st.sampled_from(["", ".", ".."]), COMPONENT_TEXT)
QUERY_FIELD = st.one_of(
    COMPONENT_TEXT,
    st.builds(lambda key, value: f"{key}={value}", COMPONENT_TEXT, COMPONENT_TEXT),
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
                "[2001:DB8::1]",
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
    fragment = draw(st.one_of(st.just(""), COMPONENT_TEXT.map(lambda text: "#" + text)))
    return f"{scheme}://{userinfo}{host}{port}{path}{query}{fragment}"


@PROPERTY_SETTINGS
@given(
    value=http_urls(),
    collapse_slashes=st.booleans(),
    remove_trailing_slash=st.booleans(),
)
def test_normalization_is_idempotent(value, collapse_slashes, remove_trailing_slash):
    """Reach a fixed point after one normalization of a supported URL."""
    options = {
        "collapse_slashes": collapse_slashes,
        "remove_trailing_slash": remove_trailing_slash,
    }
    normalized = url_normalize(value, **options)

    assert isinstance(normalized, str)
    assert url_normalize(normalized, **options) == normalized


@PROPERTY_SETTINGS
@given(
    value=http_urls(),
    collapse_slashes=st.booleans(),
    remove_trailing_slash=st.booleans(),
)
def test_humanization_normalizes_back_to_the_same_url(
    value, collapse_slashes, remove_trailing_slash
):
    """Keep normalized output stable when rendering a URL for display."""
    options = {
        "collapse_slashes": collapse_slashes,
        "remove_trailing_slash": remove_trailing_slash,
    }
    humanized = url_humanize(value, **options)

    assert isinstance(humanized, str)
    assert url_normalize(humanized, **options) == url_normalize(value, **options)
