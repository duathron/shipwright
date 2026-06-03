---
name: quality-gate
description: Run Tier-1 quality gates (lint, format-check, unit tests, smoke) on a project. Use before committing or promoting work. Triggers: "quality gate", "gate <tool>", "run the checks", "is it green".
---

# quality-gate

Tier-1 gates — fast, mocked, every change.

## Steps
```bash
cd projects/<tool>
just lint     # ruff check + format-check
just test     # pytest (incl. property/fuzz tests at parse boundaries)
just smoke    # CLI answers without crashing
```
Report real pass/fail output. A failing gate blocks promotion. This is Tier-1 only — it does NOT replace the `dogfood` (live) gate required before release.
