---
name: A test that reads pre-existing data passes dirty and fails clean
description: Triage shape for CI "precondition not found" reds — the test borrowed data instead of owning it
type: feedback
aliases: [precondition not found, passes locally fails in CI, environment data issue, test owns its preconditions, borrowed test data]
tags: [area/triage, type/pattern]
created: 2026-08-27
updated: 2026-08-27
---

## The shape

A CI red reading *"X must exist in the project to satisfy the case's
precondition"* usually is **not** an environment defect, even though it looks
like one and gets filed as one. It means the test **looked data up** instead of
creating it — so it passes on a polluted environment and fails on a clean one.
That is inverted: the cleaner the env, the redder the test.

**The tell:** the failing job's *other* specs all passed. Each cleaned up after
itself, which is exactly what left nothing to borrow.

## How to resolve it

1. **Read the TMS case text before touching code.** It usually already says
   *create*. On ELITEA-1790: *"**Create or confirm** 6 distinct Skills"* with
   Test Data *"Number of Skills to create | 6"* — the "confirm" branch is what
   drifted. Then no TMS change is needed and the fix is provably faithful.
2. **Make the test own the precondition** — create everything it needs, with
   **run-unique names** (`f"prefix-{uuid4().hex[:8]}-s{n}"`), and widen cleanup
   + cleanup-verification to match. Fixed names collide with orphan debris from
   hard-killed runs, and name-based lookups then match the wrong entity.
3. **Refuse the conditional skip.** It is the tempting "resolution path" and it
   is masking: the precondition is absent on *every* clean project, so it fires
   every run and reports green-by-absence while the TMS still claims
   `execution_type: automated`.

## What "fixed" means when you cannot reproduce

A local env is usually the *dirty* one, so a green local gate cannot reproduce
the CI condition. The proof is **structural, not empirical**: grep the
post-fix spec and show no read of data the test did not create. Say so plainly,
and leave the card at `Ready` until the next CI run confirms it.

Related: [[rerun_tainted_gate_is_not_a_clean_gate]]
