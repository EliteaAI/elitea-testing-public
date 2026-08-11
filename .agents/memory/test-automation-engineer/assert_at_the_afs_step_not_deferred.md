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
