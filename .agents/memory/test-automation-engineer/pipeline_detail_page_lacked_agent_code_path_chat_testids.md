---
name: Pipeline detail page lacked agent-code-path chat testids
description: PipelineDetailPage only had a legacy CSS-based embedded-chat locator; agent-vs-user code-path testids existed on AgentDetailPage but not mirrored here — added for ELITEA-2052. Mirror the CONSTANTS, not every AgentDetailPage field verbatim.
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
needed):
- Fields (only the two `self.<field>` is actually called on directly):
  `chat_message_list`, `skill_test_last_response`
- Scoped constants (used only as `some_locator.locator(self.X_SELECTOR)` —
  never as a bare field): `CHAT_MESSAGE_ITEM_SELECTOR`,
  `CHAT_READ_OUT_BUTTON_SELECTOR`, `SKILL_TEST_LAST_RESPONSE_SELECTOR`,
  `CHAT_ANSWER_CONTENT_SELECTOR`, `CHAT_MESSAGE_DELETE_SELECTOR`
- Methods: `_embedded_chat_message_items_by_testid()`,
  `get_embedded_chat_message_item_count()`,
  `get_last_embedded_chat_message_text()`,
  `get_last_embedded_chat_message_agent_markers()` → returns
  `(has_read_out, has_answer_marker, has_delete_button)`; an
  agent-rendered message is `(True, True, False)`.

**Fix-round correction (round 1, review):** the first pass over-mirrored
`AgentDetailPage` by ALSO declaring `chat_message_item`, `chat_read_out_button`,
`chat_answer_content`, `chat_message_delete_button` as `LocatorDescriptor`
class fields even though the test's executed path only ever consumes those
three testids through the scoped `.locator(self.X_SELECTOR)` string-constant
form (chained off `chat_message_list`/`last_item`), never as a bare
`self.chat_read_out_button` field access. That made four fields dead —
declared, never referenced — which is exactly the locator-policy scope
violation (`.agents/role-overrides.md`: no carve-out for "mirrors a sibling
page object" or "plausible future use"). Removed the four dead fields;
kept the two that ARE directly referenced (`chat_message_list`,
`skill_test_last_response`) plus all five UPPER_CASE selector constants
(still referenced via `.locator()`, including one absence assertion —
`CHAT_MESSAGE_DELETE_SELECTOR` — which counts as a reference per canon
ruling #511's extension).

**Lesson for next mirror-a-sibling-page-object case:** mirroring
`AgentDetailPage`'s PATTERN (constants + methods) is fine; mirroring its
FIELD LIST verbatim is not — check which fields the new test's methods
actually call as `self.<field>` vs which testids only ever appear inside a
`.locator(self.CONSTANT)` chain, and only declare `LocatorDescriptor` fields
for the former.

Any future pipeline case that needs to assert "this message came from the
agent/pipeline, not the user" (welcome messages, HITL flows, non-AI-generated
seeded messages) can reuse these directly instead of re-deriving the pattern.
