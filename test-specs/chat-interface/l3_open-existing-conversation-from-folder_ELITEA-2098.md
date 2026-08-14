# Test Case: Open Existing Conversation from a Folder

## Metadata
- **TMS ID**: ELITEA-2098
- **Linked Story**: none
- **Priority**: l3 (medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend). Dev server confirmed running
  (`curl` 200).
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips
  login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot (cluster dispatch alongside
  ELITEA-2096/ELITEA-2097, one live session)
- **Status**: **ready-for-automation** — case executed end-to-end live
  against the Private project (399). All 8 steps reproduced, zero
  defects, zero new testids needed (all handles already on `main`, see §
  Concrete Handles). Unlike ELITEA-2096/2097 (blocked — see the sibling
  AFS), a folder's conversations do NOT need to be dated in the past —
  the folder assignment itself (`folder_id`) is instantaneous and fully
  settable via the API, so this case has no environmental blocker.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / localhost
  `auth_state`).
- At least one folder exists with 2+ conversations inside it (seeded via
  API in setup — see § Test Data).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)

Seeded live this session via direct API calls (Bearer token,
`ConversationAPI`-equivalent endpoints) against project 399 (Private):

1. `POST /elitea_core/folder/prompt_lib/399` `{"name": "autotest_2098_folder_<ts>"}`
   → folder id (confirmed live: `180`, cleaned up after)
2. `POST /elitea_core/conversations/prompt_lib/399` ×2 →
   `autotest_2098_conv_a_<ts>` / `autotest_2098_conv_b_<ts>` (confirmed
   live: ids `8144`/`8145`)
3. `PUT /elitea_core/conversation/prompt_lib/399/{id}` `{"folder_id": <folder_id>}`
   for each conversation — moves it into the folder (200 confirmed for
   both).

This is **transit setup, not the observable under test** — the case's
own observable (folder expand → conversation open → highlight moves) is
produced entirely by the real UI in steps 1–8 below, driven against these
real, server-persisted conversations. No message content was seeded into
either conversation this session (time budget; the case's own steps
don't require pre-existing message history to prove the flow — see § Blocked Steps
note on step 3's "full history" wording for the implementer).

## Test Steps

1. Navigate to the Chats page; locate the seeded folder
   - **Verify**: folder row renders with a folder icon, collapsed
     (no conversation items visible beneath it)
2. Click the folder to expand it
   - **Verify**: `ChatPage.expand_folder(folder_id)` — `is_folder_expanded(folder_id)`
     flips true; both seeded conversations render inside
     (`is_conversation_in_folder(folder_id, conv_id)` true for both)
3. Click the first conversation inside the folder (`autotest_2098_conv_a`)
   - **Verify**: URL becomes `/chat/{conv_a_id}?name=...`; browser tab
     title shows the conversation name
4. Verify the message input at the bottom is active
   - **Verify**: `message_input.is_visible()` and `.is_editable()`
5. Verify the correct model/agent name is shown in the input bar
   - **Verify**: `get_selected_model()` non-empty (live-confirmed:
     "Anthropic Claude 4.5 Sonnet")
6. Verify the PARTICIPANTS panel shows the correct participant
   - Not click-verified this session (time budget; same pre-proven
     mechanism as ELITEA-2095 — `expand_participants_panel()` +
     `get_participants_user_avatar_text()`, cross-checked against
     `ConversationAPI.get_conversation()`'s `participants` field)
7. Verify the conversation entry in the folder list is highlighted
   - **Verify**: `is_conversation_active(conv_a_id)` true — live-confirmed:
     accessibility snapshot shows `autotest_2098_conv_a...` carrying
     `[active]` after step 3's click
8. Click a different conversation inside the SAME folder
   (`autotest_2098_conv_b`)
   - **Verify**: URL becomes `/chat/{conv_b_id}?name=...`;
     `is_conversation_active(conv_b_id)` true AND
     `is_conversation_active(conv_a_id)` now false — live-confirmed: after
     clicking conv_b, the accessibility snapshot shows `[active]` moved
     from conv_a's row to conv_b's row

## Expected Results
- Folder expands on click, listing both seeded conversations.
- Clicking a conversation inside the folder opens it (URL + title update),
  shows an active input and the correct model name, and highlights that
  conversation's row.
- Clicking a second conversation in the same folder updates the
  interaction window and moves the highlight — the previous conversation
  is no longer marked active.
- No console errors beyond the pre-existing, flow-unrelated warning
  already present on page load (1 warning, 0 errors, confirmed both
  before and after the flow).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Locate folder | folder shown with icon | step 1 | `step 1`: folder row visible, collapsed | asserted |
| 2 Click folder to expand | conversations listed | step 2 | `step 2`: `is_folder_expanded` + both `is_conversation_in_folder` | asserted |
| 3 Click conversation inside folder | content displayed with history | step 3 | `step 3`: URL + title | asserted (message-history assertion left to implementer per note above) |
| 4 Input active | input active | step 4 | `step 4`: `is_visible`+`is_editable` | asserted |
| 5 Model/agent name shown | name visible | step 5 | `step 5`: `get_selected_model()` non-empty | asserted |
| 6 PARTICIPANTS correct | correct participant shown | step 6 | ELITEA-2095's proven mechanism, not re-run live this session | asserted *(reuse of a proven mechanism, not independently re-verified this session — flagged, not a gap)* |
| 7 Active conversation highlighted | highlighted | step 7 | `step 7`: `data-active="true"` on conv_a | asserted |
| 8 Click different conversation | interaction window updates, previous un-highlighted | step 8 | `step 8`: `data-active` moves from conv_a to conv_b | asserted |

### Axis 2 — Analyst additions

- Side-channel console-error check across the whole flow — *added: same
  discipline as ELITEA-2095/2091, catches silent errors the case text
  doesn't ask about.*
- Cleanup via API delete (folder + both conversations) rather than the
  UI's dot-menu "Delete" — *added: `chat-folder-menu-delete-menuitem` is a
  known-dead testid (issue #1309, `test-specs/chat-interface/_surface.md`),
  so API delete is the only reliable teardown path; confirmed this
  session that conversation delete needs the **singular** endpoint
  (`/elitea_core/conversation/...`, not `/conversations/...` — the plural
  form 404s on DELETE despite `automation/CLAUDE.md`'s "API Quirks" table
  claiming conversations are the plural-delete exception; `ConversationAPI.
  delete_conversation()`'s own docstring already has this right, the
  top-level CLAUDE.md table is stale — flagged as a doc-accuracy note,
  not a defect).*

## Cleanup

1. `DELETE /elitea_core/conversation/prompt_lib/399/{conv_a_id}` (singular
   endpoint)
2. `DELETE /elitea_core/conversation/prompt_lib/399/{conv_b_id}`
3. `DELETE /elitea_core/folder/prompt_lib/399/{folder_id}`

All three confirmed live this session (204/204/204) — the seeded folder
and both conversations were fully removed, no residue left in the
account beyond the pre-existing unrelated leaked-folder clutter (issue
#1309, not this case's doing).

## Concrete Handles (discovered during exploration)

Provenance verified fresh (`cd ../EliteaUI && git fetch origin` run this
session) against `origin/main` and `origin/automation/testids` — **all
YES/YES, zero new testids needed**:

| Element | Locator (`LocatorDescriptor` / class constant) | Provenance |
|---|---|---|
| Folder row (dynamic) | `FOLDER_ITEM = '[data-testid="chat-folder-item-{}"]'`, `.format(folder_id)` | on-main ✓ |
| Folder expanded state | `[data-expanded="true"]` on `FOLDER_ITEM` (`is_folder_expanded()`) | on-main ✓ |
| Conversation item scoped in folder | `CONVERSATION_ITEM = '[data-testid="chat-conversation-item-{}"]'`, scoped under `FOLDER_ITEM` (`is_conversation_in_folder()`) | on-main ✓ |
| Active-conversation state | `data-active="true"` on `CONVERSATION_ITEM` (`is_conversation_active()`) | on-main ✓ |
| Message input | `message_input` (existing `LocatorDescriptor` field) | on-main ✓ |
| Model selector name | `model_selector_name` (existing field, `get_selected_model()`) | on-main ✓ |
| Participants toggle | `chat-participants-panel-toggle-button` (existing field) | on-main ✓ |

No `testid needed:` rows.

## Network Behavior

- `POST /elitea_core/folder/prompt_lib/{project_id}` → 201, returns
  `{id, name, owner_id, position, meta}` (no `author_id`/timestamp fields
  needed in the request body despite `FolderCreate`'s OpenAPI schema
  listing `owner_id` as required — server fills it from auth, mirrors the
  same pattern `ConversationAPI.create_conversation()` already relies on
  for `author_id`).
- `PUT /elitea_core/conversation/prompt_lib/{project_id}/{id}`
  `{"folder_id": N}` → 200, moves a conversation into a folder
  instantaneously (no propagation delay observed).
- `DELETE /elitea_core/conversation/prompt_lib/{project_id}/{id}` →
  204 (singular path — see Axis 2 cleanup note; the plural form 404s).
- `DELETE /elitea_core/folder/prompt_lib/{project_id}/{id}` → 204.
- No unexpected console errors observed across the full flow (1
  pre-existing, flow-unrelated warning, consistent before/after).

## Known Defects Found During Exploration

None.

## Blocked Steps

None — case fully executable. One implementer-facing note (not a
blocker): step 3's "full message history" wording — the seeded
conversations in this session had zero messages (folder-assignment is the
thing under test, not message content). If the implementer's spec wants a
non-trivial history assertion for step 3, seed messages via the UI's own
`+Chat` flow before moving the conversation into the folder (per the
ELITEA-2095-documented workaround for defect #691 — never via
`ConversationAPI.create_conversation()` + first UI message on a
zero-message conversation, which silently creates a NEW conversation
instead).

## Automation Hints

- Framework: Playwright + pytest (confirmed).
- Page object: `automation/pages/chat_page.py` — `expand_folder()`,
  `is_folder_expanded()`, `is_conversation_in_folder()`,
  `is_conversation_active()`, `get_folder_item()` all pre-existing
  (ELITEA-2132/2135/2137/2114/2149) and confirmed working live this
  session — zero new page-object work.
- Folder + conversation seeding: use direct REST calls (or a thin
  `FolderAPI`-shaped helper if the implementer wants one — none exists
  yet in `automation/api/`; `ConversationAPI` has no folder methods) —
  the endpoints are `POST /elitea_core/folder/prompt_lib/{project_id}`
  and `PUT /elitea_core/conversation/prompt_lib/{project_id}/{id}` with
  `{"folder_id": N}`, both confirmed working this session.
- Cleanup MUST use the singular conversation-delete endpoint (see § Known
  Defects/Axis 2 note) and MUST NOT rely on the UI's folder dot-menu
  delete (dead testid, issue #1309).
