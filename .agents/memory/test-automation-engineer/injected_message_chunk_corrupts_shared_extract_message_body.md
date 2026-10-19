---
name: injected-message-chunk corrupts shared _extract_message_body once an interjection fires
description: A message's own <li> grows an extra "sent while running" annotation once a mid-turn interjection targets its run; the un-scoped bodyMedium selector picked up both texts concatenated
type: feedback
---

## What happened (ELITEA-2875, first live run, 2026-10-17)

`ChatPage._extract_message_body()` (shared by many callers — message-count
assertions, FIFO-order checks, response-text checks across the whole chat
test surface) reads body text via `.MuiTypography-bodyMedium` spans inside
the message `<li>`. Once a mid-turn interjection is sent WHILE a given
message's turn is still running, the frontend renders an extra annotation
block directly inside that ORIGINAL message's own `<li>`:

```html
<div class="... " data-testid="injected-message-chunk">
  <span class="...bodySmall">sent while running</span>
  <span class="...bodyMedium">Interjection message</span>
</div>
```

The un-scoped selector picked up BOTH the original message's own bodyMedium
span AND this annotation's nested bodyMedium span, concatenating them:
`"<original prompt>\nInterjection message"` instead of just `"<original
prompt>"` — which broke a 4-entry-timeline assertion that expected the
original message's text to stay unchanged.

## The fix

Exclude spans nested inside `[data-testid="injected-message-chunk"]`:
```python
body_spans = message_locator.locator(
    '.MuiTypography-bodyMedium:not([data-testid="injected-message-chunk"] .MuiTypography-bodyMedium)'
)
```
Safe for every other caller: no other message type ever renders this testid,
so the exclusion only changes behavior for the exact case that was wrong.

## When this matters

Any new chat test — mid-turn-interjection or not — that calls
`_extract_message_body` / `get_message_text_at` / `get_last_message_text` on
a message that MIGHT have had an interjection sent against its run will get
clean text now. If a FUTURE case needs to assert the annotation text itself
("sent while running: ..."), it needs its own dedicated read scoped INTO
`[data-testid="injected-message-chunk"]`, not a change to the shared body
extractor.
