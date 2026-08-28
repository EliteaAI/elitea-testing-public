---
name: Fixes to already-promoted tests branch from and PR to main
description: A red test that already reached main is repaired on main, not automation/base — and the fix must then be merged back down
type: feedback
aliases: [promoted test fix, fix red test on main, main-targeting PR, adjust-automated-test branch strategy]
tags: [area/workflow, type/branching]
created: 2026-08-27
updated: 2026-08-28
---

## The rule

The project's blanket rule is *never PR `main` directly* — but that rule is about
**new test work**, which flows `tests/<case>` → `automation/base` → batch promotion.

A **repair to a test that is already promoted to `main`** is the documented exception:
branch **from** `origin/main`, PR **to** `main`. Precedent: issues #1776, #1872 (PR #1875).
The `[Fix][ELITEA-…]` cards produced by `process-test-failure` state the branch strategy
explicitly in a *Fix Branch Strategy* section — read it, it is authoritative for that card.

## The half nobody puts on the card: merge it back down

`main` and `automation/base` both carry the file you fixed, and `automation/base` is
hundreds of commits ahead. Merging the fix to `main` leaves **`automation/base` still red**,
which is where all new work actually happens.

So the repair is not done until `origin/main` is merged into `automation/base` and pushed —
the routine main→base sync from [[sync-base-branches]], not scope creep. Verify with a run on
`automation/base` afterwards, not by inspection: on #1872 the merge auto-resolved
`agent_detail_page.py` cleanly and only the append-only `daily/` memory logs conflicted
(resolve by keeping both sides).

## Why this is easy to get wrong

The instinct is "never PR main" → open it against `automation/base` → the PR is a no-op there
or conflicts, and the CI red on `main` never clears. The direction of travel is the tell:
new work travels **up** to `main`; a repair to promoted code starts **at** `main` and travels
**down**.

## When the `main` merge is human-gated, land it on base yourself

`main` merges are human-triggered (`.agents/profile.md` § Automation PR policy), so in factory
mode you often **cannot** complete the main→base sync this entry describes — the PR sits open.
Waiting leaves `automation/base` carrying the broken test indefinitely.

Do both instead: open the PR to `main` **and** merge the same fix branch into `automation/base`
directly (that merge *is* yours). `automation/base` already contains all of `main`, so the merge
brings only the branch's own commits. Verified on ELITEA-0500 / #1888. Gate it on `base` too —
don't assume the merge is behaviour-preserving.

Expect conflicts only in append-at-the-end files: the module-level constant block at the top of a
shared spec, and the `MEMORY.md` / `daily/` logs. All resolve as a **union** — keep both sides.
An add/add on an AFS resolves in favour of the **branch** copy when the branch carries later
fix-round amendments; check what `--theirs` dropped before committing (on #1888 the 15 dropped
lines were all superseded content, but that had to be read, not assumed).

Related: [[verify_handles_and_values_against_main_not_the_working_tree]]

Related: [[sync-base-branches]]
