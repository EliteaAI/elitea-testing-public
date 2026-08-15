# Test Case: Chat – Folder Name Edited Inline During Creation — Custom Name / Cancel Discards

## Metadata
- **TMS ID**: ELITEA-2119, ELITEA-2120
- **Source cases**: `.agents/automation/chat-remaining-w05/cases/ELITEA-2119.md`,
  `.agents/automation/chat-remaining-w05/cases/ELITEA-2120.md` (snapshots;
  TMS module `chat-interface`)
- **Linked Story**: none (both cases `requirements: []`)
- **Priority**: l3 (both case frontmatter: `priority: medium` -> `p2`, same
  class as the sibling ELITEA-2132 covering test's own `@pytest.mark.p2`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids`, DEV backend; project "Private", `projectId=399`,
  `${ELITEA_PROJECT_ID}`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN`
  skips explicit Keycloak login
- **Analyst**: test-automation-engineer (agent), combined analyst+implementer slot
- **Status**: ready-for-automation

**Family AFS**: ELITEA-2119 (custom name saved) and ELITEA-2120 (cancel
discards) are true flow-variants of the SAME inline folder-creation-editor
flow that ELITEA-2118 (default name saved, `lextend_…ELITEA-2118.md`)
already extends — all three open the identical `chat-create-folder-button` ->
`chat-folder-name-input` editor, differing only in what happens next
(confirm-unchanged / confirm-changed / cancel). ELITEA-2118 was handled
separately as `extend-existing` because it is a near-duplicate of the
ALREADY-MERGED `test_folder_creation.py` (ELITEA-2132) with one small gap;
ELITEA-2119 and ELITEA-2120 have **no existing coverage anywhere** — neither
case's action (typing a custom name before confirming; typing a name then
cancelling) is exercised by any merged spec — so they get a fresh family AFS
here rather than being folded into the already-elaborate 2132 test (which
seeds a baseline folder and does full expand/collapse verification the
custom-name/cancel scenarios don't need).

Both scenarios were driven live this session via Playwright MCP against
`http://localhost:5173` before this AFS was written (not assumed from source
alone) — see § Concrete Handles and § Network Behavior for the live-observed
values.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- User is on the Chats section (`${BASE_URL}/chat`).

## Test Data

| Case | Custom/typed folder name |
|---|---|
| ELITEA-2119 | `"My Sprint Folder"` (case's own literal example) |
| ELITEA-2120 | `"Temp Folder"` (case's own literal example) |

Both names are well within `ConversationNameRegExp`'s 3-64-char, allowed-
charset bounds (source: `test-specs/chat-interface/_surface.md` § Folder
rename editor — checkmark enable/disable logic), so neither run needs to
account for a validation-inactive state.

## Test Steps

### ELITEA-2119 — Custom name saved
1. Navigate to `${BASE_URL}/chat`; click the CHATS header folder-creation
   icon.
   - **Verify**: the inline "New folder" editor opens, pre-filled and
     focused (same editor ELITEA-2118/ELITEA-2132 already open).
2. Clear the default name and type `"My Sprint Folder"`.
   - **Verify**: `chat-folder-name-input` reads `"My Sprint Folder"`
     verbatim. **Live-confirmed**: `chat.set_folder_name()`'s
     click+clear+`press_sequentially()` idiom (the project's established
     MUI-safe replace pattern) correctly replaces, not appends, the default
     value.
3. Verify the checkmark icon is active.
   - **Verify**: `chat-folder-name-confirm-button` carries
     `data-disabled="false"` — **live-confirmed**.
4. Click the checkmark icon.
   - **Verify**: `POST /elitea_core/folder/prompt_lib/{project_id}`
     resolves `201`; response `name == "My Sprint Folder"`. **Live-confirmed**
     this session — folder id `183` at exploration time (ephemeral, a fresh
     id is minted per run).
5. Verify the input field closes and the folder name is displayed as plain
   text.
   - **Verify**: `chat-folder-name-input` hidden; the new folder's row shows
     "My Sprint Folder" as plain text, collapsed (`data-expanded="false"`).
     **Live-confirmed**.

### ELITEA-2120 — Cancel discards folder creation
1. Navigate to `${BASE_URL}/chat`; click the CHATS header folder-creation
   icon.
   - **Verify**: the inline "New folder" editor opens, pre-filled and
     focused.
2. Type `"Temp Folder"` (replacing the default).
   - **Verify**: `chat-folder-name-input` reads `"Temp Folder"` verbatim.
3. Click the X (cancel) icon.
   - **Verify**: `chat-folder-name-input` is removed from the DOM (editor
     closes) without saving. **Live-confirmed**.
4. Verify no folder named "Temp Folder" appears in the folder list.
   - **Verify**: no `[data-testid^="chat-folder-item-"]` element's
     `text_content()` contains `"Temp Folder"`. **Live-confirmed** — zero
     matches.
5. Verify the folder list remains unchanged from before the creation
   attempt.
   - **Verify**: the total count of `[data-testid^="chat-folder-item-"]`
     elements after cancel equals the count captured immediately BEFORE
     step 1's click (Axis-2 addition — a bare "Temp Folder not present"
     check alone wouldn't catch a regression that discarded the TYPED name
     but still created an empty/default-named folder). **Live-confirmed**:
     no new `POST` fired at all (see § Network Behavior) — the count is
     provably unchanged, not just visually absent of the typed name.

## Expected Results
- ELITEA-2119: typing a custom name and confirming creates a REAL
  server-side folder (`POST` -> `201`) with that exact name; the editor
  closes and the name renders as plain text — same mechanism as the
  default-name path (ELITEA-2118/2132), only the `name` field differs.
- ELITEA-2120: cancelling after typing a name is a genuine client-side-only
  discard — **no** `POST` fires at all (confirmed via
  `browser_network_requests`, not just a DOM absence check), the editor
  closes, and the folder list's total count is unchanged.

## Coverage Map

### Axis 1 — Case coverage

| Case | Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|---|
| 2119 | Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| 2119 | 1 Navigate to Chats, click folder icon | New folder entry appears, editable | 2119 step 1 | `test_create_folder_with_custom_name` Step 1 | asserted |
| 2119 | 2 Clear default name, type 'My Sprint Folder' | Custom name appears in input | 2119 step 2 | Step 2 (`input_value()` check) | asserted |
| 2119 | 3 Verify checkmark icon is active | Checkmark is active | 2119 step 3 | Step 3 (`is_folder_name_confirm_enabled()`) | asserted |
| 2119 | 4 Click checkmark icon | Folder saved with 'My Sprint Folder' in list | 2119 step 4 | Step 4 (`POST` -> `201`, `name` in response body) | asserted |
| 2119 | 5 Verify input closes, name plain text | Folder visible in panel | 2119 step 5 | Step 5 (`folder_name_input` hidden, name in folder row `text_content()`) | asserted |
| 2119 | Expected Final State: "Folder 'My Sprint Folder' created and visible" | — | 2119 step 5 | Step 5 | asserted |
| 2119 | Pass/Fail: "All steps complete without errors" | — | all steps | console-error side-channel check | asserted |
| 2120 | Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| 2120 | 1 Navigate to Chats, click folder icon | New folder entry appears, editable | 2120 step 1 | `test_cancel_folder_creation_discards_folder` Step 1 | asserted |
| 2120 | 2 Type 'Temp Folder' | Name appears in input | 2120 step 2 | Step 2 (`input_value()` check) | asserted |
| 2120 | 3 Click X (cancel) icon | Input field closes without saving | 2120 step 3 | Step 3 (`folder_name_input` hidden/detached) | asserted |
| 2120 | 4 Verify no folder named 'Temp Folder' in list | Folder not created | 2120 step 4 | Step 4 (no `chat-folder-item-*` row's text contains "Temp Folder") | asserted |
| 2120 | 5 Verify folder list unchanged from before attempt | Folder list unchanged | 2120 step 5 | Step 5 (folder-item count before == after, PLUS zero new `POST` — Axis-2 addition) | asserted |
| 2120 | Expected Final State: "No folder created; list unchanged" | — | 2120 step 5 | Step 5 | asserted |
| 2120 | Pass/Fail: "Cancel discards the folder creation" | — | all steps | Steps 3-5 combined | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked`
/ `out-of-scope`. All rows `asserted` — both scenarios were executable and
confirmed live this session, no blockers, no reverse-masking (both cases'
claims match `FolderItem.jsx`'s actual create/cancel handling exactly).

### Axis 2 — Analyst additions
- ELITEA-2120 step 5 asserts the folder-item COUNT (before vs. after) AND
  zero new `POST` requests, not just "no folder named 'Temp Folder'" — *added:
  a name-only check could pass even if a regression silently created an
  empty-named or default-named folder alongside discarding the typed name;
  the count + network-silence pair is the stronger, structural proof the
  cancel path never mutates server state at all.*
- Both scenarios assert the editor's full close (input removed from DOM),
  not just visual absence — *added: consistent with the covering
  ELITEA-2132/2458 tests' own discipline of checking the strongest available
  signal.*
- Console side-channel checked after each flow — *added: standard
  discipline matching every sibling folder test in this file.*
- (nothing else added beyond the two cases — no defects found, no
  case-text drift.)

## Cleanup
- ELITEA-2119 creates ONE real folder server-side — deleted via
  `chat.delete_folder_via_menu()` in a `finally` block (same
  try/except-guarded pattern as `test_folder_creation.py`'s own cleanup —
  `FOLDER_MENU_DELETE_ITEM` is a currently-dead testid, regression tracked
  in `EliteaAI/elitea-testing-public#1309`, so the method's own
  `delete_folder_via_api()` fallback is what actually removes it).
- ELITEA-2120 creates NO folder (cancel is a genuine no-op) — nothing to
  clean up.
- Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data
  Lifecycle.

## Concrete Handles (discovered during exploration)
No new testids needed — every testid both scenarios require already exists,
added by ELITEA-2132/ELITEA-2458 and confirmed live again this session. One
new page-object METHOD was added during implementation (fix round 1,
`automation/pages/chat_page.py:3186`) on top of the existing `FOLDER_ITEM_PREFIX`
testid, to give ELITEA-2120's step 4 ("no folder named X exists") a
non-brittle assertion instead of constructing a locator inline in the test:

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| CHATS header folder-creation icon | `[data-testid="chat-create-folder-button"]` | on-`main` ✓ | `chat.click_create_folder_button()`. |
| Folder-name inline input | `[data-testid="chat-folder-name-input"]` | on-`automation/testids` ✓ | `chat.folder_name_input` / `chat.set_folder_name()`. |
| Folder-name confirm (checkmark) button | `[data-testid="chat-folder-name-confirm-button"]` | on-`automation/testids` ✓ | `chat.folder_name_confirm_button`, `chat.is_folder_name_confirm_enabled()`. |
| Folder-name cancel (X) button | `[data-testid="chat-folder-name-cancel-button"]` | on-`automation/testids` ✓ | `chat.folder_name_cancel_button`. |
| Folder item row (dynamic, per id) | `[data-testid="chat-folder-item-{id}"]` | on-`automation/testids` ✓ | `chat.get_folder_item(folder_id)`. |
| All folder items (prefix, count) | `[data-testid^="chat-folder-item-"]` (`FOLDER_ITEM_PREFIX`) | on-`automation/testids` ✓ | Used for the before/after count check (ELITEA-2120 step 5), and as the base locator inside `get_folder_names_containing()`. |

All handles verified live this session via direct DOM query
(`document.querySelector`/`querySelectorAll('[data-testid="..."]')`) against
the actual running app, not re-derived from the covering AFS's claims alone.

**Added during ELITEA-2120 implementation (fix round 1):**
`ChatPage.get_folder_names_containing(substring: str) -> list[str]`
(`automation/pages/chat_page.py:3186`) — reads every rendered folder item
(`FOLDER_ITEM_PREFIX`, page-wide, unscoped) and returns the text content of
each one whose text contains `substring`. Used in ELITEA-2120 step 4 to
assert `not matching_names` (no folder named `CANCEL_FOLDER_NAME` exists
after cancel) — replaces an earlier in-test locator construction with a
page-object method, keeping the abstraction-layer discipline (`.claude/rules/page-objects.md`)
that all locators live only as page-object class fields/methods, never
inline in spec files.

## Network Behavior
- ELITEA-2119: `POST /elitea_core/folder/prompt_lib/399` -> `201`, response
  body `name == "My Sprint Folder"` — confirmed live via
  `browser_network_requests` immediately after the confirm click.
- ELITEA-2120: **zero** new requests to `folder/prompt_lib` fire after the
  cancel click — confirmed live via `browser_network_requests` filtered to
  `folder/prompt_lib`, comparing the request list before and after; only the
  entries from an EARLIER, unrelated create (this session's own 2119
  exploration) remained, no new entry appended.

## Known Defects Found During Exploration
None. Both scenarios (custom name save, cancel discard) matched
`FolderItem.jsx`'s actual create/cancel handling exactly — no case-text
drift, no reverse-masking needed.

## Blocked Steps
None. Both scenarios were executable and confirmed live.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`).
- Page object: `automation/pages/chat_page.py` — most methods/constants both
  scenarios require already existed (`click_create_folder_button()`,
  `set_folder_name()`, `is_folder_name_confirm_enabled()`,
  `get_folder_item()`, `delete_folder_via_menu()`, `FOLDER_ITEM_PREFIX`). ONE
  new method was added during implementation (fix round 1):
  `get_folder_names_containing(substring)` (`automation/pages/chat_page.py:3186`)
  — see § Concrete Handles above — so ELITEA-2120 step 4's "no folder named X
  exists" check reads through a page-object method instead of constructing a
  locator inline in the test.
- New spec file: `automation/tests/ui/chat/test_chat_folder_creation_custom_name_and_cancel.py`,
  class `TestChatFolderCreationCustomNameAndCancel`, two independent test
  methods — one per case (not a single `pytest.mark.parametrize`, since the
  two scenarios diverge in ACTION, not just data: one confirms, the other
  cancels — same precedent as the ELITEA-2110/2112/2113 family's separate
  "Shape A" (parametrized) / "Shape B" (distinct action) split documented in
  `test_conversation_rename_invalid_chars_and_recovery.py`).
