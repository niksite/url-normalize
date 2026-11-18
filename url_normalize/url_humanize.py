"""URL humanization."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, overload
from urllib.parse import unquote

import idna

from ._encoding import RESERVED_ESCAPE_RE, has_display_controls
from ._url import URL, deconstruct_url, reconstruct_url
from .normalize_fragment import FRAGMENT_ASCII_ESCAPE_RE
from .normalize_query import process_query_param
from .normalize_scheme import DEFAULT_SCHEME
from .param_filter import _ParamRules  # noqa: TC001 - resolve runtime annotations
from .url_normalize import url_normalize

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import TypedDict, Unpack

    class _DisplayChanges(TypedDict, total=False):
        """Text components eligible for humanization, excluding presence flags."""

        host: str
        userinfo: str
        path: str
        query: str
        fragment: str


UNICODE_REPLACEMENT_CHARACTER = "\ufffd"


def _humanize_host(host: str) -> str:
    return ".".join(_humanize_host_label(label) for label in host.split("."))


def _humanize_host_label(label: str) -> str:
    try:
        return idna.decode(label)
    except idna.IDNAError:
        return label


def _replace_if_round_trips(
    url: URL,
    normalized: str,
    *,
    normalize: Callable[[str], str | None],
    **changes: Unpack[_DisplayChanges],
) -> URL:
    candidate = url._replace(**changes)
    if candidate == url:
        return url
    try:
        if normalize(reconstruct_url(candidate)) == normalized:
            return candidate
    except ValueError:
        # Invalid candidate syntax or Unicode must not reject the original URL.
        return url
    return url


def _safe_unquote(value: str) -> str:
    decoded = unquote(value)
    if (
        UNICODE_REPLACEMENT_CHARACTER in decoded
        or "\\" in decoded
        or has_display_controls(decoded)
    ):
        return value
    return decoded


def _humanize_fragment(fragment: str) -> str:
    """Decode safe Unicode around ASCII escapes without exposing fragment syntax."""
    return "".join(
        part if index % 2 else _safe_unquote(part)
        for index, part in enumerate(FRAGMENT_ASCII_ESCAPE_RE.split(fragment))
    )


def _humanize_reserved_text(value: str) -> str:
    """Decode readable text around escapes that must remain literal data."""
    return "".join(
        part if index % 2 else _safe_unquote(part)
        for index, part in enumerate(RESERVED_ESCAPE_RE.split(value))
    )


def _humanize_query_part(part: str) -> str:
    """Keep each readable spelling only if it preserves the encoded field."""
    readable = _humanize_reserved_text(part)
    if readable != part and process_query_param(readable) != part:
        return part
    return readable


def _humanize_query(
    url: URL, normalized: str, *, normalize: Callable[[str], str | None]
) -> URL:
    fields = []
    for field in url.query.split("&"):
        key, separator, value = field.partition("=")
        fields.append(
            f"{_humanize_query_part(key)}{separator}{_humanize_query_part(value)}"
        )
    return _replace_if_round_trips(
        url, normalized, normalize=normalize, query="&".join(fields)
    )


@overload
def url_humanize(
    url: str,
    *,
    default_scheme: str = DEFAULT_SCHEME,
    default_domain: str | None = None,
    filter_params: bool = False,
    param_allowlist: _ParamRules | None = None,
    param_denylist: _ParamRules | None = None,
    remove_tracking_params: bool = False,
    sort_query: bool = False,
    collapse_slashes: bool = True,
    remove_trailing_slash: bool = False,
    keep_empty_components: bool = False,
    strip_fragment: bool = False,
) -> str: ...


@overload
def url_humanize(
    url: None,
    *,
    default_scheme: str = DEFAULT_SCHEME,
    default_domain: str | None = None,
    filter_params: bool = False,
    param_allowlist: _ParamRules | None = None,
    param_denylist: _ParamRules | None = None,
    remove_tracking_params: bool = False,
    sort_query: bool = False,
    collapse_slashes: bool = True,
    remove_trailing_slash: bool = False,
    keep_empty_components: bool = False,
    strip_fragment: bool = False,
) -> None: ...


def url_humanize(  # noqa: PLR0913
    url: str | None,
    *,
    default_scheme: str = DEFAULT_SCHEME,
    default_domain: str | None = None,
    filter_params: bool = False,
    param_allowlist: _ParamRules | None = None,
    param_denylist: _ParamRules | None = None,
    remove_tracking_params: bool = False,
    sort_query: bool = False,
    collapse_slashes: bool = True,
    remove_trailing_slash: bool = False,
    keep_empty_components: bool = False,
    strip_fragment: bool = False,
) -> str | None:
    """Return a human-readable URL representation when it is safe.

    The input is normalized first. Humanization then decodes display-friendly
    components only when the result normalizes back to that same URL, so decoding
    is intentionally conservative around reserved URL characters and malformed
    percent-encoded bytes. Bidirectional controls and Unicode line/paragraph
    separators remain escaped for display; literal host display controls raise
    UnicodeError (a ValueError subclass). Userinfo and query reserved-character
    escapes and fragment ASCII escapes remain encoded to preserve embedded syntax.
    Empty query and fragment delimiters are dropped unless keep_empty_components is
    enabled. Path slashes collapse by default;
    set collapse_slashes=False to preserve repeated slashes. The selected path
    and empty-component policies are also used for round-trip checks.
    The default_scheme option uses the same cleanup and validation as
    url_normalize(). Validation runs when the cleaned URL is nonempty.
    Supplying param_allowlist enables filtering, even for an empty collection
    or when filter_params=False. Use filter_params=True without a custom rule
    to select the built-in domain rules.
    The param_denylist option accepts the same rule forms and removes matching
    names without filter_params; denied names override allowed names.
    Set remove_tracking_params=True to also remove the built-in set of exact,
    case-sensitive tracker names, including allowed ones. Disabled by default;
    it does not enable the built-in domain allowlist.
    Set sort_query=True to sort by normalized, percent-encoded keys after
    filtering, preserving equal-key order and value separators. Disabled by
    default; displayed names retain the same order as normalized names.
    Set strip_fragment=True to remove the entire fragment and its delimiter
    before display decoding. Disabled by default; overrides keep_empty_components
    for the fragment only.
    """
    normalized = url_normalize(
        url,
        default_scheme=default_scheme,
        default_domain=default_domain,
        filter_params=filter_params,
        param_allowlist=param_allowlist,
        param_denylist=param_denylist,
        remove_tracking_params=remove_tracking_params,
        sort_query=sort_query,
        collapse_slashes=collapse_slashes,
        remove_trailing_slash=remove_trailing_slash,
        keep_empty_components=keep_empty_components,
        strip_fragment=strip_fragment,
    )
    if not normalized:
        return normalized

    normalize_candidate = partial(
        url_normalize,
        sort_query=sort_query,
        collapse_slashes=collapse_slashes,
        remove_trailing_slash=remove_trailing_slash,
        keep_empty_components=keep_empty_components,
    )
    url_elements = deconstruct_url(normalized)
    url_elements = _replace_if_round_trips(
        url_elements,
        normalized,
        normalize=normalize_candidate,
        host=_humanize_host(url_elements.host),
    )

    for component, humanize in (
        ("userinfo", _humanize_reserved_text),
        ("path", _safe_unquote),
    ):
        value = getattr(url_elements, component)
        url_elements = _replace_if_round_trips(
            url_elements,
            normalized,
            normalize=normalize_candidate,
            **{component: humanize(value)},
        )
    url_elements = _replace_if_round_trips(
        url_elements,
        normalized,
        normalize=normalize_candidate,
        fragment=_humanize_fragment(url_elements.fragment),
    )
    url_elements = _humanize_query(
        url_elements, normalized, normalize=normalize_candidate
    )

    return reconstruct_url(url_elements)
