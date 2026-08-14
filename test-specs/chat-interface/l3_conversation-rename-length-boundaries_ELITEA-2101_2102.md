# Test Case: Chat – Conversation Rename – Save with 49/50-Character Names (Length Boundaries)

## Metadata
- **TMS IDs**: ELITEA-2101, ELITEA-2102 (family AFS — differ only in data: 49-char
  vs 50-char name; same steps, same flow)
- **Linked Story**: none (both cases `requirements: []`)
- **Priority**: l3 (case priority: medium, both)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Elitea Testing Team", observed live as `projectId=471` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: ready-for-automation (both members)
- **family_afs**: true — one parameterized spec covers both TMS cases

**Related existing coverage (reused as context/transit, not as a covering spec):**
`test-specs/chat-interface/l3_conversation-rename-basic-via-edit-option_ELITEA-2099.md`
(→ `automation/tests/ui/chat/test_conversation_rename_basic_via_edit_option.py`, merged
to `automation/base`) already proves the full rename mechanics (3-dot → Rename menu item
→ inline input pre-filled with current name → checkmark commits via `PUT
.../conversation/prompt_lib/{project_id}/{id}` → sidebar shows new name) for a short,
ordinary name. ELITEA-2101/2102 ask for the SAME mechanics at two specific data points —
exactly 49 and exactly 50 characters (the product's `MAX_CONVERSATION_LENGTH` boundary,
confirmed by source read — see § Automation Hints). Reused as transit knowledge (which
testids/flow to drive) and as the pattern for a NEW parameterized test in the same file/
class — not cited as already covering these two length points (2099's test uses a fixed
short name, never exercises the length boundary).

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
  ELITEA-2099/2100 pattern). Suggested original name: `at_rename_len_orig`.

### Parameter table (one row per TMS case)

| TMS ID | Param — name length | Param — literal value | Expected |
|---|---|---|---|
| ELITEA-2101 | 49 chars | `"A" * 49` | accepted, saved, no error |
| ELITEA-2102 | 50 chars | `"A" * 50` | accepted, saved, no error (exact `MAX_CONVERSATION_LENGTH` boundary — not truncated) |

## Test Steps (shared shape, executed once per parameter row)

**Setup (not a numbered case step)**
0. Create `conv_target` via `conversation_api.create_conversation("at_rename_len_orig")`.
   Navigate to `${BASE_URL}/chat`.

1. Hover `conv_target`'s sidebar item, click the three-dot icon
   (`get_conversation_menu_button(conv_target_id)`), click the **Rename** menu item
   (`chat-conversation-menu-rename-menuitem`).
   - **Verify**: the conversation name becomes an editable inline input
     (`chat-conversation-name-input`).
2. Clear the input and type exactly N characters (N = 49 or 50 per the row).
   - **Verify**: `chat-conversation-name-input`'s value has length == N (all N
     characters accepted, none truncated — live-confirmed for both 49 and 50: the
     product's `onChangeConversationName` handler slices at `MAX_CONVERSATION_LENGTH =
     50`, so 50 is the exact boundary where truncation would first apply to a 51st
     character, not to the 50th itself). `chat-conversation-name-confirm-button`'s
     `data-disabled` attribute is `"false"` (name changed AND passes
     `ConversationNameRegExp`, which allows 3–64 chars — both 49 and 50 satisfy it).
3. Click the checkmark (save) icon — an explicit click on
   `chat-conversation-name-confirm-button`.
   - **Verify**: the input closes (`chat-conversation-name-input` no longer present);
     `[data-testid="chat-conversation-item-{conv_target_id}"]` shows the new N-character
     name in the sidebar. Underlying network call: `PUT
     /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}`
     resolves `200` (live-confirmed for both N=49 and N=50).
4. Verify no error message is shown.
   - **Verify**: no `[data-testid="toast-alert"][data-severity="error"]` appears; no
     NEW console errors beyond the pre-existing, unrelated `secrets/secrets/default`
     403 noise present on every page load in this environment (same exclusion as
     ELITEA-2099's AFS).

## Expected Results
- Both a 49-character and an exactly-50-character conversation name are accepted
  without truncation, save successfully via the checkmark (an explicit `PUT` that
  resolves 200), and the sidebar reflects the new full-length name.
- No error surfaces at either length — 50 is the boundary the product enforces
  (`MAX_CONVERSATION_LENGTH`), and the boundary value itself is valid, not rejected.

## Coverage Map

### Axis 1 — Case coverage (per TMS case; identical shape, own row per case)

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: ≥1 conversation exists | — | Setup | `conversation_api.create_conversation` | asserted |
| 1 Navigate to Chats, hover, click 3-dot, click Edit → editable | conversation name is editable | step 1 | `chat-conversation-name-input` visible | asserted |
| 2 Clear name, type exactly 49/50 chars → all chars accepted | full string accepted | step 2 | input value length == N | asserted |
| 3 Click checkmark → conversation renamed | rename committed | step 3 | input gone + sidebar item text (length N) + `PUT …/conversation/…` 200 | asserted |
| 4 Verify no error message is shown | save completes successfully | step 4 | toast-alert(error) absence + console check | asserted |
| Expected Final State: "renamed with N-char name without errors" | — | steps 3, 4 | covered by the rows above | asserted |
| Pass/Fail: "All steps complete without errors" / "N-char name accepted and saved" | — | steps 2–4 | covered by the rows above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- step 2 additionally asserts `chat-conversation-name-confirm-button`'s
  `data-disabled` flips to `"false"` for both lengths — *added: proves the save
  affordance is genuinely enabled at both data points, not just that the string sits
  in the input; mirrors ELITEA-2099's same assertion.*
- step 3 asserts the underlying `PUT .../conversation/prompt_lib/{project_id}/{id}`
  network call resolves `200` for both lengths — *added: proves the rename is real
  (backend-persisted) at the boundary, not a client-side-only list splice.*
- step 4 explicitly asserts no NEW console errors, excluding the pre-existing
  unrelated `secrets/secrets/default` 403 noise — *added: standard side-channel
  discipline, same exclusion already documented for ELITEA-2099/2114.*
- Both cases additionally assert the input's length is exactly N post-type (not just
  "accepted") — *added: the case's own Test Data table is explicit about exact
  character counts (49, "exactly 50"), and 50 is the product's documented truncation
  point (`MAX_CONVERSATION_LENGTH`), so confirming NO truncation occurred at 50 is the
  actual boundary assertion the case's title promises ("Boundary").*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)` in a
   `try`/`finally`, per `.claude/rules/ui-tests.md` § Test Data Lifecycle (once per
   parameter row / conv_target).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback
ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). All
handles below are pre-existing (added during ELITEA-2099's implementation,
`EliteaAI/EliteaUI@ff56e29d` on `automation/testids`) — **no new testids needed for
this family**.

| Element | Testid handle | Notes / provenance |
|---|---|---|
| Conversation list item (dynamic) | `[data-testid="chat-conversation-item-{id}"]` | Pre-existing class constant (`CONVERSATION_ITEM`). On `main` (pre-existing, long-standing). |
| Conversation 3-dot menu button | `[data-testid="conversation-menu-menu-button"]`, scoped inside `chat-conversation-item-{id}` | Pre-existing (`CONVERSATION_MENU_BUTTON`); use `ChatPage.get_conversation_menu_button(id)`. On `main`. |
| Rename menu item | `[data-testid="chat-conversation-menu-rename-menuitem"]` | Pre-existing (ELITEA-2114, `EliteaAI/EliteaUI@20567b81`). On `automation/testids` (added post-`main`-fork of this feature; verify at implementation time per closure-record discipline). |
| Conversation-rename inline input | `chat-conversation-name-input` | Added ELITEA-2099, `EliteaAI/EliteaUI@ff56e29d`, on `automation/testids`. Live-verified again this session: accepts 49 and 50 chars with no truncation. |
| Conversation-rename confirm (checkmark) button | `chat-conversation-name-confirm-button`, carries `data-disabled="true"/"false"` | Same commit `ff56e29d`. Live-verified `data-disabled="false"` at both N=49 and N=50. **A11y-snapshot pruning gotcha applies in the disabled/unchanged state** (documented in ELITEA-2099's AFS / the `_surface.md` digest) — assert via the testid locator directly, never via a `browser_snapshot` accessible-name read; not hit in this exploration since the button was enabled throughout, but the implementer should still avoid a snapshot-based assertion on this element as a matter of policy. |
| App-wide toast alert (error/success severity) | `[data-testid="toast-alert"][data-severity="{severity}"]` | Pre-existing (`ChatPage.toast_alert`, `TOAST_ALERT_SEVERITY`). |

## Network Behavior

- Rename commit (step 3, both rows): `PUT
  /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}` → `200`,
  live-confirmed at both N=49 and N=50 (request body includes the new `name`).
- No other mutating calls expected on this flow beyond setup's `create_conversation`.

## Known Defects Found During Exploration

None. Both cases pass end-to-end against the live product exactly as their own case
text expects — no case-text drift, no defect. (Unlike ELITEA-2099/2114, whose context-
menu item-label/count drift does NOT recur here since these two cases' steps don't
describe the menu's content, only the Rename flow itself.)

## Blocked Steps

None — both cases' 4 steps executed live end-to-end this session, using the shared
pre-existing "Review attached documents" conversation (id 420) during live exploration
ONLY: renamed to the 49-char name, verified, renamed to the 50-char name, verified,
then restored to its original name ("Review attached documents") immediately after —
to avoid leaving pollution in the shared DEV project. The automated test itself
creates and deletes its own `conv_target` per § Test Data / § Cleanup, so this
substitution is exploration-only and does not appear in the spec.

## Automation Hints

- **Source-confirmed validation logic** (`EliteaUI/src/[fsd]/features/chat/
  conversation-list/ui/conversations/ConversationItem.jsx` +
  `EliteaUI/src/common/constants.js`), grounds every assertion in this AFS:
  - `MAX_CONVERSATION_LENGTH = 50` (`constants.js:74`).
  - `onChangeConversationName`: `const newName = event.target.value.slice(0,
    MAX_CONVERSATION_LENGTH)` — truncates at 50 on EVERY keystroke/paste. A 49-char or
    50-char string is never touched by this slice (only a 51st+ character would be
    dropped) — this is why both rows in this family are "accepted, not rejected", and
    why 50 is genuinely the boundary the case's title calls out (2103/2104, not part
    of this family, are the ones that actually hit truncation/overflow at 51+).
  - `ConversationNameRegExp = /^[a-zA-Z0-9_[\].()][a-zA-Z0-9_[\].() -]{2,63}$/` (3–64
    chars total) — both 49-char and 50-char all-`A` strings satisfy this easily; the
    binding constraint at these two data points is `MAX_CONVERSATION_LENGTH`, not the
    regex.
  - `isSaveEnabled = isConversationNameValid && (isNew || conversationName !== name)`
    — same "valid AND changed" gate documented for ELITEA-2099/ELITEA-2458 (folder
    rename).
- **Implementer note**: write this as ONE parameterized test
  (`@pytest.mark.parametrize` or equivalent) in the same file/class as ELITEA-2099's
  `test_conversation_rename_basic_via_edit_option` — same page object, same helpers
  (`ChatPage.get_conversation_menu_button`, `click_conversation_menu_item("rename")`),
  differing only in the literal name string and its expected length. Do not write two
  near-identical non-parameterized test functions.
- `.playwright-mcp/console-2026-08-14T20-53-01-168Z.log` (and successors in the same
  session) capture the full console stream for both save operations — the only new
  errors across both are the pre-existing `secrets/secrets/default` 403 noise,
  confirmed via `browser_console_messages`/`browser_network_requests` at each step.
