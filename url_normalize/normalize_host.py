"""URL host normalization."""

from __future__ import annotations

import re
from contextlib import suppress
from encodings.idna import nameprep
from ipaddress import AddressValueError, IPv6Address
from urllib.parse import unquote

import idna

from ._encoding import force_unicode, has_display_controls

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


def _encode_reg_name(host: str) -> str:
    """Encode a registered name, preserving the legacy whole-host fallback."""
    parts = host.translate(IDNA_DOT_TRANSLATION).split(".")
    try:
        encoded = [
            idna.encode(part, uts46=True).decode("ascii") if part else ""
            for part in parts
        ]
    except idna.IDNAError:
        # Keep the legacy IDNA fallback without discarding empty labels.
        parts = host.lower().translate(IDNA_DOT_TRANSLATION).split(".")
        encoded = [
            part.encode("idna").decode("ascii") if part else "" for part in parts
        ]

    return ".".join(encoded)


def _decode_host_escapes(host: str) -> str | None:
    """Decode one layer only when it produces a safe ASCII registered name."""
    try:
        decoded = unquote(host, errors="strict")
        encoded = _encode_reg_name(decoded)
    except UnicodeError:
        return None
    if has_display_controls(decoded) or not re.fullmatch(r"[A-Za-z0-9._~-]+", encoded):
        return None
    return encoded


def _encode_escaped_reg_name(host: str) -> str:
    """Recognize host escapes before converting international labels to Punycode."""
    spelling = host
    if not host.isascii():
        # Keep percent signs during UTS #46 mapping. Hosts outside that profile
        # still go through the existing legacy IDNA fallback.
        with suppress(idna.IDNAError):
            spelling = idna.uts46_remap(host, std3_rules=False)
    if "%" in spelling:
        decoded = _decode_host_escapes(spelling)
        if decoded is not None:
            return decoded

    encoded = _encode_reg_name(host)
    # Legacy nameprep can also join an escape. Decode the Unicode spelling
    # before Punycode so its non-ASCII character positions remain correct.
    if "%" in encoded and encoded != spelling:
        labels = host.lower().translate(IDNA_DOT_TRANSLATION).split(".")
        legacy = ".".join(nameprep(label) for label in labels)
        if legacy != encoded:
            decoded = _decode_host_escapes(legacy)
            if decoded is not None:
                return decoded
        return _decode_host_escapes(encoded) or encoded
    return encoded


def normalize_host(host: str | bytes) -> str:
    """Normalize host part of the url.

    Lowercase and remove a single final dot, preserving other empty labels.
    Canonicalize IPv6 literals while preserving zone identifiers.
    Also, handle IDN domains using IDNA2008 with UTS46 processing.

    Params:
        host : str | bytes : URL host as text or UTF-8 bytes, e.g., 'site.com'

    Returns:
        string : normalized host data.

    Raises:
        UnicodeError: The host contains display controls or invalid IDNA text.

    """
    host = force_unicode(host)
    if not host:
        return host
    if has_display_controls(host):
        msg = "Host must not contain display controls"
        raise UnicodeError(msg)
    if host.startswith("[") and host.endswith("]"):
        return _normalize_ip_literal(host)
    host = _encode_escaped_reg_name(host)
    # Preserve repeated trailing dots and the DNS root itself as fixed points.
    if len(host) > 1 and host.endswith(".") and not host.endswith(".."):
        return host[:-1]
    return host
