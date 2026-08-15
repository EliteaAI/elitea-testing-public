# Test Case: Chat – Search Cleared by Clicking X Icon Restores Default View

## Metadata
- **TMS ID**: ELITEA-2164
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

**Covering spec**: `automation/tests/ui/chat/test_chat_search_and_modules_panel.py` (class
`TestChatSearchAndModulesPanel`). Its existing test opens search, types two queries, and clicks a
result — it never clicks the clear/X icon at all. `ChatPage.search_conversations_clear_button`
(`conversation-search-clear-button`) is a pre-existing `LocatorDescriptor` field, but no test in the
suite currently exercises a click on it. This is a genuinely new scenario, not a duplicate.

## Preconditions
- User is authenticated (`auth_state` fixture — localhost skips real login).
- At least one conversation exists (the default project, id 399/"Private", already has 45+
  pre-existing folders/conversations — sufficient to prove "full list restored").

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A conversation created via `ConversationAPI.create_conversation(name)`
  (`conv_name = f"AutomationXClear{uuid4().hex[:8]}"`) — matched by the search query so the test can
  assert the filtered state existed before clearing.
- Search query: `"un"`-equivalent partial substring drawn from the generated name (same
  case-insensitive-substring pattern as the covering spec — the literal `"un"` is embedded early in
  the generated name, e.g. via the "Unique"-style substring already used by the covering spec's own
  fixture convention: reuse `AutomationUnique{hex}` as the naming convention here too, so the same
  `"un"` query already proven works is reused verbatim rather than inventing a new one).
- Cleanup: `ConversationAPI.delete_conversation(conv_id)` in test teardown.

## Test Steps
1. Navigate to `${ELITEA_URL}/chat`. Click the search icon (`conversation-search-button`), type the
   partial query into `conversation-search-input`.
   - **Verify** (after debounce): the generated conversation's row
     (`chat-conversation-item-{conv_id}`) is visible — filtered results shown.
2. Click the clear/X icon (`conversation-search-clear-button`).
   - **Verify**: `conversation-search-input` is no longer visible/attached (search field closed) —
     the pre-search "Search chats" magnifier button (`conversation-search-button`) is visible again
     in the CHATS header.
3. Verify the left panel returns to the default view with all conversations, folders, and date
   groups.
   - **Verify**: `get_folder_link_count()` (`[data-testid^="chat-folder-item-"]`) count is > 0 (the
     project's pre-existing folders are back); the generated conversation's item
     (`chat-conversation-item-{conv_id}`) is visible again scoped inside its date group
     (`is_conversation_in_group(conv_id, group="today")` — pre-existing method).
4. Verify no search filter is applied (all conversations visible).
   - **Verify**: `get_conversation_item_rows()` (`[data-testid^="chat-conversation-item-"]`) count is
     ≥ 2 — i.e. more than just the generated conversation, proving the list is genuinely unfiltered
     (a filtered-but-not-fully-cleared state would still show only 1).
5. Verify the magnifier icon is visible again in the CHATS header (same handle as step 2's second
   assertion — restated per the case's own step numbering for traceability).

## Expected Results
- Clicking the X icon closes the search input entirely (not just clears its text) and the magnifier
  button reappears.
- The left panel shows the full unfiltered list: folders + date-grouped conversations, including the
  generated conversation back in its date group.
- No search filter remains applied.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in, Chats page with ≥1 conversation | — | `auth_state` fixture + Test Data | fixture + setup | asserted (reused) |
| 1 Click magnifier, type 'un', verify filtered results | Filtered results shown | step 1 | step 1: generated item visible | asserted |
| 2 Click the X (clear/close) icon | Search field closes and disappears | step 2 | step 2: search input gone, magnifier button visible | asserted |
| 3 Verify left panel returns to default view (conversations, folders, date groups) | Full conversation list restored | step 3 | step 3: folder count > 0 + item back in its date group | asserted |
| 4 Verify no search filter is applied | All conversations visible | step 4 | step 4: item-row count ≥ 2 | asserted |
| 5 Verify the magnifier icon is visible again | Magnifier icon visible | step 5 (same handle as step 2) | step 5 | asserted |
| Expected Final State: default view restored | — | steps 2–5 | — | asserted (composite) |

**Axis 2 — Analyst additions**

- Step 4's "count ≥ 2" (rather than merely "count > 0") specifically distinguishes "the filter was
  fully cleared" from "the filter is still narrowly matching" — *added: a count of exactly 1 would
  be ambiguous (could mean the filter is still active and coincidentally matches only the generated
  conversation), so a stronger multi-row assertion is the only way to make "no filter applied" a real
  check given this project's pre-existing data.*
- (No other additions beyond the case.)

## Cleanup
1. Delete the generated conversation via `ConversationAPI.delete_conversation(conv_id)` in test
   teardown.

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance | Notes |
|---|---|---|---|
| Search button | `conversation-search-button` | on-main ✓ | `ChatPage.search_conversations_button` (pre-existing) |
| Search input | `conversation-search-input` | on-main ✓ | `ChatPage.search_conversations_input` (pre-existing) |
| Clear/X button | `conversation-search-clear-button` | on-`automation/testids` only (awaiting human promotion to main) | `ChatPage.search_conversations_clear_button` (pre-existing) — live-confirmed clicking it fully closes the search field, not just clears the text |
| Folder items | `[data-testid^="chat-folder-item-"]` | on-`automation/testids` only (awaiting human promotion to main) | `ChatPage.FOLDER_ITEM_PREFIX` / `get_folder_link_count()` (pre-existing) |
| Conversation items | `[data-testid^="chat-conversation-item-"]` | on-`automation/testids` only (awaiting human promotion to main) | `ChatPage.CONVERSATION_ITEM_PREFIX` / `get_conversation_item_rows()` (pre-existing) |
| Date-group scoped item check | n/a (method, not a raw testid) | — | `ChatPage.is_conversation_in_group(conv_id, group="today")` (pre-existing) — scopes `CONVERSATION_ITEM` inside `CONVERSATION_GROUP_HEADER` |

## Network Behavior
No new network behavior — clicking the clear button unmounts the search UI entirely (confirmed live:
the input element itself is removed from the DOM, not merely emptied), which re-triggers the
existing non-search `folder/prompt_lib` list fetch the covering spec's fixtures already rely on for
the initial page load.

## Known Defects Found During Exploration
None.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest. **Artefact is a NEW test method** in the covering spec file
  (`test_chat_search_and_modules_panel.py`, class `TestChatSearchAndModulesPanel`) — sits alongside
  `test_search_filters_and_modules_panel_toggles`, does not modify it. New method name:
  `test_search_cleared_by_x_icon_restores_default_view`.
- New `@allure.issue(...)` decorator referencing ELITEA-2164's TMS case link.
- **Priority marker**: case priority "medium" → `l3`/`p3` convention. Add `@pytest.mark.p3` on the
  new method (class-level `pytestmark` already applies `ui`/`chat`/`regression`).
- Reuse the `AutomationUnique{hex}` naming convention from the covering spec's own fixture (not a
  new one) — keeps the `"un"` partial-query behavior identical/already-proven, and avoids inventing
  a second unrelated naming scheme in the same file.
