# Test Case: Chat - only conversation creator sees/uses Export (ELITEA-3786)

## Metadata
- **TMS ID**: ELITEA-3786
- **Priority**: l2 (case: high)
- **Status**: blocked
- **surface_key**: `chat-export-modal`
- **Environment Explored**: DEV (scripted probes) + EliteaUI source on `origin/main` (read-only)

## Blocked Steps
1. **User B credentials do not exist in the analysis environment** (`TEST_USER_B_EMAIL/PASSWORD` unset; `auth_state_user_b` fixture skips). Steps 8-15 (User B) could not be run live. Unblock: provide User B creds in `.env.test` and a conversation that B can open (public chat in a shared project, since a private chat is invisible to B).
2. **Premise contradicts product code.** `ConversationItem.jsx` (origin/main) menuItems: `chat-conversation-menu-export` has NO author gating (`disabled: isActive && isEditingCanvas` only). Author gating exists only on Rename/Delete (`disabled: userId != author_id`), Restrict access and Share externally (`display: 'none'` when `userId != author_id`). So by source, a non-creator who can open the chat SEES and can use Export. Case expectation (step 12 "Export NOT present") would fail => probable product defect (or case-text/intent gap) - needs a decision.
3. **Live API evidence (non-creator export works):** as user 940, `GET /elitea_core/conversation_export/prompt_lib/470/385` (chat authored by user 39, `is_private: true`) -> 200 `application/octet-stream` `ELITEA-CHAT-ENC/1`, summary 200. So the backend does not enforce creator-only export either (caveat: 940 may be project admin; unverified role). Not filed: UI path for B unrun, "has access" semantics unclear - lead to decide (candidate bug: "Export available to non-creator").

## Part automatable once unblocked
- Creator (User A) steps 1-7: identical to ELITEA-3784/3779 flow (already covered by `test_chat_export_menu_option.py` / `test_chat_export_download.py` for the creator); 3786's distinct value is only the User B negative assertion (menu items for B: `get_conversation_menu_item("export")` count 0), which currently would be RED against DEV by code reading.

## Coverage Map
| Case element | Disposition |
|---|---|
| 1-7 creator sees Export, exports | covered by existing 3779/3784 specs (creator part) |
| 8-15 User B negative | **blocked** (no creds) + probable defect (source + API evidence above) |
