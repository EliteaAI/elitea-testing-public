---
name: Support Assistant bubble is absent (not empty) while a status message shows
description: In-flight assistant messages render NO bubble node — strict inner_text() raises; use get_last_assistant_text_or_empty()
type: feedback
aliases: [support assistant in-flight text, showBubble, elitea-assistant status message, empty bubble]
tags: [area/support-assistant, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## The fact

`MessageItem.tsx:19` (elitea_assistant):

```
showBubble = message.role === 'user' || message.content || (!hasStatusMessage && message.isStreaming)
```

An in-flight ASSISTANT message has a `statusMessage` and no `content`, so all three disjuncts are
false and the `support-assistant-message-bubble` node **does not exist**. It is not an empty bubble.

## Why it bites

A `page.evaluate` probe reading `document.querySelector(...)?.textContent` sees `''` (JS null-ish),
so analysis notes may say "the in-flight bubble holds 0 characters". Playwright's strict locator API
**raises** on the same state. Any spec sampling in-flight assistant text must tolerate absence.

Use `SupportAssistantPage.get_last_assistant_text_or_empty()` (added for ELITEA-2426) — treats "no
bubble yet" and "an empty bubble" as the same observation: zero rendered characters.

## Related

The Support Assistant renders **no partial text ever** — status messages are the only in-flight
feedback; the typewriter (`AnimatedMessage`/`useTypewriter`) is dead code (`isAnimating` only ever
assigned `false`). Any case asking to observe progressive text arrival here is case-text drift.

Related: [[project_briefing]]
