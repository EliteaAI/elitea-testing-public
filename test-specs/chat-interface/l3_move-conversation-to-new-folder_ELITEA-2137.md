# Test Case: Chat – Move Conversation to a New Folder via Move To Menu

## Metadata
- **TMS ID**: ELITEA-2137
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`; see ELITEA-2135's
  AFS for the medium→l3/p2 mapping evidence in this suite)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, the account's own Private/personal project — treat as
  `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit
  Keycloak login
- **Analyst**: qa-engineer (agent) — cluster dispatch with ELITEA-2135, ELITEA-2149
- **Status**: ready-for-automation
- **surface_key**: `chat-conversation-context-menu`

Sibling of ELITEA-2135 (same "Move to" submenu, but picks an EXISTING folder instead of creating
one) — see that AFS's header note for why this is a separate file rather than a family AFS (this
case's steps 2–5, the inline-editable-name-input flow, have no equivalent in ELITEA-2135 at all).
Shares the SAME activation-gesture defect as ELITEA-2135 (filed once,
EliteaAI/elitea-testing-public#1117, cross-referenced here rather than re-filed — see § Known
Defects).

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- At least one conversation exists — test creates its own (see § Test Data).
- The target conversation must NOT be pinned and NOT already inside a folder (same "Move to" is
  disabled while pinned" constraint as ELITEA-2135).

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`conv_target`** — the conversation that will be moved. Create via
  `conversation_api.create_conversation(name)`.
- **the new folder itself** — this case's own observable under test. `onMoveToNewFolderConversation`
  (`useMoveToFolderConversation.hooks.js`) seeds a CLIENT-SIDE placeholder folder object
  (`DefaultFolderName` = `"New folder"`, `isNew: true`) the instant "Create folder" is clicked; the
  REAL, server-side folder is only created when the checkmark is confirmed
  (`moveTargetConversationToNewFolder()` calls `createFolder({name, projectId})` THEN
  `onMoveToFolderConversation(conversation, newCreatedFolder)` to actually move the conversation into
  it) — i.e. this is the SAME two-phase pattern ELITEA-2132's AFS already documented for the CHATS
  header "Create folder" button, reused here via the "Move to" submenu's own "Create folder" entry
  point instead.

## Test Steps

1. Navigate to `${BASE_URL}/chat`. Hover `conv_target`'s sidebar item, click its 3-dot menu, click
   **Move to**.
   - **Verify (with retry — see ELITEA-2135's AFS § Known Defects, same defect, not re-documented
     here in full)**: the submenu mounts, showing `chat-move-to-create-folder-menuitem`,
     `chat-move-to-back-to-list-menuitem`, and any existing folders.
2. Click **Create folder** (`chat-move-to-create-folder-menuitem`).
   - **Verify**: a new inline-editable folder entry appears at the top of the folder list, with
     `chat-folder-name-input` focused and pre-filled with the default name **"New folder"**
     (live-verified exact string — `DefaultFolderName` constant, matches the case's expected result
     and ELITEA-2132's own already-established default-name behaviour for the OTHER create-folder
     entry point). No server-side folder exists yet at this point (see § Test Data).
3. Verify checkmark and X (cancel) icons are visible next to the input.
   - **Verify**: `chat-folder-name-confirm-button` and `chat-folder-name-cancel-button` are both
     visible — same shared editor markup ELITEA-2132's AFS already documented (this case reuses that
     EXACT editor component, just reached via a different entry point).
4. Click `chat-folder-name-confirm-button` without changing the default name.
   - **Verify**: the app-wide success toast (`toast-message`) appears with text
     **`Chat moved to "New folder" folder successfully`** (live-verified exact string — note this is
     the "moved to a folder" toast from `onMoveToFolderConversation`, NOT ELITEA-2132's plain "folder
     created" flow, which has no equivalent toast at all; the two "Create folder" entry points in
     this app — CHATS header icon vs. this submenu's "Create folder" item — are DIFFERENT code paths
     with different UX consequences, only superficially similar).
5. Verify `conv_target` is no longer rendered under any date-group heading.
   - **Verify**: same scoped (not page-wide) 0-count discipline as ELITEA-2135's step 4 — the new
     folder is collapsed by default and its children stay DOM-mounted (MUI `Collapse`), so an
     unscoped page-wide count would give a false pass.
6. Expand the new folder and verify `conv_target` is inside it.
   - **Verify**: the new folder's id is captured from the `POST .../folder/prompt_lib/{project_id}`
     response (live-observed `201`, same shape ELITEA-2132's AFS documented:
     `{"name": "New folder", "meta": {}, "id": <int>, "owner_id": <int>, "position": <int>}`); its
     row (`chat-folder-item-{new_folder_id}`) `data-expanded` flips `"false"` → `"true"` on click;
     `chat-conversation-item-{conv_target_id}` scoped inside it resolves 1.

## Expected Results
- "Create folder" inside the "Move to" submenu inserts the SAME inline-editable "New folder" entry
  ELITEA-2132's CHATS-header icon does, reached via a different UI path.
- Confirming with the default name creates a real folder server-side AND moves `conv_target` into it
  in one action (unlike ELITEA-2132's flow, which only creates an EMPTY folder) — confirmed via the
  "moved to" toast, not the plain "folder created" absence-of-toast ELITEA-2132 documented.
- The conversation disappears from its date group and appears inside the new folder.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in, ≥1 conversation exists | — | Setup | `auth_state` + API-seeded conversation | asserted |
| 1 Navigate to Chats, hover conversation, 3-dot icon, hover Move to | Submenu appears | AFS step 1 | step 1: submenu mounted (with retry workaround) | asserted, with the SAME filed defect as ELITEA-2135 (#1117) — cross-referenced, not re-filed |
| 2 Click 'Create folder' | New folder entry appears at top of folder list in editable mode | AFS step 2 | step 2: `chat-folder-name-input` visible + focused + value "New folder" | asserted |
| 3 Verify checkmark and X icons are visible | Both icons visible | AFS step 3 | step 3: `chat-folder-name-confirm-button` + `chat-folder-name-cancel-button` visible | asserted |
| 4 Click the checkmark icon to save the default folder name | New folder created; conversation moved into it | AFS step 4 | step 4: `POST .../folder/prompt_lib/{project_id}` → `201` (implicit, via the toast which only fires on a successful move) + toast text | asserted |
| 5 Verify a success toast appears confirming the move | Toast shown | AFS step 4 | step 4: `Chat moved to "New folder" folder successfully` | asserted *(exact live text has quote marks the case's paraphrase omits — same CLARIFICATION as ELITEA-2135, not re-filed separately)* |
| 6 Verify the conversation is no longer in its original date group | Removed from date groups | AFS step 5 | step 5: scoped 0-count | asserted |
| 7 Expand the new folder and verify the conversation is inside | Conversation inside folder | AFS step 6 | step 6: `data-expanded` flip + scoped 1-count | asserted |
| Expected Final State (prose): "Conversation moved to a newly created folder" | — | steps 4–6 | covered by the rows above | asserted |
| Pass/Fail: "All steps complete without errors" | — | all steps | console-check (Axis 2) | asserted, with 1 cross-referenced defect that does not block completion |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 1's submenu-open retry workaround — *added, cross-referencing ELITEA-2135's AFS rather than
  duplicating the full defect narrative; the underlying bug (EliteaAI/elitea-testing-public#1117) is
  the SAME one, not a second occurrence needing its own ticket per the strict-per-bug dedup rule
  (same object: the "Move to" menu item; same trigger: opening its submenu; same
  expected/actual — this is a duplicate within one analyst pass, not a sibling).*
- Step 4 explicitly distinguishes this flow's toast from ELITEA-2132's TOAST-LESS plain-create flow —
  *added: without calling this out explicitly, an implementer skimming both AFSes side-by-side could
  reasonably assume "Create folder" always behaves identically regardless of entry point; it doesn't
  — this submenu's version moves a conversation in the same action, the header-icon version doesn't
  move anything (there's nothing to move).*
- Step 5 requires a SCOPED 0-count for the same reason as ELITEA-2135's step 4 — *added, same
  MUI-Collapse-keeps-children-mounted trap.*
- Console/network side-channel checked after every interaction — *added: standard side-channel
  discipline.*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)`.
2. Delete the new folder — capture its id from the `POST .../folder/prompt_lib/{project_id}` response
   observed in step 4 (do NOT assume any hardcoded id; live exploration observed a range of ids
   across repeated runs in the shared project, e.g. `78`, `82`, `85`, `87`, `89` across this pass's
   own repro runs). Same UI-Delete-flow-or-`FolderAPI` choice as ELITEA-2135's cleanup, same
   independent `try`/`except` per resource so one failing delete doesn't block the other.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

All of this case's "Move to" submenu handles (`chat-move-to-create-folder-menuitem`,
`chat-move-to-back-to-list-menuitem`) plus the shared editor handles
(`chat-folder-name-input`/`chat-folder-name-confirm-button`/`chat-folder-name-cancel-button`,
pre-existing from ELITEA-2132) are documented in full in ELITEA-2135's AFS § Concrete Handles — not
repeated verbatim here to avoid drift between the two files. Testid commit provenance is the same
single commit, `cf348d32` on `EliteaAI/EliteaUI`'s `automation/testids` (see ELITEA-2135's AFS).

| Element | Testid handle | Notes |
|---|---|---|
| "Move to" submenu — "Create folder" item | `[data-testid="chat-move-to-create-folder-menuitem"]` | This case's own step-2 handle — see ELITEA-2135's AFS for full provenance. |
| Folder-name inline editor input / confirm / cancel | `chat-folder-name-input` / `chat-folder-name-confirm-button` / `chat-folder-name-cancel-button` | Pre-existing, ELITEA-2132 — the SAME editor component, reused verbatim (shared between the CHATS-header create-folder flow and this submenu's create-folder flow — only one folder can be in edit mode at a time, confirmed by ELITEA-2132's AFS, still true here). |
| New folder's own row (for step 6) | `[data-testid="chat-folder-item-{new_folder_id}"]`, `data-expanded` | Pre-existing, ELITEA-2132 — id captured from the `201` response, not hardcoded. |
| Success toast | `[data-testid="toast-message"]` | Pre-existing, `ChatPage.toast_message`. |

## Network Behavior
- `POST .../folder/prompt_lib/{project_id}` → `201 Created` on confirm (step 4) — same shape as
  ELITEA-2132's Network Behavior section.
- The subsequent conversation-move edit call (same `useConversationEditMutation` family as
  ELITEA-2135's step 3) fires immediately after, chained inside
  `moveTargetConversationToNewFolder()` — not independently asserted, same reasoning as ELITEA-2135
  (the toast is the product's own confirmation signal).
- `GET .../folder/prompt_lib/{project_id}?...&grouped=true` refetches after.
- Pre-existing, unrelated: project 399's `secrets/secrets/default` `403` on every page load —
  excluded from "no new console errors" checks, same as every sibling AFS.

## Known Defects Found During Exploration

Cross-referenced, not re-filed: **EliteaAI/elitea-testing-public#1117** (the "Move to" submenu
activation-gesture defect) — see ELITEA-2135's AFS § Known Defects for the full narrative and
evidence. Same object (the "Move to" menu item), same trigger (opening its submenu), same
expected/actual — filing a second ticket for this case would be a duplicate per
`.agents/profile.md` § Bug filing's dedup rule, not a sibling (nothing about this case's OWN steps —
the "Create folder" sub-flow — surfaced any NEW defect; the create/move mechanics worked correctly
and completely once the submenu was reached).

No other defects found. All 6 case steps executed live end-to-end, matched expected results (minor
case-text-drift CLARIFICATIONs noted in the Coverage Map, not defects).

## Blocked Steps
None.

## Automation Hints
- Reuse `open_move_to_submenu()` (new method, specced in ELITEA-2135's AFS — implement it once,
  both cases' specs call it) plus ELITEA-2132's pre-existing `folder_name_input` /
  `folder_name_confirm_button` locators and `create_folder()`-style flow for the confirm step.
- New method needed: `select_move_to_create_folder()` — click
  `chat-move-to-create-folder-menuitem` (distinct from `select_move_to_folder(folder_id)` in
  ELITEA-2135's AFS, which targets an EXISTING folder instead).
- Capture the new folder's id from the `POST .../folder/prompt_lib/{project_id}` response (Playwright
  `page.on("response", ...)` or `page.expect_response(...)`) rather than assuming any fixed id or
  scraping it from the DOM — matches the pattern this AFS's own exploration script used.
- Priority marker: `@pytest.mark.p2` (see ELITEA-2135's AFS note on the l3/p2 mapping).
- If both ELITEA-2135 and ELITEA-2137 land in the SAME test file/class (reasonable, given they share
  a setup shape and the same new `open_move_to_submenu()` helper), consider a shared
  `conversation_api`-seeded `conv_target` per test (function-scoped, not shared across the two) to
  keep them independent — do NOT share one conversation between the two tests' assertions, since
  ELITEA-2135 leaves it inside `target_folder` and ELITEA-2137 needs a fresh, not-yet-moved
  conversation of its own.
