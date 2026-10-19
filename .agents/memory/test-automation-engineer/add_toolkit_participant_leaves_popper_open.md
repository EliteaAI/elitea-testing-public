---
name: ChatPage.add_toolkit_participant() leaves the Toolkits submenu popper open after selection
description: After it selects a toolkit, the plus-menu Toolkits submenu popper stays open and intercepts the next click (composer send, HITL Authorize/Block button) — close it with Escape + an outside mouse click before the next interaction
type: feedback
tags: [area/chat, area/hitl, type/pitfall]
created: 2026-10-19
---

## What happened

Confirmed live 2026-10-19 (ELITEA-3372 implementation, HITL steps 9-12).
`ChatPage.add_toolkit_participant(toolkit_name)` opens the plus menu → Toolkits
submenu, searches, and clicks the matching `li[role="menuitem"]` to add the
toolkit — but it does not close the popper afterward. The open popper's
subtree (`<li data-testid="skills-menuitem">` or similar, or the `<p>Toolkits</p>`
label) then intercepts pointer events on whatever is clicked next:
- immediately sending a message in the composer, AND
- later, the `sensitive-action-authorize-button` / `sensitive-action-block-button`
  click on the HITL card that message triggers.

Playwright's own retry-with-force eventually powers through the second case
(hence `.click(force=True)` on the HITL buttons works), but the first case
(`send_message()`'s own button/Enter press) can still race it.

## The fix

Right after `add_toolkit_participant()`, before sending the triggering message:

```python
chat.add_toolkit_participant(toolkit_name, timeout=UI_ELEMENT_TIMEOUT)
chat.page.keyboard.press("Escape")
chat.page.mouse.click(10, 10)
chat.send_message(...)
```

Same idiom `close_modules_panel()` / the ELITEA-3372 AFS's own exploration
notes already use for a lingering Modules-panel popper — this is the SAME
class of stale-popper interception, just triggered by `add_toolkit_participant()`
instead of the Modules panel. If `add_toolkit_participant()` gains its own
close-popper step in a future change, this workaround becomes redundant but
harmless (Escape + an outside click on an already-closed popper is a no-op).
