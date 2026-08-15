---
name: Assert at the AFS step, not deferred
description: Reviewer rejected assertion placement twice on the same case (ELITEA-2353) — verify each step's expected result inside that step's own allure.step block
type: feedback
---

Twice in a row, ELITEA-2353 ("Agent Hub — filter agents by multiple
categories") was rejected in review because the AFS's Step 3 expected result
(both category chips show `data-selected="true"` after the second chip
click) was verified one `allure.step` later — the implementation did
`click(second chip)` in "Step 3" and only asserted "both selected" in a
separate "Step 4".

**Rule:** when translating an AFS Coverage Map row into code, the assertion
for step N's "Verify: ..." clause goes INSIDE step N's own `allure.step`
block, immediately after the action that step describes — never pushed into
the following step's block, even if it reads more naturally that way in
code. This applies to every AFS-derived test, not just this one case: check
the AFS Test Steps table's own step numbering against your `allure.step`
numbering 1:1 before considering the test done.

Fixed in the third attempt (`tests/2353-multi-category-filter`,
`automation/tests/ui/agents/test_agent_hub_filter_multiple_categories.py`):
Step 2's click is immediately followed by asserting the first chip's
`data-selected="true"`; Step 3's click is immediately followed by asserting
BOTH chips' `data-selected="true"` — in the same block as the click that AFS
step describes.

**Variant caught in fix round 1 (ELITEA-2121, PR #1535, 2026-08-15): a step's
own verify can be missing altogether, not just moved — when a later step's
page-object method call happens to exercise the same precondition as a
side effect.** `test_folder_rename_via_context_menu_edit_option`'s Step 1
was labelled "hover row; verify 3-dot menu button becomes visible" but the
block only seeded the folder — no hover, no assertion. Step 2 then called
`open_folder_context_menu()`, which internally hovers + waits for the same
button before clicking it, so the test passed even though Step 1 asserted
nothing: the helper's internal `wait_for` silently absorbed Step 1's claimed
verify. Fix: add the explicit `hover()` + `expect(...).to_be_visible()` in
Step 1's own block even though a later step's helper would have caught a
regression anyway — a green run through a helper's internal wait is not
evidence for the step that claims the observable as ITS OWN. Same root
check as the deferred-assertion case: for every `allure.step` label, ask
"does an assertion I can point to actually live in THIS block for THIS
claim" — a helper call in a later block doesn't count, even if it happens
to depend on the same DOM state.
