---
name: Per-step loop assertions can silently skip pre-loop steps
description: A "for step in range(3, N)" pattern asserting per-step observables (title/description/counter) often omits those checks for the 1-2 steps handled BEFORE the loop starts — check pre-loop blocks assert the SAME observable set the loop asserts, not a subset.
type: feedback
---

## What happened (2026-08-05, ELITEA-2227 review, PR #1162)

`test_help_center_sidebar_tour.py` implements "at each step, verify title +
description + step counter" (case step 6 / AFS step 6) as a loop over
`range(3, TOUR_TOTAL_STEPS + 1)` that asserts `title`, `description`
(visible + non-empty), and `step_counter`. Steps 1 and 2, handled in their
own `allure.step` blocks BEFORE the loop starts (because step 1 needs the
new-tab-open assertion and step 2 needs the Back-disabled/spotlight-baseline
assertion), only assert `title` + `step_counter` — `description` is never
checked for those two steps. The AFS Coverage Map still claimed "3 testids
checked per step" for all 17 steps.

The gap is invisible on a quick read because each individual block "looks
complete" (it asserts something plausible for what that block is about) —
it only shows up by grepping every occurrence of the shared observable
(`description`) across the whole file and counting which step numbers it
actually fires for.

## Reviewer check to reuse

When a per-step case requirement ("at each step, verify X/Y/Z") is
implemented as pre-loop setup blocks + a loop, grep the implementation for
every observable named in that requirement and manually map each hit to
the step number(s) it covers. A requirement claiming "each step" needs
100% step coverage for every named observable — partial coverage (skipping
the steps handled before the loop starts) is a real gap even though nothing
in the diff *looks* wrong locally, and it makes the AFS Coverage Map's
"asserted" disposition inaccurate.
