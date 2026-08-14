---
name: Implementer stalls waiting on its own background task — do it yourself after 2 stalls
description: When a dispatched implementer ends its turn twice in a row waiting on a background pytest run/notification instead of blocking in-turn, stop re-dispatching the full task — run the verification yourself and hand back a minimal mechanical commit/PR-only task
type: feedback
---

## What happened

Issue #26 (ELITEA-1735 testid-only rework). Dispatched `test-automation-engineer`
with a large implementer task (page-object rewrite + EliteaUI testid PR + test
run + self-check + commit + PR). The agent did excellent work on the hard parts
(page objects, additive `Popper` helper, EliteaUI testid PR — all verified
independently afterward and were genuinely correct) but ended its turn with
"I'll simply wait for the background test notification rather than poll"
instead of running the test synchronously and finishing the loop.

Resumed it via `SendMessage` with an explicit instruction to poll in-turn
rather than end its turn again — it stalled the same way a second time (this
resume got killed by the user before even that).

## Why it matters

Each stall costs a full round trip (dispatch → stall → notice → resume/re-dispatch
→ stall again) without producing the actual missing artifact (a green run +
commit + PR). In an unattended/headless context this is expensive — nobody is
watching to catch the stall except the next orchestrator turn. Two stalls on the
exact same step (run pytest, wait for it) is a pattern, not a fluke — a third
identical full dispatch is unlikely to behave differently.

## Rule going forward

**After a subagent stalls twice on the same "run and wait" step**, don't send a
third full-scope dispatch. Instead:

1. Verify the already-completed work independently yourself (I re-read the
   diffs, confirmed the EliteaUI PR was real and additive, etc. — this was
   already good practice and caught nothing wrong).
2. Run the missing verification step yourself, synchronously, as the
   orchestrator (running a test via Bash is not editing framework code — it's
   the same tool already used for the live-run gate; committing/pushing/PR
   are still off-limits, those stay the implementer's job).
3. Re-dispatch a MUCH narrower task: "here is the verified evidence
   (paste it), your only job is commit + push + open the PR citing this
   evidence." A small, mechanical task is far less likely to hit the same
   stall pattern, and it did in fact land cleanly in one pass (PR #203).

This is a distinct failure mode from `interrupted_dispatch_recovery.md` (which
is about an interruption from the ORCHESTRATOR's side losing track of a
subagent that actually finished) — this one is the SUBAGENT itself choosing to
end its turn early on a step it should have blocked on, repeatedly, on the
same task.
