---
name: dogfood
description: Run the mandatory pre-release dogfood gate — the real CLI against real + adversarial inputs (and live services if keys are present). No release without a dogfood pass. Triggers: "dogfood", "release gate", "live check", "ready to ship".
---

# dogfood

The release gate that mocks cannot fake — real execution against real + adversarial inputs.

## Steps
```bash
cd projects/<tool>
just dogfood   # runs ./dogfood.sh
```
Must print `DOGFOOD: PASS`. Any non-zero CLI exit on any input = FAIL.

## Rules
- **Skip ≠ Pass.** If the live tier is skipped (no API key), that does NOT satisfy the gate — it must be run with a key before release.
- No release without a dogfood pass (ratified portfolio policy, 2026-06-02). Analogous to "no analyzer without an eval".
