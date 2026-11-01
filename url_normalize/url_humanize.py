"""URL humanization."""

from __future__ import annotations

import unicodedata
from urllib.parse import unquote

import idna

from .normalize_scheme import DEFAULT_SCHEME
from .tools import URL, deconstruct_url, reconstruct_url
from .url_normalize import url_normalize

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
    url: URL, normalized: str, *, collapse_slashes: bool, **changes: str
) -> URL:
    candidate = url._replace(**changes)
    if candidate == url:
        return url
    try:
        if (
            url_normalize(reconstruct_url(candidate), collapse_slashes=collapse_slashes)
            == normalized
        ):
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


def _format_query_param(key: str, separator: str, value: str) -> str:
    return f"{key}{separator}{value}" if separator else key


def _replace_query_part_if_round_trips(  # noqa: PLR0913
    url: URL,
    normalized: str,
    parts: list[str],
    index: int,
    part: str,
    *,
    collapse_slashes: bool,
) -> tuple[URL, list[str]]:
    if part == parts[index]:
        return url, parts
    candidate_parts = [*parts]
    candidate_parts[index] = part
    candidate = _replace_if_round_trips(
        url,
        normalized,
        collapse_slashes=collapse_slashes,
        query="&".join(candidate_parts),
    )
    if candidate is not url:
        return candidate, candidate_parts
    return url, parts


def _humanize_query(url: URL, normalized: str, *, collapse_slashes: bool) -> URL:
    parts = url.query.split("&")
    for index, param in enumerate(parts):
        key, separator, value = param.partition("=")

        url, parts = _replace_query_part_if_round_trips(
            url,
            normalized,
            parts,
            index,
            _format_query_param(_safe_unquote(key), separator, value),
            collapse_slashes=collapse_slashes,
        )
        key, separator, value = parts[index].partition("=")  # noqa: PLR1736
        url, parts = _replace_query_part_if_round_trips(
            url,
            normalized,
            parts,
            index,
            _format_query_param(key, separator, _safe_unquote(value)),
            collapse_slashes=collapse_slashes,
        )

    return url


def url_humanize(  # noqa: PLR0913
    url: str | None,
    *,
    default_scheme: str = DEFAULT_SCHEME,
    default_domain: str | None = None,
    filter_params: bool = False,
    param_allowlist: dict | list | None = None,
    collapse_slashes: bool = False,
) -> str | None:
    """Return a human-readable URL representation when it is safe.

    The input is normalized first. Humanization then decodes display-friendly
    components only when the result normalizes back to that same URL, so decoding
    is intentionally conservative around reserved URL characters and malformed
    percent-encoded bytes. Bidirectional controls and Unicode line/paragraph
    separators remain escaped for display. The path policy, including
    collapse_slashes, is also used for round-trip checks.
    """
    normalized = url_normalize(
        url,
        default_scheme=default_scheme,
        default_domain=default_domain,
        filter_params=filter_params,
        param_allowlist=param_allowlist,
        collapse_slashes=collapse_slashes,
    )
    if not normalized:
        return normalized

    url_elements = deconstruct_url(normalized)
    url_elements = _replace_if_round_trips(
        url_elements,
        normalized,
        collapse_slashes=collapse_slashes,
        host=_humanize_host(url_elements.host),
    )

    for component in ("userinfo", "path", "fragment"):
        value = getattr(url_elements, component)
        url_elements = _replace_if_round_trips(
            url_elements,
            normalized,
            collapse_slashes=collapse_slashes,
            **{component: _safe_unquote(value)},
        )
    url_elements = _humanize_query(
        url_elements, normalized, collapse_slashes=collapse_slashes
    )

    return reconstruct_url(url_elements)
