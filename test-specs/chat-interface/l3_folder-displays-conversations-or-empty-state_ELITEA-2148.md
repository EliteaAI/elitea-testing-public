# Test Case: Chat – Folder Displays Conversation Count or Empty State

## Metadata
- **TMS ID**: ELITEA-2148
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`; see ELITEA-2135's
  AFS for the medium→l3/p2 mapping evidence in this suite)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, the account's own Private/personal project — treat as
  `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit
  Keycloak login
- **Analyst**: qa-engineer (agent) — cluster dispatch with ELITEA-2146, ELITEA-2147 (chat-remaining
  wave-07); genuinely different steps (expand/collapse + empty state, not scrolling), own AFS.
- **Status**: ready-for-automation
- **surface_key**: `chat-folder-list`

Live-confirmed this pass that the case's TITLE ("Displays Conversation Count") is slightly broader
than what the product actually renders: there is NO numeric count badge anywhere on a folder's
collapsed header (confirmed via source read, `FolderAccordionItem.jsx` / `FolderAccordion.jsx` — the
only place `folder.total`/`conversations.length` is used is `ListInfiniteMoreLoader`'s internal
pagination logic, never rendered as visible text). The case's own numbered STEPS never actually ask
for a count badge either — they ask to expand and see the conversations listed, or see the empty-state
text — and those steps match live behavior exactly. Treated as a title/scope mismatch, not case-text
drift requiring a clarification filing (the steps, which are what this AFS actually automates, are
accurate); noted here so nobody "fixes" a future gap by chasing a count badge that was never real.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- At least one folder with conversations and one empty folder exist (seeded, see § Test Data).

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`folder_with_conversation`** — created via `conversation_api.create_folder(name)`, then one
  conversation created via `conversation_api.create_conversation(name)` and moved into it via
  `conversation_api.move_conversation_to_folder(conversation_id, folder_id)`.
- **`empty_folder`** — created via `conversation_api.create_folder(name)`, left empty.

## Test Steps

1. Navigate to `${BASE_URL}/chat` and click `folder_with_conversation` to expand it.
   - **Verify**: conversations are listed below the folder name —
     `is_conversation_in_folder(folder_with_conversation_id, conversation_id)` reads `True`
     (pre-existing helper, `chat_page.py:6451`); `is_folder_expanded(folder_with_conversation_id)`
     reads `True` (`data-expanded="true"`, pre-existing helper).
2. Click `folder_with_conversation` again to collapse it.
   - **Verify**: `is_folder_expanded(folder_with_conversation_id)` reads `False`
     (`data-expanded="false"`); the conversation item is no longer visible — live-confirmed this pass
     that the conversation row stays mounted (MUI `Collapse`) but gains `visibility: hidden` via the
     ancestor `.MuiCollapse-hidden` class, so the assertion must be
     `expect(item).not_to_be_visible()` (visibility-based), NOT `to_have_count(0)` (the element is
     still IN the DOM, just visually collapsed — asserting absence-from-DOM would be asserting the
     wrong thing and could pass for the wrong reason).
3. Click `empty_folder` to expand it.
   - **Verify**: `get_folder_empty_state_text(empty_folder_id)` (pre-existing helper,
     `chat_page.py:6508`) returns exactly **"No conversations added"** — live-confirmed this pass
     (folder `279`, this session's own exploration) via the `chat-folder-empty-state` testid
     (pre-existing, `FOLDER_EMPTY_STATE`).

## Expected Results
- Expanding a folder with conversations lists them below the folder name.
- Collapsing hides them again (via CSS visibility, not DOM removal).
- Expanding an empty folder shows "No conversations added".

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: one folder with conversations + one empty folder | — | Setup | 2 API-seeded folders (§ Test Data) | asserted |
| 1 Click a folder with conversations to expand it | Conversations are listed below the folder name | AFS step 1 | `is_conversation_in_folder()` True + `is_folder_expanded()` True | asserted |
| 2 Click the folder again to collapse it | Folder collapses; conversations hidden | AFS step 2 | `is_folder_expanded()` False + conversation item `not_to_be_visible()` | asserted |
| 3 Click on a folder with no conversations | Folder shows 'No conversations added' text when expanded | AFS step 3 | `get_folder_empty_state_text()` == "No conversations added" | asserted |
| Case title's implication of a "conversation count" display | — | n/a | source-confirmed: no count badge exists anywhere on a folder header | out-of-scope (see note above metadata) |
| Expected Final State (prose): "Folders expand/collapse correctly and show empty state when empty" | — | steps 1–3 | covered by the rows above | asserted |
| Pass/Fail: "All steps complete without errors" | — | all steps | console-check (Axis 2) | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 2 specifies a VISIBILITY assertion (`not_to_be_visible()`) rather than an absence/count
  assertion — *added: live-confirmed this pass that the collapsed conversation row stays mounted in
  the DOM under MUI's `Collapse` component (`.MuiCollapse-hidden` ancestor sets `visibility: hidden`,
  not `display: none` and not unmount) — a `to_have_count(0)` assertion here would be asserting a
  fact that isn't true of the real implementation, even though it happens to also "pass" for the
  wrong reason (Playwright's `to_have_count` counts DOM presence, and the element IS still present).
  This is exactly the kind of trap `.agents/memory/qa-engineer/passing_assertion_may_prove_nothing.md`
  warns about — this AFS closes it by naming the correct assertion shape up front.*
- Step 3 asserts the EXACT empty-state string, not just presence of the `chat-folder-empty-state`
  element — *added: catches a scenario where the element renders but with placeholder/wrong text
  (a weaker "element exists" check wouldn't).*
- Console/network side-channel checked after every interaction — *added: standard side-channel
  discipline for this suite; 0 console errors observed across every expand/collapse this pass.*

## Cleanup
1. Delete the conversation via `conversation_api.delete_conversation(id)` (folder-scoped deletion
   confirmed to work identically to ungrouped, ELITEA-2115's AFS).
2. Delete both folders via `conversation_api.delete_folder(id)`.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Folder row (expand/collapse trigger) | `[data-testid="chat-folder-item-{id}"]` (`FOLDER_ITEM`) | pre-existing, on-`automation/testids` ✓ | `ChatPage.expand_folder(folder_id)` (pre-existing, `chat_page.py:6435`) clicks the WHOLE row (not just the icon) and waits for `data-expanded="true"` — confirmed live this pass, clicking either the row or the scoped `FOLDER_EXPAND_ICON` toggles identically. |
| Folder expanded state | `data-expanded="true"/"false"` on `FOLDER_ITEM` | pre-existing | `ChatPage.is_folder_expanded(folder_id)` (pre-existing, `chat_page.py:6430`). |
| Conversation-in-folder check | `[data-testid="chat-conversation-item-{id}"]` scoped inside `FOLDER_ITEM` | pre-existing | `ChatPage.is_conversation_in_folder(folder_id, conversation_id)` (pre-existing, `chat_page.py:6451`). |
| Folder empty-state text | `[data-testid="chat-folder-empty-state"]` (`FOLDER_EMPTY_STATE`), scoped inside `FOLDER_ITEM` | pre-existing, on-`automation/testids` ✓ | `ChatPage.get_folder_empty_state_text(folder_id)` (pre-existing, `chat_page.py:6508`). Live text: **"No conversations added"** (verified this pass, folder `279`). |

**Page-object gap (method, not testid — normal implementer work):** no `collapse_folder()` method
exists yet. `expand_folder()` is not safe to call a second time to collapse (it waits for
`data-expanded="true"`, which is already true, then would immediately be stale once the click flips
it back to `false`). The implementer needs a small `collapse_folder(folder_id)` mirroring
`expand_folder()` but clicking `get_folder_item(folder_id)` and waiting for
`[data-expanded="false"]` instead — confirmed live this pass that a second click on the same
`FOLDER_EXPAND_ICON`/row genuinely toggles `data-expanded` back to `false` (folder `91`, this
session).

**Implementer amendment (discovered during ELITEA-2148 implementation):** clicking the WHOLE
`get_folder_item(folder_id)` container (mirroring `expand_folder()`'s own click target exactly) is
NOT safe for the collapse direction specifically, though it live-confirmed fine during analyst
exploration on a single ambient folder. `FOLDER_ITEM` scopes both the header AND the (now-visible,
EXPANDED) body as descendants — Playwright's plain `.click()` lands at the bounding box's CENTER,
which for an expanded folder with body content can fall inside the conversation-list body instead of
the header, leaving `data-expanded="true"` and timing out the wait for `"false"` (live-reproduced this
pass). The shipped `collapse_folder()` instead clicks the scoped `FOLDER_EXPAND_ICON` (always inside
the header, unaffected by body height) — see `automation/pages/chat_page.py`'s `collapse_folder()`
docstring.

**Live measurement (this pass, confirms the mechanism end-to-end):**
- Expanded folder `91` (containing conversation `8153`, a pre-existing folder-scoped conversation
  found during exploration): `data-expanded` flipped `false → true`, conversation's computed
  `visibility` flipped `hidden → visible`.
- Collapsed it again: `data-expanded` flipped back to `false`, conversation's computed `visibility`
  flipped back to `hidden` — round-trip confirmed.
- Expanded folder `279` (an ambient, empty orphaned folder — NOT this AFS's own seeded data, used
  only to confirm the mechanism during exploration): `chat-folder-empty-state` present,
  `textContent === "No conversations added"`.
- **Unrelated gotcha noted, not this case's concern**: a PINNED folder's expand/collapse button sits
  inside a `disabled` HTML ancestor (`isDragDisabled={isPinned}`) and needs `click(force=True)` — a
  plain click times out ("element is not enabled") even though the button's own `.disabled` property
  reads `false`. Already documented in `test-specs/chat-interface/_surface.md`'s ELITEA-2121/2130
  section and already handled correctly by other existing methods (`open_folder_rename_editor()`,
  `delete_folder_via_menu()`) — this case's own seeded folders are never pinned, so it doesn't need
  the workaround, but flagging so nobody mistakes a future pinned-folder flake for a NEW defect.

## Network Behavior
- Folder/conversation create/move/delete: same endpoints as ELITEA-2146/ELITEA-2147
  (`ConversationAPI.create_folder`/`create_conversation`/`move_conversation_to_folder`/
  `delete_folder`/`delete_conversation`).
- Expand/collapse is a pure client-side operation (no network call) — confirmed via
  `browser_network_requests` during this pass, no new request fired on either click.
- Pre-existing, unrelated: project 399's `secrets/secrets/default` `403` on every page load —
  excluded from "no new console errors" checks, same as every sibling AFS.

## Known Defects Found During Exploration
None. All 3 case steps executed live end-to-end and matched expected results exactly (0 console
errors across every expand/collapse this pass).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Page object: extend `automation/pages/chat_page.py`. Reuse `expand_folder()`,
  `is_folder_expanded()`, `is_conversation_in_folder()`, `get_folder_empty_state_text()` (all
  pre-existing). Add `collapse_folder()` per § Concrete Handles — small, mirrors `expand_folder()`.
- Priority marker: `@pytest.mark.p2` (see ELITEA-2135's AFS note on the l3/p2 mapping).
- Feature markers: `@pytest.mark.chat`, `@pytest.mark.regression`.
