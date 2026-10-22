# Test Case: Chat - exported JSON contains all messages in correct order (ELITEA-3775)

## Metadata
- **TMS ID**: ELITEA-3775
- **Priority**: l1 (case: critical)
- **Status**: ready-for-automation (REDUCED observable - see Clarification)
- **surface_key**: `chat-export-modal`
- **Environment Explored**: DEV `https://dev.elitea.ai/app` (scripted pytest-playwright + requests probes, headless, `APP_PREFIX=/app`; Playwright MCP chrome missing on host)
- **Neighbours read**: ELITEA-3784 (`automation/tests/ui/chat/test_chat_export_download.py`), 3762, 3764, 3779 AFS. Not coverage: none seeds a message-bearing chat and compares counts/order.

## Clarification (case-text drift, no product defect)
Steps 7-16 (open JSON, count, first/last, middle, timestamps, order, duplicates) are NOT observable: DEV export is AES-256-GCM encrypted (`ELITEA-CHAT-ENC/1` header, `.json.enc`; source `useExportConversation.hooks.js`: `application/octet-stream` => `.enc`). Also right-click opens nothing (hover 3-dot menu), filename is `<name>_<date>_<time>.json.enc`. Question for lead: is a test decrypt key/utility obtainable? Without it this case is automated as: UI count == API message list == export summary count, order verified on the API/UI list, export download valid and larger than an empty export.

## Steps to automate (observed live)
Seeding: DEV has NO message-posting API in `ConversationAPI`; seed through UI. 20 messages = 10 AI exchanges (~10-15s each); probe used 2 exchanges (4 messages). Implementer choice: N exchanges (declared deviation from 20 if runtime too long; >=5 exchanges = 10 messages recommended).
1. API-create chat (`conversation_api.create_conversation`), `page.goto(<url>/app/chat)` (+ `dismiss_platform_banner_dialog`), click `get_conversation_item(cid)`.
2. Send N prompts **with `use_enter=True`** (`chat.send_message(text, use_enter=True)`; the send-button click was intercepted by `platform-banner-corner` / sent nothing in probe) and `wait_for_ai_response(initial_count=n_before)`. Observed after 2 exchanges: `get_message_count()==4`, API `message_groups_count==4`.
3. Record UI count, first and last message text (`chat-message-item`, first = user prompt 1, last = AI reply N).
4. Order/duplicates: `GET /elitea_core/conversation/prompt_lib/{P}/{cid}` -> `message_groups[]` (keys `id, created_at, author_participant_id, message_items[{item_type:"text_message", item_details.content}]`): assert `created_at` ascending, ids unique, first group content == first prompt, count == UI count.
5. `GET /elitea_core/conversation_export/prompt_lib/{P}/{cid}?summary=true` -> `{"messages_count": 4, "attachments_count": 0, "total_size": null}`; assert `messages_count == UI count` (this is the server's own count of what the export contains).
6. Open context menu -> Export -> modal (3784 flow); click Export; download name matches `^<name>_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.json(\.enc)?$`, header `ELITEA-CHAT-ENC/1` (or valid JSON if not encrypted: then assert `messages` len/order directly - keep branch), toast "Chat exported successfully". Weak proxy: size greater than empty-chat export (3762 AFS gap 4).
7. Cleanup: delete the conversation in `finally`.

## Handles Reference
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| 1 | `chat-conversation-item-{id}` (`get_conversation_item`) | - | testid on DEV ✓ (probe: `chat-conversation-item-1291`) |
| 1 | `chat-message-item`, `chat-message-list`, `chat-message-input` | - | testid on DEV ✓ |
| 1 | `chat-conversation-menu-export-menuitem`, `export-chat-modal*` | - | testid on DEV ✓ (3784) |
| - | all already declared in `ChatPage`; no new handles | | |

## Coverage Map
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| Pre: 20 msgs | chat with messages | Steps 1-2 (N exchanges) | covered; count deviation declared |
| 1-4 open, count, first, last | recorded | Steps 2-3 | covered |
| 5-6 menu, Export, download | JSON downloads | Step 6 | covered; right-click = clarification; `.json.enc` |
| 7-8 open file, messages array | JSON visible | - | **not observable** (encrypted) |
| 9-12 count/first/last/middle in JSON | match | Steps 4-5 (API + summary proxy) | proxy only |
| 13-14 timestamps ascending | ordered | Step 4 on API list | proxy for the export |
| 15-16 no dup / none missing | unique, complete | Step 4-5 | proxy |
Axis 2: export summary count (server-side truth); export file larger than empty export.

## Findings
- Chat on a fresh API-created conversation with Send-button click sent nothing in probe (banner overlay); Enter works.
- `navigate_to_chat()`+`wait_for_page_load()` timed out again on blank-chat landing (same as in `_surface.md`); `page.goto` works. Transit flake, not a regression signal.
- No product defect.
