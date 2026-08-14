# Test Case: Chat – Conversation Rename – Cannot Paste More Than 50 Characters

## Metadata
- **TMS ID**: ELITEA-2104
- **Linked Story**: none (`requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Elitea Testing Team", observed live as `projectId=471` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: ready-for-automation
- **family_afs**: false — sibling of ELITEA-2103 (type variant). The two differ in
  ACTION (real clipboard paste vs character-by-character typing), not just in data
  (per `test-case-analysis` § Execute: differ-in-steps → separate AFS files). Both
  executed in the SAME live session (cluster dispatch) and share setup/handles/
  page-object surface with ELITEA-2101/2102/2099/2103.

**Related existing coverage (reused as context/transit, not as a covering spec):**
`test-specs/chat-interface/l3_conversation-rename-length-boundaries_ELITEA-2101_2102.md`
(merged to this batch's trunk) source-confirms `ConversationItem.jsx`'s
`onChangeConversationName` truncates at `MAX_CONVERSATION_LENGTH = 50` on every
`onChange` event — but its AFS explicitly names 2103/2104 as un-covered territory
(truncation itself, never triggered by 49/50-char inputs). This case's own
observable — pasting 60 chars and having the field truncate to 50 — has never been
exercised until this session.
`test-specs/chat-interface/l3_conversation-rename-cannot-type-beyond-50-chars_ELITEA-2103.md`
(sibling, same session) proves the identical `slice(0, 50)` mechanism via TYPING;
this AFS proves the SAME mechanism is reached via PASTE (confirmed by source read:
`ConversationItem.jsx` wires only a single `onChange={onChangeConversationName}` —
no separate `onPaste` handler — so a native paste event, which mutates the DOM input
value and then fires the browser's standard `input`/`change` event, is caught by the
identical handler). Both cases are therefore expected — and live-confirmed — to
truncate identically; the only automation-relevant difference is HOW the 51st+
character reaches the DOM (keystroke vs clipboard).

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- Test creates its own conversation (see § Test Data) — the case's "at least one
  conversation exists" precondition is satisfied by setup, not ambient data.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Active project — whatever `${TEST_USER}`'s default/last-selected project is
  (observed live as "Elitea Testing Team", id 471). Don't hardcode the id.

### generate-per-test (created in setup, cleaned up in teardown)
- **`conv_target`** — the conversation to rename. Create via
  `conversation_api.create_conversation(name)`. Suggested original name:
  `at_rename_paste60_orig`.
- **60-character clipboard string**: `"A" * 60` (case's own Test Data table gives
  the literal 60-A string verbatim).

## Test Steps

1. Hover `conv_target`'s sidebar item, click the three-dot icon
   (`get_conversation_menu_button(conv_target_id)`), click the **Rename** menu item
   (`chat-conversation-menu-rename-menuitem`).
   - **Verify**: the conversation name becomes an editable inline input
     (`chat-conversation-name-input`), pre-filled with the current name.
2. Clear the input (select-all + Backspace, or the input's own clear affordance).
   - **Verify**: the input value is empty (length 0).
3. Write the 60-character string to the REAL system clipboard
   (`page.evaluate("(text) => navigator.clipboard.writeText(text)", text)` — a real
   OS/browser clipboard write, not a DOM injection into the input itself) and paste
   it into the focused input via a real keyboard shortcut
   (`page.keyboard.press("Control+V")`/`"Meta+V"` per platform — the SAME idiom
   already used honestly elsewhere in this suite, see
   `ProjectContextPage.set_editor_content_via_paste()`,
   `automation/pages/project_context_page.py:90-124`). This is NOT a substitution:
   the clipboard write only stages the data a real user would have copied from
   somewhere; the paste itself is a genuine browser paste event dispatched by the
   OS/browser paste shortcut, exercised through the product's own `onChange` handler
   exactly as a user's `Ctrl+V` would be.
   - **Verify**: the input's value has length == 50, not 60 (live-confirmed: pasting
     `"A"*60` leaves the input holding exactly the first 50 characters — same
     `onChangeConversationName` slice as the typing path, since paste triggers the
     identical `onChange` event; no separate paste handler exists).
4. Verify the 51st character and beyond are not present in the input value
   (same length/content read as step 3 — the case's own step 4 restates step 3's
   expected result, no separate assertion target).
5. Click the checkmark (save) icon — an explicit click on
   `chat-conversation-name-confirm-button`.
   - **Verify**: the input closes (`chat-conversation-name-input` no longer
     present); `[data-testid="chat-conversation-item-{conv_target_id}"]` shows the
     new 50-character name in the sidebar. Underlying network call: `PUT
     /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}`
     resolves `200` (live-confirmed this session).
   - **Verify**: no error message is shown — no
     `[data-testid="toast-alert"][data-severity="error"]`; no NEW console errors
     beyond the pre-existing, unrelated `secrets/secrets/default` 403 noise (same
     exclusion as every sibling rename case).

## Expected Results
- Pasting a 60-character clipboard string into the rename input results in exactly
  the first 50 characters landing in the field — characters 51–60 are silently
  dropped by the product's own `onChange` handler (client-side `slice(0, 50)`),
  reached via the SAME code path as typing (ELITEA-2103), not by any test-side
  interception.
- The checkmark saves the resulting 50-character name successfully (`PUT` → `200`,
  no error toast, no new console errors).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: ≥1 conversation exists | — | Setup | `conversation_api.create_conversation` | asserted |
| 1 Navigate, hover, click 3-dot, click Edit → editable | conversation name is editable | step 1 | `chat-conversation-name-input` visible | asserted |
| 2 Clear name → field empty | field empty | step 2 | input value length == 0 | asserted |
| 3 Paste 60-char string via Ctrl+V → field ≤50 chars, truncated | text truncated | step 3 | input value length == 50 after pasting 60 | asserted |
| 4 Verify 51st+ chars not present | only 50 accepted | step 3 (same read) | input value length/content == first 50 of the source string | asserted |
| 5 Click checkmark → saved with exactly 50 chars, no error | rename committed, no error | step 5 | input gone + sidebar text (50 chars) + `PUT …` 200 + toast/console absence | asserted |
| Expected Final State: "pasted text truncated, conversation saved successfully" | — | steps 3, 5 | covered by the rows above | asserted |
| Pass/Fail: "paste truncation works; 50-char limit enforced" | — | steps 3–5 | covered by the rows above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- step 3 additionally asserts the input's exact string value equals the source
  string's first 50 characters (not just the length) — *added: proves a left-slice
  truncation (matching `event.target.value.slice(0, 50)`), not e.g. a dropped or
  reordered paste.*
- step 3/5 additionally asserts `chat-conversation-name-confirm-button`'s
  `data-disabled` flips to `"false"` after the paste — *added: proves the truncated
  50-char value is itself save-enabled, mirrors every sibling rename case's same
  assertion.*
- step 5 asserts the underlying `PUT .../conversation/prompt_lib/{project_id}/{id}`
  network call resolves `200` — *added: proves the save is real
  (backend-persisted).*
- step 5 explicitly asserts no NEW console errors, excluding the pre-existing
  `secrets/secrets/default` 403 noise — *added: standard side-channel discipline,
  consistent with every sibling rename case's AFS.*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)` in a
   `try`/`finally`, per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback
ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). All
handles below are pre-existing (added during ELITEA-2099's implementation,
`EliteaAI/EliteaUI@ff56e29d` on `automation/testids`) — **no new testids needed**.

| Element | Testid handle | Notes / provenance |
|---|---|---|
| Conversation list item (dynamic) | `[data-testid="chat-conversation-item-{id}"]` | Pre-existing class constant (`CONVERSATION_ITEM`). On `main` (pre-existing, long-standing). |
| Conversation 3-dot menu button | `[data-testid="conversation-menu-menu-button"]`, scoped inside `chat-conversation-item-{id}` | Pre-existing (`CONVERSATION_MENU_BUTTON`); use `ChatPage.get_conversation_menu_button(id)`. On `main`. |
| Rename menu item | `[data-testid="chat-conversation-menu-rename-menuitem"]` | Pre-existing (ELITEA-2114, `EliteaAI/EliteaUI@20567b81`). On `automation/testids`. |
| Conversation-rename inline input | `chat-conversation-name-input` | Added ELITEA-2099, `EliteaAI/EliteaUI@ff56e29d`, on `automation/testids`. Live-verified this session: pasting 60 chars leaves exactly 50 in the field. |
| Conversation-rename confirm (checkmark) button | `chat-conversation-name-confirm-button`, carries `data-disabled="true"/"false"` | Same commit `ff56e29d`. Live-verified `data-disabled="false"` after the truncated paste. **A11y-snapshot pruning gotcha applies in the disabled/unchanged state** (`test-specs/chat-interface/_surface.md`) — assert via the testid locator directly, never a `browser_snapshot` accessible-name read. |
| App-wide toast alert (error/success severity) | `[data-testid="toast-alert"][data-severity="{severity}"]` | Pre-existing (`ChatPage.get_toast_alert`, `TOAST_ALERT_SEVERITY`). |

## Network Behavior

- Rename commit (step 5): `PUT
  /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}` → `200`,
  live-confirmed with the truncated 50-character name as the payload's `name`.
- No mutating call fires during steps 2–4 (clear + paste alone) — only the explicit
  checkmark click in step 5 triggers the `PUT`, same as every sibling rename case.
- No clipboard-related network call — `navigator.clipboard.writeText()` is a local
  browser API call, not a network request.

## Known Defects Found During Exploration

None. The case passes end-to-end against the live product exactly as its own case
text expects — pasted characters 51–60 are silently dropped by the product's own
client-side `slice(0, MAX_CONVERSATION_LENGTH)` (the same handler the typing case,
ELITEA-2103, exercises), with no error surfaced on the truncation itself, and the
subsequent save also completes with no error — matching the case's Pass criteria.

## Blocked Steps

None — all 5 case steps executed live end-to-end this session, using the shared
pre-existing "Review attached documents" conversation (id 420) during live
exploration ONLY: renamed to a 50-char truncated-from-60-pasted name, verified, then
restored to its original name ("Review attached documents") immediately after — to
avoid leaving pollution in the shared DEV project. The automated test itself creates
and deletes its own `conv_target` per § Test Data / § Cleanup, so this substitution
is exploration-only and does not appear in the spec.

## Automation Hints

- **Source-confirmed validation logic** (`EliteaUI/src/[fsd]/features/chat/
  conversation-list/ui/conversations/ConversationItem.jsx` +
  `EliteaUI/src/common/constants.js`):
  - `MAX_CONVERSATION_LENGTH = 50` (`constants.js:74`).
  - `onChangeConversationName`: `const newName = event.target.value.slice(0,
    MAX_CONVERSATION_LENGTH)` — wired ONLY to `onChange` (no `onPaste` handler
    exists on the input, confirmed by grep of the component file), so a native
    paste's resulting `input`/`change` event is caught by the identical function
    that handles typing.
  - `ConversationNameRegExp = /^[a-zA-Z0-9_[\].()][a-zA-Z0-9_[\].() -]{2,63}$/`
    (3–64 chars total) — the resulting 50-char all-`A` string easily satisfies this.
- **Paste implementation — reuse the project's own honest paste idiom, don't
  reinvent it.** `automation/pages/project_context_page.py`'s
  `set_editor_content_via_paste()` (lines ~90–124) is the in-repo precedent: real
  `navigator.clipboard.writeText()` + a real `Control+V`/`Meta+V` keypress, platform
  detected via `page.evaluate("() => navigator.platform.includes('Mac')")`. The
  implementer should add an equivalent `ChatPage` method (e.g.
  `paste_conversation_name(text)`) rather than injecting the value via `fill()` or
  `page.evaluate()` directly into the input's DOM value — the latter would bypass
  the browser's native paste event entirely and NOT prove the product's own
  `onChange` handler does the truncating (a terminal-substitution risk this AFS
  explicitly avoids: the observable this case asks for — "pasted text is
  truncated" — must be produced by a REAL paste, not a test-authored one).
  `clipboard-read`/`clipboard-write` permissions are already granted in this
  suite's browser context (same as the existing clipboard tests, e.g.
  `test_agent_copy_version_link.py`).
- **Implementer note**: write this as a NEW test function in the SAME file/class as
  ELITEA-2101/2102/2103
  (`automation/tests/ui/chat/test_conversation_rename_length_boundaries.py`) — same
  page object, same helpers. NOT parametrized together with ELITEA-2103 (differ in
  interaction technique: paste vs type), but a natural neighbor in the same module.
- `.playwright-mcp/console-2026-08-14T21-08-14-439Z.log` (and successors in the same
  session, timestamped ~21:10) capture the full console stream for the clear + paste
  + save sequence; the only new errors are the pre-existing `secrets/secrets/default`
  403 noise (3 cumulative occurrences across both 2103 and 2104's save actions in
  this session, all matching the same exclusion pattern).
