---
name: Embedded-chat "agent responded" oracle passes on the loading placeholder
description: get_last_chat_response_text() + wait_for_chat_response() cannot prove an agent answered — both are satisfied by the "Waking the agent…" placeholder
type: feedback
aliases: [get_last_chat_response_text, wait_for_chat_response, skill-test-last-response, agent responded assertion, inert assertion embedded chat]
tags: [area/chat, type/inert-assertion]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

The common embedded-chat "the agent responded" shape

```python
detail_page.wait_for_chat_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
assert detail_page.get_chat_message_count() > initial_count
assert detail_page.get_last_chat_response_text() != ""
```

**proves nothing about the agent answering.** Two independent holes:

1. `AgentDetailPage.wait_for_chat_response()` swallows its own timeout — it logs
   `WARNING … Embedded chat response did not stabilize within timeout`
   (`pages/agent_detail_page.py:3145`) and RETURNS. It never raises.
2. `get_last_chat_response_text()` reads `skill-test-last-response` **only if it
   exists**, otherwise falls through to `get_last_chat_message()`, which returns
   the last message item's RAW `text_content()`.

Measured live (2026-08-27, localhost, ELITEA-1886 probe) at t≈0 after Send:
`count == 2`, `skill_test_last_response.count() == 0`, and the oracle returned
`'elitea-1886-probeb-…toMessageless than a minute agoWaking\xa0the\xa0agent…'`
— the answer placeholder's header + rotating loading phrase. So
`response_text != ""` is **True before any answer exists**, and the count is
already 2 because the placeholder item renders alongside the user's message.

Net effect: a run where the send registers but the agent never answers (or
errors) goes **GREEN**. Only a send that never fires at all turns it red.

## Assert instead

- `detail_page.skill_test_last_response.first.wait_for(state="visible", timeout=…)`
  then assert its stripped text is non-empty — that testid is set by
  `ApplicationAnswer.jsx` only on a real ANSWER (`isLastMessage ? 'skill-test-last-response' : 'chat-answer-content'`).
- Assert the USER message carries the exact text that was sent, not just a count delta.
- Wrap the Send click in `page.expect_response(...)` on
  `POST .../conversations/prompt_lib/{project}` → 201, so a click that no-ops
  fails in seconds with a precise reason instead of a vacuous count assertion
  60 s later.

Related: [[chat_send_button_force_click_race]] (the failure this masked on DEV)
