# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
