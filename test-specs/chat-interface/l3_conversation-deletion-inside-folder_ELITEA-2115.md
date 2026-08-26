# Test Case: Chat – Conversation Deletion – Conversation Inside a Folder

## Metadata
- **TMS ID**: ELITEA-2115
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend); project **"UI Testing" (id 400)** — a dedicated, normally-empty sandbox project (confirmed live: 0 conversations before this session), used instead of the default `${ELITEA_PROJECT_ID}`/`${TEST_USER}`'s Team project so this case's folder+conversation seeding/deletion never touches shared fixture data other analyses reuse (`_surface.md` documents "Review attached documents" id 420 on project 471 as repeatedly-reused shared data — this case doesn't touch it)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-14
- **Status**: ready-for-automation

No existing AFS or merged test covers deleting a conversation that lives INSIDE a
folder. `test_conversation_deletion_flow.py` (ELITEA-2114) and
`test_conversation_management.py::TestConversationActions` both delete only
top-level/ungrouped conversations. `test_move_conversation_to_folder.py` /
`test_open_conversation_from_folder.py` exercise folders but never delete a
conversation from inside one. This is genuinely new coverage.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- Test creates its own folder + conversation via API (see § Test Data) — the
  case's "a folder with at least one conversation exists" precondition is
  satisfied by setup, not ambient data.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- **Project 400 ("UI Testing")** — pass `project_id="400"` explicitly to
  `ConversationAPI`/the conversation-scoped fixtures for this test (do NOT rely
  on the default `${ELITEA_PROJECT_ID}`/last-selected-project — this case needs
  a project with no ambient conversations so the folder-preserved assertion is
  unambiguous; confirmed empty live prior to seeding).

### generate-per-test (created in test setup, cleaned up in its own teardown)
- **`folder`** — via `conversation_api.create_folder(name)`.
- **`conv_in_folder`** — via `conversation_api.create_conversation(name)` then
  `conversation_api.move_conversation_to_folder(conv_id, folder_id)`. This is
  the conversation that gets deleted.

## Test Steps

**Setup (not a numbered case step)**
0. Create `folder` then `conv_in_folder` via the API, move `conv_in_folder` into
   `folder`. Navigate to `${BASE_URL}/chat` (project 400).

1. Navigate to Chats and expand `folder`.
   - **Verify**: `[data-testid="chat-folder-item-{folder_id}"]` visible;
     folders render **expanded by default** on this project (live-confirmed —
     no explicit expand click was needed; `is_folder_expanded()`/`expand_folder()`
     remain available defensively in case a differently-seeded folder starts
     collapsed). `[data-testid="chat-conversation-item-{conv_in_folder_id}"]`
     visible as a descendant of the folder item
     (`is_conversation_in_folder(folder_id, conv_id)` → `True`).
2. Hover `conv_in_folder`, click the three-dot icon.
   - **Verify**: `conversation-menu-menu-button` (scoped inside
     `chat-conversation-item-{conv_in_folder_id}`) transitions to visible on
     hover, then the context menu opens showing **Delete** among the live item
     set. Live-confirmed set for a folder-scoped conversation on this project:
     Rename, Move to, Playback, Duplicate, Make public, Share, Pin on top
     (**disabled** — folder-scoped conversations can't be pinned, per
     `_surface.md` § Pin conversation: `disabled: !isPinned &&
     !!conversation.folder_id`), Delete.
3. Click Delete.
   - **Verify**: `[data-testid="delete-confirm-dialog"]` visible, body text
     `"Are you sure to delete the {conv_in_folder name} chat? It can't be
     restored."` (same live string pattern as ELITEA-2114's AFS — case's
     literal wording is stale, same known drift).
4. Click the Delete (confirm) button.
   - **Verify**: `[data-testid="delete-confirm-button"]` click →
     `DELETE /api/v2/elitea_core/conversation/prompt_lib/400/{conv_in_folder_id}`
     resolves `204`; dialog closes;
     `[data-testid="chat-conversation-item-{conv_in_folder_id}"]` has 0 count.
5. Verify the folder still exists in the left panel.
   - **Verify**: `[data-testid="chat-folder-item-{folder_id}"]` still visible,
     unaffected count (folder itself is a separate entity from its
     conversations — confirmed live: no folder-level DELETE request fires).
6. Verify the folder now shows an empty state (it was the last conversation in
   this folder).
   - **Verify**: `get_folder_empty_state_text(folder_id)` returns the live
     text **"No conversations added"** (`FOLDER_EMPTY_STATE` testid,
     `[data-testid="chat-folder-empty-state"]`, scoped inside the folder item —
     already a page-object method, no new handle needed). Live-verified this
     session (§ below) — case's own wording ("Folder shows empty state or
     updated count") is satisfied by the empty-state branch since this test
     seeds exactly one conversation into the folder.

## Expected Results
- Deleting a conversation that lives inside a folder removes only that
  conversation; the folder itself is never touched (no folder-level API call).
- The folder renders its own dedicated empty state
  (`chat-folder-empty-state`, "No conversations added") once its last
  conversation is gone — live-confirmed, not inferred.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | fixture/`auth_state` | asserted |
| Precondition: folder with ≥1 conversation exists | — | Setup | `create_folder` + `create_conversation` + `move_conversation_to_folder` | asserted |
| 1 Navigate to Chats, expand folder → conversations inside visible | folder expanded, conversation visible | step 1 | `is_conversation_in_folder()` | asserted |
| 2 Hover conversation inside folder, click 3-dot → context menu with Delete option | menu appears with Delete | step 2 | menu-item visibility check | asserted |
| 3 Click Delete → "Delete conversation?" modal appears | confirmation modal | step 3 | `delete-confirm-dialog` visible + body text | asserted *(dialog title/body wording matches the live product, not the case's stale literal text — same documented drift as ELITEA-2114)* |
| 4 Click Delete button → conversation removed from folder | conversation removed | step 4 | `DELETE` 204 + item count 0 | asserted |
| 5 Verify folder still exists → folder not deleted | folder preserved | step 5 | `chat-folder-item-{id}` still visible | asserted |
| 6 Verify folder empty/updated-count state | empty state or updated count shown | step 6 | `get_folder_empty_state_text()` == "No conversations added" | asserted |
| Expected Final State: "conversation deleted from folder; folder remains" | — | steps 4–6 | covered by rows above | asserted |
| Pass/Fail: "no errors" | — | step 4 | `DELETE` 204 (no error response) | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- Step 2 explicitly documents the live 8-item menu set (incl. Pin on top
  disabled) for a folder-scoped conversation — *added: the case only says
  "Delete option" appears, doesn't enumerate the rest; documenting the
  disabled-Pin state here avoids a future case tripping over it as a surprise
  (already flagged generically in `_surface.md` § Pin conversation).*
- Step 4 asserts the underlying `DELETE` network call resolves 204 — *added:
  same "prove it's real, not a client-side splice" discipline as ELITEA-2114's
  AFS.*
- Step 5 explicitly asserts NO folder-level API call fires — *added: this is
  the case's own core assertion ("folder itself preserved") made concrete
  and network-verifiable rather than just a DOM-persistence check.*

## Cleanup
1. `conversation_api.delete_folder(folder_id)` — `conv_in_folder` is already
   consumed by the test's own delete action.
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

| Element | Testid handle | Notes |
|---|---|---|
| Folder item (dynamic) | `[data-testid="chat-folder-item-{folder_id}"]` | Already a class constant (`FOLDER_ITEM`), already used by `get_folder_item()`/`expand_folder()`/`is_conversation_in_folder()`. |
| Conversation-in-folder scoping | `is_conversation_in_folder(folder_id, conversation_id)` | Pre-existing `ChatPage` method (`chat_page.py:6233-6254`) — scopes `CONVERSATION_ITEM` inside `FOLDER_ITEM`, no new locator needed. |
| Folder empty state | `[data-testid="chat-folder-empty-state"]` via `get_folder_empty_state_text(folder_id)` | Pre-existing (`chat_page.py:6290-6297`). Live-verified text this session: `"No conversations added"`. |
| Delete confirm dialog / button | `delete-confirm-dialog`, `delete-confirm-message`, `delete-confirm-button` | Same handles as ELITEA-2114's AFS — already on `main` via that implementation's `automation/testids` commit. |
| Conversation 3-dot menu / Delete menu item | `conversation-menu-menu-button` (scoped), `chat-conversation-menu-delete-menuitem` | Same handles as ELITEA-2114's AFS. |
| Folder-scoped Pin item disabled state | `chat-conversation-menu-pin-menuitem` (existing) | No new handle needed — `disabled` attribute already reflects `ConversationItem.jsx`'s existing logic; this AFS just documents it's expected to be disabled here. |

No new testids needed — every handle this case touches already exists on
`automation/testids` (added by ELITEA-2114/ELITEA-2098/ELITEA-2149's prior
implementations).

## Network Behavior
- `DELETE /api/v2/elitea_core/conversation/prompt_lib/400/{conv_in_folder_id}` →
  `204 No Content` on confirm (step 4).
- No `DELETE .../folder/prompt_lib/400/{folder_id}` call fires at any point
  (step 5's "folder preserved" assertion, network-verified).

## Known Defects Found During Exploration
None. All 6 case steps matched live product behavior exactly (module the
already-documented dialog-title/body-text case-text drift shared with
ELITEA-2114/#695, not re-filed here).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`). Extend `ChatPage`
  (`automation/pages/chat_page.py`) — every method this case needs already
  exists (`expand_folder`, `is_conversation_in_folder`,
  `get_folder_empty_state_text`, `open_conversation_context_menu`,
  `click_conversation_menu_item`, `confirm_delete_conversation`).
- **Use project 400 ("UI Testing"), not the default `${ELITEA_PROJECT_ID}`.**
  `ConversationAPI(browser_cookies=[], project_id="400")` (or the equivalent
  fixture parameterization) — this project was confirmed live to have zero
  ambient conversations/folders before seeding, so the "folder preserved with
  empty state" assertion can't be muddied by stray pre-existing folders.
  Bearer-token auth (`ELITEA_API_TOKEN`, no `browser_cookies`) works fine for
  this project per the same pattern `ConversationAPI` already documents for
  the trap in `_surface.md` § "Manual `ConversationAPI()` script vs the
  `conversation_api` fixture" — just pass `project_id` explicitly rather than
  relying on the settings default (399).
- Reuse `conversation_api.create_folder()`/`move_conversation_to_folder()`
  (added by ELITEA-2098's implementation) — no new API client methods needed.
- Folders on this project rendered **expanded by default** with a single
  conversation inside — if a future variant seeds multiple folders, don't
  assume this holds generally; call `expand_folder()` defensively.
