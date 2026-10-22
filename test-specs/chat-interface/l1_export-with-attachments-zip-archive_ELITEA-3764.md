# Test Case: Chat - Export with attachments produces a ZIP archive

## Metadata
- **TMS ID**: ELITEA-3764
- **Priority**: l1 (case: high)
- **Environment Explored**: DEV `https://dev.elitea.ai/app` (scripted pytest-playwright probe, headless, storage state; run with `APP_PREFIX=/app` exported - see Findings)
- **User set**: `${TEST_USER}`
- **Status**: ready-for-automation
- **surface_key**: `chat-export-modal`
- **Sibling (merged to main)**: ELITEA-3784 `automation/tests/ui/chat/test_chat_export_download.py` (JSON path; explicitly left the ZIP/progress branch uncovered). Not `already-covered`/`extend-existing`: different branch, different expected result. Implementer: add a second test in the same class/file reusing its page-object fields.

## Preconditions (seed via API/UI, observed working)
- `conversation_api.create_conversation(name)`; delete in `finally`.
- Open the chat in UI: `chat.navigate_to_chat()`; `dismiss_platform_banner_dialog()`; click `get_conversation_item(cid)` (do NOT `page.goto(/chat/<id>)` bare - 404; do NOT `navigate_to_chat(conversation_id=...)` - timed out, see Findings).
- Attach 3 tiny files in ONE chooser action: `chat.attach_files_via_menu([txt, csv, md])` (tmp_path files, e.g. `note_alpha.txt`, `data_beta.csv`, `doc_gamma.md`). 3 chips rendered (`get_attachment_chip_count()==3`).
- `chat.send_message("Reply with just OK")`, wait ~ for send to complete (attachments are bound to the sent message; export summary then reported 3 files). Wait on a condition (message item / assistant reply), not a sleep. Probe used a fixed wait; implementer must replace with a real wait.
- Then return to list and open the export modal.

## Steps (observed live)
1. Chat list: `chat-conversation-item-{id}` visible.
2. Context menu = hover + scoped `conversation-menu-menu-button` (right-click: case-text drift, see ELITEA-3784 AFS). `click_conversation_menu_item("export")`.
3. `export-chat-modal` opens; title "Export chat"; `export-chat-modal-chat-name` = chat name.
4. "With attachments" option label observed: **`With attachments (3 files · 36 Bytes)`** (size formatted by `formatFileSize`; case says "X.XX MB" - drift because files are tiny; assert regex `With attachments \(3 files · .+\)`).
5. Click the radio inside `export-chat-modal-option-with` (`export-chat-modal-option-radio` scoped, `force=True`) -> `is_checked()` True.
6. `export-chat-modal-option-description` text exactly: "Chat messages and all attached and generated files/images will be exported as a ZIP archive."
7. Click `export-chat-modal-export-button` inside `expect_download`. A MutationObserver (installed before click) caught modal text: "Exporting chat... 3 files" with `export-chat-modal-progress` present, and Export button text "Exporting...". Progress is transient; to assert it reliably install the observer (or poll) BEFORE the click, as probe did; alternatively delay is short for tiny files (download still resolved within the 60s window). Treat step 7-8 as asserted via observer capture; assert text AND progress element existed.
8. Download filename: **`<chat name>_<YYYY-MM-DD>_<HH-MM-SS>.zip.enc`** (observed `probe_3764_1792544547_2026-10-21_01-03-17.zip.enc`). Case says `Conversation_[Name]_YYYY-MM-DD.zip` - drift (name pattern + encrypted `.enc` suffix on DEV). Regex: `^(?P<name>.+)_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.zip(\.enc)?$`.
9. **Content is encrypted**: file begins `ELITEA-CHAT-ENC/1\n{"cipher":"AES-256-GCM","frame_size":...` (size 1513 B). It cannot be unzipped in a test, so case steps 11-15 (extract, JSON + attachments folder, original names, JSON references) are **not observable**. Automate as: `download.failure() is None`, saved, size > 0, `.zip` in name, header `ELITEA-CHAT-ENC/1`; if an env serves plain `.zip`, branch: `zipfile.is_zipfile` and assert one `.json` + attachments folder entries containing the 3 original filenames (conditional, only if observed on that env; not observed on DEV).
10. Modal closed (`export-chat-modal` hidden) after fetch; toast "Chat exported successfully" (`toast_message` text), no "Failed to export".

## Handles Reference
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| 1 | `export-chat-modal`, `-chat-name`, `-option-with`, `-option-description`, `-export-button` | - | testid on DEV ✓, already declared in ChatPage (lines ~1223-1248) |
| 1 | `export-chat-modal-progress` | - | testid on DEV ✓ (observed in DOM during export, transient) - NOT yet a ChatPage field; add class-level `LocatorDescriptor(testid=...)` |
| 1 | progress text (inside `export-chat-modal`) | - | assert via `export_chat_modal` `to_contain_text("Exporting chat... 3 files")` |
| 1 | `chat-attach-menuitem-button` via `attach_files_via_menu` | - | testid on DEV ✓ existing |
| 1 | `chat-attachment-chip-*` | - | existing `get_attachment_chip_count` |
| ladder | toast "Chat exported successfully" | `chat-export-success-toast` | existing `chat.toast_message` filter has_text (as in 3784) |

## Coverage Map
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| 1-3 list, context menu, Export | dialog opens | menu helpers + modal visible | covered (right-click = clarification) |
| 4 option label | "(3 files · X.XX MB)" | regex on label | covered, size text drift (Bytes) |
| 5 select radio | selected | `is_checked` | covered |
| 6 help text | exact string | text assert | covered |
| 7-8 progress "Exporting chat... 3 files" + bar | shown | observer capture, progress testid | covered (transient; see above) |
| 9-10 ZIP download, name | `Conversation_[Name]_date.zip` | regex on actual pattern `.zip(.enc)` | covered, **clarification**: name pattern differs |
| 11-15 extract / contents / names / JSON refs | files intact | header+size only | **not observable on DEV (encrypted)** - disposition: clarification / out-of-scope; no assert invented |
| 16 success banner | text | toast assert | covered |
Axis 2: modal closes; no error toast; filename starts with chat name.

## Findings
- Clarification: right-click (use hover 3-dot); name pattern `<name>_<date>_<time>.zip.enc`; archive encrypted so contents unverifiable; label size is "36 Bytes" for tiny files.
- No product defect found.
- Env note for implementer/lead: this sandbox had no `automation/.env.test`; `APP_PREFIX` unset -> app_base_url `https://dev.elitea.ai` -> every page 404 (even existing ELITEA-3784 test failed). `export APP_PREFIX=/app` fixed it. Probably an environment gap, not a regression.
- Transit flag: `ChatPage.navigate_to_chat(conversation_id=...)` timed out again (2 attempts incl. 404 root cause above - may be the same APP_PREFIX issue).
