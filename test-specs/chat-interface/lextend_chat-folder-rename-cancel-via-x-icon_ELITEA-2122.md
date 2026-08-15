# Test Case: Chat – Folder Rename – Cancel via X Icon Discards Changes

## Metadata
- **TMS ID**: ELITEA-2122
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private", observed live as `projectId=399` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer)
- **Status**: extend-existing
- **Extension target**: `automation/tests/ui/chat/test_chat_folder_rename_checkmark_validation.py` (its own AFS: `test-specs/chat-interface/l2_chat-folder-rename-checkmark-validation_ELITEA-2458.md`)

**No live re-execution needed to confirm the mechanism — confirmed via a full
source read of `FolderItem.jsx`** (the same file the ELITEA-2458/2459/2121
AFS files in this directory already derive every assertion from), cross-
checked against `chat-folder-name-cancel-button`'s testid presence on BOTH
`main` and `automation/testids` (`git grep`, fresh `git fetch origin` first —
see § Concrete Handles). The cancel `Box`'s `onClick` is
`isNewFolder ? handleOnCancelCreateFolder : handleOnCloseEditFolder`; for an
EXISTING folder being renamed (`isNewFolder === false`, this case's own
scenario) that resolves to `handleOnCloseEditFolder`:
```js
const handleOnCloseEditFolder = useCallback(() => {
  setFolderName(name);        // resets the LOCAL editor state to the folder's
                               // persisted `name` prop — discards any typed edit
  setIsFolderEditing(false);  // exits edit mode, editor unmounts
}, [name]);
```
No network call anywhere in this handler or its dependency chain — the
discard is purely client-side local-state reset, the exact same mechanism
already live-confirmed for the sibling flows this AFS extends from:
ELITEA-2120 (folder-CREATION cancel, same file's `handleOnCancelCreateFolder`
sibling) and ELITEA-2100 (conversation-rename cancel,
`ConversationItem.jsx`'s analogous handler) — both documented in
`test-specs/chat-interface/_surface.md` as "cancel fires zero new requests,
confirmed via `browser_network_requests`". This case is the missing sibling
of that pair for **folder rename** specifically: `test_chat_folder_rename_checkmark_validation.py`
(ELITEA-2458/2459/2121/2130) never exercises the cancel/X-icon path, only the
checkmark/confirm path — confirmed by reading the full file (grep for
"cancel" returns zero hits in it) — and
`test_chat_folder_creation_custom_name_and_cancel.py` (ELITEA-2119/2120/2133/
2134) only exercises cancel during folder **creation**, never rename. Zero
existing coverage of this exact case element anywhere on the trunk.

A source-grounded AFS (no live run) is a deliberate choice here, not a
shortcut of convenience: the mechanism is a pure, dependency-array-scoped
`useCallback` with no async/network branch, already read start-to-finish, and
the identical discard idiom is independently live-confirmed twice on sibling
components in this same file tree (ELITEA-2120, ELITEA-2100) — re-driving a
third, mechanically-identical instance live would reconfirm a already-proven
pattern rather than discover anything new. The implementer's Phase 4 live
pytest run is still the actual proof for THIS test; this paragraph only
explains why Phase 2 exploration didn't need a separate manual click-through
first.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- At least one folder exists that the test owns (this case seeds its own
  folder — same rationale as ELITEA-2121's AFS: a known, controlled starting
  name is required to assert "original name preserved" precisely, and the
  shared DEV project already carries extensive pre-existing folder-name
  pollution documented in the ELITEA-2458 AFS).

## Test Data

### generate-per-test (created by the test's own setup, cleaned up in its own teardown)
- One folder, created via the existing `click_create_folder_button()` +
  `set_folder_name(<name>)` + `folder_name_confirm_button.click()` flow
  (ELITEA-2132's create path, already reused verbatim by ELITEA-2458/2121),
  with a deterministic seed name — `"ELITEA2122RenameCancelSource"`.
- Temp rename typed then discarded, per the case's own § Test Data table:
  `"Renamed Folder"`.

## Test Steps

1. Navigate to `${BASE_URL}/chat`, seed the folder (§ Test Data), hover the
   folder row, click the 3-dot icon, click "Rename" (case says "Edit" — see
   the already-filed case-text drift below, same drift as ELITEA-2121/#1534).
   - **Verify**: the inline editor opens — `chat-folder-name-input` is
     visible and pre-filled with the folder's current name
     (`"ELITEA2122RenameCancelSource"`).
2. Clear the current name and type `"Renamed Folder"`.
   - **Verify**: the input shows `"Renamed Folder"`.
3. Click the X (cancel) icon (`chat-folder-name-cancel-button`).
   - **Verify**: the editor closes (`chat-folder-name-input` → count 0) with
     NO new `PUT /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_id}`
     request fired (network-silence signal, same idiom as ELITEA-2120/
     ELITEA-2100's cancel checks) — the discard is provably client-side-only,
     not a save-then-instant-revert.
4. Verify the folder still displays its original name.
   - **Verify**: `chat-folder-item-{folder_id}`'s displayed name reads
     `"ELITEA2122RenameCancelSource"` (the ORIGINAL seed name, not
     `"Renamed Folder"`).
5. Verify no error message is shown.
   - **Verify**: no unexpected console errors fired across the whole flow
     (the environment-wide, pre-existing `secrets/secrets/default` 403 noise,
     filtered in every sibling folder test in this file, is excluded).

## Expected Results
- Hovering a folder reveals its 3-dot menu button; clicking it and then
  "Rename" opens the shared inline editor `FolderItem.jsx` renders for both
  create and rename, pre-filled with the folder's current name.
- Typing a new name and clicking the X (cancel) icon closes the editor
  WITHOUT firing any network request — a pure client-side local-state
  discard (`handleOnCloseEditFolder`'s `setFolderName(name)`).
- The folder's displayed name is unchanged — still the original seed name.
- No new console errors beyond the pre-existing, environment-wide `secrets`
  403 noise.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: at least one folder exists | — | Setup | test seeds its own folder | asserted |
| 1 Hover folder, click 3-dot, click Edit | Folder name is editable | AFS step 1 (as "Rename" — drift, see below) | step 1: editor open, pre-filled | asserted |
| 2 Clear + type 'Renamed Folder' | New name appears in the input | AFS step 2 | step 2: input value | asserted |
| 3 Click the X (cancel) icon | Input closes without saving | AFS step 3 | step 3: editor closed + zero new PUT requests | asserted |
| 4 Verify the folder still displays its original name | Original name preserved | AFS step 4 | step 4: displayed name equals original seed name | asserted |
| Expected Final State: "Original folder name is preserved after cancelling" | — | step 4 | covered by the row above | asserted |
| Pass/Fail: "All steps complete without errors" / "Name is changed despite cancelling" | — | all steps | step 5 console-check + step 4's name-unchanged assertion | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` /
`out-of-scope`. All rows `asserted`. No reverse-masking: the one case-text/
product-labelling mismatch (menu item name) is handled per the Hard Rules'
reverse-masking guard — see below.

**Case-text drift, already filed, not re-filed here:** the case's step 1 says
"click Edit" — the live/source-confirmed item is labelled "Rename", the exact
same drift as ELITEA-2121's case text (own case: "verify context menu:
Delete, Edit, Export, Pin or Unpin"), filed there as
[elitea-testing-public#1534](https://github.com/EliteaAI/elitea-testing-public/issues/1534).
This AFS's step 1 clicks the real "Rename" menu item (`chat-folder-menu-rename-menuitem`,
restored on `automation/testids` by the ELITEA-2121 session, see that AFS's
Concrete Handles table) — asserting the real behavior, not the case's stale
label, per the reverse-masking guard. No new clarification issue needed;
#1534 already covers this exact drift on this exact menu.

### Axis 2 — Analyst additions

- Step 3's cancel-discard check asserts network silence (zero new PUT
  requests) in addition to the DOM-level "editor closes" signal — *added:
  the case's own step 3 expected result ("Input closes without saving") is
  ambiguous between "closes with no network effect" and "closes after an
  instant no-op save"; asserting the network layer directly disambiguates,
  same idiom as ELITEA-2120/ELITEA-2100's already-merged cancel checks.*
- Console-error check after the full flow — *added: standard side-channel
  discipline, same idiom as every sibling folder test in this file
  (`test_chat_folder_rename_checkmark_validation.py`'s existing three test
  methods all include this check).*
- (nothing else added beyond the case — the remaining steps map 1:1 onto the
  case's own literal steps.)

## Cleanup
1. Delete the seeded folder via `ChatPage.delete_folder_via_api()` directly
   (NOT `delete_folder_via_menu()`'s UI path when that path's target testid
   is unavailable — `delete_folder_via_menu()` itself already falls back to
   the API path automatically per its own docstring, so either call is safe;
   reuse the same pattern the sibling tests in this file use).
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is testid-only (`.agents/testing.md` § Locator policy).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Folder dot-menu button (3-dot) | `[data-testid="conversation-menu-menu-button"]`, scoped inside `chat-folder-item-{folder_id}` | on-`main` ✓ | Pre-existing (ELITEA-2132), reused verbatim. |
| Folder dot-menu "Rename" item | `[data-testid="chat-folder-menu-rename-menuitem"]` | on-`automation/testids` ✓ (`EliteaAI/EliteaUI@be489cee`, ELITEA-2121 session), on-`main` ✗ (pending human cherry-pick) | Reused verbatim, no new work — `open_folder_rename_editor()` already wraps this. |
| Folder-name inline input | `chat-folder-name-input` | on-`automation/testids` ✓, on-`main` ✓ | Pre-existing (ELITEA-2132/2458), reused verbatim. Verified via fresh `git fetch origin` + `git grep` against `EliteaAI/EliteaUI` both refs this session. |
| Folder-name confirm (checkmark) button | `chat-folder-name-confirm-button` | on-`automation/testids` ✓, on-`main` ✓ | Not clicked by this case's own flow (rename is cancelled, never confirmed) — listed for completeness only, not referenced by this test. |
| Folder-name cancel (X) button | `chat-folder-name-cancel-button` | on-`automation/testids` ✓, on-`main` ✓ | **This case's core handle.** `LocatorDescriptor` field `folder_name_cancel_button` already exists in `automation/pages/chat_page.py:1197` (added defensively alongside the confirm button during an earlier session) but has **zero existing callers** anywhere in `automation/tests/` — confirmed via grep. This test is its first live use — compliant per canon ruling #511 ("referenced" = called on the test's actual executed code path; a page-object field with no caller isn't referenced until now). |
| Folder row (displayed name) | `chat-folder-item-{id}` | on-`automation/testids` ✓, on-`main` ✗ | Pre-existing (ELITEA-2132/2458), reused verbatim for the step-4 name-preserved check (`.text_content()`). |

## Network Behavior
- **Zero** new requests to `folder/prompt_lib/{project_id}/{folder_id}` (any
  method) fire on the cancel-click (step 3) — source-grounded
  (`handleOnCloseEditFolder` has no fetch/dispatch call in its body or
  dependency closure) and consistent with the two independently
  live-confirmed sibling cancel flows (ELITEA-2120 folder-creation-cancel,
  ELITEA-2100 conversation-rename-cancel) already documented in
  `test-specs/chat-interface/_surface.md`.
- `POST /api/v2/elitea_core/folder/prompt_lib/{project_id}` → `201 Created` —
  seed-folder creation only (setup, not the case's own observable).

## Known Defects Found During Exploration
None. No new defect surfaced by this AFS — the mechanism is source-confirmed
identical to two already-live-verified sibling cancel flows.

## Blocked Steps
None. All 5 case steps are executable via existing, already-verified page-object
infrastructure (`open_folder_rename_editor()`, `set_folder_name()`,
`folder_name_cancel_button`, `get_folder_item()`).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Page object: extend `automation/tests/ui/chat/test_chat_folder_rename_checkmark_validation.py`
  as a new test method on `TestChatFolderRenameCheckmarkValidation` — no new
  page-object methods needed. Reuse verbatim: `chat.navigate_to_chat()`,
  `chat.wait_for_page_load()`, `chat.click_create_folder_button()`,
  `chat.set_folder_name()`, `chat.folder_name_confirm_button` (seed only),
  `chat.get_folder_item()`, `chat.open_folder_rename_editor()`,
  `chat.folder_name_input`, `chat.folder_name_cancel_button` (its first
  caller), `chat.delete_folder_via_menu()` (cleanup, existing API fallback).
- Wait strategy: `page.expect_response()` for the seed-folder `POST`, same
  idiom as the file's existing test. For the cancel-click's "no PUT fires"
  check, register a `page.on("request", ...)` PUT-collector BEFORE the click
  (same idiom as the existing test's steps 3/6 no-op-click checks in this
  same file) and assert the collected list is unchanged after
  `chat.wait_for_network()` — do NOT use a raw sleep to "wait and see if a
  request appears."
- Coverage-tag mechanics: append a second `@allure.issue(...)` decorator (this
  case's own onetest-ai case-file URL) directly onto the NEW test method —
  do not touch the file's three existing test methods (ELITEA-2458/2459,
  ELITEA-2121, ELITEA-2130), which stay byte-identical (additive-only on this
  shared-caller file, verified via `git diff | grep -E '^-[^-]'` before
  handoff).
