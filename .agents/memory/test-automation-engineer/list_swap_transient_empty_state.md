---
name: List-swap transient empty state defeats baselines and absence assertions
description: When a UI swaps one collection for another it usually clears first — read baselines only after an explicit non-empty settle
type: feedback
aliases: [transient empty list, baseline reads zero, conversation swap, absence assertion vacuous]
tags: [area/ui-tests, type/flake]
created: 2026-08-22
updated: 2026-08-22
---

## The trap

A control that swaps collection A for collection B (pick a conversation, switch a
project, change a filter) typically does it in two React commits: **clear**, then
**render the fetched data**. Between them the list is genuinely empty, and two
different assertion shapes both go wrong there:

- A `.count()` **baseline** taken in that window reads **0**. Every later delta
  assertion built on it is then off by the size of B. Symptom: a later step expects
  `1` where the correct answer is `len(B) + 1`.
- An **absence** assertion (`to_have_count(0)` on an item unique to A) is satisfied
  **vacuously** by the empty state, so it proves the swap happened when it may only
  prove the clear happened.

Waiting on the swap's own network response does not fix either — the response
resolves before React commits the render.

## The fix

Settle on a product-guaranteed non-empty invariant of B *first*, then read:

```python
expect(page_obj.copy_buttons).not_to_have_count(0, timeout=EXPECT_TIMEOUT)  # B has rendered
baseline = page_obj.get_copy_button_count()                                  # now safe
expect(page_obj.item_with_text(A_ONLY_TEXT)).to_have_count(0)                # now meaningful
```

Pick an invariant the product guarantees for *any* B (an assistant greeting, a
header row, a "0 results" placeholder), not one specific to the B you happened to
open.

Found on the Support Assistant history panel (ELITEA-2423) — cost one rerun. The
surface-specific record is `test-specs/support-assistant/_surface.md` quirk 35.

Related: [[project_briefing]]
