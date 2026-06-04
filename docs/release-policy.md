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

## Output / eval schema contract (G10)

The library's **serialized** output surfaces are versioned **independently of the package
version**:

- **`shipwright_kit.eval.EVAL_SCHEMA_VERSION`** — the `EvalResult.to_dict()` shape.
- **`shipwright_kit.design.OUTPUT_SCHEMA_VERSION`** — the `render(fmt="json")` envelope.

Both are embedded in the serialized output (`"schema_version"` key) so a downstream reader
can branch on it. A **golden contract test** (`tests/eval/test_schema_contract.py`,
`tests/design/test_output_schema_contract.py`) pins the exact key-set + value types and
couples it to the version: **any structural change fails CI** until you deliberately bump the
relevant `*_SCHEMA_VERSION`, update the golden, and add a migration note here.

**Honest scope (what this does and does NOT protect):** the golden tests stop the library
from changing its serialized shape *silently* — a bump is forced. They do **not** yet protect
the consumers' path: barb and sift read `EvalResult` via **attribute access** and build their
own JSON; a field *rename* would still break them at attribute access regardless of the schema
version. Full N6 closure requires those consumers to adopt `EvalResult.to_dict()` (optional
follow-on). Until then, treat a structural change to the eval surface as MAJOR-equivalent and
coordinate the bump across barb + sift.

**Notes:** `to_dict()` emits **raw** floats (rounding is a display concern; consumers round
themselves). `confusion` is intentionally omitted (it is just `tp/fp/tn/fn`, already top-level
keys). `ndjson`/`csv` are row-streams with no envelope slot — they carry no per-row version;
consumers pin the producer's `OUTPUT_SCHEMA_VERSION`.

## Publish (operator-gated — NOT automated yet)

Publishing to PyPI is deliberately **not** wired into `main`. The build/sign/publish pipeline
(`.github/workflows/python-release.yml`: `uv build` → CycloneDX SBOM → PEP 740 attestations →
OIDC Trusted-Publisher upload, behind the `pypi` GitHub Environment) exists and is
SHA-pinned, but is invoked only in a separate, explicit publish step that also requires a
PyPI Trusted Publisher to be configured. "Build ≠ publish."
