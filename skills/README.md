# Skills

Invokable capabilities the framework ships with — the actionable layer over the
`../personas/`. Each `<name>/SKILL.md` encodes how to perform one lifecycle action.

| Skill | Use it to |
|-------|-----------|
| `scaffold` | create a new project from the template |
| `propagate` | push template improvements into existing projects (`copier update`) |
| `onboard` | bring an existing repo under the framework |
| `quality-gate` | run Tier-1 lint/test/smoke |
| `dogfood` | run the mandatory live pre-release gate |
| `review` | independent Skeptic gap-review (replaces self-review) |
| `meetup` | structured multi-persona decision session |
| `release` | drive the gate ladder to a PyPI release |

**Standing rules (ratified 2026-06-02):** no self-review — gate with `review`;
no release without a `dogfood` pass.
