# Test Case: Chat – Unpin a Pinned Conversation

## Metadata
- **TMS ID**: ELITEA-2150
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`, matching the
  ELITEA-2149 sibling's medium→l3/p2 mapping)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, Private project — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — `auth_state`/`VITE_DEV_TOKEN` skips explicit login on localhost
- **Analyst**: test-automation-engineer (combined analyst+implementer), chat-remaining-w08
- **Status**: extend-existing
- **surface_key**: `chat-conversation-context-menu`

## Extension target
`automation/tests/ui/chat/test_pin_conversation.py`
(`TestPinConversationViaPinOnTop::test_pin_conversation_via_pin_on_top`, ELITEA-2149, merged
`origin/automation/base`, commit `e06c3bd6`). **Purely additive** — one new test method
(`test_unpin_conversation_via_context_menu`, new class `TestUnpinConversationViaContextMenu`) in
the same file. ELITEA-2150 is the inverse flow of ELITEA-2149 (unpin instead of pin) and needs its
own precondition — a conversation that is ALREADY pinned — so it cannot be a named-insertion-point
extension of ELITEA-2149's existing test body; it is a new, sibling test method sharing the file's
imports, timeout constants, and `_is_known_secrets_403` console filter.

## Live exploration (this session)

Live-driven via Playwright MCP against `localhost:5173` (2 conversations seeded via
`ConversationAPI.create_conversation()`, cleaned up via `delete_conversation()` after). Confirmed
every case step end-to-end:

- **Setup — pin via the UI, as a precondition, not a case step.** `conv_target` is created via API
  (lands in "Today", unpinned, matching ELITEA-2149's own setup pattern), then pinned via the SAME
  UI flow ELITEA-2149's own test already proves correct (`open_conversation_context_menu()` →
  `click_conversation_menu_item("pin")`). This is transit, not substitution: the case's own
  observable (unpinning) is still produced by clicking a real "Unpin" menu item and reading real
  DOM state afterward; pinning is only how the required PRECONDITION ("at least one pinned
  conversation exists") is reached, and it reuses an already-covered, already-merged action rather
  than inventing a raw API pin call. Live-confirmed after pin: `data-pinned="true"`,
  `chat-pin-icon` count 1.
- **Live gotcha, already handled by the existing page-object method, no new workaround needed**: a
  PINNED conversation's `DraggableConversationItem`-style wrapper (same `aria-disabled="true"`
  ancestor pattern the `_surface.md` digest already documents for PINNED FOLDERS,
  `isDragDisabled={isPinned}`) renders around a pinned conversation's row too — confirmed live via
  `browser_evaluate` DOM-chain inspection (a plain click on the scoped 3-dot menu button times out
  with "element is not enabled" because Playwright's actionability walk sees the disabled ancestor,
  even though the button's own `.disabled` is `false`). `ChatPage.open_conversation_context_menu()`
  ALREADY calls `menu_button.click(force=True)` (pre-existing, ELITEA-2114) — this bypasses the
  issue correctly for real pytest runs, confirmed by reading the method; no page-object change
  needed. Worth recording here since this is the first case to actually exercise a PINNED
  conversation's own context menu (ELITEA-2149 only ever opens the menu BEFORE pinning).
- Reopening the (now-pinned) conversation's context menu: the SAME `chat-conversation-menu-pin-
  menuitem` testid resolves, and its label text reads **"Unpin"** (live-confirmed via
  `textContent()`) — confirming the state-via-label-text design ELITEA-2149's AFS already
  documented from the OTHER side (pre-pin "Pin on top").
- Clicking "Unpin": live-confirmed via `browser_evaluate` DOM read immediately after —
  `data-pinned` flips `"true"` → `"false"`, `chat-pin-icon` count flips `1` → `0`, the conversation
  item testid still resolves to exactly 1 element (re-rendered back into the date-grouped list, not
  duplicated), and it is now found scoped inside `chat-conversation-group-header-today`'s container
  (`is_conversation_in_group(conv_target_id, "today") == True`). 0 unexpected console errors
  across the whole flow (only startup noise: React DevTools notice, an ASCII-art version banner,
  and Vite's `stream` externalization warning — none conversation/pin-related).
- No new testids, no new page-object methods — every handle this case needs already exists from
  ELITEA-2149/ELITEA-2114's own work.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- At least one pinned conversation exists — satisfied by API-seeding `conv_target` then pinning it
  via the UI in Setup (see § Live exploration; not a case step).

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`conv_target`** — the conversation to unpin. Create via `conversation_api.create_conversation(name)`
  (lands in "Today"), then pin via `chat.open_conversation_context_menu()` +
  `chat.click_conversation_menu_item("pin")` (UI setup action, not a case step).
- **`conv_sibling`** — a second, unpinned conversation created the same way, kept unpinned
  throughout. Mirrors ELITEA-2149's own `conv_sibling` reasoning: guarantees the "Today" date-group
  heading stays visible and non-empty regardless of ambient shared-project state, and gives Step 3
  a real "still correctly in Today" comparison point.

## Test Steps
1. Navigate to `${BASE_URL}/chat`. Hover the pinned `conv_target`'s sidebar item, click its 3-dot
   menu, click **Unpin** (`chat-conversation-menu-pin-menuitem` — same testid as ELITEA-2149's
   "Pin on top", state carried via label text).
   - **Verify**: label reads **"Unpin"** before the click (live-confirmed).
2. Verify the conversation is removed from the pinned section.
   - **Verify**: `chat.is_conversation_pinned(conv_target_id)` is `False` (`data-pinned` flips
     `"true"` → `"false"`); `chat-conversation-item-{conv_target_id}` still resolves exactly 1
     element (re-rendered back into the date-grouped list, not duplicated — same
     "one testid template renders in multiple possible locations" pattern ELITEA-2149's AFS
     documents for the opposite transition).
3. Verify the pin icon is no longer displayed.
   - **Verify**: `chat.get_pin_icon(conv_target_id)` count flips `1` → `0` (1->0 transition,
     captured before/after the click — mirrors ELITEA-2149's own 0->1 transition check for the
     same reason: catches a regression where the icon renders unconditionally rather than gated on
     `isPinned`).
4. Verify the conversation reappears in the appropriate date group.
   - **Verify**: `chat.is_conversation_in_group(conv_target_id, "today")` is `True` (scoped
     presence inside the "Today" date-group container — the conversation was created fresh, so
     "Today" is the deterministically correct group per ELITEA-2149's own precedent).
     `conv_sibling` (never pinned) is also asserted still in "Today", proving the group container
     itself wasn't disturbed by the unpin.

## Expected Results
- Unpinning removes the conversation from the pinned section.
- The pin icon no longer renders next to the conversation's name.
- The conversation reappears in its date group ("Today", for a freshly-created conversation).
- No unexpected console errors across the flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: ≥1 pinned conversation exists | — | Setup | API-seeded `conv_target`, pinned via UI setup action | asserted |
| 1 Navigate to Chats, hover pinned conversation, 3-dot icon, click 'Unpin' | Conversation removed from pinned section | AFS steps 1–2 | step 2: `data-pinned` flips to `"false"` + single-element re-render | asserted |
| 2 Verify the pin icon is no longer displayed | Pin icon gone | AFS step 3 | step 3: `chat-pin-icon` count flips `1`→`0` | asserted |
| 3 Verify the conversation reappears in the appropriate date group | Conversation in correct date group | AFS step 4 | step 4: scoped presence inside `chat-conversation-group-header-today` | asserted |
| Expected Final State (prose): "Conversation unpinned and returned to date group" | — | steps 2–4 | covered by the rows above | asserted |
| Pass/Fail: "Conversation remains pinned or disappears" (Fail condition) | — | steps 2, 4 | negative-pinned-state (step 2) + positive-in-group (step 4) together | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- Step 1 asserts the menu item's label text reads "Unpin" before the click — *added: confirms the
  state-carrying label design (ELITEA-2149's own "Pin on top" pre-pin check, mirrored here for the
  post-pin state) is in its expected pre-unpin state, not just that the click succeeds.*
- Step 3 confirms the pin icon via a 1→0 transition (before/after), not just a post-unpin absence
  check — *added, mirrors ELITEA-2149's own 0→1 transition discipline: catches a scenario where the
  icon renders unconditionally (a false pass on an always-absent-after-unpin icon regardless of
  actual gating) vs. correctly gated on `isPinned` flipping false.*
- Step 4 also asserts `conv_sibling` (never pinned) stays in "Today" — *added: proves the date-group
  container itself wasn't disturbed by the unpin action, not merely that `conv_target` happens to
  reappear somewhere; same sibling-comparison discipline ELITEA-2149's own step 4 uses in the
  opposite direction (proving the group didn't just vanish along with the pinned item).*
- Console/network side-channel checked after every interaction — *added: standard side-channel
  discipline, confirmed 0 relevant console errors across the full pin-then-unpin flow this session.*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)` — unpinning first is not
   required (ELITEA-2149's AFS already live-verified deleting a PINNED conversation works
   identically to an unpinned one; this case additionally leaves it unpinned by the time cleanup
   runs, which is strictly the simpler case).
2. Delete `conv_sibling` via `conversation_api.delete_conversation(id)`.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)
No new handles. Reuses, all pre-existing (ELITEA-2114/2149):
- `ChatPage.open_conversation_context_menu(conversation_id)`
- `ChatPage.click_conversation_menu_item("pin")` (same key toggles pin ↔ unpin; the testid and the
  page-object key are identical in both directions — only the rendered label text changes)
- `ChatPage.get_conversation_menu_item("pin")` (for the pre-click label-text check)
- `ChatPage.is_conversation_pinned(conversation_id)`
- `ChatPage.get_pin_icon(conversation_id)`
- `ChatPage.is_conversation_in_group(conversation_id, group)`
- `ChatPage.get_conversation_item(conversation_id)`

## Network Behavior
- `DELETE /pin/prompt_lib/{project_id}/conversation/{conversation_id}` → unpin (source-confirmed,
  `src/api/social.js`'s `togglePinItem` mutation: `method: shouldPin ? 'POST' : 'DELETE'` — same
  endpoint ELITEA-2149's AFS documents for the `POST` pin direction) — not independently
  network-asserted in this AFS's steps, same rationale ELITEA-2149's AFS already gives: the
  UI-state assertions (steps 2–4) are sufficient, and `usePinConversation.hooks.js`'s optimistic
  update already reverts UI state on a failed request, so a UI-state check that stays green also
  indirectly proves the request didn't fail.
- Pre-existing, unrelated: project 399's `secrets/secrets/default` `403` on every page load —
  excluded from "no new console errors" checks, same as every sibling AFS in this suite.

## Known Defects Found During Exploration
None. All 3 case steps executed live end-to-end and matched expected results exactly (0 relevant
console errors). The pinned-conversation `aria-disabled` ancestor gotcha documented in
§ Live exploration is NOT a defect — it's a pre-existing DOM pattern already correctly handled by
`open_conversation_context_menu()`'s existing `force=True` click.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`. No new page-object work — every
  method and locator this case needs already exists from ELITEA-2149/ELITEA-2114.
- New test method + new class in `test_pin_conversation.py`, alongside (not replacing)
  `TestPinConversationViaPinOnTop::test_pin_conversation_via_pin_on_top` — verify additive-only via
  `git diff <base> -- automation/tests/ui/chat/test_pin_conversation.py | grep -E '^-[^-]'` (should
  be empty; the entire diff is new lines).
- Priority marker: `@pytest.mark.p2` (medium → l3/p2 mapping, same as ELITEA-2149).
- Reuse the file's existing `_is_known_secrets_403` console filter and `UI_ELEMENT_TIMEOUT` /
  `NAVIGATION_TIMEOUT` module constants — no new constants needed.
