---
name: scaffold
description: Create a new CLI project from the Shipwright python-cli template (Typer + Pydantic + Rich, with QA gates baked in). Use when starting a new tool. Triggers: "scaffold a project", "new tool", "neues Projekt", "create a CLI".
---

# scaffold

Generate a new, standards-compliant project from `templates/python-cli/`.

## Steps
1. Collect variables (ask the operator if unknown): `project_name`, `pypi_name`, `package_name` (snake_case), `cli_command`, `description`, `env_prefix` (UPPERCASE), `python_version` (default 3.11).
2. Render the template:
   ```bash
   uvx copier copy --data project_name="…" --data pypi_name="…" \
     --data package_name="…" --data cli_command="…" \
     --data description="…" --data env_prefix="…" \
     <shipwright>/templates/python-cli <target-dir>
   ```
3. In the new project: `git init`, `uv sync --dev`, `uv run pre-commit install`.
4. Verify green: `just lint && just test && just dogfood` (must print `DOGFOOD: PASS`).
5. Report results. The new project is its own git repo + (eventually) its own PyPI package.

## Policy
Every later change to the project must be gated by the `review` skill (independent Skeptic) — never self-review. No release without a `dogfood` pass.
