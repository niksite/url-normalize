# url-normalize

[![tests](https://github.com/niksite/url-normalize/actions/workflows/ci.yml/badge.svg)](https://github.com/niksite/url-normalize/actions/workflows/ci.yml)
[![Coveralls](https://img.shields.io/coveralls/github/niksite/url-normalize/master.svg)](https://coveralls.io/r/niksite/url-normalize)
[![PyPI](https://img.shields.io/pypi/v/url-normalize.svg)](https://pypi.org/project/url-normalize/)
[![Python Versions](https://img.shields.io/pypi/pyversions/url-normalize.svg)](https://pypi.org/project/url-normalize/)
[![License](https://img.shields.io/pypi/l/url-normalize.svg)](https://github.com/niksite/url-normalize/blob/master/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Normalize URL spelling consistently for storage, comparison, and display. Use `url_normalize()` for normalized URLs and `url_humanize()` for readable display URLs.

Requires **Python 3.11 or newer**. Normalization operates on URL text; it does not fetch pages or follow redirects.

## Installation

Install the library and CLI:

```sh
python -m pip install url-normalize
```

Or install the CLI in its own environment with [uv](https://docs.astral.sh/uv/):

```sh
uv tool install url-normalize
```

## Quick start

```python
from url_normalize import url_normalize

print(url_normalize("HTTP://Example.COM:80/a/../b"))
# Output: http://example.com/b

print(url_normalize("bücher.de/résumé"))
# Output: https://xn--bcher-kva.de/r%C3%A9sum%C3%A9
```

From the terminal:

```sh
url-normalize "HTTP://Example.COM:80/a/../b"
# Output: http://example.com/b
```

## Normalization behavior

| Behavior | Input | Output |
| --- | --- | --- |
| Add a missing scheme | `example.com` | `https://example.com/` |
| Lowercase scheme and host; remove a default port | `HTTP://Example.COM:80/` | `http://example.com/` |
| Resolve dot segments | `https://example.com/a/../b` | `https://example.com/b` |
| Encode Unicode hosts and paths | `https://bücher.de/résumé` | `https://xn--bcher-kva.de/r%C3%A9sum%C3%A9` |
| Remove trailing host dots, including Unicode equivalents | `https://example.com。/` | `https://example.com/` |
| Preserve encoded path separators; uppercase escape hex | `https://example.com/a%2fb` | `https://example.com/a%2Fb` |
| Preserve query order and repeated keys | `https://example.com/?b=2&a=1&a=3` | `https://example.com/?b=2&a=1&a=3` |
| Preserve explicit empty query values | `https://example.com/?flag=&flag` | `https://example.com/?flag=&flag` |

In query parameters, `+`, `%2B`, and `%20` remain distinct. Parameter filtering is disabled by default. Fragments are preserved and normalized; hashbang fragments (`#!`) are converted to the `_escaped_fragment_` query parameter.

Normalization applies consistent spelling rules; it does not establish whether two URLs serve the same content. Applications using normalized URLs as persistent cache keys or identifiers should review the [changelog](CHANGELOG.md) when upgrading.

## Python API

Both functions accept a URL as `str` or `None` and return `str` or `None`. An empty string and `None` are returned unchanged. Malformed input can raise `ValueError`, including `UnicodeError` for invalid hostnames.

The following options are keyword-only and apply to both functions:

| Option | Default | Purpose |
| --- | --- | --- |
| `default_scheme` | `"https"` | Scheme to add when the URL has none. |
| `default_domain` | `None` | Domain to add to an absolute path such as `/images/logo.png`. |
| `filter_params` | `False` | Retain only allowlisted query parameters. |
| `param_allowlist` | `None` | Override built-in rules with a list of names or a dictionary mapping domains to lists. Requires `filter_params=True`. |

Unicode URL characters always use UTF-8 percent encoding.

### Query parameter filtering

With `filter_params=True`, only explicitly allowed parameters remain. Built-in rules cover Google, Bing, Baidu, and YouTube; see the [domain rules](url_normalize/param_allowlist.py) for their parameter names.

**Unknown domains have an empty default allowlist**, so filtering removes all their query parameters unless you supply a custom rule. A custom allowlist replaces the built-in rules.

```python
from url_normalize import url_normalize

# Use the built-in Google rule.
result = url_normalize(
    "www.google.com/search?q=test&utm_source=test", filter_params=True
)
print(result)
# Output: https://www.google.com/search?q=test

# Apply a list of allowed names to any domain.
result = url_normalize(
    "example.com/?page=1&id=123&ref=test",
    filter_params=True,
    param_allowlist=["page", "id"],
)
print(result)
# Output: https://example.com/?page=1&id=123

# Use domain-specific rules, including Unicode parameter names.
result = url_normalize(
    "https://example.com/?r%C3%A9sum%C3%A9=1&drop=2",
    filter_params=True,
    param_allowlist={"example.com": ["résumé"]},
)
print(result)
# Output: https://example.com/?r%C3%A9sum%C3%A9=1
```

Allowed names use the same normalization as query keys, including Unicode and spaces. Domain rules match normalized hostnames and ignore a leading `www.` and the port. Rules do not automatically apply to other subdomains.

### Default domain and scheme

Use `default_domain` for paths starting with a single `/`. URLs starting with `//` already specify their host. This option does not resolve relative paths such as `../images/logo.png` against a page URL.

```python
from url_normalize import url_normalize

result = url_normalize(
    "/images/logo.png", default_domain="example.com", default_scheme="http"
)
print(result)
# Output: http://example.com/images/logo.png
```

### Human-readable URLs

`url_humanize()` normalizes its input, then decodes components only when the display URL normalizes back to the same result. Some escapes therefore remain encoded.

```python
from url_normalize import url_humanize, url_normalize

normalized = "https://xn--bcher-kva.de/r%C3%A9sum%C3%A9"
readable = url_humanize(normalized)
print(readable)
# Output: https://bücher.de/résumé

assert url_normalize(readable) == normalized
```

## Command-line usage

The CLI accepts one URL per invocation and prints the result to standard output. Quote URLs containing shell characters such as `&`.

```sh
# Keep selected query parameters.
url-normalize -f -p page,id "example.com/?page=1&id=123&ref=test"
# Output: https://example.com/?page=1&id=123

# Supply a domain and scheme for an absolute path.
url-normalize -d example.com -s http "/images/logo.png"
# Output: http://example.com/images/logo.png

# Display a readable URL.
url-normalize -H "https://xn--bcher-kva.de/r%C3%A9sum%C3%A9"
# Output: https://bücher.de/résumé
```

Use `url-normalize --help` for all options and `url-normalize --version` for the installed version. Normalization errors are written to standard error with exit status 1; invalid command-line arguments use exit status 2.

To run without a persistent tool installation:

```sh
uvx url-normalize "example.com"
# Output: https://example.com/
```

## Contributing

After cloning the repository, install the development dependencies and run the checks with [uv](https://docs.astral.sh/uv/):

```sh
uv sync --locked --extra dev
uv run --locked --extra dev python -m pytest
uv run --locked --extra dev pre-commit run --all-files
```

The test suite requires 100% statement coverage. CI tests Python 3.11 through 3.15 on Linux, macOS, and Windows. Please include regression tests with bug fixes.

## Changelog and license

See [CHANGELOG.md](CHANGELOG.md) for release history and upgrade notes. Distributed under the [MIT License](LICENSE).

Inspired by Sam Ruby's [urlnorm.py](http://intertwingly.net/blog/2004/08/04/Urlnorm).
