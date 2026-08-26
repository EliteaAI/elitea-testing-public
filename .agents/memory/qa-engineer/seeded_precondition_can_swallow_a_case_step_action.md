---
name: Seeded precondition can swallow a case step's ACTION
description: An API-seeded fixture flag can silently replace a case step the user was supposed to perform — and the Fidelity Declaration only names the content it seeded
type: feedback
aliases: [seed swallows a step, fixture flag substitutes an action, enabled by default seeded, wrong-interface precondition]
tags: [area/review, type/fidelity]
created: 2026-08-26
updated: 2026-08-26
---

## What happened

ELITEA-2266/2267/2276 (Project Context) all use a `project_context_seed(content,
enabled=True)` fixture. The AFS Fidelity Declarations each carry exactly one row —
"seeding a non-empty Project Context via PUT" — justified as transit because the
toggle only renders when content is non-empty. True, and fine.

But the same PUT also sets `enabled`, and that flag is not neutral:

- ELITEA-2266 case step 6 / ELITEA-2267 case step 2 assert the toggle is "ON **by
  default**" — read back off the value the fixture just wrote. The product's own
  default is never exercised.
- ELITEA-2276 case step 6 is an *action* ("Turn the Project Context toggle ON").
  Phase B satisfies it by re-seeding `enabled=True` and asserting `to_be_checked()`
  — the UI control is never operated in that phase.

None of the three declarations mentions the flag. Each declares the *content*.

## The check to run

For every fixture/seed parameter, ask separately: **does this parameter also
appear as an expected result or an action in the case?** A seed is transit only
for the parameters that merely reach the step under test. A parameter that
lands on a case step's own observable or gesture needs its own Fidelity
Declaration row — or the step needs to be performed for real.

Corollary for reviewers: "the AFS declared the substitution" is not enough —
read *which* substitution the row names, and compare it against the fixture's
full signature.

Related: [[afs_claims_need_full_sweep_and_grep]]
