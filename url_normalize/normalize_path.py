"""URL path normalization."""

from __future__ import annotations

import re

from ._encoding import normalize_component
from ._schemes import (
    EMPTY_PATH_SCHEMES,
    PATH_NORMALIZATION_SCHEMES,
    looks_like_host_port,
)


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


def _remove_relative_dot_segments(path: str) -> str:
    """Resolve internal dots while retaining parents that need a base directory."""
    if path in {".", ".."}:
        return path
    output: list[str] = []
    directory = False
    for part in path.split("/"):
        directory = part == "."
        if part == "..":
            if output and output[-1] != "..":
                output.pop()
                directory = True
            else:
                output.append(part)
        elif part != ".":
            output.append(part)
    if directory:
        output.append("")
    result = "/".join(output)
    # Keep the result distinct from a bare host, a scheme or a root-relative path.
    return result if output[0] == ".." else "./" + result


def normalize_path(
    path: str,
    scheme: str,
    *,
    collapse_slashes: bool = True,
    remove_trailing_slash: bool = False,
) -> str:
    """Normalize path part of the url.

    Resolve dots, optionally collapse slashes, then optionally remove trailing runs.
    Document-relative paths keep unresolved parents and an explicit relative prefix.

    Params:
        path : string : url path, e.g., '/section/page.html'
        scheme : string : url scheme, e.g., 'http'
        collapse_slashes : bool : collapse literal path slashes after dot removal
            (True by default)
        remove_trailing_slash : bool : remove trailing literal slashes, keeping root

    Returns:
        string : normalized path data.

    """
    # Only perform percent-encoding where it is essential.
    # Always use uppercase A-through-F characters when percent-encoding.
    # All portions of the URI must be utf-8 encoded NFC from Unicode strings
    path = normalize_component(path, "~:/[]@!$&'()*+,;=")
    if looks_like_host_port(scheme, path):
        # Retain an escaped digit to keep an opaque URI distinct from host:port.
        path = f"%{ord(path[0]):02X}{path[1:]}"
    if scheme in PATH_NORMALIZATION_SCHEMES:
        if not scheme and path and not path.startswith("/") and path != "-":
            path = _remove_relative_dot_segments(path)
        else:
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
