---
name: propagate
description: Propagate Shipwright template improvements into existing projects via `copier update`. This is how framework changes reach every project. Use after improving the template or shared standards. Triggers: "propagate", "update projects from template", "spread the framework change", "copier update".
---

# propagate

Pull the latest template into existing projects so standards stay in sync.

## Steps
For each target project (it must have been scaffolded/onboarded with copier, so it has a `.copier-answers.yml`):
1. `cd <project>` then `copier update --defaults` (drop `--defaults` to resolve conflicts interactively, like a git merge).
2. Resolve any conflicts.
3. Run gates: `just lint && just test`.
4. **Gate the diff with the `review` skill (Skeptic)** before committing — never self-review.
5. Commit + push to the project's OWN repo.

## Notes
Projects stay independent repos. Propagation is a reviewable pull per project, not a silent overwrite.
