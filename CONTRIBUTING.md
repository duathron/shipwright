# Contributing

## Local setup
    uv sync --dev
    uv run pre-commit install

## Before every commit
    just lint   # ruff check + format-check
    just test   # pytest

Pre-commit runs the same gates plus gitleaks. CI mirrors them exactly — if it
passes locally, it passes in CI.

## Commits
Use Conventional Commits (`feat:`, `fix:`, `chore:`, `ci:`, `docs:`). The
release tooling derives versions and the changelog from these prefixes.
