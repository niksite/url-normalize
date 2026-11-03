"""Exercise the installed package without pytest or access to the checkout."""

import os
import subprocess
import sys
import sysconfig
from importlib.metadata import distribution
from pathlib import Path

import url_normalize
from url_normalize import url_humanize
from url_normalize import url_normalize as normalize


def cli(*args: str) -> subprocess.CompletedProcess[bytes]:
    """Launch the installed entry point and capture the actual UTF-8 bytes."""
    filename = "url-normalize.exe" if os.name == "nt" else "url-normalize"
    executable = Path(sysconfig.get_path("scripts")) / filename
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONIOENCODING"] = "cp1252"
    return subprocess.run(  # noqa: S603 - exercise this environment's installed CLI
        [str(executable), *args], env=env, capture_output=True, check=False, timeout=30
    )


def main() -> None:
    """Check metadata, public imports, Unicode output and representative options."""
    package = Path(url_normalize.__file__).resolve().parent
    assert package.is_relative_to(Path(sys.prefix).resolve()), package
    assert (package / "py.typed").is_file(), "The installed package must ship py.typed"
    metadata = distribution("url-normalize")
    assert metadata.version == sys.argv[1] == url_normalize.__version__
    assert any(
        entry.name == "url-normalize" and entry.value == "url_normalize.cli:main"
        for entry in metadata.entry_points
        if entry.group == "console_scripts"
    )

    value = "HTTP://Example.COM:80/a/../b"
    assert normalize(value) == "http://example.com/b"
    assert normalize(None) is None
    assert url_humanize("") == ""
    unicode_url = "https://example.com/日本語?q=café"
    encoded = (
        "https://example.com/%E6%97%A5%E6%9C%AC%E8%AA%9E"
        "?q=caf%C3%A9"  # codespell:ignore caf
    )
    assert normalize(unicode_url) == encoded
    assert url_humanize(encoded) == unicode_url
    assert (
        normalize(
            "https://example.com/?page=2&id=1&ref=email",
            param_allowlist=("page", "id", "ref"),
            param_denylist=frozenset({"ref"}),
        )
        == "https://example.com/?page=2&id=1"
    )

    result = cli("--version")
    assert result.returncode == 0, result.stderr
    assert result.stderr == b"", result.stderr
    # Windows launchers may retain .exe in argparse's displayed program name.
    assert result.stdout.decode("utf-8").strip() in {
        f"url-normalize {metadata.version}",
        f"url-normalize.exe {metadata.version}",
    }, result.stdout

    for arguments, expected in [
        ((unicode_url,), encoded),
        (("--humanize", encoded), unicode_url),
        (
            (
                "../a//b/?z=2&id=1&id=3&ref=email&utm_source=test#section",
                "--param-allowlist",
                "z,id,ref,utm_source",
                "--param-denylist",
                "ref",
                "--remove-tracking-params",
                "--sort-query",
                "--no-collapse-slashes",
                "--remove-trailing-slash",
                "--strip-fragment",
                "--keep-empty-components",
            ),
            "../a//b?id=1&id=3&z=2",
        ),
    ]:
        result = cli(*arguments)
        assert result.returncode == 0, result.stderr
        assert result.stderr == b"", result.stderr
        assert result.stdout.decode("utf-8").splitlines() == [expected], result.stdout

    result = cli("https://example.com/", "--日本語")
    assert result.returncode == 2, result  # noqa: PLR2004 - argparse usage error
    assert result.stdout == b"", result.stdout
    assert "日本語" in result.stderr.decode("utf-8"), result.stderr
    print(f"Installed API, CLI and metadata checks passed: {package}")  # noqa: T201


if __name__ == "__main__":
    main()
