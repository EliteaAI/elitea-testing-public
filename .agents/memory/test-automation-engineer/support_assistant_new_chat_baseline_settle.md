---
name: Support Assistant New-chat baseline settle
description: After start_new_chat_via_testid(), assert copy-button count == 1 before taking any baseline — the helper's own wait can be satisfied by a stale button
type: feedback
aliases: [new chat baseline, start_new_chat_via_testid, support assistant fresh session, greeting copy button]
tags: [area/support-assistant, type/flake-prevention]
created: 2026-08-22
updated: 2026-08-22
---

## The trap

`SupportAssistantPage.start_new_chat_via_testid()` waits for
`message_copy_buttons.first` to become **visible**. When the previous conversation
already had completed assistant messages, a *stale* copy button satisfies that wait
while the message list is still being cleared — so a baseline read immediately after
can be too high, and a later `to_have_count(baseline + 1)` never converges.

## The fix

A New chat opens with exactly **one** completed assistant greeting (surface digest
quirk 10), so the exact count is a settle a stale DOM cannot satisfy:

```python
support_page.start_new_chat_via_testid(timeout=WIDGET_TIMEOUT)
expect(support_page.message_copy_buttons).to_have_count(1, timeout=WIDGET_TIMEOUT)
```

Shipped in `test_support_assistant_history_title_preview.py` (ELITEA-2427), used
twice — once before the send, once for the case's own "New chat pushes the session
into history" step.

## Related

Closing the history dropdown is a **second click on the history button**, not an
outside click: the button sits inside `historyDropdownRef`, so the outside-click
handler in `ChatHeader.tsx` never fires for it.

Related: [[project_briefing]]
