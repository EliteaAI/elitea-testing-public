---
name: Allure step title can claim a verification the code never makes
description: Read every allure.step title as a claim and check it against the assertions inside that block
type: feedback
aliases: [allure step title claim, step title vs assertion, unmade verification]
tags: [area/review, type/heuristic]
created: 2026-08-22
updated: 2026-08-22
---

## The trap

`with allure.step("... verify exactly one DELETE request fires ...")` read well in review and
matched the AFS — but the block only awaited ONE response via `page.expect_response` and asserted
its status + query params. Nothing counted requests, and the test registered no
`page.on("request")` listener at all (its two sibling tests in the same file did). The step title
is what a report reader sees, so it shipped a verification claim nobody made.

Found on ELITEA-1848 (`test_artifacts_delete_all_and_dismissal.py`, Step 7), 2026-08-22.

## The check

Treat each step title as an assertion inventory: every verb in it ("exactly one", "only", "no",
"still", "immediately") must map to a statement inside that `with` block. Mismatch ⇒ either add
the assertion or reword the title — the cheap fix is usually the assertion, since a sibling test
in the same file often already has the listener.

Related: [[afs_axis2_claim_needs_grep_not_just_row_presence]] · [[passing_assertion_may_prove_nothing]]
