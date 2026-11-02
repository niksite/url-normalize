"""Opt-in removal of documented tracker names without broad prefix matching."""

import pytest

from url_normalize import url_humanize, url_normalize


@pytest.mark.parametrize(
    "query",
    [
        (
            "utm_id=1&utm_source=2&utm_medium=3&utm_campaign=4&utm_source_platform=5"
            "&utm_term=6&utm_content=7&utm_creative_format=8&utm_marketing_tactic=9"
            "&utm_referrer=10"
        ),
        "gclid=1&dclid=2&gbraid=3&wbraid=4&gad_source=5&gad_campaignid=6&srsltid=7",
        "fbclid=1&msclkid=2&ttclid=3&twclid=4&yclid=5",
        "mc_cid=1&mc_eid=2",
        (
            "mtm_campaign=1&mtm_keyword=2&mtm_source=3&mtm_medium=4&mtm_content=5"
            "&mtm_cid=6&mtm_group=7&mtm_placement=8&mtm_kwd=9&matomo_campaign=10"
            "&pk_campaign=11&piwik_campaign=12&pk_kwd=13&piwik_kwd=14&pk_keyword=15"
            "&matomo_kwd=16"
        ),
    ],
)
def test_tracker_removal_covers_documented_families(query):
    """Exercise the documented provider names through the public API."""
    # Courlan's UTM-removal cases inspired this check; provider names and exact
    # matching follow our own documented preset, not Courlan's broad regex:
    # https://github.com/adbar/courlan/blob/v1.4.0/tests/unit_tests.py
    assert (
        url_normalize(
            f"https://example.com/product?id=123&{query}&variant=blue",
            remove_tracking_params=True,
        )
        == "https://example.com/product?id=123&variant=blue"
    )


@pytest.mark.parametrize("api", [url_normalize, url_humanize])
def test_tracker_removal_is_opt_in(api):
    """Retain attribution unless removal is explicitly requested."""
    value = "https://example.com/?utm_source=email&ttclid=abc&srsltid=xyz&id=1"
    assert api(value) == value
    assert api(value, remove_tracking_params=False) == value
    assert api(value, remove_tracking_params=True) == "https://example.com/?id=1"


@pytest.mark.parametrize("api", [url_normalize, url_humanize])
def test_tracker_removal_preserves_retained_query_syntax(api):
    """Remove repeated/encoded tracker names without changing retained fields."""
    value = (
        "https://example.com/?tag=red&%75tm_source=email&flag&tag=blue&empty="
        "&utm_source=second&keep=utm_source%3Dx#details"
    )
    expected = (
        "https://example.com/?tag=red&flag&tag=blue&empty=&keep=utm_source%3Dx#details"
    )
    assert api(value, remove_tracking_params=True) == expected
    assert api(expected, remove_tracking_params=True) == expected


@pytest.mark.parametrize(
    "value",
    [
        (
            "https://api.github.com/repos/niksite/url-normalize/contents/README.md"
            "?ref=v3.1.0"
        ),
        "https://example.com/success?session_id=cs_test_example",
        (
            "https://example.com/search?keyword=python&source=books&campaign=summer"
            "&uid=7&gallery=large&gateway=main&global=1&reference=42"
        ),
        (
            "https://example.com/?utm_custom=1&gclid_extra=2&mc_internal=3"
            "&UTM_SOURCE=4&GCLID=5&utm_source%2Fx=6&utm_source+=7"
        ),
        "https://example.com/?mkt_tok=1&_ga=2&_gl=3&igshid=4&ysclid=5&vero_id=6",
        "https://example.com/#/route?utm_source=email",
    ],
)
def test_tracker_removal_preserves_other_names_and_fragments(value):
    """Avoid the functional-name, near-match and fragment losses seen in Courlan."""
    assert url_normalize(value, remove_tracking_params=True) == value


def test_tracker_removal_only_changes_query_keys():
    """Leave matching words in path, values and fragment routes alone."""
    assert (
        url_normalize(
            "https://example.com/utm_source?keep=gclid&utm_source=email"
            "#/route?utm_source=email",
            remove_tracking_params=True,
        )
        == "https://example.com/utm_source?keep=gclid#/route?utm_source=email"
    )


@pytest.mark.parametrize("api", [url_normalize, url_humanize])
@pytest.mark.parametrize("keep_empty", [False, True])
def test_tracker_removal_uses_empty_component_policy(api, keep_empty):
    """Retain an emptied query delimiter only when requested."""
    expected = "https://example.com/?#" if keep_empty else "https://example.com/"
    assert (
        api(
            "https://example.com/?gclid=abc#",
            remove_tracking_params=True,
            keep_empty_components=keep_empty,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("api", "expected"),
    [
        (url_normalize, "../a//b?keep=caf%C3%A9#"),  # codespell:ignore caf
        (url_humanize, "../a//b?keep=café#"),
    ],
)
def test_tracker_removal_with_relative_unicode_reference(api, expected):
    """Share path/display policies with query removal and maintain round trips."""
    value = "../a//b?keep=caf%C3%A9&ttclid=abc#"  # codespell:ignore caf
    options = {
        "remove_tracking_params": True,
        "collapse_slashes": False,
        "keep_empty_components": True,
    }
    result = api(value, **options)
    assert result == expected
    assert url_normalize(result, **options) == url_normalize(value, **options)


@pytest.mark.parametrize(
    ("options", "expected_query"),
    [
        ({"param_allowlist": ["id", "utm_source"]}, "?id=1"),
        ({"param_denylist": "tag"}, "?id=1"),
        (
            {"param_allowlist": ["id", "tag", "utm_source"], "param_denylist": "tag"},
            "?id=1",
        ),
        ({"param_denylist": []}, "?id=1&tag=red"),
        ({"param_allowlist": []}, ""),
    ],
)
def test_tracker_removal_combines_with_custom_rules(options, expected_query):
    """Apply the tracker preset in addition to both kinds of custom rule."""
    assert (
        url_normalize(
            "https://example.com/?id=1&utm_source=email&tag=red",
            remove_tracking_params=True,
            **options,
        )
        == f"https://example.com/{expected_query}"
    )


def test_tracker_removal_can_narrow_builtin_filtering():
    """Keep the existing explicit built-in allowlist behavior when also requested."""
    assert (
        url_normalize(
            "https://google.com/search?q=hello&ie=UTF-8&utm_source=email",
            filter_params=True,
            param_denylist="ie",
            remove_tracking_params=True,
        )
        == "https://google.com/search?q=hello"
    )


def test_tracker_removal_does_not_modify_custom_rules():
    """Keep successive calls independent when a rule object is reused."""
    denylist = ["drop"]
    value = "https://example.com/?utm_source=email&drop=1&id=2"
    assert (
        url_normalize(value, param_denylist=denylist, remove_tracking_params=True)
        == "https://example.com/?id=2"
    )
    assert url_normalize(value, param_denylist=denylist) == (
        "https://example.com/?utm_source=email&id=2"
    )
    assert denylist == ["drop"]
