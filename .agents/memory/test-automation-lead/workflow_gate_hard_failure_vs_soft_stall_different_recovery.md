---
name: Workflow gate hard-failure (StructuredOutput never called) recovers via plain resume — unlike the soft "not-run" stall
description: distinguish the gate agent parking on a Monitor and never returning (hard failure, Workflow() throws) from it returning a useless not-run verdict (soft stall) — the two need opposite recoveries
type: feedback
---

## Two different gate-stall shapes, opposite recoveries

`workflow_gate_stall_gives_false_blocked_lead_runs_gate_directly.md` documents
the gate agent **completing** with a useless `{verdict: "not-run", runs: 0}`
result (e.g. a slow `git fetch` it gave up waiting on) — that call is cached
as "done", so `resumeFromRunId` just replays the same bogus verdict. Recovery
there is to run the gate yourself.

This is the **other** shape, seen on #943/ELITEA-2435 (2026-08-06): the gate
agent backgrounded its long-running `gate-case.mjs` invocation (120s tool
timeout → moved to background), armed a `Monitor` to wait for the verdict,
and then ended its turn ("I'll wait for the monitor notification before
proceeding further") without ever calling `StructuredOutput` — even after an
in-conversation `[structured-output-enforce]` nudge. The whole `Workflow()`
call then **throws**: `Error: agent({schema}): subagent completed without
calling StructuredOutput (after in-conversation nudge)`. Usage block showed
`agents_done: 8, agents_error: 0, agents_empty_result: 1` — the gate agent's
call was never cached as a completed result (it hard-failed the harness
contract, not "returned something useless").

**Recovery here is just `Workflow({scriptPath, resumeFromRunId, args})` with
the identical args** (see `workflow_resume_requires_args_too.md` — args is
mandatory on every resume). Every prior agent (triage → analyst → implement →
review → fix → review → merge, 7 calls) replayed from cache in the resumed
run's journal; only the gate (and the report writer after it) ran live,
finishing in ~10 min with a real `GREEN 3/3` verdict. No manual gate-running
needed — check first whether the failure is a hard `Workflow()` exception
(→ plain resume likely recovers it) vs. a normal-looking completed run whose
gate section reads `not-run`/suspicious (→ run the gate directly instead,
per the sibling entry).

**Before resuming:** confirm the tree is safe — this stall left the repo
`HEAD detached at origin/tests/batch-<slug>` with a clean working tree (no
uncommitted work, no stray pytest processes). Check `git status` /
`ps aux | grep pytest` before resuming; if either is dirty, land or discard
it first (the gate script itself also refuses a dirty tree).

See also: subagent_parks_on_monitor_in_headless_resume_synchronously.md (the
same park-on-Monitor failure mode, but for a directly-`Agent()`-dispatched
subagent — recovered via `SendMessage`, not `Workflow` resume, because that
one isn't running inside a `Workflow()` call at all).
