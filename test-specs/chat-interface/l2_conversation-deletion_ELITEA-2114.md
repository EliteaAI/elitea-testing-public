# Test Case: Chat – Conversation Deletion

## Metadata
- **TMS ID**: ELITEA-2114
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Elitea Testing Team", observed live as `projectId=471` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: ready-for-automation

No existing AFS covers this case (`test-specs/chat-interface/` had only ELITEA-2095 and ELITEA-2090 before this file). Two case-adjacent tests are already merged in `automation/tests/ui/chat/test_conversation_management.py::TestConversationActions` (`test_delete_conversation_with_confirmation`, `test_delete_conversation_cancel`) but cover roughly half of this case's 12 steps and, per live verification, one of their own assertions is currently broken by a product regression (see § Known Defects). See § Coverage Map and § Automation Hints for exactly how this AFS relates to that existing coverage — this is `ready-for-automation`, not `extend-existing`, because the gap (date-grouping, full menu enumeration, dialog body text, deleting the *active* conversation to trigger next-conversation auto-select, main-panel-clears) spans most of the case and needs a new, richer flow rather than a small patch to the existing two tests.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- Test creates its own conversations (see § Test Data) — the case's "at least one conversation exists" precondition is satisfied by setup, not by relying on ambient data.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Active project — whatever `${TEST_USER}`'s default/last-selected project is (observed live as "Elitea Testing Team", id 471). Don't hardcode the id; read it the same way the existing `conversation_api` fixture does.

### generate-per-test (created in test setup, cleaned up in its own teardown)
- **`conv_target`** — the conversation that will be deleted. Create via `conversation_api.create_conversation(name)` (fast, no LLM round-trip — matches the existing tests' pattern; live exploration used a real UI chat-send only because that's the natural way to explore, not because it's required for automation).
- **`conv_sibling`** — a second conversation that must exist so the "next conversation selected" behavior (case step 11) has something deterministic to select. Without a second conversation, deleting the only/active conversation falls back to a dummy/empty state instead of exercising the "next conversation highlighted" branch (see `useDeleteConversation.js`'s `findNextConversation` — returns `null` with 0 remaining conversations).

## Test Steps

**Setup (not a numbered case step)**
0. Create `conv_sibling` then `conv_target` via `conversation_api.create_conversation(name)`. Navigate to chat and open `conv_target` specifically (`chat.navigate_to_chat(conversation_id=conv_target_id)` or click its sidebar item) so it becomes the **active** conversation (shown in the main panel) — this is required for step 11's next-conversation-selection to trigger at all (see § Known Defects/Automation Hints — `onDeleteConversation` only picks a replacement when the deleted conversation IS `activeConversation`).

1. Navigate to `${BASE_URL}/chat`. Verify the sidebar conversation list renders under at least one date-group heading.
   - **Verify**: `[data-testid="chat-conversation-group-header-today"]` is visible and contains `[data-testid="chat-conversation-item-{conv_target_id}"]` as a descendant (a freshly-created conversation always lands in "today" — deterministic, no reliance on ambient older data).
2. Hover the `conv_target` sidebar item.
   - **Verify**: the three-dot menu button (`conversation-menu-menu-button`, scoped under `chat-conversation-item-{conv_target_id}`) transitions from not-visible to visible on hover (it's present in the DOM at all times but CSS `display:none` until hover/`showMenu` — see `ConversationItem.jsx` `menuWrapper` style).
3. Click the three-dot button to open the context menu.
   - **Verify**: the menu (`[data-testid^="chat-conversation-menu-"][data-testid$="-menuitem"]`, testids added this implementation — see § Concrete Handles) shows exactly **Rename, Move to, Playback, Pin on top, Delete** (5 items) for a conversation in the default test project (`${ELITEA_PROJECT_ID}`, the account's own Private/personal project) — NOT the case's literal list, and NOT the 7-item list originally recorded here either; see **CLARIFICATION-2 (implementer, amended in-PR)** below.
4. Click **Delete**.
   - **Verify**: `[data-testid="delete-confirm-dialog"]` becomes visible.
5. Verify the dialog body text.
   - **Verify**: `[data-testid="delete-confirm-message"]`.text == `"Are you sure to delete the {conv_target name} chat? It can't be restored."` (live-verified exact string — NOT the case's literal wording; see CLARIFICATION #695).
6. Verify both dialog buttons are present.
   - **Verify**: `[data-testid="delete-confirm-button"]` visible (text "Delete"); a button with accessible name "Cancel" is visible inside `[data-testid="delete-confirm-dialog"]` (no testid on Cancel — see § Concrete Handles gap).
7. Click **Cancel**.
   - **Verify**: `[data-testid="delete-confirm-dialog"]` is gone; `[data-testid="chat-conversation-item-{conv_target_id}"]` is still present in the sidebar; page URL still contains `/chat/{conv_target_id}` (conversation still active/open).
8. Hover `conv_target` again, click its three-dot button, click **Delete** again.
   - **Verify**: `[data-testid="delete-confirm-dialog"]` visible again (dialog re-opens cleanly after a prior cancel — Axis 2 addition, guards against stale-modal residue).
9. Click `[data-testid="delete-confirm-button"]`.
   - **Verify**: `[data-testid="delete-confirm-dialog"]` becomes hidden; `DELETE /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}` resolves `204`.
10. Verify `conv_target` is gone from the sidebar.
    - **Verify**: `[data-testid="chat-conversation-item-{conv_target_id}"]` has 0 count. If `conv_target` was the only item in the "today" group, `[data-testid="chat-conversation-group-header-today"]` disappears entirely too (live-observed: the whole group collapses when its last conversation is removed).
11. Verify no error surfaces and the next conversation is auto-selected.
    - **Verify**: no new console errors beyond the pre-existing unrelated `secrets/secrets/default` 403 noise (see § Automation Hints — that 403 is unrelated background noise present on every page load in this environment, not caused by delete). Page URL now contains `/chat/{some-other-conversation-id}` (not `conv_target_id`) — live-verified: the app auto-navigates to and selects the next conversation (`conv_sibling` in the 2-conversation setup above) via `POST /api/v2/elitea_core/select_conversation/prompt_lib/{project_id}/{next_id}`. **There is currently no compliant testid+state handle for "this sidebar item is visually highlighted as active"** (see § Concrete Handles gap) — assert via the URL + main-panel content instead of a sidebar CSS class.
12. Verify the main chat panel no longer shows the deleted conversation.
    - **Verify**: `[data-testid="chat-message-list"]` / `[data-testid="chat-message-item"]` content no longer contains `conv_target`'s distinguishing message text, and instead shows `conv_sibling`'s content (consistent with the URL now pointing at `conv_sibling`).

## Expected Results
- Cancel (step 7) leaves `conv_target` fully intact and still active.
- Delete (step 9) removes `conv_target` from the sidebar and from the API's conversation list (`GET .../conversations/prompt_lib/{project_id}` no longer includes its id).
- Deleting the **active** conversation auto-selects and navigates to another remaining conversation; the main panel updates accordingly.
- No console errors attributable to the delete flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | fixture/`auth_state` | asserted |
| Precondition: ≥1 conversation exists | — | Setup | `conversation_api.create_conversation` ×2 | asserted |
| 1 Navigate to Chats, list grouped by date (Today/This Week/Older) | grouped list shown | step 1 | `step 1`: `chat-conversation-group-header-today` visible | asserted *(today + this_week both live-observed during exploration; "older" bucket not reachable with fresh test data in this session — see § Blocked Steps, not a gate)* |
| 2 Hover conversation, 3-dot icon appears | icon visible | step 2 | `step 2`: menu button visibility toggle | asserted |
| 3 Click 3-dot, menu shows: Delete, Edit, Move to, Export, Playback, Pin on top | context menu visible | step 3 | `step 3`: live menu item list | asserted *(live list differs from BOTH the case's list AND this AFS's originally-recorded 7-item list — CLARIFICATION-2, asserting the LIVE 5-item set for the default test project per reverse-masking guard)* |
| 4 Click Delete → modal "Delete conversation?" | confirmation modal appears | step 4 | `step 4`: `delete-confirm-dialog` visible | asserted *(dialog appearance asserted; the case's literal title text "Delete conversation?" doesn't match live "Delete confirmation" — CLARIFICATION #695; the underlying `aria-labelledby`/id wiring is also broken — BUG #694)* |
| 5 Modal body "Are you sure to delete conversation? It can't be restored." | body text correct | step 5 | `step 5`: `delete-confirm-message` text | asserted *(live text differs from case wording — CLARIFICATION #695; AFS asserts the live string)* |
| 6 Modal has Cancel + Delete buttons | both visible | step 6 | `step 6`: button presence | asserted |
| 7 Click Cancel | modal closes, conversation remains | step 7 | `step 7`: dialog gone + item still present | asserted *(duplicates part of already-merged `test_delete_conversation_cancel` — kept because the case requires cancel-then-delete on the SAME conversation as one continuous flow; see § Automation Hints)* |
| 8 Hover same conversation, reopen menu, click Delete again | confirmation modal appears again | step 8 | `step 8`: dialog visible again | asserted |
| 9 Click Delete | modal closes | step 9 | `step 9`: dialog hidden + `DELETE` 204 | asserted *(duplicates part of already-merged `test_delete_conversation_with_confirmation`; kept for the same continuous-flow reason)* |
| 10 Conversation no longer in left panel | removed | step 10 | `step 10`: item count 0 | asserted |
| 11 No error message; next conversation highlighted | no errors, next selected | step 11 | `step 11`: console check + URL routes to next id | asserted *(no compliant sidebar-highlight testid exists yet — asserted via URL + main panel instead; see § Concrete Handles gap)* |
| 12 Main chat panel doesn't show deleted conversation | deleted content gone | step 12 | `step 12`: conversation-content-fetch network check (id-scoped, 200) + message-list content check | asserted *(CLARIFICATION-3, implementer round-2 review fix — see below: message-list-content-only was vacuous since both test conversations are zero-message by design)* |
| Expected Final State (prose): "conversation deleted after confirmation; Cancel preserves it; panel refreshes correctly" | — | steps 7, 9–12 | covered by the rows above | asserted |
| Pass/Fail: "All steps complete without errors" | — | step 11 | console-check | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- `step 8` asserts the dialog re-opens cleanly (no stale backdrop/portal residue) after a prior Cancel — *added: MUI modals are known to leave stale-mounted artifacts in this codebase (see `mui-patterns.md` overlay gotchas); the case's own "hover → reopen menu → Delete again" step implies this should be clean, so it's worth a positive check rather than assuming it.*
- `step 9` asserts the underlying `DELETE .../conversation/prompt_lib/{project_id}/{id}` network call resolves `204` — *added: matches the existing tests' pattern of confirming deletion via the API, not just the DOM, and is what actually proves the deletion is real rather than a client-side-only list splice.*
- `step 11` explicitly asserts no *new* console errors — *added: standard side-channel discipline (silent errors are the worst bugs); the pre-existing unrelated `secrets/secrets/default` 403 noise present on every page load in this environment must be excluded from the "new errors" check, not treated as a failure.*
- `step 12` asserts the `GET .../conversation/prompt_lib/{project_id}/{next_id}?messages_limit=10&sort_order=desc` network request (§ Network Behavior) was made and resolved `200` — *added, CLARIFICATION-3 (implementer, round-2 review fix): `conv_target` and `conv_sibling` are both zero-message by design (§ Automation Hints), so the message-list-content check alone can't distinguish "panel correctly refreshed to `conv_sibling`" from "panel is stuck on stale `conv_target` content" — both read as an empty message list. The network check proves a genuine refetch of the auto-selected conversation's content actually happened, which the DOM-only check could not.*
- (nothing else added beyond the case.)

## Cleanup
1. Delete `conv_sibling` via `conversation_api.delete_conversation(id)` (if not already removed by the test itself — `conv_target` is consumed by the test's own delete action).
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text
fallback ladder (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md`). Where no testid exists, the gap is flagged
explicitly rather than defaulting to a role/name locator.

| Element | Testid handle | Notes |
|---|---|---|
| Conversation list item (dynamic) | `[data-testid="chat-conversation-item-{id}"]` | Already a class constant in `chat_page.py` (`CONVERSATION_ITEM`). |
| Date group header (dynamic) | `[data-testid="chat-conversation-group-header-{group}"]`, `group` ∈ `{today, this_week, older}` (`DATE_GROUP_ORDER` in `conversationList.constants.js`) | Already a class constant (`CONVERSATION_GROUP_HEADER`). `today`/`this_week` live-confirmed this session; `older` inferred from source, not visually confirmed (see § Blocked Steps). |
| Conversation 3-dot menu button | `[data-testid="conversation-menu-menu-button"]`, **must be scoped** inside `chat-conversation-item-{id}` | **Not globally unique** — `ConversationItem.jsx` passes the same static `id="conversation-menu"` to every `DotMenu` instance, so an unscoped query resolves to N elements once N conversations are on screen (confirmed live: `strict mode violation ... resolved to 2 elements` the moment a 2nd conversation existed). Always scope: `page.get_by_test_id(f"chat-conversation-item-{id}").get_by_test_id("conversation-menu-menu-button")`. |
| Context menu items (Rename / Move to / Playback / Make public / Share / Pin on top·Unpin / Delete) | **ADDED this implementation**: `[data-testid="chat-conversation-menu-{key}-menuitem"]`, `key` ∈ `rename, move-to, playback, make-public, share, pin, delete` (one stable id for Pin/Unpin — state carried by the label text, not a second testid). Wired by adding `key: 'chat-conversation-menu-<key>'` to each item in `ConversationItem.jsx`'s `menuItems` array — the existing `DotMenu`/`BasicMenuItem` plumbing already renders `data-testid={testId}-menuitem` off `item.key`, exactly as this AFS predicted. Live-verified: only 5 of the 7 render for a Private-project conversation — see CLARIFICATION-2. Committed on `EliteaAI/EliteaUI`'s `automation/testids` (commit `20567b81`). The pre-existing raw pattern in `chat_page.py::click_delete_menu_item` stays as tracked tech debt (unrelated pre-existing merged tests still use it); the new `click_conversation_menu_item()` method uses the real testid. |
| Delete confirmation dialog container | `[data-testid="delete-confirm-dialog"]` | Works. |
| Delete confirmation body text | `[data-testid="delete-confirm-message"]` | Works — exact live text captured in step 5. |
| Delete confirmation title | **ADDED this implementation**: `[data-testid="delete-confirm-title"]` — a new `titleTestId` prop on `BaseModal.jsx` (mirrors the pre-existing `titleTestId`/`subtitleTestId` pattern already used by `IWModalEntityCardWrapper.jsx`), wired at the `DeleteEntityModal.jsx` call site (`titleTestId="delete-confirm-title"`). Applied to the title's wrapping `Box`, NOT the broken `id="variables-dialog-title"`/`#alert-dialog-title` pair (BUG #694) — a fresh, correct handle. Live-verified text: `"Delete confirmation"`. Committed on `automation/testids` (commit `20567b81`). |
| Delete confirm button | `[data-testid="delete-confirm-button"]` | Works. |
| Cancel button (in delete dialog) | **ADDED this implementation**: `[data-testid="delete-confirm-cancel-button"]`. Root cause was more precise than originally recorded: `DeleteEntityModal.jsx` builds its own `actionsNode` (bypassing `BaseModal.jsx`'s `renderActions()`/`cancelButtonTestId` prop entirely, since it passes `actions=` explicitly) — the fix is a `data-testid` added directly on that Cancel `Button.BaseBtn` in `DeleteEntityModal.jsx`, not a prop wired through `BaseModal.jsx`. Live-verified text: `"Cancel"`. Committed on `automation/testids` (commit `20567b81`). |
| Main panel message list / items | `[data-testid="chat-message-list"]` / `[data-testid="chat-message-item"]` | Already class constants in `chat_page.py` (`messages_list`, `messages_container`) — note their existing `fallback=` params are legacy and should not be copied into new locators. |
| "Sidebar item is the active/highlighted conversation" | **ADDED this implementation**: `data-active="true"/"false"` on `chat-conversation-item-{id}` (`ConversationItem.jsx`, mirrors the project's `data-expanded` pattern), driven off the existing `isActive` prop — a small, mechanical addition, not a bigger change than expected. Committed on `automation/testids` (commit `20567b81`). Step 11 asserts via `is_conversation_active()` (the new attribute) AND the pre-existing URL + main-panel checks (belt-and-suspenders, matching the AFS's original fallback acceptance). |

## Network Behavior
- `DELETE /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}` → `204 No Content` on confirm (step 9).
- `GET /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{next_id}?messages_limit=10&sort_order=desc` → `200` — fetches the auto-selected next conversation's content (step 11).
- `POST /api/v2/elitea_core/select_conversation/prompt_lib/{project_id}/{next_id}` → `200` — marks the next conversation as selected server-side (step 11).
- `DELETE /api/v2/elitea_core/select_conversation/prompt_lib/{project_id}` → `204` — observed immediately after, unselects the deleted conversation's prior selection record. Non-blocking cleanup call; don't gate assertions on it.

## CLARIFICATION-2 (implementer, amended in-PR)

Discovered during Phase 2 exploration for the `add-data-testid` work: this
AFS's step 3 claimed "7 items, live-verified" (Rename, Move to, Playback,
Make public, Share, Pin on top, Delete). Empirically re-verified against the
conversation the AUTOMATED test actually creates — via the default
`conversation_api` fixture, i.e. `${ELITEA_PROJECT_ID}` (`.env.test`, value
`399`) — that conversation comes back `is_private: true` (the account's own
Private/personal project), and only **5** menu items render:
Rename, Move to, Playback, Pin on top, Delete.

Root cause (read from source, `ConversationItem.jsx`'s `menuItems` `useMemo`):
"Make public" and "Share" are conditionally hidden
(`display: projectId == PUBLIC_PROJECT_ID || projectId == personal_project_id
? 'none' : undefined`) whenever the conversation's project IS the viewer's own
personal project — intentional product behavior (a user can't "make public" or
"share" a link to their own private space), not a bug. The original AFS's
7-item observation was made against a *different* active project during
analysis (`id 471`, "Elitea Testing Team" — see § Metadata "Environment
Explored"), where the same conditional resolves to `undefined` (item shown).

Per the reverse-masking guard, this AFS now asserts the LIVE, correct set for
the project the automated test actually runs against (5 items) rather than
either the case's original list or this AFS's own prior 7-item claim. Using
the plain default `conversation_api` fixture (no explicit project switch)
matches the pattern already established by the two existing merged tests in
this suite (`test_delete_conversation_with_confirmation`,
`test_delete_conversation_cancel`), keeping this test's setup simple and
consistent rather than introducing a `switch_project()` call solely to chase
a larger menu-item count.

## Known Defects Found During Exploration

- **[MAJOR] BUG #694** — `BaseModal.jsx` sets `aria-labelledby="alert-dialog-title"` on the MUI `Dialog`, but its own `DialogTitle` has `id="variables-dialog-title"` (a stale leftover predating the `EL-2863` "universal BaseModal" refactor, commit `459c1f8a`, 2026-06-22). No element with `id="alert-dialog-title"` exists anywhere in the DOM for **any** dialog rendered through `BaseModal`/`DeleteEntityModal` — this breaks the accessible name for screen readers app-wide, not just for chat delete. It also silently broke the already-merged `tests/ui/chat/test_conversation_management.py::TestConversationActions::test_delete_conversation_with_confirmation`, whose title assertion I confirmed FAILS right now (ran it locally: `AssertionError: Expected 'Delete conversation' in title, got:` — empty string, because `Dialog.get_title()` in `automation/components/mui.py` queries the non-existent `#alert-dialog-title`). This AFS's own step 4/5 assertions avoid the same trap by asserting the dialog body (`delete-confirm-message`, which works) rather than a title lookup through the broken id. Isolated, non-blocking for this AFS — soft-assert-and-link if a title assertion is ever added: `# Known defect: #694`.

## Blocked Steps
- Step 1's "Older" date-group bucket (`chat-conversation-group-header-older`) was not reachable with fresh-created test data in a single session (would need a conversation genuinely dated outside the current week, which the API doesn't offer a way to backdate). The grouping *mechanism* and testid pattern are verified for `today` and `this_week` (both live-observed), and `older` is a documented third member of the same `DATE_GROUP_ORDER` constant — low risk, but flagging so the implementer doesn't claim full 3-bucket coverage without either backdated fixture data or accepting the 2-of-3 verification as sufficient for the case's intent ("list is grouped by date").

## Automation Hints
- Framework: Playwright + pytest, confirmed (`.agents/testing.md`). Follow `ChatPage` (`automation/pages/chat_page.py`) — it already has `conversation_exists_in_list`, `open_conversation_menu`, `click_delete_menu_item`, `get_delete_button_count`; the new methods this case needs (menu-item enumeration, group-header scoping, active-conversation targeting) should live there too, not inline in the spec.
- Use `conversation_api.create_conversation(name)` for `conv_target`/`conv_sibling` (session-scope fixture, matches `test_delete_conversation_with_confirmation`'s existing pattern) — don't create test data via a real chat-send (that invokes the live LLM and is unnecessarily slow/costly; the live exploration for this AFS used chat-send only because that's how a human/analyst naturally explores a chat UI).
- **Overlap disclosure**: steps 6/7 (Cancel preserves) and 9/10 (Delete removes, dialog buttons) functionally duplicate assertions already in the merged `test_delete_conversation_with_confirmation` / `test_delete_conversation_cancel`. This AFS specs them anyway because (a) the case requires cancel-then-delete on the *same* conversation as one continuous flow, which neither existing test does, and (b) this flow opens `conv_target` as the *active* conversation before deleting it (required for step 11), which neither existing test does either. Whether to keep all three tests, or fold the two existing ones into this richer one, is an implementer/lead call — not made unilaterally here.
- Next-conversation selection (step 11) is only deterministic with exactly the two test-created conversations present (`conv_target` + `conv_sibling`) — if the test project accumulates other stray conversations over time, `findNextConversation`'s "most recent other conversation" pick could land on one of those instead of `conv_sibling`. Assert generically ("URL no longer references `conv_target_id`, and references *some* valid remaining conversation") rather than hardcoding `conv_sibling`'s id, unless the suite guarantees a clean project.
- The pre-existing `secrets/secrets/default/{project_id}` `403` console error is unrelated background noise present on every page load in this local environment (unrelated toolkit/secrets panel probe) — exclude it explicitly from any "no new console errors" filter rather than let it cause false positives.
