---
name: Promotability must cover every testid dependency, not just this case's own PR
description: A closure record's promotability row must list every testid the test actually uses as a potential blocker — including ones reused from an unrelated, still-in-flight case — not only the testids this case's own draft PR added
type: feedback
---

Self-caught during a control-audit of my own delivery (issue #64, ELITEA-1971,
2026-07-15). The test used `ENTITY_CARD_SELECTOR` (`entity-card`), a testid the
implementer correctly identified as "already existing, no new testid needed" —
true in the sense that this case didn't need to add it. But "already existing"
was checked against `automation/testids` (the integration branch), not `main`.
Ground truth: `entity-card` was added by an *unrelated, still-open* case
(EL-1740 / EliteaUI#544), so it is exactly as un-promoted as this case's own
new testids (EliteaUI#562).

The closure record I posted named only EliteaUI#562 as the promotion blocker.
That's wrong — the case is ALSO blocked on #544, a dependency with zero
connection to this case's own PR. This is the same shape as the #35/#36/#37
false-promotability-row failure this control loop exists to catch, just
arriving via a *reused* testid instead of a *new* one.

**Rule going forward:** the promotability check (`.agents/workflow.md` §
Closure record) must enumerate EVERY testid the test's page-object diff
references — not just the ones the case's own testid PR touches — and check
each independently against `origin/main`. A testid being "pre-existing" on
`automation/testids` does NOT mean pre-existing on `main`; it only means some
other case (open or merged) put it there first. Every "no new testid needed"
claim in a PR/AFS still needs its own main-vs-testids row in the verification
block, sourced by finding which commit/PR actually introduced it
(`git log -p origin/automation/testids -- <file>` grepped for the testid
string) so the true blocking PR can be named.

**Recurrence (control-audit, issue #78, ELITEA-1974, 2026-07-15/16):** exact
same shape, exact same unrelated blocker PR (`EliteaUI#544`, still open) —
this time the reused dependency was `entity-card` again, in a *different*
case's delivery, caught during an independent control audit rather than
self-caught by the deliverer. The closure record named only the case's own
`EliteaUI#569` as the blocker. Confirms this isn't a one-off slip: any
Credentials/Mcp/Skills/Applications/Toolkits list-page case that reuses the
shared `Card.jsx` `entity-card` testid inherits the SAME #544 blocker until
that sibling case's testid PR merges — worth checking for on every future
case in this family, not just re-deriving from scratch each time.
