---
name: SkillTestPanel does not create a Chat conversation — three-way ground truth
description: ELITEA-2441 confirmed the Skill test panel never touches elitea_core/conversations*; also flags leftover ELITEA2459RenameTest/ABC Chat folders that can be mistaken for conversations in a naive count.
type: feedback
---

## The finding (ELITEA-2441, 2026-08-12)

Running a prompt through a Skill's `SkillTestPanel` does **not** create a
Chat conversation. Confirmed three independent ways in one run (project
`Private`/399):

1. **Network capture** (`browser_network_requests`) across the entire
   create-skill + send-test-message + wait-for-response flow: **zero**
   requests to any `elitea_core/conversations*` endpoint. The only
   "conversation"-shaped traffic was the unrelated Support Assistant
   widget's `support_assistant/conversations/` — don't confuse the two;
   they're separate features hitting separate endpoint families.
2. **API ground truth**: `ConversationAPI.list_conversations()`
   (`{"total": int, "rows": [...]}`, fixture `conversation_api` in
   `automation/fixtures/api_fixtures.py:115`) stayed at `total: 1`, same
   conversation `id` (`7929`), before and after.
3. **DOM ground truth**: Chat sidebar's `[data-testid^="chat-conversation-
   item-"]` count (`ChatPage.CONVERSATION_ITEM_PREFIX`) stayed at `1`.

The network-capture check is the strongest of the three — it proves
absence-of-cause, not just absence-of-symptom (a before/after count alone
can't distinguish "never created" from "created then auto-deleted within
the same flow").

## Gotcha — leftover folders can masquerade as conversations in a naive count

The live Chat sidebar (project 399) carries roughly a dozen duplicate
`ELITEA2459RenameTest`/`ABC` **folder** entries — apparent leftover test
data from a prior ELITEA-2459 rename-flow run that didn't clean up. In a
Playwright MCP accessibility snapshot these render as `heading > button`
pairs and look, at a glance, like a much bigger conversation list (~2
dozen buttons) than the real conversation count.

**They are folders, not conversations.** `document.querySelectorAll(
'[data-testid^="chat-conversation-item-"]').length` correctly returns just
the real conversation count (`1`), unaffected by the folder clutter.
`ChatPage.get_conversation_list_items()` — the pre-testid-policy `:has(h6)
> button` CSS selector the same file flags as tracked tech debt — would
very likely miscount here too, since folder headers are also `<button>`
siblings of `<h6>`-shaped containers. **Always scope a conversation-count
assertion to `CONVERSATION_ITEM_PREFIX`/`CONVERSATION_ITEM`, never a raw
structural or bare visual count**, on this project.

Not filed as a product defect — no reproducible trigger was observed this
run (just residue from an earlier session), and it's out of ELITEA-2441's
own scope. Whoever next works ELITEA-2459 or any Chat-folder case should
decide whether to file/clean it up from a position of actually reproducing
the leak.

Full AFS: `test-specs/skills/l3_test-panel-does-not-create-new-chat-conversation_ELITEA-2441.md`.
Surface digest: `test-specs/skills/_surface.md`.
