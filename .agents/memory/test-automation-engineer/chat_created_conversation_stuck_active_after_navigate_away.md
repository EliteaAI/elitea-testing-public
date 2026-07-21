---
name: +Chat-created conversation stays stuck "active" after navigating away — reload fixes it
description: A conversation created via +Chat keeps its sidebar item permanently marked active-conversation even after navigating to a different conversation, silently no-op'ing any later click back onto it. Confirmed product defect #692. A page.reload() while on the OTHER conversation's URL clears the stale flag.
type: feedback
---

## What happens

Sequence: click "+Chat" → send message(s) → wait for the AI reply AND for
generation to genuinely complete (`ChatPage.wait_for_generation_complete()`,
not just `wait_for_message_content_stable()` — see the companion gotcha
below) → click a DIFFERENT, already-existing conversation in the sidebar.
Navigation to the different conversation works correctly (URL changes,
content loads). But inspecting the DOM: the FIRST conversation's sidebar row
(`DraggableConversationItem`'s wrapper `<div>`) still carries the
`active-conversation` CSS class. Clicking that row again does **nothing** —
no navigation, no network request, no error. It is a permanent no-op for
the rest of the session.

Confirmed via direct DOM inspection
(`el.parentElement.className.includes('active-conversation')`) before/after
navigating away — the class never moves off the +Chat-created conversation,
even though the URL and page content correctly reflect the OTHER
conversation.

## Root cause (read from EliteaUI source)

`ConversationItem.jsx`:
```js
const onClickConversation = useCallback(() => {
  if (!isActive) onSelectConversation(conversation);
}, [conversation, isActive, onSelectConversation]);
```
`isActive` comes from `Conversations.jsx`:
`isActive={selectedConversationId === genConversationId(conversation)}`.
For a conversation object created via the `+Chat` flow, this comparison
apparently never re-evaluates to `false` for that object after navigating
away — the guard silently blocks the re-click forever. Ruled out timing: a
`sleep`/longer wait does not help; the flag genuinely never clears on its
own for this conversation's list entry.

## The workaround that works

**A `page.reload()` immediately after navigating to the OTHER conversation**
(so the reload lands on the DIFFERENT conversation's URL, not the stuck
one) forces a full client-state re-derivation and correctly clears the
stale flag — confirmed live, clicking back onto the original conversation
afterward works. A **same-URL reload of the seeded (stuck) conversation
does NOT fix it** — the reload has to happen on the OTHER conversation's
URL specifically.

```python
chat.click_first_other_conversation(conv_id, timeout=UI_ELEMENT_TIMEOUT)
page.reload(wait_until="domcontentloaded")
chat.wait_for_page_load()
```

## Filed as

EliteaAI/elitea-testing-public#692 (ELITEA-2095, PR #693).

## Related gotcha in the same investigation

`wait_for_message_content_stable()` (a text-heuristic) can resolve BEFORE
the app's own internal streaming/nav-blocking flag actually clears — a
conversation-switch click issued right after content-stable but before
`wait_for_generation_complete()` confirms is silently swallowed (separate
from the stuck-active bug above). Always call
`chat.wait_for_generation_complete()` before any navigation-away attempt
right after an AI response.

## When this applies

Any future case that needs to create a conversation via `+Chat`, navigate
away from it, and later click back onto it from a sidebar list (Today
section, search results, etc.) in the SAME test/session. Add the reload
step between the navigate-away and the re-open.
