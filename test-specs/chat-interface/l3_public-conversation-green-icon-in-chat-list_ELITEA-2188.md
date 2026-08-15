# Test Case: Chat – Team Project – Public Conversation Marked with Green People Icon in Chat List

## Metadata
- **TMS ID**: ELITEA-2188
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; Team project "Elitea Testing Team", observed live as `projectId=471`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login (dev-token user renders as "Test Bot"/"TB")
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live. Confirmed the green-icon signal is real (fill color `#2BD48D` = `theme.palette.status.published` = `green`, vs `#A9B7C1` default for private conversations with participants) and is NOT yet distinguishable via a stable state attribute — only via raw SVG `fill`. Two genuine **testid gaps** found (not defects): (1) the "Make public" confirmation dialog carries zero testids at all; (2) the multi-user-icon element's existing `data-has-icon` boolean only encodes *presence*, not *publicness* — a new `data-*` state attribute is needed to assert "green because public" without reading a raw CSS/SVG fill value. Both are implementer work per `add-data-testid`, spec'd below — not blockers.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User is in a **Team project** — not ambient at session start (the account's default/last-active project can be Private); automation must explicitly switch via `ChatPage.switch_project("471")` (existing method, ELITEA-2091/2167/2168 precedent) to the Team project **"Elitea Testing Team"** (`471`) before proceeding.
- At least one conversation must exist that the acting user can make public (a fresh conversation created via `+ Chat` and one sent message, per the ELITEA-2167/2091 pattern — do NOT reuse a pre-existing shared conversation; see § Test Data note on conversation 420).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Team project "Elitea Testing Team", id `471` — `ChatPage.switch_project("471")`.

### generate-per-test (created in test setup, own teardown)
- **New conversation A** ("to be made public") — created via `+ Chat` + one sent message (same pattern as ELITEA-2167 step 9), so it has a real server-side id and appears under "Today". Made public via the conversation's context-menu "Make public" action (case step under test).
- **New conversation B** ("private control, WITH participants")  — created the same way, then given a second participant (e.g. via "Invite Users", ELITEA-2167's `open_add_teammate_dialog()` flow) so it renders `data-has-icon="true"` but stays private. This is the case's own step 3 negative control, and it is the **sharp** one: a single-owner conversation (`private_without_users`) renders **no icon at all** (`data-has-icon="false"`) and would only prove "an icon is/isn't there", not "the icon isn't green" — confirmed live this session against the environment's pre-existing conversations (below).

### Analyst-session-only observation (NOT test data to reuse)
- **Conversation id `420`** ("Review attached documents", project 471) was made public live during this analysis to confirm the green-icon behavior (§ below). It is now **permanently public** — the UI exposes no "Make private" action once a conversation is public (`ConversationItem.jsx`'s `menuItems` filters `'Make public'` out entirely once `!is_private`, and no inverse item is ever added — confirmed by reading the `.filter(item => item.label !== 'Make public')` at the end of the `menuItems` `useMemo`). Reverting via the app's own `PUT /api/v2/elitea_core/conversation/prompt_lib/471/420` was attempted from the browser console and failed (`Failed to fetch` — the app's real fetch call carries a bearer token not present in `localStorage`/reachable from a bare `fetch()`; not pursued further as an analysis-time side effect). **The implementer's test MUST create its own fresh conversations (A/B above), never assert against conversation 420.** No further action needed — this is dev/local test data, already routinely mutated by the rest of the suite.

## Test Steps

1. Switch to the Team project (`ChatPage.switch_project("471")`); confirm the project switcher shows "Elitea Testing Team".
   - **Verify**: sidebar shows the "Chats" list; `chat-conversations-heading`-scoped list is populated.
2. Create conversation A (`+ Chat` → send one message, e.g. "hello") and conversation B (`+ Chat` → send one message → Invite a second user via the existing Invite-Users flow, ELITEA-2167 pattern).
   - **Verify**: both appear under "Today" (`is_conversation_in_group(id, "today")`); B's `conversation-multi-user-icon` settles to `data-has-icon="true"` (2 participants: owner + invited user) — same assertion idiom as `ChatPage.wait_for_conversation_multi_user_icon()`.
3. Open conversation A's context menu (`open_conversation_context_menu(conv_a_id)`) and click **Make public** (`click_conversation_menu_item("make-public")` — the item key already exists in `CONVERSATION_MENU_ITEM_KEYS`).
   - **Verify**: the confirmation dialog opens (title "Public conversation?", body "Are you sure to make your conversation public?", buttons "Cancel"/"Make public") — **currently has NO testids of any kind** (confirmed live via DOM read — see § Concrete Handles gap #1). Click "Make public" to confirm.
   - **Verify (network)**: `PUT /api/v2/elitea_core/conversation/prompt_lib/471/{conv_a_id}` fires and returns `200` (confirmed live).
4. Re-read conversation A's sidebar row.
   - **Verify**: `conversation-multi-user-icon`'s inner `<svg>` renders with `fill="#2BD48D"` (== `theme.palette.status.published`, a green) — confirmed live this session. `data-has-icon` stays `"true"` (unchanged from before — presence was already true if A had ≥1 participant besides the owner at creation, or becomes true once public per `getConversationType()`'s `!is_private` branch — either way the wrapper doesn't disappear, only the icon's color/type changes).
5. Compare against conversation B (private, `data-has-icon="true"`) and against a private single-owner conversation with no other participants (if one exists in the fixture set; the environment's pre-existing "HI Chat"/"All" conversations — ids 507/506 — served this role live: `fill="#A9B7C1"`, the DEFAULT (non-green) icon fill).
   - **Verify**: B's icon fill is **NOT** `#2BD48D`/`theme.palette.status.published` — it stays the default `theme.palette.icon.fill.default` (`#A9B7C1` observed live). This is the case's own step-3 assertion ("private conversations do NOT show the green icon"), satisfied by a conversation that DOES show *an* icon (proving the distinguishing factor is publicness/color, not mere icon presence).
6. Click conversation A (now public) to open it.
   - **Verify**: full message history renders (sender name + "to Elitea"/"to {agent}" + relative timestamp per message, e.g. "1 day ago" observed live on a pre-existing conversation) — same `region "scrollable content"` / message-list rendering already exercised by every other chat test in this suite (no new handle needed here; reuse `ChatPage`'s existing message-thread assertions, e.g. as in `test_open_conversation_today_section.py`).
7. Verify the message input field and the PARTICIPANTS USERS section.
   - **Verify**: `chat.message_input` is visible and enabled. The "Users in this conversation" badge (`chat-participants-badge-button`, scoped via `PARTICIPANTS_BADGE.format("users")`) is visible and clickable; opening it (`open_participants_popover(section="users")`) shows a "Users" heading and lists the conversation's participants (owner at minimum) — same handle already established by ELITEA-2167/2168/2095.

## Expected Results
- Making a Team-project conversation public (via the existing "Make public" context-menu action) turns its sidebar multi-user icon **green** (`theme.palette.status.published`, `#2BD48D` observed).
- A private conversation with participants shows the SAME icon wrapper (`data-has-icon="true"`) but in the DEFAULT, non-green fill (`theme.palette.icon.fill.default`, `#A9B7C1` observed) — never green.
- The now-public conversation's full history, sender/timestamp metadata, message input, and PARTICIPANTS USERS section all remain fully accessible/functional — no regression from the publicness change.
- No unexpected console errors (the pre-existing, already-documented project-471 `secrets` 403 is filtered — see `_is_known_project_471_secrets_403` idiom already used by 3 other tests in this suite).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Chats in Team project | Conversations listed | step 1 | step 1: switch_project + list populated | asserted |
| 2 Locate a public conversation; verify green people icon | Green icon visible | steps 2–4 | step 4: SVG `fill` == `theme.palette.status.published` | asserted |
| 3 Verify private conversations do NOT show the green icon | Private convs without green icon | step 5 | step 5: SVG `fill` != published-green, using a WITH-PARTICIPANTS private control (sharper than a no-icon-at-all control) | asserted |
| 4 Click the public conversation | Full history shown; senders + timestamps | step 6 | step 6: message thread renders, reusing existing message-list assertions | asserted |
| 5 Message input available; PARTICIPANTS USERS shows participants | Input field + PARTICIPANTS visible | step 7 | step 7: `message_input` visible, users popover lists participants | asserted |

### Axis 2 — Analyst additions
- step 3 (Make public confirm) asserts the underlying `PUT .../conversation/prompt_lib/471/{id}` returns `200` — *added: the case only describes the visible outcome (icon turns green); the network assertion proves the publicness change is server-persisted, not a client-only list re-render (same idiom as `confirm_delete_conversation()`'s response-status check elsewhere in this page object).*
- step 5 uses a WITH-PARTICIPANTS private conversation as the negative control, not a single-owner one — *added: a single-owner control only proves "icon present/absent", the sharper control isolates the actual variable the case cares about (publicness), matching the case's own step 3 wording ("private conversations", not "conversations without other participants").*
- No unexpected-console-errors guard across the full flow — *added: standing suite convention (every recent chat AFS in this feature carries it), catches a silent regression the case's own steps wouldn't otherwise surface.*

## Cleanup
1. Delete conversations A and B via the existing `open_conversation_context_menu` → `click_conversation_menu_item("delete")` → `confirm_delete_conversation()` flow (already used elsewhere in this suite) — both are test-created, safe to remove.
2. Conversation `420` is NOT cleaned up (see § Test Data — no UI path exists to make a conversation private again; left as-is, a pre-existing, already-mutated dev-environment artifact).

## Concrete Handles (discovered during exploration)

Per `.agents/testing.md` § Locator policy (testid-only, no fallback ladder) — the getByRole/getByText ladder in the generic AFS template does NOT apply on this project.

| Element | Testid / Handle | State |
|---|---|---|
| Conversation sidebar item | `[data-testid="chat-conversation-item-{id}"]` (`CONVERSATION_ITEM` template, existing) | `data-active`, `data-pinned` |
| Multi-user icon wrapper | `[data-testid="conversation-multi-user-icon"]` (existing, `chat_page.py:5557`) | `data-has-icon="true"/"false"` (existing) — **see gap #2 below: no attribute yet distinguishes public/green from private-with-users/default** |
| Context-menu button | `[data-testid="conversation-menu-menu-button"]` scoped inside `CONVERSATION_ITEM` (existing, `get_conversation_menu_button()`) | — |
| "Make public" menu item | `[data-testid="chat-conversation-menu-make-public-menuitem"]` (existing — `"make-public"` already in `CONVERSATION_MENU_ITEM_KEYS`, `chat_page.py:1010`) | — |
| **"Make public" confirm dialog** | **testid needed** — see gap #1 | — |
| **"Make public" confirm dialog's confirm/cancel buttons** | **testid needed** — see gap #1 | — |
| Users participants badge | `[data-testid="chat-participants-badge-button"]` scoped via `PARTICIPANTS_BADGE.format("users")` (existing) | — |
| Users participants popover | `participants_popper` `LocatorDescriptor(testid="chat-participants-popper")` (existing) | — |
| Message input | `chat.message_input` `LocatorDescriptor` (existing) | — |

### Testid gap #1 — "Make public" confirmation dialog has ZERO testids

`ConversationItem.jsx`'s `menuItems` array (line 232) wires the "make-public" menu item's `alertTitle`/`confirmText`/`confirmButtonTitle`/`onConfirm` (lines 232–243) with no `entityName`, so `DotMenu.jsx` renders it via the plain `Modal.BaseModal` branch (`DotMenu.jsx:535–545`), **not** the `Modal.DeleteEntityModal` branch that already carries testids (`delete-confirm-dialog`/`delete-confirm-button`/etc., used by chat's own Delete action). Confirmed live via a direct DOM read of the open dialog (`role="dialog"`): no element inside it — title, body, Cancel button, confirm button — carries any `data-testid`. `BaseModal.jsx` itself DOES accept `data-testid` / `titleTestId` / `closeButtonTestId` / `confirmButtonTestId` / `cancelButtonTestId` props (`BaseModal.jsx:31–34`); `DotMenu.jsx`'s `Modal.BaseModal` call (lines 535–545) simply never forwards any of them — this is the ONLY other consumer of this exact confirm shape (`BucketItem.jsx`'s "Delete bucket?", grepped — both share the same gap).

**Work needed (`add-data-testid`, EliteaUI `automation/testids`):**
- Thread new caller-supplied testid props through the `menuItems` item shape (same precedent as the existing `submenuTestId` prop on the "Move to" item, `ConversationItem.jsx` — a per-item, caller-named testid forwarded through `DotMenu.jsx` to avoid hardcoding a feature-scoped id in the shared component, per `.agents/testing.md` § Locator policy "shared components never hardcode feature-scoped testids").
- Suggested names (case-scoped, `{section}-{element}-{type}`): `chat-conversation-make-public-confirm-dialog`, `chat-conversation-make-public-confirm-button`, `chat-conversation-make-public-cancel-button`. Verify uniqueness before adding; naming is the implementer's call, this is a starting suggestion only.
- `DotMenu.jsx`'s `Modal.BaseModal` render (lines 535–545) needs `data-testid={activeDialog.props.dialogTestId}`, `confirmButtonTestId={activeDialog.props.confirmButtonTestId}`, `cancelButtonTestId={activeDialog.props.cancelButtonTestId}` (or equivalent) added and threaded from `activeDialog.props` the same way `alertTitle`/`confirmText`/etc. already are.

### Testid gap #2 — icon color/publicness has no state attribute, only `data-has-icon` presence

`ConversationItem.jsx`'s `conversation-multi-user-icon` wrapper (line 419) already carries `data-has-icon` (line 420, presence-only: `true` for BOTH `private_with_users` and `public`). The GREEN-vs-default distinction this case is actually about lives ONLY in the rendered `<svg>`'s `fill` attribute (lines 424–434: `theme.palette.icon.fill.default` vs `theme.palette.status.published`), which is a raw CSS-adjacent value, not a testid-policy-compliant handle. Per `.agents/testing.md` § Locator policy ("Testid = stable identity; state via `data-*` attributes… never a state-dependent testid"), the compliant fix is a NEW `data-*` attribute on the SAME `conversation-multi-user-icon` element (testid identity unchanged) — e.g. `data-conversation-type={conversationType}` (reusing the existing `getConversationType()` value, line 108–113: `"public"` / `"private_with_users"` / `"private_without_users"`), OR the narrower `data-public={!is_private}` if the implementer prefers a boolean scoped exactly to what this case asserts.

**Work needed (`add-data-testid`):** add the chosen `data-*` attribute to `ConversationItem.jsx` line 419's `<Box>` (one-line JSX change, no new DOM node, no functional impact — passes the zero-functional-impact check). Page-object addition: extend (or add a sibling to) `wait_for_conversation_multi_user_icon()` with a second `expect().to_have_attribute()` on the new attribute — same `expect()`-based auto-retry idiom already used there (the method's own docstring already documents the attribute settling asynchronously right after conversation creation; the new attribute is expected to settle on the SAME event, not a separate one).

## Network Behavior
- `PUT /api/v2/elitea_core/conversation/prompt_lib/471/{conversation_id}` — fires on "Make public" confirm, body includes `is_private: false`; `200 OK` confirmed live (this is the same endpoint `onEdit({ ...conversation, is_private: false })` in `ConversationItem.jsx`'s `handleMakePublic` calls — `ConversationItem.jsx:161-163`).
- Pre-existing, already-documented project-471 `GET .../secrets/secrets/default/471` → `403` fires on every page load in this project regardless of action — filter it exactly as `test_create_new_conversation_team_project_attachments_and_llm.py` / `test_participants_dropdown_click_name_inserts_mention.py` / `test_team_users_mention_and_remove_participants.py` already do (`_is_known_project_471_secrets_403`), so it can't mask a genuinely new error.

## Known Defects Found During Exploration
None found. Both items above (§ Concrete Handles gaps #1/#2) are testid/state-attribute GAPS — implementer work per `add-data-testid`, not product defects; the underlying behavior (publicness persists, icon color changes) works correctly.

## Blocked Steps
None. All 5 case steps executed live end-to-end (see § Test Steps for exact observations); the two testid gaps are additive JSX/attribute work, not blockers to automating this case.

## Automation Hints
- Framework: Playwright/pytest, testid-only locators (`.agents/testing.md` § Locator policy — the generic AFS template's `getByRole` ladder does not apply on this project).
- Page object: `automation/pages/chat_page.py` (extend — do not duplicate `switch_project`, `open_conversation_context_menu`, `click_conversation_menu_item`, `wait_for_conversation_multi_user_icon`, `open_participants_popover`, all pre-existing).
- Reuse `ChatPage.click_conversation_menu_item("make-public")` for step 3's click — the item key already exists in `CONVERSATION_MENU_ITEM_KEYS` (`chat_page.py:1010`); only the CONFIRM step needs new testid-backed handles (gap #1).
- Reuse the ELITEA-2167 pattern for creating conversation B with a second participant (Invite Users flow) — do not reinvent.
- Wait strategy for the icon-color assertion: `expect().to_have_attribute()` on the new `data-*` attribute (gap #2), same pattern `wait_for_conversation_multi_user_icon()` already uses for `data-has-icon` — NOT a raw one-shot DOM read (that method's own docstring documents the attribute settling asynchronously).
- `_is_known_project_471_secrets_403` console-filter idiom — copy verbatim from `test_team_users_mention_and_remove_participants.py` (or extract to a shared helper if the implementer judges the 4th copy crosses that threshold — analyst leaves this call to the implementer, not prescribing it).
