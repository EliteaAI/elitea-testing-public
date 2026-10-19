---
name: DOM node content replacement needs a text-match wait, not a presence wait
description: When an action REPLACES an existing visible element's text (not inserting a new one), locator.wait_for(state="visible") resolves instantly and reads stale content — poll for the exact expected text instead
type: feedback
---

## What happened (ELITEA-2878, chat mid-turn interjection "Stop" rescue, 2026-10-17)

Clicking the chat's Stop control while interjections are queued rescues the
head-of-queue item by REPLACING the text content of the ORIGINAL (already
on-screen) prompt message's own `<li>` DOM node — not by inserting a new
timeline entry. Same element, new text, confirmed live via a DOM dump.

The natural-looking wait:
```python
chat.messages_container.nth(initial_count).wait_for(state="visible", timeout=5000)
rescued_text = chat._extract_message_body(chat.messages_container.nth(initial_count))
assert rescued_text == "First queued message"
```
fails intermittently (and failed outright on the first real run) because the
node is ALREADY visible before the click — `wait_for(state="visible")`
resolves in ~0ms and proves nothing about the node's *content*, so the read
immediately after can catch the pre-replacement text.

`wait_for_message_body_growth()` (an existing helper, built for streaming
responses) doesn't fit either: it only detects the text getting LONGER, and
a rescued interjection's text can be SHORTER than the long-running prompt it
replaces (replacement, not append).

## The fix — poll for exact content equality

```python
def wait_for_message_body_text(self, message_locator, expected_text: str, timeout: int = 5000) -> str:
    """Poll _extract_message_body(message_locator) until it equals expected_text exactly."""
    deadline = time.monotonic() + timeout / 1000.0
    last_seen = ""
    while time.monotonic() < deadline:
        last_seen = self._extract_message_body(message_locator)
        if last_seen == expected_text:
            return last_seen
        time.sleep(0.3)
    raise TimeoutError(f"... last seen {last_seen!r}")
```
(`chat_page.py` — new general-purpose method, distinct from
`wait_for_message_body_growth`.)

## When to reach for this again

Any time a UI "cancel/stop/undo/retry" action is suspected to REUSE an
existing DOM node's content rather than add/remove a sibling — the tell is a
message-count assertion staying flat (`get_message_count()` unchanged)
across the action while the text you expect to see changes. A presence-only
wait on that node is a no-op; verify with a live DOM dump
(`_extract_message_body` + raw `inner_html()` before/after) before assuming
either shape — don't guess from the case text alone (the AFS here originally
said "lands at nth(initial_count) immediately", true for the INDEX but silent
on the content-replacement mechanism, which is the part that actually races).
