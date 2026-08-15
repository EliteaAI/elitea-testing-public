# Test Case: Chat – Folder Creation Cancel Discards New Folder

## Metadata
- **TMS ID**: ELITEA-2134
- **Source case**: `.agents/automation/chat-remaining-w05/cases/ELITEA-2134.md`
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
`test_cancel_folder_creation_discards_folder`) — merged **onto this batch's
trunk** `tests/batch-chat-remaining-w05` (commit `ec4c9e29`, unit
ELITEA-2118/2119/2120), not yet merged to `origin/automation/base`. Per the
merged-target rule, `extend-existing` may target a spec already merged onto
the batch's own trunk. AFS that authored the covering test:
`test-specs/chat-interface/l3_chat-folder-creation-custom-name-and-cancel_ELITEA-2119_2120.md`.

**Behavioural-overlap argument, confirmed LIVE this session (not assumed
from source alone)**: ELITEA-2134 and the already-merged ELITEA-2120 are the
*identical* flow with no divergence in steps or expected results — "open
the CHATS-header create-folder editor, type a name, click the X (cancel)
icon, verify no folder with that name appears, verify the folder list is
unchanged" — differing only in the literal discarded-name string
(ELITEA-2134's case data: "Cancelled Folder"; ELITEA-2120's chosen literal:
"Temp Folder"). Re-drove the identical flow live via Playwright MCP against
`http://localhost:5173` using ELITEA-2134's OWN test data before writing
this AFS: clicked the CHATS-header folder icon, typed "Cancelled Folder"
(`ControlOrMeta+a` + `pressSequentially`), clicked the X (cancel) icon —
confirmed via `browser_network_requests` that **zero** new requests fired to
`folder/prompt_lib` across the whole flow (the last `folder/prompt_lib`
entries in the network log predate this attempt entirely), and confirmed
"Cancelled Folder" appears nowhere in the resulting accessibility snapshot.
This exactly matches every assertion `test_cancel_folder_creation_discards_folder`
already makes (`get_folder_names_containing()` empty, folder count
unchanged, zero POSTs observed).

**Gap this case fills: none.** Every step and expected result of ELITEA-2134
is already asserted by the covering test's existing method — this is a
**complete duplicate observable**, not a partial-overlap case. Per the
merged-target rule, `already-covered` cannot be used here because the
covering spec is merged onto the batch's own trunk, not onto
`origin/automation/base` (that verdict is terminal and requires a base-merged
target); `extend-existing` is the correct routing for a same-batch-trunk
target, and its allowed shape includes a **tag-only** extension — the
"Coverage tag chain" mechanic (§ Gap assertions below) with zero new
assertions, since there is nothing left to assert.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- User is on the Chats section (`${BASE_URL}/chat`).

## Test Data
### literal
- Discarded folder name: `"Cancelled Folder"` (case's own value — NOT the
  covering test's `"Temp Folder"` constant; kept distinct so this case's own
  literal is genuinely exercised, not borrowed, even though no new
  assertion is added).

## Test Steps
1. Navigate to `${BASE_URL}/chat`; click the CHATS header folder-creation
   icon.
   - **Verify**: the inline "New folder" editor opens. *(already-covered —
     covering test's own Step 1.)*
2. Type "Cancelled Folder".
   - **Verify**: input reads `"Cancelled Folder"` verbatim.
     *(already-covered — covering test's own Step 2, same mechanism,
     different literal — live-confirmed with this case's own literal this
     session.)*
3. Click the X (cancel) icon.
   - **Verify**: input closes without saving. *(already-covered — covering
     test's own Step 3.)*
4. Verify no folder named "Cancelled Folder" is added to the list.
   - **Verify**: `get_folder_names_containing("Cancelled Folder")` is empty.
     *(already-covered — covering test's own Step 4, same mechanism.)*
5. Verify the folder list remains unchanged.
   - **Verify**: folder count before == after; no new POST to
     `folder/prompt_lib` fired. *(already-covered — covering test's own
     Step 5.)*

## Expected Results
- No new folder is created after cancelling — fully proven by the covering
  test; nothing new to assert for this case's own literal beyond what's
  already covered.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: on Chats section | — | Setup | covering test's own navigation | already-covered |
| 1 Click folder icon in CHATS header | New folder input appears | AFS step 1 | covering test Step 1 | already-covered |
| 2 Type "Cancelled Folder" | Name in input | AFS step 2 | covering test Step 2 (same mechanism; re-confirmed live with this case's own literal) | already-covered |
| 3 Click the X (cancel) icon | Input closes without saving | AFS step 3 | covering test Step 3 | already-covered |
| 4 Verify no folder named "Cancelled Folder" added | Folder not created | AFS step 4 | covering test Step 4 (`get_folder_names_containing()` empty; re-confirmed live) | already-covered |
| 5 Verify folder list remains unchanged | Folder list unchanged | AFS step 5 | covering test Step 5 (count unchanged, zero POSTs; re-confirmed live via `browser_network_requests`) | already-covered |
| Expected Final State: "No new folder is created after cancelling" | — | AFS steps 4–5 | covering test Steps 4–5 | already-covered |
| Pass/Fail: "All steps complete without errors" | — | all steps | covering test's own console-error side-channel check | already-covered |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked`
/ `out-of-scope`. Every row is `already-covered` — confirmed both via source
read and via fresh live re-execution of this case's own literal data this
session. No row is newly `asserted`; this extension is coverage-tag-only.

### Axis 2 — Analyst additions
- None. No assertions were added beyond the case's own scope, which the
  covering test already fully satisfies.

## Cleanup
No folder is ever created by this flow (cancel fires zero requests) — no
cleanup needed, same as the covering test's own cancel scenario. Nothing
created during this session's live re-verification either (confirmed via
`browser_network_requests` — zero POSTs to `folder/prompt_lib` across the
whole cancel attempt).

## Concrete Handles (discovered during exploration)
No new handles needed — every testid and page-object method this case
requires already exists and was confirmed live again this session:

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| CHATS header folder-creation icon | `[data-testid="chat-create-folder-button"]` | on-`main` ✓ | `chat.click_create_folder_button()`. |
| Folder-name inline input | `[data-testid="chat-folder-name-input"]` | on-`automation/testids` ✓ | `chat.folder_name_input`, `chat.set_folder_name()`. |
| Folder-name cancel (X) button | `[data-testid="chat-folder-name-cancel-button"]` | on-`automation/testids` ✓ | `chat.folder_name_cancel_button`. |

All handles verified live this session via Playwright MCP against the
actual running app.

## Network Behavior
Confirmed live this session (`browser_network_requests`, filtered to
`folder/prompt_lib`): the cancel click fires **zero** new requests — matches
the covering test's own assertion exactly (same client-side-only discard
already documented for the conversation-rename cancel path,
`test-specs/chat-interface/_surface.md` § Folder creation inline editor).

## Known Defects Found During Exploration
None. The cancel-discard flow matched `FolderItem.jsx`'s documented
behavior exactly for this case's own literal test data — no case-text
drift, no reverse-masking needed.

## Blocked Steps
None. Confirmed executable and fully overlapping live this session.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`).
- Page object: `automation/pages/chat_page.py` — no changes needed.
- See § Gap assertions below — tag-only, no test-body changes.

## Gap assertions (implementer: append to the covering spec)

**Coverage tag chain only — no new test code.** Add a second
`@allure.issue(...)` decorator above `test_cancel_folder_creation_discards_folder`
in
`automation/tests/ui/chat/test_chat_folder_creation_custom_name_and_cancel.py`,
citing ELITEA-2134's own case link, stacked alongside the existing
ELITEA-2120 one (same double-`@allure.issue` precedent already used
elsewhere in this feature area, e.g.
`test_conversation_management.py::test_create_conversation_via_ui_button`).
The test body stays byte-identical — every assertion ELITEA-2134 needs is
already there.

```python
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2120_chat-folder-name-edited-inline-during-creation-cancel-discards-folder.md",
    "onetest-ai Test Case link",
)
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2134_chat-folder-creation-cancel-discards-new-folder.md",
    "onetest-ai Test Case link",
)
@pytest.mark.p2
def test_cancel_folder_creation_discards_folder(self, page):
```

No new page-object methods, no new `LocatorDescriptor` fields, no new
constants, no new imports.
