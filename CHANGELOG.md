# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-03-29

### Added

- Dedicated CHANGELOG.md file
- Semantic versioning compliance

### Changed

- **BREAKING:** Switch default scheme from 'http' to 'https'
- Migrated from Travis CI to GitHub Actions for testing across multiple Python versions
- Upgraded project structure to modern Python packaging standards using pyproject.toml
- Moved pytest configuration from tox.ini to pyproject.toml
- Added pre-commit hooks for code quality and linting
- Increased test coverage requirement to 100%

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
