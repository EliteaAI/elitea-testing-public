---
name: Conditional assertions that may never fire — the guarded-lookup trap
description: An assert wrapped in `if x is not None:` over an UNFILTERED first page is nondeterministic coverage — it reads as a check but may silently skip
type: feedback
aliases: [conditional assert, guarded assertion, dead assertion, is_seen check, unfiltered rows]
tags: [area/review, area/assertions]
created: 2026-08-26
updated: 2026-08-26
---

## The shape

```python
rows_after = page_obj.navigate_and_get_rows()      # UNFILTERED first API page
page_obj.search_notifications(TERM)                # response DISCARDED
row_after = next((r for r in rows_after if r["id"] == target_id), None)
if row_after is not None:                          # <- may silently be None
    assert row_after["is_seen"] == is_seen_before
```

Seen in PR #1787 (ELITEA-2261, `test_notification_link_navigates_to_conversation.py`
step 6). The target was selected from a *filtered* search result, but the guard
searches an unfiltered page-1 payload.

**Verified sizing (2026-08-26, EliteaUI source — correct the earlier claim in this
entry that it "can never" fire):** `NotificationCenter.jsx` defaults
`pageSize: 50` while the DEV account carries 89+ notifications and grows. So the
guard fires *sometimes* — it is nondeterministic, not permanently dead, which is
worse for review: it can pass a spot-check and still skip silently as history grows.

## How to catch it

Ask of every `if <lookup> is not None:` / `if <list>:` guard around an assert:
**under the live data this spec runs against, is the guard reliably true?** If the
collection is a paginated/unfiltered page and the target came from a *filtered*
set, the answer is "only by luck". Check the product's own page size before
concluding either way — do not assert "never fires" without it.

## The fix is usually free

The filtered response is already in hand — the spec threw it away. Use
`search_notifications(TERM).json()["rows"]` (the same oracle step 2 selected the
target from) and drop the guard, making the assertion unconditional.

Related: [[project_briefing]]
