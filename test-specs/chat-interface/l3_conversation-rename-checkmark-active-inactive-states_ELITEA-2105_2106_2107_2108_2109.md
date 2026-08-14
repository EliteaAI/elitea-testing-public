# Test Case: Chat – Conversation Rename – Checkmark Active/Inactive States

## Metadata
- **TMS IDs**: ELITEA-2105, ELITEA-2106, ELITEA-2107, ELITEA-2108, ELITEA-2109
  (family AFS — all five drive the SAME `isSaveEnabled` gate on the SAME inline
  rename editor, differing only in the data/state fed into the input: no change,
  empty, 1 char, 2 chars, 2→3-char transition)
- **Linked Story**: none (all five `requirements: []`)
- **Priority**: l3 (case priority: medium, all five)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Elitea Testing Team", observed live as `projectId=471` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent, combined analyst+implementer slot)
- **Status**: ready-for-automation (all five members)
- **family_afs**: true — one parameterized spec (plus one standalone transition
  test for ELITEA-2109) covers all five TMS cases

**Related existing coverage (reused as context/transit, not as a covering spec):**
`test-specs/chat-interface/l3_conversation-rename-basic-via-edit-option_ELITEA-2099.md`
(→ `automation/tests/ui/chat/test_conversation_rename_basic_via_edit_option.py`, merged
to `automation/base`) already proves the full rename mechanics (3-dot → Rename menu item
→ inline input pre-filled with current name → checkmark commits via `PUT
.../conversation/prompt_lib/{project_id}/{id}` → sidebar shows new name) AND already
asserts the checkmark's `data-disabled="true"` in the unchanged state as an Axis-2
addition — but only as ONE incidental snapshot on ONE case (a valid, unchanged name);
it never exercises the empty/1-char/2-char INVALID states, never asserts a no-op click
has zero effect, and never exercises the 2→3-char activation transition. ELITEA-2099's
own § Automation Hints explicitly forecasts this cluster: *"directly relevant to the
sibling conversation-rename boundary cases already in the TMS folder (ELITEA-2100–2113:
… empty/short/special-char checkmark-inactive states, tooltip content)"*. That AFS's own
near-rewrite call ("most of this case's 9 steps, not a small number of missing
assertions" → `ready-for-automation`, not `extend-existing`) applies with even more force
here — five whole new cases with their own click-has-no-effect / regex-boundary
assertions the existing spec doesn't cover — so this family is `ready-for-automation`,
not an extension of ELITEA-2099's spec.
`test-specs/chat-interface/l3_conversation-rename-length-boundaries_ELITEA-2101_2102.md`
(→ `automation/tests/ui/chat/test_conversation_rename_length_boundaries.py`, merged)
proves the SAVE path at the *upper* length boundary (49/50 chars, all valid/changed);
this family proves the *lower* length boundary (0/1/2/3 chars) where the checkmark
stays disabled below 3 and activates exactly at 3 — the opposite edge of the same
`ConversationNameRegExp`, not previously exercised by any merged test.

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
  `conversation_api.create_conversation(name)` (fast, no LLM round-trip — matches the
  ELITEA-2099/2100/2101/2102 pattern). Suggested original name:
  `at_rename_checkmark_orig` (25 chars — a stable, VALID, already-persisted name
  that itself passes `ConversationNameRegExp`, so "no change" (ELITEA-2105) tests
  the "valid-but-unchanged" branch specifically, not "invalid AND unchanged").

### Parameter table (one row per TMS case)

| TMS ID | Scenario | Input action | Expected input value | Expected `data-disabled` | Click behavior |
|---|---|---|---|---|---|
| ELITEA-2105 | No changes made | Open editor, type nothing | unchanged (`at_rename_checkmark_orig`) | `"true"` | no-op: editor stays open, no PUT, name unchanged in sidebar |
| ELITEA-2106 | Field cleared to empty | Clear the input entirely | `""` (empty) | `"true"` | no-op |
| ELITEA-2107 | 1-character input | Clear + type `"A"` | `"A"` | `"true"` | no-op |
| ELITEA-2108 | 2-character input | Clear + type `"AB"` | `"AB"` | `"true"` | no-op |
| ELITEA-2109 | 2→3-character transition | Clear + type `"AB"` (verify inactive), then append `"C"` (verify active) | `"AB"` then `"ABC"` | `"true"` then `"false"` | click on `"ABC"` SAVES successfully |

## Test Steps

### Shared shape A — ELITEA-2105/2106/2107/2108 (checkmark stays inactive, click is a no-op)

**Setup (not a numbered case step)**
0. Create `conv_target` via `conversation_api.create_conversation("at_rename_checkmark_orig")`.
   Navigate to `${BASE_URL}/chat`.

1. Hover `conv_target`'s sidebar item, click the three-dot icon
   (`get_conversation_menu_button(conv_target_id)`), click the **Rename** menu item
   (`chat-conversation-menu-rename-menuitem`).
   - **Verify**: the conversation name becomes an editable inline input
     (`chat-conversation-name-input`), pre-filled with the current name.
2. Apply the row's input action (no typing / clear / type "A" / type "AB").
   - **Verify**: `chat-conversation-name-input`'s value matches the row's "Expected
     input value" exactly.
3. Verify the checkmark icon is in a disabled/inactive state.
   - **Verify**: `chat-conversation-name-confirm-button`'s `data-disabled` attribute
     is `"true"` (`is_conversation_name_confirm_enabled()` returns `False`).
4. Attempt to click the checkmark icon.
   - **Verify**: click has no effect — `ConversationItem.jsx` wires
     `onClick={isSaveEnabled ? handler : null}`, so a disabled click is a genuine
     browser no-op, not a suppressed handler: (a) no `PUT
     /conversation/prompt_lib/{project_id}/{conv_target_id}` request fires (captured
     via `capture_requests_matching`, confirmed empty after `chat.wait_for_network()`
     settles); (b) the inline input remains OPEN (`chat-conversation-name-input`
     still visible, same value as before the click); (c) the conversation's
     PERSISTED name (read via `conversation_api.get_conversation(id)["name"]`, the
     real backend record — not a substitution) is still the ORIGINAL name
     `at_rename_checkmark_orig`, never the edited-but-unsaved value. **Implementer
     amendment (this session):** `chat-conversation-item-{id}` is NOT a valid handle
     for this check — source-confirmed `ConversationItem.jsx` renders the
     `data-testid="chat-conversation-item-{id}"` node ONLY in the `!isEditing`
     branch; while the inline editor is open (which it stays, per this step's own
     "input remains open" expectation) that testid does not exist in the DOM at
     all, so asserting against it times out with "element(s) not found" rather than
     a text mismatch. The API-level persisted-name read is the honest equivalent
     observable available while the editor stays open, and is what the case's
     "conversation name remains unchanged" (2105) / "name unchanged" (2106) really
     needs proven — not a substitution, since it reads the real system's stored
     record, live-verified to correctly reject the fix on first run (4/4 Shape-A
     rows failed with the old `chat-conversation-item-{id}` assertion, confirming
     it as a real handle-availability bug in the AFS, not the product).

### Shared shape B — ELITEA-2109 (2→3-char activation + successful save)

**Setup (not a numbered case step)**
0. Create `conv_target` via `conversation_api.create_conversation("at_rename_checkmark_orig")`.
   Navigate to `${BASE_URL}/chat`.

1. Hover `conv_target`'s sidebar item, click the three-dot icon, click the **Rename**
   menu item.
   - **Verify**: inline input editable, pre-filled with the current name.
2. Clear the current name and type exactly 2 characters (`"AB"`).
   - **Verify**: `chat-conversation-name-input` value == `"AB"`; checkmark icon is
     inactive/greyed out (`data-disabled="true"`).
3. Type one more character to reach 3 characters (append `"C"` → `"ABC"`).
   - **Verify**: `chat-conversation-name-input` value == `"ABC"`; checkmark icon
     becomes active/enabled (`data-disabled="false"`).
4. Click the checkmark icon.
   - **Verify**: the input closes (`chat-conversation-name-input` no longer
     present); `chat-conversation-item-{conv_target_id}` shows `"ABC"` in the
     sidebar. Underlying network call: `PUT
     /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}`
     resolves `200`.

## Expected Results
- The checkmark (save) icon stays disabled (`data-disabled="true"`) for an
  unchanged name, an empty field, a 1-character input, and a 2-character input —
  four independent ways `isSaveEnabled` evaluates `false` (unchanged for
  ELITEA-2105; `ConversationNameRegExp` failing the 3-char minimum for
  ELITEA-2106/2107/2108).
- In every disabled state, clicking the checkmark is a genuine no-op: no network
  mutation, no editor close, no name change.
- The checkmark activates (`data-disabled="false"`) exactly when the input reaches
  3 characters (the regex's minimum), and a click at that point saves successfully.

## Coverage Map

### Axis 1 — Case coverage (per TMS case; four share one shape, ELITEA-2109 is the transition)

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: ≥1 conversation exists | — | Setup | `conversation_api.create_conversation` | asserted |
| ELITEA-2105 step 1 Navigate/hover/3-dot/Edit → editable, pre-filled | name editable, current name shown | Shape A step 1 | `chat-conversation-name-input` visible + value | asserted |
| ELITEA-2105 step 2 No changes made | name unchanged in field | Shape A step 2 | input value == original | asserted |
| ELITEA-2105 step 3 Checkmark disabled | inactive | Shape A step 3 | `data-disabled == "true"` | asserted |
| ELITEA-2105 step 4 Click checkmark → no effect | input stays open, not saved | Shape A step 4 | no PUT + input still open + persisted name unchanged (API) | asserted |
| ELITEA-2105 step 5 Name remains unchanged in left panel | name unchanged | Shape A step 4 | `conversation_api.get_conversation(id)["name"]` == original | asserted |
| ELITEA-2106 step 1 Navigate/hover/3-dot/Edit → editable | editable | Shape A step 1 | same as above | asserted |
| ELITEA-2106 step 2 Clear field → empty | field empty | Shape A step 2 | input value == "" | asserted |
| ELITEA-2106 step 3 Checkmark disabled | inactive | Shape A step 3 | `data-disabled == "true"` | asserted |
| ELITEA-2106 step 4 Click checkmark → no effect | save not triggered | Shape A step 4 | no PUT fired | asserted |
| ELITEA-2106 step 5 Field stays open, name unchanged | field open, unchanged | Shape A step 4 | input still visible + persisted name unchanged (API) | asserted |
| ELITEA-2107 step 1 Navigate/hover/3-dot/Edit → editable | editable | Shape A step 1 | same as above | asserted |
| ELITEA-2107 step 2 Type "A" | 1 char in field | Shape A step 2 | input value == "A" | asserted |
| ELITEA-2107 step 3 Checkmark disabled | inactive | Shape A step 3 | `data-disabled == "true"` | asserted |
| ELITEA-2107 step 4 Click checkmark → no effect | save not triggered | Shape A step 4 | no PUT fired + persisted name unchanged (API) | asserted |
| ELITEA-2108 step 1 Navigate/hover/3-dot/Edit → editable | editable | Shape A step 1 | same as above | asserted |
| ELITEA-2108 step 2 Type "AB" | 2 chars in field | Shape A step 2 | input value == "AB" | asserted |
| ELITEA-2108 step 3 Checkmark disabled | inactive | Shape A step 3 | `data-disabled == "true"` | asserted |
| ELITEA-2108 step 4 Click checkmark → no effect | save not triggered | Shape A step 4 | no PUT fired + persisted name unchanged (API) | asserted |
| ELITEA-2109 step 1 Navigate/hover/3-dot/Edit → editable | editable | Shape B step 1 | same as above | asserted |
| ELITEA-2109 step 2 Type "AB" → checkmark inactive | inactive | Shape B step 2 | input == "AB" + `data-disabled == "true"` | asserted |
| ELITEA-2109 step 3 Type "C" → checkmark becomes active | active | Shape B step 3 | input == "ABC" + `data-disabled == "false"` | asserted |
| ELITEA-2109 step 4 Click checkmark → renamed, applied in left panel | rename committed | Shape B step 4 | input gone + sidebar text "ABC" + `PUT` 200 | asserted |
| Each case's Expected Final State | — | shape steps | covered by rows above | asserted |
| Each case's Pass/Fail criteria | — | shape steps | covered by rows above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Shape A step 4 additionally asserts NO `PUT .../conversation/prompt_lib/...`
  request fires on a disabled-checkmark click, for all four inactive rows — *added:
  each case's own Pass/Fail table only says "click has no effect" / "save is not
  triggered" in prose; asserting the absence of the underlying network mutation is
  the strongest, most honest proof of "no effect" (source-confirmed:
  `onClick={isSaveEnabled ? handler : null}` — a disabled click has literally zero
  JS handler attached, so an honest test proves the network-silence, not just a
  DOM read).*
- Shape A step 4 additionally asserts the sidebar item still shows the conversation's
  ORIGINAL persisted name (never the typed-but-unsaved value) — *added: distinguishes
  "input field shows the typed value" (expected, benign) from "the conversation was
  actually renamed" (the case's real failure mode to guard against), mirroring the
  same distinction ELITEA-2100's cancel-flow AFS already draws.*
- ELITEA-2105's "no changes made" row specifically starts from a name that is itself
  VALID per `ConversationNameRegExp` (25 chars, all allowed characters) — *added:
  isolates the "valid but unchanged" branch of `isSaveEnabled` from the "invalid"
  branch that ELITEA-2106/2107/2108 exercise; without this the family risks
  conflating two different reasons the checkmark stays disabled.*
- ELITEA-2109 step 3 uses a real incremental keystroke (append `"C"` to the existing
  `"AB"` value via `press_sequentially`) rather than clearing and retyping `"ABC"`
  from scratch — *added: the case's own step 3 says "type ONE MORE character to
  reach 3 characters", which is a genuine incremental-typing action, not a
  full-field replace; this is the only step in the family where that distinction
  matters (a clear+retype would still assert the correct end-state but wouldn't
  honestly reproduce the case's own described action).*
- All rows assert the underlying `ConversationNameRegExp`/`isSaveEnabled` source
  logic is what's being exercised (documented in § Automation Hints) — *added:
  grounds every expected `data-disabled` value in the actual gate, not a guess.*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)` in a
   `try`/`finally`, per `.claude/rules/ui-tests.md` § Test Data Lifecycle (once per
   parameter row / conv_target — six conv_targets total: four Shape-A rows + one
   Shape-B conv_target... actually five total, one per TMS case, since ELITEA-2109
   is its own conv_target).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback
ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). All
handles below are pre-existing (added during ELITEA-2099's implementation,
`EliteaAI/EliteaUI@ff56e29d` on `automation/testids`, confirmed present via a fresh
source read of `ConversationItem.jsx` this session) — **no new testids needed for
this family**.

| Element | Testid handle | Notes / provenance |
|---|---|---|
| Conversation list item (dynamic) | `[data-testid="chat-conversation-item-{id}"]` | Pre-existing class constant (`CONVERSATION_ITEM`). On `main` (pre-existing, long-standing). |
| Conversation 3-dot menu button | `[data-testid="conversation-menu-menu-button"]`, scoped inside `chat-conversation-item-{id}` | Pre-existing (`CONVERSATION_MENU_BUTTON`); use `ChatPage.get_conversation_menu_button(id)`. On `main`. |
| Rename menu item | `[data-testid="chat-conversation-menu-rename-menuitem"]` | Pre-existing (ELITEA-2114, `EliteaAI/EliteaUI@20567b81`). |
| Conversation-rename inline input | `chat-conversation-name-input` | Added ELITEA-2099, `EliteaAI/EliteaUI@ff56e29d`. |
| Conversation-rename confirm (checkmark) button | `chat-conversation-name-confirm-button`, carries `data-disabled="true"/"false"` | Same commit `ff56e29d`. `onClick={isSaveEnabled ? (isNew ? onCreate : onSave) : null}` — source-confirmed this session (`EliteaUI/src/[fsd]/features/chat/conversation-list/ui/conversations/ConversationItem.jsx`): a disabled click has NO handler attached at all, so "no effect" is provably a network-silent no-op, not a suppressed action. **A11y-snapshot pruning gotcha applies in the disabled/unchanged state** (documented in ELITEA-2099's AFS / the `_surface.md` digest) — assert via the testid locator directly, never via a `browser_snapshot` accessible-name read. |
| App-wide toast alert (error/success severity) | `[data-testid="toast-alert"][data-severity="{severity}"]` | Pre-existing (`ChatPage.toast_alert`, `TOAST_ALERT_SEVERITY`). Not exercised by this family's own case steps (none of the five cases describe an error-toast expectation) — available if the implementer wants an extra negative check, not required. |

## Network Behavior

- Shape A (ELITEA-2105/2106/2107/2108): NO mutating call fires at any point —
  neither from typing/clearing alone, nor from the no-op checkmark click. Verify via
  `capture_requests_matching("/conversation/prompt_lib", method="PUT")` staying
  empty, after `chat.wait_for_network()` gives any would-be async call a chance to
  register.
- Shape B (ELITEA-2109): `PUT
  /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}` → `200`
  fires ONLY on the final (3-char, enabled) checkmark click — not on either of the
  two typing steps before it.

## Known Defects Found During Exploration

None. All five cases' steps are directly grounded in `ConversationItem.jsx`'s
source (`isSaveEnabled = isConversationNameValid && (isNew || conversationName !==
name)`, `ConversationNameRegExp = /^[a-zA-Z0-9_[\].()][a-zA-Z0-9_[\].() -]{2,63}$/`
— 3–64 chars total) and match the live product exactly as each case's own text
expects. No case-text drift (unlike ELITEA-2099/2100/2114's Rename-vs-Edit menu
label drift — none of these five cases' steps describe the context-menu's content,
only the rename-editor's checkmark behavior, so that drift does not recur here).

## Blocked Steps

None — every element and interaction this family needs was already added and
live-verified during ELITEA-2099's implementation (source re-read this session,
not re-driven live against the shared DEV project, to avoid repeating pollution
risk already documented for that session; the validation-logic conclusions above
are grounded in a direct source read of the current `ConversationItem.jsx`, which
is a stronger form of confirmation than a repeated manual click-through would add).
The automated tests themselves create and delete their own `conv_target`(s) per
§ Test Data / § Cleanup and exercise every assertion live via the real browser
against the real product — nothing in the shipped spec is source-only.

## Automation Hints

- **Source-confirmed validation logic** (`EliteaUI/src/[fsd]/features/chat/
  conversation-list/ui/conversations/ConversationItem.jsx` +
  `EliteaUI/src/common/constants.js`), grounds every assertion in this AFS:
  - `ConversationNameRegExp = /^[a-zA-Z0-9_[\].()][a-zA-Z0-9_[\].() -]{2,63}$/`
    (`constants.js:94`) — first char from one class, THEN 2–63 more chars from a
    slightly wider class → 3–64 characters total. This is why 1 and 2 characters
    both fail (below the 3-char floor) and exactly 3 characters is the activation
    point (ELITEA-2109's title, "Becomes Active at 3 Characters", is a precise,
    literal description of this regex's `{2,63}` quantifier, not an approximation).
  - `isConversationNameValid = ConversationNameRegExp.test(conversationName ?? '')`
    — an empty string also fails (regex requires at least the first mandatory
    character), covering ELITEA-2106.
  - `isSaveEnabled = isConversationNameValid && (isNew || conversationName !==
    name)` — for an EXISTING conversation (`isNew` false, always true in this
    family's setup), this collapses to `isValid && changed`. ELITEA-2105's "no
    changes" row fails ONLY the `changed` half (the name IS valid); ELITEA-
    2106/2107/2108 fail the `isValid` half (regardless of whether they also
    happen to differ from the original — they do, but that's not why they're
    disabled).
  - The confirm `Box`'s `onClick={isSaveEnabled ? (isNew ? onCreate : onSave) :
    null}` — when disabled, the `onClick` prop is literally `null`. A Playwright
    `.click()` on an element with no click handler is a legitimate, standard DOM
    no-op (not intercepted, not force-needed) — no `force=True` required.
- **Implementer note**: write Shape A as ONE parameterized test
  (`@pytest.mark.parametrize`) covering ELITEA-2105/2106/2107/2108, and Shape B as
  a separate non-parameterized test for ELITEA-2109 (its steps genuinely differ —
  a two-stage incremental type + a successful save — not just a data variation of
  Shape A). Same page object/helpers as the merged ELITEA-2099/2100/2101/2102/2103/2104
  tests: `ChatPage.get_conversation_menu_button`, `open_conversation_context_menu`,
  `click_conversation_menu_item("rename")`, `set_conversation_name`,
  `clear_conversation_name`, `is_conversation_name_confirm_enabled`,
  `capture_requests_matching`. For the "no PUT fires" assertions, follow the
  established idiom from `test_conversation_rename_cancel_discards_changes.py`
  (ELITEA-2100): capture BEFORE the click, then give any async effect a chance to
  register via `chat.wait_for_network()` (framework-native `networkidle` wait, per
  `.claude/rules/ui-tests.md` — never a raw `page.wait_for_timeout()`) before
  reading the captured list.
- Do not write four near-identical non-parametrized test functions for Shape A —
  the four rows differ only in the typed value and the resulting input-value
  assertion; a single parametrized test with a `pytest.param(..., id=...)` per TMS
  case is the established pattern in this exact file cluster
  (`test_conversation_rename_length_boundaries.py`).
