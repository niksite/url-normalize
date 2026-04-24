# url-normalize

[![tests](https://github.com/niksite/url-normalize/actions/workflows/ci.yml/badge.svg)](https://github.com/niksite/url-normalize/actions/workflows/ci.yml)
[![Coveralls](https://img.shields.io/coveralls/github/niksite/url-normalize/master.svg)](https://coveralls.io/r/niksite/url-normalize)
[![PyPI](https://img.shields.io/pypi/v/url-normalize.svg)](https://pypi.org/project/url-normalize/)
[![Python Versions](https://img.shields.io/pypi/pyversions/url-normalize.svg)](https://pypi.org/project/url-normalize/)
[![License](https://img.shields.io/pypi/l/url-normalize.svg)](https://github.com/niksite/url-normalize/blob/master/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A Python library for standardizing and normalizing URLs. Ideal for database deduplication, caching, web crawling, and anywhere you need to ensure that equivalent URLs resolve to the exact same string.

```python
from url_normalize import url_normalize

# Fixes IDN, lowercases host/scheme, removes default ports, resolves path segments
url_normalize("HTTP://User:Pass@www.FOO.com:80///foo/../bar/./baz?q=1#frag")
# -> 'http://User:Pass@www.foo.com/bar/baz?q=1#frag'
```

## Features

url-normalize provides a robust URI normalization function that handles IDN domains, scheme/host lowercasing, and RFC-compliant path normalization.

- **IDN Support**: Full internationalized domain name handling (using IDNA2008 with UTS46).
- **Humanization**: Convert normalized URLs to a readable display format while preserving round-trip normalization.
- **RFC Compliance**:
  - Proper percent-encoding (minimal, uppercase hex).
  - Dot-segment removal in paths.
  - Default port and authority handling.
  - UTF-8 NFC normalization.
- **Configurable Defaults**:
  - Customizable default scheme (https by default).
  - Configurable default domain for absolute paths.
- **Query Parameter Control**:
  - Parameter filtering with allowlists.
  - Support for domain-specific parameter rules.
- **Versatile URL Handling**: Handles empty strings, double-slash URLs (//domain.tld), and shebang (#!) URLs.
- **Developer Friendly**:
  - Python 3.10+ compatibility.
  - 100% test coverage.
  - Modern type hints and string handling.

Inspired by Sam Ruby's [urlnorm.py](http://intertwingly.net/blog/2004/08/04/Urlnorm).

## Installation

Install as a library:

```sh
pip install url-normalize
```

Or install as a standalone CLI tool using [uv](https://docs.astral.sh/uv/):

```sh
uv tool install url-normalize
```

## Usage

### Python API

#### Basic Normalization

```python
from url_normalize import url_normalize

# Basic normalization (uses https by default)
print(url_normalize("www.foo.com:80/foo"))
# Output: https://www.foo.com/foo

# With custom default scheme
print(url_normalize("www.foo.com/foo", default_scheme="http"))
# Output: http://www.foo.com/foo
```

#### Query Parameter Filtering

You can strip out tracking parameters and only keep the ones you care about using allowlists.

```python
# With query parameter filtering enabled (strips all params by default)
print(url_normalize("www.google.com/search?q=test&utm_source=test", filter_params=True))
# Output: https://www.google.com/search?q=test

# With custom parameter allowlist as a list
print(url_normalize(
    "example.com?page=1&id=123&ref=test",
    filter_params=True,
    param_allowlist=["page", "id"]
))
# Output: https://example.com?page=1&id=123

# With domain-specific parameter allowlists
print(url_normalize(
    "example.com?page=1&id=123&ref=test",
    filter_params=True,
    param_allowlist={"example.com": ["page", "id"]}
))
# Output: https://example.com?page=1&id=123
```

#### Default Domain & Scheme

Useful for resolving relative URLs found on a specific page.

```python
# With default domain for absolute paths
print(url_normalize("/images/logo.png", default_domain="example.com"))
# Output: https://example.com/images/logo.png

# With default domain and custom scheme
print(url_normalize("/images/logo.png", default_scheme="http", default_domain="example.com"))
# Output: http://example.com/images/logo.png
```

#### Humanizing URLs

Convert normalized URLs back into a user-friendly format for display, particularly useful for IDN domains and percent-encoded paths.

```python
from url_normalize import url_humanize

# Human-readable display form that still normalizes back to the same URL
print(url_humanize("https://xn--e1afmkfd.xn--80akhbyknj4f/%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F"))
# Output: https://пример.испытание/Служебная

# Humanization accepts the same normalization options
print(url_humanize("/%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F", default_domain="xn--e1afmkfd.xn--80akhbyknj4f"))
# Output: https://пример.испытание/Служебная
```

### Command-line Usage

You can also use `url-normalize` directly from the terminal to process URLs.

```bash
$ url-normalize "www.foo.com:80/foo"
# Output: https://www.foo.com/foo

# With custom default scheme
$ url-normalize -s http "www.foo.com/foo"
# Output: http://www.foo.com/foo

# With query parameter filtering
$ url-normalize -f "www.google.com/search?q=test&utm_source=test"
# Output: https://www.google.com/search?q=test

# With custom allowlist
$ url-normalize -f -p page,id "example.com?page=1&id=123&ref=test"
# Output: https://example.com/?page=1&id=123

# With default domain for absolute paths
$ url-normalize -d example.com "/images/logo.png"
# Output: https://example.com/images/logo.png

# With default domain and custom scheme
$ url-normalize -d example.com -s http "/images/logo.png"
# Output: http://example.com/images/logo.png

# Human-readable display form
$ url-normalize -H "https://xn--e1afmkfd.xn--80akhbyknj4f/%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F"
# Output: https://пример.испытание/Служебная

# Via uv tool/uvx
$ uvx url-normalize www.foo.com:80/foo
# Output: https://www.foo.com:80/foo
```

## Documentation

For a complete history of changes, see [CHANGELOG.md](CHANGELOG.md).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License
