# Test Case: Chat – Conversation Rename – Cancel Discards Changes

## Metadata
- **TMS ID**: ELITEA-2100
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Elitea Testing Team", observed live as `projectId=471` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: ready-for-automation

**Related existing coverage (reused as context — testid handles, page-object helpers,
and the conversation-rename validation logic — not as a covering spec):**
`automation/tests/ui/chat/test_conversation_rename_basic_via_edit_option.py` (ELITEA-2099,
merged onto this batch's trunk `tests/batch-chat-remaining-w02`) proves the *save* half
of the same inline rename editor — pre-fill, checkmark/cancel affordances, explicit
checkmark click, PUT 200, persistence after nav-away/back. This case exercises the
opposite branch of the SAME editor (the **cancel/discard** path — clicking the X icon
instead of the checkmark) and asserts a *different* observable: that clicking the X
input closes WITHOUT any network mutation and the original name survives, including
across a navigate-away-and-back. Distinct steps (discard vs save), so this is a
separate AFS/spec per SKILL.md's "differ in STEPS → separate AFS" rule, not an
extension of ELITEA-2099's test.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- At least one conversation exists in the Chats section — satisfied live by the
  shared pre-existing "Review attached documents" conversation (id 420); the
  automated test creates its own conversation instead (see § Test Data), matching
  the sibling ELITEA-2099 test's convention of not depending on ambient shared data.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Active project — whatever `${TEST_USER}`'s default/last-selected project is
  (observed live as "Elitea Testing Team", id 471). Don't hardcode the id.

### generate-per-test (created in setup, cleaned up in teardown)
- **`conv_target`** — the conversation whose rename will be cancelled. Create via
  `conversation_api.create_conversation(name)` (fast, no LLM round-trip — same
  pattern as ELITEA-2099). Suggested original name: `at_rename_cancel_orig`. The
  "new" name typed and then discarded, per the case's own Test Data table:
  `Renamed Chat`.

**Live-verified project mismatch gotcha (NOT part of the spec, a setup caveat):**
`ConversationAPI()` instantiated with default `settings.elitea_project_id` resolved
to project `399` during this session's exploration, while the browser's active
project (via `auth_state`/`VITE_DEV_TOKEN`) is `471` ("Elitea Testing Team") — a
conversation created against `399` produced "Conversation not found" when opened at
`/chat/{id}` in the browser. The existing `conversation_api` PYTEST FIXTURE is
session-scoped and (per ELITEA-2099's own precedent, which passes) resolves
correctly when driven through the fixture chain — this note flags that a
**standalone** `ConversationAPI(browser_cookies=[])` script (as used for this
session's manual exploration only) is not equivalent to the fixture and must not be
copied into test setup. The implementer should use the `conversation_api` fixture
exactly as ELITEA-2099's test does — no new risk to that test, purely an
exploration-session caveat, recorded here and in the `_surface.md` digest.

## Test Steps

**Setup (not a numbered case step)**
0. Create `conv_target` via `conversation_api.create_conversation("at_rename_cancel_orig")`.
   Navigate to `${BASE_URL}/chat`.

1. Navigate to the Chats section.
   - **Verify**: `chat.conversations_panel_heading` (`chat-conversations-heading`)
     visible; `[data-testid="chat-conversation-item-{conv_target_id}"]` visible in
     the sidebar list.
2. Hover `conv_target`'s sidebar item, click the three-dot icon, click **Rename**
   (the case's own "Edit" — same case-text drift already accepted for ELITEA-2099/
   #1513/#695: the live menu item is labelled "Rename", not "Edit").
   - **Verify**: the conversation name becomes an editable inline input
     (`chat-conversation-name-input`) pre-filled with the CURRENT name
     (`at_rename_cancel_orig`); checkmark (`chat-conversation-name-confirm-button`,
     `data-disabled="true"` while unchanged) and X/cancel
     (`chat-conversation-name-cancel-button`) icons both visible.
3. Clear the current name and type `Renamed Chat` (per the case's own Test Data).
   - **Verify**: `chat-conversation-name-input`'s value equals `Renamed Chat`;
     `chat-conversation-name-confirm-button`'s `data-disabled` flips to `"false"`
     (live-confirmed: name changed AND passes `ConversationNameRegExp`). No PUT
     network request fires from typing alone (live-confirmed via
     `browser_network_requests` — only pre-existing GET/`select_conversation` POST
     traffic present, no `.../conversation/prompt_lib/...` PUT).
4. Click the X (cancel) icon (`chat-conversation-name-cancel-button`).
   - **Verify**: the inline input closes — `chat-conversation-name-input` no longer
     present (`to_have_count(0)`). Live-confirmed: **no** PUT to
     `.../conversation/prompt_lib/{project_id}/{conv_target_id}` fires at all — the
     only conversation-scoped network traffic present after the click is the
     pre-existing GET (message history) and `select_conversation` POST from earlier
     navigation, not a new mutating call.
5. Verify the conversation still displays its original name.
   - **Verify**: `[data-testid="chat-conversation-item-{conv_target_id}"]` shows
     `at_rename_cancel_orig` (unchanged), not `Renamed Chat`.
6. Verify no changes were applied.
   - **Verify**: no `[data-testid="toast-alert"]` of any severity appears (live:
     `document.querySelectorAll('[data-testid="toast-alert"]').length === 0`); no
     NEW console errors beyond the pre-existing, unrelated
     `secrets/secrets/default` 403 noise present on every page load in this
     environment (same exclusion documented for ELITEA-2099/ELITEA-2114).

## Expected Results
- Clicking the X (cancel) icon during rename closes the inline editor without
  issuing any network mutation and without changing the conversation's stored
  name.
- The original name is preserved both immediately in the sidebar and (per the
  Axis-2 addition below) after navigating away and back.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: ≥1 conversation exists | — | Setup | `conversation_api.create_conversation` | asserted |
| 1 Navigate to Chats section, list displayed | conversations list shown | step 1 | `chat-conversations-heading` + item visible | asserted |
| 2 Hover conversation, click three-dot icon, click Edit; name editable with checkmark and X icons | editable input, checkmark + X visible | step 2 | `chat-conversation-name-input`, `-confirm-button`, `-cancel-button` visible | asserted *(the case's own "Edit" item is labelled "Rename" live — same #1513/#695 clarification already accepted for the sibling ELITEA-2099; reverse-masking guard, live product is correct)* |
| 3 Clear current name, type 'Renamed Chat'; new name appears in field | new name in field | step 3 | input value check | asserted |
| 4 Click the X (cancel) icon; input field closes without saving | editor closes, no save | step 4 | input `to_have_count(0)` + network-request absence check (no PUT) | asserted |
| 5 Verify conversation still displays original name | original name preserved | step 5 | sidebar item text == original name | asserted |
| 6 Verify no changes were applied | no changes applied | step 6 | toast-alert absence + no NEW console errors | asserted |
| Expected Final State (prose): "original name preserved after cancelling" | — | steps 4, 5 | covered by the rows above | asserted |
| Pass/Fail: "All steps complete without errors" | — | step 6 | toast/console check | asserted |
| Pass/Fail: "Original name preserved after cancel" | — | step 5 | covered by the row above | asserted |
| Pass/Fail (fail condition): "Name is changed despite cancelling" | — | steps 4, 5 | inverse of the pass assertions — no PUT + unchanged sidebar text together rule this out | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 4 additionally asserts **no PUT network request fires at all** (not just
  "no visible change") — *added: proves the cancel is a true client-side no-op, not
  a save-then-silently-revert round-trip; matches the network-check discipline
  already used by ELITEA-2099's save-path test (which asserts the PUT DOES fire and
  resolves 200) — this is the direct, symmetric negative check.*
- An extra persistence check — navigate away (`/chat` root) and back into
  `conv_target` — is recommended so the implementer asserts the ORIGINAL name
  survives a full round-trip through the UI, not just the immediate post-cancel DOM
  state — *added: mirrors ELITEA-2099 step 9's persistence-after-navigation check;
  live-confirmed this session (navigated away to `/chat`, `conv_target`'s sidebar
  item — proxied here via the shared "Review attached documents" conversation during
  exploration only — still read its original name on return, no drift).* Not one of
  the case's own 6 numbered steps, so it's an addition, not a requirement — but
  cheap and directly strengthens the "original name preserved" claim beyond a
  same-render-cycle check.
- Step 6 explicitly asserts no NEW console errors, excluding the pre-existing
  unrelated `secrets/secrets/default` 403 noise — *added: standard side-channel
  discipline, same exclusion already documented for ELITEA-2099/ELITEA-2114.*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)` in a
   `try`/`finally`, per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback
ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). All
handles below are **pre-existing** — added by ELITEA-2099's implementation
(`EliteaAI/EliteaUI@ff56e29d` on `automation/testids`) and already wired in
`automation/pages/chat_page.py`; nothing new needed for this case.

| Element | Testid handle | Notes / provenance |
|---|---|---|
| Conversations panel heading | `chat-conversations-heading` | Pre-existing (`ChatPage.conversations_panel_heading`). |
| Conversation list item (dynamic) | `[data-testid="chat-conversation-item-{id}"]` | Pre-existing class constant (`CONVERSATION_ITEM`). |
| Conversation 3-dot menu button | `[data-testid="conversation-menu-menu-button"]`, scoped inside `chat-conversation-item-{id}` | Pre-existing (`CONVERSATION_MENU_BUTTON`); use `ChatPage.get_conversation_menu_button(id)` / `hover_conversation_item(id)` / `open_conversation_context_menu(id)`. |
| Context menu Rename item | `chat-conversation-menu-rename-menuitem` | Pre-existing (`CONVERSATION_MENU_ITEM`/`CONVERSATION_MENU_ITEM_KEYS`), `key="rename"`. Live-verified this session on the shared "Review attached documents" conversation: menu renders Rename, Move to, Playback, Duplicate, Make public, Share, Pin on top, Delete (8 items, same set ELITEA-2099 documented). |
| Conversation-rename inline input | `chat-conversation-name-input` | Pre-existing (`ChatPage.conversation_name_input`). Live-verified pre-fills with current name; `set_conversation_name()` helper exists and works via click+clear+press_sequentially. |
| Conversation-rename confirm (checkmark) button | `chat-conversation-name-confirm-button`, `data-disabled="true"/"false"` | Pre-existing (`ChatPage.conversation_name_confirm_button`, `is_conversation_name_confirm_enabled()`). Live-confirmed `data-disabled` flips `"true"`→`"false"` on typing a valid changed name. Not clicked by this case (cancel path only) — read for state confirmation, not exercised as an action. |
| Conversation-rename cancel (X) button | `chat-conversation-name-cancel-button` | Pre-existing (`ChatPage.conversation_name_cancel_button`). **This case's primary action target** — live-confirmed: clicking it closes the input (`to_have_count(0)`) and fires NO PUT request. Always `cursor:pointer` — no a11y-snapshot pruning gotcha (unlike the confirm button in its disabled state). |
| App-wide toast alert (error/success severity) | `[data-testid="toast-alert"]` (optionally `[data-severity="{severity}"]`) | Pre-existing (`ChatPage.get_toast_alert`, `TOAST_ALERT_SEVERITY`). Live-confirmed 0 present after cancel. |

## Network Behavior

- Typing a new name (step 3) fires **no** network request — live-confirmed via
  `browser_network_requests` immediately after typing: only pre-existing
  `GET .../conversation/prompt_lib/471/420?...` and
  `POST .../select_conversation/prompt_lib/471/420` traffic from the earlier
  navigation-into-conversation, no new request.
- Clicking cancel (step 4) fires **no** `PUT .../conversation/prompt_lib/{project_id}/{conv_target_id}`
  — live-confirmed: network log unchanged (same two pre-existing entries) after the
  click. This is the case's central assertion: cancel is a pure client-side
  discard, not a save-then-revert round-trip.

## Known Defects Found During Exploration

None new. The case's own "Edit option" label vs the live "Rename" label is the
same drift already filed and accepted as issue #1513 (sibling of #695, both on
`ConversationItem.jsx`'s identical `menuItems` array) — not re-filed here; this
AFS's step 2 asserts the LIVE behavior per that existing clarification, same as
ELITEA-2099.

## Blocked Steps

None — all 6 case steps executed live end-to-end this session, using the shared
pre-existing "Review attached documents" conversation (id 420) as the manual
exploration target (typed "Renamed Chat" into its rename input, then clicked
Cancel — never saved, so no restoration was needed; confirmed via network log that
no PUT ever fired and the sidebar/re-navigation both showed the original name
throughout). This substitution is exploration-only and does not appear in the
spec — the automated test creates and deletes its own `conv_target` per
§ Test Data / § Cleanup.

## Automation Hints

- Reuse `ChatPage.get_conversation_menu_button(id)` /
  `open_conversation_context_menu(id)` / `click_conversation_menu_item("rename")` /
  `set_conversation_name(name)` — all already used by ELITEA-2099's test in the
  same file/class; add this case as a sibling test method reusing the same page
  object, no new page-object work needed.
- Assert the network-request absence the same way `test_conversation_rename_basic_via_edit_option.py`
  asserts the PUT's presence: `chat.capture_requests_matching("/conversation/prompt_lib", method="PUT")`
  around the cancel-click, then assert the captured list is EMPTY (the symmetric
  negative of ELITEA-2099's `assert rename_put_requests`).
- The pre-existing `secrets/secrets/default` 403 console-error exclusion helper
  (`_is_known_secrets_403`) is already written for ELITEA-2099's test file — reuse
  it verbatim rather than re-deriving.
- `ConversationNameRegExp`/`MAX_CONVERSATION_LENGTH` (documented in the
  `chat-interface` `_surface.md` digest) govern `isSaveEnabled`, not the cancel
  path — irrelevant to this case's own assertions, noted only so the implementer
  doesn't need to re-derive it while reading the confirm-button state.
