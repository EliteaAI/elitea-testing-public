---
name: Implementer can orphan its own background verification loop
description: a dispatched subagent started a multi-run background bash verification loop, then ended its turn saying it would "wait for the background monitor to notify" it — no such monitor exists in this dispatch model, so the orchestrator had to discover and poll the orphaned OS process itself
type: feedback
---

## What happened (#150, ELITEA-1892, PR #615, fix round 1)

Dispatched the implementer (test-automation-engineer) fix-only to harden a
flaky known-defect handling path. It applied the fix (uncommitted), then
kicked off a 14-run `bash` verification loop in the background (a shell
script under `/tmp/`, redirecting per-run logs, checking a summary file) to
confirm the fix converged on a single failure signature — and then ended
its turn with: *"I'll stop here and wait for the background monitor to
notify me when the run batch completes."*

There is no such monitor in this Agent-tool dispatch model. The subagent's
turn ending means control returns to the orchestrator with nobody left
watching the loop. I had to notice the still-running `pytest`/Playwright
process myself (`ps -ef`, then `lsof` on its parent to find the wrapper
script and log paths) and poll the log file to completion in my OWN turn —
exactly the "waiting is work you do inside the turn" discipline the
orchestrator's own factory-mode rules mandate, except here it was rescuing
a SUBAGENT's abandoned wait, not my own.

## Why it matters

This is the same failure class as `sendmessage_resume_fragile_in_factory_mode.md`
and `polling_resumed_subagent_transcript_jsonl.md` (SendMessage resumes
always background, so "wait for a notification" is a trap) — but it shows
up on the IMPLEMENTER side too, in a plain one-shot `Agent()` dispatch, not
just on resume. Any subagent that starts a long-running background process
to verify its own work is vulnerable to the same "assume someone else is
watching" mistake the orchestrator itself is warned against.

## The fix

1. **Detect it**: if a dispatched subagent's final message references a
   background job, a monitor, or "will notify," and the described
   verification isn't actually reflected in the returned Run Report /
   commit history, assume it's orphaned. Check for the process directly
   (`ps -ef | grep <relevant tool>`, `lsof -p <pid>` to find the script +
   log paths) rather than trusting the subagent's framing.
2. **Recover it**: poll the log/summary file to completion yourself
   (`until grep -q "<completion marker>" <log>; do sleep 20; done`) — the
   work is usually already correctly running, just unsupervised.
3. **Prevent recurrence**: on the NEXT dispatch to the same role, name the
   exact violation explicitly and instruct: "if you start any background
   run batch, poll it to completion synchronously inside this same turn
   before ending your turn." This worked cleanly on the very next round —
   the implementer ran an 18-run batch, waited it out in-turn, and reported
   full results with no orphaned process.

## Broader lesson

The "wait inside the turn, never assume a later notification" rule isn't
just an orchestrator-level factory-mode rule — it's a property any
subagent working in this dispatch model needs, and it's worth stating
explicitly in dispatch prompts for implementer/analyst/reviewer rounds
that are likely to involve a multi-run verification batch (flaky-test
hardening, load-style repetition checks), not just assumed as obvious.
