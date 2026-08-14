# Test Case: Chat – Conversation Rename – Cannot Type Beyond 50 Characters

## Metadata
- **TMS ID**: ELITEA-2103
- **Linked Story**: none (`requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Elitea Testing Team", observed live as `projectId=471` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: ready-for-automation
- **family_afs**: false — sibling of ELITEA-2104 (paste variant), but the two cases
  differ in ACTION (character-by-character typing vs a real clipboard paste), not
  just in data, so per `test-case-analysis` § Execute ("differ only in data → family;
  differ in steps → separate") they are two AFS files. Both were executed in the
  SAME live session (cluster dispatch) and share setup/handles/page-object surface
  with ELITEA-2101/2102/2099 — see § Automation Hints for the shared-file recommendation.

**Related existing coverage (reused as context/transit, not as a covering spec):**
`test-specs/chat-interface/l3_conversation-rename-length-boundaries_ELITEA-2101_2102.md`
(→ `automation/tests/ui/chat/test_conversation_rename_length_boundaries.py`, merged to
this batch's trunk) proves the rename mechanics + confirms via source read that
`ConversationItem.jsx`'s `onChangeConversationName` truncates at
`MAX_CONVERSATION_LENGTH = 50` on every `onChange` event — but only exercises 49/50-char
names (never a 51-char input, so never triggers the truncation itself). That AFS's own
Automation Hints flagged 2103/2104 as "not part of this family" — the truncation
boundary itself. Reused here as transit knowledge (flow, testids, source pointer) —
not cited as already covering this case's own observable (typing past 50 and having
the 51st char rejected has never been exercised until this session).

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
  `conversation_api.create_conversation(name)` (fast, no LLM round-trip — matches
  the ELITEA-2099/2101/2102 pattern). Suggested original name: `at_rename_type51_orig`.
- **51-character literal string to type**: `"A" * 51` (case's own Test Data table
  says "51-character string"; a flat repeated character is sufficient — the case
  does not ask for character diversity, only length).

## Test Steps

1. Hover `conv_target`'s sidebar item, click the three-dot icon
   (`get_conversation_menu_button(conv_target_id)`), click the **Rename** menu item
   (`chat-conversation-menu-rename-menuitem`).
   - **Verify**: the conversation name becomes an editable inline input
     (`chat-conversation-name-input`), pre-filled with the current name.
2. Clear the input and TYPE 51 characters via a real character-by-character keyboard
   simulation (`press_sequentially`/`type(..., delay=...)` — NOT `fill()`, which
   bypasses per-keystroke `onChange` events and would not exercise the same code
   path a real user's typing does).
   - **Verify**: the input's value has length == 50, not 51 (live-confirmed: typing
     `"A"*51` character-by-character leaves the input holding exactly the first 50
     characters — the 51st keystroke never lands because `onChangeConversationName`
     slices `event.target.value` to `MAX_CONVERSATION_LENGTH=50` on every change).
     `chat-conversation-name-confirm-button`'s `data-disabled` attribute is
     `"false"` (name changed AND the 50-char all-`A` string passes
     `ConversationNameRegExp`).
3. Verify the character count does not exceed 50 (same assertion as step 2 —
   the case's step 3 restates step 2's expected result; no separate UI character
   counter exists on this editor, unlike the Project-Context editor's char counter,
   so this is the same input-length read, not a second element).
4. Click the checkmark (save) icon — an explicit click on
   `chat-conversation-name-confirm-button`.
   - **Verify**: the input closes (`chat-conversation-name-input` no longer
     present); `[data-testid="chat-conversation-item-{conv_target_id}"]` shows the
     new 50-character name in the sidebar. Underlying network call: `PUT
     /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}`
     resolves `200` (live-confirmed this session).
   - **Verify**: no error message is shown — no
     `[data-testid="toast-alert"][data-severity="error"]`; no NEW console errors
     beyond the pre-existing, unrelated `secrets/secrets/default` 403 noise present
     on every page load in this environment (same exclusion as ELITEA-2099/2101/2102).

## Expected Results
- Typing a 51-character string into the rename input results in exactly the first
  50 characters landing in the field — the 51st keystroke is silently dropped by the
  product's own `onChange` handler (client-side `slice(0, 50)`), not by any test-side
  interception.
- The checkmark saves the resulting 50-character name successfully (`PUT` → `200`,
  no error toast, no new console errors) — the case's own step 4 expects "no error
  shown" for the 50-char SAVE, distinct from the (correctly silent, non-erroring)
  truncation of the 51st character in step 2.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: ≥1 conversation exists | — | Setup | `conversation_api.create_conversation` | asserted |
| 1 Navigate, hover, click 3-dot, click Edit → editable | conversation name is editable | step 1 | `chat-conversation-name-input` visible | asserted |
| 2 Clear + attempt to type 51 chars → only first 50 accepted | 51st char not entered | step 2 | input value length == 50 after typing 51 | asserted |
| 3 Verify character count does not exceed 50 | max 50 enforced | step 2 (same read) | input value length == 50 | asserted |
| 4 Click checkmark → saved with exactly 50 chars, no error | rename committed, no error | step 4 | input gone + sidebar text (50 chars) + `PUT …` 200 + toast/console absence | asserted |
| Expected Final State: "51st char not accepted" | — | step 2 | covered by the row above | asserted |
| Pass/Fail: "50-char limit is enforced" | — | steps 2–4 | covered by the rows above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- step 2 additionally asserts the input's exact string value equals `"A"*50` (not
  just the length) — *added: proves the RIGHT 50 characters survived (a left-slice
  truncation, not e.g. dropped-from-the-middle corruption), matching the live-read
  `event.target.value.slice(0, 50)` semantics exactly.*
- step 2 additionally asserts `chat-conversation-name-confirm-button`'s
  `data-disabled` flips to `"false"` — *added: proves the truncated 50-char value is
  itself a valid, save-enabled state, not a broken intermediate one; mirrors
  ELITEA-2099/2101/2102's same assertion.*
- step 4 asserts the underlying `PUT .../conversation/prompt_lib/{project_id}/{id}`
  network call resolves `200` — *added: proves the save is real
  (backend-persisted), not a client-side-only list splice.*
- step 4 explicitly asserts no NEW console errors, excluding the pre-existing
  unrelated `secrets/secrets/default` 403 noise — *added: standard side-channel
  discipline, same exclusion already documented for ELITEA-2099/2100/2101/2102/2114.*

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
| Conversation-rename inline input | `chat-conversation-name-input` | Added ELITEA-2099, `EliteaAI/EliteaUI@ff56e29d`, on `automation/testids`. Live-verified this session: typing 51 chars leaves exactly 50 in the field. |
| Conversation-rename confirm (checkmark) button | `chat-conversation-name-confirm-button`, carries `data-disabled="true"/"false"` | Same commit `ff56e29d`. Live-verified `data-disabled="false"` after the truncated 50-char value. **A11y-snapshot pruning gotcha applies in the disabled/unchanged state** (`test-specs/chat-interface/_surface.md`) — assert via the testid locator directly, never via a `browser_snapshot` accessible-name read. |
| App-wide toast alert (error/success severity) | `[data-testid="toast-alert"][data-severity="{severity}"]` | Pre-existing (`ChatPage.get_toast_alert`, `TOAST_ALERT_SEVERITY`). |

## Network Behavior

- Rename commit (step 4): `PUT
  /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}` → `200`,
  live-confirmed with the truncated 50-character name as the payload's `name`.
- No mutating call fires during step 2 (typing alone) — only the explicit checkmark
  click in step 4 triggers the `PUT`, same as every sibling rename case.

## Known Defects Found During Exploration

None. The case passes end-to-end against the live product exactly as its own case
text expects — the 51st character is silently dropped by the product's own
client-side `slice(0, MAX_CONVERSATION_LENGTH)`, with no error surfaced (correct —
the case's Pass criteria explicitly does NOT ask for an error on truncation, only on
the later save step, and no error appears there either).

## Blocked Steps

None — all 4 case steps executed live end-to-end this session, using the shared
pre-existing "Review attached documents" conversation (id 420) during live
exploration ONLY: renamed to a 50-char truncated-from-51 name, verified, then
restored to its original name ("Review attached documents") immediately after — to
avoid leaving pollution in the shared DEV project. The automated test itself creates
and deletes its own `conv_target` per § Test Data / § Cleanup, so this substitution
is exploration-only and does not appear in the spec.

## Automation Hints

- **Source-confirmed validation logic** (`EliteaUI/src/[fsd]/features/chat/
  conversation-list/ui/conversations/ConversationItem.jsx` +
  `EliteaUI/src/common/constants.js`), grounds every assertion in this AFS:
  - `MAX_CONVERSATION_LENGTH = 50` (`constants.js:74`).
  - `onChangeConversationName`: `const newName = event.target.value.slice(0,
    MAX_CONVERSATION_LENGTH)` — fires on every `onChange` (keystroke), which is
    exactly why per-keystroke simulation (`press_sequentially`) is required, not
    `fill()` (a single DOM mutation that only fires one `onChange` with the whole
    string — Playwright's native input-event dispatch means `fill()` would ALSO be
    sliced correctly by React, since the underlying DOM `input` event still carries
    the full pasted-equivalent value through the same handler; either approach is
    expected to land on the same 50-char result, but `press_sequentially` is
    preferred here because it matches the case's own literal instruction to
    "attempt to type" character-by-character).
  - `ConversationNameRegExp = /^[a-zA-Z0-9_[\].()][a-zA-Z0-9_[\].() -]{2,63}$/`
    (3–64 chars total) — the resulting 50-char all-`A` string easily satisfies this.
- **Implementer note**: write this as a NEW test function in the SAME file/class as
  ELITEA-2101/2102's `test_conversation_rename_length_boundary`
  (`automation/tests/ui/chat/test_conversation_rename_length_boundaries.py`) — same
  page object, same helpers (`ChatPage.get_conversation_menu_button`,
  `click_conversation_menu_item("rename")`, `chat.set_conversation_name` or an
  equivalent `press_sequentially` call). This is NOT a `@pytest.mark.parametrize`
  merge with 2101/2102 (different expected outcome shape — truncation vs no
  truncation — and different literal length), but it belongs in the same module as
  a related, non-duplicative test of the same input.
- **Sibling**: ELITEA-2104 (paste variant) is analysed in the SAME session — see
  `test-specs/chat-interface/l3_conversation-rename-cannot-paste-beyond-50-chars_ELITEA-2104.md`.
  Consider placing both new test functions in the same file/class for locality
  (same fixtures, same helpers), but each is its own test function — they are NOT
  parametrized together (differ in interaction technique, not just data).
- `.playwright-mcp/console-2026-08-14T21-08-14-439Z.log` (and successors in the same
  session) capture the full console stream for this rename+save; the only new
  errors are the pre-existing `secrets/secrets/default` 403 noise.
