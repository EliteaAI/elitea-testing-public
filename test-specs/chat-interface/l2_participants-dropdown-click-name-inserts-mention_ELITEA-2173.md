# Test Case (family): Chat – Team Project – Mention User(s) by Clicking Name(s) in Participants Dropdown

## Metadata
- **TMS IDs**: ELITEA-2173 (mention ONE user), ELITEA-2174 (mention TWO users) —
  same flow, differ only in how many names are clicked before Send. `family_afs: true`.
- **Linked Story**: none (`requirements: []` on both case files)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`,
  DEV backend; Team project "Elitea Testing Team" — `projectId=471`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips
  explicit Keycloak login (dev-token user renders as "Test Bot"/"TB")
- **Analyst**: qa-engineer (agent)
- **Status (both cases)**: **ready-for-automation** — cluster dispatch, ONE live
  Playwright MCP session, EACH case's own steps executed and observed
  independently (§ Cluster execution log below). Zero product defects found on
  the cases' own subject; one case-text CLARIFICATION filed (issue #1558 — see
  § Known Defects Found). Zero new testids needed — the entire flow reuses
  handles ELITEA-2168 already added to both `main` and `automation/testids`.
- **Distinguishing from ELITEA-2168 (merged,
  `test_team_users_mention_and_remove_participants.py`, `origin/automation/base`)
  — NOT a target for `extend-existing`.** ELITEA-2168's own steps 7/12 mention a
  user via the **composer's own typed-`"@"` mention popper**
  (`UserMentionList`/`onSelectUserMention` — a DIFFERENT React component and
  handler than the Users **participants dropdown**). This family's cases click a
  participant's **name row inside the Users dropdown itself**
  (`UserMenu.jsx`/`onSelectParticipant`→`onSelectThisParticipant`→
  `NewChat.jsx`'s `onSelectParticipant(foundParticipant, false)`) — a genuinely
  different code path that ELITEA-2168's test never exercises (it only ever
  clicks a dropdown row's *delete* icon, or the dropdown footer's "All users"
  item — never a row's *name*). Source-confirmed via
  `../EliteaUI/src/pages/NewChat/NewChat.jsx:575-594` and
  `../EliteaUI/src/[fsd]/features/chat/participants/ui/UsersParticipantDropdown/UserMenu.jsx:22-27`
  — this session read the source BEFORE assuming behavior, then confirmed it
  live (interaction-discovery ladder, `.agents/role-overrides.md` step 6).

## Preconditions (shared by both cases)
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User is in a **Team project** ("Elitea Testing Team", `471`) — the "Invite
  Users"/participants-dropdown-mention feature is Team-project-only
  (`PlusChatButton.jsx`'s `!isPrivateProject` guard, same precondition ELITEA-2167/
  2168 already document).
- A conversation exists with the target user(s) already added as **Users**
  participants (case text: "conversation with at least one/two added
  participant(s)"). Automation seeds this itself — see § Test Data.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Team project "Elitea Testing Team", id `471` — `ChatPage.switch_project("471")`.
- Org users searched via the "Add users" modal (client-side substring filter,
  confirmed live and previously by ELITEA-2168): **Hrach Sargsyan** (`"sa"`),
  **Levon Dadayan** (`"ad"`) — same two names ELITEA-2168 already established
  for this environment. ELITEA-2173's case Test Data literally names "user_1" →
  Hrach Sargsyan. ELITEA-2174's case Test Data literally names "user_1, user_2"
  → Hrach Sargsyan, Levon Dadayan (in that order).
- Test messages: case's own literal `'hi'` suffix, composed AFTER the mention
  click(s) (mention-then-type, not typed verbatim — the mention insertion
  happens via a UI click, not typing `@name`).

### generate-per-test (created in test setup, cleaned up in its own teardown)
- **New conversation** — created via `+ Chat` (`ChatPage.click_create_conversation()`/
  `sidebar-create-button` testid), retry-guarded open (`_open_blank_conversation()`
  idiom, ELITEA-2167/2168 precedent — works around the already-tracked #1082
  stale-conversation flake). Add the case's own target user(s) via the "Add
  users" modal, send a setup message so they persist server-side (two-phase
  persistence: `localUsers` queue → flushed to `participants` endpoint only on
  first Send — same mechanism ELITEA-2167/2168 already documented).

## Cluster execution log (both cases run live this session, Playwright MCP)

**ELITEA-2173 (single mention)** — reused an existing Team-project conversation
(`/chat/420`, "Review attached documents", 1 pre-existing user participant,
Hrach Sargsyan):
1. Clicked the Users badge (`chat-participants-badge-button`) → dropdown opened,
   listing "Hrach Sargsyan" and "TB Test Bot" (self, non-selectable per
   `isSelectable = selectable && user.entity_meta?.id !== currentUserId`).
2. Clicked the **"Hrach Sargsyan" menuitem (the name/row itself, not a delete
   icon)** → composer (`chat-message-input`) immediately read
   `"@Hrach Sargsyan"` (confirmed via `browser_snapshot`, then via screenshot —
   `ELITEA-2173-step2-mention-inserted.png`, uploaded to the `evidence` release,
   embedded in issue #1558). The Model Selector simultaneously became disabled
   (`isSendingToUser` flips true — same structural signal ELITEA-2168 documents
   for the composer's own `@`-mention path).
3. **Case's own step 3 ("Verify mention is highlighted/formatted") does NOT
   hold** — the inserted text is plain, unstyled text, visually identical to
   anything else typed in the composer (confirmed via screenshot). Classified
   as **case-text drift** (reverse-masking guard), filed as CLARIFICATION issue
   [#1558](https://github.com/EliteaAI/elitea-testing-public/issues/1558) — see
   § Known Defects Found. Do NOT assert any highlighting/formatting state; assert
   the composer's exact text content instead.
4. Appended `" hi"` via `press_sequentially` (NOT `fill()` — `fill()` REPLACES
   the whole composer value, destroying the mention; confirmed the hard way this
   session, see § Automation Hints) and sent. Result: message list gained
   **exactly one** new entry (`"hi@Hrach Sargsyan"` in the reused-conversation
   repro, `"@Hrach Sargsyan hi"` in the clean re-drive below) — **no** subsequent
   assistant/LLM reply was created (message count went N → N+1, not N → N+2;
   Model Selector re-enabled immediately after send, confirming the to-user path
   completed and reset). Matches the case's "no LLM response generated"
   expectation exactly.
5. **Not independently assertable in this environment**: the case's own
   "user_1 receives notification" expected result describes something visible
   only in the MENTIONED user's own session — this single-account localhost
   setup has no second session to observe it from (same limitation ELITEA-2168
   already documented for its own composer-`@` mention steps). The message-count
   structural check above is the correct single-account proxy.
6. Cleanup: deleted the stray message from the reused conversation
   (`chat-message-delete-button` + confirm) to restore it to its pre-session
   state (this conversation is shared exploration data, not this test's own).

**ELITEA-2174 (two mentions)** — fresh conversation, own setup (blank
conversation created via `sidebar-create-button`, added Hrach Sargsyan + Levon
Dadayan via "Add users", sent a setup message, badge read "3" = owner + 2):
1. Opened the Users dropdown, clicked **"Hrach Sargsyan"** (case's own user_1)
   → composer read `"@Hrach Sargsyan"` (fresh confirmation, same mechanism as
   ELITEA-2173).
2. **Reopened** the Users dropdown (case's own literal step 2 — "Reopen USERS
   dropdown, click on user_2's name") and clicked **"Levon Dadayan"** (user_2) →
   composer read exactly `"@Hrach Sargsyan @Levon Dadayan"` — the second
   mention **appends** to the existing composer content (space-separated, not a
   replace), matching the case's own literal expected result ("@user_2 appended
   in message field") word-for-word. This confirms the mention-insertion
   mechanism composes correctly across repeated dropdown interactions, not just
   once.
3. Appended `" hi"` (via `press_sequentially`, `End` first) and sent. Composer
   read exactly `"@Hrach Sargsyan @Levon Dadayan hi"` before Send — matching the
   case's own literal Test Data / expected message text. Result: message list
   gained **exactly one** new entry with that literal text; **no** subsequent
   assistant/LLM reply followed (Model Selector re-enabled immediately after
   send). Matches the case's "no LLM response generated" expectation exactly.
4. **Not independently assertable in this environment**: "both users notified"
   — same single-account limitation as ELITEA-2173's step 5 above.
5. Cleanup: deleted the entire conversation (dot-menu → Delete → confirm dialog)
   — this was a fresh, this-test-only conversation, zero net pollution left.

**Side-channel check (both cases)**: console monitored throughout both drives.
Only the two already-documented, already-filed noise sources fired — the
project-471 `secrets` 403 (unrelated to this flow, fires on every page load)
and issue #719's `sx`-on-`<svg>` `CheckedIcon` warning (fires on every "Add
users" option selection, ELITEA-2167/2168-documented). Zero NEW console errors
from either case's own mention-click/send flow.

## Test Steps (per-case, parameterized)

| Param | ELITEA-2173 | ELITEA-2174 |
|---|---|---|
| Users to mention (in click order) | Hrach Sargsyan | Hrach Sargsyan, Levon Dadayan |
| Number of dropdown re-opens | 1 (single click) | 2 (reopen between each click — case's own literal step 2) |
| Expected composer text before Send | `"@Hrach Sargsyan hi"` (composed order may vary; content is what's asserted) | `"@Hrach Sargsyan @Levon Dadayan hi"` |
| Expected message-count delta on Send | `+1` (no LLM reply) | `+1` (no LLM reply) |

1. Open the conversation; verify the USERS participants section is visible
   (`is_participants_badge_visible(section="users")` — reuses ELITEA-2168's
   existing method, zero new code).
2. Open the Users dropdown (`open_participants_popover(section="users")` —
   ELITEA-2168 precedent) and click the target user's **name row** (NEW method
   — see § Concrete Handles). **Verify**: composer text becomes
   `"@<DisplayName> "` (exact, via `chat.message_input.text_content()`).
3. **ELITEA-2174 only** — reopen the dropdown (a fresh
   `open_participants_popover()` call) and click the SECOND user's name row.
   **Verify**: composer text is now `"@<User1> @<User2> "` (appended, not
   replaced).
4. Type `'hi'` (via `press_sequentially`, after `End` — **never `fill()`**, it
   replaces the whole value and destroys the mention) and send.
   **Verify**: message count goes `N → N+1` (structural "no LLM response"
   proof, same idiom ELITEA-2168 established — `wait_for_message_count()` +
   a follow-up count read, never a timed "wait and confirm nothing appeared").
5. **Not independently assertable** — recipient notification (single-account
   environment, see § Cluster execution log).

## Expected Results
- Both cases' own numbered steps pass exactly as specced, EXCEPT ELITEA-2173's
  step 3 ("mention is highlighted/formatted") — case-text drift, filed as
  CLARIFICATION #1558, NOT asserted as literally specced.
- Zero product defects found on either case's own subject.
- Recipient-notification halves of both cases' final expected results are
  **not independently assertable** in this single-account environment — same
  scope note ELITEA-2168 already established for its own mention steps.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| ELITEA-2173 precondition: existing conversation, ≥1 participant | — | Setup | reused conversation, badge visible | asserted |
| ELITEA-2173 step 1: open USERS dropdown | dropdown shows participants | step 1-2 | `browser_snapshot` menu listing | asserted |
| ELITEA-2173 step 2: click user_1's name | @user_1 inserted | step 2 | composer text == `"@Hrach Sargsyan "` | asserted |
| ELITEA-2173 step 3: mention highlighted/formatted | highlighted | step 2 (checked, not present) | screenshot — plain text, no styling | **case-text drift — CLARIFICATION #1558, not asserted as specced** |
| ELITEA-2173 step 4: type 'hi', send '@user_1 hi' | sent; user_1 notified; no LLM response | step 4 | message count +1 not +2; notification half not independently assertable | asserted (structural half only) |
| ELITEA-2174 precondition: ≥2 participants | — | Setup | 2 users added + setup message sent, badge "3" | asserted *(seeded per § Test Data)* |
| ELITEA-2174 step 1: open dropdown, click user_1 | @user_1 inserted | step 2 | composer text == `"@Hrach Sargsyan "` | asserted |
| ELITEA-2174 step 2: reopen dropdown, click user_2 | @user_2 appended | step 3 | composer text == `"@Hrach Sargsyan @Levon Dadayan "` | asserted |
| ELITEA-2174 step 3: type 'hi', send '@user_1 @user_2 hi' | sent; both notified; no LLM response | step 4 | composer text before send matches exactly; message count +1 not +2; notification half not independently assertable | asserted (structural + text half) |
| Both cases' Expected Final State / Pass-Fail criteria | "mention works; user(s) notified" | steps 2-4 | as above, EXCEPT the notification half (scope note) and ELITEA-2173's highlighting claim (drift) | asserted, with two named exceptions |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- **Mechanism distinction from ELITEA-2168 (composer's own typed-`"@"` path)** —
  *added: source-read (`NewChat.jsx`/`UserMenu.jsx`) BEFORE live confirmation,
  per the interaction-discovery ladder — this is a genuinely different React
  component/handler chain than ELITEA-2168's `UserMentionList`/
  `onSelectUserMention`, not a duplicate of already-tested behavior.*
- **`fill()` destroys an in-progress mention** — *added: hit live this session
  (a `browser_type` call defaulted to `.fill()`, silently replaced
  `"@Hrach Sargsyan"` with `"hi"`); confirmed the fix (`press_sequentially`
  after `End`) recovers the mention correctly. Not documented anywhere in
  ELITEA-2168's AFS because that case's mention flow uses a different
  insertion mechanism (`UserMentionList.onClick` / keyboard) that happens not
  to trigger this failure mode the same way.*
- **Second mention appends, doesn't replace** — *added: this is ELITEA-2174's
  own core observable, confirmed live (`"@Hrach Sargsyan @Levon Dadayan"` after
  two sequential dropdown-reopen-and-click cycles), not assumed from source.*
- **Console/network side-channel checked throughout both drives** — *added: only
  the two already-known, already-filed noise sources fired; zero new console
  errors from either case's own flow.*

## Cleanup
1. ELITEA-2173: deleted the one stray message added to the REUSED exploration
   conversation (`/chat/420`) — restored to pre-session state (see § Cluster
   execution log).
2. ELITEA-2174: deleted the entire fresh conversation created for this case's
   own setup, via the existing testid-compliant flow
   (`open_conversation_context_menu` → `click_conversation_menu_item("delete")`
   → confirm dialog).
3. No agent/toolkit entities created by either case — only conversation +
   conversation-scoped participant links, cascade-deleted with the conversation.
4. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback
ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`).
Provenance verified via `git grep` on both `origin/main` and
`origin/automation/testids` in the sibling `EliteaUI` clone (fresh
`git fetch origin` this session).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Users participants dropdown trigger (badge) | `chat-participants-badge-button` | on `main` ✓ AND `automation/testids` ✓ | Reused verbatim from ELITEA-2167/2168 — `ChatPage.open_participants_popover(section="users")`. |
| Users dropdown — per-user row (NAME click target, not delete icon) | `chat-participant-row-user_{userId}_` (dynamic, trailing segment empty for Users — ELITEA-2168 correction) | on `main` ✓ AND `automation/testids` ✓ | **Zero new testid needed.** Same `PARTICIPANT_ROW` class-constant template ELITEA-2168 already added; this family's NEW page-object method (below) clicks the row's outer Box directly (no hover needed — the delete icon is `visibility: hidden` by default and does not intercept a plain click at the row's center, confirmed live). |
| Message composer | `chat-message-input` | on `main` ✓ AND `automation/testids` ✓ | Reused verbatim — `ChatPage.message_input`. |
| Send button | `chat-send-button` | on `main` ✓ AND `automation/testids` ✓ | Reused verbatim — `ChatPage.send_button`. |
| New-conversation trigger | `sidebar-create-button` | on `main` ✓ AND `automation/testids` ✓ | Reused verbatim — `ChatPage.click_create_conversation()`. |
| "Add users" modal (search, options, confirm) | `add-users-search-input`, `add-users-option-{id}` (dynamic), `add-users-confirm-button` | on `main` ✓ AND `automation/testids` ✓ | Reused verbatim from ELITEA-2167/2168 setup flow. |

**Zero new testids required for this whole family** — every element the two
cases touch already carries a testid ELITEA-2167/2168 added, present on BOTH
`main` and `automation/testids`.

## Network Behavior
- Clicking a user's name in the dropdown: **no network call** — pure
  client-side composer-state mutation (`chatInput.current.replaceRange(...)`
  equivalent via `mentionUser()`/`onSelectParticipant`, same class of
  client-side-only interaction ELITEA-2168 already documented for chip
  selection/deselection).
- Sending the mention message: same conversation/message endpoints ELITEA-2168
  documented (WebSocket-emitted predict payload carries `is_sending_to_user: true`
  + `user_ids: [...]`) — the reliable assertion is the **message-count
  structural fact**, not a network-response wait.

## Known Defects Found During Exploration
- **[CLARIFICATION, filed this session] Issue
  [#1558](https://github.com/EliteaAI/elitea-testing-public/issues/1558)** —
  ELITEA-2173's case text (step 3) expects the inserted `@mention` to be
  "highlighted/formatted"; the live product inserts plain, unstyled text (same
  mechanism as the composer's own typed-`"@"` mention path, which is also
  plain text — confirmed via ELITEA-2168's AFS/test). Classified as reverse-masking
  case-text drift, NOT a product defect (the product's behavior is internally
  consistent with its own composer-mention mechanism elsewhere). Recommend a
  TMS case-text update dropping or clarifying the highlighting expectation.
  Automate the composer's exact TEXT content instead of any highlighting state.

## Blocked Steps
None. Both cases fully executable against the live product; the one gap
(recipient-side notification) is a scope note (single-account environment),
not a blocker — same limitation ELITEA-2168 already documents for its own
mention steps.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Page object: extend `ChatPage` with ONE new method,
  `mention_user_via_participants_dropdown(user_id: int, timeout: int = 10000)`:
  opens the Users popover (`open_participants_popover(section="users")` —
  reused, unmodified), resolves the row via the EXISTING `PARTICIPANT_ROW`
  class-constant template (`chat-participant-row-user_{user_id}_`, same
  template `open_remove_user_dialog()` already uses), and clicks it directly
  (no hover needed — the row's own `onClick` fires on the whole row, and the
  hover-only delete icon is `visibility:hidden` by default so it never
  intercepts the click). Purely additive — `open_remove_user_dialog()` and
  every other existing `ChatPage` method are untouched.
- **`fill()` vs `press_sequentially()` gotcha (hit live this session,
  distinct from the already-documented `press_sequentially()`-for-MUI-fields
  rule)**: appending `" hi"` to an in-progress mention via `fill()` REPLACES
  the entire composer value (losing the mention text entirely) rather than
  appending. Always `click()` the composer, `press("End")`, then
  `press_sequentially(" hi", delay=50)` — never `fill()` when a mention is
  already present in the composer.
- **"No LLM response" assertion**: same idiom ELITEA-2168 established — assert
  via message-count delta (`+1`, not `+2`), never a timed "wait and confirm
  nothing appeared" check. The assistant placeholder is structurally never
  created for a to-user send (`initializeNewMessages()` in EliteaUI source).
- Reuse `_open_blank_conversation()` (ELITEA-2167/2168's retry-guarded helper)
  for ELITEA-2174's own fresh-conversation setup — same already-tracked #1082
  flake class applies.
- Wait strategy elsewhere: reuse `wait_for_message_count()`/`wait_for_network()`
  (condition-based) — never a fixed sleep, per `.agents/testing.md`.
