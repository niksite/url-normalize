# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
