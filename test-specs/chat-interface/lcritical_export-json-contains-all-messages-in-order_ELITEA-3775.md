# Test Case: Verify JSON Contains All Messages In Correct Order

## Metadata
- **TMS ID**: ELITEA-3775
- **Linked Story**: EliteaAI/elitea_issues#4590
- **Priority**: critical
- **Environment Explored**: dev (`https://dev.elitea.ai/app`, as deployed), project 575 (`${ELITEA_PROJECT_ID}`)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (analyst slot)
- **Status**: blocked

## Why blocked (live-verified 2026-10-20)
Steps 1-6 work as written (modulo clarifications). **Steps 7-16 cannot be executed or automated: the downloaded
"JSON" is not JSON.** On DEV every chat export is server-side encrypted:
- Download file name `<chat>_<date>_<time>.json.enc` (UI: `useExportConversation` appends `.enc` when response
  content-type is `application/octet-stream`).
- Body begins `ELITEA-CHAT-ENC/1\n{"cipher":"AES-256-GCM","frame_size":1048576,"kdf":"HKDF-SHA256","key_id":"988ba1ed35002dde","salt":"..."}`
  followed by binary ciphertext.
- `GET /api/v2/elitea_core/conversation_export/prompt_lib/{project_id}/{conv_id}?include_attachments=false&file_name=x`
  returns 200 `application/octet-stream`, `Content-Disposition: ...x.json.enc` - `encrypt=false` / `format=json`
  query params are ignored (same output). No key, decrypt endpoint or env var is available to the test suite.
  The kdf/key_id indicate a server-managed key.
So "messages array", count, first/last content, timestamp order, duplicates (case steps 8-16) are unobservable.

## What IS observable / automatable (not what the case asks)
1. Open conv (`/chat/{id}`), hover `chat-conversation-item-{id}`, click scoped `conversation-menu-menu-button`.
2. Menu (7 items on DEV project 575): Rename, Move to, Playback, **Export**, Share externally, Pin on top, Delete.
   Export item: `[data-testid="chat-conversation-menu-export-menuitem"]`.
3. Modal `[data-testid="export-chat-modal"]` (title "Export chat"): `export-chat-modal-chat-name`,
   radio group `export-chat-modal-option` ("Without attachments" default / "With attachments"),
   `export-chat-modal-option-description` ("Only chat messages will be exported as a JSON file."),
   `export-chat-modal-cancel-button`, `export-chat-modal-export-button`. All testids on DEV (rung 1).
4. Click export button inside `page.expect_download()` -> download event; modal closes (count 0).

## Clarifications (case text vs product)
- Case says "Right-click conversation"; live: hover + 3-dot menu (right-click not verified as a trigger).
- Case says "JSON file downloads"; live: encrypted `.json.enc`, not human-readable.
- Case says "Export, then Export in dialog"; matches (menu item Export, then modal Export button).
- Prerequisite of 20 messages needs 20 LLM round trips (~9s each) or seeded data; no API found for injecting messages.

## Unblock options (lead/human decision)
a. Provide a decrypt key / test-only unencrypted export flag (product/backend) -> then parse JSON in test.
b. Redefine the case as a round-trip: export -> Import (`chat-import-button`) -> imported chat has same message
   count/order/first/last (import handles `.enc` server-side). Needs a new case text; not verified live here.
c. Mark manual / un-automatable for content checks.

## Coverage Map
| Case element | Disposition |
|---|---|
| Steps 1-6 (open, count, export via menu+modal, download) | automatable (above) but only as transit |
| Steps 7-16 (JSON content, order, dupes, missing) | blocked - encrypted export |
