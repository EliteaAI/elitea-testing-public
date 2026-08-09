---
name: Embedded-chat .last right after Send can read the AI placeholder, not the sent message
description: After send_message_in_embedded_chat + wait_for_embedded_chat_message_count(n+1), .last can already be the AI "Waking the agent…" placeholder, not the user's own message — read a FIXED index instead
type: feedback
---

## What happened (ELITEA-2059, implementer fix-round-1, 2026-08-09)

Needed to assert the just-sent USER message bubble shows the typed text +
an attachment card (AFS Coverage-Map row 6). First attempt read
`pipeline_page._embedded_chat_messages().last` right after
`wait_for_embedded_chat_message_count(initial_count + 1)` returned. This
intermittently — but not always — read the AI's transient "Waking the
agent…" placeholder text instead of the user's own sent message: by the
time the assertion ran, BOTH the user message AND the AI placeholder had
already rendered, so `.last` pointed at the placeholder, one position past
where the user's own message actually landed (`initial_count`).

`wait_for_embedded_chat_message_count(minimum)` only guarantees the count
reached `minimum` — it says nothing about which position holds which
message once the AI's placeholder starts appearing near-simultaneously
with the user's own message being accepted.

## Fix

Read the message at the FIXED index (`initial_count`), never `.last`, for
anything you need to assert about the message the code you just called
was supposed to produce — same idiom `ChatPage.get_message_text_at(index)`
already documents (ELITEA-2369) for exactly this race on the general Chat
page. Added `PipelineDetailPage.get_embedded_chat_message_full_text_at(index)`
/ `get_embedded_chat_message_attachment_names_at(index)` mirroring it for
the pipeline's embedded chat.

## Related but distinct

`embedded_chat_progressive_growth_needs_transient_placeholder_filter.md`
covers a DIFFERENT race on the same surface: a growth-check sampling
`.last`'s TEXT twice and being fooled by a placeholder swap (short
placeholder -> longer placeholder) mid-poll. This one is about `.last`
pointing at the WRONG MESSAGE ENTIRELY (the placeholder's own `<li>`) right
after send, before any response wait even starts. Same root cause family
(the AI placeholder appears fast and unpredictably), different failure
shape — one is "wrong text same slot", this one is "wrong slot".
