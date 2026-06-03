---
name: onboard
description: Onboard an existing repository into the framework — clone it into the gitignored projects/, apply the framework standards, and converge its tooling. Use to bring an existing tool under Shipwright. Triggers: "onboard <repo>", "integrate <tool> into the framework", "adopt this repo".
---

# onboard

Bring an existing repo under the framework's standards. The repo stays its own
git repo + PyPI package; it is integrated locally via the gitignored `projects/`.

## Steps
1. Clone the repo into `<shipwright>/projects/<name>/`.
2. Apply the standard files from `templates/python-cli/project/`: `tooling/ruff-base.toml`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml` + `release.yml` (callers to `duathron/shipwright/...@main`), `release-please-config.json` + manifest, `dogfood.sh`, and a property/fuzz test skeleton for each parse boundary. Adapt to the project's real package name + boundaries.
3. Fix the gaps Shipwright was built to fix: ensure a real `[tool.ruff]` config, a real CI test workflow, and a `dogfood.sh` exist.
4. `uv sync --dev`; run `just lint && just test && just dogfood`.
5. **Gate with the `review` skill (Skeptic)**; then commit + push to the project's OWN repo.

## Live-data QA (mandatory before any release)
Add a Tier-2 / live dogfood path for the project's real external services (read keys from env, skip cleanly if absent — skip ≠ pass).
