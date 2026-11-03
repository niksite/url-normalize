# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Upgrade notes

Path normalization now resolves dot segments before collapsing repeated slashes. For example, `/a//../b` becomes `/a/b`, whereas the old algorithm produced `/b`. This changes normalized URLs and requires a major release under the project's versioning policy. Applications using persisted cache keys or deduplication identifiers should rebuild them from original URLs.

Repeated path slashes collapse by default. Use `collapse_slashes=False` in either Python API, or `--no-collapse-slashes` in the CLI, to preserve them. Dot segments are resolved first with either setting, including internal dots in document-relative paths. Previously collapsed URLs cannot recover their lost empty segments; apply preservation to original URLs when available.

Explicit relative references now stay relative: `../images/a.png`, `./a`, `?q=1`, and `#section` no longer gain an empty HTTPS authority. The paths `.` and `..` are also preserved. Internal dots are resolved while leading unresolved `../` segments remain. The same slash options apply: `../a//../b///` becomes `../a/b/` by default, `../a/b///` with `collapse_slashes=False`, or `../a/b` with trailing-slash removal. An explicit `./` prefix protects ordinary relative results from host/scheme inference, and a path reduced to the current directory remains `./` (or `.` with trailing-slash removal). Bare hosts and network-path references still receive the selected default scheme, and `default_domain` still applies only to root-relative paths. Reprocess original references to recover this behavior from previously stored malformed output.

Fragment output also changes: `#!/route` remains a fragment instead of becoming `?_escaped_fragment_=/route`, and literal routing and text-directive punctuation stays literal. Existing ASCII escapes remain encoded, including unreserved letters, hyphens and tildes, to preserve syntax interpreted before percent-decoding. The humanizer follows the same rule while decoding safe Unicode; fragment spaces remain `%20`.

There is no legacy hashbang conversion flag. Applications that need the old crawler-specific query representation must construct it explicitly. Rebuild stored normalized keys from original URLs: previously encoded punctuation cannot reliably be distinguished from originally escaped data, and an existing `_escaped_fragment_` query parameter is treated as ordinary query data.

Hostname normalization now preserves leading dots, empty interior labels, repeated trailing dots, and dot-only hosts. For example, `https://a..example.com/` stays unchanged instead of silently becoming `https://a.example.com/`; `https://example.com../` also stays unchanged. A single trailing dot is still removed from an otherwise nonempty host, while `https://./` retains the DNS root dot. Unicode IDNA separators are mapped to ASCII dots without merging label boundaries. The same policy applies to `default_domain` and custom allowlist keys, so `.example.com` no longer selects an entry for `example.com`. Normalization does not validate DNS hostnames. Reprocess original URLs and review allowlist keys; previously discarded dots cannot be recovered from stored normalized output.

Nonempty parsed ports now require ASCII decimal digits. Both APIs raise `ValueError: Port must contain only ASCII digits` for alphabetic, signed, Unicode or percent-encoded port text. For example, `http://example.com:abc/` now raises instead of being preserved, and `http://example.com:８０/` raises instead of becoming `http://example.com/`. The same check applies to custom-scheme authorities and `default_domain`; colons in paths and opaque payloads are unaffected. The CLI exits with status 1 and a diagnostic on stderr. Callers processing arbitrary input should handle `ValueError`. Reprocess original URLs if prior normalization converted or removed Unicode port digits. Empty ports remain accepted and are removed. Numeric range validation is unchanged: `:65536` is still accepted.

IPv6 host spellings now converge: `https://[2001:0DB8:0:0:0:0:0:1]/` becomes `https://[2001:db8::1]/`, and `https://[::FFFF:C000:280]/` becomes `https://[::ffff:192.0.2.128]/`. Zone identifiers retain their exact spelling and case. The same normalization applies to `default_domain` and allowlist keys; expanded and compressed spellings now match, and canonical keys take precedence over aliases. Re-normalize stored IPv6 URL keys and review allowlists with duplicate address spellings.

Query keys and values now retain escapes for all reserved characters. For example, `https://example.com/?q=a%2fb` becomes `https://example.com/?q=a%2Fb` instead of `https://example.com/?q=a/b`. Literal punctuation remains literal. `url_humanize()` also keeps these escapes, including `%3D` in values, while decoding safe Unicode around them. Allowlisted names follow the same policy: `a/b` and `a%2Fb` no longer match each other. Review custom allowlists and rebuild stored keys from original URLs; old output cannot reveal which reserved characters were originally escaped.

The `default_scheme` option now accepts case differences, surrounding whitespace and one optional trailing colon, so `default_scheme=" HTTPS: "` behaves like `"https"`. Malformed strings such as `"https://"` raise `ValueError` instead of producing malformed URLs; non-string values raise `TypeError`. Validation applies to nonempty inputs even if the default is unused. Empty input and `None` keep their pass-through behavior. Check configuration and CLI `--default-scheme` values before upgrading; use `https` or `https:` rather than `https://`.

Allowlist rules now accept a single parameter name as a string, globally or per domain. For example, `param_allowlist="id"` and `param_allowlist={"example.com": "id"}` both select the complete name `id`. Previously a string-valued domain rule silently selected the individual characters `i` and `d`; callers intending that behavior must use `["i", "d"]` explicitly. API strings containing commas remain one name; use a list for multiple names. The CLI keeps its comma-separated format.

Supplying any custom allowlist other than `None` now enables filtering in both APIs and the CLI, even if `filter_params=False` or `-f` is omitted. An empty list or dictionary removes all query parameters; an empty string selects the empty parameter name, including with CLI `-p ""`. To disable filtering, omit the custom rule or pass `param_allowlist=None` with `filter_params=False`. Use `filter_params=True` or CLI `-f` without a custom rule to select the built-in domain rules.

### Added

- Verify built wheels and source archives in isolated environments before publishing, including installed API/CLI behavior, UTF-8 output, metadata and consumer typing.
- Accept reusable sequences and sets of parameter names, including tuples and frozensets, in both custom filters. Precisely type domain mappings and their values. Preserve existing string/list rules, matching, activation and query order; type checkers now reject non-string names and malformed domain values. One-shot iterators are outside the supported API.
- Add precise return-type overloads for both Python APIs: string inputs produce `str`, `None` produces `None`, and optional inputs produce `str | None`. Typed callers can use known string results without redundant `None` checks or casts. URL output and runtime behavior are unchanged. Check public consumer examples with ty alongside the package.
- Add opt-in `strip_fragment=True` to both Python APIs and `--strip-fragment` to the CLI. Remove the entire fragment and its delimiter, including anchors, routes and text highlights. Override empty-fragment preservation while retaining the selected empty-query policy; keep encoded hashes in other components. Fragment-only references become empty references. Fragments remain preserved by default.
- Add opt-in `sort_query=True` to both Python APIs and `--sort-query` to the CLI. Sort retained query fields by normalized, percent-encoded key, preserving equal-key order, duplicates and each field's value separator. Compose with allowlist, denylist and tracker removal. Query order is unchanged by default; humanized output follows the normalized key order.
- Add opt-in `remove_tracking_params=True` to both Python APIs and `--remove-tracking-params` to the CLI. Remove 40 documented, exact, case-sensitive attribution parameter names on any domain, including `ttclid` and `srsltid`. Preserve generic names such as `ref` and `session_id`, remaining query syntax and fragment routes. Combine with custom allow/deny rules, with removal taking precedence; default behavior is unchanged.
- Add `param_denylist` to both Python APIs and `--param-denylist` to the CLI. Remove specified query names without an extra enable flag, preserving all other parameters. Accept the same single-name, list and domain-map forms as the allowlist, with the same case-sensitive normalization. Denied names override allowed names when both rules apply; an empty denylist or an unmatched domain removes nothing.
- Accept a single-name string in `param_allowlist`, including domain-specific rules, in both Python APIs.
- Add `keep_empty_components=False` to both Python APIs and `--keep-empty-components` to the CLI. Empty query and fragment delimiters are removed by default as before; enabling the option preserves them, including a query delimiter left empty by parameter filtering. Empty query fields are still removed.
- Add `remove_trailing_slash=False` to both Python APIs and `--remove-trailing-slash` to the CLI. When enabled, it removes the entire trailing run of literal path slashes after dot resolution and optional collapsing, while keeping the root `/`. It shares the scheme scope of `collapse_slashes` and leaves encoded separators intact.
- Add the keyword-only `collapse_slashes=True` option to `url_normalize()` and `url_humanize()`, plus `--collapse-slashes` and `--no-collapse-slashes` in the CLI. Collapsing is enabled by default for HTTP(S), WS(S), FTP, file URLs and path references; set the option to `False` to preserve repeated slashes. Encoded separators remain intact.

### Changed

- **BREAKING:** Resolve dot segments before collapsing repeated path slashes, retaining empty segments during dot resolution.
- **BREAKING:** Preserve explicit document-relative, query-only and fragment-only references instead of inventing a scheme and authority. Resolve internal relative dots while retaining unresolved parents and honoring path cleanup options.
- **BREAKING:** Preserve fragment routes and text directives, stop converting hashbang fragments into query parameters, and retain ASCII fragment escapes in both Python APIs and the CLI.
- **BREAKING:** Preserve empty hostname labels instead of silently deleting them. Keep repeated trailing dots and dot-only hosts, while continuing to remove a single trailing dot from other hosts. Map Unicode IDNA separators consistently.
- **BREAKING:** Reject nonempty ports containing characters outside ASCII decimal digits with a clear `ValueError`, consistently across both APIs and the CLI.
- **BREAKING:** Canonicalize bracketed IPv6 hosts with zero compression and a consistent dotted-decimal suffix for IPv4-mapped addresses, while preserving zone identifiers. Apply the same spelling to default domains and query allowlist keys.
- **BREAKING:** Preserve reserved-character escapes in query keys and values, including during humanization and allowlist matching. Keep literal punctuation distinct from its escaped form.
- **BREAKING:** Validate `default_scheme` for nonempty inputs in both APIs and the CLI. Accept surrounding whitespace and one optional colon, normalize case, and report malformed values with clear type/value errors.
- **BREAKING:** Interpret string-valued domain allowlists as one complete name instead of a set of characters, preventing accidental removal of the intended parameter and retention of unrelated one-letter names.
- **BREAKING:** Enable query filtering whenever an explicit allowlist is supplied, including empty collections and CLI rules provided without `-f`. Keep `filter_params` for enabling built-in rules when no custom rule is provided.

### Fixed

- Validate readable query changes together in `url_humanize()`, avoiding repeated whole-URL normalization for each decoded key and value when the combined candidate round-trips. Keep independent decoding as a fallback when it does not, preserving existing output.
- Normalize ASCII port numbers using string operations, avoiding integer-conversion errors on heavily padded numbers and long digit strings.
- Resolve dot segments against empty path segments correctly, including for WebSocket URLs. Keep path references from being reinterpreted as hostnames when dot removal exposes leading `//`.
- Keep explicit relative references stable across repeated normalization and humanization, including references with Unicode, empty components and query filtering.
- Support CLI output streams whose `reconfigure` attribute is not callable.
- Keep bidirectional controls and Unicode line/paragraph separators percent-encoded in `url_humanize()` output, including when supplied as literal characters. Ordinary multilingual text and join controls remain readable.
- Avoid rebuilding and re-normalizing URLs for unchanged components in `url_humanize()`, improving performance for already-readable queries while retaining round-trip checks for decoded candidates.
- Normalize empty WebSocket paths to `/`, including query-only URLs, in both `url_normalize()` and `url_humanize()`. For example, `wss://example.com?room=1` now becomes `wss://example.com/?room=1`; stored normalized WebSocket URLs without a path can be re-normalized to adopt this spelling.

### Internal

- Centralize independent scheme rules for default ports, authority repair, path operations and empty paths.
- Replace mypy with ty, running package type checks through the locked development environment.
- Add bounded Hypothesis tests for HTTP(S) normalization idempotence and humanization round trips, plus explicit relative-reference structure and stability checks.

## [3.1.0] - 2026-10-28

### Upgrade notes

Python 3.11 or newer and `idna>=3.20` are now required. Python 3.10 users must upgrade Python before installing this release.

Remove the `charset` keyword from calls to `url_normalize()` and `url_humanize()`, and remove `-c` / `--charset` from CLI commands. These options have been removed; Unicode URL characters always use UTF-8 percent encoding.

Hosts ending in Unicode equivalents of a dot now normalize without a trailing dot on the first pass. Query filtering now retains explicitly allowed names containing Unicode or spaces. If normalized URLs are used as cache keys or deduplication identifiers, review stored keys and re-normalize the original URLs where available.

### Changed

- **BREAKING:** Drop support for end-of-life Python 3.10; Python 3.11 or newer is required.
- **BREAKING:** Remove the legacy `charset` API argument and `-c` / `--charset` CLI option.
- Declare Python 3.15 support in package metadata.
- Require `idna>=3.20`.

### Fixed

- Write CLI error diagnostics in UTF-8, including Unicode arguments on Windows.
- Strip trailing Unicode IDNA label separators from hosts and custom allowlist domain keys in one normalization pass.
- Normalize allowlisted query parameter names consistently with URL query keys, including Unicode and spaces, while keeping literal plus signs, encoded plus signs, and encoded spaces distinct.

### Internal

- Refresh dependencies, pre-commit hooks, and GitHub Actions.
- Use the committed dependency lockfile for CI checks and tests.
- Test every supported Python version from 3.11 through 3.15 on Linux, macOS, and Windows.
- Make `uv` run CI tests with the Python interpreter selected by the matrix.
- Run `pytest` as a Python module so coverage measures the checkout instead of an installed copy.

## [3.0.1] - 2026-09-22

### Upgrade notes

Normalization fixes change canonical output for some URLs, including encoded delimiters, query plus signs, explicit empty query values, and trailing spaces. If normalized URLs are used as cache keys or deduplication identifiers, review stored keys and re-normalize the original URLs where available; information discarded by earlier normalization cannot be recovered from those normalized values alone.

### Fixed

- Preserve invalid UTF-8 percent-encoded octets instead of replacing them with U+FFFD; valid UTF-8 still normalizes to NFC.
- Preserve percent-encoded reserved characters in paths, keeping values such as `a%2Fb` distinct from `a/b`.
- Preserve encoded plus signs (`%2B`) in query parameters and explicit empty values such as `flag=`.
- Normalize Unicode and unsafe characters in URL credentials while preserving encoded delimiters; correctly separate credentials containing `@` from the host.
- Correctly parse bracketed IPv6 hosts and ports, lowercase IPv6 addresses, and preserve zone identifier case.
- Recognize long and custom URL schemes, protocol-relative URLs, and bare domains or `localhost` with numeric ports.
- Remove leading whitespace and parser-ignored control characters before applying default domains and detecting URL schemes, preserving the intended destination.
- Trim trailing authority whitespace without discarding trailing spaces or punctuation belonging to paths, query values, or fragments.
- Convert hashbang fragments (`#!`) into a single escaped query parameter, preserving existing parameters and leaving ordinary fragments intact.
- Match query parameter allowlists against normalized hosts and equivalent custom domain keys, including Unicode/Punycode aliases, case variants, and trailing dots. Exact canonical keys take precedence over aliases.
- Decode IDNA host output as ASCII regardless of the `charset` argument.
- Keep encoded backslashes and C0/C1 control characters encoded in `url_humanize()` output, and retain the normalized URL when a decoding candidate cannot be parsed.
- Resolve query parameter allowlists once per URL to avoid repeated domain alias scans for each parameter.

### Documentation

- Correct normalization examples and clarify that parameter filtering uses allowlists, unknown domains have no default allowed parameters, and Unicode URL data uses UTF-8 percent encoding regardless of `charset`.

### Internal

- Enforce 100% statement coverage in the test suite and expand regression coverage for URL component handling.

## [3.0.0] - 2026-04-24

### Added

- Add `url_humanize()` and `url-normalize --humanize`/`-H` to convert normalized URLs to readable display URLs while preserving normalization round trips (#4).

### Changed

- **BREAKING:** Updated minimum Python version to 3.10 to match currently supported Python versions.

### Fixed

- Stop passing the deprecated `transitional` argument to `idna.encode()` (#43).
- Updated project license metadata to the current SPDX string format to resolve setuptools deprecation warnings (#39).

## [2.2.1] - 2025-04-26

### Added

- Include `py.typed` marker file for PEP 561 compatibility.

## [2.2.0] - 2025-03-30

### Added

- New `default_domain` parameter to support absolute paths with domain names (#22)

### Fixed

- Handle URLs with missing slashes correctly (#19)
- Fix decoding of reserved characters in URL paths (#25)
- Fix Twitter hashtag encoding in query parameters (#31)

### Internal

- Update CI configuration to use uv from PATH

## [2.1.0] - 2025-03-30

### Added

- New command-line interface (`url-normalize`) with support for:
  - Version information (`--version`, `-v`)
  - Charset selection (`--charset`, `-c`)
  - Default scheme override (`--default-scheme`, `-s`)
  - Query parameter filtering (`--filter-params`, `-f`)
  - Custom allowlist for query parameters (`--param-allowlist`, `-p`)

### Fixed

- Do not encode equals sign in fragment (Fixes #36)

### Internal

- Add GitHub Action to publish package to PyPI using uv

## [2.0.1] - 2025-03-29

### Fixed

- Reverted license format in pyproject.toml to maintain Python 3.8 compatibility with older setuptools versions

## [2.0.0] - 2025-03-29

### Added

- Query parameter filtering functionality
- Parameter allowlist feature for controlling accepted query parameters
- IDNA 2008 support via `idna` package

### Changed

- **BREAKING:** Switch default scheme from 'http' to 'https'
- **BREAKING:** Migrated IDNA handling to use IDNA 2008 with UTS46 processing
- **BREAKING:** Updated minimum Python version to 3.8 (removed Python 2.7 support)
- **BREAKING:** Removed sort_query_params option as it was incorrect - query parameter order is semantically meaningful and cannot be changed
- Enhanced query normalization with parameter filtering support
- Updated URL cleanup to support new filtering features
- Changed host normalization to handle each domain label separately

### Internal

- Refactored code organization for improved maintainability:
  - Split url_normalize.py into separate function modules
  - Moved each normalization function to its own file
  - Reorganized constants to their relevant modules
  - Maintained backward compatibility and test coverage
- Added pre-commit hooks for code quality and linting
- Dedicated CHANGELOG.md file
- Increased test coverage requirement to 100%
- Migrated from Travis CI to GitHub Actions for testing across multiple Python versions
- Moved pytest configuration from tox.ini to pyproject.toml
- Removed Travis CI configuration in favor of GitHub Actions
- Semantic versioning compliance
- Upgraded project structure to modern Python packaging standards using pyproject.toml

## [1.4.3] - 2024-02-15

### Added

- LICENSE file

## [1.4.2]

### Added

- Optional param `sort_query_params` (True by default)

## [1.4.1]

### Added

- Param `default_scheme` to url_normalize ('https' by default)

## [1.4.0]

### Changed

- Code refactoring and cleanup

## [1.3.3]

### Added

- Support for empty string and double slash urls (//domain.tld)

## [1.3.2]

### Added

- Cross-version compatibility: same code supports both Python 3 and Python 2

## [1.3.1]

### Added

- Python 3 compatibility

## [1.2.1]

### Changed

- PEP8 compliance improvements
- Setup.py improvements

## [1.1.2]

### Added

- Support for shebang (#!) urls

## [1.1.1]

### Changed

- Using 'http' schema by default when appropriate

## [1.1.0]

### Added

- Handling of IDN domains

## [1.0.0]

### Changed

- Code PEP8 compliance

## [0.1.0]

### Added

- Initial release
- Forked from Sam Ruby's urlnorm.py
