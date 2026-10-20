# Test Case: Chat - Export button triggers download (JSON path)

## Metadata
- **TMS ID**: ELITEA-3784
- **Priority**: l1 (case: critical)
- **Environment Explored**: DEV `https://dev.elitea.ai/app` (headless scripted probe, storage state), project `${ELITEA_PROJECT_ID}` (Private)
- **User set**: `${TEST_USER}`
- **Status**: ready-for-automation
- **surface_key**: `chat-export-modal`
- **Source read**: EliteaUI `ExportConversationModal.jsx`, `useExportConversation.hooks.js`, `ConversationItem.jsx` (origin/main)

## Preconditions
- Logged in. Test creates its own conversation via `ConversationAPI.create_conversation(name)` (empty is enough - the export button works on an empty chat; case asks 5+ messages "for quick download", not needed to prove the trigger). Delete in teardown.
- Playwright context must have `accept_downloads=True` (default in pytest-playwright).
- Dismiss the platform announcement dialog first (`ChatPage.platform_banner_*` / `dismiss` helper) - it intercepts pointer events on DEV.

## Steps (observed live)
1. Open `/chat`; dismiss banner; conversation item `chat-conversation-item-{id}` is in the list. 
2. Open the item's context menu: hover the item, click scoped `conversation-menu-menu-button` (force). **Right-click does NOT open a menu** (0 export items after `button="right"`) - case text "Right-click" is drift; the menu is the hover 3-dot button (existing `ChatPage.open_conversation_context_menu`).
   Menu items observed (7): rename, move-to, playback, export, share-external, pin, delete.
3. Click `chat-conversation-menu-export-menuitem` -> modal `export-chat-modal` opens (title "Export chat", chat name shown in `export-chat-modal-chat-name`).
4. `export-chat-modal-export-button`: visible, enabled, text "Export".
5. Options: `export-chat-modal-option-without` (checked by default) and `export-chat-modal-option-with`. For a chat with NO attachments the "with" option is **disabled** (label "With attachments", info "This chat has no attachments"). Description `export-chat-modal-option-description` = "Only chat messages will be exported as a JSON file."
6. Click Export inside `page.expect_download()` -> download fires.
7. Download filename: `<chat name>_<YYYY-MM-DD>_<HH-MM-SS>.json.enc` (observed `probe_export_3775_2026-10-20_19-40-55.json.enc`). **DEV serves the export encrypted**: content-type octet-stream, file starts `ELITEA-CHAT-ENC/1\n{"cipher":"AES-256-GCM",...}` then ciphertext. Hook appends `.enc` when response is `application/octet-stream`.
9. Modal closes (`export-chat-modal` not visible) after the fetch completes.
10. Success toast text exactly "Chat exported successfully" (hook `toastSuccess`; it is the only toast text on a no-missing-files export; warning variant "Chat exported. N file(s) could not be included.").
11-15. "Browser downloads list / open file / not corrupted": not observable in headless Playwright. Automate as: `download.failure() is None`, file saved via `download.save_as`, size > 0, header line `ELITEA-CHAT-ENC/1` (for `.enc`) - or, if a plain `.json` is served on another env, `json.loads` succeeds. Decrypting content is out of scope (content correctness is ELITEA-3775's concern).

## Handles Reference
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| 1 | `chat-conversation-item-{id}` | - | testid on DEV ✓ (existing `CONVERSATION_ITEM`) |
| 1 | `conversation-menu-menu-button` (scoped in item) | - | testid on DEV ✓ (existing) |
| 1 | `chat-conversation-menu-export-menuitem` | - | testid on DEV ✓ (key `export`; check `CONVERSATION_MENU_ITEM_KEYS` includes it) |
| 1 | `export-chat-modal` | - | testid on DEV ✓ |
| 1 | `export-chat-modal-chat-name` | - | testid on DEV ✓ |
| 1 | `export-chat-modal-option-without` / `-with` | - | testid on DEV ✓ (wrapper; the radio `input` is inside) |
| 1 | `export-chat-modal-option-description` | - | testid on DEV ✓ |
| 1 | `export-chat-modal-export-button` | - | testid on DEV ✓ |
| 1 | `export-chat-modal-cancel-button` | - | testid on DEV ✓ |
| 1 | `export-chat-modal-progress` | - | in source (ZIP only, transient); NOT observed live |
| 1 | `export-chat-modal-browser-download-note` / `-large-warning` | - | in source; not observed |
| ladder | toast "Chat exported successfully" | `chat-export-success-toast` | ladder - `get_by_text` exact; no testid observed (probe matched `[role=alert]`-ish container); implementer: verify rung/uniqueness |

## Coverage Map
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| Step 1 chat list | list shown | conversation item visible | covered |
| Step 2 right-click | context menu with Export | hover + 3-dot menu | **clarification** (right-click opens nothing) |
| Step 3-4 | dialog opens; Export btn visible+enabled | modal + button asserts | covered |
| Step 5-6 | select option, click Export, download | default "Without" (assert checked), expect_download | covered (JSON) |
| Step 7 JSON immediate | download | expect_download resolves | covered |
| Step 8 ZIP progress "Exporting chat... N files" | progress shown | none | **out-of-scope / not verified**: needs a chat with attachments; progress bar is transient during fetch. See Blocked/Open |
| Step 9 | dialog closes | modal hidden | covered |
| Step 10 | green "Chat exported successfully" | toast text assert | covered (text; colour not asserted) |
| Step 11-12 | in downloads list, completes | `download.failure() is None`, saved file | covered (equivalent) |
| Step 13-15 | accessible, not corrupt | size>0 + ENC header | covered, weaker than "open" (encrypted) |
Axis 2 (extra): modal closed AND no error toast ("Failed to export chat") - guards silent failure.

## Open items / findings
- **Clarification (case drift)**: step 2 right-click; step 7 says JSON, DEV delivers `.json.enc` (encrypted); steps 14-15 cannot open the file as written.
- **ZIP/attachments branch unverified**: With-attachments requires a chat that has an attachment (uploaded file); not set up in this pass. Implementer may add as a second parametrisation only if an attachment can be seeded cheaply via API (`upload_file`); otherwise leave ZIP step to a follow-up. Assert only what is observed; do not assert progress text without seeing it.
- Right-click-based discovery wasted nothing; no product defect found. Console not instrumented in headless probe.

## Automation Hints
- Reuse `ChatPage.open_conversation_context_menu` + `click_conversation_menu_item("export")` (add `"export"` to key tuple if absent), new class-level descriptors for modal parts on ChatPage.
- Fixture: `conversation_api` create/delete. Use `with page.expect_download() as d:` around the Export click; assert toast/modal-hidden after.
- No sleeps; wait for `export-chat-modal` hidden.
