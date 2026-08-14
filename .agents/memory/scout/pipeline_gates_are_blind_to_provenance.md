---
name: Pipeline gates are blind to provenance (fidelity drift class)
description: Every gate checks that an assertion exists/is strong/matches the AFS — none asks what produced the value. Substitution drifts silently and the hardening gate rewards it.
type: feedback
---

## The failure class (generalise beyond mocks)

**Substitution of the system under test.** An assertion is evidence only if the value
it reads was produced by the system. Anything the test authors, injects, forces or
short-circuits between trigger and observable is a substitution: fabricated responses
(`route.fulfill`), injected state (`page.evaluate`), wrong-interface preconditions
(API-seeding what the case says the UI creates), replaced clients (`monkeypatch`),
bypassed subjects (reusing `auth_state` in a login case).

Canon written 2026-08-14: `.agents/testing.md` § Fidelity policy (authoritative),
`.agents/role-overrides.md` § fidelity / § precedent / per-slot, `.agents/workflow.md`
§ Review gates (provenance grep), `CLAUDE.md` Critical Conventions.

## Why no gate catches it — the part worth remembering

Every standing reviewer check is shaped for **under-coverage**; substitution produces
**over-coverage**, so all of them pass:

- Coverage completeness / per-step assertion — verify assertion **presence**, never
  **provenance**. They never ask what produced the value.
- Assertion strength — a fabricated payload yields *exact-equality* assertions, i.e.
  scores **better**.
- Defect masking — **inverted**. Masking hides a failure; a substitution can *create*
  one, which then gets filed and soft-asserted with a ticket link — the exact pattern
  the checklist teaches agents to reward.
- Triangulation (case ↔ AFS ↔ diff) — if the **analyst** authored the substitution,
  all three artifacts agree and row 1 of the table says APPROVED. Triangulation has no
  axis for *what system produced the value*.
- Hardening gate (N× green) — **rewards it**. A fabricated response is maximally
  deterministic; an honest live test (real LLM, 10–30 s, variance) is the one at risk.
  Selection pressure runs toward substitution. Any fix must acknowledge this or lose.

## The two amplifiers (both generic, both now ruled on)

1. **Declaration used as a bypass token.** `role-overrides.md` said a declared
   improvisation "can never solo-FAIL a delivery" — so *explaining* a deviation made
   it unblockable, and its escalation half (turn the gap into canon) had no artifact,
   trigger or owner, so it never ran. ~20 substitutions produced zero policy lines.
   Fixed with a ceiling (a declaration can never authorise a change to *what* is
   verified), an obligation (must produce a `question` card before batch close), and
   a brake (second use of the same pattern is a blocker, not a declaration).
2. **Precedent laundering.** Each AFS justified itself by citing the previous merged
   one, and borrowed the word "sanctioned" from unrelated rules. Fixed with
   § Every role — precedent is not authority (neighbours are authority on convention,
   never on deviation).

## Two things that were NOT the cause — don't re-investigate

- **Model tier.** All four slots ran `claude-sonnet-5`, no overrides; the *legitimate*
  decision three weeks earlier ran the same model. Governance, not capability.
- **A careless reviewer.** The reviewer executed its contract correctly and returned
  "zero blockers"; the contract had no axis on which the substitution was visible.

## Watch for the same shape elsewhere

Whenever a rule is enumerated as a **list of forbidden acts** (masking: remove /
demote / weaken / skip / hide), check whether the inverse operation — *adding* a
fabricated condition while leaving the assertion strong — is covered. It usually is
not. The same asymmetry is likely in any other "don't do X" list in the canon.

Full incident report (chain, evidence, transcript refs, bundle findings):
`sdlc-skills/bundles/test-automation/incidents/2026-08-14-response-mocking-drift.md`
