"""Tests for the command line interface."""

import subprocess
import sys
from io import StringIO

import pytest

from url_normalize import __version__
from url_normalize.cli import main


@pytest.fixture
def invoke_cli(capsys, monkeypatch):
    """Run successful CLI calls in-process and return their stdout."""

    def invoke(*args: str) -> str:
        monkeypatch.setattr(sys, "argv", ["url-normalize", *args])
        main()
        captured = capsys.readouterr()
        assert not captured.err
        return captured.out

    return invoke


def run_cli_subprocess(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI command with given arguments.

    Params:
        *args: Command line arguments to pass to the CLI.

    Returns:
        A completed process with stdout, stderr, and return code.

    """
    command = [sys.executable, "-m", "url_normalize.cli", *list(args)]
    return subprocess.run(  # noqa: S603
        command, capture_output=True, text=True, encoding="utf-8", check=False
    )


@pytest.mark.parametrize("humanize", [False, True])
def test_cli_rejects_host_display_controls(humanize):
    """Capture terminal controls as input without emitting them on either stream."""
    options = ["--humanize"] if humanize else []
    result = run_cli_subprocess(*options, "https://[fe80::1%eth0\x1b[2J\x1b[Hspoofed]/")
    assert result.returncode == 1
    assert not result.stdout
    assert result.stderr == (
        "Error normalizing URL: Host must not contain display controls\n"
    )


@pytest.mark.parametrize("humanize", [False, True])
@pytest.mark.parametrize("prefix", ["../", "./", "?q=", "#"])
def test_cli_preserves_relative_references(humanize, prefix, invoke_cli):
    """Print relative text without adding a scheme, domain or root path."""
    options = ["--humanize"] if humanize else []
    output = invoke_cli(*options, prefix + "%C3%A9")
    expected = prefix + ("é" if humanize else "%C3%A9")
    assert output == expected + "\n"


@pytest.mark.parametrize("humanize", [False, True])
@pytest.mark.parametrize("collapse_slashes", [None, False, True])
@pytest.mark.parametrize("remove_trailing_slash", [False, True])
def test_cli_relative_policy_options(
    humanize, collapse_slashes, remove_trailing_slash, invoke_cli
):
    """Apply dot removal and each path option while retaining relative context."""
    options = ["--humanize"] if humanize else []
    if collapse_slashes is not None:
        options.append(
            "--collapse-slashes" if collapse_slashes else "--no-collapse-slashes"
        )
    if remove_trailing_slash:
        options.append("--remove-trailing-slash")
    value = "../a//../%C3%A9///?#"
    output = invoke_cli(
        *options,
        "--keep-empty-components",
        "--default-domain",
        "example.com",
        value,
    )
    segment = "é" if humanize else "%C3%A9"
    trailing = (
        "" if remove_trailing_slash else "///" if collapse_slashes is False else "/"
    )
    assert output == f"../a/{segment}{trailing}?#\n"


def test_cli_help() -> None:
    """Describe allowlist filtering and omit the removed charset option."""
    result = run_cli_subprocess("--help")
    assert result.returncode == 0
    help_text = " ".join(result.stdout.split())
    assert "Filter query parameters using built-in rules" in help_text
    assert "Unknown domains have an empty default allowlist." in help_text
    assert "enables filtering without -f." in help_text
    assert "An empty string selects the empty name." in help_text
    assert "--param-denylist" in help_text
    assert "Denied names override allowed names." in help_text
    assert "--remove-tracking-params" in help_text
    assert "exact, case-sensitive tracker names" in help_text
    assert "--sort-query" in help_text
    assert "keeping repeated values in their original order" in help_text
    assert "--strip-fragment" in help_text
    assert "Remove the entire fragment and its # delimiter" in help_text
    assert "charset" not in result.stdout
    assert not result.stderr


@pytest.mark.parametrize("option", ["-c", "--charset"])
def test_cli_rejects_removed_charset_option(option, monkeypatch):
    """Report removed flags with UTF-8 diagnostics even under a legacy encoding."""
    monkeypatch.setenv("PYTHONIOENCODING", "cp1252")
    usage_error_status = 2
    result = run_cli_subprocess(option, "utf-8", "https://example.com/é")
    assert result.returncode == usage_error_status
    assert "unrecognized arguments" in result.stderr
    assert "https://example.com/é" in result.stderr
    assert not result.stdout


@pytest.mark.parametrize("humanize", [False, True])
def test_cli_preserves_empty_host_labels(humanize, invoke_cli):
    """Print unusual host boundaries while normalizing or humanizing Unicode."""
    options = ["--humanize"] if humanize else []
    output = invoke_cli(*options, "https://.BÜCHER..de../%C3%A9")
    host, path = (
        (".bücher..de..", "é") if humanize else (".xn--bcher-kva..de..", "%C3%A9")
    )

    assert output == f"https://{host}/{path}\n"


@pytest.mark.parametrize("humanize", [False, True])
def test_cli_compresses_ipv6_literals(humanize, invoke_cli):
    """Print canonical IPv6 text while retaining zone case in both output modes."""
    options = ["--humanize"] if humanize else []
    output = invoke_cli(*options, "https://[FE80:0:0:0:0:0:0:ABCD%25EthA]:443/%C3%A9")
    path = "é" if humanize else "%C3%A9"
    assert output == f"https://[fe80::abcd%25EthA]/{path}\n"


@pytest.mark.parametrize("reconfigure_attribute", ["missing", "non-callable"])
def test_cli_replacement_streams(reconfigure_attribute, monkeypatch):
    """Support output streams without a callable reconfigure method."""
    stdout, stderr = StringIO(), StringIO()
    for stream_name, stream in (("stdout", stdout), ("stderr", stderr)):
        if reconfigure_attribute == "non-callable":
            monkeypatch.setattr(stream, "reconfigure", None, raising=False)
        monkeypatch.setattr(sys, stream_name, stream)
    monkeypatch.setattr(
        sys,
        "argv",
        ["url-normalize", "--humanize", "https://xn--bcher-kva.de/%C3%A9"],
    )

    main()

    assert stdout.getvalue() == "https://bücher.de/é\n"
    assert not stderr.getvalue()


@pytest.mark.parametrize("humanize", [False, True])
def test_cli_error_handling(humanize, capsys, monkeypatch):
    """Report a real malformed port with status 1 and no partial URL output."""
    options = ["--humanize"] if humanize else []
    monkeypatch.setattr(
        sys, "argv", ["url-normalize", *options, "https://example.com:²/%C3%A9"]
    )

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert captured.err == (
        "Error normalizing URL: Port must contain only ASCII digits\n"
    )
    assert not captured.out


@pytest.mark.parametrize("humanize", [False, True])
def test_cli_preserves_reserved_query_escapes(humanize, invoke_cli):
    """Share query escape preservation and readable Unicode with the Python APIs."""
    value = "https://example.com/?q=%C3%A9%2f&flag=&flag"
    text = "é" if humanize else "%C3%A9"
    options = ["--humanize"] if humanize else []
    assert (
        invoke_cli(*options, value) == f"https://example.com/?q={text}%2F&flag=&flag\n"
    )


def test_cli_basic_normalization() -> None:
    """Test basic URL normalization via CLI."""
    url = "http://EXAMPLE.com/./path/../other/"
    expected = "http://example.com/other/"

    result = run_cli_subprocess(url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


@pytest.mark.parametrize("io_encoding", ["utf-8", "cp1252"])
def test_cli_humanize(io_encoding, monkeypatch):
    """Print Unicode display URLs in UTF-8 even under a legacy encoding."""
    monkeypatch.setenv("PYTHONIOENCODING", io_encoding)
    url = (
        "https://xn--e1afmkfd.xn--80akhbyknj4f/"
        "%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F"
    )
    expected = "https://пример.испытание/Служебная"

    result = run_cli_subprocess("--humanize", url)

    assert result.returncode == 0
    assert result.stdout.strip() == expected
    assert not result.stderr


@pytest.mark.parametrize("humanize", [False, True])
@pytest.mark.parametrize("keep_empty_components", [False, True])
@pytest.mark.parametrize("suffix", ["?", "#", "?#"])
def test_cli_empty_component_policy(
    humanize, keep_empty_components, suffix, invoke_cli
):
    """Drop empty delimiters by default and keep them on request in both modes."""
    options = ["--humanize"] if humanize else []
    if keep_empty_components:
        options.append("--keep-empty-components")
    value = f"https://example.com/%C3%A9{suffix}"
    path = "é" if humanize else "%C3%A9"
    expected_suffix = suffix if keep_empty_components else ""
    expected = f"https://example.com/{path}{expected_suffix}"

    output = invoke_cli(*options, value)

    assert output == f"{expected}\n"


@pytest.mark.parametrize("humanize", [False, True])
@pytest.mark.parametrize("keep_empty_components", [False, True])
def test_cli_empty_component_policy_after_filtering(
    humanize, keep_empty_components, invoke_cli
):
    """Apply the selected policy when filtering removes every query parameter."""
    options = ["--filter-params", "--param-allowlist", "keep"]
    if humanize:
        options.append("--humanize")
    if keep_empty_components:
        options.append("--keep-empty-components")

    output = invoke_cli(*options, "https://example.com/?drop=1#")

    expected_suffix = "?#" if keep_empty_components else ""
    assert output == f"https://example.com/{expected_suffix}\n"


@pytest.mark.parametrize("humanize", [False, True])
@pytest.mark.parametrize(
    "fragment", ["!/route", ":~:text=%C3%A9%2Dtest", ":%7E:text=%C3%A9"]
)
def test_cli_preserves_fragment_syntax(humanize, fragment, invoke_cli):
    """Keep routes and text directives in the fragment in both output modes."""
    options = ["--humanize"] if humanize else []
    value = f"https://example.com/?keep=1#{fragment}"
    expected = value.replace("%C3%A9", "é") if humanize else value

    output = invoke_cli(*options, value)

    assert output == f"{expected}\n"


@pytest.mark.parametrize("humanize", [False, True])
@pytest.mark.parametrize("collapse_slashes", [None, False, True])
@pytest.mark.parametrize("remove_trailing_slash", [False, True])
def test_cli_path_policy(humanize, collapse_slashes, remove_trailing_slash, invoke_cli):
    """Expose independent path cleanup options in both CLI output modes."""
    options = []
    if humanize:
        options.append("--humanize")
    if collapse_slashes is not None:
        options.append(
            "--collapse-slashes" if collapse_slashes else "--no-collapse-slashes"
        )
    if remove_trailing_slash:
        options.append("--remove-trailing-slash")
    output = invoke_cli(*options, "https://example.com/a//%C3%A9///?q=a//b")
    segment = "é" if humanize else "%C3%A9"
    path = {
        (False, False): f"/a//{segment}///",
        (True, False): f"/a/{segment}/",
        (False, True): f"/a//{segment}",
        (True, True): f"/a/{segment}",
    }[collapse_slashes is not False, remove_trailing_slash]
    assert output == f"https://example.com{path}?q=a//b\n"


def test_cli_humanize_short_arg(invoke_cli):
    """Test human-readable URL output via CLI using short argument."""
    url = (
        "https://xn--e1afmkfd.xn--80akhbyknj4f/"
        "%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F"
    )
    expected = "https://пример.испытание/Служебная"

    output = invoke_cli("-H", url)

    assert output.strip() == expected


def test_cli_humanize_respects_normalization_options(invoke_cli):
    """Test humanized output keeps the existing CLI normalization options."""
    url = "/%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F"
    expected = "https://пример.испытание/Служебная?keep=Ç"

    output = invoke_cli(
        "--humanize",
        "--default-domain",
        "xn--e1afmkfd.xn--80akhbyknj4f",
        "--filter-params",
        "--param-allowlist",
        "keep",
        f"{url}?utm_source=ignored&keep=%C3%87",
    )

    assert output.strip() == expected


def test_cli_default_scheme(invoke_cli):
    """Test default scheme addition via CLI."""
    url = "//example.com"
    expected = "https://example.com/"

    output = invoke_cli(url)

    assert output.strip() == expected


@pytest.mark.parametrize("humanize", [False, True])
def test_cli_reports_invalid_default_scheme(humanize, capsys, monkeypatch):
    """Fail a malformed scheme option with a clear diagnostic and no URL output."""
    options = ["--humanize"] if humanize else []
    monkeypatch.setattr(
        sys, "argv", ["url-normalize", *options, "-s", "https://", "example.com/path"]
    )
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert captured.err == (
        "Error normalizing URL: default_scheme must be a scheme name "
        "such as 'https' or 'https:'\n"
    )
    assert not captured.out


@pytest.mark.parametrize("humanize", [False, True])
def test_cli_accepts_default_scheme_with_colon(humanize, invoke_cli):
    """Share default-scheme cleanup with both API modes."""
    options = ["--humanize"] if humanize else []
    assert (
        invoke_cli(*options, "-s", " HTTP: ", "example.com:80/path")
        == "http://example.com/path\n"
    )


def test_cli_custom_default_scheme(invoke_cli):
    """Test custom default scheme via CLI."""
    url = "//example.com"
    expected = "ftp://example.com/"

    output = invoke_cli("--default-scheme", "ftp", url)

    assert output.strip() == expected


def test_cli_custom_default_scheme_short_arg(invoke_cli):
    """Test custom default scheme via CLI using short argument."""
    url = "//example.com"
    expected = "ftp://example.com/"

    output = invoke_cli("-s", "ftp", url)

    assert output.strip() == expected


def test_cli_filter_params(invoke_cli):
    """Test parameter filtering via CLI."""
    url = "http://google.com?utm_source=test&q=1"
    expected = "http://google.com/?q=1"

    output = invoke_cli("--filter-params", url)

    assert output.strip() == expected


def test_cli_filter_params_short_arg(invoke_cli):
    """Test parameter filtering via CLI using short argument."""
    url = "http://google.com?utm_source=test&q=1"
    expected = "http://google.com/?q=1"

    output = invoke_cli("-f", url)

    assert output.strip() == expected


def test_cli_param_allowlist(invoke_cli):
    """Test parameter allowlist via CLI."""
    url = "http://example.com?remove=me&keep=this&remove_too=true"
    expected = "http://example.com/?keep=this"
    # Keep accepting the explicit filtering flag alongside a custom rule.

    output = invoke_cli("-f", "-p", "keep", url)

    assert output.strip() == expected


def test_cli_param_allowlist_multiple(invoke_cli):
    """Test parameter allowlist with multiple params via CLI."""
    url = "http://example.com?remove=me&keep=this&keep_too=yes&remove_too=true"
    expected = "http://example.com/?keep=this&keep_too=yes"

    output = invoke_cli("-p", "keep,keep_too", url)

    assert output.strip() == expected


@pytest.mark.parametrize("mode", [(), ("--humanize",)])
def test_cli_param_allowlist_enables_filtering(invoke_cli, mode):
    """Apply a custom rule without requiring the separate filtering flag."""
    url = "http://example.com?remove=me&keep=this&remove_too=true"
    expected = "http://example.com/?keep=this"

    output = invoke_cli(*mode, "--param-allowlist", "keep", url)

    assert output.strip() == expected


@pytest.mark.parametrize("mode", [(), ("--humanize",)])
def test_cli_empty_name_allowlist_enables_filtering(invoke_cli, mode):
    """Distinguish an explicit empty parameter name from an omitted option."""
    url = "https://google.com/?=value&q=hello&drop=1"
    expected = "https://google.com/?=value"

    output = invoke_cli(*mode, "-p", "", url)

    assert output.strip() == expected


@pytest.mark.parametrize("mode", [(), ("--humanize",)])
def test_cli_denylist_enables_removal(invoke_cli, mode):
    """Remove selected names without requiring -f or deleting unknown names."""
    value = "https://example.com/?id=1&utm_source=x&ref=y&flag&empty="
    assert invoke_cli(*mode, "--param-denylist", "utm_source,ref", value).strip() == (
        "https://example.com/?id=1&flag&empty="
    )


def test_cli_denylist_wins_allowlist_overlap(invoke_cli):
    """Apply removal after explicit selection through the CLI as in the API."""
    value = "https://example.com/?id=1&tag=red&drop=2"
    assert (
        invoke_cli("-p", "id,tag", "--param-denylist", "tag", value).strip()
        == "https://example.com/?id=1"
    )


def test_cli_denylist_can_remove_empty_name(invoke_cli):
    """Keep an explicit empty CLI string distinct from an absent rule."""
    assert (
        invoke_cli("--param-denylist", "", "https://example.com/?=value&keep=1").strip()
        == "https://example.com/?keep=1"
    )


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ((), "https://example.com/?keep=caf%C3%A9&ref=main"),  # codespell:ignore caf
        (("--humanize",), "https://example.com/?keep=café&ref=main"),
    ],
)
def test_cli_remove_tracking_params(invoke_cli, mode, expected):
    """Remove the preset names without enabling the domain allowlist."""
    value = (
        "https://example.com/?keep=caf%C3%A9"  # codespell:ignore caf
        "&ttclid=abc&ref=main&srsltid=xyz"
    )
    assert invoke_cli(*mode, "--remove-tracking-params", value).strip() == expected


def test_cli_tracker_removal_combines_with_custom_rules(invoke_cli):
    """Forward simultaneous preset, allowlist and denylist choices."""
    value = "https://example.com/?id=1&utm_source=email&tag=red&drop=2"
    assert (
        invoke_cli(
            "--remove-tracking-params",
            "-p",
            "id,tag,utm_source",
            "--param-denylist",
            "tag",
            value,
        ).strip()
        == "https://example.com/?id=1"
    )


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ((), "https://example.com/?a=caf%C3%A9&a=first&z=1"),  # codespell:ignore caf
        (("--humanize",), "https://example.com/?a=café&a=first&z=1"),
    ],
)
def test_cli_sort_query(invoke_cli, mode, expected):
    """Sort keys stably and combine sorting with tracker removal in both modes."""
    value = "https://example.com/?z=1&a=café&utm_source=email&a=first"
    assert (
        invoke_cli(*mode, "--sort-query", "--remove-tracking-params", value).strip()
        == expected
    )


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ((), "https://example.com/caf%C3%A9?"),  # codespell:ignore caf
        (("--humanize",), "https://example.com/café?"),
    ],
)
def test_cli_strip_fragment(invoke_cli, mode, expected):
    """Remove the fragment while keeping the requested empty query in both modes."""
    assert (
        invoke_cli(
            *mode,
            "--strip-fragment",
            "--keep-empty-components",
            "https://example.com/café?#/route?x=1",
        ).strip()
        == expected
    )


def test_cli_no_url() -> None:
    """Test CLI error when no URL is provided."""
    result = run_cli_subprocess()

    assert result.returncode != 0
    assert "the following arguments are required: url" in result.stderr


def test_cli_version_long() -> None:
    """Test version output with --version flag."""
    result = run_cli_subprocess("--version")

    assert result.returncode == 0
    assert __version__ in result.stdout
    assert not result.stderr


def test_cli_version_short() -> None:
    """Test version output with -v flag."""
    result = run_cli_subprocess("-v")

    assert result.returncode == 0
    assert __version__ in result.stdout
    assert not result.stderr


def test_cli_unicode_host_and_path() -> None:
    """Encode Unicode hosts with IDNA and paths with UTF-8 on every platform."""
    result = run_cli_subprocess("http://пример.рф/é")
    assert result.returncode == 0
    assert result.stdout.strip() == "http://xn--e1afmkfd.xn--p1ai/%C3%A9"
    assert not result.stderr


def test_cli_default_domain(invoke_cli):
    """Test adding default domain to absolute path via CLI."""
    url = "/path/to/image.png"
    expected = "https://example.com/path/to/image.png"

    output = invoke_cli("--default-domain", "example.com", url)

    assert output.strip() == expected


def test_cli_default_domain_short_arg(invoke_cli):
    """Test adding default domain using short argument."""
    url = "/path/to/image.png"
    expected = "https://example.com/path/to/image.png"

    output = invoke_cli("-d", "example.com", url)

    assert output.strip() == expected


def test_cli_default_domain_with_scheme(invoke_cli):
    """Test adding default domain with custom scheme."""
    url = "/path/to/image.png"
    expected = "http://example.com/path/to/image.png"

    output = invoke_cli("-d", "example.com", "-s", "http", url)

    assert output.strip() == expected


def test_cli_default_domain_no_effect_on_absolute_urls(invoke_cli):
    """Test default domain has no effect on absolute URLs."""
    url = "http://original-domain.com/path"
    expected = "http://original-domain.com/path"

    output = invoke_cli("-d", "example.com", url)

    assert output.strip() == expected


def test_cli_default_domain_no_effect_on_relative_paths(invoke_cli):
    """Test default domain has no effect on relative paths."""
    url = "path/to/file.html"
    # This becomes a regular URL with the default scheme
    expected = "https://path/to/file.html"

    output = invoke_cli("-d", "example.com", url)

    assert output.strip() == expected


def test_humanize_credentials_in_cli(invoke_cli):
    """Expose the same readable credential spelling through the humanization flag."""
    value = "https://us%C3%A9r%40example.net:p%C3%A4ss@example.com/"
    assert invoke_cli("--humanize", value) == (
        "https://usér%40example.net:päss@example.com/\n"
    )


@pytest.mark.parametrize("option", [[], ["--humanize"]])
def test_cli_parser_error_omits_authority(option):
    """Keep userinfo out of diagnostics on URL parsing failures."""
    result = run_cli_subprocess(*option, "https://user:example-password@[::")
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "Error normalizing URL: Invalid URL authority\n"
