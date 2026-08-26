# Test Case: Chat – Folder Rename – Checkmark (Confirm) Icon Validation

## Metadata
- **TMS ID**: ELITEA-2458
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case frontmatter: `priority: high`; per `spec-format.md` §
  Location, `high` maps to digit `2`, matching the sibling ELITEA-2114
  chat-interface AFS's identical priority class — NOT l1, which is `critical`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids`, DEV backend; project "Private", observed live as
  `projectId=399` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN`
  skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: ready-for-automation

No existing AFS or automated test covers folder **rename** — `test-specs/chat-interface/`
and `automation/tests/ui/chat/` only had folder **creation** (ELITEA-2132,
`test_folder_creation.py`) and folder **move** (`test_move_conversation_to_folder.py`)
before this file; `chat_page.py` already carries `set_folder_name()`,
`folder_name_input`/`folder_name_confirm_button`/`folder_name_cancel_button`
(all added by the ELITEA-2132 pass, shared by BOTH the create-new-folder and
rename-existing-folder editor, since `FolderItem.jsx` renders the identical
markup for both), but **no method opens the RENAME path via the dot-menu** —
only the create-header-icon path is wired. All 9 case steps were executed
live end-to-end against a dedicated seeded folder (`AutomationRenameTest`,
created and deleted within this session, id `138` at exploration time — treat
as ephemeral, a fresh id is minted per run). No product defects found; the
case's every claim (empty/2-char/unchanged → inactive; 3-char+changed →
active; click-when-inactive → no-op; click-when-active → renames) was
confirmed to match `FolderItem.jsx`'s actual logic exactly (see § Concrete
Handles for the source-level derivation). Two real gaps exist, both
`needs-adding` work, not defects: (1) the dot-menu "Rename" item has **never**
carried a testid (case step 1's "click Edit (or Rename)"), and (2) the
confirm checkmark's active/inactive **state** has no `data-*` attribute at
all today — only a CSS fill-color/cursor difference — so per
`.agents/testing.md` § Locator policy ("state via `data-*` attribute, never a
state-dependent testid") a `data-disabled` attribute needs adding to the
*existing* `chat-folder-name-confirm-button` testid. See § Concrete Handles.

**Adjacent finding, filed separately, NOT part of this AFS's own scope:**
while tracing the dot-menu's testid mechanism (`DotMenu.jsx`'s
`item.key` → `${item.key}-menuitem"` `data-testid`) to work out how to add
the Rename item's testid, a **regression** was found and confirmed:
`FolderItem.jsx`'s "Delete" menu item's `key: 'chat-folder-menu-delete'` —
added by ELITEA-2132, already re-added once after being lost, and lost
*again* by a later hotfix commit (`6bec1451`, "Fix rename conversation block
behaviour") — is absent from current `main` AND `automation/testids` HEAD.
This silently breaks `ChatPage.delete_folder_via_menu()`'s cleanup in 3
merged test files (swallowed by their own `try`/`except`), and the shared DEV
project was observed carrying **19 leaked "New folder"/"New folder6" test
folders** as a result (including a `"New folder6New folder"` artifact that is
independently explained by the *other* documented `set_folder_name()` bug —
see that method's own docstring). Filed as
[EliteaAI/elitea-testing-public#1309](https://github.com/EliteaAI/elitea-testing-public/issues/1309) —
out of scope for this case (the Delete item isn't touched by ELITEA-2458's
own steps), but the implementer should be aware the SAME "lost `key` on a
future refactor" failure mode applies to whatever `key` gets added for
Rename here, and should not assume `chat-folder-menu-delete-menuitem`
currently works if reusing any part of `delete_folder_via_menu()` as a
pattern.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- User is on the Chats section (`${BASE_URL}/chat` — the CHATS panel renders
  on every chat route).
- At least one folder exists that the test owns (see § Test Data — this case
  seeds its own folder rather than reusing a shared one, so the "pre-filled
  name" and "unchanged name" assertions have a known, controlled value).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Active project — whatever `${TEST_USER}`'s default project is (observed
  live as "Private", id 399). No project switch required.

### generate-per-test (created by the test's own setup, cleaned up in its own teardown)
- One folder, created via the existing `click_create_folder_button()` +
  `set_folder_name(<name>)` + `folder_name_confirm_button.click()` flow
  (ELITEA-2132's create path), with a **valid, ≥3-character, deterministic
  name** — e.g. `AutomationRenameTest` (live-verified value used this
  session). This folder is the rename target for every step; its pre-filled
  name is what step 6's "unchanged name" comparison is against, and it is
  the folder actually renamed to `"ABC"` by the final step.

## Test Steps

1. Navigate to `${BASE_URL}/chat`, seed the folder (§ Test Data), then hover
   the folder row, click its dot-menu (`conversation-menu-menu-button`,
   scoped inside `chat-folder-item-{folder_id}`), and click **Rename**.
   - **Verify**: the inline editor opens — `chat-folder-name-input` is
     visible, focused, and pre-filled with the folder's current name (the
     seeded name, e.g. `AutomationRenameTest`).
2. Clear the input entirely (`folder_name_input.clear()` — do NOT rely on a
   bare `Control+a`, see § Concrete Handles / `set_folder_name()`'s own
   docstring for the documented race).
   - **Verify**: `chat-folder-name-input` value is empty.
3. Verify the checkmark is inactive AND that clicking it has no effect.
   - **Verify (state)**: `chat-folder-name-confirm-button` carries
     `data-disabled="true"` (**needs-adding** — see § Concrete Handles).
   - **Verify (no-op)**: click `chat-folder-name-confirm-button`; the editor
     stays open, `chat-folder-name-input` is still present/empty, no
     `PUT .../folder/prompt_lib/{project_id}/{folder_id}` request fires, and
     the folder does not disappear/rename in the list.
4. Type exactly 2 characters (e.g. `"AB"`) into `chat-folder-name-input`.
   - **Verify**: the input shows `"AB"`; `chat-folder-name-confirm-button`
     still carries `data-disabled="true"`.
5. Hover `chat-folder-name-confirm-button` and verify the tooltip validation
   message.
   - **Verify**: a tooltip becomes visible with the EXACT text (live-confirmed
     this session, see § Concrete Handles for the source constant):
     `"The folder name should be 3 to 64 characters long. It can include
     letters (a-z, A-Z), numbers (0-9), underscores (_), brackets ([]),
     parentheses (()), dots (.), hyphen(-), and spaces. Please note that the
     first character should not be a space."`
6. Restore the pre-filled name unchanged (`set_folder_name(<original name>)`
   or equivalent — end state must exactly equal the folder's name from step 1).
   - **Verify (state)**: `chat-folder-name-confirm-button` carries
     `data-disabled="true"` again — valid name, but no CHANGE from the
     original, so still inactive. **No tooltip** this time (live-confirmed:
     the tooltip title is empty when the name is *valid*, regardless of
     whether it changed — this is the one case-text detail the case gets
     exactly right by omission: step 6 doesn't mention a tooltip, and none
     appears).
   - **Verify (no-op)**: click `chat-folder-name-confirm-button`; same
     no-effect checks as step 3 (editor stays open, no PUT request, no rename).
7. Type one more character so the total is 3 (e.g. `"AB"` → `"ABC"`, or
   directly `set_folder_name("ABC")` — either reaches the same asserted end
   state; see § Automation Hints).
   - **Verify**: the input shows `"ABC"`.
8. Verify the checkmark becomes active.
   - **Verify**: `chat-folder-name-confirm-button` carries
     `data-disabled="false"` (or the attribute's absence, per whatever exact
     shape the implementer adds — see § Concrete Handles' note on the
     attribute's boolean representation).
9. Click `chat-folder-name-confirm-button` and verify the folder is renamed.
   - **Verify**: `PUT /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_id}`
     resolves `200 OK`; the editor closes; `chat-folder-item-{folder_id}`'s
     name text now reads `"ABC"` (live-confirmed exact request/response
     shape in § Network Behavior).

## Expected Results
- The checkmark (confirm) icon is inactive — no `onClick` handler fires, no
  network call, no rename — whenever the name is empty, 1–2 characters, OR
  unchanged from the folder's current name.
- A validation tooltip appears ONLY when the name is invalid per the 3–64
  character regex (empty and 2-char both qualify); the "valid but unchanged"
  case shows NO tooltip — validity and "has it changed" are independent
  conditions, both must hold for the checkmark to activate.
- The checkmark activates the instant the name is BOTH valid (3–64 chars,
  first-char-not-space, allowed charset) AND different from the current name.
- Clicking the active checkmark persists the rename server-side (`PUT … →
  200`) and updates the folder's displayed name immediately.
- No new console errors beyond the pre-existing, unrelated Vite dev-server
  warning (`Module "stream" has been externalized…`, `@eigenpal_docx-js-editor`
  — confirmed present before this test even starts, unrelated to folders).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| 1 Navigate to Chats, hover folder, click 3-dot icon, click Edit/Rename | Target page/section loads | AFS step 1 | step 1: editor opens, pre-filled, focused | asserted |
| 2 Clear the input entirely | Action completes, expected UI state | AFS step 2 | step 2: input value empty | asserted |
| 3 Checkmark disabled/inactive; clicking has no effect | Condition holds | AFS step 3 | step 3: `data-disabled="true"` + click no-op (no PUT, editor stays open) | asserted *(decomposed: state + behavior)* |
| 4 Type exactly 2 characters; checkmark remains inactive | Field accepts input | AFS step 4 | step 4: input = "AB", `data-disabled="true"` | asserted |
| 5 Verify tooltip validation message is shown | Condition holds | AFS step 5 | step 5: exact tooltip text confirmed live | asserted |
| 6 Don't change pre-filled name; checkmark inactive, no effect when clicked | Action completes, expected UI state | AFS step 6 | step 6: `data-disabled="true"`, no tooltip, click no-op | asserted *(decomposed: state + behavior, + the no-tooltip nuance the case doesn't spell out but doesn't contradict either)* |
| 7 Type one more character (total 3, e.g. "ABC") | Field accepts input | AFS step 7 | step 7: input = "ABC" | asserted |
| 8 Verify checkmark becomes active/enabled | Condition holds | AFS step 8 | step 8: `data-disabled="false"` | asserted |
| 9 Click checkmark; folder renamed to "ABC" | Control responds, next state shown | AFS step 9 | step 9: `PUT … → 200`, displayed name = "ABC" | asserted |
| Expected Final State (prose): "folder is renamed to ABC" | — | step 9 | covered by the row above | asserted |
| Pass/Fail: "All steps complete without errors" | — | all steps | console-check after every interaction (Axis 2) | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked`
/ `out-of-scope`. All rows `asserted` — every case element was executable and
confirmed live, no blockers, no reverse-masking (the case's expected
behaviors all match `FolderItem.jsx`'s actual `isFolderSaveEnabled`/
`isFolderNameValid` logic exactly — see § Concrete Handles for the source
derivation that grounds every "verify" above).

### Axis 2 — Analyst additions

- Steps 3 and 6 assert the click-has-no-effect claim via THREE independent
  signals (editor stays open, no PUT network call, folder name unchanged in
  the list) rather than just one — *added: a single signal (e.g. "editor
  didn't close") could pass even if some OTHER unintended side effect fired;
  the network-silence check is the strongest proof nothing happened
  server-side.*
- Step 3's and 6's/8's state checks use a `data-disabled` attribute
  (needs-adding) rather than reading the icon's computed CSS `fill` color or
  relying on the element's presence/absence in an accessibility-tree snapshot
  — *added, and important: live exploration found the confirm button is
  **inconsistently represented in the Playwright accessibility snapshot**
  depending on state (present-with-name when the tooltip has text, i.e.
  invalid-name states; present-but-unlabeled, sometimes omitted entirely from
  a scoped snapshot, when the tooltip title is empty, i.e. valid-name states
  — both changed AND unchanged). This means a role/label-based locator is not
  just against policy here, it is **functionally unreliable** — testid-only
  targeting via CSS attribute selector (`page.locator('[data-testid="..."]')`)
  is the only way that worked consistently across all 4 states tested this
  session (empty / 2-char / unchanged / 3-char-changed). See § Concrete
  Handles for the exact observation.*
- Step 5 pins down the EXACT tooltip text (the case only says "verify a
  tooltip validation message is shown", leaving the copy unspecified) —
  *added: determined live and recorded verbatim so automation asserts real
  copy, not a substring guess.*
- Step 6 explicitly asserts NO tooltip appears (case doesn't ask for this,
  doesn't contradict it either) — *added: this is the detail that
  distinguishes "invalid" from "valid-but-unchanged" as two DIFFERENT reasons
  the checkmark can be inactive; without this assertion a bug that started
  showing the tooltip for ALL 3 inactive cases (not just the invalid ones)
  could regress silently.*
- Console/network side-channel checked after every interaction — *added:
  standard side-channel discipline; confirmed clean throughout (only the
  pre-existing, documented, unrelated Vite `stream` externalization warning
  — present from page load, before any folder interaction).*
- (nothing else added beyond the case.)

## Cleanup
1. Delete the seeded folder via the UI Delete flow (three-dot menu on
   `chat-folder-item-{folder_id}` → "Delete" menu item → `delete-confirm-button`)
   — mirrors ELITEA-2132's cleanup pattern. **CAUTION (see the adjacent
   finding above):** `ChatPage.delete_folder_via_menu()` / `FOLDER_MENU_DELETE_ITEM`
   currently target a DEAD testid (`chat-folder-menu-delete-menuitem` — regressed,
   tracked in EliteaAI/elitea-testing-public#1309, NOT part of this case's own
   scope to fix). Until that ticket lands, this test's cleanup will silently
   no-op the same way the 3 pre-existing consumers do — wrap in
   `try`/`except` per the existing pattern so a cleanup failure never fails
   the test itself, but **do not treat a silently-failed cleanup as
   evidence this case's OWN assertions are wrong** — they aren't; the
   deletion mechanism is a separate, already-filed, already-regressed
   dependency.
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data
   Lifecycle — delete must run (or be attempted) even if a step-level
   assertion fails.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text
fallback ladder (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md`). This is not just policy here — see the Axis-2
note above: the confirm button's accessible representation genuinely changes
across states, so a role/label locator would be **unreliable**, not merely
non-compliant.

**Source-level derivation (why every "verify" above is grounded, not
guessed)** — `FolderItem.jsx`:
```js
const isFolderNameValid = useMemo(() => ConversationNameRegExp.test(folderName ?? ''), [folderName]);
const isFolderSaveEnabled = useMemo(
  () => isFolderNameValid && (isNewFolder || folderName !== name),
  [isFolderNameValid, isNewFolder, folderName, name],
);
// ConversationNameRegExp (src/common/constants.js:94):
//   /^[a-zA-Z0-9_[\].()][a-zA-Z0-9_[\].() -]{2,63}$/   — i.e. 3–64 chars total
// Tooltip title={isFolderNameValid ? '' : FolderNameWarningMessage}  (empty when VALID, regardless of "changed")
// Confirm Box: onClick={isFolderSaveEnabled ? handler : null}, icon fill = default (bright) vs .disabled (dim)
// cursor: isFolderSaveEnabled ? 'pointer' : 'default'
```
For an EXISTING folder (`isNewFolder = false`, this case's whole scenario),
`isFolderSaveEnabled` is `true` **only** when the name is both regex-valid
AND different from the current name — exactly the case's 4 scenarios (empty
→ invalid; 2-char → invalid; unchanged-valid-name → valid-but-same;
3-char-different → valid-and-changed).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Folder dot-menu button (3-dot) | `[data-testid="conversation-menu-menu-button"]`, **must be scoped inside `chat-folder-item-{folder_id}`** | on-`main` ✓ (confirmed live via `git grep` — the `DotMenu.jsx` template `${id}-menu-button` + `FolderAccordion.jsx`'s `id="conversation-menu"` wiring are BOTH present on `origin/main`, unlike the folder-editor testids below) | Pre-existing, reused verbatim from ELITEA-2132's `CONVERSATION_MENU_BUTTON` constant (already in `chat_page.py`). Non-unique across folders — always scope via `FOLDER_ITEM.format(folder_id)`. |
| Folder dot-menu "Rename" item | `[data-testid="chat-folder-menu-rename-menuitem"]` | **needs-adding.** Zero testid coverage today (never had one — not a regression, unlike the sibling "Delete" item, see the adjacent-finding note above). | Add `key: 'chat-folder-menu-rename'` to the `menuItems` array's "Rename" entry in `FolderItem.jsx` (mirrors `ConversationItem.jsx`'s existing `key: 'chat-conversation-menu-rename'` sibling pattern, and the `DotMenu`/`BasicMenuItem` `testId={item.key}` → `data-testid={testId}-menuitem"` mechanism already used for the folder Delete item). Scope: ONLY `key` on Rename — Pin remains untouched per the testid-scope ruling (this case's test never opens Pin). |
| Folder-name inline input (shared create/rename editor) | `[data-testid="chat-folder-name-input"]` | on-`automation/testids` ✓, on-`main` ✗ (confirmed via `git log -S` + `git merge-base --is-ancestor`: introduced by commit `6fceb3e2`, which is NOT an ancestor of `origin/main`) | Pre-existing (ELITEA-2132), reused verbatim — `ChatPage.folder_name_input`. Confirmed live this session it lands on the real `<input>` and correctly shows/accepts the rename scenario's values too (create and rename share the identical editor markup). |
| Folder-name confirm (checkmark) button | `[data-testid="chat-folder-name-confirm-button"]` | on-`automation/testids` ✓, on-`main` ✗ (same commit `6fceb3e2` as above) | Pre-existing (ELITEA-2132), reused verbatim — `ChatPage.folder_name_confirm_button`. **The STATE (active/inactive) needs a NEW `data-*` attribute — the testid itself is not new, but it currently carries no machine-readable disabled signal at all**, only a CSS `fill`/`cursor` difference (confirmed live via screenshot: dim grey icon when inactive, bright/white when active — visually correct, not automatable via DOM read). Add `data-disabled={!isFolderSaveEnabled}` (or `data-enabled={isFolderSaveEnabled}` — implementer's call on polarity, but pick ONE and match the project's existing `data-expanded` boolean-string convention, i.e. renders as the literal string `"true"`/`"false"`) directly on this `Box`, per `.agents/testing.md` § Locator policy ("state via `data-*` attribute filter, never a state-dependent testid" — this element's identity/testid stays fixed, only a sibling attribute changes). |
| Folder-name confirm tooltip content | `[data-testid="chat-folder-name-confirm-tooltip-content"]` (suggested name — implementer may rename) | **needs-adding.** The Tooltip (`@/ComponentsLib/Tooltip`, a thin MUI `Tooltip` wrapper that spreads `{...props}` through) has NO testid on its popper content today; the warning text is only reachable via the ambient `role="tooltip"` landmark or by reading the wrapping `Box`'s accessible name (itself inconsistent — see the Axis-2 note). | Add `slotProps={{ popper: { 'data-testid': 'chat-folder-name-confirm-tooltip-content' } }}` on the `<Tooltip>` wrapping the confirm `Box` in `FolderItem.jsx` — MIRRORS the exact precedent already in this codebase: `toolkit_creation_page.py`'s `bucket_info_tooltip_content` / `toolkit-field-bucket-info-tooltip-content` (added via a `contentTestId` prop chain for a shared component; here it's simpler since `@/ComponentsLib/Tooltip` already passes arbitrary props through, so `slotProps` can be set directly at THIS call site with no shared-component API change). No hover-then-read alternative needed once this lands — `page.locator('[data-testid="chat-folder-name-confirm-tooltip-content"]').text_content()` after a `hover()`. |
| Folder-name cancel (X) button | `[data-testid="chat-folder-name-cancel-button"]` | on-`automation/testids` ✓, on-`main` ✗ (same commit `6fceb3e2`) | Pre-existing (ELITEA-2132). Not exercised by this case's own steps (case doesn't test Cancel) — live-confirmed during exploration it correctly reverts to the pre-filled name and closes the editor; noted here only because it was accidentally clicked once during this session's manual exploration (see § Automation Hints for the exact accessibility-tree gotcha that caused it) and behaved exactly as expected. |
| Folder item row (for the renamed-name-text final check) | `[data-testid="chat-folder-item-{folder_id}"]` | on-`automation/testids` ✓, on-`main` ✗ (commit `6fceb3e2`) | Pre-existing (ELITEA-2132) — reused for step 9's "displayed name now reads ABC" check (read the row's accessible name / heading text, scoped inside this testid). |
| Delete confirmation dialog / message / button (cleanup only) | `[data-testid="delete-confirm-dialog"]` / `[data-testid="delete-confirm-message"]` / `[data-testid="delete-confirm-button"]` | on-`automation/testids` ✓ (pre-existing, generic `BaseModal`/`DeleteEntityModal`, confirmed live for folders too) | Already-covered, not new — same generic dialog documented in the ELITEA-2132 AFS. |

**Accessibility-tree gotcha, confirmed live (grounds the Axis-2 testid-only
necessity claim above):** with `browser_snapshot`, the confirm `Box` appears
in the accessibility tree WITH its tooltip text as its accessible name when
`isFolderNameValid` is `false` (empty / 2-char states — MUI's `Tooltip` wires
a non-empty `title` as an accessible-name source). When `isFolderNameValid`
is `true` (unchanged OR 3-char-changed), the tooltip `title` prop is the
empty string, MUI attaches no accessible-name attribute, and the element
either appears as a bare unlabeled `generic` (distinguishable from the
Cancel button only by DOM position, not by any stable snapshot handle) or is
pruned from a scoped snapshot entirely when its computed `cursor` isn't
`pointer` (the inactive-but-valid "unchanged name" state) — confirmed by
directly comparing 4 live snapshots (empty / "AB" / unchanged / "ABC")
side-by-side this session. A `getByRole`/`getByText` locator would silently
fail or mis-target in at least 2 of these 4 states; `page.locator('[data-testid="chat-folder-name-confirm-button"]')`
resolved correctly in all 4.

## Network Behavior
- `PUT /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_id}` →
  `200 OK` on confirm click with a valid, changed name (step 9). Live-observed
  this session: `PUT .../folder/prompt_lib/399/138 => [200] OK` (folder id is
  per-run, treat as a variable, not a literal).
- `GET /api/v2/elitea_core/folder/prompt_lib/{project_id}?sort_by=updated_at&sort_order=desc&grouped=true`
  → `200` — refetches the folder list after the rename; also fires on every
  page load / mutation, same as ELITEA-2132's documented pattern.
- No network call at all fires on a click while the checkmark is inactive
  (steps 3 and 6) — confirmed via `browser_network_requests` filtered to
  `folder` immediately after each no-op click: zero new PUT/POST entries.
- `DELETE /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_id}` →
  cleanup only; see § Cleanup for the currently-broken UI path to reach it
  (EliteaAI/elitea-testing-public#1309).

## Known Defects Found During Exploration
None found in THIS case's own scope. All 9 case steps executed live
end-to-end and matched `FolderItem.jsx`'s actual validation/enablement logic
exactly — no case-text drift, no reverse-masking needed. (A real regression
WAS found adjacent to this case's exploration — the dead
`chat-folder-menu-delete-menuitem` testid — but it does not block or alter
any of THIS case's own assertions; filed separately as
EliteaAI/elitea-testing-public#1309, see the intro paragraph and § Cleanup.)

## Blocked Steps
None. All 9 case steps were executable and confirmed live.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`).
- Page object: extend `automation/pages/chat_page.py`. Reuse `set_folder_name()`,
  `folder_name_input`, `folder_name_confirm_button`, `folder_name_cancel_button`,
  `CONVERSATION_MENU_BUTTON`, `FOLDER_ITEM`, `get_folder_item()` verbatim — all
  pre-existing from ELITEA-2132. New additions needed:
  - `FOLDER_MENU_RENAME_ITEM = '[data-testid="chat-folder-menu-rename-menuitem"]'`
    (class constant, mirrors `FOLDER_MENU_DELETE_ITEM`'s existing shape).
  - `open_folder_rename_editor(folder_id)` — hover the folder row, open the
    scoped dot-menu (mirrors `delete_folder_via_menu()`'s hover-then-open
    pattern exactly, just clicking Rename instead of Delete), click
    `FOLDER_MENU_RENAME_ITEM`, wait for `folder_name_input` visible.
  - `is_folder_name_confirm_enabled() -> bool` — read the
    `data-disabled`/`data-enabled` attribute added to
    `folder_name_confirm_button` (exact attribute name/polarity is the
    implementer's call, see § Concrete Handles — keep the page-object method
    name polarity-neutral either way: `True` = clickable/active).
  - `get_folder_name_confirm_tooltip_text() -> str` — `hover()` the confirm
    button first (MUI tooltip content only mounts on hover/focus), THEN read
    the new `chat-folder-name-confirm-tooltip-content` testid's text.
- Steps 4→7 ("AB" then "ABC"): either (a) call `set_folder_name("AB")` then
  `set_folder_name("ABC")` (two full replaces, matches this AFS's and the
  case's literal reading most directly and avoids any incremental-typing
  state assumption), or (b) type "AB" then append "C" via a direct
  `press_sequentially("C")` on the already-focused input (closer to the
  case's literal "type one more character" wording). Both reach the
  identical asserted end state (`"ABC"`, `data-disabled="false"`) — pick
  whichever fits the page object's existing method shapes better; this
  AFS does not mandate one.
- Wait strategy: after clicking the active confirm button (step 9), wait for
  the `PUT .../folder/prompt_lib/{project_id}/{folder_id}` response (or the
  editor's `folder_name_input` to detach) rather than a fixed timeout — the
  rename is a real network round-trip, same class of wait as ELITEA-2132's
  `POST` confirmation.
- **Do not reuse `ChatPage.delete_folder_via_menu()` / `FOLDER_MENU_DELETE_ITEM`
  as a copy-paste template without first checking whether
  EliteaAI/elitea-testing-public#1309 has landed** — as of this analysis pass
  those target a dead testid (see the intro paragraph's adjacent finding).
  `open_folder_rename_editor()` above should be modeled on the SHAPE of
  `delete_folder_via_menu()` (hover → scoped dot-menu → menu item click) but
  target the NEW `chat-folder-menu-rename-menuitem` this case adds, which
  will exist and work regardless of #1309's status.
- Testid provenance summary: 5 of 6 handles this test depends on
  (`chat-folder-name-input`, `-confirm-button`, `-cancel-button`,
  `chat-folder-item-{id}`) are pre-existing on `automation/testids` only
  (commit `6fceb3e2`, not yet on `main`); `conversation-menu-menu-button` is
  the one exception, already on `main`. Three genuinely NEW pieces of work
  this case introduces: the `chat-folder-menu-rename-menuitem` testid, the
  `data-disabled` attribute, and the tooltip-content testid — all land on
  `automation/testids` per the standard `add-data-testid` flow, all pushed,
  none reach `main` without a human cherry-pick (current promotion policy).
