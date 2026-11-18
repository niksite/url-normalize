"""Install a built artifact in isolation and check the public consumer surface."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(*command: str | Path, cwd: Path) -> None:
    """Run an explicit tool command without inheriting a source import path."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    subprocess.run(command, cwd=cwd, env=env, check=True)  # noqa: S603


def main() -> None:
    """Check an archive in a fresh environment without development extras."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", type=Path, default=ROOT / "dist")
    parser.add_argument(
        "--kind",
        choices=("wheel", "sdist"),
        default=os.getenv("DISTRIBUTION_KIND", "wheel"),
    )
    parser.add_argument(
        "--check-types", action="store_true", default=os.getenv("CHECK_TYPES") == "true"
    )
    args = parser.parse_args()
    pattern = "*.whl" if args.kind == "wheel" else "*.tar.gz"
    archives = list(args.dist_dir.resolve().glob(pattern))
    if len(archives) != 1:
        parser.error(
            f"Expected one {pattern} in {args.dist_dir}, found {len(archives)}"
        )
    uv = shutil.which("uv")
    if uv is None:
        parser.error("uv must be installed to create the isolated environment")
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    expected_version = metadata["project"]["version"]

    with tempfile.TemporaryDirectory(prefix="url-normalize-distribution-") as directory:
        work = Path(directory)
        environment = work / "venv"
        scripts = environment / ("Scripts" if os.name == "nt" else "bin")
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        run(uv, "venv", "--python", sys.executable, environment, cwd=work)
        run(uv, "pip", "install", "--python", python, archives[0], cwd=work)
        run(
            python,
            "-I",
            ROOT / "tests/packaging/smoke.py",
            expected_version,
            cwd=work,
        )
        if args.check_types:
            lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
            ty_version = next(
                p["version"] for p in lock["package"] if p["name"] == "ty"
            )
            run(uv, "pip", "install", "--python", python, f"ty=={ty_version}", cwd=work)
            consumers = work / "consumers"
            shutil.copytree(
                ROOT / "tests/typing",
                consumers,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
            ty = scripts / ("ty.exe" if os.name == "nt" else "ty")
            # Avoid inheriting a parent project's source include/exclude rules.
            config = work / "ty.toml"
            config.touch()
            run(
                ty,
                "check",
                "--config-file",
                config,
                "--python",
                environment,
                "--python-version",
                "3.11",
                "--python-platform",
                "all",
                "--error",
                "unused-ignore-comment",
                consumers,
                cwd=work,
            )


if __name__ == "__main__":
    main()
