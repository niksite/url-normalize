"""Tests for normalize_port function."""

import pytest

from url_normalize.url_normalize import normalize_port


@pytest.mark.parametrize(
    ("port", "expected"),
    [
        ("8080", "8080"),  # Non-default port
        ("", ""),  # Empty port
        ("80", ""),  # Default HTTP port
        ("string", "string"),  # Non-numeric port (should pass through)
        # Add more cases as needed, e.g., for HTTPS
        pytest.param("443", "", id="https_default_port"),
    ],
)
def test_normalize_port_result_is_expected(port: str, expected: str):
    """Assert we got expected results from the normalize_port function."""
    # Test with 'http' scheme for most cases
    scheme = "https" if port == "443" else "http"

    result = normalize_port(port, scheme)

    assert result == expected
