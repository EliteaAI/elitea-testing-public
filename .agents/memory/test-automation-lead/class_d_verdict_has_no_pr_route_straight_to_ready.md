---
name: A Class-D (infra/flake) adjust-automated-test verdict has no PR — the closure record and reviewer step both adapt
description: When adjust-automated-test's triage lands on Class D/F (nothing to fix), there's no diff to gate/review and the normal merged-artifact closure record doesn't fit — write a trimmed version and route straight to Ready
type: feedback
aliases: [class d closure, no fix needed closure, zero delta verdict, nothing to merge, adjust-automated-test no code change]
tags: [area/triage, type/lesson]
created: 2026-09-09
updated: 2026-09-09
---

## The situation

`adjust-automated-test`'s Step 2 triage table has two classes where the answer
is explicitly "do NOT touch the test": **D** (data/flake/infra) and **F**
(promotion gap). When the verdict lands there, Steps 4-8 (branch, fix, gate,
open PRs) never run — there is no diff.

Two things the standard pipeline assumes stop applying:

1. **No fresh-reviewer pass.** The "every automation PR gets a fresh
   qa-engineer review" rule is about *PRs* — there is no PR to review. Don't
   manufacture a review dispatch for a no-op diff; it has nothing to look at.
2. **The `workflow.md` closure-record template doesn't fit.** It's built
   around a merged test + testid rows + a promotability table. For a Class-D/F
   verdict, adapt it: keep the triage-class + evidence sections (same-run
   correlation, promotion-gap check, live reproduction), drop the
   merged-artifact/testid-promotion rows, and say explicitly "nothing to
   merge" rather than leaving a blank where "Test: #N merged" would go.

## Where it still routes

`Done` stays human-only regardless of whether anything was merged — a
verified-non-defect outcome is still an agent-terminal state, not a closer.
Route to **Ready** with the adapted closure comment, leave the issue **OPEN**,
and let a human close it (optionally bundling correlated siblings — see
`sibling_fix_cards_can_have_different_root_causes.md` for when that
correlation is itself verified rather than assumed).

## Don't skip the independent verification just because there's no diff to gate

A Class-D verdict resting only on the implementer's self-report is a claim,
not a closure. Re-run the reproduction yourself with an independent method
before writing the closure comment — worked case #2049/ELITEA-1898: the
implementer's DEV-green run used a flagged-off-limits `.env.test` edit; I
reran independently via the sanctioned `-p devenv` harness (see
`dev_repro_use_localhost_not_shared_env_test.md`) and got a first-hand
confirmation of the exact flake mechanism (1 passed, 1 rerun — the first
attempt hit the documented raw timeout live). That is materially stronger
than trusting the subagent's number.

Related: [[dev_repro_use_localhost_not_shared_env_test]] · [[repair_of_a_transient_needs_a_negative_control]]
