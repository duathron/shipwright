---
name: release
description: Drive a project's release through the quality-gate ladder to PyPI (release-please + OIDC trusted publishing, with pre-release support). Use to ship a version. Triggers: "ship <tool> <version>", "release", "publish to PyPI", "cut a release".
---

# release

Drive the gate ladder to a published package. The operator approves; agents execute.

## Preconditions (all required)
- `quality-gate` green (Tier-1) AND `dogfood` PASS (live) AND `review` (Skeptic) clean. No self-review.

## Steps
1. Ensure the project has `release-please-config.json` + `.release-please-manifest.json` and a `release.yml` calling `duathron/shipwright/.github/workflows/python-release.yml@main`.
2. Conventional-commit history drives the version + changelog. On push to `main`, release-please opens a **Release PR**.
3. The operator reviews + merges the Release PR (this is the approval).
4. The `publish` job runs in a GitHub Environment (`pypi`) whose required reviewers are the **QM / beta gate** — it pauses for approval, then publishes to PyPI via OIDC (no stored token).

## Pre-releases (beta channel)
Set `prerelease: true` on the release workflow → a pre-release version (e.g. `1.6.0b1`), installable only with `pip install --pre`. Stable users are unaffected. (TestPyPI may be used as an internal publish dry-run.)
