"""URL scheme validation and attachment."""

from __future__ import annotations

from .normalize_scheme import DEFAULT_SCHEME


def provide_url_scheme(url: str, default_scheme: str = DEFAULT_SCHEME) -> str:
    """Make sure we have valid url scheme.

    Params:
        url : string : the URL
        default_scheme : string : default scheme to use, e.g. 'https'

    Returns:
        string : updated url with validated/attached scheme

    """
    has_scheme = ":" in url[:7]
    is_universal_scheme = url.startswith("//")
    is_file_path = url == "-" or (url.startswith("/") and not is_universal_scheme)
    if not url or has_scheme or is_file_path:
        return url
    if is_universal_scheme:
        return default_scheme + ":" + url
    return default_scheme + "://" + url
