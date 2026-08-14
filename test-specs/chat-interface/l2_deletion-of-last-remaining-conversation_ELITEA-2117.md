# Test Case: Chat – Deletion of the Last Remaining Conversation in a Project

## Metadata
- **TMS ID**: ELITEA-2117
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend); project **"UI Testing" (id 400)** — REQUIRED for this case specifically (see § Automation Hints — the empty-panel/welcome-state observable can only be honestly reached by genuinely emptying a project's conversation list, and 400 is a dedicated sandbox confirmed live to normally hold zero conversations, unlike the shared Team/Private projects other analyses reuse)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-14
- **Status**: ready-for-automation

No existing AFS or merged test exercises deleting the LAST remaining
conversation. `test_conversation_deletion_flow.py` (ELITEA-2114) explicitly
seeds a SECOND conversation (`conv_sibling`) specifically so the delete does
**NOT** hit this code path (its own AFS says so directly — "without a second
conversation, deleting the only/active conversation falls back to an
empty/dummy state instead of exercising next-conversation selection"). This
case's empty/welcome-state observable is the exact branch that AFS
deliberately avoided — genuinely new coverage. **A real, isolated product
defect was found and is documented below (§ Known Defects) — the affected
step is specced with `expect.soft()` per the no-masking decision tree; every
other step is a hard assertion.**

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- Test seeds project 400 down to EXACTLY one conversation (see § Test Data) —
  the case's "exactly one conversation remains... no other conversations or
  folders" precondition is satisfied by using a project confirmed empty
  beforehand, not by destructively clearing a shared project.

## Test Data

### reuse-existing
- `${TEST_USER}`.
- **Project 400 ("UI Testing")** — confirmed live (API `list_conversations()`,
  `total: 0`) to be genuinely empty before this test's own seeding. This
  project must stay empty between runs for this test to remain valid/isolated
  — see § Automation Hints for why no other project in this environment can
  honestly host this case without destroying shared fixture data.

### generate-per-test
- **`conv_last`** — the ONLY conversation, via
  `conversation_api.create_conversation(name)` on project 400. Consumed by
  the test's own delete action — nothing to clean up afterward (project
  returns to its normal empty state).

## Test Steps

**Setup (not a numbered case step)**
0. Create `conv_last` via the API on project 400. Navigate to
   `${BASE_URL}/chat` (project 400) and confirm it auto-opens/is selectable as
   the sole conversation.

1. Navigate to Chats and verify exactly one conversation exists in the left
   panel; no others.
   - **Verify**: sidebar conversation list shows exactly 1 item
     (`[data-testid="chat-conversation-item-{conv_last_id}"]`), no other
     `chat-conversation-item-*` present, no `chat-folder-item-*` present.
2. Click on the conversation to open it.
   - **Verify**: `page.url` contains `/chat/{conv_last_id}`; message input
     area (`message_input`) visible and active/editable;
     `chat-conversation-item-{conv_last_id}` carries `data-active="true"`.
3. Hover, click three-dot icon, click Delete.
   - **Verify**: `[data-testid="delete-confirm-dialog"]` becomes visible.
4. Verify modal body reads the live body text (case's literal wording is
   stale — see the shared drift already documented for ELITEA-2114/#695, not
   re-filed here).
   - **Verify**: `[data-testid="delete-confirm-message"]`.text ==
     `f"Are you sure to delete the {conv_last name} chat? It can't be
     restored."`.
5. Click the Delete button.
   - **Verify**: dialog closes without error;
     `DELETE /api/v2/elitea_core/conversation/prompt_lib/400/{conv_last_id}`
     resolves `204`.
6. Verify the left panel conversation list is empty — no conversations under
   any date group.
   - **Verify**: `chat-conversation-item-*` count == 0 in the sidebar; no
     date-group heading (`chat-conversation-group-header-*`) present.
     Live-confirmed: the sidebar renders no group headings at all once the
     project has zero conversations (distinct from the reload-only
     `"Still no conversations created."` sidebar-empty-state text, which only
     appears after a full page reload — see § Known Defects).
7. Verify the main panel transitions to the new-chat welcome/empty state with
   Elitea logo and greeting.
   - **Verify**: `new_conversation_greeting`
     (`[data-testid="chat-new-conversation-greeting"]`) becomes visible,
     containing the Elitea logo image and `"Hello, {user}! What can I do for
     you today?"` text — live-confirmed this is the SAME component the
     blank-unsent `+Chat` state uses (ELITEA-2167's existing handle), reached
     here via `onDeleteConversation`'s `setActiveConversation(dummyConversation)`
     fallback (`useDeleteConversation.js`) rather than a real navigation.
8. Verify the message input area is visible and active.
   - **Verify**: `message_input` visible and editable (no `disabled`
     attribute) in the welcome state.
9. Verify no error banners or toast messages are present.
   - **Verify**: no `[data-testid="toast-message"]` visible; no new console
     errors beyond the pre-existing unrelated `secrets/secrets/default` 403
     noise (same exclusion filter as ELITEA-2114's test).
10. Verify the page URL no longer references the deleted conversation.
    - **`expect.soft()`, `# Known defect: #1523`** — live-confirmed
      this DOES NOT happen within the same SPA session: `page.url` remains
      `/chat/{conv_last_id}?name={conv_last name}` (the deleted conversation's
      own id + name query param) even though the visible UI has fully
      transitioned to the empty/welcome state. See § Known Defects — this is
      an isolated, non-blocking product defect (all other steps' observables
      are unaffected; a hard reload at the stale URL correctly shows a
      "Conversation not found" dialog and resets, proving the underlying data
      state IS consistent — only the client-side URL/route sync is stale).
11. Verify the + Chat button remains available.
    - **Verify**: `create_conversation_button`
      (`[data-testid="sidebar-create-button"]`) visible and enabled in the
      welcome state.

## Expected Results
- Deleting the sole remaining conversation empties the sidebar and transitions
  the main panel to the exact same welcome/greeting component the blank
  `+Chat` state uses, with the message input and `+Chat` button both
  available — all live-confirmed.
- **Isolated defect**: the browser URL does not update/clear to reflect the
  now-deleted conversation within the same SPA session (only a reload fixes
  it) — see § Known Defects.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: exactly 1 conversation, no others/folders | — | Setup + step 1 | project-400 seeding + count checks | asserted |
| 1 Verify exactly one conversation, no others | one listed | step 1 | item count == 1, no folders | asserted |
| 2 Click conversation → messages displayed, highlighted | opens, active | step 2 | URL + `data-active` | asserted |
| 3 Hover, 3-dot, Delete → modal appears | dialog appears | step 3 | `delete-confirm-dialog` visible | asserted |
| 4 Verify modal body text correct | body correct | step 4 | `delete-confirm-message` text | asserted *(live text differs from case's literal wording — same shared drift as ELITEA-2114/#695, not re-filed)* |
| 5 Click Delete → modal closes without error | closes cleanly | step 5 | dialog hidden + `DELETE` 204 | asserted |
| 6 Left panel empty, no date groups | panel empty | step 6 | item count 0, no group headers | asserted |
| 7 Main panel welcome state with logo+greeting | welcome shown | step 7 | `chat-new-conversation-greeting` visible | asserted |
| 8 Message input visible and active | input ready | step 8 | `message_input` visible+editable | asserted |
| 9 No error banners/toasts | no errors | step 9 | no toast + console check | asserted |
| 10 URL no longer references deleted conversation | URL updated | step 10 | `expect.soft()` — **FAILS live** | asserted *(soft — isolated known defect, see § Known Defects)* |
| 11 + Chat button remains available | button active | step 11 | `sidebar-create-button` visible+enabled | asserted |
| Expected Final State: "panel empty, welcome shown, new conversation can be started" | — | steps 6–8, 11 | covered by rows above | asserted |
| Pass/Fail: "left panel empties; welcome shown; +Chat available" | — | steps 6,7,11 | covered by rows above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- Step 2 asserts `data-active="true"` on the opened conversation — *added:
  the case's own step 2 says "conversation highlighted", this is the concrete
  testid+state handle for that (ELITEA-2114's existing pattern).*
- Step 5 asserts the underlying `DELETE` resolves 204 — *added: same
  "prove it's real" discipline as every other delete AFS in this cluster.*
- Step 9 explicitly excludes the pre-existing unrelated `secrets` 403 console
  noise — *added: same exclusion already established by ELITEA-2114's test,
  reused here for consistency.*
- Step 10's soft-assert + linked defect — *added per the project's no-masking
  decision tree (`.agents/testing.md` § Merge gate, sanctioned-RED /
  isolated-defect handling): the URL-staleness observable is real, isolated,
  deterministic, and doesn't block any other step, so it's specced as a soft
  assertion with a filed ticket rather than dropped or silently weakened.*

## Known Defects Found During Exploration

- **[MINOR] URL does not clear/update after deleting the LAST remaining
  conversation (dummy-state branch only).** Live-confirmed, deterministic
  (reproduced 2/2 attempts across separate seeded conversations, ids 111 and
  113 on project 400): after clicking Delete on the sole remaining
  conversation, the visible UI correctly transitions to the empty
  sidebar/welcome-state (§ steps 6–8), but `page.url` / the browser address
  bar remains unchanged at `/chat/{deleted_id}?name={deleted_name}` — the
  SAME url shown before the delete, still literally naming the now-deleted
  conversation. Two confirming console errors also fire ~1.5s later (delayed
  background refetch attempts against the dead id):
  `GET .../elitea_core/conversation/prompt_lib/400/{id}?messages_limit=10&sort_order=desc`
  → `400`, and `GET .../elitea_core/select_conversation/prompt_lib/400/{id}` →
  `400`. A subsequent hard reload at that stale URL correctly resolves to a
  `"Conversation not found"` dialog and a genuinely clean `/chat/{id}` (no
  query param) — proving the underlying app/server state IS consistent; only
  the client-side URL/router sync is stale.

  **Root cause (read from source,
  `EliteaUI/src/hooks/chat/useDeleteConversation.js`):**
  `onDeleteConversation`'s `findNextConversation()` return value gates the
  branch: when a next conversation exists,
  `onSelectConversation(nextConversation)` fires (which DOES update the
  route/URL — confirmed working correctly by ELITEA-2114's existing test).
  When NO next conversation exists (this case's exact scenario),
  the code takes the `else` branch —
  `setActiveConversation(dummyConversation)` — which updates Redux/component
  state (hence the correct VISUAL welcome-state transition) but never calls
  any router/`navigate()` function. The URL is simply never told the
  conversation is gone.

  Filed: **EliteaAI/elitea-testing-public#1523** (dedup checked — no existing
  open issue matched). Isolated (steps 1–9, 11 all pass cleanly; only step 10
  is affected) — spec per step 10 above: `expect.soft()` +
  `# Known defect: #1523`.

## Blocked Steps
None — every case step was reachable and observed live, including the
precondition (via the dedicated empty project 400, see § Automation Hints).

## Automation Hints
- Framework: Playwright + pytest. Extend `ChatPage`
  (`automation/pages/chat_page.py`) — reuse `new_conversation_greeting`
  (ELITEA-2167), `create_conversation_button`, `message_input`,
  `confirm_delete_conversation()`, `open_conversation_context_menu()`,
  `click_conversation_menu_item()` (all existing).
- **Why project 400, and why this is NOT a substitution.** This case's own
  precondition ("exactly one conversation remains... no other conversations
  or folders") is a genuine PROJECT-LEVEL empty-state requirement — the
  `findNextConversation()` mechanism in `useDeleteConversation.js` searches
  ALL of the project's ungrouped conversations (not folder-scoped), so
  reaching the true `dummyConversation`/welcome-state branch requires a
  project with truly zero OTHER conversations at delete time. The shared
  Team project (471, id used by most other chat analyses — "Review attached
  documents", id 420) and the default Private project (399) both already
  carry pre-existing conversations that other analyses/tests reuse and
  restore — deliberately emptying either to reach this case's precondition
  would be destructive to shared fixture data, not a reasonable test-isolation
  move. Project 400 ("UI Testing") is a genuinely separate, normally-empty
  sandbox project (confirmed live via `ConversationAPI(project_id="400")
  .list_conversations()` → `total: 0`, both before AND after this session's
  exploration, once temp data was cleaned up) — using it satisfies the case's
  literal precondition HONESTLY (a real empty project, not a fabricated
  empty-list response) rather than requiring any mock/stub of the
  conversations-list endpoint. This is transit-appropriate project selection,
  not a fidelity substitution — the observable (welcome state after last
  delete) is still produced entirely by the real system against real,
  API-created data.
- **Isolation discipline for CI-worthiness**: this test's own setup
  (`create_conversation` on project 400) MUST run immediately before its
  delete action, and nothing else should ever seed persistent data into
  project 400 — if a future case needs multiple conversations there
  temporarily, it must clean ALL of them up before finishing, or this test
  will start seeing a false "not the last conversation" state. Consider a
  session-scoped guard/assertion at test start (`list_conversations().total
  == 0` before seeding) that fails loudly rather than silently running against
  a polluted project.
- Bearer-token `ConversationAPI(browser_cookies=[], project_id="400")` works
  fine for seeding (confirmed live) — same pattern as ELITEA-2115/2116's
  AFS.
