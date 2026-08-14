# Test Case: Chat – Search Icon Filters Conversations, Opens Result, Modules Panel Toggles Work

## Metadata
- **TMS ID**: ELITEA-2162
- **Linked Story**: none
- **Priority**: l2 (high — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN` — no explicit login performed)
- **Analyst**: qa-engineer (analyst slot), batch `approved-next50`
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (`auth_state` fixture — localhost skips real login).
- At least one conversation exists whose name contains the test's chosen search
  substrings (see § Test Data — created fresh per test, not a fixed seeded record).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A conversation created via `ConversationAPI.create_conversation(name)` (same
  pattern as the `conversation_id` fixture in `fixtures/data_fixtures.py`, but
  **not** that fixture directly — the generic `autotest_<testname>` prefix
  doesn't guarantee the specific substrings this case's search steps need).
  Recommended name: `f"AutomationUnique{uuid4().hex[:8]}"` — e.g.
  `AutomationUniquea1b2c3d4`. This single conversation supplies both queries:
  - **Partial query** (Step 2): `"un"` — the case's literal value. `"Unique"`
    (case-insensitive) is embedded early in the generated name so it matches;
    do **not** assert an exact result count for this step (the substring `un`
    is common — a shared DEV backend may have unrelated matches). Assert only
    that the generated conversation's row (`chat-conversation-item-{id}`) is
    present.
  - **Exact/full-name query** (Step 3): the conversation's **full generated
    name** (not the literal string `"unique"` from the case — a hardcoded
    literal isn't safe test-isolation on a shared backend where another run's
    leftover data could coincidentally match). Assert **exactly one** result
    and that it is the created conversation.
  - This mirrors the case's own Test Data intent (a partial substring vs. an
    exact full name) while keeping the test self-isolating. Live-confirmed:
    the backend filter (`GET /elitea_core/folder/prompt_lib/{projectId}
    ?query=<value>&grouped=true`) is a case-insensitive substring match on
    conversation name, so both forms behave identically to the case's
    literal `"un"` / `"unique"` example.
- Cleanup: `ConversationAPI.delete_conversation(conv_id)` in teardown (even on
  failure) — same as the existing `conversation_id` fixture pattern.

## Test Steps
1. Navigate to `${ELITEA_URL}/chat`.
   - **Verify**: `conversation-search-button` (magnifier icon) is visible in
     the CHATS panel header.
2. Click the search icon (`conversation-search-button`).
   - **Verify**: `conversation-search-input` becomes visible and focused; a
     clear/X icon is visible next to it (see § Concrete Handles — needs a
     testid). Do **not** assert the folder/date-group list disappears at
     this point — it doesn't (see Coverage Map row 1, `clarification`,
     issue #1114).
3. Type the partial query (`"un"`) into `conversation-search-input`.
   - **Verify** (after the 500 ms debounce — wait on the network response,
     not a fixed sleep, per § Network Behavior): `[data-testid="chat-conversation-item-{conv_id}"]`
     for the generated conversation is visible.
4. Clear and type the exact/full-name query (the generated conversation's
   full name) into `conversation-search-input`.
   - **Verify**: exactly one `[data-testid^="chat-conversation-item-"]` row is
     present, and it is `chat-conversation-item-{conv_id}`.
5. Click the matching conversation row.
   - **Verify**: `page.url` matches `**/chat/{conv_id}*`; the conversation's
     message history area loads (main panel is no longer the empty-state
     greeting); `conversation-search-input` is still visible in the left
     panel.
6. Click the `+` icon (`plus-menu-button`), then hover the "Modules" menuitem
   (`internal-tools-menuitem`) — **hover, not click, reveals the submenu**
   (`PlusChatButton.jsx` wires it via `onMouseEnter`, same mechanism as the
   existing `agents_menuitem` in the page object; case text says "click" but
   the live mechanism is hover-to-reveal, consistent with the rest of this
   plus-menu).
   - **Verify**: 7 toggle switches (`role="switch"`) are visible with
     accessible names, in this order: "Image creation", "Data Analysis",
     "Agents & Pipeline Builder", "Planner", "Python Sandbox", "Swarm Mode",
     "Smart Tool Selection" — live-confirmed exact match to the case's list.
7. Toggle "Image creation" on, then off (two separate clicks, each on the
   switch identified by `image_generation`'s testid — see § Concrete
   Handles).
   - **Verify** after each click: the switch's checked state flips
     (`True`→`False`→...); `toast-message` becomes visible with text
     `"Modules configuration updated"` (**lowercase "updated"** — the case
     text says "Updated"; see Coverage Map row 6, `clarification`, issue
     #1115).
8. Repeat Step 7 for at least one more module (live-confirmed with "Data
   Analysis"/`data_analysis`) — toggle on, verify state + toast. (Full
   coverage of all 7 is a reasonable implementer choice; live-confirmed 2 of
   7 behave identically and share one code path — `onInternalToolsConfigChange`
   — so per-toggle behavior is not expected to diverge by module.)
9. Close the Modules panel by clicking elsewhere in the main chat area (an
   empty area of the conversation panel — **`Escape` does NOT close it**,
   live-confirmed: switch count stayed at 7 after `Escape`; only an
   outside-click closed the popover, taking it to 0 switches).
   - **Verify**: `role="switch"` locator count is 0 (panel closed); the main
     conversation view (message history / composer) is unobstructed.

## Expected Results
- Search UI is reachable from the magnifier icon and both partial and exact
  substring queries filter the conversation list correctly (case-insensitive
  substring match against conversation name, live-confirmed via the
  `folder/prompt_lib` endpoint's `query` param).
- Clicking a search result opens that conversation (URL updates,
  `conversation-search-input` remains visible).
- The Modules panel opens from `+` → Modules (hover), shows all 7 toggles,
  each toggle persists via `useConversationEditMutation` (PUT on the
  conversation's `meta.internal_tools`) and confirms with a
  `Modules configuration updated` toast.
- Closing the panel (outside click) restores the plain conversation view.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: conversation with a unique name exists | — | Test Data (generate-per-test) | setup | asserted |
| 1 Click magnifier icon | left panel → search input; X icon appears; **folder list replaced by search results area** | step 2 | step 2: input+X visible | clarification — folder list is *not* replaced until a query is typed (debounced), not on click alone. Filed: EliteaAI/elitea-testing-public#1114. AFS step 2 asserts the live behavior instead. |
| 2 Type 'un' partial query | filtered list shows matches, non-matching hidden | step 3 | step 3: `chat-conversation-item-{id}` visible | asserted |
| 3 Type exact 'unique' | only matching conversation(s) shown | step 4 | step 4: exactly 1 matching row | asserted |
| 4 Click matching conversation | opens in main panel; URL updates; search input remains visible | step 5 | step 5: URL + input visibility assertions | asserted |
| 5 Click + icon, click Modules | Modules panel opens w/ 7 named toggles | step 6 | step 6: switch count + accessible names | asserted *(mechanism is hover, not click — noted in step, not a case defect)* |
| 6 Toggle Image creation on/off | toggle state changes; "Modules configuration Updated" message | step 7 | step 7: `is_checked()` + toast text | clarification — actual toast text is "Modules configuration **updated**" (lowercase). Filed: EliteaAI/elitea-testing-public#1115. AFS step 7 asserts the live text. |
| 7 Toggle Data Analysis + repeat for other modules | all toggles work; success message each time | step 8 | step 8: same assertions on `data_analysis` | asserted *(sampled: Image creation + Data Analysis, both drive the identical `onInternalToolsConfigChange` code path — see step 8 note)* |
| 8 Close Modules panel | main conversation view restored | step 9 | step 9: switch count 0 | asserted *(closing mechanism is outside-click, not `Escape` — `Escape` was live-confirmed NOT to close it)* |
| Expected Final State: search + open + Modules panel functional | — | steps 3–9 | — | asserted (composite of the above) |

**Axis 2 — Analyst additions**

- Step 3 asserts on the concrete network request
  (`GET .../folder/prompt_lib/{projectId}?query=un&grouped=true`) firing
  after the debounce, not just the DOM — *added: confirms the filtering is
  server-driven (not a stale client-side cache), matching what I observed
  live (no client-side filter logic exists in `Conversations.jsx` beyond
  passing `searchQuery` up to the fetch hook).*
- Step 9 asserts `Escape` does **not** close the panel (a negative check) —
  *added: this is the natural first thing an implementer would try, and it
  silently does nothing (no error, no close) — worth guarding so a future
  regression to "Escape now closes it" or a broken outside-click handler
  doesn't slip through unnoticed either way.*
- (No other additions beyond the case.)

## Cleanup
1. Delete the generated conversation via `ConversationAPI.delete_conversation(conv_id)`
   in test teardown (`try`/`finally` or a pytest fixture, per the existing
   `conversation_id` fixture pattern in `fixtures/data_fixtures.py`).

## Concrete Handles (discovered during exploration)

Testid-only per `.agents/role-overrides.md` / `.agents/testing.md` § Locator
policy. Every row's PROVENANCE was verified with a fresh `git fetch origin`
in `../EliteaUI` at analysis time (2026-08-03).

| Element | Testid | Provenance | Notes |
|---|---|---|---|
| Search icon button | `conversation-search-button` | on-main ✓ | `src/components/ConversationSearchButton.jsx:30` |
| Search input field | `conversation-search-input` | on-main ✓ | `Conversations.jsx:685` (rendered on the `<input>` itself) |
| Search clear/X icon button | **testid needed: `conversation-search-clear-button`** | needs-adding | `Conversations.jsx` ~L686-692 — an `IconButton onClick={handleSearchClear}` wrapping `<CloseIcon>`, currently has **no testid and no aria-label** (MUI doesn't auto-inject one here since the icon isn't itself an `IconButton`'s only child in a way that gives it a name — verify at add-time). Add via `add-data-testid`. |
| Conversation search-result row (dynamic) | `chat-conversation-item-{conversation.id}` | **on-`automation/testids` only** (awaiting human promotion to `main`) | `ConversationItem.jsx:349` — template: `f'[data-testid="chat-conversation-item-{conv_id}"]'` (class-level constant per the dynamic-testid convention in `.agents/testing.md`) |
| Plus (`+`) menu button | `plus-menu-button` | on-main ✓ | `PlusChatButton.jsx:341`. Existing page-object field `ChatPage.plus_menu_button` already uses this testid — reuse directly. |
| "Modules" menuitem | `internal-tools-menuitem` | on-main ✓ | `PlusChatButton.jsx:379` — `data-testid={key === SUBMENU_KEYS.INTERNAL_TOOLS ? 'internal-tools-menuitem' : undefined}` (same-element conditional pair, shape (a) per canon ruling #277 — only the used branch is named — compliant). **Existing page-object field `ChatPage.internal_tools_menuitem` currently uses a RAW locator (`'[role="menuitem"]:has-text("Modules")'`) instead of this testid** — pre-existing tech debt (not introduced by this case). Recommend switching it to `LocatorDescriptor(testid="internal-tools-menuitem")` when this AFS's methods touch it, since new call sites must be testid-only. |
| Module toggle switch (×7, dynamic by tool key) | **testid needed: `modules-toggle-{tool_key}`** | needs-adding | `PlusChatButton.jsx` ~L260-283, `Switch.BaseSwitch` rows with **zero** testid today (identified only via MUI `role="switch"` + `label={tool.title}`, i.e. accessible name). Stable keys confirmed from `src/[fsd]/shared/lib/constants/internalTools.constants.js`: `image_generation` ("Image creation"), `data_analysis` ("Data Analysis"), `internal_mcp` ("Agents & Pipeline Builder"), `planner` ("Planner"), `pyodide` ("Python Sandbox"), `swarm` ("Swarm Mode"), `lazy_tools_mode` ("Smart Tool Selection"). Class-level template constant, per the dynamic-testid convention: `MODULES_TOGGLE_SWITCH = '[data-testid="modules-toggle-{}"]'`, formatted with the tool key (e.g. `.format("image_generation")`) — **not** the display title. |
| Success toast | `toast-message` | on-main ✓ | `src/components/Toast.jsx:66` — app-wide generic component, already used by `ArtifactsPage.success_toast_message` / `SkillsListPage.import_success_toast_message`. Text asserted: `"Modules configuration updated"` (exact, lowercase "u"). |

## Network Behavior
- `GET /api/v2/elitea_core/folder/prompt_lib/{projectId}?sort_by=updated_at&sort_order=desc&query=<value>&grouped=true`
  — fires ~500 ms after the search input stops changing (debounced via
  `useDebounceValue`); response drives both the date-grouped conversations
  and folders shown in search mode. Wait on this response (`page.expect_response`
  matching `/folder/prompt_lib/.*query=/`) rather than a fixed sleep before
  asserting the filtered list.
- `PUT` on the conversation-edit endpoint (`useConversationEditMutation`,
  same underlying route as `ConversationAPI.rename_conversation` —
  `/elitea_core/conversation/prompt_lib/{projectId}/{id}`) — fires when a
  module toggle is clicked, carrying `meta.internal_tools` (array of tool
  keys). `toastSuccess('Modules configuration updated')` fires only after
  this resolves without error — wait on the response before asserting the
  toast, not a fixed sleep.

## Known Defects Found During Exploration
None found — both discrepancies from the case text are case-authoring
accuracy issues (correct product behavior, case text imprecise), filed as
CLARIFICATIONS, not defects:
- EliteaAI/elitea-testing-public#1114 — Step 1: folder-list replacement
  timing.
- EliteaAI/elitea-testing-public#1115 — Steps 6/7: toast text casing.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`); page object
  `automation/pages/chat_page.py` (extend, don't duplicate — it already has
  `open_internal_tools_menu()`, `enable_image_creation()` /
  `disable_image_creation()` / `is_image_creation_enabled()`, and
  `open_search_conversations_button()`; none of the existing methods cover
  the *filtering* assertions or the *close-panel* / *toast* assertions this
  case needs, so new methods are additive, not a rewrite).
- **Priority marker**: `@pytest.mark.p1` (this case's "high" priority maps
  to `l2` in the AFS filename and `p1` in pytest — confirmed against 8/9
  sibling `l2 (high)` cases in this suite using `p1`, per
  `.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`).
  Also mark `@pytest.mark.chat` and `@pytest.mark.regression`.
- Don't reuse the generic `conversation_id` fixture as-is for this case —
  it names conversations `autotest_<testname>`, which won't reliably contain
  the `"un"` partial-match substring. Create the conversation inline (or a
  new fixture) per § Test Data.
- Sibling TMS cases **ELITEA-2463** ("Chat – Search input opens, filters
  results dynamically, conversation is interactable" — tracking card
  EliteaAI/elitea-testing-public#971) and **ELITEA-2464** ("Chat – Modules
  panel accessible from + icon…" — tracking card
  EliteaAI/elitea-testing-public#972) are both still `draft`/unautomated and
  are, respectively, a more granular breakdown of this case's steps 1–4 and
  5–9. **Flagging for the orchestrator**: once this AFS's implementation
  merges, ELITEA-2463 and ELITEA-2464 should very likely classify as
  `already-covered` (or `extend-existing` for any granular sub-assertion
  this AFS doesn't already make, e.g. 2463's explicit "grouped by pinned and
  date sections" check) against the resulting spec — worth sequencing their
  analysis AFTER this case lands to avoid duplicate implementation.
