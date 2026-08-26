---
name: Large-batch gate — scope by node-id (the batch's own new/changed tests), never by whole file
description: an internal gate agent can run out of its own turn on a big batch; when the lead runs it manually, file-level scope sweeps in unrelated pre-existing flaky tests and produces false reds
type: feedback
---

## What happened (2026-08-07, #1277 agents-batch1-1277, 11 cases / 9 units)

The workflow's own internal gate agent tried to fit N=3 (30 tests, all files
touched) + a 57-test blast-radius pass into one dispatch turn. It started a
background `gate-case.mjs --n 1` calibration run to gauge real runtime, and
its own session was "forced to conclude" before the calibration run even
finished — it returned an honest `{verdict: "not-run", runs: 0}` with the
recommendation to chunk the runs. This is a DIFFERENT stall shape from
`workflow_gate_stall_gives_false_blocked_lead_runs_gate_directly.md` (that one
was a git-fetch timeout on a small batch); here the agent worked correctly
but the batch was simply too large for one turn's Bash-call budget. Expect
this for batches of roughly ≥8-10 units — don't treat it as a bug, just run
the gate yourself per `testing.md` § Merge gate (which already assigns N=3
execution to the lead, not exclusively the workflow).

## The scoping mistake to avoid

The gate agent (and my own first manual attempt) computed "the batch's own
new/changed specs" via `git diff --name-only base...trunk` — a FILE list.
When a batch extends an EXISTING file with new test methods (here:
`test_agent_management.py` gained 3 new methods for ELITEA-1873/1878/1879),
file-level scope pulls in every OTHER pre-existing test in that file too —
23 unrelated siblings in this case, one of which (`test_agent_executes_with_
name_description_instructions_only`, ELITEA-1897, untouched by this batch's
diff) was independently flaky on an unrelated timing race. That flake then
gated the whole batch red on work it had nothing to do with.

**Scope the REQUIRED N=3 gate to the exact node-ids the batch actually
added/changed** (`file.py::Class::method`), not the files. Precedent already
established this session for a single new method
(`test_pipeline_run_details_state_before_after.py::test_run_details_...`) —
the mistake here was reverting to file-level scope once MULTIPLE new methods
landed in one pre-existing file. A blast-radius-style pass over the REST of
a touched shared file (or file importing a touched page object) still runs
ONCE, unblocking per the existing doctrine — pre-existing failures there
don't block, only regressions do. Don't conflate the two passes' scopes.

## Bonus payoff

Narrowing the scope this way also made the SECOND real red (a genuine timing
bug the narrow scope caught in the batch's own extended spec) immediately
attributable and fixable — see `batch_stabilize_for_shared_page_object_race.md`
and the console-404-known-defect entry for the two causes this batch's gate
actually found once correctly scoped.
