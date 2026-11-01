"""URL humanization."""

from __future__ import annotations

import unicodedata
from functools import partial
from typing import TYPE_CHECKING
from urllib.parse import unquote

import idna

from .normalize_fragment import FRAGMENT_ASCII_ESCAPE_RE
from .normalize_scheme import DEFAULT_SCHEME
from .tools import URL, deconstruct_url, reconstruct_url
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
# Bidi_Control: https://www.unicode.org/Public/UCD/latest/ucd/PropList.txt
# Join_Control characters are separate.
BIDI_CONTROL_CHARACTERS = frozenset(
    "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
)


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
        or any(
            unicodedata.category(character) in {"Cc", "Zl", "Zp"}
            or character in BIDI_CONTROL_CHARACTERS
            for character in decoded
        )
    ):
        return value
    return decoded


def _humanize_fragment(fragment: str) -> str:
    """Decode safe Unicode around ASCII escapes without exposing fragment syntax."""
    return "".join(
        part if index % 2 else _safe_unquote(part)
        for index, part in enumerate(FRAGMENT_ASCII_ESCAPE_RE.split(fragment))
    )


def _format_query_param(key: str, separator: str, value: str) -> str:
    return f"{key}{separator}{value}" if separator else key


def _replace_query_part_if_round_trips(  # noqa: PLR0913
    url: URL,
    normalized: str,
    parts: list[str],
    index: int,
    part: str,
    *,
    normalize: Callable[[str], str | None],
) -> tuple[URL, list[str]]:
    if part == parts[index]:
        return url, parts
    candidate_parts = [*parts]
    candidate_parts[index] = part
    candidate = _replace_if_round_trips(
        url,
        normalized,
        normalize=normalize,
        query="&".join(candidate_parts),
    )
    if candidate is not url:
        return candidate, candidate_parts
    return url, parts


def _humanize_query(
    url: URL, normalized: str, *, normalize: Callable[[str], str | None]
) -> URL:
    parts = url.query.split("&")
    for index, param in enumerate(parts):
        key, separator, value = param.partition("=")

        url, parts = _replace_query_part_if_round_trips(
            url,
            normalized,
            parts,
            index,
            _format_query_param(_safe_unquote(key), separator, value),
            normalize=normalize,
        )
        key, separator, value = parts[index].partition("=")  # noqa: PLR1736
        url, parts = _replace_query_part_if_round_trips(
            url,
            normalized,
            parts,
            index,
            _format_query_param(key, separator, _safe_unquote(value)),
            normalize=normalize,
        )

    return url


def url_humanize(  # noqa: PLR0913
    url: str | None,
    *,
    default_scheme: str = DEFAULT_SCHEME,
    default_domain: str | None = None,
    filter_params: bool = False,
    param_allowlist: dict | list | None = None,
    collapse_slashes: bool = True,
    remove_trailing_slash: bool = False,
    keep_empty_components: bool = False,
) -> str | None:
    """Return a human-readable URL representation when it is safe.

    The input is normalized first. Humanization then decodes display-friendly
    components only when the result normalizes back to that same URL, so decoding
    is intentionally conservative around reserved URL characters and malformed
    percent-encoded bytes. Bidirectional controls and Unicode line/paragraph
    separators remain escaped for display. Fragment ASCII escapes remain encoded
    to preserve embedded syntax. Empty query and fragment delimiters are dropped
    unless keep_empty_components is enabled. Path slashes collapse by default;
    set collapse_slashes=False to preserve repeated slashes. The selected path
    and empty-component policies are also used for round-trip checks.
    """
    normalized = url_normalize(
        url,
        default_scheme=default_scheme,
        default_domain=default_domain,
        filter_params=filter_params,
        param_allowlist=param_allowlist,
        collapse_slashes=collapse_slashes,
        remove_trailing_slash=remove_trailing_slash,
        keep_empty_components=keep_empty_components,
    )
    if not normalized:
        return normalized

    normalize_candidate = partial(
        url_normalize,
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

    for component in ("userinfo", "path"):
        value = getattr(url_elements, component)
        url_elements = _replace_if_round_trips(
            url_elements,
            normalized,
            normalize=normalize_candidate,
            **{component: _safe_unquote(value)},
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
