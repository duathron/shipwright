---
name: review
description: Independent gap-review of a diff or target by the Skeptic persona — REPLACES self-review. Use after any implementation and before declaring anything done/passing/shipped. Triggers: "review this", "skeptic", "gate this change", "is this actually done".
---

# review

The standing gate. The agent that did the work never certifies it — this does.

## Steps
1. Dispatch a subagent using `personas/independent-review-agent.md` as the prompt (paste its content / its Invocation block).
2. Give it: the subject, the requirements, the implementer's claims, and the repo path. Tell it to **trust nothing**, re-verify every claim from primary evidence (re-run commands, read the actual diff), build a requirement→evidence table, and report severity-tagged gaps with no praise.
3. If gaps are found: the implementer (not this reviewer) fixes them; then re-run `review`. Loop until clean.

## Hard rule
No self-review. Do not let the implementer's self-assessment substitute for this gate (ratified 2026-06-02). For security-specific exploits, also use `personas/adversarial-review-agent.md`.
