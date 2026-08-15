# Test Case: Chat – Search No Results State

## Metadata
- **TMS ID**: ELITEA-2163
- **Linked Story**: none
- **Priority**: lextend (case frontmatter says `priority: medium`, which maps to `l3` — filename prefix
  replaced per spec-format.md's rule that `extend-existing` outcomes use `lextend_`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`,
  DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN` — no explicit login
  performed)
- **Analyst**: test-automation-engineer (combined analyst+implementer dispatch), batch
  `chat-remaining-w04`
- **Status**: **extend-existing** — case executed live end-to-end against project 399 ("Private", a
  project carrying 45+ pre-existing folders/conversations — the correct precondition for a genuine
  "no results" search, as opposed to a "no conversations exist at all" empty state). One product
  defect found and filed (see § Known Defects). Target: the ELITEA-2162/2464 covering spec — a NEW
  test method in the same file/class, same fixtures.

## Overlap check vs existing automation

**Covering spec**: `automation/tests/ui/chat/test_chat_search_and_modules_panel.py` (class
`TestChatSearchAndModulesPanel`, merged to `automation/base`; covers ELITEA-2162 + ELITEA-2464).
Read in full before this run, along with `automation/pages/chat_page.py`'s search methods
(`open_search_conversations_button()`, `type_conversation_search_query()`,
`get_conversation_item_rows()`, `get_folder_link_count()` — all pre-existing, testid-based).

**What the covering spec already proves**: search opens, partial/exact-match queries filter the
list, clicking a match opens the conversation. It never types a query that matches **nothing** —
the no-results state is entirely unautomated. This is a genuinely new scenario, not a duplicate.

## Preconditions
- User is authenticated (`auth_state` fixture — localhost skips real login).
- Project has existing, unrelated conversations/folders (so the no-results state is distinguishable
  from "this project has never had a conversation" — the default project, id 399/"Private", already
  satisfies this; **do not** use the project-400 empty-sandbox pattern here, it would prove the wrong
  thing).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A conversation created via `ConversationAPI.create_conversation(name)`, same pattern as the
  covering spec (`conv_name = f"AutomationNoResults{uuid4().hex[:8]}"`) — used only to prove the
  search UI is otherwise functional (sanity: it's real conversation state, not an empty project) and
  as an implicit control that the no-results query genuinely matches nothing.
- Query with no results: the case's literal `"xyznotexists"` — safe to hardcode verbatim (a random
  gibberish string is not going to coincidentally match any real conversation name on a shared DEV
  backend, unlike the ELITEA-2162 precedent's concern about the substring `"un"`).
- Cleanup: `ConversationAPI.delete_conversation(conv_id)` in test teardown.

## Test Steps
1. Navigate to `${ELITEA_URL}/chat`. Click the search icon (`conversation-search-button`).
   - **Verify**: `conversation-search-input` becomes visible and focused.
2. Type `"xyznotexists"` into `conversation-search-input`.
   - **Verify** (after the 500ms debounce — wait on the network response, not a fixed sleep):
     `chat-search-no-results-message` (new testid, added this pass) is visible with text
     "No conversations found" / "Try adjusting your search terms".
3. Verify no conversation items are displayed.
   - **Verify**: `get_conversation_item_rows()` (`[data-testid^="chat-conversation-item-"]`) has
     count 0.
4. Verify no error or crash occurs; page remains stable.
   - **Verify**: no console errors fired during the search (page's console-error collector, already
     wired via `conftest.py`'s failure-diagnostics — assert the collected list is empty for this
     window); `conversation-search-input` remains visible/interactable (page did not navigate away
     or blank).
   - **Known-defect regression guard** (`expect.soft()`, non-blocking): `chat-conversations-empty-
     state-message` ("Still no conversations created.", new testid, added this pass) should NOT be
     visible at the same time — it currently IS, incorrectly, on a project that has other
     non-matching data (see § Known Defects, issue #1525). Soft-asserted so this test still goes
     green while the defect stands, and flips to catching a real regression once fixed.

## Expected Results
- Typing a query that matches nothing shows the search-specific "No conversations found" empty
  state (not the "user has never created any conversation" empty state — currently a live defect,
  see below).
- Zero conversation item rows render.
- No console errors, no crash; the search UI stays interactable.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in, on Chats page | — | `auth_state` fixture | fixture | asserted (reused) |
| 1 Navigate to Chats, click magnifier icon | Search input opens | step 1 | step 1: input visible+focused | asserted |
| 2 Type 'xyznotexists' | Left panel shows empty state or 'No conversations found' message | step 2 | step 2: `chat-search-no-results-message` visible | asserted |
| 3 Verify no conversation items are displayed | Results area is empty | step 3 | step 3: item-row count 0 | asserted |
| 4 Verify no error or crash occurs | Page remains stable | step 4 | step 4: console-error list empty + search input still interactable | asserted |
| Expected Final State: no-results state shown correctly | — | steps 2–4 | — | asserted (composite) |

**Axis 2 — Analyst additions**

- Step 4 adds a soft-asserted regression guard for a live defect found this run (§ Known Defects) —
  *added: the case's own pass criteria ("no error/crash") is satisfied even with the defect present,
  but leaving the misleading co-rendered text completely unassessed would let a related regression
  (e.g. the correct message disappearing while the wrong one stays) slip through silently.*
- (No other additions beyond the case.)

## Cleanup
1. Delete the generated conversation via `ConversationAPI.delete_conversation(conv_id)` in test
   teardown (`try`/`finally`, matching the covering spec's own pattern).

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance | Notes |
|---|---|---|---|
| Search button | `conversation-search-button` | on-main ✓ | `ChatPage.search_conversations_button` (pre-existing) |
| Search input | `conversation-search-input` | on-main ✓ | `ChatPage.search_conversations_input` (pre-existing) |
| No-results message | `chat-search-no-results-message` | on-`automation/testids` only (awaiting human promotion to main) | **new this pass** — `EliteaAI/EliteaUI@d5e0ba63`; wraps the outer `Box` around "No conversations found" / "Try adjusting your search terms" in `Conversations.jsx` |
| Empty-state ("Still no conversations created.") message | `chat-conversations-empty-state-message` | on-`automation/testids` only (awaiting human promotion to main) | **new this pass** — `EliteaAI/EliteaUI@d5e0ba63`; `GroupedConversations.jsx` — used only for the soft regression-guard check |
| Conversation item rows | `[data-testid^="chat-conversation-item-"]` | on-`automation/testids` only (awaiting human promotion to main) | `ChatPage.CONVERSATION_ITEM_PREFIX` / `get_conversation_item_rows()` (pre-existing) |

## Network Behavior
Same debounced `GET .../elitea_core/folder/prompt_lib/{projectId}?query=xyznotexists&grouped=true`
mechanism as the covering spec's existing search steps — 500ms debounce, filter is server-driven.
Expected response: empty `conversations`/`folders` arrays (grouped, zero matches).

## Known Defects Found During Exploration
**Isolated, non-blocking** — filed: [EliteaAI/elitea-testing-public#1525](https://github.com/EliteaAI/elitea-testing-public/issues/1525).
When a search query matches nothing on a project that HAS other, non-matching conversations/folders,
`GroupedConversations.jsx`'s "Still no conversations created." empty state renders SIMULTANEOUSLY
with `Conversations.jsx`'s correct "No conversations found" search-empty state — because
`GroupedConversations` receives the search-**filtered** `totalConversationsAmount` (0) rather than
the true unfiltered project total, so its own "literally zero conversations ever" condition
(`visibleGroups.length === 0 && totalConversationsAmount === 0`) fires during a no-results SEARCH
too. Confirmed live via source read + screenshot (project 399, 45+ pre-existing folders). Does not
block the case's own pass criteria (the correct message is also present, no crash) — asserted via
`expect.soft()` in step 4 as a regression guard, not a hard fail.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest. **Artefact is a NEW test method** in the covering spec file
  (`test_chat_search_and_modules_panel.py`, class `TestChatSearchAndModulesPanel`) — sits alongside
  `test_search_filters_and_modules_panel_toggles`, does not modify it. New method name:
  `test_search_no_results_state`.
- New `@allure.issue(...)` decorator referencing ELITEA-2163's TMS case link (onetest markdown path
  under `tests/automated-full-regression-ui/chat/`), alongside the class's existing method's
  decorators pattern.
- **Priority marker**: case priority "medium" → `l3`/`p3` convention (`.agents/memory/qa-engineer/
  priority_marker_drift_afs_vs_pytest_mark.md`). Class-level `pytestmark` already applies
  `ui`/`chat`/`regression` — add `@pytest.mark.p3` on the new method.
- Console-error assertion: reuse whatever collector `conftest.py`/existing tests already use for
  "no console errors" checks (grep neighbouring tests in `tests/ui/chat/` for the pattern before
  inventing a new one — several already assert `page.on("console", ...)`-collected error lists).
- Run the new test method standalone AND alongside the existing method in the same file to confirm
  no cross-test interference (separate conversations, separate fixtures — same isolation pattern
  the covering spec already uses).
