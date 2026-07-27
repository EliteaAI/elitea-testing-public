---
name: Finite test-data pool exhaustion only surfaces at the 3x gate
description: A "reuse an existing pre-created resource, delete it at teardown" test-data strategy against a finite, non-replenishing pool passes 1-2 runs and fails deterministically once the pool empties — the implementer's own GREEN and the reviewer's own GREEN both miss it because neither runs the test 3+ times in a row; only the orchestrator's mandated 3x-consecutive pre-merge gate catches it
type: feedback
---

## What happened

ELITEA-1888 ("Save As Version creates a named version"). Agent creation was
blocked by an unrelated open defect (#524), so the AFS's test-data strategy
was "reuse an existing disposable debris agent, delete the WHOLE agent at
teardown" — sourced from a finite pool of leftover agents from a prior,
unrelated case (ELITEA-1735). Implementer ran GREEN 2/2 locally. Reviewer
independently ran GREEN 2/2. Both looked clean. My own independent 3x
pre-merge gate: runs 1-2 GREEN, run 3 **RED** —
`AssertionError: Expected at least one existing disposable agent ... none
found in the project`. Three consecutive runs (2 from the implementer/
reviewer's own testing before mine, plus my own first 2) had already
consumed 3 of the pool's remaining members; my 3rd run hit empty.

## Why it matters

This is a **distinct failure class** from flake or product defect — the
test is 100% deterministic GREEN on any individual run for as long as the
pool has members, then 100% deterministic RED forever after. No amount of
implementer-local or reviewer-local re-running catches it reliably, because
2 runs (the typical local check count) usually still finds pool members —
it's specifically the *3rd+* consecutive run, run by an *independent actor
who wasn't tracking the pool's remaining count*, that exposes it. This is
exactly the class of bug the mandated N=3-separate-invocations merge gate
exists to catch (see `live_run_gate_is_pre_merge_not_post.md`) — but until
this case, that memory's stated justification was "environment drift /
parallel-context interaction / fresh-credential interaction." Finite-pool
test-data exhaustion is a fourth, previously-undocumented member of that
class.

## Rule going forward

1. **When an AFS proposes "reuse an existing pre-created X, delete at
   teardown" as its test-data strategy** (typically because create-fresh is
   blocked by some other defect), ask explicitly: is the reused pool
   **finite and non-replenishing**? If the reuse source is "debris left
   over from a different, unrelated case's prior runs" rather than a
   dedicated fixture that regenerates itself, treat it as a known
   liability, not a clean workaround — it WILL exhaust under repeated
   runs, full stop, not "might flake."
2. **Prefer a self-sufficient pattern**: create a dedicated, uniquely-named
   resource via whatever create path avoids the blocking defect (e.g. a raw
   payload through an existing `_full()`/raw-payload API method with
   different default values than the broken convenience method — see
   ELITEA-1888's fix: `AgentAPI.create_agent_full()` +
   `reasoning_effort: "none"` avoided #524 without touching
   `AgentAPI.create_agent()`'s shared defaults, which other tests depend
   on), and delete it at teardown. This is create-and-clean, not
   scavenge-and-consume — sustainable indefinitely, zero shared-pool
   dependency, and doesn't require coordinating with whatever else in the
   suite might also be scavenging the same pool.
3. **If a gate run does catch pool exhaustion**, it's an infrastructure
   finding at the gate step, not a rerun against the implementer's R2
   budget (the implementer's own local runs were legitimately green — the
   gate found something they structurally couldn't have found alone).
   Route back fix-only, get a FRESH reviewer pass on the delta (the
   test-data strategy changed substantively), then re-run your OWN gate
   from scratch — don't reuse/count the pre-fix green runs.
