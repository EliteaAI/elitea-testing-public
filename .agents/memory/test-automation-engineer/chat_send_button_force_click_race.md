---
name: Chat send-button force-click race after fast composer population
description: chat-send-button force=True click can silently no-op right after a starter/programmatic setValue() populates the composer — use a plain (non-force) click there
type: feedback
updated: 2026-08-27
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

**Recurrence 3 (ELITEA-1886 / issue #1812, 2026-08-27) — the first one that
reached CI red, and the first with a DEV-only signature.** Third distinct flow:
the **agent-detail embedded chat** (`/agents/all/{id}`), where `ChatBox.jsx`'s
`onSendConversationStarter` populates the composer through an imperative ref
(`chatInput.current.setValue(starter)` → `UserInput.jsx`). Two things this
occurrence adds that recurrences 1-2 did not show:

- **A local gate structurally cannot catch this class.** The spec was 5/5 green
  on localhost — the button settles in ~2 ms there, so the race window does not
  exist — and failed only on `dev.elitea.ai` (GHA run 32931571484) with
  `assert 0 > 0` after burning the full 60 s AI timeout. Count ZERO means not
  even the user's own message landed. **Never report a local green as evidence
  that a fix in this class works**; it proves non-regression only. The
  corollary: a `force=True` send that passes locally today is not safe, it is
  merely untested against the environment where the window is wide.
- **Wrap the Send click in its own response oracle**, not just a plain click:
  ```python
  expect(page_obj.chat_send_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)
  with page.expect_response(_is_send_response, timeout=SAVE_RESPONSE_TIMEOUT):
      page_obj.chat_send_button.click()
  ```
  A silent no-op then fails in ~15 s **naming the POST that never fired**,
  instead of vacuously burning 60 s and reporting a meaningless message-count
  assertion. This diagnostic half is worth more than the click change itself
  when the next recurrence appears — it converts an unreadable timeout into a
  statement of what the app did not do.

Canon card **#1849** now proposes making the non-force Send the written rule,
plus a reviewer grep and a sweep — 5 other specs and `pages/chat_page.py:1891`
still force-click a send button.

Related: [[embedded_chat_response_oracle_is_inert]] — same case, same Step 8. A
silent no-op send *plus* an inert response oracle is how a fully broken step
still reported green locally.
