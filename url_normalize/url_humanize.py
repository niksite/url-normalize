"""URL humanization."""

from __future__ import annotations

from urllib.parse import unquote

import idna

from .normalize_host import DEFAULT_CHARSET
from .normalize_scheme import DEFAULT_SCHEME
from .tools import URL, deconstruct_url, reconstruct_url
from .url_normalize import url_normalize

UNICODE_REPLACEMENT_CHARACTER = "\ufffd"


def _humanize_host(host: str) -> str:
    return ".".join(_humanize_host_label(label) for label in host.split("."))


def _humanize_host_label(label: str) -> str:
    try:
        return idna.decode(label)
    except idna.IDNAError:
        return label


def _replace_if_round_trips(url: URL, normalized: str, **changes: str) -> URL:
    candidate = url._replace(**changes)
    if url_normalize(reconstruct_url(candidate)) == normalized:
        return candidate
    return url


def _safe_unquote(value: str) -> str:
    decoded = unquote(value)
    if UNICODE_REPLACEMENT_CHARACTER in decoded:
        return value
    return decoded


def _format_query_param(key: str, separator: str, value: str) -> str:
    return f"{key}{separator}{value}" if separator else key


def _replace_query_part_if_round_trips(
    url: URL,
    normalized: str,
    parts: list[str],
    index: int,
    part: str,
) -> tuple[URL, list[str]]:
    candidate_parts = [*parts]
    candidate_parts[index] = part
    candidate = url._replace(query="&".join(candidate_parts))
    if url_normalize(reconstruct_url(candidate)) == normalized:
        return candidate, candidate_parts
    return url, parts


def _humanize_query(url: URL, normalized: str) -> URL:
    parts = url.query.split("&")
    for index, param in enumerate(parts):
        key, separator, value = param.partition("=")

        url, parts = _replace_query_part_if_round_trips(
            url,
            normalized,
            parts,
            index,
            _format_query_param(_safe_unquote(key), separator, value),
        )
        key, separator, value = parts[index].partition("=")  # noqa: PLR1736
        url, parts = _replace_query_part_if_round_trips(
            url,
            normalized,
            parts,
            index,
            _format_query_param(key, separator, _safe_unquote(value)),
        )

    return url


def url_humanize(  # noqa: PLR0913
    url: str | None,
    *,
    charset: str = DEFAULT_CHARSET,
    default_scheme: str = DEFAULT_SCHEME,
    default_domain: str | None = None,
    filter_params: bool = False,
    param_allowlist: dict | list | None = None,
) -> str | None:
    """Return a human-readable URL representation when it is safe.

    The input is normalized first. Humanization then decodes display-friendly
    components only when the result normalizes back to that same URL, so decoding
    is intentionally conservative around reserved URL characters and malformed
    percent-encoded bytes.
    """
    normalized = url_normalize(
        url,
        charset=charset,
        default_scheme=default_scheme,
        default_domain=default_domain,
        filter_params=filter_params,
        param_allowlist=param_allowlist,
    )
    if not normalized:
        return normalized

    url_elements = deconstruct_url(normalized)
    url_elements = _replace_if_round_trips(
        url_elements,
        normalized,
        host=_humanize_host(url_elements.host),
    )

    for component in ("userinfo", "path", "fragment"):
        value = getattr(url_elements, component)
        url_elements = _replace_if_round_trips(
            url_elements,
            normalized,
            **{component: _safe_unquote(value)},
        )
    url_elements = _humanize_query(url_elements, normalized)

    return reconstruct_url(url_elements)
