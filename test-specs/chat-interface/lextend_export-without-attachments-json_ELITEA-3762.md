# Test Case: Chat - Export conversation WITHOUT attachments (JSON file) - extension of ELITEA-3784

## Metadata
- **TMS ID**: ELITEA-3762
- **Priority**: l1 (case: high)
- **Status**: extend-existing
- **surface_key**: `chat-export-modal`
- **Environment Explored**: DEV `https://dev.elitea.ai/app` (scripted pytest-playwright probe, headless; `APP_PREFIX=/app` exported - no `.env.test` in sandbox)
- **Covering spec (merged to main)**: `automation/tests/ui/chat/test_chat_export_download.py:36-111` (`TestChatExportDownload.test_export_button_triggers_download`, ELITEA-3784), AFS `l1_export-button-triggers-download_ELITEA-3784.md`.
- **Related (merged)**: ELITEA-3779 (menu contains Export) `test_chat_export_menu_option.py`; ELITEA-3764 (with attachments) `test_chat_export_with_attachments_zip.py`.

## Overlap argument (what is already proven)
3784 already runs case steps 1-9 and 15 of this case against the same modal: open context menu (hover 3-dot; right-click is drift), Export item, `export-chat-modal` with chat name, "Without attachments" checked by default, exact help text "Only chat messages will be exported as a JSON file.", Export button visible+enabled, click -> download, modal closes, toast "Chat exported successfully", file saved and non-empty with `ELITEA-CHAT-ENC/1` header. Its chat is EMPTY, though; this case's distinguishing premise is a chat WITH text messages and no attachments.

## Gap assertions (implementer: extend 3784's spec, e.g. parametrise/second test in same class)
1. **Seed a conversation with text messages** (case says >=5; probe used 2 AI exchanges, enough). Seed via UI: open chat item, `chat.send_message("Reply with just: one")` twice, waiting on a condition (`wait_for_ai_response(initial_count=N)`, N = count BEFORE send), NOT the probe's fixed 9s wait. If cheap, post messages through the API instead is NOT confirmed available (`ConversationAPI` only exposes list/create/delete) - use UI.
2. With messages present and no attachments: `export-chat-modal-option-without` checked, `export-chat-modal-option-with` still disabled (info "This chat has no attachments"); help text unchanged. (Probe confirmed modal text/desc; with-option disabled expected same as 3784, re-assert.)
3. Download for the message-bearing chat: name matches `^<chat name>_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.json(\.enc)?$` (observed `probe_3762_1792646890_2026-10-22_05-28-55.json.enc`), header `ELITEA-CHAT-ENC/1`, `download.failure() is None`.
4. **Messages are included** (only observable proxy): saved size for the message chat (observed 3055 B with 2 exchanges) is strictly greater than the empty-chat export size taken in the same test (export an empty API-created chat first, or compare against a small constant only if measured on that run - prefer the relative comparison). Weak vs. case steps 11-14; say so in a comment.
5. Modal hidden + toast "Chat exported successfully" + no "Failed to export" (same as 3784; keep, do not re-implement if extended in one test).

## Handles Reference
All already declared in `ChatPage` (lines ~1157, 1220-1250, 3702): `export-chat-modal*` testids, `chat-conversation-menu-export-menuitem`, `click_export_and_capture_download`. Seeding reuses existing `send_message`, `wait_for_ai_response`, `get_conversation_item`. No new handles; no ladder rungs needed.

## Coverage Map
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| 1-3 list, context menu, Export, dialog w/ name | dialog opens | 3784 (+ gap 1 seeded chat) | covered; right-click = clarification |
| 4-7 radios, default, help text, buttons | as written | 3784 + gap 2 | covered |
| 8 click Export -> download | immediate | 3784 + gap 3 | covered |
| 9 file name `Conversation_[Name]_YYYY-MM-DD.json` | pattern | gap 3 | **clarification**: DEV = `<name>_<date>_<time>.json.enc` |
| 10-14 open file; JSON valid; messages/timestamps/sender/metadata; order; ISO 8601; no attachments key | content | gap 4 (size proxy only) | **not observable** - DEV export is AES-256-GCM encrypted (`ELITEA-CHAT-ENC/1`); key not available to tests. Content-level asserts out of scope; flag to lead |
| 15 success banner | text | 3784 | covered (green colour not asserted) |
Axis 2: filename starts with chat name; no error toast.

## Findings
- Clarification: right-click (hover 3-dot menu); filename pattern & `.enc`; steps 10-14 unverifiable because export is encrypted - case needs rewriting or a decrypt path (question for lead: is a test decrypt key/utility obtainable?).
- No product defect. Transit: `navigate_to_chat()` + banner dismiss + item click worked in this run (no flake).
- Moderate-value case: extension is thin; acceptable as a second test in the 3784 class.
