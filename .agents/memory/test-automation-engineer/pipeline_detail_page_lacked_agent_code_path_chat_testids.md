---
name: Pipeline detail page lacked agent-code-path chat testids
description: PipelineDetailPage only had a legacy CSS-based embedded-chat locator; agent-vs-user code-path testids (chat-read-out-button, skill-test-last-response, chat-answer-content, chat-message-delete-button, chat-message-list, chat-message-item) existed on AgentDetailPage but not mirrored here — added for ELITEA-2052.
type: feedback
---

`PipelineDetailPage`'s embedded chat only had `_embedded_chat_messages()` /
`get_embedded_chat_message_count()` — a legacy raw-CSS locator
(`ul.MuiList-root li.MuiListItem-root`), pre-testid-policy tech debt (left
untouched, additive-only). It had no testid-scoped fields for distinguishing
an agent-rendered message from a user-rendered one, even though the pipeline
embedded chat panel shares the exact same `ChatMessageList.jsx`/
`ApplicationAnswer.jsx`/`UserMessage.jsx` FSD components as the agent surface
(`AgentDetailPage`), which already had this pattern from ELITEA-1885.

Added (all pre-existing testids on `main` — no `add-data-testid` work
needed), mirroring `AgentDetailPage` exactly:
- Fields: `chat_message_list`, `chat_message_item`, `chat_read_out_button`,
  `skill_test_last_response`, `chat_answer_content`,
  `chat_message_delete_button`
- Scoped constants: `CHAT_MESSAGE_ITEM_SELECTOR`,
  `CHAT_READ_OUT_BUTTON_SELECTOR`, `SKILL_TEST_LAST_RESPONSE_SELECTOR`,
  `CHAT_ANSWER_CONTENT_SELECTOR`, `CHAT_MESSAGE_DELETE_SELECTOR`
- Methods: `_embedded_chat_message_items_by_testid()`,
  `get_embedded_chat_message_item_count()`,
  `get_last_embedded_chat_message_text()`,
  `get_last_embedded_chat_message_agent_markers()` → returns
  `(has_read_out, has_answer_marker, has_delete_button)`; an
  agent-rendered message is `(True, True, False)`.

Any future pipeline case that needs to assert "this message came from the
agent/pipeline, not the user" (welcome messages, HITL flows, non-AI-generated
seeded messages) can reuse these directly instead of re-deriving the pattern.
