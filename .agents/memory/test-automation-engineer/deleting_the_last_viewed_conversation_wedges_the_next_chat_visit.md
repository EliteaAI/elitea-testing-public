---
name: Deleting the last-viewed conversation wedges the next /chat visit
description: A chat spec whose teardown deletes the conversation it just viewed leaves the SPA restoring a dead id — the pane spins forever and its overlay intercepts the model-selector click
type: feedback
aliases: [chat pane spinner, model-selector click intercepted, last-viewed conversation restore, open_blank_composer]
tags: [area/chat, type/gotcha]
created: 2026-08-30
updated: 2026-08-30
---

## Symptom

`Locator.click: Timeout 10000ms exceeded … waiting for get_by_test_id("model-selector-name")`
with `<div class="MuiBox-root css-15msj7j">… intercepts pointer events`, on a spec that
only navigates to `/chat` and picks a model. Deterministic — it does NOT clear on rerun.
Screenshot shows the chat pane holding a spinner while the sidebar renders fine.

## Mechanism

The SPA restores the **last-viewed conversation** on a bare `/chat` visit
(`ChatPage.navigate_to_chat()` documents the redirect). A spec that creates a
conversation and **deletes it in teardown** leaves that pointer aimed at a dead id: the
restore never resolves, and its loading overlay covers the composer area — so every
click in the pane is intercepted, in THIS spec and in any later one that lands on `/chat`
the same way. Verified on ELITEA-2416 (settings-w11): 4 consecutive failures at the same
click, including a **pristine-HEAD control run**, i.e. it is environment state, not a diff.

## Fix

`utils/blank_conversation.open_blank_composer(chat)` immediately after
`navigate_to_chat()` — it clicks +Chat and verifies the blank state HOLDS, which escapes
the dead restore. Two independent reasons to do it on any spec that sends a message:

1. It un-wedges the restore.
2. Without it the send appends to a PRE-EXISTING conversation — and a teardown that then
   deletes "the conversation" destroys one the test never created.

Then send with `send_message(..., use_enter=True)`: in the fresh-chat view an overlay
intercepts `chat-send-button` (same reason the personalization / context-settings specs
use Enter).

Related: [[a_teardown_id_read_after_the_assertions_is_not_a_guard]]
