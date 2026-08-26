---
name: "\"3 sessions without leaving queue\" auto-park can be a spend ceiling, not a real blocker"
description: before treating this auto-park comment as a signal something is wrong with the WORK, check the prior session's actual failure — an account-level spend/rate ceiling looks identical from the board but has zero bearing on the batch
type: feedback
---

## What happened (#1398, settings-w01, 2026-08-24/25 → recovered 2026-08-26)

A prior session ran a `batch-build` workflow that made real progress (5 of 9
cases analysed/built/reviewed, 2 merged) and then every remaining agent call
started failing with `You've hit your monthly spend limit ... your weekly
limit resets 8pm (Asia/Tbilisi)`. The workflow tool doesn't distinguish that
from any other agent failure — it just shows up as failed calls in the
diagnostics. The session (correctly, per its own rules) parked the card
`Blocked` with the generic comment "3 sessions without the card leaving this
loop's queue."

Read at face value, that comment reads like the WORK is stuck — a real
blocker needing a human decision on scope/approach. It wasn't: the account
literally could not spend any more tokens until a schedule-based reset. The
batch itself had zero problems; the ceiling was infrastructure, orthogonal
to the cases.

## What to actually do

When picking up a card auto-parked this way, **don't assume the parking
reason is a work-content blocker** — check what actually failed in the prior
session (its work-log comments, or the workflow's own diagnostics /
`journal.jsonl` if a run ID is named). A `spend limit` / rate-limit / `529
Overloaded` failure signature means: the batch's real state is exactly
where it was left (partially built, partially reviewed, nothing wrong with
it) — resync branches, harvest what's on disk/git, and continue from there.
Only park it again as a genuine blocker if you find an actual work-content
problem (a canon gap, a missing precondition, something needing a human
decision on scope).

Related: [[workflow_gate_stall_gives_false_blocked_lead_runs_gate_directly]]
(a different "blocked at face value, fine underneath" pattern — same
discipline of reading the actual failure before trusting the surface label).
