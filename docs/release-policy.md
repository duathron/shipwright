# Release & Versioning Policy

How the `shipwright` library is versioned and released. (Harden-and-prove phase: the
release **PR** automation is wired; the actual PyPI **publish** is a separate,
operator-gated step — see "Publish" below.)

## SemVer

The library follows [Semantic Versioning](https://semver.org/) over its **public surface**:
`shipwright_kit.design`, `shipwright_kit.eval`, `shipwright_kit.security` (the names exported from each
module + their documented behaviour).

| Bump | When | Conventional-commit |
|------|------|---------------------|
| **MAJOR** | A breaking change to the public surface (removed/renamed symbol, changed signature or semantics) | `feat!:` / `fix!:` / a `BREAKING CHANGE:` footer |
| **MINOR** | Backward-compatible addition (new module/function/option) | `feat:` |
| **PATCH** | Backward-compatible bug fix, perf, internal refactor | `fix:` / `perf:` / `refactor:` |

**Pre-1.0 caveat:** the library is `0.x` (currently `0.1.1`). Under `0.x`, a MINOR bump
*may* contain breaking changes (`bump-minor-pre-major` is on). Consumers pin a tag, not
`@main`, and read the CHANGELOG before upgrading. SemVer-strict guarantees begin at `1.0.0`.

## Automation (release-please)

Releases are driven by [release-please](https://github.com/googleapis/release-please) from
Conventional Commits on `main`:

1. Each merged commit's type (`feat`/`fix`/…) accrues into a pending release.
2. release-please keeps an open **"chore(main): release X.Y.Z"** PR with the computed next
   version + generated CHANGELOG. Config: `release-please-config.json` (release-type `python`,
   with an `extra-files` updater that bumps `pyproject.toml [project] version` alongside
   `shipwright_kit/__init__.py`); state: `.release-please-manifest.json`.
3. Merging that PR tags the release. (It does **not** publish — see below.)

`type: docs/test/ci/build/chore` do not bump the version.

## Pre-releases

The reusable release workflow accepts a `prerelease` input → publishes PyPI pre-release tags
(`X.Y.ZbN`) and sets `skip-existing`. Use for betas before a stable cut.

## Deprecation

Before removing a public symbol: ship it for at least one MINOR with a `DeprecationWarning`
naming the replacement; remove only in a subsequent MAJOR (or, pre-1.0, a clearly-noted MINOR).

## Output / eval schema contract (forward note)

The library's structured output (`shipwright_kit.eval` metrics, `shipwright_kit.design` output
contract) is consumed by separately-versioned tools (barb, sift). Once 2+ tools depend on a
structural field, that surface needs its **own** schema version + migration story, independent
of the package version — tracked as gap **G10**. Until then, structural changes to shared
output are treated as MAJOR-equivalent and coordinated across consumers.

## Publish (operator-gated — NOT automated yet)

Publishing to PyPI is deliberately **not** wired into `main`. The build/sign/publish pipeline
(`.github/workflows/python-release.yml`: `uv build` → CycloneDX SBOM → PEP 740 attestations →
OIDC Trusted-Publisher upload, behind the `pypi` GitHub Environment) exists and is
SHA-pinned, but is invoked only in a separate, explicit publish step that also requires a
PyPI Trusted Publisher to be configured. "Build ≠ publish."
