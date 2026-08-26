---
name: A non-reproducing gate red still goes to stabilize
description: When a red gate will not reproduce, send it to batch-stabilize with your hypothesis framed as verify-or-refute — re-running only ever buys you a green, never a cause
type: feedback
aliases: [gate red does not reproduce, flaky gate, cannot reproduce red, stabilize workflow, non-reproducing failure]
tags: [area/gate, type/lesson]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

A gate goes red once. You re-run it and it is green. Re-run again — green.
Seven green runs later the honest-looking conclusion is *"flake, merge it"*.

That conclusion is unearned. **Re-running can only ever tell you the failure is
intermittent — it can never tell you why.** And "intermittent" covers both
harmless environment noise *and* a real race that will fire in CI on someone
else's morning.

## What to do instead

Send it to the **stabilize workflow** (`batch-stabilize`), which is the
sanctioned route for a red classified as flake-or-test-code-bug. It reads
artifacts a re-run throws away — allure result JSON, the failure **screenshot**,
the aria snapshot — and reasons about product source.

**Frame your hypothesis as "verify or refute", never as a prescription.** Write
down what you think, the evidence for it, *and* an explicit instruction that a
contrary finding is the wanted answer:

> "LEAD'S DIAGNOSIS TO VERIFY OR REFUTE: … If you conclude it is NOT a race but a
> genuine product inconsistency, that is a product bug: say so, do not paper over
> it, and return it for the lead to file."

This matters because of `.agents/role-overrides.md` § Orchestrator slot — a
lead's dispatch is the strongest signal in the pipeline, and an IC treats it as
settled. Framing it as refutable is what keeps the check independent.

Also state the boundaries, or the cheap fix wins: **do not merely lengthen a
timeout** (that hides a race rather than removing it), do not weaken or drop the
assertion, no sleeps, no masking.

## The worked case (#1397 wave 4, 2026-08-24)

Red: `sidebar-notifications-mark-all-read-button` not found, popover open.
It did not reproduce in **7** subsequent runs (4 standalone + 3 of the gate's
exact scope). Signals that it was load-correlated rather than random: runs 1-2
passed at ~34 s, the failing run took **56.91 s** (~1.7×).

Stabilize found what no re-run could: the **failure screenshot showed five grey
Skeleton bars**, and `NotificationList.jsx` renders skeletons only while
`isFetching && !notifications.length` — the three list states are mutually
exclusive. Proof the list request was still in flight at 5.07 s. Not empty data,
not a wrong project, not a 4xx.

Fix: wait on the product's **own** list response inside the page object, plus a
unit regression test pinning that the predicate must *reject* the unread-count
probe (which shares the URL prefix and fires on page load — matching it would
resolve instantly and hand back a Skeleton, restoring the defect silently).

It also found and fixed a **second latent cause I never asked about**, which a
re-run-until-green would have shipped.

## Two things that hide reds here

- `pytest.ini` sets `--reruns=2`. It is `--only-rerun`-filtered to infra patterns,
  so an `AssertionError` is not retried — but other classes are, and a retried
  failure is recorded **PASS** in the junit archive. Judge flake rate from
  **allure results**, not junit.
- A collection error in the selected directory aborts the whole invocation, so
  "2 errors" can be pre-existing breakage rather than your change (see #1769).

Related: [[blast_radius_red_classify_with_a_control_run_on_base]] · [[gate_red_recurring_on_different_tests_check_tracker_before_diagnosing]]
