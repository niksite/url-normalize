# url-normalize

URI Normalization function:

* Take care of IDN domains.
* Always provide the URI scheme in lowercase characters.
* Always provide the host, if any, in lowercase characters.
* Only perform percent-encoding where it is essential.
* Always use uppercase A-through-F characters when percent-encoding.
* Prevent dot-segments appearing in non-relative URI paths.
* For schemes that define a default authority, use an empty authority if the
  default is desired.
* For schemes that define an empty path to be equivalent to a path of "/",
  use "/".
* For schemes that define a port, use an empty port if the default is desired
* All portions of the URI must be utf-8 encoded NFC from Unicode strings

Inspired by Sam Ruby's [urlnorm.py](<http://intertwingly.net/blog/2004/08/04/Urlnorm>)

## Features

* IDN (Internationalized Domain Name) support
* Configurable default scheme (https by default)
* Query parameter filtering with allowlists
* Support for various URL formats including:
  * Empty string URLs
  * Double slash URLs (//domain.tld)
  * Shebang (#!) URLs
* Cross-version Python compatibility (3.8+)
* 100% test coverage
* Modern type hints and string handling

## Installation

```sh
pip install url-normalize
```

## Usage

Basic usage:

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

# With custom parameter allowlist
print(url_normalize(
    "example.com?page=1&id=123&ref=test",
    filter_params=True,
    param_allowlist={"example.com": ["page", "id"]}
))
# Output: https://example.com?page=1&id=123
print(url_normalize(
    "example.com?page=1&id=123&ref=test",
    filter_params=True,
    param_allowlist=["page", "id"]
))
# Output: https://example.com?page=1&id=123
```

## Documentation

For a complete history of changes, see [CHANGELOG.md](CHANGELOG.md).

## License

MIT License
