---
name: Proving a negative without wait_for_timeout
description: Use Locator.wait_for(state=attached, timeout=N) + pytest.raises(TimeoutError) instead of a raw sleep to assert "nothing appeared"
type: feedback
---

## The trap

"Prove Shift+Enter didn't submit" / "prove no toast appeared" / any assertion
of absence feels like it needs a raw `page.wait_for_timeout(N)` because there's
no positive condition to wait for. There IS no sanctioned "no sleeps" exception
for this in `.agents/testing.md` or `.agents/role-overrides.md` — don't invent
one in a comment (ELITEA-1875 fix-round-1 finding: a comment cited a
nonexistent testing.md carve-out for exactly this).

## The fix — a real framework-native wait

```python
would_be_next = page_obj.some_item_locator.nth(baseline_count)
with pytest.raises(playwright.sync_api.TimeoutError):
    would_be_next.wait_for(state="attached", timeout=1500)
```

`Locator.wait_for()` is Playwright's own polling primitive (same family as
`wait_for_selector`/web-first assertions — explicitly allowed under Hard Rule
5's "framework-native waits" umbrella). Two real advantages over a blind sleep:
it resolves EARLY (fails fast) if the bad thing actually happens, and it needs
no exception comment because it isn't a sleep — it's the same mechanism used
to prove a positive, aimed at a slot that should stay empty.

Same duration as a sleep in the (expected) passing case — that's fine; the
point is the *mechanism*, not the wall-clock cost. Applies to: "no message
sent", "no toast shown", "no new row appended", any assert-nothing-happened
check.
