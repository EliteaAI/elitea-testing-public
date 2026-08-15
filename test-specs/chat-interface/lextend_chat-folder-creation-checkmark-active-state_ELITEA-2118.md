# Test Case: Chat – Folder Name Edited Inline During Creation with Default Name Saved

## Metadata
- **TMS ID**: ELITEA-2118
- **Source case**: `.agents/automation/chat-remaining-w05/cases/ELITEA-2118.md`
  (snapshot; TMS module `chat-interface`)
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` -> `p2`, same class
  as the covering test's own `@pytest.mark.p2` decorator)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids`, DEV backend; project "Private", `projectId=399`,
  `${ELITEA_PROJECT_ID}`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN`
  skips explicit Keycloak login
- **Analyst**: test-automation-engineer (agent), combined analyst+implementer slot
- **Status**: extend-existing

## Extension target

**Covering spec**: `automation/tests/ui/chat/test_folder_creation.py`
(class `TestChatFolderCreation`, method `test_create_folder_via_chats_header_icon`),
merged to `origin/automation/base`, AFS
`test-specs/chat-interface/l3_chat-folder-creation-via-chats-header-icon_ELITEA-2132.md`.

**Behavioural-overlap argument, confirmed LIVE this session (not assumed from
source alone)**: the covering test already exercises every step of this case
except one — it navigates to Chats (case step 1), opens the folder editor
with the default "New folder" name pre-filled (case step 2/3), clicks the
confirm checkmark without changing the name and verifies the POST resolves
201 with `name == "New folder"` (case step 5), and verifies the editor
closes and the name renders as plain text (case step 6). **Live-confirmed
this session** by re-driving the identical flow via Playwright MCP against
`http://localhost:5173`: opening the create-folder editor pre-fills
`"New folder"`, focused; clicking confirm without changes fires
`POST /elitea_core/folder/prompt_lib/399` -> `201`; the folder then renders
collapsed with the default name as plain text — all matching both the case
text and the covering test's own assertions exactly.

**Gap this case fills**: case step 4 ("Verify the checkmark icon is active
(default name meets 3 char minimum)") is never asserted by the covering
test — it only asserts the confirm/cancel icons are **visible** (Step 4 of
`test_create_folder_via_chats_header_icon`), never their **enabled/active
state** (`data-disabled` attribute, added by ELITEA-2458 on the same
pre-existing `chat-folder-name-confirm-button` testid). This is a genuine,
narrow coverage gap, not a duplicate: the covering test never fails if a
regression made the checkmark inactive-yet-still-clickable (or if the click
handler bypassed the `isFolderSaveEnabled` gate), because it never reads the
attribute.

**Live-confirmed this session**: immediately after opening the create-folder
editor (default name "New folder", untouched), `chat-folder-name-confirm-button`
carries `data-disabled="false"` (active) — read via
`document.querySelector(...).getAttribute('data-disabled')` against the live
DOM. `FolderItem.jsx`'s `isFolderSaveEnabled = isFolderNameValid &&
(isNewFolder || folderName !== name)` — for a NEW folder (`isNewFolder ===
true`) the `(isNewFolder || …)` clause short-circuits true, so the gate
collapses to `isFolderNameValid` alone (no "changed" requirement, unlike the
rename path `test_chat_folder_rename_checkmark_validation.py` exercises) —
"New folder" (10 chars, all within `ConversationNameRegExp`'s allowed
charset) is valid, hence active immediately, with no typing required.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- User is on the Chats section (`${BASE_URL}/chat`).

## Test Data
### literal
- None required (case explicitly keeps the default "New folder" name).

## Test Steps
1. Navigate to `${BASE_URL}/chat`; click the CHATS header folder-creation
   icon.
   - **Verify**: the inline "New folder" editor opens, pre-filled and
     focused. *(already-covered — the covering test's own Step 3 asserts
     this identically.)*
2. Do not change the default name.
   - **Verify**: `chat-folder-name-input` still reads `"New folder"`.
     *(already-covered — implicit in the covering test, nothing is typed
     between its Step 3 and Step 5.)*
3. Verify the checkmark icon is active (default name meets the 3-char
   minimum).
   - **Verify (NEW)**: `chat-folder-name-confirm-button` carries
     `data-disabled="false"` — **not asserted by the covering test**, this
     is the gap this case closes.
4. Click the checkmark icon.
   - **Verify**: `POST /elitea_core/folder/prompt_lib/{project_id}` resolves
     `201`, response `name == "New folder"`. *(already-covered — the
     covering test's own Step 5.)*
5. Verify the input field closes and the folder name is displayed as plain
   text.
   - **Verify**: `chat-folder-name-input` hidden; the new folder's row shows
     "New folder" as plain text. *(already-covered — the covering test's own
     Step 5/Step 6.)*

## Expected Results
- The confirm checkmark is provably ACTIVE (`data-disabled="false"`) for the
  untouched default name at folder-creation time — proving
  `isFolderSaveEnabled`'s `isNewFolder` short-circuit branch, not just its
  `changed` branch (which the sibling rename-checkmark-validation test
  already covers).
- Everything else in this case (editor opens pre-filled, confirm saves with
  the default name, editor closes, name renders as plain text) is already
  proven by the covering test — reasserting it here would duplicate that
  proof without adding coverage.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: on Chats section | — | Setup | covering test's own navigation | already-covered |
| 1 Navigate to Chats section | Chats section is displayed | AFS step 1 | covering test Step 1 (`conversations_panel_heading` visible) | already-covered |
| 2 Click folder icon to create new folder | New folder entry appears, editable, default name | AFS step 1 | covering test Step 3 (input pre-filled `"New folder"`, focused) | already-covered |
| 3 Do not change default name | Default name remains in input | AFS step 2 | covering test — nothing typed between Step 3 and Step 5, input untouched | already-covered |
| 4 Verify checkmark icon is active (3-char minimum) | Checkmark is active | AFS step 3 | **new appended test — `data-disabled="false"` asserted directly** | asserted |
| 5 Click the checkmark icon | Folder saved with default name, appears in folder list | AFS step 4 | covering test Step 5 (`POST` -> `201`, `name == "New folder"`, folder item visible) | already-covered |
| 6 Verify input field closes, name shown as plain text | Folder name shows as plain text | AFS step 5 | covering test Step 5/6 (`folder_name_input` hidden, name in `text_content()`) | already-covered |
| Expected Final State: "Folder is saved with the default name" | — | AFS step 4 | covering test Step 5/6 | already-covered |
| Pass/Fail: "All steps complete without errors" | — | all steps | covering test's own console-error side-channel check | already-covered |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked`
/ `out-of-scope`. Only row 4 (checkmark-active state) is newly `asserted` —
every other row is `already-covered` by the merged covering test, confirmed
both via source read (unchanged since ELITEA-2132/ELITEA-2458) and via fresh
live re-execution of this case's own flow this session.

### Axis 2 — Analyst additions
- None beyond the case's own step 4 — the appended test's sole purpose is
  closing that one gap; no additional assertions were added to avoid
  duplicating the covering test's already-established proof surface.

## Cleanup
The appended test opens the create-folder editor and immediately closes it
via the CANCEL icon (not confirm) — it never creates a real folder, so there
is nothing to delete. This keeps the gap-closing test minimal and avoids
adding a third folder-creation flow to the shared DEV project's already
heavily-polluted folder list (documented in `test-specs/chat-interface/_surface.md`
§ Folder rename editor — `set_folder_name()`'s "append not replace" race).

## Concrete Handles (discovered during exploration)
No new handles needed — every testid and page-object method this case's gap
requires already exists, added by ELITEA-2132/ELITEA-2458 and confirmed live
again this session:

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| CHATS header folder-creation icon | `[data-testid="chat-create-folder-button"]` | on-`main` ✓ | `chat.click_create_folder_button()`. |
| Folder-name inline input | `[data-testid="chat-folder-name-input"]` | on-`automation/testids` ✓ | `chat.folder_name_input`. |
| Folder-name confirm (checkmark) button | `[data-testid="chat-folder-name-confirm-button"]` | on-`automation/testids` ✓ | `chat.folder_name_confirm_button`, `chat.is_folder_name_confirm_enabled()` (reads `data-disabled`, added ELITEA-2458). |
| Folder-name cancel (X) button | `[data-testid="chat-folder-name-cancel-button"]` | on-`automation/testids` ✓ | `chat.folder_name_cancel_button`. |

All handles verified live this session via direct DOM query
(`document.querySelector('[data-testid="..."]')`) against the actual
running app, not re-derived from the covering AFS's claims alone.

## Network Behavior
No network call is expected from the appended test — it opens the editor,
reads the `data-disabled` attribute, then cancels (no POST). The covering
test already asserts the `POST` -> `201` behavior for this exact flow.

## Known Defects Found During Exploration
None. The checkmark's active state for the untouched default name matches
`FolderItem.jsx`'s `isFolderSaveEnabled` logic exactly (`isNewFolder` branch
short-circuits true) — no case-text drift, no reverse-masking needed.

## Blocked Steps
None. The gap was executable and confirmed live.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`).
- Page object: `automation/pages/chat_page.py` — no changes needed.
- See § Gap assertions below for the exact additive test method to append to
  the covering spec.

## Gap assertions (implementer: append to the covering spec)

Add a **new, independent `test()` method** to
`automation/tests/ui/chat/test_folder_creation.py`'s `TestChatFolderCreation`
class — purely additive, the existing `test_create_folder_via_chats_header_icon`
body stays byte-identical. Decorate with `@pytest.mark.p2` (matching the
existing test's own per-function decorator).

```python
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2118_chat-folder-name-edited-inline-during-creation-with-default-name-saved.md",
    "onetest-ai Test Case link",
)
@pytest.mark.p2
def test_create_folder_default_name_checkmark_active(self, page):
    """ELITEA-2118 — closes the one gap in ELITEA-2132's own coverage: the
    confirm (checkmark) icon is explicitly proven ACTIVE for the untouched
    default "New folder" name at folder-creation time
    (data-disabled="false"), which test_create_folder_via_chats_header_icon
    never asserts (it only checks icon VISIBILITY). Every other step of
    this case (editor opens pre-filled, confirm saves with the default
    name, editor closes, name renders as plain text) is already proven by
    that covering test — not re-asserted here. Opens the editor and closes
    it via CANCEL (never confirms) so this test creates no real folder and
    needs no cleanup.
    """
    chat = ChatPage(page)

    with allure.step("Step 1 — Navigate to chat, open the create-folder editor"):
        chat.navigate_to_chat()
        chat.wait_for_page_load()
        chat.click_create_folder_button(timeout=UI_ELEMENT_TIMEOUT)

    with allure.step(
        "Step 2 — Verify the default name remains unchanged in the input"
    ):
        assert chat.folder_name_input.input_value() == DEFAULT_FOLDER_NAME, (
            f"Input should still read {DEFAULT_FOLDER_NAME!r} — untouched"
        )

    with allure.step(
        "Step 3 — Verify the checkmark icon is ACTIVE for the untouched "
        "default name (case step 4 — the gap this test closes)"
    ):
        assert chat.is_folder_name_confirm_enabled(), (
            'chat-folder-name-confirm-button should carry '
            'data-disabled="false" for the untouched default name '
            f"{DEFAULT_FOLDER_NAME!r} (3-char minimum satisfied, "
            "isNewFolder short-circuits the change-requirement)"
        )

    with allure.step(
        "Cleanup — close the editor via cancel; no folder was created"
    ):
        chat.folder_name_cancel_button.click()
        chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
```

No new page-object methods, no new `LocatorDescriptor` fields, no new
module-level constants beyond what the covering spec already defines
(`DEFAULT_FOLDER_NAME`, `UI_ELEMENT_TIMEOUT`, `ChatPage`, `allure`, `pytest`
are all already imported/defined in the covering spec file — no new imports
needed).
