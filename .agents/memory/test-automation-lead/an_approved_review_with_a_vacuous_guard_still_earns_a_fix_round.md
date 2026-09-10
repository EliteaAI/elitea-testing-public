---
name: An APPROVED review with a vacuous guard still earns a fix round
description: When the weak assertion IS the one enforcing the finding, spend the round — approved-but-vacuous looks identical to working
type: feedback
aliases: [vacuous assertion, to_have_count(0), absence assertion ordering, APPROVED with MINORs, fix round on approval]
tags: [area/review, type/gate-discipline]
created: 2026-09-10
updated: 2026-09-10
---

## The call

On #2145 the reviewer returned **APPROVED** with a MINOR: the `back-button` absence assertion ran
*before* its container was proven rendered, so `to_have_count(0)` could pass vacuously. Approval means
I could have merged. I ordered a fix round anyway.

## Why that is the right default

The test is a **repair**, and that one assertion is the entire mechanism keeping the repaired drift
**test-enforced** rather than documented-in-a-comment. A vacuous guard is indistinguishable from a
working one until the exact day it was supposed to fire. Cost of the round: minutes. Cost of getting
it wrong: the drift silently un-enforces itself and the next regression lands unnoticed.

**The test to apply:** is the weak assertion the one carrying the finding? If yes, MINOR-on-an-APPROVAL
is not a nit — fix it before merge. If it is incidental hardening, ship and note it.

Generalisation of the ordering itself: **an absence assertion must prove its container rendered first.**
`to_have_count(0)` / `not_to_be_visible()` are satisfied by a page that has not committed. Assert the
replacement is visible, *then* assert the old thing is gone.

## Also worth keeping

Batch the reviewer's cheap MINORs into that one round — I folded in whitespace-normalising an
environment-derived expected value and softening an over-firm defect claim in the AFS. One round, three
fixes, one re-gate.

Related: [[el6460_breadcrumb_drift_class]]
