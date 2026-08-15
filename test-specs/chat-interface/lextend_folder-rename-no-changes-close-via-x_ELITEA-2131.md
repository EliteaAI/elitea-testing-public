# Test Case: Chat – Folder Rename – No Changes Made Checkmark Inactive

## Metadata
- **TMS ID**: ELITEA-2131
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case frontmatter: `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private", `projectId=399`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-15, wave-06
- **Status**: extend-existing
- **Extension target**: `automation/tests/ui/chat/test_chat_folder_rename_checkmark_validation.py`
  (its own AFS: `test-specs/chat-interface/l2_chat-folder-rename-checkmark-validation_ELITEA-2458.md`)

**Steps 1–4 are already covered, steps 5–6 are a genuine gap.** ELITEA-2131's
steps 1–4 (open editor pre-filled, make no changes, verify checkmark
disabled, click → no effect) map exactly onto the covering test's Step 6
(`FolderItem.jsx`'s `isFolderSaveEnabled` is a pure string comparison at
render time — `folderName !== name` — so "restore the pre-filled value after
typing something else" and "never touch the field at all" are behaviourally
IDENTICAL states, not merely similar ones; source-confirmed, not assumed).
The genuinely new element is steps 5–6: **close the editor via the X (cancel)
icon while NO change was ever made, then verify the folder's name is
unchanged in the LIST** (not just in the still-open editor). Neither existing
test method in this file exercises this exact combination:
`test_folder_rename_checkmark_validation` (ELITEA-2458) never closes via X at
all (its no-op checks click the CONFIRM button, not cancel, and leave the
editor open for its own subsequent steps); `test_folder_rename_cancel_via_x_icon_discards_changes`
(ELITEA-2122) closes via X, but only AFTER typing a genuinely different name
first — it never covers the "cancel with zero edits ever made" path.

Because closing the editor is a terminal action for that editing session (it
cannot be followed by the covering test's own Steps 7–9, which need the
editor still open), this gap cannot be spliced inline into
`test_folder_rename_checkmark_validation` the way ELITEA-2125's gap can — it
needs its own NEW test method on the same class, mirroring exactly how
ELITEA-2121/2130/2122 were each added as new methods in this same file
rather than modifying the existing ones.

**Live-verified this session** (fresh live drive, `browser_run_code_unsafe`
against `localhost:5173`, project 399, same session as the ELITEA-2125 gap
check): using the SAME seeded folder (`"W06GapCheck5"`, id 242), after
restoring the input to the folder's original name (functionally equivalent
to "no changes made" per the source-derivation above — confirmed
`data-disabled="true"`, no tooltip), clicked `chat-folder-name-cancel-button`
and observed: the editor closed (`chat-folder-name-input` became not
visible), zero new `PUT .../folder/prompt_lib/399/242` requests fired, and
the folder's row (`chat-folder-item-242`) re-rendered showing the ORIGINAL
name `"W06GapCheck5"` (confirmed via `.textContent()`).

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- At least one folder exists that the test owns (this case seeds its own
  folder — same rationale as ELITEA-2122's AFS: a known, controlled starting
  name is required to assert "original name preserved" precisely).

## Test Data

### generate-per-test (created by the test's own setup, cleaned up in its own teardown)
- One folder, created via the existing `click_create_folder_button()` +
  `set_folder_name(<name>)` + `folder_name_confirm_button.click()` flow, with
  a deterministic seed name — `"ELITEA2131NoChangesSource"`.

## Test Steps

1. Navigate to `${BASE_URL}/chat`, seed the folder (§ Test Data), hover the
   folder row, click the 3-dot icon, click "Rename" (case says "Edit" — same
   already-documented drift as the sibling ELITEA-2121/2122/2130/2123/2124/
   2126/2125 cases, not re-filed here).
   - **Verify**: the inline editor opens — `chat-folder-name-input` is
     visible and pre-filled with the folder's current name
     (`"ELITEA2131NoChangesSource"`).
2. Do not make any changes to the folder name.
   - **Verify**: the input still shows `"ELITEA2131NoChangesSource"`.
3. Verify the checkmark icon is in a disabled/inactive state.
   - **Verify**: `chat-folder-name-confirm-button` carries
     `data-disabled="true"` (valid but unchanged).
4. Attempt to click the checkmark icon.
   - **Verify**: the editor stays open, the input value is still unchanged,
     the folder's `chat-folder-item-{folder_id}` row does NOT re-render, and
     zero new `PUT .../folder/prompt_lib/{project_id}/{folder_id}` requests
     fire — same three-signal no-op pattern the covering test's own Step 6
     already uses.
5. **NEW** — Click the X (cancel) icon (`chat-folder-name-cancel-button`) to
   close the edit mode.
   - **Verify**: the editor closes (`chat-folder-name-input` → not visible),
     with zero new `PUT` requests firing on the close itself.
6. **NEW** — Verify the folder name is unchanged in the folder list.
   - **Verify**: `chat-folder-item-{folder_id}`'s displayed name still reads
     `"ELITEA2131NoChangesSource"`.

## Expected Results
- The checkmark stays inactive when no changes are made (same mechanism as
  the covering test's valid-but-unchanged state), clicking it has no effect,
  and closing the editor via the X icon with zero prior edits cleanly exits
  edit mode with no network call and no change to the folder's displayed
  name.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: at least one folder exists | — | Setup | test seeds its own folder | asserted |
| 1 Hover folder, click 3-dot, click Edit → editable, pre-filled | Target state reached | AFS step 1 | editor open + pre-fill assertion | asserted |
| 2 No changes made → name unchanged | Field state unchanged | AFS step 2 | input value assertion | asserted |
| 3 Checkmark disabled/inactive | Condition holds | AFS step 3 | `is_folder_name_confirm_enabled()` is `False` | asserted |
| 4 Click checkmark → no effect | No-op | AFS step 4 | editor-open + input-unchanged + folder-row-absent + no-PUT assertions | asserted |
| 5 Click X icon → edit mode closed | Editor closes | **AFS step 5 (new)** | editor not-visible + no-PUT-on-close assertion | asserted (new) |
| 6 Verify folder name unchanged in list | Name unchanged | **AFS step 6 (new)** | `chat-folder-item-{id}` text content assertion | asserted (new) |
| Expected Final State: "Checkmark stays inactive when no changes are made; folder name is unchanged" | — | steps 3–6 | covered by the rows above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked`
/ `out-of-scope`. All rows resolved; steps 1–4 restate the covering spec's
existing Step-6 mechanism against a new (but source-proven-equivalent) test
method for traceability, steps 5–6 are the genuinely new assertions.

### Axis 2 — Analyst additions
- Step 5's cancel-close check asserts network silence in addition to the
  DOM-level "editor closes" signal, and separates it from step 6's
  list-display check into its own step — *added: same idiom as ELITEA-2122's
  Axis-2 rationale (disambiguates "closed with no network effect" from
  "closed after an instant no-op save").*
- Step 6 explicitly re-reads the folder row's text AFTER the editor has fully
  closed (not merely inferred from step 5's editor-closed signal) — *added:
  a regression that closed the editor UI-side but silently mutated the
  server-side name would slip past step 5 alone; step 6 is the independent
  ground-truth check.*
- Console-error check after the full flow — *added: standard side-channel
  discipline, same idiom as every sibling folder test in this file.*

## Cleanup
1. Delete the seeded folder via `ChatPage.delete_folder_via_api()` (same
   pattern as ELITEA-2121/2130/2122's own cleanup in this file — the UI
   dot-menu Delete path's testid is dead per issue #1309, unresolved as of
   this session, reconfirmed live during this session's own gap-check
   exploration).
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `chat-folder-name-input`,
`chat-folder-name-confirm-button` (`data-disabled` state attribute),
`chat-folder-name-cancel-button`, `chat-folder-menu-rename-menuitem`,
`conversation-menu-menu-button` (scoped), `chat-folder-item-{id}` — all
confirmed present and functioning on live localhost this session (fresh live
drive, folder id 242). No new handles needed.

## Network Behavior
- Zero new `PUT /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_id}`
  requests fire on either the no-op confirm-click (step 4) or the cancel-close
  (step 5) — live-confirmed this session via a `page.on('request', ...)`
  collector, same idiom the covering test and ELITEA-2122's test already use.

## Known Defects Found During Exploration
None. Live behavior matches the case's every expectation exactly.

## Blocked Steps
None. All 6 case steps are executable via existing, already-verified
page-object infrastructure (`open_folder_rename_editor()`,
`folder_name_confirm_button`, `folder_name_cancel_button`,
`get_folder_item()`) — no new handles or page-object methods needed.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- New test method on `TestChatFolderRenameCheckmarkValidation` in
  `test_chat_folder_rename_checkmark_validation.py` (mirrors the
  ELITEA-2121/2130/2122 method shape already in this file) — no new
  page-object methods needed. Reuse verbatim: `chat.navigate_to_chat()`,
  `chat.wait_for_page_load()`, `chat.click_create_folder_button()`,
  `chat.set_folder_name()`, `chat.folder_name_confirm_button` (seed +
  no-op-click check), `chat.get_folder_item()`,
  `chat.open_folder_rename_editor()`, `chat.folder_name_input`,
  `chat.folder_name_cancel_button`, `chat.delete_folder_via_api()`.
- Wait strategy: `page.expect_response()` for the seed-folder `POST`, same
  idiom as the file's existing tests. For the no-op-click and cancel-close
  checks, register a `page.on("request", ...)` PUT-collector BEFORE the
  interactions (same idiom as the existing tests' no-op-click checks) and
  assert the collected list is unchanged — do NOT use a raw sleep to "wait
  and see if a request appears."
- Coverage-tag mechanics: add a new `@allure.issue(...)` decorator (this
  case's own onetest-ai case-file URL) on the new method, matching the
  file's existing per-method tagging convention (ELITEA-2121/2130/2122 each
  carry their own single `@allure.issue`).
