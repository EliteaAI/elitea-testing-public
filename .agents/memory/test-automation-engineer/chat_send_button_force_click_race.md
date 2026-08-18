---
name: Chat send-button force-click race after fast composer population
description: chat-send-button force=True click can silently no-op right after a starter/programmatic setValue() populates the composer — use a plain (non-force) click there
type: feedback
---

## What happened (ELITEA-2093, 2026-08-14)

`UserInput.jsx`'s `sendQuestion()` gates the actual send on its OWN
`disabledSend` prop read (`if (question.trim() && !disabledSend)`) —
independently of whatever the `chat-send-button`'s DOM `disabled` attribute
reads at the moment Playwright's `.is_enabled()`/`expect(...).to_be_enabled()`
checks it. When the composer is populated **programmatically** right before
Send — e.g. `AgentModal.jsx`'s `onSelectStarter` → `NewConversationView.jsx`'s
`useEffect` (`selectedAgent && activeConversation?.isNew`) calling BOTH
`convertParticipantAndAddIt()` (adds the agent participant) AND
`onSendStarter()` (sets the composer text) off the SAME 100ms `setTimeout` —
`disabledSend`'s own dependency (`selectedParticipant`) can still be mid-flap
for a brief window after the button already reads enabled.

**Symptom:** `chat.send_button.click(force=True)` (the pattern the
ELITEA-2368/2369 siblings use successfully) reproduced a **deterministic
silent no-op** in this flow — no navigation, no network call, composer text
unchanged, no exception, no console error. `force=True` bypasses Playwright's
own actionability WAIT (stable/receives-events/enabled), so it can dispatch a
real click a moment before the DOM's `disabled` state has genuinely settled
in sync with the internal `disabledSend` state `sendQuestion()` reads.

**Fix that worked, reproduced 2/2 clean runs:** drop `force=True` — a **plain
`.click()`** makes Playwright wait for the element to be stable/actionable
before dispatching, which (empirically, this flow) lines up with
`disabledSend` having actually settled. `expect(chat.send_button).to_be_enabled()`
beforehand is still worth keeping (catches the OTHER 100ms race — the
`message_input` value itself not yet set) but is NOT sufficient on its own to
guarantee the click will register.

## When this applies

Any flow where the agent participant + composer content are populated
**together, asynchronously, right before the test clicks Send** — the Catalog
modal-starter click (ELITEA-2093), and by the same code path any future case
touching `NewConversationView.jsx`'s starter/attach-and-test entry (wave 12's
message-input/starter cases, `test-specs/agent-hub/_surface.md`). Flows where
the user TYPES the message manually (`fill()`/`type()`, ELITEA-2368) or where
the participant was already settled well before the starter click (the
ELITEA-2369 chat-area-tile click, well after page load) have not shown this
race — `force=True` there is probably fine, but prefer plain `.click()` on
`chat-send-button` whenever the composer content was JUST set programmatically.

**Recurrence 2 (ELITEA-2177/2465, 2026-08-16):** same exact shape on the
mid-conversation "add agent via + menu, click a starter tile, click Send"
flow (`/chat/{id}`, not the Agent Hub modal) — `force=True` right after
`click_chat_starter_tile()` deterministically no-opped (composer text
unchanged, no navigation to `/chat/{id}`, still on the pre-send landing view
in the failure screenshot). Plain `.click()` fixed it, same as recurrence 1.
Two independent flows now confirmed — treat "starter tile click then Send"
as the trigger pattern generally, not just the Agent Hub modal's specific
`setTimeout` combo.
