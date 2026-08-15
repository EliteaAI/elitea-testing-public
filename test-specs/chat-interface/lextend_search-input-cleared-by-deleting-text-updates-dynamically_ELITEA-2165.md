# Test Case: Chat – Search Input Cleared by Deleting Text Updates Results Dynamically

## Metadata
- **TMS ID**: ELITEA-2165
- **Linked Story**: none
- **Priority**: lextend (case frontmatter says `priority: medium`, which maps to `l3` — filename prefix
  replaced per spec-format.md's rule that `extend-existing` outcomes use `lextend_`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`,
  DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN` — no explicit login
  performed)
- **Analyst**: test-automation-engineer (combined analyst+implementer dispatch), batch
  `chat-remaining-w04`
- **Status**: **extend-existing** — case executed live end-to-end, zero product defects. Target: the
  ELITEA-2162/2464 covering spec — a NEW test method in the same file/class.

## Overlap check vs existing automation

**Covering spec**: `automation/tests/ui/chat/test_chat_search_and_modules_panel.py`. Its existing
test types a full/exact query directly (via `type_conversation_search_query()`'s triple-click +
`press_sequentially`) — it never types a broad query then narrows it, nor removes characters to
broaden the match set again. The "results grow as you delete characters" direction is entirely
unautomated. This is a genuinely new scenario, not a duplicate.

**Live-confirmed mechanism** (this pass, project 399 — "Private", 45+ pre-existing folders/
conversations): typing a longer, more-specific value narrows results (1 match); deleting back down
to a shorter, broader prefix (e.g. `"AutomationSearchDelete<hex>"` → `"Automat"`) grows the match set
(1 → 5, mixing conversations AND folders whose names also match) via the same debounced
`folder/prompt_lib?query=...` mechanism already documented for the covering spec — each keystroke
(add or remove) is a real, independent React `onChange` event, so deletion updates the filter exactly
like typing does. Clearing the field to empty restores the exact same unfiltered default view as
before search was opened (not a distinct "empty search" state — `isSearchMode` becomes `false` when
the trimmed query is empty, per `Conversations.jsx`'s `debouncedSearchQuery.trim()` check).

## Preconditions
- User is authenticated (`auth_state` fixture — localhost skips real login).
- Multiple conversations exist whose names share a common broader prefix but differ in a more
  specific suffix (so narrowing/broadening the query produces an observably different match count at
  each stage) — the default project (399/"Private") already has this via its 3 pre-existing
  `AutomationRenameTest` conversations sharing the `Automat`-prefix; the test seeds its own two
  conversations sharing a distinguishable prefix rather than depending on that pre-existing data
  (test isolation — pre-existing data could be cleaned up by an unrelated process).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Two conversations created via `ConversationAPI.create_conversation(name)` sharing a common prefix
  but differing after it:
  - `conv_narrow_name = f"AutomationDynUnique{uuid4().hex[:8]}"` — the FULL query typed first (matches
    only itself).
  - `conv_broad_name = f"AutomationDynOther{uuid4().hex[:8]}"` — does NOT match the narrow query, but
    DOES match the shared prefix `"AutomationDyn"`.
- Query sequence: type the full `conv_narrow_name` first (1 match), then delete characters back down
  to the shared prefix `"AutomationDyn"` (grows to 2 matches — both seeded conversations), then clear
  entirely (restores the full default view).
- Cleanup: `ConversationAPI.delete_conversation()` for both, in test teardown.

## Test Steps
1. Click the magnifier icon (`conversation-search-button`), type the full `conv_narrow_name` into
   `conversation-search-input`.
   - **Verify** (after debounce): `get_conversation_item_rows()` count is exactly 1, and it is
     `conv_narrow_name`'s item (`chat-conversation-item-{conv_narrow_id}`).
2. Delete characters from the end of the input, in one committed step, down to the shared prefix
   `"AutomationDyn"` (via select-all + retype the shorter value — a controlled-input React `onChange`
   fires identically whether the shorter value arrives via repeated Backspace or a single replace,
   per the live-confirmed mechanism above; both are genuine keystroke-driven updates, not a
   programmatic bypass).
   - **Verify** (after debounce): `get_conversation_item_rows()` count is exactly 2, and BOTH
     `chat-conversation-item-{conv_narrow_id}` and `chat-conversation-item-{conv_broad_id}` are
     visible — results updated dynamically, showing MORE matches after deletion than before.
3. Delete all remaining characters (select-all + Backspace) so the input is empty.
   - **Verify**: `chat.search_conversations_input` is still visible/focused (search mode stays open,
     per the covering spec's own Step 2 finding that clicking the icon opens the field and it does
     NOT auto-close); the full default view is restored — `get_folder_link_count()` > 0 AND both
     seeded conversations' items are visible, each correctly scoped inside its date group
     (`is_conversation_in_group(conv_id, group="today")`); no error/crash (console-error collector
     empty for this window).

## Expected Results
- Deleting characters from the search query dynamically re-filters the list via the same debounced
  server-driven mechanism as typing — each committed value change (broader or narrower) produces an
  independent, correct result set.
- Clearing the query to empty restores the full unfiltered default view (not a distinct empty-search
  state) with no error.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in, on Chats page | — | `auth_state` fixture | fixture | asserted (reused) |
| 1 Click magnifier, type 'unique', verify filtered results shown | Filtered results shown | step 1 | step 1: exactly 1 row, correct item | asserted *(case's literal query `"unique"` replaced with the test's own generated full name — same reasoning as the covering ELITEA-2162 AFS: a hardcoded literal isn't safe test-isolation on a shared backend)* |
| 2 Delete characters one by one from the input | Results update dynamically showing more matches with each deletion | step 2 | step 2: row count grows 1→2, both items present | asserted |
| 3 Delete all characters | All conversations shown or appropriate empty search state | step 3 | step 3: full default view restored (folders + both items, correctly grouped), no error | asserted — live-confirmed behavior is "all conversations shown" (not a distinct empty-search state), per source read of `Conversations.jsx`'s `isSearchMode = !!debouncedSearchQuery.trim()` |
| Expected Final State: dynamic update on each deletion | — | steps 1–3 | — | asserted (composite) |

**Axis 2 — Analyst additions**

- Step 2 uses a single select-all-and-retype action rather than N individual `Backspace` keystrokes
  to reach the intermediate broader value — *added/declared: live-confirmed both mechanisms produce
  the identical debounced-filter re-fetch (any committed `onChange` value triggers the same
  `useDebounceValue` → `folder/prompt_lib?query=...` path); N repeated single-key tool calls would
  be functionally equivalent but far more turns for the same evidence, so the docstring names this
  choice explicitly per the implementer's technique latitude (Phase 2 — this is a **how**, not a
  **what**, decision; the case's own expected result, "results update dynamically", is unchanged).*
- Step 3 explicitly asserts the console-error collector is empty and both conversations render
  correctly grouped — *added: the case's "appropriate empty search state" language is ambiguous
  about whether the FULL list or a distinct empty-search placeholder is correct; live behavior is
  confirmed to be the former, and grouping-correctness plus no-error strengthens the check beyond
  "some conversations appeared."*

## Cleanup
1. Delete both generated conversations via `ConversationAPI.delete_conversation()` in test teardown.

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance | Notes |
|---|---|---|---|
| Search button | `conversation-search-button` | on-main ✓ | `ChatPage.search_conversations_button` (pre-existing) |
| Search input | `conversation-search-input` | on-main ✓ | `ChatPage.search_conversations_input` (pre-existing); `type_conversation_search_query()` already implements the select-all(triple-click)+`press_sequentially` pattern needed for step 2's "replace with shorter value" action |
| Conversation items / row count | `[data-testid^="chat-conversation-item-"]` | on-`automation/testids` only (awaiting human promotion to main) | `ChatPage.CONVERSATION_ITEM_PREFIX` / `get_conversation_item_rows()`, `get_conversation_item()` (pre-existing) |
| Folder items | `[data-testid^="chat-folder-item-"]` | on-`automation/testids` only (awaiting human promotion to main) | `ChatPage.FOLDER_ITEM_PREFIX` / `get_folder_link_count()` (pre-existing) |
| Date-group scoped item check | n/a (method) | — | `ChatPage.is_conversation_in_group(conv_id, group="today")` (pre-existing) |

## Network Behavior
Same debounced `GET .../elitea_core/folder/prompt_lib/{projectId}?query=<value>&grouped=true`
mechanism as the covering spec for the narrow→broad transition (step 2) — 500ms debounce.
**Implementer correction**: the final clear-to-empty step (step 3) does **NOT** reliably fire a
NEW network response — live-confirmed via a failing first implementation attempt that waited on
`page.expect_response()` and timed out. The empty/no-query state is the SAME query-client cache key
the page loaded with, so React Query (or whatever caching layer backs `useFoldersListQuery`) can
serve it from cache with zero network round-trip. The correct wait is on the resulting UI state
(the polling `is_conversation_in_group()` / `get_folder_link_count()` checks), not a network event —
this section's earlier claim that this step "fires the debounced empty-query fetch" was NOT actually
verified against the Network tab during analysis and was wrong.

## Known Defects Found During Exploration
None.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest. **Artefact is a NEW test method** in the covering spec file
  (`test_chat_search_and_modules_panel.py`, class `TestChatSearchAndModulesPanel`). New method name:
  `test_search_input_cleared_by_deleting_text_updates_dynamically`.
- New `@allure.issue(...)` decorator referencing ELITEA-2165's TMS case link.
- **Priority marker**: case priority "medium" → `l3`/`p3` convention. Add `@pytest.mark.p3` on the
  new method.
- `type_conversation_search_query()` already does exactly the "click(click_count=3) + press_
  sequentially + wait for the query-tagged response" sequence needed for step 2's narrow→broad
  transition (a non-empty replacement value). It is NOT reusable verbatim for step 3's clear-to-empty
  case — `press_sequentially("")` types zero characters, so no `onChange` fires and the wrapping
  `expect_response()` would hang waiting for a request that never triggers. Working clear sequence:
  click the input, `page.keyboard.press("Meta+a")` (macOS Chromium — plain `Control+a` does NOT
  select-all in a Chromium text field, per `.claude/rules/mui-patterns.md`'s documented gotcha,
  live-reconfirmed this session), then `page.keyboard.press("Backspace")`. **Do NOT wrap this in
  `page.expect_response()`** — implementation-round-1 confirmed this specific transition (back to the
  page's initial no-query cache key) can be served entirely from cache with no new network round-trip,
  so the wait times out. Wait on the resulting UI state instead — the polling `is_conversation_in_
  group()` calls already used in step 3's other assertions are sufficient; run them BEFORE any
  non-polling `.count()` read (e.g. `get_folder_link_count()`) so the DOM has actually settled first.
