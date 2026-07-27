---
name: Cardless intake's max_new_cards_per_run cap appears unenforced in practice
description: .agents/test-automation.yaml and project_briefing.md both state ≤10 new cards per run, but observed carded-issue-count history is inconsistent with that cap ever having been honored — flag the discrepancy each run rather than silently splitting into small batches or silently ignoring the yaml
type: feedback
---

## What happened

`.agents/test-automation.yaml` § intake: `max_new_cards_per_run: 10  # more
arrive next tick`. `project_briefing.md` repeats it: "≤10 new cards per
run". Neither the intake mission's own task text (as received, at least
as of the 2026-07-15 and 2026-07-23 runs) nor
`bulk_tms_intake_technique.md` (the accumulated how-to memory for this
exact mission) mention any cap — the latter's "Summary/tracking issue"
section describes filing the *entire* delta in one pass.

Evidence the cap has never actually been enforced:
- Pre-2026-07-23-run carded count was exactly 436, which equals 219 (the
  count before the 2026-07-15 "run 7") + 217 (that run's own delta) — no
  gap consistent with a 10-per-run trickle.
- Daily logs between 2026-07-15 and 2026-07-23 show zero intake-run
  entries (only unrelated `sync-base-branches` cardless runs), so the
  217→436 growth wasn't achieved via ~22 separate capped runs either —
  it reads as one full-delta filing pass.
- The 2026-07-23 run repeated the pattern: filed the full 256-case delta
  in one pass (issues #726-#982), not split into runs of 10.

## What to do

Treat the yaml's cap as **stale/unconfirmed** until an operator
explicitly reconciles it. Each run that files more than 10 new cards:
file the full delta (matches actual practice + the task's own literal
instructions), but **state the cap discrepancy explicitly** in the
summary/tracking issue and in the report to the operator, so it's a
standing, visible question rather than a silent override. Don't
unilaterally "fix" the yaml file to remove the cap — that's an operator
decision (last correction of this shape, the already-automated
three-condition rule, was explicitly operator-confirmed before being
adopted as the new default — see `bulk_tms_intake_technique.md`).
