---
name: API-created zero-message conversation gets orphaned on first UI send
description: Seeding a conversation via ConversationAPI.create_conversation() then messaging it via the UI does NOT append to that conversation — a brand-new one is silently created instead, leaving the API-created one permanently empty. Confirmed product defect #691. Seed via +Chat instead.
type: feedback
---

## What happens

`ConversationAPI(project_id=...).create_conversation(name)` creates a
conversation server-side with zero messages. Opening it in the UI (either
direct `/chat/{id}` navigation OR clicking it in the sidebar list — both
reproduce identically) and sending the FIRST message does not append to
that conversation. Instead, a BRAND-NEW conversation is created (auto-titled
from the message text), and the original API-created conversation is left
behind, permanently empty (`message_groups_count: 0`), still showing its
original given name in the sidebar.

Confirmed via a direct API query after repro: the original conversation
stayed at 0 messages; a new, higher-id conversation appeared holding the
actual sent message + AI reply.

## Root cause (read from EliteaUI source)

`src/[fsd]/features/chat/ui/chat-box/ChatBox.jsx`'s `onPredictStream()`
gates the "create new conversation" decision purely on
`activeConversation?.uuid` being falsy (~lines 843, 896:
`needsConversationCreation: !activeConversation?.uuid && isAgentsPage`,
`isNewConversationCreated = sendResult?.createdConversation &&
!activeConversation?.uuid`). For a freshly-loaded, zero-message
conversation, `activeConversation.uuid` does not appear to get hydrated
before the first Send fires, so the send flow treats it as "no conversation
yet" and creates one. A conversation that already has ≥1 message does not
exhibit this — sending follow-ups to an existing, previously-messaged
conversation (e.g. a long-lived fixture like "HI Chat") works correctly.

## The fix (test technique, not a product fix)

Do NOT seed via `ConversationAPI.create_conversation()` when the UI needs to
send the first message. Seed via the UI's own `+Chat` button instead
(`ChatPage.click_create_conversation()`), matching the pattern already
proven in `test_create_conversation_via_ui_button` /
`test_context_budget_reflects_profile_max_tokens`: click +Chat, send the
message, THEN extract the resulting conversation id from the URL
(`re.search(r"/chat/(\d+)", page.url)`) — the id is assigned by this flow,
not chosen in advance.

## Filed as

EliteaAI/elitea-testing-public#691 (ELITEA-2095, PR #693).

## When this applies

Any future case whose Test Data section says "create a conversation via the
API, then send the first message via the UI" — that instruction is broken
by this defect. Seed via +Chat instead, or seed via API but never send the
FIRST message via UI to a conversation you created via bare API create
(only OK if the API itself later gets a message-injection endpoint, or if
you only ever send FOLLOW-UP messages to an already-messaged conversation).
