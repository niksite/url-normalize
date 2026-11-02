"""URL host normalization."""

from __future__ import annotations

from ipaddress import AddressValueError, IPv6Address

import idna

from .tools import force_unicode

IDNA_DOT_TRANSLATION = str.maketrans("\u3002\uff0e\uff61", "...")


def _normalize_ip_literal(host: str) -> str:
    """Canonicalize a bracketed IPv6 address, preserving its zone identifier."""
    address, separator, zone = host[1:-1].partition("%")
    try:
        ipv6 = IPv6Address(address)
    except AddressValueError:
        # Keep the existing case policy for IPvFuture and other literal text.
        address = address.lower()
    else:
        mapped = ipv6.ipv4_mapped
        # Choose mixed notation explicitly for consistent Python-version output.
        address = f"::ffff:{mapped}" if mapped is not None else str(ipv6)
    return f"[{address}{separator}{zone}]"


def normalize_host(host: str | bytes) -> str:
    """Normalize host part of the url.

    Lowercase and remove a single final dot, preserving other empty labels.
    Canonicalize IPv6 literals while preserving zone identifiers.
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
        return _normalize_ip_literal(host)
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
