# url-normalize

[![tests](https://github.com/niksite/url-normalize/actions/workflows/ci.yml/badge.svg)](https://github.com/niksite/url-normalize/actions/workflows/ci.yml)
[![Coveralls](https://img.shields.io/coveralls/github/niksite/url-normalize/master.svg)](https://coveralls.io/r/niksite/url-normalize)
[![PyPI](https://img.shields.io/pypi/v/url-normalize.svg)](https://pypi.org/project/url-normalize/)

A Python library for standardizing and normalizing URLs with support for internationalized domain names (IDN).

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Python API](#python-api)
  - [Command Line](#command-line-usage)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Introduction

url-normalize provides a robust URI normalization function that:

- Takes care of IDN domains.
- Always provides the URI scheme in lowercase characters.
- Always provides the host, if any, in lowercase characters.
- Only performs percent-encoding where it is essential.
- Always uses uppercase A-through-F characters when percent-encoding.
- Prevents dot-segments appearing in non-relative URI paths.
- For schemes that define a default authority, uses an empty authority if the
  default is desired.
- For schemes that define an empty path to be equivalent to a path of "/",
  uses "/".
- For schemes that define a port, uses an empty port if the default is desired
- Ensures all portions of the URI are utf-8 encoded NFC from Unicode strings

Inspired by Sam Ruby's [urlnorm.py](http://intertwingly.net/blog/2004/08/04/Urlnorm)

## Features

- **IDN Support**: Full internationalized domain name handling
- **Configurable Defaults**:
  - Customizable default scheme (https by default)
  - Configurable default domain for absolute paths
- **Query Parameter Control**:
  - Parameter filtering with allowlists
  - Support for domain-specific parameter rules
- **Versatile URL Handling**:
  - Empty string URLs
  - Double slash URLs (//domain.tld)
  - Shebang (#!) URLs
- **Developer Friendly**:
  - Cross-version Python compatibility (3.8+)
  - 100% test coverage
  - Modern type hints and string handling

## Installation

```sh
pip install url-normalize
```

## Usage

### Python API

```python
from url_normalize import url_normalize

# Basic normalization (uses https by default)
print(url_normalize("www.foo.com:80/foo"))
# Output: https://www.foo.com/foo

# With custom default scheme
print(url_normalize("www.foo.com/foo", default_scheme="http"))
# Output: http://www.foo.com/foo

# With query parameter filtering enabled
print(url_normalize("www.google.com/search?q=test&utm_source=test", filter_params=True))
# Output: https://www.google.com/search?q=test

# With custom parameter allowlist as a dict
print(url_normalize(
    "example.com?page=1&id=123&ref=test",
    filter_params=True,
    param_allowlist={"example.com": ["page", "id"]}
))
# Output: https://example.com?page=1&id=123

# With custom parameter allowlist as a list
print(url_normalize(
    "example.com?page=1&id=123&ref=test",
    filter_params=True,
    param_allowlist=["page", "id"]
))
# Output: https://example.com?page=1&id=123

# With default domain for absolute paths
print(url_normalize("/images/logo.png", default_domain="example.com"))
# Output: https://example.com/images/logo.png

# With default domain and custom scheme
print(url_normalize("/images/logo.png", default_scheme="http", default_domain="example.com"))
# Output: http://example.com/images/logo.png
```

### Command-line Usage

You can also use `url-normalize` from the command line:

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
