# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and [Semantic Versioning](https://semver.org/).

## [Unreleased]
### Fixed
- docs: removed an inaccurate TestPyPI claim; pin examples to `@main` until tagged releases exist
- python-release: `config-file`/`manifest-file` are now overridable workflow inputs (were hardcoded)

### Added
- Framework foundation: uv workspace, single-source ruff config, just runner,
  pre-commit (+ gitleaks), dogfood CI, governance files.
- Reusable CI/CD: `python-ci.yml` (dogfooded by Shipwright's own CI) and
  `python-release.yml` (release-please + PyPI OIDC publish + pre-release
  support); canonical release-please config templates; actionlint gate;
  CI/CD contract docs (`docs/ci-cd.md`).
