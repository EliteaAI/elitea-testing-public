# Test Case: Chat – Conversation Rename – Basic Rename via Edit Option

## Metadata
- **TMS ID**: ELITEA-2099
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Elitea Testing Team", observed live as `projectId=471` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: ready-for-automation

**Related existing coverage (reused as context, not as a covering spec):**
`automation/tests/ui/chat/test_conversation_management.py::TestConversationActions::test_rename_conversation_via_ui`
(linked to a *different* TMS case, ELITEA-0570) already proves the core "rename via
three-dot menu → new name in sidebar, old name gone, persisted via API" outcome, via
`ChatPage.rename_conversation_via_menu()` (raw `[role="menuitem"]:has-text("Rename")`
+ raw-class input selectors, confirms with **Enter**, not a checkmark click). This
case's own steps ask for observables that test never touches: 3-dot icon
appears-on-hover, full context-menu content, the input pre-filled with the *current*
name before editing, checkmark/cancel icons visible, save via an explicit **click on
the checkmark** (not Enter), no-error-shown, and persistence verified by navigating
away and back through the UI (not just re-fetching via API). That is most of this
case's 9 steps, not "a small number of missing assertions" — per SKILL.md's
near-rewrite boundary call this is `ready-for-automation`, not `extend-existing`.
Both tests may live in the same file/class and share the page object; nothing here
requires touching the existing test.

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
  `conversation_api.create_conversation(name)` (fast, no LLM round-trip — matches the
  existing `test_rename_conversation_via_ui` pattern). Suggested original name:
  `at_rename_basic_orig`. New name per the case's own Test Data table:
  `HI Chat_edited`.

## Test Steps

**Setup (not a numbered case step)**
0. Create `conv_target` via `conversation_api.create_conversation("at_rename_basic_orig")`.
   Navigate to `${BASE_URL}/chat`.

1. Verify the Chats/Conversations panel is displayed.
   - **Verify**: `chat.conversations_panel_heading` (`chat-conversations-heading`)
     visible; `[data-testid="chat-conversation-item-{conv_target_id}"]` visible in
     the sidebar list.
2. Hover `conv_target`'s sidebar item and verify the three-dot icon appears.
   - **Verify**: `get_conversation_menu_button(conv_target_id)` (scoped
     `conversation-menu-menu-button` inside `chat-conversation-item-{id}`) transitions
     from not-visible to visible on hover (present in DOM at all times, CSS
     `display:none` until hover — `ConversationItem.jsx`'s `menuWrapper` style).
3. Click the three-dot icon and verify the context menu is visible with its live
   item set.
   - **Verify**: `[data-testid^="chat-conversation-menu-"][data-testid$="-menuitem"]`
     resolves to the LIVE set for a non-personal/non-public project — **Rename, Move
     to, Playback, Duplicate, Make public, Share, Pin on top, Delete** (8 items) —
     **NOT** the case's literal "Delete, Edit, Move to, Export, Playback, Pin on top"
     (6 items, wrong labels, one nonexistent item). This is case-text drift, same
     pattern already accepted for ELITEA-2114 (issue #695) — filed as a sibling
     clarification, issue #1513 (see § Known Defects Found). Assert the LIVE set
     is non-empty and contains `chat-conversation-menu-rename-menuitem`; do not
     assert the case's stale literal list.
4. Click the **Rename** menu item (`chat-conversation-menu-rename-menuitem` — the
   case's own "Edit option" refers to this item; its rendered label is "Rename",
   not "Edit" — see step 3's clarification).
   - **Verify**: the conversation name becomes an editable inline input
     (`chat-conversation-name-input`, ADDED this session — see § Concrete Handles)
     **pre-filled with the CURRENT name** (`conv_target`'s original name,
     `at_rename_basic_orig`) — assert the input's value equals the pre-rename name
     before any edit is made.
5. Verify a checkmark (save) icon and X (cancel) icon appear.
   - **Verify**: `chat-conversation-name-confirm-button` visible, carrying
     `data-disabled="true"` (unchanged name ⇒ save not yet enabled — mirrors the
     folder-rename `isFolderSaveEnabled` pattern, ELITEA-2458); a11y-snapshot gotcha
     from the folder-rename digest applies here too — this element may be pruned
     from a `browser_snapshot`'s tree in the unchanged/`cursor:default` state, so
     assert via the testid locator directly (`is_visible()`/`get_attribute`), never
     via a `browser_snapshot` accessible-name read. `chat-conversation-name-cancel-button`
     visible (always `cursor:pointer`, never pruned).
6. Clear the current name and type `HI Chat_edited` (per the case's own Test Data).
   - **Verify**: `chat-conversation-name-input`'s value equals `HI Chat_edited`;
     `chat-conversation-name-confirm-button`'s `data-disabled` flips to `"false"`
     (name changed AND passes `ConversationNameRegExp`).
7. Click the checkmark (save) icon — **an explicit click on
   `chat-conversation-name-confirm-button`, not Enter** (distinct from the existing
   `rename_conversation_via_menu()` helper, which presses Enter).
   - **Verify**: the input closes (`chat-conversation-name-input` no longer present);
     `[data-testid="chat-conversation-item-{conv_target_id}"]` shows the new name
     `HI Chat_edited` in the sidebar. Underlying network call:
     `PUT /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}`
     resolves `200` (live-confirmed).
8. Verify no error message is shown.
   - **Verify**: no `[data-testid="toast-alert"][data-severity="error"]` appears; no
     NEW console errors beyond the pre-existing, unrelated
     `secrets/secrets/default` 403 noise present on every page load in this
     environment (same exclusion as ELITEA-2114's AFS).
9. Navigate away and return to the Chats section; verify the updated name persists.
   - **Verify**: navigate to `${BASE_URL}/chat` (root — the empty-composer/greeting
     state), then back into `conv_target` via its sidebar item (or via
     `chat.navigate_to_chat(conversation_id=conv_target_id)`); the sidebar item
     still reads `HI Chat_edited` (asserted through the UI, not only re-fetched via
     API — closes the gap the existing `test_rename_conversation_via_ui` leaves,
     which only re-checks via `conversation_api.get_conversation()`).

## Expected Results
- The conversation's inline rename editor pre-fills with its current name, shows
  distinct checkmark/cancel affordances gated on a real "name changed AND valid"
  state, and commits the new name via an explicit checkmark click (not just Enter).
- No error surfaces on save.
- The new name persists both immediately in the sidebar and after navigating away
  and back into the conversation.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: ≥1 conversation exists | — | Setup | `conversation_api.create_conversation` | asserted |
| 1 Navigate to Chats section, list displayed | conversations list shown | step 1 | `chat-conversations-heading` + item visible | asserted |
| 2 Hover conversation, verify 3-dot icon appears | icon visible | step 2 | menu-button visibility toggle | asserted |
| 3 Click 3-dot, verify menu shows: Delete, Edit, Move to, Export, Playback, Pin on top | context menu visible with all options | step 3 | live menu item list | asserted *(live list is Rename/Move to/Playback/Duplicate/Make public/Share/Pin on top/Delete — differs from the case's literal list; CLARIFICATION, issue #1513, sibling of #695 — reverse-masking guard, live product is correct)* |
| 4 Click Edit → conversation becomes editable inline input, current name pre-filled | editable input with current name | step 4 | `chat-conversation-name-input` value == pre-rename name | asserted *(the case's own item is labelled "Rename" live, not "Edit" — same #1513 clarification)* |
| 5 Verify checkmark + X icons appear | both visible | step 5 | `chat-conversation-name-confirm-button` / `-cancel-button` visible | asserted |
| 6 Clear name, type 'HI Chat_edited' | new name appears in field | step 6 | input value check | asserted |
| 7 Click checkmark → input closes, new name shown in left panel | rename committed | step 7 | input gone + sidebar item text + `PUT …/conversation/…` 200 | asserted |
| 8 Verify no error message is shown | no error shown | step 8 | toast-alert(error) absence + console check | asserted |
| 9 Navigate away and return, updated name persists | name persists | step 9 | sidebar item text after nav-away/nav-back | asserted |
| Expected Final State (prose): "renamed and persists after navigation" | — | steps 7, 9 | covered by the rows above | asserted |
| Pass/Fail: "All steps complete without errors" | — | step 8 | toast/console check | asserted |
| Pass/Fail: "Rename succeeds and name persists" | — | steps 7, 9 | covered by the rows above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- step 4 additionally asserts the input is **pre-filled with the current name**
  (not just "an input appears") — *added: the case's own expected result explicitly
  says "with current name pre-filled", which the existing
  `rename_conversation_via_menu()` helper never checks (it clears immediately).*
- step 5 asserts `data-disabled="true"` on the confirm button in the unchanged
  state, and `"false"` once changed (step 6) — *added: mirrors the ELITEA-2458
  folder-rename precedent (testid=identity/state=data-* ruling) and gives the
  "checkmark active/inactive" a real, testable signal instead of a CSS-only cue.*
- step 7 asserts the underlying `PUT .../conversation/prompt_lib/{project_id}/{id}`
  network call resolves `200` — *added: proves the rename is real (backend-persisted),
  not a client-side-only list splice, matching the existing tests' network-check
  pattern.*
- step 8 explicitly asserts no NEW console errors, excluding the pre-existing
  unrelated `secrets/secrets/default` 403 noise — *added: standard side-channel
  discipline; same exclusion already documented for ELITEA-2114.*
- step 9 asserts persistence via the **UI** (sidebar text after navigate-away/back),
  not only via a `conversation_api.get_conversation()` re-fetch — *added: the
  existing `test_rename_conversation_via_ui` only re-checks via API; the case's own
  step 9 explicitly asks for navigate-away-and-return, which is a UI-level check the
  existing test never performs.*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)` in a
   `try`/`finally`, per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback
ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Where
no testid existed, testids were added this session (see below); nothing in this
AFS relies on a role/name/CSS handle.

| Element | Testid handle | Notes / provenance |
|---|---|---|
| Conversations panel heading | `chat-conversations-heading` | Pre-existing (`ChatPage.conversations_panel_heading`). |
| Conversation list item (dynamic) | `[data-testid="chat-conversation-item-{id}"]` | Pre-existing class constant (`CONVERSATION_ITEM`). |
| Conversation 3-dot menu button | `[data-testid="conversation-menu-menu-button"]`, must be scoped inside `chat-conversation-item-{id}` | Pre-existing (`CONVERSATION_MENU_BUTTON`); not globally unique — same static `id="conversation-menu"` on every item, confirmed live. Use `ChatPage.get_conversation_menu_button(id)`. |
| Context menu items (Rename / Move to / Playback / Duplicate / Make public / Share / Pin on top·Unpin / Delete) | `[data-testid="chat-conversation-menu-{key}-menuitem"]`, `key` ∈ `rename, move-to, playback, make-public, share, pin, delete` (`Duplicate` has no `key` in `ConversationItem.jsx` — no testid, not needed by this case) | Pre-existing (`CONVERSATION_MENU_ITEM`, `CONVERSATION_MENU_ITEM_KEYS`), added during ELITEA-2114's implementation (`EliteaAI/EliteaUI@20567b81`). Live-verified this session: 8 items render for project 471 (non-personal/non-public) — `Rename, Move to, Playback, Duplicate, Make public, Share, Pin on top, Delete`. |
| Conversation-rename inline input | **ADDED this session**: `chat-conversation-name-input` — `inputProps={{ 'data-testid': '...' }}` on `ConversationItem.jsx`'s `Input.StyledInputEnhancer`, mirroring `FolderItem.jsx`'s pre-existing `chat-folder-name-input` (`inputProps` channel, ladder rung 1 per `add-data-testid`). Committed `EliteaAI/EliteaUI@ff56e29d` on `automation/testids`. Live-verified: pre-fills with the current name, updates on type. |
| Conversation-rename confirm (checkmark) button | **ADDED this session**: `chat-conversation-name-confirm-button`, carrying `data-disabled="true"/"false"` (state via data-*, testid=identity — mirrors `chat-folder-name-confirm-button`'s `isFolderSaveEnabled` pattern exactly). Same commit `EliteaAI/EliteaUI@ff56e29d`. **A11y-snapshot gotcha applies** (documented for the folder-rename sibling, ELITEA-2458): in the disabled/`cursor:default` state the element MAY be pruned from a `browser_snapshot`'s accessibility tree — assert via the testid locator directly, never via a snapshot accessible-name read. |
| Conversation-rename cancel (X) button | **ADDED this session**: `chat-conversation-name-cancel-button`. Same commit. Always `cursor:pointer` (unlike confirm) — not affected by the snapshot-pruning gotcha. |
| App-wide toast alert (error/success severity) | `[data-testid="toast-alert"][data-severity="{severity}"]` | Pre-existing (`ChatPage.toast_alert`, `TOAST_ALERT_SEVERITY`). |

## Network Behavior

- Rename commit (step 7): `PUT /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}` → `200`, live-confirmed (request body includes the new `name`).
- No `DELETE`/`POST` calls expected on this flow beyond the setup's `create_conversation` and the incidental `POST .../select_conversation/...` the app fires when the rename click also navigates into the conversation (observed live; not a case-required assertion, note only — see § Automation Hints).

## Known Defects Found During Exploration

- **Issue #1513** `[Clarification][ELITEA-2099] Case text says context-menu item is
  'Edit'/lists 'Export'; product labels it 'Rename' and has no 'Export'` — filed as
  a `question` + `case-text-drift` sibling of the already-accepted #695
  (ELITEA-2114, identical pattern on the same component). Reverse-masking: the live
  product is correct, the case text is stale. This AFS's steps 3–4 assert the LIVE
  behavior, not the case's literal wording — no `defect-found` status, no code
  change requested.

## Blocked Steps

None — all 9 case steps executed live end-to-end this session (`conv_target`
substituted with the shared pre-existing "Review attached documents" conversation
during live exploration only; renamed to `HI Chat_edited` then restored to its
original name immediately after, to avoid leaving pollution in the shared DEV
project — the automated test itself creates and deletes its own conversation, per
§ Test Data / § Cleanup, so this substitution is exploration-only and does not
appear in the spec).

## Automation Hints

- Clicking the confirm (checkmark) button, when the conversation being renamed is
  NOT already the active/open one, ALSO opens/selects that conversation (observed
  live: URL changed from `/chat` to `/chat/{id}?name=...` and the main panel loaded
  the conversation's message history). This is incidental to `onSave`/`onEdit`'s
  existing conversation-select side effect, not a defect — if the test asserts
  page URL, account for this navigation rather than treating it as unexpected.
- Reuse `ChatPage.get_conversation_menu_button(id)` /
  `open_conversation_context_menu(id)` / `click_conversation_menu_item("rename")`
  (testid-based, id-scoped — ELITEA-2114 helpers) rather than the older
  `open_conversation_menu(conv_name)` / `rename_conversation_via_menu()` pair
  (name-based, raw-selector, tracked tech debt) — the new helpers are what this
  AFS's handles assume, and they don't collide with the pre-existing
  `test_rename_conversation_via_ui` (ELITEA-0570) which is free to keep using the
  older pair unmodified.
- `ConversationNameRegExp`/`MAX_CONVERSATION_LENGTH` govern `isSaveEnabled` the same
  way `FolderNameRegExp` governs folder rename (see the chat-interface `_surface.md`
  digest's Folder-rename section) — not exercised by this case (which only uses a
  simple valid name), but directly relevant to the sibling conversation-rename
  boundary cases already in the TMS folder (ELITEA-2100–2113: cancel-discards,
  49/50-char saves, >50-char typing/pasting, first-char-space, empty/short/special-char
  checkmark-inactive states, tooltip content) — this AFS's `chat-conversation-name-*`
  testids are the handles those cases will need too; check `test-specs/chat-interface/`
  for an existing AFS on the same testids before re-adding them.
