---
name: AFS step merging into one allure.step
description: causally-linked AFS steps (e.g. reload+verify-refresh) sometimes land as ONE allure.step in the implementation — check both sub-assertions exist, not just that the label mentions both
type: reference
---

## Pattern observed (PR #1231, ELITEA-2365 review, 2026-08-06)

AFS `l3_agent-hub-my-liked-reload-cross-tab-sync_ELITEA-2365.md` had distinct
numbered steps 8 ("click reload") and 9 ("verify list refreshes"), each with
its own Coverage Map row. The implementation
(`test_agent_hub_my_liked_reload_cross_tab_sync.py`) merged both into a single
`with allure.step("Step 8 — Reload Tab A ... and verify ... (Step 9)")` block.

`.agents/testing.md` § Step reporting / `.claude/rules/ui-tests.md` both say
"one `allure.step` per AFS step" — strictly this is a deviation. But it did
NOT cost coverage: both steps' assertions (reload response captured +
`"rows" in response` for step 9, chip re-selected + section visible for the
continuation) were present in the merged block. Verdict: non-blocking nit,
not `CHANGES_REQUESTED` — the causal link (you can't observe "refreshes"
without first reloading) makes the merge defensible, and no assertion was
dropped.

**What to check when this pattern recurs:** don't stop at "the step label
mentions both AFS steps" — read the block's body and confirm EACH merged
step's own expected-result assertion is still literally present. A merge
that drops one step's assertion while keeping the other's IS blocking; a
merge that keeps both is a documentation nit at most.

Also worth an eye during triangulation: a Coverage Map row can claim an
assertion exists ("Tab A state unchanged" at case step 6) that isn't
literally checked at that step in code (here: `page.bring_to_front()`, no
assert) — non-blocking when a LATER step's assertion actually proves the
same observable (step 7's "target agent absent" here), but still worth
naming in the review as an AFS/implementation precision drift.
