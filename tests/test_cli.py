"""Tests for the command line interface."""

import subprocess
import sys
from unittest.mock import patch

import pytest

from url_normalize import __version__
from url_normalize.cli import main


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Run the CLI command with given arguments.

    Params:
        *args: Command line arguments to pass to the CLI.

    Returns:
        A completed process with stdout, stderr, and return code.

    """
    command = [sys.executable, "-m", "url_normalize.cli", *list(args)]
    return subprocess.run(  # noqa: S603
        command, capture_output=True, text=True, check=False
    )


def test_cli_error_handling(capsys, monkeypatch):
    """Test CLI error handling when URL normalization fails."""
    with patch("url_normalize.cli.url_normalize") as mock_normalize:
        mock_normalize.side_effect = Exception("Simulated error")
        monkeypatch.setattr("sys.argv", ["url-normalize", "http://example.com"])

        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "Error normalizing URL: Simulated error" in captured.err
        assert not captured.out


def test_cli_basic_normalization() -> None:
    """Test basic URL normalization via CLI."""
    url = "http://EXAMPLE.com/./path/../other/"
    expected = "http://example.com/other/"

    result = run_cli(url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_basic_normalization_short_args() -> None:
    """Test basic URL normalization via CLI using short arguments."""
    url = "http://EXAMPLE.com/./path/../other/"
    expected = "http://example.com/other/"
    # Using short args where applicable (none for the URL itself)

    result = run_cli(url)  # No short args needed for basic case

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_default_scheme() -> None:
    """Test default scheme addition via CLI."""
    url = "//example.com"
    expected = "https://example.com/"

    result = run_cli(url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_default_scheme_short_arg() -> None:
    """Test default scheme addition via CLI using short argument."""
    url = "//example.com"
    expected = "https://example.com/"

    result = run_cli(url)  # Default scheme is implicit, no arg needed

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_custom_default_scheme() -> None:
    """Test custom default scheme via CLI."""
    url = "//example.com"
    expected = "ftp://example.com/"

    result = run_cli("--default-scheme", "ftp", url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_custom_default_scheme_short_arg() -> None:
    """Test custom default scheme via CLI using short argument."""
    url = "//example.com"
    expected = "ftp://example.com/"

    result = run_cli("-s", "ftp", url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_filter_params() -> None:
    """Test parameter filtering via CLI."""
    url = "http://google.com?utm_source=test&q=1"
    expected = "http://google.com/?q=1"

    result = run_cli("--filter-params", url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_filter_params_short_arg() -> None:
    """Test parameter filtering via CLI using short argument."""
    url = "http://google.com?utm_source=test&q=1"
    expected = "http://google.com/?q=1"

    result = run_cli("-f", url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_param_allowlist() -> None:
    """Test parameter allowlist via CLI."""
    url = "http://example.com?remove=me&keep=this&remove_too=true"
    expected = "http://example.com/?keep=this"
    # Use filter_params to enable filtering, then allowlist to keep specific ones

    result = run_cli("-f", "-p", "keep", url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_param_allowlist_multiple() -> None:
    """Test parameter allowlist with multiple params via CLI."""
    url = "http://example.com?remove=me&keep=this&keep_too=yes&remove_too=true"
    expected = "http://example.com/?keep=this&keep_too=yes"

    result = run_cli("-f", "-p", "keep,keep_too", url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_param_allowlist_without_filtering() -> None:
    """Test allowlist has no effect if filtering is not enabled."""
    url = "http://example.com?remove=me&keep=this&remove_too=true"
    expected = "http://example.com/?remove=me&keep=this&remove_too=true"
    # Not using -f, so allowlist should be ignored

    result = run_cli("-p", "keep", url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_no_url() -> None:
    """Test CLI error when no URL is provided."""
    result = run_cli()

    assert result.returncode != 0
    assert "the following arguments are required: url" in result.stderr


def test_cli_version_long() -> None:
    """Test version output with --version flag."""
    result = run_cli("--version")

    assert result.returncode == 0
    assert __version__ in result.stdout
    assert not result.stderr


def test_cli_version_short() -> None:
    """Test version output with -v flag."""
    result = run_cli("-v")

    assert result.returncode == 0
    assert __version__ in result.stdout
    assert not result.stderr


@pytest.mark.skipif(
    sys.platform == "win32", reason="Charset handling differs on Windows CLI"
)
def test_cli_charset() -> None:
    """Test charset handling via CLI (might be platform-dependent)."""
    # Example using Cyrillic characters which need correct encoding
    url = "http://пример.рф/path"
    expected_idn = "http://xn--e1afmkfd.xn--p1ai/path"

    # Test with default UTF-8
    result_utf8 = run_cli(url)

    assert result_utf8.returncode == 0
    assert result_utf8.stdout.strip() == expected_idn
    assert not result_utf8.stderr

    # Test specifying UTF-8 explicitly
    result_charset = run_cli("--charset", "utf-8", url)

    assert result_charset.returncode == 0
    assert result_charset.stdout.strip() == expected_idn
    assert not result_charset.stderr

    # Test specifying UTF-8 explicitly using short arg
    result_charset_short = run_cli("-c", "utf-8", url)

    assert result_charset_short.returncode == 0
    assert result_charset_short.stdout.strip() == expected_idn
    assert not result_charset_short.stderr


def test_cli_default_domain() -> None:
    """Test adding default domain to absolute path via CLI."""
    url = "/path/to/image.png"
    expected = "https://example.com/path/to/image.png"

    result = run_cli("--default-domain", "example.com", url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_default_domain_short_arg() -> None:
    """Test adding default domain using short argument."""
    url = "/path/to/image.png"
    expected = "https://example.com/path/to/image.png"

    result = run_cli("-d", "example.com", url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_default_domain_with_scheme() -> None:
    """Test adding default domain with custom scheme."""
    url = "/path/to/image.png"
    expected = "http://example.com/path/to/image.png"

    result = run_cli("-d", "example.com", "-s", "http", url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_default_domain_no_effect_on_absolute_urls() -> None:
    """Test default domain has no effect on absolute URLs."""
    url = "http://original-domain.com/path"
    expected = "http://original-domain.com/path"

    result = run_cli("-d", "example.com", url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


def test_cli_default_domain_no_effect_on_relative_paths() -> None:
    """Test default domain has no effect on relative paths."""
    url = "path/to/file.html"
    # This becomes a regular URL with the default scheme
    expected = "https://path/to/file.html"

    result = run_cli("-d", "example.com", url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr
