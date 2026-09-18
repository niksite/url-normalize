"""URL userinfo normalization."""

from __future__ import annotations

from .tools import RESERVED_CHARACTERS, normalize_component


def normalize_userinfo(userinfo: str) -> str:
    """Normalize userinfo part of the url.

    Params:
        userinfo : string : url userinfo, e.g., 'user@'

    Returns:
        string : normalized userinfo data.

    """
    if userinfo in ["@", ":@"]:
        return ""
    separator = "@" if userinfo.endswith("@") else ""
    return (
        normalize_component(
            userinfo.removesuffix("@"), "!$&'()*+,;=:", RESERVED_CHARACTERS
        )
        + separator
    )
