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
    permissions:
      contents: read
    jobs:
      ci:
        uses: duathron/shipwright/.github/workflows/python-ci.yml@<sha> # vX.Y.Z
        with:
          python-version: "3.11"   # optional, default 3.11
          run-build: true          # optional, default true

> **Pinning:** pin the reusable workflow to the full commit SHA of a release tag, with the tag as a trailing comment (`@<sha> # vX.Y.Z`); never `@main`. Let Dependabot (github-actions ecosystem) bump it.

## Release — `.github/workflows/release.yml` in a project

Copy Shipwright's own `.github/workflows/release.yml` (at the release tag you pin to) into the project **inline**. PyPI Trusted Publishing matches the workflow file that runs the `publish` job, so the publish job must live in the consumer repo; a reusable `python-release.yml` call makes the OIDC claim name the reusable workflow and cannot match a Trusted Publisher. Keep the filename your Trusted Publisher names (`release.yml`) and re-sync the copy when Shipwright's release workflow changes.

The release runs as two jobs: `build` (`contents: read`, no OIDC) builds `dist` and the CycloneDX SBOM from the locked runtime dependencies, then `publish` (`id-token: write`, in the Environment) only downloads `dist` and uploads it to PyPI. The project must commit a current `uv.lock` (the SBOM is exported with `uv export --locked`; a stale lock fails the build before anything is published).

The project must include `release-please-config.json` and `.release-please-manifest.json` at its root (Shipwright ships canonical templates under `templates/release/`).

**uv.lock extra-files:** add a second `extra-files` entry to `release-please-config.json` so release PRs keep `uv.lock` in sync (otherwise `uv sync --locked` fails on every release PR): `{"type": "toml", "path": "uv.lock", "jsonpath": "$.package[?(@.name.value=='<dist-name>')].version"}`, where `<dist-name>` is your distribution name normalised the way uv stores it (lower-case, runs of `-`, `_`, `.` collapsed to `-`). The static `templates/release/release-please-config.json` cannot know your name, so it omits this entry; the Copier template renders it for you.

## One-time project setup (done by the scaffolder / onboarding)

1. **PyPI Trusted Publishing (OIDC):** on PyPI, add a trusted publisher for the project's GitHub repo + `release.yml` workflow + the `pypi` environment. No API token is stored.
2. **Environments:** create the gate environments with required reviewers; the reviewer approves in the GitHub UI when the release pauses — this is the QM / beta sign-off gate.

## Pre-releases (beta channel)

Set `prerelease: true` and let release-please produce a pre-release version (e.g. `1.6.0b1`). Users get it only with `pip install --pre <package>`; stable users are unaffected.
