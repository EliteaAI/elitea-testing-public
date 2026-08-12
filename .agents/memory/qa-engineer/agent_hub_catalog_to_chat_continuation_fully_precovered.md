---
name: Agent Hub Catalog-to-chat continuation fully pre-covered
description: Catalog modal Start Chat -> ChatPage continuation needs zero new testids; ChatPage already has every handle
type: project
---

Confirmed live (ELITEA-2368, 2026-08-06): after clicking "Start Chat" in the
Catalog agent-preview modal, the ENTIRE chat-side continuation is already
covered by pre-existing `ChatPage` fields/methods — zero new testids, zero
new page-object work, for any future agent-hub case whose steps continue
past "Start Chat" into the chat surface:

- Welcome greeting: `new_conversation_greeting` (`chat-new-conversation-greeting`)
  — "Hello, {user}! What can I do for you today?"
- Composer agent identity: `switch_participant_button`
  (`chat-switch-participant-button`) + `chat_version_selector_trigger`
  (`chat-version-selector-trigger`) — **two separate adjacent elements**,
  not one combined "AgentName vX.X" chip. A dedicated sibling case,
  ELITEA-2362/#870 ("agent chip visible in message input with version and
  settings"), exists specifically to formally document this split — not yet
  analysed as of 2026-08-06. Don't re-discover the split when that case
  comes up; defer detail to it.
- Participants panel: `expand_participants_panel_via_toggle()` +
  `get_participant_row_by_name()` — expanded panel shows an "Agents"
  heading + the row.
- Send flow: `message_input`, `send_button`/`is_send_button_enabled()`,
  `answer_thought_accordion` ("Thought for N secs"), `wait_for_ai_response()`.
- Sidebar grouping: `is_conversation_in_group(conv_id, "today")`.
- Context Budget: **absent entirely pre-send** (no indicator at all, not a
  "0%" state) — appears only once >=1 message is sent. Use
  `wait_for_context_budget_panel()` then `wait_for_context_budget_messages_count()`
  before reading — a one-shot read right after the panel appears can catch
  a stale value (documented race in the method's own docstring).

Cleanup precedent (ELITEA-2075, reused again here): parse `conv_id` from
`page.url` via `re.search(r"/chat/(\d+)", page.url)`, delete via
`ConversationAPI(browser_cookies=_browser_cookies).delete_conversation(conv_id)`
in a `finally` block.

Also: "Business Analyst" (application id 31) independently confirmed to
satisfy the "no starters / no welcome message" precondition too, not just
"User Story Creator" (id 172) — useful when a case's own literal "e.g."
example needs to match without a Test Data substitution note.
