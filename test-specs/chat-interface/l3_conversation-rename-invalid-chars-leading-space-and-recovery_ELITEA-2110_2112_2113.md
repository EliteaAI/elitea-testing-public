# Test Case: Chat – Conversation Rename – Invalid Characters / Leading Space / Recovery After Invalid Input

## Metadata
- **TMS IDs**: ELITEA-2110, ELITEA-2112, ELITEA-2113
  (family AFS — all three drive the SAME `isSaveEnabled`/`ConversationNameRegExp`
  gate on the SAME inline rename editor as ELITEA-2105-2109, differing only in
  the specific invalid-then-valid data fed into the input: special characters,
  a leading space, and a full invalid→valid recovery-and-save cycle)
- **Linked Story**: none (all three `requirements: []`)
- **Priority**: l3 (case priority: medium, all three)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Elitea Testing Team", observed live as `projectId=471` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent, combined analyst+implementer slot)
- **Status**: ready-for-automation (all three members)
- **family_afs**: true — one parameterized spec (plus one standalone recovery
  test for ELITEA-2113) covers all three TMS cases

**Related existing coverage (reused as context/transit, not as a covering spec):**
`test-specs/chat-interface/l3_conversation-rename-checkmark-active-inactive-states_ELITEA-2105_2106_2107_2108_2109.md`
(→ `automation/tests/ui/chat/test_conversation_rename_checkmark_active_state.py`,
on this batch trunk) proves the SAME `isSaveEnabled`/`ConversationNameRegExp` gate
for length-boundary invalid states (empty/1-char/2-char) and the 2→3-char
activation transition, and already establishes the "click a disabled checkmark
is a genuine no-op" idiom (`onClick={isSaveEnabled ? handler : null}`) this
family reuses verbatim. That family does NOT exercise: (a) a CHARSET failure
(all its invalid rows are too-short, not wrong-character); (b) a leading-space
failure specifically; (c) the tooltip/validation-message content; (d) a full
invalid→valid RECOVERY-and-save cycle (2109 goes straight from 2 to 3 valid
chars, never through an invalid-charset detour). ELITEA-2099's own § Automation
Hints forecast this cluster too ("special-char checkmark-inactive states,
tooltip content"). This family covers exactly that remainder — not an extension
of the 2105-2109 spec (different assertion shape: tooltip content + charset/
first-char regex branch, not just the length branch), so `ready-for-automation`.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- Test creates its own conversation (see § Test Data) — the cases' "at least one
  conversation exists" precondition is satisfied by setup, not ambient data.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Active project — whatever `${TEST_USER}`'s default/last-selected project is
  (observed live as "Elitea Testing Team", id 471). Don't hardcode the id.

### generate-per-test (created in setup, cleaned up in teardown)
- **`conv_target`** — the conversation to rename, one per parameter row. Create via
  `conversation_api.create_conversation(name)` (fast, no LLM round-trip — same
  pattern as the 2105-2109 family). Suggested original name:
  `at_rename_invalid_orig` (23 chars — itself VALID per `ConversationNameRegExp`,
  so the "invalid" assertions test the CHARSET/first-char branch, not an
  unrelated "unchanged" branch).

### Parameter table (one row per TMS case)

| TMS ID | Scenario | Input action | Expected input value | Expected `data-disabled` | Tooltip asserted | Click behavior |
|---|---|---|---|---|---|---|
| ELITEA-2110 | Special characters rejected | Clear + type `"HI Chat$$%"` | `"HI Chat$$%"` | `"true"` | yes — exact `ConversationNameWarningMessage` text | no-op: editor stays open, no PUT, name unchanged in sidebar/API |
| ELITEA-2112 | Leading space rejected | Clear + press Space, then type 2 valid chars (`" ab"`, as sequential keystrokes) | `" ab"` | `"true"` | yes — same message (Axis-2 addition, see below) | no-op: same as above |
| ELITEA-2113 | Recovery after invalid → valid | Clear + type invalid (`"$$%%"`, checkmark inactive) → clear + type `"Chat 01 (test)."` | `"$$%%"` then `"Chat 01 (test)."` | `"true"` then `"false"` | not required by the case (not asserted) | click on `"Chat 01 (test)."` SAVES successfully |

## Test Steps

### Shared shape A — ELITEA-2110/2112 (checkmark stays inactive, tooltip shown, click is a no-op)

**Setup (not a numbered case step)**
0. Create `conv_target` via `conversation_api.create_conversation("at_rename_invalid_orig")`.
   Navigate to `${BASE_URL}/chat`.

1. Hover `conv_target`'s sidebar item, click the three-dot icon
   (`get_conversation_menu_button(conv_target_id)`), click the **Rename** menu item
   (`chat-conversation-menu-rename-menuitem`).
   - **Verify**: the conversation name becomes an editable inline input
     (`chat-conversation-name-input`), pre-filled with the current name.
2. Clear the input and apply the row's input action (type the special-char
   string / press Space then type 2 valid chars).
   - **Verify**: `chat-conversation-name-input`'s value matches the row's
     "Expected input value" exactly.
3. Hover the checkmark icon and verify a tooltip/hint appears with the exact
   validation-rule text; verify the checkmark icon is disabled/inactive.
   - **Verify**: `chat-conversation-name-confirm-tooltip-content`'s text equals
     `ConversationNameWarningMessage` verbatim ("The chat name should be 3 to 64
     characters long. It can include letters (a-z, A-Z), numbers (0-9),
     underscores (_), brackets ([]), parentheses (()), dots (.), hyphen(-), and
     spaces. Please note that the first character should not be a space.");
     `chat-conversation-name-confirm-button`'s `data-disabled` attribute is
     `"true"` (`is_conversation_name_confirm_enabled()` returns `False`).
4. Attempt to click the checkmark icon.
   - **Verify**: click has no effect — same source-confirmed no-op mechanism as
     the 2105-2109 family (`onClick={isSaveEnabled ? handler : null}`, `null`
     when disabled): (a) no `PUT /conversation/prompt_lib/{project_id}/{conv_target_id}`
     request fires (captured via `capture_requests_matching`, confirmed empty
     after `chat.wait_for_network()` settles); (b) the inline input remains OPEN
     with the same (unsaved) value; (c) the conversation's PERSISTED name (read
     via `conversation_api.get_conversation(id)["name"]`, the real backend
     record) is still the ORIGINAL name `at_rename_invalid_orig`.

### Shared shape B — ELITEA-2113 (invalid → valid recovery, successful save)

**Setup (not a numbered case step)**
0. Create `conv_target` via `conversation_api.create_conversation("at_rename_invalid_orig")`.
   Navigate to `${BASE_URL}/chat`.

1. Hover `conv_target`'s sidebar item, click the three-dot icon, click the
   **Rename** menu item.
   - **Verify**: inline input editable, pre-filled with the current name.
2. Clear the current name and type invalid characters (`"$$%%"`).
   - **Verify**: `chat-conversation-name-input` value == `"$$%%"`; checkmark
     icon is inactive (`data-disabled="true"`).
3. Clear the invalid input and type `"Chat 01 (test)."`.
   - **Verify**: `chat-conversation-name-input` value == `"Chat 01 (test)."`;
     checkmark icon becomes active (`data-disabled="false"`); no validation
     error/tooltip shown (title is empty per `isConversationNameValid ? '' :
     ConversationNameWarningMessage` — asserted indirectly by the confirm
     button's enabled state; no separate error toast).
4. Click the checkmark icon.
   - **Verify**: input closes (`chat-conversation-name-input` no longer
     present); `chat-conversation-item-{conv_target_id}` shows `"Chat 01
     (test)."` in the sidebar. Underlying network call: `PUT
     /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}`
     resolves `200`.
5. Verify no error message is shown.
   - **Verify**: no `[data-testid="toast-alert"][data-severity="error"]` present.

## Expected Results
- The checkmark (save) icon stays disabled (`data-disabled="true"`) for a
  charset-invalid name (special characters) and for a name whose first
  character is a space — two independent ways `ConversationNameRegExp` fails
  (character-class violation, first-char-class violation) that the 2105-2109
  family's length-only rows never exercised.
- Hovering the disabled checkmark shows the exact `ConversationNameWarningMessage`
  validation tooltip.
- In every disabled state, clicking the checkmark is a genuine no-op: no
  network mutation, no editor close, no name change.
- Replacing an invalid value with a valid one (`"Chat 01 (test)."`) activates
  the checkmark and a click saves successfully with no error shown.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: ≥1 conversation exists | — | Setup | `conversation_api.create_conversation` | asserted |
| ELITEA-2110 step 1 Navigate/hover/3-dot/Edit → editable | editable | Shape A step 1 | `chat-conversation-name-input` visible + value | asserted |
| ELITEA-2110 step 2 Clear + type 'HI Chat$$%', hover checkmark → tooltip appears | tooltip appears | Shape A steps 2-3 | tooltip text non-empty via testid locator | asserted |
| ELITEA-2110 step 3 Tooltip text indicates allowed chars/first-char rule | correct message | Shape A step 3 | exact `ConversationNameWarningMessage` string match | asserted |
| ELITEA-2110 step 4 Checkmark disabled | inactive | Shape A step 3 | `data-disabled == "true"` | asserted |
| ELITEA-2110 step 5 Click checkmark → no effect | click no-op | Shape A step 4 | no PUT + input open + persisted name unchanged (API) | asserted |
| ELITEA-2110 step 6 Name remains unchanged | unchanged | Shape A step 4 | `conversation_api.get_conversation(id)["name"]` == original | asserted |
| ELITEA-2112 step 1 Navigate/hover/3-dot/Edit → editable | editable | Shape A step 1 | same as above | asserted |
| ELITEA-2112 step 2 Space as first char + 2 valid chars | space rejected | Shape A step 2 | input value == `" ab"`, `data-disabled == "true"` | asserted |
| ELITEA-2112 step 3 Checkmark stays inactive, not clickable | inactive + no-op | Shape A steps 3-4 | `data-disabled == "true"` + no PUT fires + input open | asserted |
| ELITEA-2113 step 1 Navigate/hover/3-dot/Edit → editable | editable | Shape B step 1 | same as above | asserted |
| ELITEA-2113 step 2 Type invalid chars → checkmark inactive | inactive | Shape B step 2 | input == `"$$%%"` + `data-disabled == "true"` | asserted |
| ELITEA-2113 step 3 Clear + type "Chat 01 (test)." → checkmark active, no error | active, no error | Shape B step 3 | input == valid name + `data-disabled == "false"` | asserted |
| ELITEA-2113 step 4 Click checkmark → renamed in left panel | rename committed | Shape B step 4 | input gone + sidebar text + `PUT` 200 | asserted |
| ELITEA-2113 step 5 No error message shown | no error | Shape B step 5 | no `toast-alert[data-severity="error"]` | asserted |
| Each case's Expected Final State | — | shape steps | covered by rows above | asserted |
| Each case's Pass/Fail criteria | — | shape steps | covered by rows above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Shape A step 3 asserts the tooltip for **BOTH** ELITEA-2110 and ELITEA-2112,
  even though ELITEA-2112's own case text only says "checkmark remains inactive
  and is not clickable" (no explicit tooltip step) — *added: source-confirmed
  (live-verified this session) that `ConversationItem.jsx` shows ONE static
  `ConversationNameWarningMessage` for ANY regex-failure reason (charset,
  first-char, or length) — the same mechanism the folder-rename family already
  established for `FolderItem.jsx`. Asserting it uniformly across both
  charset-invalid rows grounds the disabled state in the actual validation
  message, not just the `data-disabled` bit, at zero extra cost since both rows
  share the same test shape.*
- Shape A step 4 asserts NO `PUT .../conversation/prompt_lib/...` request fires
  on a disabled-checkmark click, for both invalid rows — *added, same rationale
  as the 2105-2109 family: the strongest, most honest proof of "click has no
  effect" is the network-silence, not just a DOM read.*
- Shape A step 4 asserts the sidebar/API-persisted name is still the ORIGINAL
  name, never the typed-but-unsaved value — *added: distinguishes "input shows
  the typed value" from "the conversation was actually renamed", same
  distinction as the 2105-2109 family.*
- ELITEA-2112's input action is executed as genuinely SEQUENTIAL keystrokes
  (press Space, then type "ab") via `press_sequentially`, not a single
  `fill(" ab")` — *added: the case's own step 2 says "press the Space key as
  the first character, THEN enter 2 more", a real incremental-typing action,
  matching the same discipline the 2105-2109 family applied to ELITEA-2109's
  2→3-char transition.*
- ELITEA-2113 step 5's "no error message shown" is asserted via the absence of
  the app-wide error toast testid (`toast-alert[data-severity="error"]"`),
  reusing the same handle the 2105-2109 family used for its equivalent check —
  *added: the case's own text doesn't name a specific handle, this grounds the
  assertion in a real, already-proven-stable observable rather than a generic
  "no error" prose claim.*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)` in a
   `try`/`finally`, per `.claude/rules/ui-tests.md` § Test Data Lifecycle — one
   `conv_target` per TMS case (three total: two Shape-A rows share the
   parametrize, one Shape-B `conv_target` for ELITEA-2113).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback
ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`).

| Element | Testid handle | Notes / provenance |
|---|---|---|
| Conversation list item (dynamic) | `[data-testid="chat-conversation-item-{id}"]` | Pre-existing (`CONVERSATION_ITEM`). On `main`. |
| Conversation 3-dot menu button | `[data-testid="conversation-menu-menu-button"]`, scoped inside `chat-conversation-item-{id}` | Pre-existing; `ChatPage.get_conversation_menu_button(id)`. On `main`. |
| Rename menu item | `[data-testid="chat-conversation-menu-rename-menuitem"]` | Pre-existing (ELITEA-2114, `EliteaAI/EliteaUI@20567b81`). |
| Conversation-rename inline input | `chat-conversation-name-input` | Added ELITEA-2099, `EliteaAI/EliteaUI@ff56e29d`. |
| Conversation-rename confirm (checkmark) button | `chat-conversation-name-confirm-button`, carries `data-disabled="true"/"false"` | Same commit `ff56e29d`. |
| **Conversation-rename validation tooltip content** | `[data-testid="chat-conversation-name-confirm-tooltip-content"]` | **`needs-adding` at analysis time — ADDED this session** (mirrors `chat-folder-name-confirm-tooltip-content` from ELITEA-2458 exactly: `slotProps={{ popper: { 'data-testid': '...' } }}` on the existing `Tooltip` wrapping the confirm `Box`). Committed `EliteaAI/EliteaUI@888dac13` on `automation/testids`. Live-verified: mounts on hover of the confirm button while the name is invalid; text matches `ConversationNameWarningMessage` verbatim. Same MUI-portal gotcha as the folder tooltip — only appears in the DOM after an explicit hover, not merely because `title` is non-empty (the `title` attribute alone surfaces in an a11y-snapshot's accessible-name read without a real hover — do not rely on that for evidence; use the testid locator after `hover()`, same idiom as `get_folder_name_confirm_tooltip_text()`). |
| Conversation-rename cancel button | `chat-conversation-name-cancel-button` | Same commit `ff56e29d`. |
| App-wide toast alert (error/success severity) | `[data-testid="toast-alert"][data-severity="{severity}"]` | Pre-existing (`ChatPage.toast_alert`, `TOAST_ALERT_SEVERITY`). Used for ELITEA-2113 step 5. |

## Network Behavior

- Shape A (ELITEA-2110/2112): NO mutating call fires at any point — neither
  from typing the invalid value, nor from the no-op checkmark click. Verify via
  `capture_requests_matching("/conversation/prompt_lib", method="PUT")` staying
  empty, after `chat.wait_for_network()` gives any would-be async call a chance
  to register.
- Shape B (ELITEA-2113): `PUT
  /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}` →
  `200` fires ONLY on the final (valid, enabled) checkmark click — not while the
  input holds the invalid value.

## Known Defects Found During Exploration

None. All three cases' steps are directly grounded in `ConversationItem.jsx`'s
source (`ConversationNameRegExp = /^[a-zA-Z0-9_[\].()][a-zA-Z0-9_[\].() -]{2,63}$/`
— first-char class excludes space/hyphen, later-char class allows both) and
`ConversationNameWarningMessage` (`src/common/constants.js`), each live-verified
this session against the shared DEV project (typed "HI Chat$$%" → tooltip shown
verbatim, checkmark disabled, no-op click; typed " ab" → checkmark stayed
disabled; typed "$$%%" then "Chat 01 (test)." → checkmark flipped to enabled).
No case-text drift.

## Blocked Steps

None. One gap found and closed during this implementation: the conversation-rename
confirm button's validation tooltip had NO testid on its popper content before
this session (same pre-existing gap the `_surface.md` digest already flagged for
the sibling folder-rename tooltip, closed there by ELITEA-2458) — added
`chat-conversation-name-confirm-tooltip-content` this session
(`EliteaAI/EliteaUI@888dac13` on `automation/testids`), mirroring the exact
`slotProps` pattern ELITEA-2458 used for `FolderItem.jsx`. Everything else this
family needs (input/confirm/cancel/toast) was already added and live-verified
during ELITEA-2099's implementation.

## Automation Hints

- **Source-confirmed validation logic** — same `ConversationNameRegExp`/
  `isSaveEnabled` pair documented in the 2105-2109 family's AFS; this family
  additionally exercises the CHARSET and FIRST-CHAR branches of the regex
  (`[a-zA-Z0-9_[\].()][a-zA-Z0-9_[\].() -]{2,63}`): a first char outside
  `[a-zA-Z0-9_[\].()]` (space, or any char not in the later class either, e.g.
  `$`/`%`) fails immediately regardless of length.
- **Implementer note**: write Shape A as ONE parameterized test
  (`@pytest.mark.parametrize`) covering ELITEA-2110/2112, and Shape B as a
  separate non-parameterized test for ELITEA-2113 (its steps genuinely differ —
  an invalid→valid recovery + successful save — not just a data variation of
  Shape A). Same page object/helpers as the merged/trunk 2099-2109 family:
  `ChatPage.get_conversation_menu_button`, `open_conversation_context_menu`,
  `click_conversation_menu_item("rename")`, `set_conversation_name`,
  `clear_conversation_name`, `is_conversation_name_confirm_enabled`,
  `capture_requests_matching`. NEW page-object addition needed:
  `get_conversation_name_confirm_tooltip_text()` (mirrors
  `get_folder_name_confirm_tooltip_text()` exactly — hover the confirm button,
  read `CONVERSATION_NAME_CONFIRM_TOOLTIP_CONTENT`, return `""` on timeout since
  that's the expected outcome for every VALID-name state).
- For the "no PUT fires" assertions, follow the established idiom from
  `test_conversation_rename_cancel_discards_changes.py` / the 2105-2109 family:
  capture BEFORE the click, then `chat.wait_for_network()` before reading the
  captured list.
