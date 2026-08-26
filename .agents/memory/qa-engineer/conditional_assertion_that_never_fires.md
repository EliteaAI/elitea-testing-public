---
name: Conditional assertions that never fire — the guarded-lookup trap
description: An assert wrapped in `if x is not None:` where the lookup targets an UNFILTERED first page is dead code that reads as coverage
type: feedback
aliases: [conditional assert, guarded assertion, dead assertion, is_seen check, unfiltered rows]
tags: [area/review, area/assertions]
created: 2026-08-26
updated: 2026-08-26
---

## The shape

```python
rows_after = page_obj.navigate_and_get_rows()      # UNFILTERED first API page
page_obj.search_notifications(TERM)                # response discarded
row_after = next((r for r in rows_after if r["id"] == target_id), None)
if row_after is not None:                          # <- almost always None
    assert row_after["is_seen"] == is_seen_before
```

Seen in PR #1787 (ELITEA-2261). The target notification was id `109487` in a
history of 89+ rows sorted `created_at desc`, so it is never on the first page —
the guarded assertion cannot execute, yet it reads as a real server-side check in
review and in the Coverage Map.

## How to catch it

Ask of every `if <lookup> is not None:` / `if <list>:` guard around an assert:
**under the live data this spec actually runs against, is the guard ever true?**
If the collection being searched is a paginated/unfiltered first page and the
target was selected from a *filtered* set, the answer is no.

## The fix is usually free

The filtered response is already in hand — the spec threw it away. Use
`search_notifications(TERM).json()["rows"]` (the same oracle step 2 selected the
target from) and drop the guard, making the assertion unconditional.

Related: [[project_briefing]]
