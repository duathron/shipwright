# CI/CD — consuming Shipwright's reusable workflows

Shipwright ships two reusable GitHub Actions workflows. A project gets full CI/CD by calling them — no copied YAML, no drift. Bump the Shipwright tag and every project picks up the change on its next run.

## Quality-gate ladder

    commit → lint + unit (auto) → build → smoke (auto) →
    QM gate (manual) → beta sign-off (manual) → release (PyPI, OIDC)

Manual rungs are **GitHub Environments with required reviewers**. The release workflow's `publish` job runs in an Environment, so it pauses for approval before publishing.

## CI — `.github/workflows/ci.yml` in a project

    name: CI
    on:
      push:
      pull_request:
    jobs:
      ci:
        uses: duathron/shipwright/.github/workflows/python-ci.yml@main
        with:
          python-version: "3.11"   # optional, default 3.11
          run-build: true          # optional, default true

> **Pinning:** examples use `@main` while Shipwright is pre-release. Once release automation cuts tagged releases, pin to a major tag (e.g. `@v1`) for stability.

## Release — `.github/workflows/release.yml` in a project

    name: Release
    on:
      push:
        branches: [main]
    jobs:
      release:
        uses: duathron/shipwright/.github/workflows/python-release.yml@main
        with:
          release-environment: pypi   # GitHub Environment gating publish
          prerelease: false           # true → PyPI pre-release (e.g. 1.6.0b1)
        permissions:
          contents: write
          pull-requests: write
          id-token: write

The project must include `release-please-config.json` and `.release-please-manifest.json` at its root (Shipwright ships canonical templates under `templates/release/`).

## One-time project setup (done by the scaffolder / onboarding)

1. **PyPI Trusted Publishing (OIDC):** on PyPI, add a trusted publisher for the project's GitHub repo + `release.yml` workflow + the `pypi` environment. No API token is stored.
2. **Environments:** create the gate environments with required reviewers; the reviewer approves in the GitHub UI when the release pauses — this is the QM / beta sign-off gate.

## Pre-releases (beta channel)

Set `prerelease: true` and let release-please produce a pre-release version (e.g. `1.6.0b1`). Users get it only with `pip install --pre <package>`; stable users are unaffected.
