"""URL path normalization."""

from __future__ import annotations

import re

from ._schemes import EMPTY_PATH_SCHEMES, PATH_NORMALIZATION_SCHEMES
from .tools import RESERVED_CHARACTERS, normalize_component


def _remove_dot_segments(path: str) -> str:
    """Resolve RFC 3986 section 5.2.4 dot segments, retaining empty segments."""
    output: list[str] = []
    for part in path.split("/"):
        if part == "..":
            if output and output != [""]:
                output.pop()
                if not output:
                    # Removing the first relative segment leaves its next slash.
                    output.append("")
        elif part != ".":
            output.append(part)
    if path.endswith(("/.", "/..")):
        output.append("")
    return "/".join(output)


def normalize_path(
    path: str,
    scheme: str,
    *,
    collapse_slashes: bool = False,
    remove_trailing_slash: bool = False,
) -> str:
    """Normalize path part of the url.

    Resolve dots, optionally collapse slashes, then optionally remove trailing runs.

    Params:
        path : string : url path, e.g., '/section/page.html'
        scheme : string : url scheme, e.g., 'http'
        collapse_slashes : bool : collapse literal path slashes after dot removal
        remove_trailing_slash : bool : remove trailing literal slashes, keeping root

    Returns:
        string : normalized path data.

    """
    # Only perform percent-encoding where it is essential.
    # Always use uppercase A-through-F characters when percent-encoding.
    # All portions of the URI must be utf-8 encoded NFC from Unicode strings
    path = normalize_component(path, "~:/[]@!$&'()*+,;=", RESERVED_CHARACTERS)
    if scheme in PATH_NORMALIZATION_SCHEMES:
        path = _remove_dot_segments(path)
        if collapse_slashes:
            path = re.sub(r"/{2,}", "/", path)
        if remove_trailing_slash and path:
            path = path.rstrip("/") or "/"
    if not scheme and path.startswith("//"):
        # Keep a path reference from becoming an authority reference on reparse.
        path = "/." + path
    # For schemes that define an empty path to be equivalent to a path of "/",
    # use "/".
    if not path and scheme in EMPTY_PATH_SCHEMES:
        path = "/"
    return path
