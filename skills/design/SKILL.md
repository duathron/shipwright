---
name: design
description: Review a CLI tool's terminal output against the Shipwright design tokens — tiers, palette, glyphs, banner, accessibility, and the output-format contract. Use when designing or auditing a tool's output. Triggers: "design review", "review the output", "check colors/banner", "a11y of the CLI".
---

# design

Independent design review of a tool's output against `shipwright_kit.design`.

## Steps
1. Dispatch a subagent using `personas/ux-design-agent.md` as the prompt, targeting the tool's output formatter + banner.
2. Check against the tokens:
   - **Tiers:** does the tool map its domain verdicts to `shipwright_kit.design.tiers.Severity` via `TierMappable` (not hardcoded colors)? Off-axis states mapped explicitly?
   - **Glyphs:** every tier indicator renders **symbol + label**, never color-only (colorblind rule).
   - **Palette:** uses a `Theme` (default / colorblind / `shipwright[security]` threat theme), not ad-hoc colors.
   - **a11y:** honours `NO_COLOR`/`--no-color`, strips color on a pipe, has a Windows/Unicode ASCII fallback.
   - **Banner:** via `shipwright_kit.design.banner.make_banner`, to stderr, suppressed on quiet/pipe.
   - **Formats:** the `--output` set matches the `shipwright_kit.design.output` contract (`rich|console|json|ndjson|csv`); `console` is the reduced-density plain formatter.
3. Report findings (gaps, not praise). The implementer fixes; re-review until clean.

## Policy
No self-review — this skill IS the independent design gate.
