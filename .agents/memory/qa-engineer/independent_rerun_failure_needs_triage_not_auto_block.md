---
name: An independent-rerun failure needs triage before it becomes CHANGES_REQUESTED
description: Not every red run during independent live re-verification is a code defect in the reviewed PR — duration anomalies and non-recurrence under targeted follow-up are real signal that a rerun failure is environmental noise, not a structural race; distinguish before writing the verdict, don't auto-block on the first red run
type: feedback
---

PR #693/ELITEA-2095 round-3 re-review. The dispatch explicitly demanded
independent live reruns (not trusting the implementer's "GREEN 5/5" Run
Report) because round 2's own reviewer had caught two real, reproducible
race conditions that way (2/5 failed). Ran the merged spec 15x (deliberately
more than round 2's 5x, since 2/5 is a coin flip and I wanted real
confidence). Result: 14/15 GREEN, 1/15 RED.

The one failure was a genuinely new signal — an unfiltered console error
(`Failed to load resource: ... 500`) that was NOT either of the two
previously-fixed races (Context Budget counter poll, missing
`wait_for_generation_complete()`) — both of those held perfectly across all
15 runs. Two facts pointed away from "this PR's new code caused it":

1. The failing run's duration was 123s vs ~50-56s for every other run
   (>2x) — a strong signal of an external hiccup (slow/flaky shared DEV
   backend), not a deterministic logic race, which would show consistent
   timing.
2. I added temporary reviewer-only `page.on("response", ...)` debug
   instrumentation (properly reverted after, `git diff` confirmed clean)
   and ran 8 MORE times specifically hunting a recurrence. The known
   project-471 secrets 403 fired reliably every time (this incidentally
   also reconfirmed round 1's console-filter fix is real, not just
   claimed) but the mystery 500 never recurred, so I couldn't even pin the
   endpoint.

Given non-recurrence under targeted follow-up + a duration outlier + zero
attribution to any line this PR touches, I classified the finding as a
non-blocking follow-up (enrich the failure assertion with `msg.location` for
future triage) rather than CHANGES_REQUESTED, and returned APPROVED overall.

**The lesson: independent live-rerun is for catching real, attributable
defects — not for treating every observed red run as automatically
blocking.** The discipline that matters is: (a) always do the reruns
(rounds 1/2 prove this catches real bugs the Run Report misses), (b) when a
rerun goes red, spend the effort to characterize it — check if it's one of
the specific things under review, check timing for anomalies, try to
reproduce it again with more instrumentation before writing the verdict.
Auto-blocking on an unreproduced, duration-anomalous, non-attributable
single red run would set a bad precedent: it punishes a PR for its
environment's flakiness rather than its own defects, and every side-channel
check (console/pageerror) becomes a de facto merge-blocker for any one-time
backend blip. The bar is "did I genuinely investigate," not "did I find
zero red at any cost" or "did I block on any red no matter what."
