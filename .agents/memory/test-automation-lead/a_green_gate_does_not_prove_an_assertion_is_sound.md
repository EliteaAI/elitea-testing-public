---
name: A green gate does not prove an assertion is SOUND — only that it passed here
description: An assertion whose expected value comes from the test's own environment (a clock, a locale, a machine offset) can be structurally wrong and still pass N-of-N; ask what produced the EXPECTED side, not just the actual
type: feedback
aliases: [clock-coupled assertion, datetime.now in a test, expected side oracle, green but unsound, TZ-dependent test, N-green proves nothing]
tags: [area/test-repair, area/gate, type/diagnosis]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

The fidelity policy trains everyone to ask *"what produced this value?"* about the
**actual** side of an assertion — that is what catches mocks and injected state. Nobody
asks it about the **expected** side, because an expectation is "just the test".

But an expectation computed from the test's own environment is an oracle too, and it can
be wrong. On ELITEA-1891 (#1873, PR #1878) round 0 shipped:

```python
now = datetime.now()
acceptable = {fmt(now), fmt(now - timedelta(minutes=10))}   # bound the midnight edge
assert rendered_date in acceptable
```

It passed the implementer's 3×, and would have passed mine. It was still unsound: this
backend serializes **naive** timestamps and the renderer skips the app's own
`convertTime()` normalizer, so the UI shows the **server's** clock. Measured on a UTC+4
box: rendered `15:30` while `datetime.now()` read `19:31` — **4 hours**. It only passed
because it compared *dates*, and a 4-hour skew at 15:30 does not cross midnight.

## Why the gate was structurally blind to it

- **GHA runs UTC**, so there `datetime.now()` *is* the server clock — green forever.
- It would fail **only** on a developer machine, **only** between local midnight and
  midnight+offset — then go **3/3 deterministic RED** and read exactly like a real
  regression under § Merge gate.

So the environment where it is wrong is the one that never runs it, and the shape of the
failure impersonates the thing the gate exists to detect. More runs cannot find this. Only
reading can.

## What to actually do

1. **Grep the diff for environment-derived expectations**, not just for substitutions:
   `datetime.now|utcnow|time\.time|locale|tzname|platform\.`. On this repo that grep hit
   exactly one file in the entire suite — a lone hit is itself the signal (no precedent
   = no one reviewed this shape before).
2. **Prefer the API-derived oracle** — `.agents/testing.md` § Fidelity policy already says
   it: *capture the real response and assert the UI against it*. Both sides then read the
   same `created_at` string and there is no clock in the comparison at all.
3. **Mirror the product's arithmetic; never compensate for it.** A helper that "corrects"
   the product's timezone handling passes before *and* after a fix — silently masking the
   defect forever. A mirror goes red **by name** when the product is fixed, which is the
   signal you want. Say so in the assertion message and name the bug id.
4. **When an IC self-flags an assertion as the weak spot, that is a blocker, not an FYI.**
   The implementer here flagged it and shipped it anyway, deferring to me; it cost a full
   review round. Fix or escalate *before* handoff.

## The generalisable form

> If the expected value would differ on another machine, at another hour, or in another
> locale, the assertion is coupled to the environment — and N×-green on ONE environment
> is not evidence about it.

Related: [[local_gate_cannot_verify_a_deployed_only_race]], [[deployed_only_failure_claims_are_hypotheses]], [[ci_green_can_mean_zero_tests_ran]]
