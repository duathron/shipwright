---
name: meetup
description: Run a MeetUp — a structured multi-persona decision session that ALSO sharpens the personas every round (briefs → anonymous peer-critique → vote → Skeptic-gate → recorded decision → agent self-update). Use for durable or cross-project decisions (architecture, schema/wire-format, QA policy, naming, release readiness, freeze-lifts). Triggers: "meetup", "convene", "decide X with the agents", "call a meetup".
---

# meetup

Structured decision-making with the persona roster — built so the roster improves every time it runs. The decision is one output; a sharper set of agents is the other.

## Hard rules (non-negotiable)
- **Real independent subagents** — one per persona, dispatched separately, no shared draft. NEVER one author role-playing the roster (fabricated unanimity hides the dissent that catches the landmine).
- **Grounding-first** — each persona reads the real code/artifact before forming a position.
- **Honest dissent** — record every minority/abstain verbatim; a 4-1 with the dissent preserved beats a fake 5-0.
- **Skeptic-gate the decision** and **self-update the agents after every round** — both mandatory.

## Standing advisors — seated in EVERY MeetUp (`personas/`, not optional, not selected)
Five thinking-lens advisors join every MeetUp on top of the domain personas — the fixed challenge-core:
- **The Contrarian** (`advisor-contrarian`) — finds what will fail (pre-mortem; silent break, unhappy path).
- **The First Principles Thinker** (`advisor-first-principles`) — reframes the real problem; briefs **first**.
- **The Expansionist** (`advisor-expansionist`) — finds hidden upside / the 10× version; counterweight to the Contrarian.
- **The Outsider** (`advisor-outsider`) — no domain context; names the shared blind spot + the **undo** option.
- **The Executor** (`advisor-executor`) — briefs **last**; collapses to the Monday-morning action + owner.

The Contrarian↔Expansionist and First-Principles↔Outsider tensions are deliberate; the Executor closes. They participate in every step and improve via the Step-8 self-update.

## Steps
1. **Convene & roster.** State the question. **Seat the 5 standing advisors automatically**, then select the **domain** personas from `personas/` (Architect moderates + tie-breaks). If a needed domain has no persona, **create one and save it to `personas/`** before the round. Quorum ≥ 3.
2. **Ground + briefs** (parallel, independent subagents): each reads the artifact, returns ≤4 bullets — position, risks, BLOCKs. No interruptions.
3. **Anonymous peer-weakness review:** strip author identities (Position A/B/C…); give each persona the anonymized others and have it name their weaknesses, blind spots, unsupported claims, missed risks. Anonymity removes deference. Surface the aggregate **before** the vote — it's what the room would otherwise wave through.
4. **Discussion:** one round addressing the peer-review findings.
5. **Vote:** For / Against / Abstain. Simple majority of non-abstaining; Architect breaks ties; quorum ≥ 3. Record counts + dissent.
6. **Skeptic-gate:** dispatch the independent reviewer over the drafted decision (vote honest? follows from positions? claims verified vs the artifact? dissent preserved?). Loop until clean APPROVE.
7. **Record:** decision log (`MeetUp Logs/<date>-<topic>.md`, frontmatter `type: decision`; counts, rationale, dissent, peer-critique findings, action + owner) + a line in `MEETUP_INDEX.md`.
8. **Agent self-update — EVERY round:** feed the round's lessons + the anonymous peer-critique back into each participating `personas/` file (the standing check that would have sharpened it; the blind spot peers named). Bump its `Updated:` line. New personas stay. Over rounds the roster compounds.

## Output
A recorded, Skeptic-gated decision (counts, rationale, honest dissent, action + owner) AND a sharper roster (each participant updated). Decided questions are not reopened without a new MeetUp.

## Anti-patterns
One author voicing all personas (fabricated unanimity) · skipping the anonymous peer-critique (shared blind spot waved through) · skipping the self-update (roster never improves — the whole point) · skipping the Skeptic-gate (un-verified "decided") · positions from memory not the artifact · burying dissent to look decisive.
