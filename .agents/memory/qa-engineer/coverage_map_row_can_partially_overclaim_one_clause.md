---
name: Coverage Map row can partially overclaim one clause
description: An AFS Coverage Map row's "asserted" disposition is not a single atomic fact — a row can genuinely assert 2 of 3 claimed sub-clauses while silently overclaiming the third; verify each clause in the "Asserted where" text against the actual code, not just the row's overall disposition
type: feedback
---

## What happened

PR #698 (ELITEA-2132, chat folder creation), round-2 review. The AFS
Coverage Map row for case step 3 (`test-specs/chat-interface/l3_chat-folder-creation-via-chats-header-icon_ELITEA-2132.md:60`)
reads:

> `3 Click the folder icon | New folder entry appears at top of folder list in editable mode with default name e.g. 'New folder' | AFS step 3 | step 3: entry at top of list, chat-folder-name-input value = "New folder", focused | asserted`

The "Asserted where" cell names three sub-claims: (1) entry at top of
list, (2) input value = "New folder", (3) focused. The wording traces
directly to the **original TMS case's own step-3 expected result**
(`ELITEA-2132_....md:42`: "New folder entry appears **at top of**
folder list").

`automation/tests/ui/chat/test_folder_creation.py:142-152` (Step 3
block) genuinely asserts (2) and (3) — `folder_name_input.input_value()
== "New folder"` and `expect(...).to_be_focused()`. It never asserts
(1) — no check of DOM/visual position relative to the existing "This
Week" date-group heading. The row's disposition is still marked
`asserted` for the whole thing.

This was missed by the analyst (who wrote the row), by round-1's
reviewer (who only checked the named hover-target delta), and would
have been missed by me too if I'd only spot-checked row presence
instead of reading each clause in the "Asserted where" text against
the actual assertions in the code.

## Why it matters

A future regression that renders the new-folder entry at the *bottom*
of the list (or inside the wrong date-group) instead of the top would
sail through this test undetected, while the Coverage Map — the
document whose entire purpose is traceability — insists the case's own
expected result is covered.

## The check to run

When ticking a Coverage Map row against the source case (standing
reviewer check "Coverage completeness"), don't stop at "does this row
exist and say `asserted`". Split the "Asserted where" text into its
individual claimed sub-observations and grep the implementation for
each one separately. A row is only fully honest if every sub-clause it
names has a matching assertion — partial coverage inside one row is as
real a gap as a missing row entirely, and the existing standing-check
wording ("every `asserted` row's expected result maps to a real
assertion in the implementation") already covers this if read
literally — the miss here was reading it as "row has *an*
assertion" instead of "row's *full* expected result has a matching
assertion".
