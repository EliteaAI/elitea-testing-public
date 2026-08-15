# Test Case: Chat – Search input opens, filters results dynamically, conversation is interactable

## Metadata
- **TMS ID**: ELITEA-2463
- **Linked Story**: [EliteaAI/elitea-testing-public#971](https://github.com/EliteaAI/elitea-testing-public/issues/971) (originating tracking issue)
- **Priority**: lextend (case frontmatter says `priority: high`, which maps to `l2` — filename prefix
  replaced per spec-format.md's rule that `extend-existing` outcomes use `lextend_`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`,
  DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN` — no explicit login
  performed)
- **Analyst**: test-automation-engineer (combined analyst+implementer dispatch), batch
  `chat-remaining-w04`
- **Status**: **extend-existing** — case executed live end-to-end, zero product defects. Core flow
  (steps 1–5, 8, 10–12) is a near-verbatim breakdown of the already-merged ELITEA-2162 spec's own
  steps 1–5; only steps 6, 7, and 9's "under its correct date group" clause are a genuine gap. Target:
  the covering test method itself (additive `expect()` lines inserted at the existing Step 3/Step 4
  points — NOT a new test method, per the AFS Gap-assertions insertion-point rule).

## Overlap check vs existing automation

**Covering spec**: `automation/tests/ui/chat/test_chat_search_and_modules_panel.py::
TestChatSearchAndModulesPanel::test_search_filters_and_modules_panel_toggles` (merged to
`automation/base`, covers ELITEA-2162 + ELITEA-2464). Its own AFS:
`test-specs/chat-interface/l2_chat-search-and-modules-panel_ELITEA-2162.md` — read in full before
this run.

**What the covering spec already proves** (ELITEA-2463 steps it fully satisfies as-is):
- Step 1 (magnifier icon visible) — covering spec's step 1.
- Step 2 (click magnifier) / Step 3 (input focused + X icon appears) — covering spec's step 2.
- Step 4 (type partial query) — covering spec's step 3 (types `"un"`).
- Step 5 (filtered conversations shown) — covering spec's step 3 (generated item visible).
- Step 8 (type exact full name) — covering spec's step 4.
- Step 10 (click matching conversation, opens with full history) — covering spec's step 5.
- Step 11 (URL updates) — covering spec's step 5 (`wait_for_conversation_url`).
- Step 12 (search input remains visible while conversation open) — covering spec's step 5.

**What ELITEA-2463 demands that the covering spec does NOT yet assert** (this AFS's Gap
assertions, § below):
1. Step 6 — "results are grouped by pinned and date sections": the covering spec's step 3/4 only
   assert a single generated conversation's visibility/count; it never proves the search results
   panel actually separates pinned conversations from date-grouped ones (as opposed to, say, a flat
   unified list). **Live-confirmed this pass**: pinning a conversation before searching renders it
   OUTSIDE the date-group container entirely (via `PinnedConversations` — same DOM position as the
   non-search pinned-section rendering), while non-pinned matches stay correctly scoped inside their
   `CONVERSATION_GROUP_HEADER` (e.g. "Today"). Confirmed via `useQueryFoldersList.hooks.js`'s
   `searchQuery` param feeding the SAME backend call that produces `pinned`/`folders`/date-grouped
   conversations together — search filtering applies to all three tiers uniformly, not just the
   flat conversation list.
2. Step 7 — "non-matching conversations are not displayed": the covering spec's step 4 asserts
   `to_have_count(1)` for the EXACT-match query, which already implicitly proves non-matching rows
   are absent for that one query — but never for the PARTIAL-match query (step 3), where a
   non-matching sibling could in principle still render alongside the real match without the
   existing assertions catching it (they only assert the target item's presence, never a control's
   absence).
3. Step 9 — "shown under its correct date group": the covering spec's step 4 asserts the matching
   item is visible (page-wide, unscoped `get_conversation_item()`), not that it renders specifically
   INSIDE the correct date-group container (as opposed to, hypothetically, outside any group or in
   the wrong one). The pre-existing `is_conversation_in_group()` method exists precisely for this
   distinction and is unused by the covering spec's search steps.

## Preconditions
- User is authenticated (`auth_state` fixture — localhost skips real login).
- Reuses the covering spec's existing precondition (a generated conversation via
  `ConversationAPI.create_conversation`) — no separate setup, since this AFS extends the SAME test
  method.

## Test Data
No additional test data beyond what the covering spec's `conv_name`/`conv_id` already provides, PLUS
one additional seeded conversation for the Gap assertions:
- `sibling_conv_name = f"AutomationOther{uuid4().hex[:8]}"` — deliberately does NOT contain the
  substring `"un"` (verified: "Automation" and "Other" contain no `"un"` substring), used as the
  non-matching control for Gap 2 (step 7).
- The SAME `sibling_conv_name` conversation is pinned (via `open_conversation_context_menu()` +
  `click_conversation_menu_item("pin")`, both pre-existing) before the search steps run, used as the
  pinned-grouping control for Gap 1 (step 6).
- Cleanup: `ConversationAPI.delete_conversation(sibling_conv_id)` in the covering spec's existing
  `finally` block (additive — alongside the existing conversation's cleanup, not replacing it;
  deleting a pinned conversation needs no separate unpin step).

## Test Steps (delta over the covering spec — inserted at the corresponding point in the SAME
`test_search_filters_and_modules_panel_toggles` method)

1. **New — in Setup, after the existing conversation is created**: create `sibling_conv_name` and pin
   it via the context menu.
   - **Verify**: `is_conversation_pinned(sibling_conv_id)` is `True` immediately after pinning
     (pre-existing method, `data-pinned="true"` attribute check).
2. **Extends existing Step 3** (types partial query `"un"`, additive `expect()` lines only — the
   existing assertion for the generated conversation's visibility is untouched):
   - **New**: `chat.get_conversation_item(sibling_conv_id)` is NOT visible (`sibling_conv_name`
     doesn't match `"un"`) — satisfies Gap 2 (case step 7) for the partial-query case.
   - **New**: `chat.is_conversation_pinned(sibling_conv_id)` is unaffected by the fact its row isn't
     currently matched — no assertion needed here, this is just documenting that the pin state is
     orthogonal to search matching (not a new check).
3. **New — after existing Step 3, still inside the same allure.step or a new one immediately
   following it**: type the query `"AutomationOther"` (an exact-ish prefix that DOES match
   `sibling_conv_name` but not the generated `AutomationUnique...` conversation) — satisfies Gap 1
   (case step 6, pinned grouping).
   - **Verify**: `chat.is_conversation_pinned(sibling_conv_id)` is still `True`; the sibling's row
     (`chat-conversation-item-{sibling_conv_id}`) is visible; the generated conversation's row is
     NOT visible (query doesn't match it) — proves search results correctly narrow to the pinned
     match alone, and the pinned item is retrievable via the page-wide `CONVERSATION_ITEM` testid
     regardless of its (pinned, not date-grouped) DOM position.
   - Re-type the original partial query `"un"` afterward (`type_conversation_search_query("un", ...)`
     again — same pre-existing method) to restore state for the existing Step 4 that follows.
4. **Extends existing Step 4** (types the exact full-name query, additive `expect()` lines only — the
   existing `to_have_count(1)` assertion is untouched, it already proves Gap 2 for the exact-match
   case):
   - **New**: replace the existing plain `get_conversation_item(conv_id)` visibility check's
     REDUNDANT information with an ADDITIONAL, stronger assertion —
     `chat.is_conversation_in_group(conv_id, group="today")` is `True` — satisfies Gap 3 (case step
     9, "under its correct date group"). This is an ADDITIVE new assertion line; the existing
     `expect(chat.get_conversation_item(conv_id)).to_be_visible(...)` line stays byte-identical.

## Expected Results
- Search results correctly separate pinned matches (rendered via the pinned-section mechanism,
  outside any date group) from date-grouped matches (rendered inside their correct
  `CONVERSATION_GROUP_HEADER`) — both filtered by the same query.
- A partial query's results exclude conversations that don't match the substring (not just "the
  target conversation is present" but "an explicit non-match is absent").
- The exact-match result renders inside its correct date group, not merely "somewhere on the page."

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | covering spec `auth_state` | fixture | asserted (reused) |
| 1 Navigate, verify magnifier icon | Target page loads | covering spec step 1 | covering spec | asserted (reused) |
| 2 Click magnifier icon | Control responds | covering spec step 2 | covering spec | asserted (reused) |
| 3 Verify input focused, X icon appears | Condition holds | covering spec step 2 | covering spec | asserted (reused) |
| 4 Type partial query 'un' | Field accepts input | covering spec step 3 | covering spec | asserted (reused) |
| 5 Verify filtered conversations shown | Condition holds | covering spec step 3 | covering spec | asserted (reused) |
| 6 Verify results grouped by pinned and date sections | Condition holds | new step 1 (pin setup) + new step 3 | new step 3: pinned item present via query match while non-pinned generated conv is absent, `is_conversation_pinned` stays True | asserted |
| 7 Verify non-matching conversations are not displayed | Condition holds | new step 2 | new step 2: sibling (non-matching) item NOT visible during partial-query step | asserted |
| 8 Type exact full name | Field accepts input | covering spec step 4 | covering spec | asserted (reused) |
| 9 Verify only the matching conversation is shown under its correct date group | Condition holds | covering spec step 4 (count=1) + new step 4 (`is_conversation_in_group`) | both | asserted |
| 10 Click matching conversation, opens with full history | Control responds | covering spec step 5 | covering spec | asserted (reused) |
| 11 Verify URL updates | Condition holds | covering spec step 5 | covering spec | asserted (reused) |
| 12 Verify search input remains visible while conversation open | Condition holds | covering spec step 5 | covering spec | asserted (reused) |
| Expected Final State: search input stays visible while conversation open | — | covering spec step 5 | covering spec | asserted (reused) |

**Axis 2 — Analyst additions**

- New step 3 re-types the original `"un"` query after the pinned-grouping check to restore state for
  the existing Step 4 that follows — *added: purely a test-mechanics necessity (the existing Step 4
  assumes the query is still `"un"`'s partial-match state before it types the exact full name); not
  a case requirement, but required to keep the additive insertion from breaking the untouched
  original flow.*
- (No other additions beyond the case.)

## Cleanup
1. Delete the `sibling_conv_name` conversation via `ConversationAPI.delete_conversation()`, additive
   in the covering spec's existing `finally` block (alongside its current single-conversation
   cleanup).

## Concrete Handles (discovered during exploration)

All testid-only, all pre-existing `LocatorDescriptor` fields or methods on `ChatPage` — no new
testids required for this case (unlike ELITEA-2163/2164/2165, which needed two new testids).

| Element | Testid | Provenance | Notes |
|---|---|---|---|
| Search button/input | `conversation-search-button` / `conversation-search-input` | on-main ✓ | pre-existing, reused |
| Conversation item (page-wide) | `[data-testid="chat-conversation-item-{}"]` | on-`automation/testids` only (awaiting human promotion to main) | `ChatPage.CONVERSATION_ITEM` / `get_conversation_item()` (pre-existing) — SAME testid renders regardless of pinned/date-grouped/folder position |
| Pin state check | n/a (method) | — | `ChatPage.is_conversation_pinned(conversation_id)` (pre-existing) — `data-pinned` attribute, state-via-data-attribute pattern |
| Pin action | `chat-conversation-menu-pin-menuitem` | on-`automation/testids` only (awaiting human promotion to main) | `ChatPage.open_conversation_context_menu()` + `click_conversation_menu_item("pin")` (pre-existing, id-scoped `CONVERSATION_MENU_ITEM` template) |
| Date-group scoped item check | n/a (method) | — | `ChatPage.is_conversation_in_group(conversation_id, group="today")` (pre-existing) — scopes `CONVERSATION_ITEM` inside `CONVERSATION_GROUP_HEADER` |

## Network Behavior
Same debounced `GET .../elitea_core/folder/prompt_lib/{projectId}?query=<value>&grouped=true`
mechanism as the covering spec — confirmed (source read, `useQueryFoldersList.hooks.js`) that
`pinned`/`folders`/date-grouped conversations all come from this ONE call, with the SAME `query`
param filtering all three tiers together — this is what makes "grouped by pinned and date sections"
during search a real, testable backend-driven behavior rather than a client-side rendering quirk.

## Known Defects Found During Exploration
None (for this case specifically — see the sibling ELITEA-2163 AFS for a defect found while
exploring the broader search surface, unrelated to this case's own steps).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest. **Artefact is an edit to the covering spec**
  (`test_chat_search_and_modules_panel.py`), not a new file — insert the new steps at the
  corresponding points inside the existing `test_search_filters_and_modules_panel_toggles` method
  (same pattern as the ELITEA-2464 extension already in this file: numbered sub-steps like "Step 3b
  (ELITEA-2463 extension)", plus a third `@allure.issue(...)` decorator referencing ELITEA-2463's TMS
  case link, alongside the existing ELITEA-2162/ELITEA-2464 ones).
- **Priority marker**: case priority "high" → `l2`/`p1`, same as the existing method's
  `@pytest.mark.p1` (no change needed — already correct).
- Run the FULL extended test method (all original + new steps) to prove the additive-only contract:
  original assertions (search/open/modules-panel-toggles) must still pass unchanged.
