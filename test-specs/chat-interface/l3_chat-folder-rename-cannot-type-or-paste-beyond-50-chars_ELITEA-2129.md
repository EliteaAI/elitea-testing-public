# Test Case: Chat – Folder Rename – Cannot Type or Paste Beyond 50 Characters

## Metadata
- **TMS ID**: ELITEA-2129
- **Linked Story**: none (`requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Elitea Testing Team", observed live as `projectId=399` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer)
- **Status**: ready-for-automation
- **family_afs**: false — sibling of ELITEA-2128 (same underlying
  `MAX_CONVERSATION_LENGTH` mechanism), but the two cases differ in ACTION
  (exact-boundary acceptance vs overflow-truncation), so per `test-case-analysis`
  § Execute ("differ only in data → family; differ in steps → separate") they are
  two AFS files. Unlike the conversation-rename precedent (ELITEA-2103/2104, which
  split type-only and paste-only into TWO separate cases), THIS case's own steps
  bundle BOTH type-overflow (step 2) and paste-overflow (step 3) into ONE flow —
  so this AFS covers both interaction techniques in a single test function, per the
  case's own step sequence, not split further.

**Related existing coverage (reused as context/transit, not as a covering spec):**
`test-specs/chat-interface/l3_chat-folder-rename-max-50-chars-accepted_ELITEA-2128.md`
(same live session, same folder-creation/rename-editor mechanics) — reused as
transit knowledge for the editor-opening flow; not cited as covering this case's own
overflow/truncation observable, which ELITEA-2128 never exercises (its own 50-char
input never reaches the 51st character).
`test-specs/chat-interface/l3_conversation-rename-cannot-type-beyond-50-chars_ELITEA-2103.md`
and `l3_conversation-rename-cannot-paste-beyond-50-chars_ELITEA-2104.md` (sibling
entity, conversations not folders) prove the SAME `MAX_CONVERSATION_LENGTH = 50`
slice-truncation mechanism on the analogous conversation-rename editor, including
the same real-clipboard-paste idiom (`ConversationItem.jsx`'s `onChangeConversationName`
has no separate `onPaste` handler — a paste reaches the same `onChange` code path
as typing). Reused as source-level + technique precedent, confirmed independently
against the FOLDER editor this session (source read of `FolderItem.jsx` + live
execution — see § Concrete Handles / § Automation Hints).

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- Test creates its own folder (see § Test Data) — the case's "at least one existing
  folder is present" precondition is satisfied by setup, not ambient data.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Active project — whatever `${TEST_USER}`'s default/last-selected project is
  (observed live as "Elitea Testing Team", id 399). Don't hardcode the id.

### generate-per-test (created in setup, cleaned up in teardown)
- **`folder_target`** — the folder to rename. Create via the UI's own
  "Create folder" button + `set_folder_name()` + confirm (same setup as ELITEA-2128
  — no folder-creation API client exists on this project). Suggested original name:
  `at_folder_overflow_orig`.
- **51-character literal string to type**: `"B" * 51` (case's own step 2 says
  "attempt to type 51+ characters" — a flat repeated character is sufficient, the
  case does not ask for character diversity).
- **70-character literal string to paste** (case's own Test Data table: "70-char
  clipboard"): `"C" * 70`.

## Test Steps

1. Navigate to Chats, hover `folder_target`'s row, click the three-dot icon
   (`open_folder_rename_editor(folder_target_id)`), which opens the **Rename**
   item (labelled "Rename", not "Edit" — see § Known Defects Found).
   - **Verify**: the folder name becomes an editable inline input
     (`chat-folder-name-input`), pre-filled with the current name and focused.
2. Clear the input and attempt to TYPE 51 characters via a real
   character-by-character keyboard simulation (`press_sequentially`/
   `type(..., delay=...)` — NOT `fill()`, which bypasses per-keystroke `onChange`
   events and would not exercise the same code path a real user's typing does).
   - **Verify**: the input's value has length == 50, not 51 (live-confirmed this
     session, on the actual RENAME path — not just the create-folder editor:
     typing `"B"*51` character-by-character leaves the input holding exactly the
     first 50 characters; the 51st keystroke never lands because
     `onChangeFolderName` slices `event.target.value` to
     `MAX_CONVERSATION_LENGTH=50` on every change). `chat-folder-name-confirm-
     button`'s `data-disabled` attribute is `"false"` (name changed AND the
     50-char all-`B` string passes `ConversationNameRegExp`).
   - **Case-text drift, live-reconfirmed**: the case's own Steps-table Expected
     Result for this step reads *"Only first **64** characters accepted; 65th is
     not entered"* — this contradicts the case's own title ("...Beyond **50**
     Characters"), its own step 3 ("no more than **50** characters after paste"),
     its own step 4 ("saved with exactly **50** characters"), and its own Test
     Data table (a 70-char *paste* string, not a 65-char one). Live execution
     confirms the case's TITLE and steps 3/4 are correct and step 2's "64"/"65th"
     wording is a copy-paste slip (64 is `ConversationNameRegExp`'s CHARSET/regex
     ceiling — a distinct gate documented in `FolderItem.jsx`'s source, see
     § Automation Hints — not the input-length truncation this step actually
     tests). The AFS/spec assert the LIVE, internally-consistent 50-character
     boundary; a lightweight case-text CLARIFICATION is warranted for the TMS
     case's step 2 wording (not a product bug — see § Known Defects Found).
3. Clear the input (isolates the paste technique from step 2's typed value —
   same pattern ELITEA-2104's own case text uses for the conversation-entity
   sibling, "Clear the input" as its own step before the paste), then prepare a
   70-character string and paste it using a REAL system clipboard write
   (`navigator.clipboard.writeText`) + a genuine `Control+V`/`Meta+V` keypress —
   NOT a DOM-injected value, which would substitute the test for the browser's
   own paste event.
   - **Live-confirmed, both variants tried this session**: pasting 70 chars
     WITHOUT first clearing (directly appending at the cursor, positioned at the
     end of step 2's already-50-char truncated value) is a NO-OP — the browser
     computes the raw concatenated value (`"B"*50 + "C"*70` = 120 chars) BEFORE
     `onChangeFolderName` fires, and `.slice(0, 50)` then returns exactly the
     original first 50 characters, so the field visibly does not change (still
     `"B"*50`). This technically also satisfies the case's Expected Result
     ("no more than 50 characters after paste" — 50 ≤ 50), but is a weaker,
     easily-misread signal (a reader could mistake "value unchanged" for "the
     interaction did nothing" rather than "truncation is still active"). Clearing
     first, per ELITEA-2104's own precedent, produces the STRONGER, unambiguous
     signal: the field shows the pasted content ITSELF truncated to exactly the
     first 50 characters (`"C"*50`), directly proving the truncation logic
     operates on the pasted content, not just coincidentally on old content.
   - **Verify**: the input's value has length <= 50 after the paste (live-confirmed
     this session, on a CLEARED field: pasting `"C"*70` results in exactly the
     first 50 characters landing, characters 51-70 silently dropped — reached via
     the SAME `onChangeFolderName` code path as typing, since no separate
     `onPaste` handler exists on `FolderItem.jsx`'s input, source-confirmed).
4. Click the checkmark (save) icon — an explicit click on
   `chat-folder-name-confirm-button`.
   - **Verify**: the input closes (`chat-folder-name-input` no longer present);
     `[data-testid="chat-folder-item-{folder_target_id}"]` shows the new,
     exactly-50-character name. Underlying network call: `PUT
     /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_target_id}`
     resolves `200` (live-confirmed this session).
   - **Verify**: no error message is shown — no
     `[data-testid="toast-alert"][data-severity="error"]`; no NEW console errors
     beyond the pre-existing, unrelated `secrets/secrets/default` 403 noise present
     on every page load in this environment (same exclusion as every sibling
     rename case).

## Expected Results
- Typing beyond 50 characters (51+) results in exactly the first 50 characters
  landing in the field — the 51st+ keystroke is silently dropped by the product's
  own `onChange` handler (client-side `slice(0, 50)`), not by any test-side
  interception.
- Pasting a 70-character clipboard string results in exactly 50 characters landing
  (characters 51-70 dropped), via the SAME truncation mechanism.
- The checkmark saves the resulting 50-character name successfully (`PUT` → `200`,
  no error toast, no new console errors), matching the case's own Pass criteria
  ("50-character limit enforced for type and paste").

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: ≥1 folder exists | — | Setup | UI create-folder + `set_folder_name` | asserted |
| 1 Navigate, hover, click 3-dot, click Edit → editable | folder name is editable | step 1 | `chat-folder-name-input` visible | asserted |
| 2 Clear + type 51+ chars → "only first 64 accepted; 65th not entered" | length capped | step 2 | input value length == 50 after typing 51 (live-reconfirmed 50 is the real, internally-consistent boundary; "64"/"65th" is case-text drift — see step 2's own note) | asserted (with documented drift) |
| 3 Paste 70-char string → input has ≤50 chars | paste truncated to 50 | step 3 | input value length == 50 after pasting 70 chars | asserted |
| 4 Click checkmark → saved with exactly 50 chars, no error | folder saved, no error | step 4 | input gone + folder item text (50 chars) + `PUT …` 200 + toast/console absence | asserted |
| Expected Final State: "enforces 50-char max for both typing and paste" | — | steps 2–4 | covered by the rows above | asserted |
| Pass/Fail: "50-character limit enforced for type and paste" | — | steps 2–4 | covered by the rows above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- step 2 additionally asserts the input's exact string value equals `"B"*50` (not
  just the length) — *added: proves a left-slice truncation (first 50 chars kept),
  not e.g. dropped-from-the-middle corruption.*
- step 2 additionally asserts `chat-folder-name-confirm-button`'s `data-disabled`
  flips to `"false"` — *added: proves the truncated 50-char value is itself a
  valid, save-enabled state, mirrors ELITEA-2103's same assertion on the
  conversation entity.*
- step 3 additionally asserts the input's exact string value equals the first 50
  characters of the pasted 70-char string (`"C"*50`) — *added: same left-slice
  proof as step 2, for the paste path specifically.*
- step 4 asserts the underlying `PUT .../folder/prompt_lib/{project_id}/{id}`
  network call resolves `200` — *added: proves the save is real
  (backend-persisted), not a client-side-only list splice.*
- step 4 explicitly asserts no NEW console errors, excluding the pre-existing
  unrelated `secrets/secrets/default` 403 noise — *added: standard side-channel
  discipline, same exclusion already documented for every sibling rename case.*

## Cleanup
1. Delete `folder_target` via `chat.delete_folder_via_api(folder_id)` in a
   `try`/`finally`, per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback
ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). All
handles below are pre-existing (added during ELITEA-2458's implementation,
`EliteaAI/EliteaUI@0298860f`, on `automation/testids`) — **no new testids needed**.

| Element | Testid handle | Notes / provenance |
|---|---|---|
| Folder row (dynamic) | `[data-testid="chat-folder-item-{id}"]` | Pre-existing class constant (`FOLDER_ITEM`). On `main`. |
| Folder icon (hover target to reveal dot-menu) | `[data-testid="chat-folder-icon"]`, scoped inside `chat-folder-item-{id}` | Pre-existing (`FOLDER_ICON`). On `main`. |
| Folder 3-dot menu button | `[data-testid="conversation-menu-menu-button"]`, scoped inside `chat-folder-item-{id}` | Shared, non-unique testid — `ChatPage.open_folder_rename_editor()` scopes it with `.first`. On `main`. |
| Rename dot-menu item | `chat-folder-menu-rename-menuitem` | Added ELITEA-2458, `EliteaAI/EliteaUI@0298860f`, on `automation/testids`. |
| Folder-rename inline input | `chat-folder-name-input` | Pre-existing. On `main`. Live-verified this session on the RENAME path: typing 51 chars truncates to 50; pasting 70 chars truncates to 50. |
| Folder-rename confirm (checkmark) button | `chat-folder-name-confirm-button`, carries `data-disabled="true"/"false"` | Added ELITEA-2458, `EliteaAI/EliteaUI@0298860f`, on `automation/testids`. Live-verified `data-disabled="false"` after both the truncated-typed and truncated-pasted 50-char values. **A11y-snapshot pruning gotcha applies** (`test-specs/chat-interface/_surface.md` § Folder rename editor) — assert via the testid locator directly. |
| App-wide toast alert (error/success severity) | `[data-testid="toast-alert"][data-severity="{severity}"]` | Pre-existing (`ChatPage.get_toast_alert`, `TOAST_ALERT_SEVERITY`). |

## Network Behavior

- Rename commit (step 4): `PUT
  /api/v2/elitea_core/folder/prompt_lib/{project_id}/{folder_target_id}` → `200`,
  live-confirmed with the truncated 50-character name as the payload's `name`.
- No mutating call fires during steps 2-3 (typing/pasting alone) — only the
  explicit checkmark click in step 4 triggers the `PUT`, same as every sibling
  rename case.
- Folder creation (setup): `POST /api/v2/elitea_core/folder/prompt_lib/{project_id}`
  → `201`.

## Known Defects Found During Exploration

None. The case passes end-to-end against the live product exactly as its own
TITLE, Test Data, steps 3-4, and Pass/Fail criteria expect — both typing and
pasting are capped at exactly 50 characters via the product's own client-side
`slice(0, MAX_CONVERSATION_LENGTH)`, with no error surfaced (correct — the case's
Pass criteria explicitly does NOT ask for an error on truncation, only "no error
shown" for the final save, which also passes clean).

**Case-text drift (this case's own internal inconsistency, distinct from the
"Edit"-vs-"Rename" drift already documented elsewhere)**: step 2's Expected Result
column says "Only first **64** characters accepted; 65th is not entered" — this
contradicts the case's own title, Test Data, and steps 3-4, all of which correctly
say 50. Live execution confirms 50 is the real, internally-consistent boundary
(matches the shared `MAX_CONVERSATION_LENGTH` constant also governing conversation
rename, `.agents/testing.md`-documented). Recommend a lightweight case-text
CLARIFICATION on the TMS case (step 2's Expected Result column), per
`.agents/profile.md` § Bug filing style — NOT a product bug (the product's actual
behavior is correct and consistent; only the case's own step 2 wording is wrong).
This AFS/spec assert the live, correct 50-character behavior throughout, per the
reverse-masking guard (`test-automation-implementation` skill § Hard Rules → 2) —
asserting "64"/"65th" here would be asserting a stale, self-contradicted hypothesis
against a product that is demonstrably not following it.

## Blocked Steps

None — all 4 case steps executed live end-to-end this session against a real
folder created via the UI (id 250, deleted via the UI's own Delete flow immediately
after exploration, zero net pollution): opened the rename editor via the dot-menu,
typed 51 characters (truncated to 50, confirmed via `element.value` reads), tried
pasting a 70-character clipboard string BOTH without clearing first (a no-op —
value stayed the original truncated 50 chars, see step 3's note) and after
clearing first (truncated to the pasted content's own first 50 chars) via a real
`navigator.clipboard.writeText()` + `Control+V`-equivalent keypress, then saved
successfully (`data-disabled="false"` before save, DOM re-rendered the 50-char
name after).

## Automation Hints

- **Source-confirmed validation logic** (`EliteaUI/src/[fsd]/features/chat/
  conversation-list/ui/folders/FolderItem.jsx` + `EliteaUI/src/common/
  constants.js`), grounds every assertion in this AFS:
  - `MAX_CONVERSATION_LENGTH = 50` (`constants.js:74`); `onChangeFolderName`
    (`FolderItem.jsx:178-186`) does `const newName = event.target.value.slice(0,
    MAX_CONVERSATION_LENGTH); setFolderName(newName);` on every `onChange` — this
    is the SAME mechanism `ConversationItem.jsx`'s `onChangeConversationName` uses
    (ELITEA-2103/2104), confirmed independently for the FOLDER component this
    session (grep + line-read, not assumed from the conversation sibling).
  - No separate `onPaste` handler exists on the input (grep-confirmed) — a paste's
    resulting native `input`/`change` event is caught by the exact same
    `slice(0, MAX_CONVERSATION_LENGTH)` logic as typing, live-confirmed by pasting
    directly (see § Blocked Steps).
  - `ConversationNameRegExp = /^[a-zA-Z0-9_[\].()][a-zA-Z0-9_[\].() -]{2,63}$/`
    (3-64 chars total) is a SEPARATE, wider gate governing CHARSET/first-char
    validity — this is where the case's erroneous "64"/"65th" wording likely
    originated (a mix-up between the length-slice ceiling, 50, and the regex's
    charset-ceiling, 64) — irrelevant to this case's actual observable (the
    50-char all-`B`/`C` strings easily satisfy the regex; the length slice is the
    only gate this case's steps exercise).
- **Paste idiom precedent**: `ChatPage.paste_conversation_name()`
  (`automation/pages/chat_page.py:3731`) — real clipboard write +
  `Control+V`/`Meta+V` keypress, NOT `fill()`/`page.evaluate()` injection. No
  folder equivalent exists yet — **add `paste_folder_name()`, mirroring
  `paste_conversation_name()`'s exact implementation** (same docstring rationale,
  same clipboard-write + platform-aware keypress). Also add `clear_folder_name()`
  mirroring `clear_conversation_name()`, so step 2→3's "type 51, then paste 70
  over it" sequence has a clean, isolated per-step API (mirrors the existing
  `clear_conversation_name()`/`paste_conversation_name()` split rather than
  inlining `.clear()` calls into the test body).
- **Implementer note**: write this as the SECOND test function in the SAME file as
  ELITEA-2128, `automation/tests/ui/chat/test_chat_folder_rename_length_boundaries.py`
  — same page object (`ChatPage`), same helpers, same
  `_is_known_secrets_403`/console-listener/put-capture idioms already established
  by `test_chat_folder_rename_checkmark_validation.py` and
  `test_conversation_rename_length_boundaries.py`.
- `.playwright-mcp/console-2026-08-15T06-14-07-970Z.log` (session-wide) captures
  the full console stream; the 4 ERROR-level entries recorded are all this
  analyst's own manual cross-origin cleanup probes (CORS-blocked `fetch()` to
  `dev.elitea.ai`), not product errors, and not reachable from the shipped test.
