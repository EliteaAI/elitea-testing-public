---
name: A card at Ready with an undelivered verification is an open loop — go back and close it
description: When you merge with a stated evidence gap, the gap is a debt; re-check it next session, because the environment may have recovered and the answer may be "your fix was incomplete"
type: feedback
aliases: [Ready is not done, undelivered verification, evidence gap debt, re-check the blocker, DEV verified later]
tags: [area/test-repair, area/ci, type/gate]
created: 2026-09-04
updated: 2026-09-04
---

## What happened (ELITEA-1886 / #1812)

2026-08-27: merged a repair with DEV verification **unobtainable** (auth outage #1850),
declared the gap honestly in the PR, the closure record and the spec docstring, moved the
card to `Ready`.

2026-09-04, re-entering the same card: auth had recovered **within hours** of that merge.
DEV had been running the fix for a week and **disagreed**:

| Date | Result |
|---|---|
| 08-27 | PASS |
| **08-28** | **FAIL — 3 attempts, at the assertion I had added** |
| 09-01 | PASS |

The repair's *diagnostic* half was right; its *robustness* half did not close the race and
**could not**. `Ready` had been premature, and only re-checking found it.

## The rules

1. **A stated evidence gap is a DEBT, not a disclosure.** Saying "not verified" in the
   closure record is necessary but not sufficient. Re-check it the next time you touch the
   card — the blocking condition is often gone. ([[unparking_a_blocked_card_recheck_the_blocker_first]]
   generalises: re-check a blocker before assuming it still blocks — and also before
   assuming your delivery survived it.)
2. **When re-entering a `Ready` card, read the environment, not just the comments.** The
   dispatch says to read new comments first. Do that — but a card whose verification was
   owed also needs the *runs* read. Nobody comments "your fix failed on DEV".
3. **Grepping CI logs for one test's outcome: the verdict is NOT always on the node-id
   line.** pytest prints `PASSED`/`FAILED` on a separate line when a `[FAIL] Screenshot:`
   line is interleaved. My first pass reported the 08-28 run as "test absent" and I nearly
   filed that as fact. The tell was that "absent" made no sense in a 26-passed job.
   Grep the file name, print surrounding lines, and reconcile against the job totals.

## The corollary that actually mattered

The 08-28 failure was **at the assertion round 1 added** — which is the assertion doing its
job, not a regression. Distinguishing "my new check caught something" from "my new check is
a false red" required the failure screenshot from the run's allure attachments (**not** the
`test-results-*` artifact, which holds only junit/html/reruns). Pull the artifact before
theorising; both readings were plausible from the traceback alone and they had opposite
consequences.

Related: [[local_gate_cannot_verify_a_deployed_only_race]], [[ci_green_can_mean_zero_tests_ran]]
