# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and [Semantic Versioning](https://semver.org/).

## [0.7.0](https://github.com/duathron/shipwright/compare/v0.6.0...v0.7.0) (2026-06-07)


### Features

* **ci:** add version-consistency guard to reusable python-ci ([f0a743e](https://github.com/duathron/shipwright/commit/f0a743e54a31fb38542da96a4537a5cfac4a9481))


### Documentation

* **meta:** attribution — add LinkedIn link + README Author section ([fe8edfc](https://github.com/duathron/shipwright/commit/fe8edfcc731a5c829ceddddecd903bb2f52cc654))

## [0.6.0](https://github.com/duathron/shipwright/compare/v0.5.0...v0.6.0) (2026-06-05)


### Features

* **template:** scaffold config.py + use build_typer (G4) ([5c00503](https://github.com/duathron/shipwright/commit/5c005032b5398defe217ad4fb934f3dc634915fe))

## [0.5.0](https://github.com/duathron/shipwright/compare/v0.4.0...v0.5.0) (2026-06-05)


### Features

* **cli:** Typer app factory (build_typer) ([65ab0e2](https://github.com/duathron/shipwright/commit/65ab0e2cf1fdcb61fec45c077d03941d4a87dbe0))
* **config:** import-light shared config mechanism ([d58d46e](https://github.com/duathron/shipwright/commit/d58d46ec08d1049ae3ef3da99dcb3b85c6e2c0bb))
* **template:** G11 self-test + fix 2 latent template defects ([ce52ded](https://github.com/duathron/shipwright/commit/ce52ded6a4da91d5cc12b4c70d8cc3bcbe64a6ed))


### Documentation

* **plan:** G4 CLI/config DRY implementation plan ([749f4d2](https://github.com/duathron/shipwright/commit/749f4d26c7c39fdc54e9ecddf79786aba8d62fcd))

## [0.4.0](https://github.com/duathron/shipwright/compare/v0.3.0...v0.4.0) (2026-06-05)


### Features

* **security:** add shared prompt-injection detector ([a87bd78](https://github.com/duathron/shipwright/commit/a87bd78e82a0c1bbec782991f8e6c2f03584aac4))
* **security:** export injection detector + import-light guard ([79a2c91](https://github.com/duathron/shipwright/commit/79a2c9193f0a9a1cddbea4b3a248806d1663bf98))


### Documentation

* **plan:** G12 shared injection defense implementation plan ([29aadbb](https://github.com/duathron/shipwright/commit/29aadbb6110f9739cd205f965246c52a8f94fd62))

## [0.3.0](https://github.com/duathron/shipwright/compare/v0.2.0...v0.3.0) (2026-06-04)


### Features

* schema/contract version for eval + output surfaces (G10) ([5a20c9b](https://github.com/duathron/shipwright/commit/5a20c9b5a091c0c0d89c1b41ffe91731eb0e6fb2))

## [0.2.0](https://github.com/duathron/shipwright/compare/v0.1.1...v0.2.0) (2026-06-04)


### ⚠ BREAKING CHANGES

* rename import package shipwright -> shipwright_kit (kill PyPI namespace collision, N1)

### Features

* persona bundle-drift sync + pre-commit gate (G3) ([f94b1a9](https://github.com/duathron/shipwright/commit/f94b1a9d16fe716b31ec339f528a79c286ea629a))


### Bug Fixes

* build-requires setuptools&gt;=77 (SPDX license needs it) + gitignore .coverage ([0eee927](https://github.com/duathron/shipwright/commit/0eee927e6e4253bd45a5bf0f87b35577694bcd11))
* reconcile version to 0.1.1 (match latest tag v0.1.1) ([dd57d91](https://github.com/duathron/shipwright/commit/dd57d91996a8c1db68d0cb770e5b2686848735b0))
* SECURITY.md uses GitHub private vulnerability reporting, not personal email (G13) ([97c921a](https://github.com/duathron/shipwright/commit/97c921a958536a910eaacdcecf4eb4b0b4d6d6f2))
* stale 'shipwright' refs post-rename (console error string, prose) ([0d4d15c](https://github.com/duathron/shipwright/commit/0d4d15ca5b6a6c6509e6952d83075f6b21e09c1d))
* sync project-documentation-agent persona from vault SSOT ([ada16e1](https://github.com/duathron/shipwright/commit/ada16e1d6a3b3d5fa31a214297a68fde1f519819))


### Documentation

* library-first README + API reference (Phase C) ([d075753](https://github.com/duathron/shipwright/commit/d075753b0d76b50bc37e8cf9d13742ef11197184))
* SemVer + release policy ([c6c9ff9](https://github.com/duathron/shipwright/commit/c6c9ff9c5e618904fd033e68d4d4b50562b5ca64))


### Code Refactoring

* rename import package shipwright -&gt; shipwright_kit (kill PyPI namespace collision, N1) ([bf50dab](https://github.com/duathron/shipwright/commit/bf50dab9e7f5723ee15fc22ef760dacd86401d4b))

## [Unreleased]
### Fixed
- docs: removed an inaccurate TestPyPI claim; pin examples to `@main` until tagged releases exist
- python-release: `config-file`/`manifest-file` are now overridable workflow inputs (were hardcoded)

### Added
- Skills layer: scaffold, propagate, onboard, quality-gate, dogfood, review, meetup, release (`skills/`).
- Framework foundation: uv workspace, single-source ruff config, just runner,
  pre-commit (+ gitleaks), dogfood CI, governance files.
- Reusable CI/CD: `python-ci.yml` (dogfooded by Shipwright's own CI) and
  `python-release.yml` (release-please + PyPI OIDC publish + pre-release
  support); canonical release-please config templates; actionlint gate;
  CI/CD contract docs (`docs/ci-cd.md`).
