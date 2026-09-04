---
name: ChatBox composer clearing is a LAGGING signal — never key a send retry on it alone
description: ChatBox passes clearInputAfterSubmit={false}, so the composer resets AFTER the awaited send POST — a populated composer does not prove nothing was sent.
type: feedback
aliases: [clearInputAfterSend, clearInputAfterSubmit, composer clears after send, send retry discriminator, chat send registered]
tags: [area/chat, type/oracle]
created: 2026-09-04
updated: 2026-09-04
---

## The trap

`UserInput.jsx`'s `sendQuestion()` (EliteaUI) clears the composer synchronously
before calling `onSend` — **but only `if (clearInputAfterSend)`**. It is easy to
read that and conclude "composer populated ⇒ nothing was sent", which is the
natural discriminator for a bounded retry of a Send click.

**For `ChatBox` that conclusion is false.** `ChatBox.jsx:2950` passes
`clearInputAfterSubmit={false}` to the composer's `<NewChatInput>` (the same JSX
element as `onSend={onSendMessage}` at 2898). The composer is reset by the
CALLER instead, at `ChatBox.jsx:1174` — *after* `await onSend(...)` (1059) and
`await uploadAttachments(...)` (1085), and only on the success path (an
`uploadAttachments` failure `return`s at 1127 with no reset at all).

So during the whole send round trip the composer is still populated. A populated
composer is equally consistent with:

- nothing was sent (the handler's guard early-returned), and
- a send is in flight whose POST has not returned yet.

Retrying a Send click on that signal alone can therefore fire a **second** send.

## The sound discriminator: the REQUEST

`sendQuestion()`'s early return happens **before any network call**. So if the
send's POST was ever *issued*, the send registered — independently of whether
its response arrived, and independently of every prop-defaulting question above.

```python
send_requests: list[str] = []
page.on("request", lambda req: send_requests.append(req.url) if _is_send_request(req) else None)
...
except PlaywrightTimeoutError:
    if send_requests:                                    # authoritative
        raise
    if page_obj.chat_message_input.input_value() == "":  # second, independent proof
        raise
    if attempt == ATTEMPTS - 1:
        raise
```

Keep the composer read as a *second* proof — both must say "nothing was sent"
before a retry fires. Two independent signals can only narrow a retry, never
widen it. That is what keeps a retry-of-an-action distinguishable from masking.

## The general lesson

A prop with a `= true` default at its definition site tells you nothing until you
have **read the call site**. `grep`ping the definition (`UserInput.jsx:73`) and
the pass-through (`NewChatInput.jsx:28,378`) and stopping there is how a
plausible, well-reasoned, wrong invariant gets written into a dispatch brief and
into an analyst note. Grep for the prop name **in the consuming component** too —
one extra grep (`grep -n clearInputAfterSubmit ChatBox.jsx`) is what caught this.

Related: [[chat_send_button_force_click_race]]
