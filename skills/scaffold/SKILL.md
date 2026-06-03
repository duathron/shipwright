---
name: scaffold
description: Create a new CLI project from the Shipwright python-cli template (Typer + Pydantic + Rich, with QA gates baked in). Use when starting a new tool. Triggers: "scaffold a project", "new tool", "neues Projekt", "create a CLI".
---

# scaffold

Generate a new, standards-compliant project. The Shipwright repo is itself the
Copier template source (root `copier.yml` with `_subdirectory: templates/python-cli/project`),
so scaffolding records the template commit and later `copier update` works.

## Steps
1. Collect variables (ask the operator if unknown): `project_name`, `pypi_name`, `package_name` (snake_case), `cli_command`, `description`, `env_prefix` (UPPERCASE), `python_version` (default 3.11).
2. Render the template — point Copier at the **Shipwright repo** (not the subdir), so `_commit` is recorded for updates:
   ```bash
   # from a local clone (absolute path) …
   uvx copier copy --vcs-ref HEAD --data project_name="…" --data pypi_name="…" \
     --data package_name="…" --data cli_command="…" \
     --data description="…" --data env_prefix="…" \
     /abs/path/to/shipwright <target-dir>
   # … or from GitHub:  gh:duathron/shipwright (use --vcs-ref main, or a release tag)
   ```
3. In the new project: `git init`, `git add -A && git commit` (Copier update needs a committed tree), `uv sync --dev`, `uv run pre-commit install`.
4. Verify green: `just lint && just test && just dogfood` (must print `DOGFOOD: PASS`).
5. Report results. The new project is its own git repo + (eventually) its own PyPI package.

## Policy
Every later change to the project must be gated by the `review` skill (independent Skeptic) — never self-review. No release without a `dogfood` pass.
