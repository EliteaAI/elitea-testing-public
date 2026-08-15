---
name: is_participants_badge_visible() cannot prove a negative transition
description: ChatPage.is_participants_badge_visible() only waits for state="visible" — `assert not is_participants_badge_visible(...)` right after a removal click can read "still visible" a moment before the DOM update lands. Use the new wait_for_participants_badge_absent(section, timeout) (state="hidden") instead.
type: feedback
---

## What happened (ELITEA-2178, 2026-08-16)

`ChatPage.is_participants_badge_visible()`'s implementation:
```python
badge.first.wait_for(state="visible", timeout=timeout)
return True  # or False on TimeoutError
```
It only ever waits for VISIBLE — called as `assert not
chat.is_participants_badge_visible(...)` immediately after clicking "Remove"
in a participant-removal confirmation dialog, it read `True` (badge still
visible) even though `wait_for_network()` + the dialog closing had already
happened — the badge's own re-render just hadn't landed yet. Same class as
the project's `positive_existence_wait_cant_assert_negative_transition.md`
lesson, here hitting a NEW method the existing lesson didn't cover.

**Fix:** added `ChatPage.wait_for_participants_badge_absent(section, timeout)`
— calls `badge.first.wait_for(state="hidden", timeout=timeout)` directly, a
genuine wait for the negative transition. Also correct (and fast — resolves
immediately) when the badge was never in the DOM to begin with, e.g. checking
absence right after a fresh page reload.

## When this applies

Any assertion that a participants badge (`chat-participants-badge-{section}`)
is ABSENT right after an action that removes the last participant of that
section (agent/pipeline/toolkit/mcp/users). Checking PRESENCE (`assert
is_participants_badge_visible(...)`) is unaffected — that direction already
uses the correct wait.
