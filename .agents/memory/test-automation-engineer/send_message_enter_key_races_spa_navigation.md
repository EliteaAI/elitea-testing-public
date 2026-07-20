---
name: send_message(use_enter=True) races the SPA's /chat/{id} navigation
description: ChatPage.send_message(use_enter=True) returns as soon as Enter is dispatched, before the SPA finishes navigating from /chat to /chat/{id} — any state assertion keyed on that navigation (e.g. sidebar-create-button re-enabling) needs a polling expect(), not a synchronous read, right after send_message() returns
type: feedback
---

## What happened

ELITEA-2090 (PR #682) extended `test_create_conversation_via_ui_button` with a
gap assertion (GA3): `sidebar-create-button` (`+Chat`) should re-enable
immediately once Send is clicked, confirmed live by the analyst on the
click-`chat-send-button` path. The AFS itself flagged an open question: the
covering test actually sends via `chat.send_message(test_msg,
use_enter=True)` (Enter key), and the analyst explicitly wrote "I did not
independently re-verify the Enter-key path produces the identical timing."

Implementing GA3 as written (`assert chat.create_conversation_button.is_enabled()`
placed immediately after `send_message(use_enter=True)` returns) failed 1/1 on
first local run. JUnit capture showed the Locator's frame URL was still bare
`/chat` (not yet `/chat/{id}`) at read time — confirmed via screenshot too
(greeting screen still on-screen, message not yet visible in the transcript).

## Root cause

`ChatPage.send_message(text, use_enter=True)` calls
`self.message_input.press("Enter", timeout=60000)` and returns as soon as the
key event is dispatched — it does **not** wait for the SPA to navigate to
`/chat/{id}`. The button's disabled→enabled transition is gated on that
navigation completing (or a state update that happens around the same time),
which is async and takes a variable — if usually short — amount of time. A
bare synchronous `.is_enabled()` read right after `send_message()` returns is
racing that async transition, not testing a stable end-state.

## Fix

Replace the synchronous read with Playwright's polling web-first assertion,
scoped to a reasonable navigation timeout (this project's `NAVIGATION_TIMEOUT`
constant, 10s, already used elsewhere for the same kind of SPA-route-change
wait):

```python
expect(chat.create_conversation_button).to_be_enabled(timeout=NAVIGATION_TIMEOUT)
```

This keeps the same claim strength (still fails loudly, and within a bounded
timeout, if the button were actually gated on naming/generation completion
instead) while tolerating the real async gap. 3/3 clean-process runs green
after the fix.

## General lesson

When an AFS explicitly flags "I verified path A, the covering test actually
uses path B, I did not re-verify the timing transfers" — that sentence IS a
to-verify marker even though it isn't phrased as one in the AFS's own
"to-verify" vocabulary. Budget Phase-2/5 time for a timing race on path B
specifically; don't assume the analyst's click-path timing evidence
automatically applies to the covering test's actual send mechanism
(Enter-key vs. button-click, `fill()` vs. `press_sequentially()`, etc. — any
two "equivalent" user actions in this app can have different async
completion timing).
