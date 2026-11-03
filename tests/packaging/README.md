# Installed distribution checks

The main pytest suite tests the source checkout. These separate checks install a
built wheel or source archive into a fresh temporary environment and run outside
the checkout. They verify installed imports, version metadata, `py.typed`, the
generated CLI launcher, UTF-8 stdout/stderr and representative API/CLI options.

Run locally after building:

```sh
uv build
uv run --locked --extra dev python tests/packaging/check_distribution.py --kind wheel --check-types
uv run --locked --extra dev python tests/packaging/check_distribution.py --kind sdist
```

Use `--dist-dir PATH` to select another artifact directory. Exactly one archive of
the selected kind must be present. Install and build dependencies may require
network access. Temporary environments are removed when each check finishes.

The smoke process uses isolated Python mode and verifies that the imported
package lives inside its temporary environment. CLI checks launch that
environment's installed executable, capturing bytes with `PYTHONIOENCODING=cp1252`
to exercise UTF-8 output even under a legacy stream encoding.

`--check-types` copies the existing public consumer fixtures outside the checkout
and checks them against the installed package using the ty version in `uv.lock`.
It includes both positive assertions and rejected-call expectations. This runs
after runtime checks so installing ty cannot supply a missing runtime dependency.

CI tests wheels on Linux, macOS and Windows with Python 3.11 to cover the minimum
Python version and each platform's CLI launcher. It also builds and installs the
source archive on Linux with Python 3.15. Installed typing runs once, targeting
Python 3.11 and all platforms. The full source suite still covers every supported
Python version on all three platforms. Publishing requires these distribution
checks as well as the existing source tests and coverage completion.
