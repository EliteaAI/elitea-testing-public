---
name: Absence assertions can pass vacuously — check the locator is proven live in the same test
description: to_have_count(0) on a typo'd/renamed testid passes forever; require a positive assertion of the SAME locator somewhere in the test
type: feedback
aliases: [vacuous absence assertion, to_have_count(0), absence check, negative assertion review]
tags: [area/review, type/heuristic]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

`expect(x).to_have_count(0)` passes when the testid is misspelled, renamed upstream, or
never existed. It is the one assertion shape that gets *stronger* as the locator gets
*more* wrong — so a suite can accumulate absence checks that verify nothing, and no gate
sees it (green is green, and the mechanical locator grep only checks the handle SHAPE).

## The reviewer check (cheap, mechanical)

For every `to_have_count(0)` / `not_to_be_visible()` in the diff, ask: **is that same
locator asserted POSITIVELY somewhere on the test's executed path?** If yes, the testid is
proven live by the run itself and the absence assertion is real. If no, it is unfalsifiable
— ask for a positive anchor (usually the state transition the case already covers).

Worked example, ELITEA-2232 (`test_onboarding_provisioning.py`): five absence assertions
(`welcome_card`, `sidebar_toggle`, `project_selector_trigger`, `workspace_ready_title`,
`progress_footer`) and every one of the five is also asserted `to_be_visible()` earlier or
later in the same test, because the spec walks the state transition in both directions.
That is the pattern to look for — a state-transition spec gets this for free; a
single-state spec usually does not.

Related: [[partial_afs_amendment_hides_dropped_axis2_rows]]
