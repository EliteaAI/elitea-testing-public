---
name: Chat Send — what proves a send registered
description: The composer is a LAGGING signal in ChatBox; only the issued conversation POST proves the Send registered
type: feedback
---

**Never use "the composer still holds the text" as proof that a chat Send did not
fire.** It is a lagging signal, and keying a retry on it can fire a second send.

Verified live in `../EliteaUI` (2026-09-04, ELITEA-1886 / issue #1812 round 2):

- `UserInput.jsx`'s `sendQuestion()` DOES clear the composer synchronously before
  `onSend` — but only `if (clearInputAfterSend)`.
- `NewChatInput.jsx:378` wires `clearInputAfterSend={clearInputAfterSubmit}`
  (default `true` at :28) — **but `ChatBox.jsx:2950` passes
  `clearInputAfterSubmit={false}`.**
- So for the chat/embedded-chat composer the reset happens in the CALLER, at
  `ChatBox.jsx:1174` (`chatInput.current?.reset()`), **after** `await onSend(...)`
  (1059) and `await uploadAttachments(...)` (1085), success path only.

⇒ a populated composer is equally consistent with "nothing was sent" and with
"a send is in flight". A retry keyed on it alone duplicates messages.

**The sound discriminator is the REQUEST, at issue time.** `sendQuestion()`'s guard
(`if (question.trim() && !disabledSend)`, `UserInput.jsx:238`) early-returns before
any network call, and the create path has **no await before** `createConversation()`
(`useApplicationChat.hooks.js:311+`, reached from `onSend` at :746 with no preceding
await). So the conversation POST is issued within microseconds of the guard passing:

```python
page.on("request", lambda req: hits.append(req.url)
        if "/conversations/prompt_lib/" in req.url and req.method == "POST" else None)
```

A recorded request proves the send registered **even if the response never arrives** —
which a `page.expect_response` oracle alone cannot distinguish from "never sent".

Predicate breadth is safe: `conversationCreate` (`chat.api.js:108`) is the **only**
POST on that path; `runHistoryApi.js:19` and `evaluationApi.js:293` hit the same path
as **GET**. So a bare `"/conversations/prompt_lib/" in url and method == "POST"` is
unambiguous.

Button lifecycle, for anyone tempted to assert on it instead: `chat-send-button` does
not exist at all while the composer is empty — `SendButton.jsx` early-returns
`chat-voice-mode-button`. On localhost after a starter click the button goes
`absent -> enabled` with **no observable DISABLED state** (5 ms sampling, 2026-09-04),
which is exactly why the race is invisible locally and wide on a deployed env.

Caveat: the POST is conditional — `needsConversationCreation: !activeConversation?.uuid
&& isAgentsPage` (`ChatBox.jsx:1052`). It proves a send only for the FIRST message of a
fresh conversation. On a conversation that already exists, no POST is issued and this
signal says nothing; find a different oracle there.

Related: the fresher-fiber-props race that makes the click a no-op at all is product
bug #2011 — React delivers the synthetic handler from CURRENT fiber props, so a click
the DOM permitted can still hit a `disabledSend` that flipped true. `to_be_enabled()`
narrows that window; it cannot close it.
