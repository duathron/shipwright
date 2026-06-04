# Personas

Reference **agent mindsets** the framework ships with. Each file is a prompt you
dispatch as a subagent — a focused expert or reviewer with one clear job. They
are the human-less "team" that designs, builds, and gates work in Shipwright.

These are reference mindsets, not invokable commands. A future actionable layer
(skills like `scaffold`, `release`, `quality-gate`, `dogfood`, `meetup`,
`review`) will orchestrate these personas and live under `../skills/` — not yet
built.

## Source of truth (do not hand-edit here)

These files are a curated **copy** of the vault SSOT (`AI/AGENT PERSONAS/Agents/`).
Edit the persona **in the vault**, then refresh the bundle:

```sh
export SHIPWRIGHT_VAULT_PERSONAS="<abs path to AI/AGENT PERSONAS/Agents>"
just sync-personas
```

A pre-commit hook (`bundle-drift`) enforces parity **locally** and fails the commit
if a bundled persona differs from the vault. It is a deliberate no-op wherever the
vault isn't mounted (CI, fresh clones) — so it never blocks contributors who lack
the vault. For the gate to have teeth on your machine, export
`SHIPWRIGHT_VAULT_PERSONAS` somewhere your commit environment sees it (shell profile
**and** the gitignored `.env`), not only an interactive shell — GUI git clients
otherwise commit ungated. The absolute path is never committed.

## Roster

**Design & build**
- `architect-agent` — module boundaries, interfaces, phased roadmaps; MeetUp moderator + tie-breaker.
- `code-debug-agent` — implements features/bugfixes, writes tests.
- `devops-release-agent` — CI/CD, packaging, release automation, quality-gate wiring.
- `devex-tooling-agent` — scaffolding template, local dev loop, propagation ergonomics.

**Review & quality (no self-review — these gate the work)**
- `independent-review-agent` — "The Skeptic": trusts nothing, re-verifies claims, hunts gaps. **Replaces self-review** and gates every "done/release".
- `qa-test-architect-agent` — test strategy: two tiers (mocked / live+recorded), property/fuzz at parse boundaries, mandatory dogfood gate.
- `code-security-agent` — security correctness of a diff.
- `adversarial-review-agent` — red-team: exploits/PoCs, vulnerability chaining (security only).
- `qm-agent` — end-to-end user-journey gatekeeper (clone → install → run → output).
- `beta-tester-agent` — real-world acceptance + beta sign-off; owns the dogfood run.

**Docs & knowledge**
- `project-documentation-agent` — keeps project docs/indices accurate.
- `knowledge-systems-agent` — knowledge structure, retrieval, cross-project indices.

## How to use

Dispatch a persona as a subagent, pasting the persona file's content (or its
`Invocation` block) as the prompt. Reviews are independent by policy: the agent
that did the work never certifies it — the Skeptic does.

**Standing rule:** no self-review. After any implementation, gate it with the
`independent-review-agent`; before any release, require a `qa-test-architect`
dogfood pass. (Ratified portfolio-wide, 2026-06-02.)
