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
        pytest.param("http", "string", "string", id="non-numeric-port"),
    ],
)
def test_normalize_port_result_is_expected(scheme: str, port: str, expected: str):
    """Remove only the default port for the specified scheme."""
    assert normalize_port(port, scheme) == expected
