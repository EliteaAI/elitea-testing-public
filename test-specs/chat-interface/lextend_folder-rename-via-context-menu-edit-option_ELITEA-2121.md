# Test Case: Chat – Folder Rename via Edit Option in Context Menu

## Metadata
- **TMS ID**: ELITEA-2121
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private", observed live as `projectId=399` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer)
- **Status**: extend-existing
- **Extension target**: `automation/tests/ui/chat/test_chat_folder_rename_checkmark_validation.py` (its own AFS: `test-specs/chat-interface/l2_chat-folder-rename-checkmark-validation_ELITEA-2458.md`)

**Regression found and fixed BEFORE this case could even be attempted.** `FolderItem.jsx`'s
dot-menu "Rename" item's `key: 'chat-folder-menu-rename'` — added by ELITEA-2458
(commit `0298860f`) — had been silently dropped by a later, unrelated main-branch feature
commit (`f5e0c325`, "Restore user message to input field when Stop is clicked (#764)",
2026-08-13), which replaced `FolderItem.jsx`'s `menuItems` array wholesale to add a new
"New chat" item and lost the sibling `key` in the process. **Confirmed via a LIVE pytest
run, not just source inspection**: `test_chat_folder_rename_checkmark_validation.py`'s
own (previously merged, previously green) test failed with
`playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded`
waiting for `chat-folder-menu-rename-menuitem` before this fix. Filed as
[elitea-testing-public#1533](https://github.com/EliteaAI/elitea-testing-public/issues/1533)
(sibling regression to the already-tracked `#1309`, same failure shape — a shared
`menuItems` array literal edited by unrelated feature work, dropping a sibling item's
`key`). Fixed this session by re-adding `key: 'chat-folder-menu-rename'` — landed on
`automation/testids`, `EliteaAI/EliteaUI@be489cee` — and live-reverified: the
previously-failing test now passes cleanly (41s). **This case (and ELITEA-2130) could
not have been automated at all without this fix** — both need the dot-menu → Rename
path as their very first interactive step.

This case's own flow (open editor via dot-menu → Rename, type one valid new name
directly, confirm) is a near-total SUBSET of ELITEA-2458's own 9-step boundary-testing
flow (which already exercises: dot-menu → Rename opens the editor pre-filled — case
step 1; clearing the input — case step 2; typing a valid, changed name — case steps
4/7 combined into one direct type here; clicking the active checkmark — case step 9;
`PUT … → 200` — Network Behavior). The one case element ELITEA-2458 does NOT cover is
this case's own step 2 — verifying the context-menu's item SET on open (ELITEA-2458
never inspects menu content, only clicks straight through to Rename). Routed
`extend-existing` against `test_chat_folder_rename_checkmark_validation.py` — one new
test method appended, tag-chained via a second `@allure.issue` reference; the existing
two methods (ELITEA-2458, ELITEA-2459) are untouched.

**Case-text drift found, filed separately as clarification, NOT part of this AFS's own
scope beyond noting it:** case step 2 says "verify context menu: Delete, Edit, Export,
Pin or Unpin". Live-confirmed this session (both via `FolderItem.jsx` source read and a
live `browser_snapshot` of the open menu) the REAL item set is **New chat, Rename, Pin
on top (or Unpin), Delete** — 4 items. "Edit" doesn't exist (the item is labelled
"Rename", same drift already documented for the sibling `ConversationItem.jsx` menu,
see `#1513`/ELITEA-2099's clarification); "Export" doesn't exist at all on the folder
dot-menu; "New chat" exists but isn't mentioned by the case. Filed as
[elitea-testing-public#1534](https://github.com/EliteaAI/elitea-testing-public/issues/1534).
This AFS asserts the REAL, live-confirmed item set (Rename + Pin/Unpin, by their
testids — New chat and Delete are not asserted, neither is functionally exercised by
this case's own flow), not the case's literal (wrong) list.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- User is on the Chats section (`${BASE_URL}/chat`).
- At least one folder exists that the test owns (this case seeds its own folder — see
  § Test Data — rather than reusing a shared one, so the "hover reveals 3-dot icon" and
  "renamed name displayed" assertions have a known, controlled starting value; the
  shared DEV project already carries extensive pre-existing folder-name pollution from
  earlier analyst passes, documented in the ELITEA-2458 AFS).

## Test Data

### generate-per-test (created by the test's own setup, cleaned up in its own teardown)
- One folder, created via the existing `click_create_folder_button()` +
  `set_folder_name(<name>)` + `folder_name_confirm_button.click()` flow (ELITEA-2132's
  create path, already reused verbatim by ELITEA-2458), with a deterministic seed name —
  `"ELITEA2121RenameSource"` (live-verified value used this session, folder id `212` at
  exploration time — ephemeral, a fresh id is minted per run).
- New name from the case's own § Test Data table: `"New folder_edited"`.

## Test Steps

1. Navigate to `${BASE_URL}/chat`, seed the folder (§ Test Data), then hover the folder
   row.
   - **Verify**: the folder's 3-dot menu button becomes visible (CSS-hover-revealed —
     `CONVERSATION_MENU_BUTTON`, scoped inside `chat-folder-item-{folder_id}`; the
     button exists in the DOM at all times but per `ConversationItem.jsx`'s sibling
     pattern — confirmed for folders too — is only interactable once the row is hovered).
2. Click the 3-dot icon; verify the context menu becomes visible and shows the REAL
   item set (not the case's literal, drifted list — see the intro paragraph and
   `#1534`).
   - **Verify**: the popover (`conversation-menu-menu`) is visible; the "Rename"
     item (`chat-folder-menu-rename-menuitem`) and the "Pin on top" item
     (`chat-folder-menu-pin-menuitem`, showing "Pin on top" — this folder isn't
     pinned) are both present.
3. Click the "Rename" item.
   - **Verify**: the inline editor opens — `chat-folder-name-input` is visible and
     pre-filled with the folder's current name (`ELITEA2121RenameSource`).
4. Clear the current name and type `"New folder_edited"`.
   - **Verify**: the input shows `"New folder_edited"`.
5. Click the checkmark icon.
   - **Verify**: `PUT /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_id}`
     resolves `200 OK`; the editor closes; `chat-folder-item-{folder_id}`'s displayed
     name now reads `"New folder_edited"`.
6. Verify no error message is shown.
   - **Verify**: no unexpected console errors fired across the whole flow (the
     environment-wide, pre-existing `secrets/secrets/default` 403 noise, documented in
     every sibling folder test, is filtered).

## Expected Results
- Hovering a folder reveals its 3-dot menu button; clicking it opens a context menu
  containing (among other, case-irrelevant items) "Rename" and "Pin on top"/"Unpin".
- Clicking "Rename" opens the same shared inline editor `FolderItem.jsx` renders for
  both create and rename, pre-filled with the folder's current name.
- Typing a new valid name and clicking the (now-active) checkmark persists the rename
  server-side (`PUT … → 200`) and updates the folder's displayed name immediately.
- No new console errors beyond the pre-existing, environment-wide `secrets` 403 noise.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: at least one folder exists | — | Setup | test seeds its own folder | asserted |
| 1 Hover folder | 3-dot icon appears | AFS step 1 | step 1: menu button visible | asserted |
| 2 Click 3-dot, verify menu: Delete/Edit/Export/Pin-or-Unpin | Context menu visible | AFS step 2 | step 2: popover visible + real item set (Rename, Pin/Unpin) asserted — case's literal 4-item list is drifted, see intro + `#1534` | asserted *(case-text drift, clarification filed, real behavior asserted)* |
| 3 Click Edit | Folder name editable, checkmark + X icons | AFS step 3 (as "Rename" — drift) | step 3: editor open, pre-filled | asserted |
| 4 Clear + type 'New folder_edited' | New name appears in input | AFS step 4 | step 4: input value | asserted |
| 5 Click checkmark | Folder renamed; new name displayed | AFS step 5 | step 5: `PUT → 200`, displayed name | asserted |
| 6 Verify no error message | Rename applied successfully | AFS step 6 | step 6: console-error check | asserted |
| Expected Final State: "Folder is renamed to 'New folder_edited'" | — | step 5 | covered by the row above | asserted |
| Pass/Fail: "All steps complete without errors" | — | all steps | console-check after the full flow | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` /
`out-of-scope`. All rows `asserted`. No reverse-masking: the ONE case-text/product
mismatch (menu item labels) is handled per the Hard Rules' reverse-masking guard — the
AFS asserts the LIVE-CONFIRMED item set, not the case's stale literal list, and the
drift itself is filed as a clarification rather than silently "fixed" in the test with
no record.

### Axis 2 — Analyst additions

- Step 2 asserts the popover's real item set via the NEWLY-testid'd Rename/Pin items
  rather than the case's literal (wrong) 4-item list — *added: asserting a list the
  product doesn't actually show would either fail-for-the-wrong-reason or require a
  weakened/text-based check; per the reverse-masking guard, asserting the live-confirmed
  reality is correct, with the drift filed separately (`#1534`) so the TMS case itself
  gets fixed.*
- Console-error check after the full flow — *added: standard side-channel discipline,
  same idiom as every sibling folder test in this file.*
- (nothing else added beyond the case — this case's remaining steps map 1:1 onto
  ELITEA-2458's already-covered mechanism, reused here as a single direct
  type-and-confirm rather than re-proving the boundary states ELITEA-2458 already owns.)

## Cleanup
1. Delete the seeded folder via `ChatPage.delete_folder_via_api()` directly (NOT
   `delete_folder_via_menu()`'s UI path — its target testid,
   `chat-folder-menu-delete-menuitem`, remains dead per the still-open `#1309`; this
   case's own scope is Rename/Pin, not Delete, so no attempt was made to fix that
   separate regression).
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is testid-only (`.agents/testing.md` § Locator policy).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Folder dot-menu button (3-dot) | `[data-testid="conversation-menu-menu-button"]`, scoped inside `chat-folder-item-{folder_id}` | on-`main` ✓ | Pre-existing (ELITEA-2132), reused verbatim. |
| Folder dot-menu "Rename" item | `[data-testid="chat-folder-menu-rename-menuitem"]` | **RESTORED this session** — added by ELITEA-2458 (`0298860f`), regressed by main commit `f5e0c325`, re-added `EliteaAI/EliteaUI@be489cee` (`automation/testids` only — not yet on `main`, standard human-cherry-pick promotion pending). | See intro paragraph + `#1533`. |
| Folder dot-menu "Pin on top"/"Unpin" item | `[data-testid="chat-folder-menu-pin-menuitem"]` | **NEW this session**, `EliteaAI/EliteaUI@be489cee` (`automation/testids` only). | Added `key: 'chat-folder-menu-pin'` to `FolderItem.jsx`'s Pin/Unpin menu item — this case's own flow references it only to assert its presence/label in step 2 (doesn't click it; that's ELITEA-2130's own flow). |
| Folder-name inline input / confirm button / row | `chat-folder-name-input` / `chat-folder-name-confirm-button` / `chat-folder-item-{id}` | on-`automation/testids` ✓, on-`main` ✗ | Pre-existing (ELITEA-2132/2458), reused verbatim. |

## Network Behavior
- `PUT /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_id}` → `200 OK` on
  confirm click (step 5). Live-observed this session: folder id `212`,
  `PUT .../folder/prompt_lib/399/212 => [200] OK`, response name confirmed
  `"New folder_edited"` server-side via the subsequent
  `GET .../folder/prompt_lib/{project_id}?...` refetch.
- `POST /api/v2/elitea_core/folder/prompt_lib/{project_id}` → `201 Created` — seed-folder
  creation only (setup, not the case's own observable).

## Known Defects Found During Exploration
One REGRESSION found and FIXED before this case could be attempted at all — see intro
paragraph and `#1533` (this case's own flow depends on the fix, so it's blocking, not
isolated — fixed rather than worked around). One case-text drift found and filed as
clarification `#1534` (menu item labels/set) — not a product defect, the menu is fully
functional.

## Blocked Steps
None, after the `#1533` regression fix. All 6 case steps were executable and confirmed
live end-to-end (folder id `212`, renamed `ELITEA2121RenameSource` → `"New folder_edited"`,
`PUT → 200`, 0 console errors across the whole session).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Page object: extend `automation/pages/chat_page.py`. Reuse `open_folder_rename_editor()`,
  `folder_name_input`, `folder_name_confirm_button`, `set_folder_name()`,
  `get_folder_item()`, `click_create_folder_button()`, `delete_folder_via_api()` verbatim
  — all pre-existing. New additions needed:
  - `FOLDER_MENU_PIN_ITEM = '[data-testid="chat-folder-menu-pin-menuitem"]'` (class
    constant, mirrors `FOLDER_MENU_RENAME_ITEM`'s shape).
  - `open_folder_context_menu(folder_id, timeout)` — hover `FOLDER_ICON` + click the
    scoped dot-menu button (the SAME hover-then-open sequence
    `open_folder_rename_editor()`/`delete_folder_via_menu()` already duplicate inline —
    factored out here as a small, purely-additive new method so this test and
    ELITEA-2130's can both open the menu WITHOUT immediately clicking an item, to
    assert its content first).
- Step 2's menu-content assertion: after `open_folder_context_menu()`, assert
  `page.locator('[data-testid="conversation-menu-menu"]')` is visible, then assert the
  Rename and Pin items are visible via their own testid locators (`FOLDER_MENU_RENAME_ITEM`
  / `FOLDER_MENU_PIN_ITEM`) — do NOT assert the case's literal 4-item list.
- Wait strategy: `page.expect_response()` for both the seed-folder `POST` and the
  rename `PUT`, same idiom as `test_chat_folder_rename_checkmark_validation.py`.
