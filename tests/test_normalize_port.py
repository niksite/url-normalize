"""Tests for normalize_port function."""

import pytest

from url_normalize.normalize_port import normalize_port


@pytest.mark.parametrize(
    ("scheme", "port", "expected"),
    [
        pytest.param("http", "80", "", id="http-default"),
        pytest.param("https", "443", "", id="https-default"),
        pytest.param("ws", "80", "", id="ws-default"),
        pytest.param("wss", "443", "", id="wss-default"),
        pytest.param("ftp", "21", "", id="ftp-default"),
        pytest.param("http", "443", "443", id="http-keeps-https-port"),
        pytest.param("https", "80", "80", id="https-keeps-http-port"),
        pytest.param("ws", "443", "443", id="ws-keeps-wss-port"),
        pytest.param("wss", "80", "80", id="wss-keeps-ws-port"),
        pytest.param("ftp", "80", "80", id="ftp-keeps-http-port"),
        pytest.param("http", "8080", "8080", id="non-default"),
        pytest.param("http", "080", "", id="http-padded-default"),
        pytest.param("https", "0443", "", id="https-padded-default"),
        pytest.param("ws", "080", "", id="ws-padded-default"),
        pytest.param("wss", "0443", "", id="wss-padded-default"),
        pytest.param("https", "0080", "80", id="padded-non-default"),
        pytest.param("http", "000", "0", id="zero-port"),
        pytest.param("http", "", "", id="empty-port"),
        pytest.param("custom", "80", "80", id="custom-keeps-http-port"),
        pytest.param("custom", "443", "443", id="custom-keeps-https-port"),
        pytest.param("http", "65535", "65535", id="tcp-upper-boundary"),
        pytest.param("http", "065536", "65536", id="no-range-validation"),
    ],
)
def test_normalize_port_result_is_expected(scheme: str, port: str, expected: str):
    """Remove only the default port for the specified scheme."""
    assert normalize_port(port, scheme) == expected
    assert normalize_port(expected, scheme) == expected


@pytest.mark.parametrize(
    "port",
    [
        pytest.param("string", id="non-numeric-port"),
        pytest.param("-1", id="negative-text"),
        pytest.param("+80", id="signed-text"),
        pytest.param("0x50", id="hexadecimal-text"),
        pytest.param("8_0", id="underscore-text"),
        pytest.param("\uff18\uff10", id="fullwidth-digits"),
        pytest.param("٨٠", id="arabic-indic-digits"),
        pytest.param("²", id="superscript-digit"),
        pytest.param("8\u0660", id="mixed-digit-scripts"),
        pytest.param("%38%30", id="escaped-digits"),
        pytest.param("8 0", id="embedded-space"),
        pytest.param("80:90", id="extra-colon"),
    ],
)
def test_normalize_port_rejects_non_ascii_decimal_text(port):
    """Reject nonempty ports outside RFC 3986's ASCII decimal syntax."""
    with pytest.raises(ValueError, match=r"^Port must contain only ASCII digits$"):
        normalize_port(port, "http")


@pytest.mark.parametrize(
    ("port", "expected"),
    [
        pytest.param("0" * 5000 + "80", "", id="padded-default"),
        pytest.param("0" * 5000 + "8080", "8080", id="padded-non-default"),
        pytest.param("0" * 5000, "0", id="all-zeroes"),
        pytest.param("1" + "0" * 5000, "1" + "0" * 5000, id="large-number"),
    ],
)
def test_normalize_port_handles_long_numeric_text(port, expected):
    """Normalize digit strings independently of Python integer conversion limits."""
    assert normalize_port(port, "http") == expected
    assert normalize_port(expected, "http") == expected
