"""URL host normalization."""

from __future__ import annotations

import idna

from .tools import force_unicode

IDNA_DOT_TRANSLATION = str.maketrans("\u3002\uff0e\uff61", "...")


def normalize_host(host: str | bytes) -> str:
    """Normalize host part of the url.

    Lowercase and remove a single final dot, preserving other empty labels.
    Also, handle IDN domains using IDNA2008 with UTS46 processing.

    Params:
        host : str | bytes : URL host as text or UTF-8 bytes, e.g., 'site.com'

    Returns:
        string : normalized host data.

    """
    host = force_unicode(host)
    if not host:
        return host
    if host.startswith("[") and host.endswith("]"):
        address, separator, zone = host.partition("%")
        return address.lower() + separator + zone
    # Map equivalent IDNA separators without merging label boundaries.
    host = host.lower().translate(IDNA_DOT_TRANSLATION)

    parts = host.split(".")
    try:
        encoded = [
            idna.encode(part, uts46=True).decode("ascii") if part else ""
            for part in parts
        ]
    except idna.IDNAError:
        # Keep the legacy IDNA fallback without discarding empty labels.
        encoded = [
            part.encode("idna").decode("ascii") if part else "" for part in parts
        ]

    host = ".".join(encoded)
    # Preserve repeated trailing dots and the DNS root itself as fixed points.
    if len(host) > 1 and host.endswith(".") and not host.endswith(".."):
        return host[:-1]
    return host
