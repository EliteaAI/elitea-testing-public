# Test Case: Chat – Create folder with custom name

## Metadata
- **TMS ID**: ELITEA-2457
- **Source case**: `.agents/automation/chat-remaining-w05/cases/ELITEA-2457.md`
  (snapshot; TMS module `chat-interface`)
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: high`, but the case is a
  near-total duplicate of the ELITEA-2119/2133 flow, already carried at
  `p2` on the covering test — kept at the covering test's existing
  `@pytest.mark.p2` so the tag-only extension doesn't fork priority markers
  mid-test)
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
ELITEA-2118/2119/2120; further extended by commit `aa77e07e`, unit
ELITEA-2133/2134), not yet merged to `origin/automation/base`. Per
`.agents/role-overrides.md` / `test-automation-workflow`'s merged-target
rule, `extend-existing` may target a spec already merged onto the batch's
own trunk. AFS chain: `test-specs/chat-interface/l3_chat-folder-creation-custom-name-and-cancel_ELITEA-2119_2120.md`
(original), `test-specs/chat-interface/lextend_chat-folder-creation-custom-name-expand-empty-state_ELITEA-2133.md`
(the extension that added the expand/empty-state assertion this case also
needs).

**Behavioural-overlap argument, confirmed LIVE this session (not assumed
from source alone)**: ELITEA-2457's six steps ("click the CHATS-header
folder icon -> verify a default-named editable input appears -> clear and
type a custom name -> click the checkmark -> verify the folder is created
with that name -> expand the folder and verify it is empty") are the
*identical* flow to ELITEA-2119 (steps 1–5) **plus** ELITEA-2133's own case
step 4 (expand + verify empty), which the covering test's `test_create_folder_with_custom_name`
already has as its own Step 6 (appended by the ELITEA-2133 extension,
commit `aa77e07e`) — differing only in the literal custom-name string
(ELITEA-2457's case data: "My Test Folder"; the covering test's existing
constant: "My Sprint Folder", ELITEA-2133's own literal was also "My Test
Folder" but that run's folder was deleted before this AFS, so this case's
own literal was independently re-driven, not assumed identical from a
shared id).

Re-drove the full flow live via Playwright MCP against
`http://localhost:5173` using ELITEA-2457's OWN test data before writing
this AFS:
1. Clicked `chat-create-folder-button` — the inline editor opened
   pre-filled and **focused** with the input reading `"New folder"`
   (confirmed via accessibility snapshot: `textbox [active]: New folder`)
   — this is ELITEA-2457's own case step 2, not independently asserted by
   `test_create_folder_with_custom_name` itself (that test's Step 1 only
   opens the editor; the default-name assertion lives in the separate,
   already-merged `test_folder_creation.py::test_create_folder_default_name_checkmark_active`,
   ELITEA-2118/2132).
2. Selected all (`ControlOrMeta+a`) + `pressSequentially("My Test Folder")`
   — input read `"My Test Folder"` verbatim (replaced, not appended).
3. Confirmed `chat-folder-name-confirm-button` carried
   `data-disabled="false"`.
4. Clicked it — `POST http://localhost:5173/api/v2/elitea_core/folder/prompt_lib/399`
   resolved `201`; the new folder rendered collapsed as `"My Test Folder"`
   plain text, testid `chat-folder-item-193`.
5. Clicked the folder row to expand it — `data-expanded` flipped to
   `"true"`; the scoped `chat-folder-empty-state` element read exactly
   `"No conversations added"`.
6. Cleaned up via the UI dot-menu (Delete -> confirm) — toast confirmed
   `"The My Test Folder folder has been successfully deleted."` — no
   pollution left in the shared DEV project by this analysis pass.

Every one of these six observations matches what `test_create_folder_with_custom_name`
already asserts end-to-end (its own Steps 1–6, the last of which was added
by the ELITEA-2133 extension) — this is a **complete duplicate observable**
for five of the case's six elements, plus one element (default-name-shown,
case step 2) that is already covered by a DIFFERENT, already-merged test on
this same trunk.

**Gap this case fills: none requiring new assertion code.** Case step 2
("verify the new folder input field appears with a default name") is
already asserted by `test_folder_creation.py::test_create_folder_default_name_checkmark_active`
(ELITEA-2118/2132, merged onto this trunk earlier in the batch); every
other step is already asserted, verbatim mechanism, by
`test_create_folder_with_custom_name`'s existing six steps. Per the
merged-target rule, `already-covered` cannot be used for the AFS's overall
`Status` here because the primary covering spec is merged onto the batch's
own trunk, not onto `origin/automation/base`; `extend-existing` is the
correct routing, and its allowed shape includes a **tag-only** extension —
the "Coverage tag chain" mechanic (§ Gap assertions below) with zero new
assertions, since there is nothing left to assert that either covering test
doesn't already prove.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- User is on the Chats section (`${BASE_URL}/chat`).

## Test Data
### literal
- Custom folder name: `"My Test Folder"` (case's own value — same literal
  ELITEA-2133 used, but re-driven independently this session with a fresh
  folder id, not assumed/reused from that prior run).

## Test Steps
1. Navigate to `${BASE_URL}/chat`; click the CHATS header folder-creation
   icon.
   - **Verify**: the inline "New folder" editor opens. *(already-covered —
     covering test's own Step 1.)*
2. Verify the new folder input field appears with a default name.
   - **Verify**: input reads `"New folder"`, focused. *(already-covered —
     `test_folder_creation.py::test_create_folder_default_name_checkmark_active`,
     ELITEA-2118/2132 — a DIFFERENT covering test on this same trunk;
     re-confirmed live this session via accessibility snapshot.)*
3. Clear the default name and type "My Test Folder".
   - **Verify**: input reads `"My Test Folder"` verbatim.
     *(already-covered — covering test's own Step 2, same mechanism,
     same literal as ELITEA-2133's constant — re-confirmed live this
     session with a fresh folder id.)*
4. Click the checkmark icon.
   - **Verify**: `POST /elitea_core/folder/prompt_lib/{project_id}`
     resolves `201`, response `name == "My Test Folder"`; folder appears
     collapsed in the list. *(already-covered — covering test's own Steps
     3–5.)*
5. Verify the folder is created with the name "My Test Folder" in the
   folder list.
   - **Verify**: folder row's `text_content()` contains "My Test Folder".
     *(already-covered — covering test's own Step 5.)*
6. Expand the folder and verify it is empty with no conversations inside.
   - **Verify**: `data-expanded="true"`; `chat-folder-empty-state` reads
     "No conversations added". *(already-covered — covering test's own
     Step 6, added by the ELITEA-2133 extension; re-confirmed live this
     session with this case's own literal/fresh folder id.)*

## Expected Results
- Folder "My Test Folder" is created server-side with the exact custom
  name, and expanding it shows the empty state — fully proven, end to end,
  by the covering test plus the sibling `test_folder_creation.py` test;
  nothing new to assert for this case's own literal beyond what's already
  covered.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: on Chats section | — | Setup | covering test's own navigation | already-covered |
| 1 Click folder icon in CHATS header | New page/section loads | AFS step 1 | covering test Step 1 | already-covered |
| 2 Verify new folder input appears with default name | Condition holds | AFS step 2 | `test_folder_creation.py::test_create_folder_default_name_checkmark_active` Step 2 (sibling covering test on this trunk; re-confirmed live) | already-covered |
| 3 Clear default name, type "My Test Folder" | Action completes, expected UI state | AFS step 3 | covering test Step 2 (same mechanism; re-confirmed live with this case's own literal) | already-covered |
| 4 Click the checkmark icon | Control responds; expected next state shown | AFS step 4 | covering test Steps 3–4 (`data-disabled="false"`, POST 201) | already-covered |
| 5 Verify folder is created with the name "My Test Folder" in the list | Condition holds | AFS step 5 | covering test Step 5 (folder row text content) | already-covered |
| 6 Expand the folder and verify it is empty with no conversations inside | Action completes, expected UI state | AFS step 6 | covering test Step 6, ELITEA-2133 extension (`data-expanded="true"` + `chat-folder-empty-state` text; re-confirmed live) | already-covered |
| Expected Final State: "Expand the folder and verify it is empty with no conversations inside" | — | AFS step 6 | covering test Step 6 | already-covered |
| Pass/Fail: "All steps complete without errors" | — | all steps | covering test's own console-error side-channel check | already-covered |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked`
/ `out-of-scope`. Every row is `already-covered` — confirmed both via
source read and via fresh live re-execution of this case's own literal data
this session (a full, independent run, not just a claim carried over from
ELITEA-2133's earlier session). No row is newly `asserted`; this extension
is coverage-tag-only.

### Axis 2 — Analyst additions
- None. No assertions were added beyond the case's own scope — both
  covering tests (the custom-name-and-expand flow, and the sibling
  default-name test) already fully satisfy it.

## Cleanup
The exploration folder ("My Test Folder", id `193`) created during this
session's live re-verification was deleted via the UI dot-menu (Delete ->
confirm) before this AFS was written — confirmed via a follow-up snapshot
showing "The My Test Folder folder has been successfully deleted." toast.
No cleanup is owed by the tag-only extension itself: it runs inside the
covering test's existing `test_create_folder_with_custom_name`, which
already deletes the folder it creates in its `finally` block.

## Concrete Handles (discovered during exploration)
No new handles needed — every testid and page-object method this case
requires already exists and was confirmed live again this session:

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| CHATS header folder-creation icon | `[data-testid="chat-create-folder-button"]` | on-`main` ✓ | `chat.click_create_folder_button()`. |
| Folder-name inline input | `[data-testid="chat-folder-name-input"]` | on-`automation/testids` ✓ | `chat.folder_name_input`, `chat.set_folder_name()`. |
| Folder-name confirm (checkmark) button | `[data-testid="chat-folder-name-confirm-button"]` | on-`automation/testids` ✓ | `chat.folder_name_confirm_button`, `chat.is_folder_name_confirm_enabled()`. |
| Folder row (id-scoped, dynamic) | `[data-testid="chat-folder-item-{id}"]` | on-`automation/testids` ✓ | `chat.get_folder_item(folder_id)`, `chat.is_folder_expanded(folder_id)`, `chat.expand_folder(folder_id)`. |
| Folder empty-state text (id-scoped) | `[data-testid="chat-folder-empty-state"]` (scoped inside `chat-folder-item-{id}`) | on-`automation/testids` ✓ | `chat.get_folder_empty_state_text(folder_id)`. |

All handles verified live this session via Playwright MCP against the
actual running app.

## Network Behavior
Confirmed live this session (`browser_network_requests`, filtered to
`folder/prompt_lib`): `POST .../folder/prompt_lib/399` -> `201` on
confirm, response `name == "My Test Folder"` — matches the covering test's
own assertion exactly. Expanding the folder to view its empty state fired
no additional request (pure client-side render), same as already documented
for the ELITEA-2133 extension.

## Known Defects Found During Exploration
None. The custom-name-save flow and the expand/empty-state rendering both
matched `FolderItem.jsx`'s documented behavior exactly for this case's own
literal test data — no case-text drift, no reverse-masking needed.

## Blocked Steps
None. Confirmed executable and fully overlapping live this session.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`).
- Page object: `automation/pages/chat_page.py` — no changes needed.
- See § Gap assertions below — tag-only, no test-body changes.

## Gap assertions (implementer: append to the covering spec)

**Coverage tag chain only — no new test code.** Add a third
`@allure.issue(...)` decorator above `test_create_folder_with_custom_name`
in
`automation/tests/ui/chat/test_chat_folder_creation_custom_name_and_cancel.py`,
citing ELITEA-2457's own case link, stacked alongside the existing
ELITEA-2119 and ELITEA-2133 ones (same multi-`@allure.issue` precedent
already used for `test_cancel_folder_creation_discards_folder`'s
ELITEA-2120/2134 pair). The test body stays byte-identical — every
assertion ELITEA-2457 needs is already there.

```python
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2119_chat-folder-name-edited-inline-during-creation-with-custom-name.md",
    "onetest-ai Test Case link",
)
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2133_chat-folder-creation-with-custom-name-via-chats-header-icon.md",
    "onetest-ai Test Case link",
)
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2457_chat-create-folder-with-custom-name.md",
    "onetest-ai Test Case link",
)
@pytest.mark.p2
def test_create_folder_with_custom_name(self, page):
```

No new page-object methods, no new `LocatorDescriptor` fields, no new
constants, no new imports.
