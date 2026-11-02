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
| Collapse repeated path slashes | `https://example.com/a//b///` | `https://example.com/a/b/` |
| Encode Unicode hosts and paths | `https://bücher.de/résumé` | `https://xn--bcher-kva.de/r%C3%A9sum%C3%A9` |
| Remove one trailing host dot, including Unicode equivalents | `https://example.com。/` | `https://example.com/` |
| Preserve encoded path separators; uppercase escape hex | `https://example.com/a%2fb` | `https://example.com/a%2Fb` |
| Preserve query order and repeated keys | `https://example.com/?b=2&a=1&a=3` | `https://example.com/?b=2&a=1&a=3` |
| Preserve explicit empty query values | `https://example.com/?flag=&flag` | `https://example.com/?flag=&flag` |
| Remove empty query and fragment components | `https://example.com/?#` | `https://example.com/` |
| Preserve an explicit relative reference | `../images/a.png` | `../images/a.png` |
| Preserve fragment routes | `https://example.com/#!/users/42` | `https://example.com/#!/users/42` |
| Preserve text-highlight syntax | `https://example.com/#:~:text=hello%20world` | `https://example.com/#:~:text=hello%20world` |

In query parameters, `+`, `%2B`, and `%20` remain distinct. Parameter filtering is disabled by default. Fragments are preserved and normalized, including hashbang routes (`#!/route`) and text directives (`#:~:text=hello`).

Fragments keep literal RFC 3986 fragment punctuation and existing ASCII escapes, with uppercase escape hex. This deliberately includes escaped letters, hyphens and tildes: fragment syntax can be interpreted before percent-decoding. For example, `#:%7E:text=hello` stays encoded instead of becoming an active text directive. Unicode text uses UTF-8 and NFC normalization as usual. Hashbang fragments are no longer converted into `_escaped_fragment_` query parameters.

Empty query and fragment delimiters are removed by default. Set `keep_empty_components=True` in either Python API, or use `--keep-empty-components` in the CLI, to retain them when your application needs to distinguish an empty component from an absent one. For example, `https://example.com/?#` stays unchanged with this option.

The option applies to query and fragment delimiters. Empty parameter values such as `flag=` are preserved with either setting. Empty query fields are still removed: `?a&&b&` becomes `?a&b`, while `?&&` disappears by default or becomes `?` with `keep_empty_components=True`.

Normalization applies consistent spelling rules; it does not establish whether two URLs serve the same content. Applications using normalized URLs as persistent cache keys or identifiers should review the [changelog](CHANGELOG.md) when upgrading.

## Python API

Both functions accept a URL as `str` or `None` and return `str` or `None`. An empty string and `None` are returned unchanged. Malformed input can raise `ValueError`, including `UnicodeError` for invalid hostnames.

The following options are keyword-only and apply to both functions:

| Option | Default | Purpose |
| --- | --- | --- |
| `default_scheme` | `"https"` | Scheme to add to bare hosts and network-path references such as `//example.com/`. Accepts uppercase, surrounding whitespace and one optional trailing colon. |
| `default_domain` | `None` | Domain to add to an absolute path such as `/images/logo.png`. |
| `filter_params` | `False` | Enable built-in domain filtering when no custom allowlist is supplied. |
| `param_allowlist` | `None` | Keep one name, a list of names, or names from a dictionary mapping domains to either form. Supplying a rule enables filtering, including an empty collection. |
| `param_denylist` | `None` | Remove names using the same rule forms as the allowlist, without an extra flag. Denied names override allowed names; an empty collection removes nothing. |
| `remove_tracking_params` | `False` | Remove a built-in set of exact, case-sensitive tracking parameter names in addition to any custom filtering. |
| `sort_query` | `False` | Sort by normalized, percent-encoded query key after filtering. Preserve the order of repeated values and each field's value separator. |
| `collapse_slashes` | `True` | Collapse repeated literal path slashes after resolving dot segments, for the schemes described below. Set `False` to preserve repeated slashes. |
| `remove_trailing_slash` | `False` | Remove the entire trailing run of literal path slashes, keeping `/` for the root. Uses the same scheme scope as `collapse_slashes`. |
| `keep_empty_components` | `False` | Keep query (`?`) and fragment (`#`) delimiters when their content is empty, including a query emptied by parameter filtering. |

Unicode URL characters always use UTF-8 percent encoding.

### Hostname boundaries

Leading dots, empty interior labels, repeated trailing dots, and dot-only hosts are preserved in both APIs. A single trailing dot is removed when other host characters precede it. ASCII dots and their IDNA equivalents (`。`, `．`, `｡`) follow the same rule:

| Input | Result |
| --- | --- |
| `https://example.com./` | `https://example.com/` |
| `https://.example.com/` | `https://.example.com/` |
| `https://a..example.com/` | `https://a..example.com/` |
| `https://example.com../` | `https://example.com../` |
| `https://./` | `https://./` |
| `https://../` | `https://../` |
| `https://a。。example.com/` | `https://a..example.com/` |

This hostname policy also applies to `default_domain` and custom `param_allowlist` domain keys. Entries for `.example.com` and `example.com` remain distinct; an unusual host can have its own explicit allowlist entry. The CLI uses the same normalization policy.

Preservation does not establish DNS validity. The generic registered-name syntax in [RFC 3986 section 3.2.2](https://www.rfc-editor.org/rfc/rfc3986.html#section-3.2.2) is broader than DNS hostname syntax. Applications that require DNS-valid hostnames should validate them separately. Empty hosts in local file URLs and path references remain supported.

### IPv6 addresses

Equivalent bracketed IPv6 addresses use a consistent spelling: lowercase hexadecimal, no leading zeroes in groups, and `::` for the longest run of at least two zero groups (the first run wins a tie). These rules follow [RFC 5952 section 4](https://www.rfc-editor.org/rfc/rfc5952.html#section-4).

| Input | Result |
| --- | --- |
| `https://[2001:0DB8:0:0:0:0:0:1]/` | `https://[2001:db8::1]/` |
| `https://[FE80:0:0:0:0:0:0:ABCD%25EthA]/` | `https://[fe80::abcd%25EthA]/` |
| `https://[::FFFF:C000:280]/` | `https://[::ffff:192.0.2.128]/` |

Zone identifiers, including their case and percent-encoding spelling, are preserved. IPv4-mapped IPv6 addresses use `::ffff:` followed by dotted decimal; other IPv6 addresses use hexadecimal groups. IPvFuture literals retain their existing case normalization. These rules apply to both APIs, the CLI, `default_domain`, and allowlist keys. Expanded and compressed allowlist keys now match the same address; when entries conflict, the canonical key takes precedence.

### Port normalization

ASCII decimal ports lose leading zeroes, and scheme defaults are removed: `http://example.com:0080/` becomes `http://example.com/`, while `https://example.com:0080/` becomes `https://example.com:80/`. An empty port and its colon are removed too. Numeric normalization uses string operations, including for heavily padded numbers.

Nonempty parsed ports must contain only ASCII digits (`0–9`), following [RFC 3986 section 3.2.3](https://www.rfc-editor.org/rfc/rfc3986.html#section-3.2.3). Other port text raises `ValueError: Port must contain only ASCII digits`. For example, `http://example.com:abc/`, `http://example.com:８０/`, `http://example.com:²/`, and `http://example.com:-1/` are rejected. Percent-encoded digits are rejected too; Unicode digits are not converted to ASCII port numbers.

The check applies to ports in URL authorities, including custom schemes and `default_domain`. Colons elsewhere, such as `mailto:user:abc@example.com` and `./example.com:abc/path`, retain their existing behavior. Both Python APIs use the same rule. The CLI exits with status 1, writes a diagnostic to stderr and prints no URL when port syntax is invalid.

Normalization does not check the transport's port range: `https://example.com:065536/` becomes `https://example.com:65536/`. Range validation remains the caller's responsibility.

### Path slashes and dot segments

Repeated path slashes collapse by default, including trailing runs. Use `collapse_slashes=False` to preserve empty path segments when they matter to your application:

```python
from url_normalize import url_normalize

url = "https://example.com/a//b///"
print(url_normalize(url))
# Output: https://example.com/a/b/

print(url_normalize(url, collapse_slashes=False))
# Output: https://example.com/a//b///

print(url_normalize(url, remove_trailing_slash=True))
# Output: https://example.com/a/b

print(url_normalize(url, collapse_slashes=False, remove_trailing_slash=True))
# Output: https://example.com/a//b

print(url_normalize("https://example.com/a//../b"))
# Output: https://example.com/a/b
```

Path operations run in order: resolve dot segments, collapse slash runs unless disabled, then optionally remove trailing slashes. In `/a//../b`, `..` removes the empty segment, leaving `/a/b` with either collapse setting. Encoded separators such as `%2F` remain encoded. Query and fragment handling follows the usual normalization rules.

Collapsing retains a single trailing slash. Enable `remove_trailing_slash` to remove it as well; `/a//b///` then becomes `/a/b`. With `collapse_slashes=False`, trailing-slash removal preserves internal slash runs, producing `/a//b`. The root remains `/`, including when the input path consists entirely of slashes.

These path operations apply to HTTP, HTTPS, WS, WSS, FTP, file URLs and path references. Document-relative paths resolve internal dots while retaining leading `../` segments that need a base URL. Other schemes keep their existing path handling. When collapsing is disabled, a root-relative path that would start with `//` retains a `/.` prefix to avoid being interpreted as a hostname; for example, `/a/..//b` becomes `/.//b`.

### Query escapes

Percent-encoded reserved characters stay encoded in query keys and values, with uppercase hexadecimal digits. A literal `/`, `;`, or other query punctuation stays literal; its escaped form is kept distinct because applications can assign it a delimiter role ([RFC 3986 section 2.2](https://www.rfc-editor.org/rfc/rfc3986.html#section-2.2)). Unreserved escapes such as `%7E` become `~`.

| Input | `url_normalize()` | `url_humanize()` |
| --- | --- | --- |
| `https://example.com/?q=a%2fb` | `https://example.com/?q=a%2Fb` | `https://example.com/?q=a%2Fb` |
| `https://example.com/?q=a/b` | `https://example.com/?q=a/b` | `https://example.com/?q=a/b` |
| `https://example.com/?q=a%3Bb` | `https://example.com/?q=a%3Bb` | `https://example.com/?q=a%3Bb` |
| `https://example.com/?q=%C3%A9%2F%C3%B1` | `https://example.com/?q=%C3%A9%2F%C3%B1` | `https://example.com/?q=é%2Fñ` |
| `https://example.com/?q=%7Ehello` | `https://example.com/?q=~hello` | `https://example.com/?q=~hello` |

Parameter order is preserved by default. Duplicates and the distinction between `flag` and `flag=` are preserved with either query-sorting setting. Literal `+`, encoded `%2B`, and `%20` remain distinct in normalized output. Unicode still uses NFC normalization and UTF-8 encoding; these guarantees do not imply byte-for-byte preservation for signed URLs. The CLI uses the same rules in both modes.

### Query parameter filtering

Supplying `param_allowlist` keeps only the allowed parameters; no extra flag is needed. Use `filter_params=True` without a custom allowlist to select the built-in domain rules, which cover Google, Bing, Baidu, and YouTube; see the [domain rules](url_normalize/param_allowlist.py) for their parameter names.

`None` means no custom rule. An empty list or dictionary enables filtering and removes all query parameters. An explicit rule takes precedence even if `filter_params=False`; to turn filtering off, omit the rule or pass `param_allowlist=None` with `filter_params=False`.

Filtering that removes every parameter also removes the query delimiter by default. With `keep_empty_components=True`, the delimiter remains even when filtering empties the query. For example, filtering `https://example.com/?drop=1#` with no matching allowed name produces `https://example.com/` by default or `https://example.com/?#` with this option.

**Unknown domains have an empty default allowlist**, so filtering removes all their query parameters unless you supply a custom rule. A custom allowlist replaces the built-in rules.

```python
from url_normalize import url_normalize

# Use the built-in Google rule.
result = url_normalize(
    "www.google.com/search?q=test&utm_source=test", filter_params=True
)
print(result)
# Output: https://www.google.com/search?q=test

# Keep one parameter name on any domain.
result = url_normalize(
    "example.com/?id=123&i=456&d=789",
    param_allowlist="id",
)
print(result)
# Output: https://example.com/?id=123

# Apply a list of allowed names to any domain.
result = url_normalize(
    "example.com/?page=1&id=123&ref=test",
    param_allowlist=["page", "id"],
)
print(result)
# Output: https://example.com/?page=1&id=123

# Use domain-specific rules, including Unicode parameter names.
result = url_normalize(
    "https://example.com/?r%C3%A9sum%C3%A9=1&drop=2",
    param_allowlist={"example.com": "résumé"},
)
print(result)
# Output: https://example.com/?r%C3%A9sum%C3%A9=1
```

A string is one complete name: `"id"` means the same as `["id"]`, and `{"example.com": "id"}` means the same as `{"example.com": ["id"]}`. Strings are not split on commas; use `["page", "id"]` for two names, while `"page,id"` selects the literal name `page,id`. An empty string selects the empty parameter name (`?=value`); an empty list allows no names. Domain dictionaries may mix strings and lists. The CLI retains its comma-separated `--param-allowlist` format, enables filtering without `-f`, and treats `-p ""` as selecting the empty parameter name.

Allowed names use the same normalization as query keys, including Unicode and spaces. Reserved escapes remain distinct: `param_allowlist=["a/b"]` matches `a/b=1`, while `param_allowlist=["a%2fb"]` matches `a%2Fb=1`. Domain rules match normalized hostnames and ignore a leading `www.` and the port. Rules do not automatically apply to other subdomains.

To remove selected names while keeping all other parameters, supply `param_denylist`. It accepts the same single-name, list and domain-map forms and uses the same case-sensitive name matching. It does not enable the built-in allowlist. An empty denylist or a domain map without a matching rule removes nothing. Names are literal: `"utm_*"` is not a wildcard.

```python
result = url_normalize(
    "https://example.com/products?id=123&utm_source=newsletter&variant=blue",
    param_denylist="utm_source",
)
print(result)
# Output: https://example.com/products?id=123&variant=blue

# Narrow the built-in Google rule without copying its allowed names.
result = url_normalize(
    "https://google.com/search?q=hello&ie=UTF-8&utm_source=newsletter",
    filter_params=True,
    param_denylist="ie",
)
print(result)
# Output: https://google.com/search?q=hello
```

When both rules apply, a parameter must be allowed and must not be denied. For example, `param_allowlist=["id", "tag"]` with `param_denylist="tag"` retains only `id`. Removal preserves the order, duplicates and value separators of the remaining parameters; ordinary URL normalization and any requested query sorting still apply. Removing the last parameter follows `keep_empty_components`, just like allowlist filtering. These rules also apply to `url_humanize()`.

### Tracking parameter removal

Set `remove_tracking_params=True` to remove known attribution parameters on any domain while retaining other query names. This works in both Python APIs and does not enable the built-in domain allowlist. It is disabled by default because removing attribution changes campaign measurement.

```python
from url_normalize import url_normalize

url = "https://example.com/product?id=123&ttclid=abc&srsltid=xyz"
print(url_normalize(url))
# Output: https://example.com/product?id=123&ttclid=abc&srsltid=xyz

print(url_normalize(url, remove_tracking_params=True))
# Output: https://example.com/product?id=123

print(
    url_normalize(
        "https://example.com/search?ref=main&source=books&utm_source=email",
        remove_tracking_params=True,
    )
)
# Output: https://example.com/search?ref=main&source=books
```

The preset removes these exact names, based on provider documentation:

| Family | Parameter names | Sources |
| --- | --- | --- |
| UTM | `utm_id`, `utm_source`, `utm_medium`, `utm_campaign`, `utm_source_platform`, `utm_term`, `utm_content`, `utm_creative_format`, `utm_marketing_tactic`, `utm_referrer` | [Google Analytics](https://support.google.com/analytics/answer/10917952), [Analytics schema](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema), [Yandex](https://yandex.com/support/metrica/en/general/source-tags) |
| Google attribution | `gclid`, `dclid`, `gbraid`, `wbraid`, `gad_source`, `gad_campaignid`, `srsltid` | [Analytics identifiers](https://support.google.com/analytics/answer/16479993?hl=en), [Google Ads](https://support.google.com/google-ads/answer/10417364?hl=en), [Merchant Center](https://support.google.com/merchants/answer/15191080) |
| Other click identifiers | `fbclid`, `msclkid`, `ttclid`, `twclid`, `yclid` | [Meta](https://github.com/facebook/capi-param-builder/blob/main/client_js/README.md), [Microsoft](https://learn.microsoft.com/en-us/advertising/guides/uet-conversion-api-integration), [TikTok](https://ads.tiktok.com/help/article/tiktok-click-id?lang=en), [X](https://business.x.com/en/help/campaign-measurement-and-analytics/conversion-tracking-for-websites), [Yandex](https://yandex.com/support/metrica/en/general/source-tags) |
| Mailchimp | `mc_cid`, `mc_eid` | [Mailchimp](https://mailchimp.com/developer/marketing/concepts/e-commerce/) |
| Matomo / Piwik | `mtm_campaign`, `mtm_keyword`, `mtm_source`, `mtm_medium`, `mtm_content`, `mtm_cid`, `mtm_group`, `mtm_placement`, `mtm_kwd`, `matomo_campaign`, `pk_campaign`, `piwik_campaign`, `pk_kwd`, `piwik_kwd`, `pk_keyword`, `matomo_kwd` | [Campaign parameters](https://matomo.org/faq/reports/advanced-how-to-manually-build-campaign-tracking-urls/), [Default parameters](https://matomo.org/faq/how-to/faq_120/), [Aliases](https://plugins.matomo.org/MarketingCampaignsReporting) |

Matching uses normalized query keys: `%75tm_source` matches `utm_source`. Names remain case-sensitive, so `UTM_SOURCE` is retained. There are no prefix or wildcard rules: `utm_custom` and `gclid_extra` remain. Generic names such as `ref`, `source`, `keyword`, and `session_id` are retained because they can select content or identify a session. The preset only examines query keys; it does not remove matching words from paths, parameter values or fragment routes.

The preset adds removals to `param_denylist` and takes precedence over `param_allowlist`. An empty custom denylist does not disable it. To retain a preset name, leave this option off and supply your own `param_denylist`. Retained parameters keep their order unless `sort_query=True` is requested. Duplicates and value separators survive either setting, and an emptied query follows `keep_empty_components`.

### Query sorting

Use `sort_query=True` in either Python API, or `--sort-query` in the CLI, when your application treats the order of different query keys as irrelevant. This can produce common cache or deduplication keys. Sorting is disabled by default because some applications depend on query order.

```python
from url_normalize import url_normalize

url = "https://example.com/search?tag=red&page=2&tag=blue"
print(url_normalize(url))
# Output: https://example.com/search?tag=red&page=2&tag=blue

print(url_normalize(url, sort_query=True))
# Output: https://example.com/search?page=2&tag=red&tag=blue
```

Sorting runs after normalization and filtering. It compares the exact normalized, percent-encoded keys in ascending, case-sensitive order. An empty key sorts first; percent escapes sort before letters; uppercase ASCII letters sort before lowercase ones. For example, `https://example.com/?z=1&é=2&a=3` becomes `https://example.com/?%C3%A9=2&a=3&z=1`. `url_humanize()` displays the same order as `https://example.com/?é=2&a=3&z=1`.

Equal normalized keys retain their original order, including when normalization makes `%61` and `a` equal. Values are never used as a sorting key. Thus `tag=red&tag=blue` remains distinct from `tag=blue&tag=red`. Sorting preserves duplicates, each occurrence of `flag` versus `flag=`, and the usual escape distinctions such as `+`, `%2B`, and `%20`. It applies only to query fields; paths and fragment routes follow their existing policies. Allowlist, denylist and tracker removal can all be combined with sorting, and empty queries still follow `keep_empty_components`.

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

`default_scheme` accepts a scheme name such as `https`, `HTTP`, or `git+ssh`, optionally followed by one colon. Surrounding whitespace is removed and the name is lowercased. Names follow [RFC 3986 section 3.1](https://www.rfc-editor.org/rfc/rfc3986.html#section-3.1).

```python
print(url_normalize("example.com/path", default_scheme=" HTTPS: "))
# Output: https://example.com/path
```

Malformed values such as `https://`, `https::`, or an empty scheme raise `ValueError`; non-string values raise `TypeError`. For nonempty URL input this check also applies when the default is unused, including URLs that already have a scheme and relative references. Empty input and `None` retain their existing pass-through behavior. The CLI applies the same rules and reports configuration errors with exit status 1.

### Relative references

Explicit references starting with `./`, `../`, `?`, or `#` stay relative in both APIs and the CLI. The standalone paths `.` and `..`, including query or fragment suffixes, also stay relative. `default_domain` and `default_scheme` do not turn these references into absolute URLs.

```python
from url_normalize import url_normalize

print(url_normalize("../images/a.png"))
# Output: ../images/a.png

print(url_normalize("./a//../b"))
# Output: ./a/b

print(url_normalize("../a//../b///"))
# Output: ../a/b/

print(url_normalize("../a//../b///", collapse_slashes=False))
# Output: ../a/b///

print(url_normalize("../a//../b///", remove_trailing_slash=True))
# Output: ../a/b

print(url_normalize("?q=é#section"))
# Output: ?q=%C3%A9#section
```

Document-relative paths use the same operation order: resolve internal dots, collapse slashes by default, then optionally remove trailing slashes. Unresolved parents stay relative: `../a/../../b` becomes `../../b`. The `./` prefix keeps an ordinary path from being interpreted as a hostname or scheme; `./a/../b` becomes `./b`, and `./a/../this:that` becomes `./this:that`. With collapsing disabled, `./a/..//b` becomes `.//b`, preserving its empty segment without changing it into a root-relative path.

Paths that reduce to the current directory retain a nonempty reference: `./a/..` becomes `./`, or `.` with `remove_trailing_slash=True`. Similarly, `../a/..` becomes `../`, or `..` with trailing-slash removal. Percent encoding, Unicode handling, query filtering, and empty-component policy still apply. Use `keep_empty_components=True` when empty `?` or `#` delimiters matter to later resolution.

To obtain an absolute URL, [resolve the reference against a base URL](https://www.rfc-editor.org/rfc/rfc3986.html#section-5.2.2). For example:

```python
from urllib.parse import urljoin

from url_normalize import url_normalize

absolute = urljoin("https://example.com/docs/page.html", "../images/a.png")
print(url_normalize(absolute))
# Output: https://example.com/images/a.png
```

Bare inputs retain host inference: `site/page` becomes `https://site/page`. Use `./site/page` to explicitly identify a document-relative path. Network-path references such as `//example.com/page` receive the selected default scheme.

### Human-readable URLs

`url_humanize()` normalizes its input, then decodes components only when the display URL normalizes back to the same result. Some escapes therefore remain encoded. In fragments, ASCII escapes remain encoded even when a round trip would allow decoding; safe Unicode can still become readable. For example, `#:~:text=r%C3%A9sum%C3%A9%2Dnotes` becomes `#:~:text=résumé%2Dnotes`, preserving the encoded hyphen as text rather than directive syntax. Fragment spaces remain `%20`.

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
url-normalize -p page,id "example.com/?page=1&id=123&ref=test"
# Output: https://example.com/?page=1&id=123

# Remove selected parameters while retaining all other names.
url-normalize --param-denylist utm_source,ref "example.com/?id=123&utm_source=newsletter&ref=email"
# Output: https://example.com/?id=123

# Remove the built-in tracker names while retaining other parameters.
url-normalize --remove-tracking-params "https://example.com/product?id=123&ttclid=abc&srsltid=xyz"
# Output: https://example.com/product?id=123

# Sort query keys while preserving the order of repeated values.
url-normalize --sort-query "https://example.com/search?tag=red&page=2&tag=blue"
# Output: https://example.com/search?page=2&tag=red&tag=blue

# Supply a domain and scheme for an absolute path.
url-normalize -d example.com -s http "/images/logo.png"
# Output: http://example.com/images/logo.png

# Collapse repeated slashes in the path (the default).
url-normalize "https://example.com/a//b///"
# Output: https://example.com/a/b/

# Preserve repeated slashes in the path.
url-normalize --no-collapse-slashes "https://example.com/a//b///"
# Output: https://example.com/a//b///

# Remove trailing slashes while preserving internal empty segments.
url-normalize --no-collapse-slashes --remove-trailing-slash "https://example.com/a//b///"
# Output: https://example.com/a//b

# Retain explicitly empty query and fragment components.
url-normalize --keep-empty-components "https://example.com/?#"
# Output: https://example.com/?#

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

Type checking uses ty for the package, targeting the minimum Python version from `requires-python` and all platforms. The pre-commit hook uses the version and dependencies in `uv.lock`. To run type checking alone, use `uv run --locked --extra dev ty check`.

Alongside exact-output tests, Hypothesis generates 200 HTTP(S) URL and option combinations per property to check normalization idempotence, humanization round trips, and empty-component policy. Another 200 explicit relative references check stable output, slash options, and the absence of invented schemes or authorities. Generation is deterministic for a given Python version, Hypothesis version, and test definition. Add any minimized failures as explicit regression tests.

## Changelog and license

See [CHANGELOG.md](CHANGELOG.md) for release history and upgrade notes. Distributed under the [MIT License](LICENSE).

Inspired by Sam Ruby's [urlnorm.py](http://intertwingly.net/blog/2004/08/04/Urlnorm).
