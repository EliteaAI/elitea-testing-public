---
name: long-running gate Bash calls get infra-killed, not test-failed
description: Bash calls auto-backgrounded past 120s can be killed by the harness around 6-10min with zero test failures — retry, don't diagnose a red
type: feedback
---

Running a lead-driven N=3 merge gate by hand (see `merge_gate_operational_traps.md`
for why you'd do this — e.g. the workflow's internal gate stalled, see
`workflow_gate_stall_gives_false_blocked_lead_runs_gate_directly.md`) means
issuing long `pytest` invocations directly via Bash. Observed 3 times in one
session (2026-08-02, `approved-top10` batch): a Bash call auto-backgrounded
past the 120s foreground cap (normal — `pytest` gate runs take 6-8 minutes)
got a `status: killed` notification partway through, with **zero FAILED
markers** in the partial output captured so far — just an abrupt stop
mid-test-list. Retrying the identical command completed cleanly every time.
This is an environment/harness hiccup, not a gate result — do not report it
as a red or start debugging the test suite.

**When a long gate Bash call comes back `killed`:** grep the partial log for
`PASSED`/`FAILED` counts before concluding anything. Zero `FAILED` + an
abrupt stop = infra hiccup — just retry the same command. A real red always
shows an actual `FAILED` line with an assertion/error message.

**Separately:** chaining a git-tree-state change into the same Bash call as
the long test command (`git checkout <branch> && cd automation && pytest ...`)
sometimes suppresses the auto-backgrounding behavior entirely — the call hard
-times-out at 120s (exit 143) with no partial output captured at all, instead
of moving to background. Split them: one Bash call to change branches /
directories, a separate call for the long-running test command.
