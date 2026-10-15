---
name: CI autotest_user_<n> accounts lack a second project membership — SUPERSEDED, verify via CI history before trusting an old failure
description: ELITEA-2051's original "no 2nd project" precondition failure is fixed (ELITEA_TEAM_PROJECT_ID now works) — a card quoting that old error is stale, not current; walk recent job logs before diagnosing
type: feedback
---

## This entry's original diagnosis was WRONG and is kept only as a corrective

First version (2026-10-07) claimed: every CI `autotest_user_<n>` belongs to
only ONE non-public project, `USERS_TEAM_PROJECT_ID` is never wired, so no
code fix is possible, only an admin/CI-secret change. **That admin/CI-secret
change already happened** (a human + `ELITEA_TEAM_PROJECT_ID`, a DIFFERENT,
already-wired key — see `test-ui-dev.yml:130`, `test-ui-custom.yml:532`,
distinct from the never-wired `USERS_TEAM_PROJECT_ID` I was fixated on). Re-
checking `gh run view --job <id> --log` across 9 CI runs (2026-10-07 →
2026-10-13) showed a clean time-ordered transition:

1. **2026-10-07 → 2026-10-12 08:15** (7 runs): resolver finds a valid 2nd
   project (470, via `ELITEA_TEAM_PROJECT_ID`) — PAST the old precondition —
   but `403 Forbidden: required ['models.applications.applications.create']`
   creating a pipeline there. A PERMISSION gap, not a membership gap.
2. **2026-10-12 14:35 onward**: that 403 is ALSO gone. Full flow (steps 1-8)
   passes. Test now fails on a totally different, later assertion (Step 9,
   "Forked from" attribution link — see `#2410`'s thread for that angle).

**The lesson, not the stale fact:** when a card quotes an old CI failure
message, don't trust it as current state. Pull 3-5 of the MOST RECENT job
logs for that exact test (`gh run list --workflow test-ui-dev.yml` → filter
by suite/title → `gh run view --job <id> --log`) before diagnosing — the
underlying environment/CI config can and does change between when a card was
filed and when you pick it up, and a resolved problem dressed in old wording
wastes a full triage cycle re-deriving a diagnosis that's already obsolete.
A subagent I dispatched made exactly this mistake once (inferred "this test
has never passed since the fix landed" from a SINGLE job log plus
over-literal reasoning about a frontend code path, without walking the
timeline) — caught by independently re-checking every job log myself before
trusting the inference, per the general "no defect masking / verify before
reporting" discipline.

**`USERS_TEAM_PROJECT_ID` (ELITEA-2292-scoped) and `ELITEA_TEAM_PROJECT_ID`
(this case's actual answer) are two DIFFERENT, similarly-named settings** —
don't conflate them when grepping for "is a shared project wired in CI."
`config.py:46-48` and `:206-215` document each separately.
