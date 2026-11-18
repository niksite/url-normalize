"""URL scheme validation and attachment."""

from __future__ import annotations

import re

from ._schemes import AUTHORITY_SCHEMES, looks_like_host_port
from ._url import cleanup_url_input
from .normalize_scheme import DEFAULT_SCHEME


def provide_url_scheme(url: str, default_scheme: str = DEFAULT_SCHEME) -> str:
    """Attach a scheme to host inputs, preserving explicit relative references.

    Params:
        url : string : the URL
        default_scheme : string : default scheme, with an optional trailing colon
            and surrounding whitespace, e.g. 'https' or 'HTTPS:'

    Returns:
        string : updated url with validated/attached scheme

    Raises:
        TypeError: If default_scheme is not a string.
        ValueError: If default_scheme is not a valid scheme name.

    """
    if not isinstance(default_scheme, str):
        msg = "default_scheme must be a string"
        raise TypeError(msg)
    default_scheme = default_scheme.strip().removesuffix(":")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*", default_scheme):
        msg = "default_scheme must be a scheme name such as 'https' or 'https:'"
        raise ValueError(msg)
    default_scheme = default_scheme.lower()

    url = cleanup_url_input(url)
    is_universal_scheme = url.startswith("//")
    is_file_path = url == "-" or (url.startswith("/") and not is_universal_scheme)
    is_relative_reference = re.match(r"\.{1,2}(?:/|[?#]|$)|[?#]", url)
    if not url or is_file_path or is_relative_reference:
        return url
    if is_universal_scheme:
        return f"{default_scheme}:{url}"
    if not re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", url):
        return f"{default_scheme}://{url.lstrip('/')}"
    scheme_part, rest = url.split(":", 1)
    if looks_like_host_port(scheme_part, rest):
        return f"{default_scheme}://{url}"
    if scheme_part.lower() not in AUTHORITY_SCHEMES:
        # handle cases like tel:, mailto:, etc.
        return url
    return f"{scheme_part}://{rest.lstrip('/')}"
