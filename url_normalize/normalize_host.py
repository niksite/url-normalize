"""URL host normalization."""

from __future__ import annotations

import idna

from .tools import force_unicode


def normalize_host(host: str | bytes) -> str:
    """Normalize host part of the url.

    Lowercase and strip of final dot.
    Also, handle IDN domains using IDNA2008 with UTS46 processing.

    Params:
        host : str | bytes : URL host as text or UTF-8 bytes, e.g., 'site.com'

    Returns:
        string : normalized host data.

    """
    host = force_unicode(host)
    if host.startswith("[") and host.endswith("]"):
        address, separator, zone = host.partition("%")
        return address.lower() + separator + zone
    host = host.lower()
    # Strip trailing IDNA separators before they are mapped to ASCII dots.
    host = host.lstrip(".").rstrip(".\u3002\uff0e\uff61")

    # Split domain into parts to handle each label separately
    parts = host.split(".")
    try:
        # Process each label separately to handle mixed unicode/ascii domains
        parts = [idna.encode(p, uts46=True).decode("ascii") for p in parts if p]
        return ".".join(parts)
    except idna.IDNAError:
        # Fallback to direct encoding if IDNA2008 processing fails
        return host.encode("idna").decode("ascii")
