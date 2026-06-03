---
name: meetup
description: Run a MeetUp — a structured multi-persona decision session (briefs → discussion → vote → recorded decision). Use for durable or cross-project decisions (architecture, QA policy, naming, release readiness). Triggers: "meetup", "convene", "decide X with the agents", "call a meetup".
---

# meetup

Structured decision-making with the persona roster.

## Steps
1. **Convene:** state the question. Select relevant personas from `personas/` (architect moderates + tie-breaks). If a needed domain has no persona, create one first.
2. **Briefs:** each persona presents ≤4 bullets (requirements, risks, trade-offs). No interruptions.
3. **Discussion:** one round of cross-talk.
4. **Vote:** each persona casts For / Against / Abstain. Simple majority of non-abstaining wins; architect breaks ties. Quorum ≥ 3.
5. **Record:** write a decision log (`MeetUp Logs/<date>-<topic>.md`, frontmatter `type: decision`) and append one line to the relevant `MEETUP_INDEX.md`.

## Output
A recorded decision with vote counts, rationale, and the action + owner. Decided questions are not reopened without a new MeetUp.
