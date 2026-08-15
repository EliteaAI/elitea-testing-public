# Test Case: Chat – Folder Rename – Maximum 50 Characters Accepted

## Metadata
- **TMS ID**: ELITEA-2128
- **Linked Story**: none (`requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Elitea Testing Team", observed live as `projectId=399` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer)
- **Status**: ready-for-automation
- **family_afs**: false — no existing folder-rename length/truncation coverage
  exists on the trunk to extend (`test_chat_folder_rename_checkmark_validation.py`
  only exercises the empty/2-char/unchanged/3-char-changed/special-char/
  leading-space validity axis, never the length boundary). Sibling of ELITEA-2129
  (same underlying `MAX_CONVERSATION_LENGTH` mechanism) but the two cases differ in
  ACTION (exact-boundary acceptance vs overflow-truncation via type+paste), not just
  data, so per `test-case-analysis` § Execute ("differ only in data → family; differ
  in steps → separate") they are two AFS files, placed in the same new spec module
  for locality (mirrors the conversation-rename precedent,
  `test_conversation_rename_length_boundaries.py`).

**Related existing coverage (reused as context/transit, not as a covering spec):**
`test-specs/chat-interface/l2_chat-folder-rename-checkmark-validation_ELITEA-2458.md`
(→ `automation/tests/ui/chat/test_chat_folder_rename_checkmark_validation.py`, merged
to `origin/automation/base`) proves the rename mechanics (dot-menu → Rename →
inline editor → checkmark save) and the `isFolderNameValid`/`isFolderSaveEnabled`
gate, but only exercises names far below the length boundary (empty, 2, 3 chars) —
never a 50-character name. Reused here as transit knowledge (flow, testids, page
object methods) — not cited as already covering this case's own observable.
`test-specs/chat-interface/l3_conversation-rename-length-boundaries_ELITEA-2101_2102.md`
(sibling entity, conversations not folders) proves the SAME
`MAX_CONVERSATION_LENGTH = 50` constant governs the analogous conversation-rename
editor — reused as source-level precedent, confirmed independently against the
FOLDER editor this session (source read of `FolderItem.jsx` + live execution, see
§ Concrete Handles / § Automation Hints).

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- Test creates its own folder (see § Test Data) — the case's "at least one existing
  folder is present" precondition is satisfied by setup, not ambient data.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Active project — whatever `${TEST_USER}`'s default/last-selected project is
  (observed live as "Elitea Testing Team", id 399). Don't hardcode the id.

### generate-per-test (created in setup, cleaned up in teardown)
- **`folder_target`** — the folder to rename. Create via the UI's own
  "Create folder" button + `set_folder_name()` + confirm (no folder-creation API
  client exists on this project yet — `ChatPage.delete_folder_via_api()` exists for
  cleanup, but creation goes through the UI, matching ELITEA-2458's own precedent).
  Suggested original name: `at_folder_len50_orig`.
- **Exactly-50-character literal string**: `"A" * 50` (case's own Test Data table
  says "50 characters (e.g. AAAA...AA)"; a flat repeated character is sufficient —
  the case does not ask for character diversity, only length).

## Test Steps

1. Navigate to Chats, hover `folder_target`'s row, click the three-dot icon
   (`open_folder_rename_editor(folder_target_id)`), which opens the **Rename**
   item (labelled "Rename", not "Edit" — see § Known Defects Found).
   - **Verify**: the folder name becomes an editable inline input
     (`chat-folder-name-input`), pre-filled with the current name and focused.
2. Clear the input and type exactly 50 characters via a real character-by-character
   keyboard simulation (`ChatPage.set_folder_name()` — click + clear +
   `press_sequentially`, NOT `fill()`, per the project's established MUI
   onChange-firing idiom).
   - **Verify**: the input's value has length == 50 (no truncation — live-confirmed
     this session: typing `"A"*50` character-by-character lands ALL 50 characters,
     since `onChangeFolderName`'s `event.target.value.slice(0,
     MAX_CONVERSATION_LENGTH)` only bites the 51st+ character, never the 50th).
     `chat-folder-name-confirm-button`'s `data-disabled` attribute is `"false"`
     (name changed AND the 50-char all-`A` string passes `ConversationNameRegExp`).
3. Click the checkmark (save) icon — an explicit click on
   `chat-folder-name-confirm-button`.
   - **Verify**: the input closes (`chat-folder-name-input` no longer present);
     `[data-testid="chat-folder-item-{folder_target_id}"]` shows the new
     50-character name. Underlying network call: `PUT
     /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_target_id}`
     resolves `200` (live-confirmed this session).
   - **Verify**: no error message is shown — no
     `[data-testid="toast-alert"][data-severity="error"]`; no NEW console errors
     beyond the pre-existing, unrelated `secrets/secrets/default` 403 noise present
     on every page load in this environment (same exclusion as ELITEA-2099/2101/
     2102/2103/2104/2458).

## Expected Results
- Exactly 50 characters are accepted into the folder-rename input WITHOUT
  truncation — 50 is the boundary at which the product's `slice(0, 50)` truncation
  would first apply to a 51st character, not to the 50th itself.
- The checkmark saves the resulting 50-character name successfully (`PUT` → `200`,
  no error toast, no new console errors), matching the case's own Pass criteria
  ("All 50 characters are accepted"; "50-character name accepted and saved").

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: ≥1 folder exists | — | Setup | UI create-folder + `set_folder_name` | asserted |
| 1 Navigate, hover, click 3-dot, click Edit → editable | folder name is editable | step 1 | `chat-folder-name-input` visible | asserted |
| 2 Clear + type exactly 50 chars → all 50 accepted | all 50 characters accepted | step 2 | input value length == 50 after typing 50 | asserted |
| 3 Click checkmark → saved with 50-char name, no error | folder saved, no error | step 3 | input gone + folder item text (50 chars) + `PUT …` 200 + toast/console absence | asserted |
| Expected Final State: "Folder saved with a 50-character name" | — | step 3 | covered by the row above | asserted |
| Pass/Fail: "50-character name accepted and saved" | — | steps 2–3 | covered by the rows above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- step 2 additionally asserts the input's exact string value equals `"A"*50` (not
  just the length) — *added: proves all 50 characters landed correctly (no silent
  corruption/reordering), matching the live-read behavior exactly.*
- step 2 additionally asserts `chat-folder-name-confirm-button`'s `data-disabled`
  flips to `"false"` — *added: proves the 50-char value is itself a valid,
  save-enabled state, mirrors ELITEA-2099/2101/2102/2458's same assertion.*
- step 3 asserts the underlying `PUT .../folder/prompt_lib/{project_id}/{id}`
  network call resolves `200` — *added: proves the save is real
  (backend-persisted), not a client-side-only list splice.*
- step 3 explicitly asserts no NEW console errors, excluding the pre-existing
  unrelated `secrets/secrets/default` 403 noise — *added: standard side-channel
  discipline, same exclusion already documented for every sibling rename case.*

## Cleanup
1. Delete `folder_target` via `chat.delete_folder_via_api(folder_id)` in a
   `try`/`finally`, per `.claude/rules/ui-tests.md` § Test Data Lifecycle (same
   pattern as `test_chat_folder_rename_checkmark_validation.py`'s later tests).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback
ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). All
handles below are pre-existing (added during ELITEA-2458's implementation,
`EliteaAI/EliteaUI@0298860f`, on `automation/testids`) — **no new testids needed**.

| Element | Testid handle | Notes / provenance |
|---|---|---|
| Folder row (dynamic) | `[data-testid="chat-folder-item-{id}"]` | Pre-existing class constant (`FOLDER_ITEM`). On `main` (pre-existing, long-standing). |
| Folder icon (hover target to reveal dot-menu) | `[data-testid="chat-folder-icon"]`, scoped inside `chat-folder-item-{id}` | Pre-existing (`FOLDER_ICON`). On `main`. |
| Folder 3-dot menu button | `[data-testid="conversation-menu-menu-button"]`, scoped inside `chat-folder-item-{id}` | Shared, non-unique testid (same `DotMenu` component as conversation items) — `ChatPage.open_folder_rename_editor()` scopes it with `.first`. On `main`. |
| Rename dot-menu item | `chat-folder-menu-rename-menuitem` | Added ELITEA-2458, `EliteaAI/EliteaUI@0298860f`, on `automation/testids`. |
| Folder-rename inline input | `chat-folder-name-input` | Pre-existing, shared between create-new-folder and rename-existing-folder flows. On `main`. Live-verified this session on the RENAME path specifically (not just create): typing 50 chars lands all 50, typing a 51st is silently dropped (see ELITEA-2129 AFS). |
| Folder-rename confirm (checkmark) button | `chat-folder-name-confirm-button`, carries `data-disabled="true"/"false"` | Added ELITEA-2458, `EliteaAI/EliteaUI@0298860f`, on `automation/testids`. Live-verified `data-disabled="false"` after the 50-char value. **A11y-snapshot pruning gotcha applies** (`test-specs/chat-interface/_surface.md` § Folder rename editor) — assert via the testid locator directly, never via a `browser_snapshot` accessible-name read. |
| App-wide toast alert (error/success severity) | `[data-testid="toast-alert"][data-severity="{severity}"]` | Pre-existing (`ChatPage.get_toast_alert`, `TOAST_ALERT_SEVERITY`). |

## Network Behavior

- Rename commit (step 3): `PUT
  /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_target_id}` → `200`,
  live-confirmed with the 50-character name as the payload's `name`.
- Folder creation (setup): `POST /api/v2/elitea_core/folder/prompt_lib/{project_id}`
  → `201` (same endpoint `test_chat_folder_rename_checkmark_validation.py` already
  uses for seeding).

## Known Defects Found During Exploration

None. The case passes end-to-end against the live product exactly as its own case
text expects — exactly 50 characters are accepted with no truncation and the
checkmark saves them successfully, no error surfaced.

**Case-text drift (pre-existing, already documented elsewhere in this digest, noted
again since this AFS references it independently)**: the case's step 1 says "click
three-dot icon, click Edit" — the real dot-menu item is labelled "Rename", not
"Edit". Not a defect (`test-specs/chat-interface/_surface.md` documents this same
drift for ELITEA-2121/2130/2456/2123/2127).

## Blocked Steps

None — all 3 case steps executed live end-to-end this session against a real
folder created via the UI (id 250, deleted via the UI's own Delete flow immediately
after exploration, zero net pollution): opened the rename editor via the dot-menu
(not just the create-folder editor, to match the case's own "existing folder" +
"three-dot icon" framing), typed exactly 50 characters, confirmed no truncation,
saved successfully (`PUT` → the DOM re-rendered the 50-char name).

## Automation Hints

- **Source-confirmed validation logic** (`EliteaUI/src/[fsd]/features/chat/
  conversation-list/ui/folders/FolderItem.jsx` + `EliteaUI/src/common/
  constants.js`), grounds every assertion in this AFS:
  - `MAX_CONVERSATION_LENGTH = 50` (`constants.js:74`) — the SAME constant
    `ConversationItem.jsx` uses; `FolderItem.jsx`'s `onChangeFolderName` does
    `const newName = event.target.value.slice(0, MAX_CONVERSATION_LENGTH)` on every
    `onChange` (source line `FolderItem.jsx:180`, grep-confirmed this session).
  - `ConversationNameRegExp = /^[a-zA-Z0-9_[\].()][a-zA-Z0-9_[\].() -]{2,63}$/`
    (3–64 chars total, `isFolderNameValid`) governs CHARSET/first-char validity —
    a distinct, wider gate than the 50-char slice; the resulting 50-char all-`A`
    string easily satisfies both.
  - `isFolderSaveEnabled = isFolderNameValid && (isNewFolder || folderName !==
    name)` — for an existing folder (rename, not create) both valid AND changed
    are required, same gate ELITEA-2458 already documents.
- **Implementer note**: write this as the FIRST test function in a NEW file,
  `automation/tests/ui/chat/test_chat_folder_rename_length_boundaries.py`
  (mirrors `test_conversation_rename_length_boundaries.py`'s naming and structure
  for the conversation entity) — same page object (`ChatPage`), same helpers
  (`click_create_folder_button`, `set_folder_name`, `open_folder_rename_editor`,
  `is_folder_name_confirm_enabled`, `delete_folder_via_api`). ELITEA-2129 (overflow
  type+paste) is the sibling test function in the SAME file/class — see that AFS.
- No paste-specific page-object method exists for folders yet
  (`paste_conversation_name()` exists only for conversations) — ELITEA-2129's AFS
  specifies adding `paste_folder_name()`, mirroring that method exactly. Not needed
  for this case (ELITEA-2128 only types, never pastes).
- `.playwright-mcp/console-2026-08-15T06-14-07-970Z.log` (session-wide) captures
  the full console stream for this exploration; the 4 ERROR-level entries recorded
  during the session are all this analyst's own manual cross-origin cleanup probes
  (`fetch()` to `dev.elitea.ai` from `localhost:5173`, CORS-blocked) — NOT product
  errors, and NOT reachable from the shipped test (which cleans up via
  `delete_folder_via_api()`, which already handles the correct base URL + auth
  fallback, or via the UI's own Delete flow).
