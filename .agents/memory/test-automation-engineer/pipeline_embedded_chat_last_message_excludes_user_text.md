---
name: Pipeline embedded chat last-message getter excludes user text
description: PipelineDetailPage.get_embedded_chat_last_message() reads only the AI answer body — use find_message_containing() to check for a specific sent message
type: project
---

`PipelineDetailPage.get_embedded_chat_last_message()` returns only the AI
response body text (it explicitly extracts from the answer container /
`<p>` tags, skipping the user's own message). Asserting
`assert my_sent_text in get_embedded_chat_last_message()` fails unless the
AI happens to echo your text back — confirmed live (ELITEA-2011): the AI's
reply to `"second-run-<hex>"` was a generic clarifying question, containing
none of the literal sent text.

To confirm a specific message you just sent is present in the chat (e.g.
proving the CURRENT/active conversation is the one you expect, distinct
from a cleared one), use `find_message_containing(text)` instead — it
searches ALL message items (user bubble + AI response) via the same
`_embedded_chat_messages()` locator `get_embedded_chat_message_count()`
uses, so the literal user-typed text is found in its own bubble regardless
of what the AI replies with.

Same distinction exists on `AgentDetailPage` (`get_last_chat_message_full_text()`
vs `find_message_containing()`) — check which one a sibling test actually
relies on before assuming "last message" includes the echo; it usually
doesn't.
