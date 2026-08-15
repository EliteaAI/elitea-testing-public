# Test Case: Chat – Folder Creation with Custom Name via CHATS Header Icon

## Metadata
- **TMS ID**: ELITEA-2133
- **Source case**: `.agents/automation/chat-remaining-w05/cases/ELITEA-2133.md`
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

**Covering spec**: `automation/tests/ui/chat/test_chat_folder_creation_custom_name_and_cancel.py`
(class `TestChatFolderCreationCustomNameAndCancel`, method
`test_create_folder_with_custom_name`) — merged **onto this batch's trunk**
`tests/batch-chat-remaining-w05` (commit `ec4c9e29`, unit
ELITEA-2118/2119/2120), not yet merged to `origin/automation/base`. Per
`.agents/role-overrides.md` / `test-automation-workflow`'s merged-target
rule, `extend-existing` may target a spec already merged onto the batch's
own trunk — legitimate here because this unit rides the same trunk and
shares the batch's fate. AFS that authored the covering test:
`test-specs/chat-interface/l3_chat-folder-creation-custom-name-and-cancel_ELITEA-2119_2120.md`.

**Behavioural-overlap argument, confirmed LIVE this session (not assumed
from source alone)**: ELITEA-2133 and the already-merged ELITEA-2119 are the
same flow — "open the CHATS-header create-folder editor, replace the
default name with a custom name, click the checkmark, verify the folder is
created with that name" — differing only in the literal folder-name string
(ELITEA-2133's case data: "My Test Folder"; ELITEA-2119's chosen literal:
"My Sprint Folder"). Re-drove the identical flow live via Playwright MCP
against `http://localhost:5173` using ELITEA-2133's OWN test data before
writing this AFS (not reused from the ELITEA-2119 session): clicked the
CHATS-header folder icon, cleared the default name, typed "My Test Folder"
(`ControlOrMeta+a` + `pressSequentially`, replaced not appended), verified
the checkmark carried `data-disabled="false"`, clicked it — `POST
/api/v2/elitea_core/folder/prompt_lib/399` resolved `201`, and the new
folder rendered collapsed as "My Test Folder" plain text (`chat-folder-item-191`).
This is exactly what `test_create_folder_with_custom_name` already asserts
(case steps 1–3) — confirmed matching, not just assumed from the covering
test's own passing run.

**Gap this case fills**: case step 4 ("Click on the folder to expand it ->
Folder expands showing empty state") is **never exercised** by the covering
test — it stops at asserting the new folder renders **collapsed**
(`assert not chat.is_folder_expanded(folder_id)`), then proceeds straight to
cleanup. It never clicks the folder to expand it, and never reads the
empty-state text. This is a genuine, narrow coverage gap: a regression that
broke `expand_folder()` for a just-created folder, or broke the
`chat-folder-empty-state` rendering for a folder with zero conversations,
would not be caught by the existing test.

**Live-confirmed this session**: clicking the newly-created "My Test Folder"
row (`chat-folder-item-191`) flips `data-expanded` to `"true"` and reveals
region text **"No conversations added"**, scoped inside the folder's own
row (`chat-folder-empty-state` testid) — matching the same live-confirmed
empty-state text already documented in `test-specs/chat-interface/_surface.md`
§ Conversation deletion (ELITEA-2115/2116) for the "last conversation
deleted" case; here it is the "just-created, never populated" case, same
rendering path.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- User is on the Chats section (`${BASE_URL}/chat`).

## Test Data
### literal
- Custom folder name: `"My Test Folder"` (case's own value — NOT the
  covering test's `"My Sprint Folder"` constant; kept distinct so this
  case's own literal is genuinely exercised, not borrowed).

## Test Steps
1. Navigate to `${BASE_URL}/chat`; click the CHATS header folder-creation
   icon.
   - **Verify**: the inline "New folder" editor opens, pre-filled and
     focused. *(already-covered — covering test's own Step 1.)*
2. Clear the default name and type "My Test Folder".
   - **Verify**: input reads `"My Test Folder"` verbatim.
     *(already-covered — covering test's own Step 2, same mechanism,
     different literal — live-confirmed with this case's own literal this
     session.)*
3. Verify the checkmark icon is active.
   - **Verify**: `chat-folder-name-confirm-button` carries
     `data-disabled="false"`. *(already-covered — covering test's own
     Step 3.)*
4. Click the checkmark icon.
   - **Verify**: `POST /elitea_core/folder/prompt_lib/{project_id}` resolves
     `201`, response `name == "My Test Folder"`; folder appears collapsed
     in the list. *(already-covered — covering test's own Step 4/5.)*
5. Click on the folder to expand it.
   - **Verify (NEW)**: folder row flips `data-expanded="true"`; empty state
     region shows "No conversations added" — **not asserted by the
     covering test**, this is the gap this case closes.

## Expected Results
- Folder "My Test Folder" is created server-side with the exact custom name
  (already proven by the covering test).
- Expanding the newly-created, still-empty folder shows the
  `chat-folder-empty-state` empty state — newly proven by this extension.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: on Chats section | — | Setup | covering test's own navigation | already-covered |
| 1 Click folder icon in CHATS header | New folder entry appears in editable mode | AFS step 1 | covering test Step 1 (input pre-filled, focused) | already-covered |
| 2 Clear default name and type "My Test Folder" | Custom name in input | AFS step 2 | covering test Step 2 (same mechanism; re-confirmed live with this case's own literal) | already-covered |
| 3 Click the checkmark icon | Folder created with "My Test Folder" in the folder list | AFS steps 3–4 | covering test Steps 3–5 (`data-disabled="false"`, POST 201, folder visible collapsed) | already-covered |
| 4 Click on the folder to expand it | Folder expands showing empty state | AFS step 5 | **new appended assertion — `data-expanded="true"` + `chat-folder-empty-state` text** | asserted |
| Expected Final State: "Folder 'My Test Folder' created and is empty" | — | AFS steps 4–5 | covering test (created) + new step 5 (empty, confirmed by expanding) | asserted / already-covered |
| Pass/Fail: "All steps complete without errors" | — | all steps | covering test's own console-error side-channel check | already-covered |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked`
/ `out-of-scope`. Only row 4 (expand -> empty state) is newly `asserted` —
every other row is `already-covered` by the merged (on-trunk) covering test,
confirmed both via source read and via fresh live re-execution of this
case's own literal data this session.

### Axis 2 — Analyst additions
- None beyond the case's own step 4 — the appended assertion's sole purpose
  is closing that one gap; no additional assertions were added to avoid
  duplicating the covering test's already-established proof surface.

## Cleanup
The appended assertion runs inside the covering test's existing
`test_create_folder_with_custom_name`, which already deletes the folder it
creates in its `finally` block (`chat.delete_folder_via_menu(folder_id)`).
No additional cleanup needed — expanding the folder before that existing
teardown does not change what needs cleaning up.

Live-exploration folder ("My Test Folder", id 191) created this session was
deleted via the UI delete flow (dot-menu -> Delete -> confirm) before this
AFS was written, confirmed via a follow-up snapshot showing "The My Test
Folder folder has been successfully deleted." toast — no pollution left in
the shared DEV project by this analysis pass.

## Concrete Handles (discovered during exploration)
No new handles needed — every testid and page-object method this case's gap
requires already exists (added by ELITEA-2098/ELITEA-2115/ELITEA-2458) and
was confirmed live again this session:

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| CHATS header folder-creation icon | `[data-testid="chat-create-folder-button"]` | on-`main` ✓ | `chat.click_create_folder_button()`. |
| Folder-name inline input | `[data-testid="chat-folder-name-input"]` | on-`automation/testids` ✓ | `chat.folder_name_input`, `chat.set_folder_name()`. |
| Folder-name confirm (checkmark) button | `[data-testid="chat-folder-name-confirm-button"]` | on-`automation/testids` ✓ | `chat.folder_name_confirm_button`, `chat.is_folder_name_confirm_enabled()`. |
| Folder row (id-scoped, dynamic) | `[data-testid="chat-folder-item-{id}"]` | on-`automation/testids` ✓ | `chat.get_folder_item(folder_id)`, `chat.is_folder_expanded(folder_id)`, `chat.expand_folder(folder_id)`. |
| Folder empty-state text (id-scoped) | `[data-testid="chat-folder-empty-state"]` (scoped inside `chat-folder-item-{id}`) | on-`automation/testids` ✓ | `chat.get_folder_empty_state_text(folder_id)`. |

All handles verified live this session via Playwright MCP against the
actual running app (`chat-folder-item-191`'s `data-expanded` attribute and
its scoped empty-state text read directly from the accessibility snapshot),
not re-derived from the covering AFS's claims alone.

## Network Behavior
No new network call beyond what the covering test already asserts
(`POST /elitea_core/folder/prompt_lib/{project_id}` -> `201`). Expanding a
folder to view its empty state is a pure client-side render — no request
fires (confirmed: the covering test's cleanup `DELETE` is the only
additional request observed after the create `POST`/refresh `GET` pair).

## Known Defects Found During Exploration
None. The custom-name-save flow and the expand/empty-state rendering both
matched `FolderItem.jsx`'s documented behavior exactly — no case-text drift,
no reverse-masking needed.

## Blocked Steps
None. The gap was executable and confirmed live.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`).
- Page object: `automation/pages/chat_page.py` — no changes needed
  (`expand_folder()` / `get_folder_empty_state_text()` already exist,
  added ELITEA-2098/ELITEA-2115).
- See § Gap assertions below for the exact additive change to the covering
  spec.

## Gap assertions (implementer: append to the covering spec)

Two purely-additive changes to
`automation/tests/ui/chat/test_chat_folder_creation_custom_name_and_cancel.py`
— the existing test bodies stay byte-identical apart from this one
appended block inside `test_create_folder_with_custom_name`:

1. **Coverage tag chain**: add a second `@allure.issue(...)` decorator
   above `test_create_folder_with_custom_name`, citing ELITEA-2133's own
   case link, stacked alongside the existing ELITEA-2119 one (same
   double-`@allure.issue` precedent already used elsewhere in this feature
   area, e.g. `test_conversation_management.py::test_create_conversation_via_ui_button`).

   ```python
   @allure.issue(
       "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2119_chat-folder-name-edited-inline-during-creation-with-custom-name.md",
       "onetest-ai Test Case link",
   )
   @allure.issue(
       "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2133_chat-folder-creation-with-custom-name-via-chats-header-icon.md",
       "onetest-ai Test Case link",
   )
   @pytest.mark.p2
   def test_create_folder_with_custom_name(self, page):
   ```

2. **New Step 6** appended after the existing Step 5 block (inside the same
   `try:`, before the `finally:` cleanup), closing ELITEA-2133's own case
   step 4:

   ```python
       with allure.step(
           "Step 6 — Click the folder to expand it; verify it shows the "
           "empty state (ELITEA-2133 case step 4 — the gap this "
           "extension closes)"
       ):
           chat.expand_folder(folder_id, timeout=UI_ELEMENT_TIMEOUT)
           assert chat.is_folder_expanded(folder_id), (
               f"Folder {folder_id} should carry data-expanded=\"true\" "
               "after being clicked"
           )
           empty_state_text = chat.get_folder_empty_state_text(folder_id)
           assert "No conversations added" in empty_state_text, (
               f"Expanded empty folder {folder_id} should show the empty "
               f"state, got: {empty_state_text!r}"
           )
   ```

No new page-object methods, no new `LocatorDescriptor` fields — both
`expand_folder()` and `get_folder_empty_state_text()` already exist on
`ChatPage`. No new imports needed.
