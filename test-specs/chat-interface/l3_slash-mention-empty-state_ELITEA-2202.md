# Test Case: Chat – Slash Commands – Typing '/' With No Toolkits/MCPs Shows Empty Dropdown

## Metadata
- **TMS ID**: ELITEA-2202
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (analyst slot), batch `approved-next50`, cluster with ELITEA-2203/2204
- **Status**: **ready-for-automation** — executed live end-to-end via a `sync_playwright`-driven pytest scratch test (no Playwright MCP tools were surfaced this dispatch). Feature behaves exactly as the case describes. The dropdown's list/title/empty-message elements carry **zero testids today** — `add-data-testid` work is required (see § Concrete Handles); the toplevel trigger (`/` typed into the already-testid'd `chat-message-input`) needs no new handle.
- **Cluster note**: analysed together with ELITEA-2203 (adds a toolkit+MCP, same dropdown) and ELITEA-2204 (toolkit→tool selection) in one live session — three **separate AFS files** because the cases differ in STEPS (empty-state vs. participant-filtering vs. deep tool-selection), not just data, per `test-case-analysis` § Execute "merge only when cases differ solely in data." All three share the same underlying component (`SlashSuggestionList.jsx`) and the same new testids proposed below — the implementer should add them once and all three specs consume them.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation with **no toolkit or MCP participants** — a fresh conversation from the `conversation_id` fixture satisfies this (no participants are ever added by that fixture).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- No toolkit/MCP test data needed for this case — the point is the ABSENCE of participants.

## Test Steps

1. Navigate to the conversation (`ChatPage.navigate_to_chat(conversation_id=...)`).
   - **Verify**: no toolkit/MCP participants exist — `is_participants_badge_visible(section="toolkits")` and `is_participants_badge_visible(section="mcp")` both return `False` (pre-existing `PARTICIPANTS_BADGE` template, `chat_page.py:493` / `4059-4083` — confirmed live: the badge container is entirely absent from the DOM when a section's count is 0, per its own docstring; do not assert on a "0" text label).
2. Click the message input and type `/` (`chat.message_input.click()` then `press_sequentially("/")`).
   - **Verify**: a dropdown appears with heading text **"Mention Toolkit or MCP"** (rendered uppercase via CSS `text-transform`; the DOM text node itself is title-case — confirmed live: `<span class="MuiTypography-subtitle">Mention Toolkit or MCP</span>`, screenshot shows it rendered as "MENTION TOOLKIT OR MCP"). Case text's exact-caps framing is a CSS artifact, not literal DOM text — assert the title-case string.
3. Verify the dropdown's body text — confirmed live: exactly **"No matching results"** (not "No results" or similar; confirmed live, exact string, `NewParticipantList.jsx`'s empty-state `Typography`).
4. Click elsewhere in the page (outside the dropdown) to close it.
   - **Verify**: the dropdown closes — confirmed live via a body click at a neutral coordinate; `NewParticipantList` is wrapped in a `ClickAwayListener` (`onClickAway={onClose}` — closes on ANY outside click, this is the component's own designed behavior, not something case-specific). **Do not use `Escape`** to close it — a sibling surface with the identical `Popper`+`ClickAwayListener` shape (the plus-menu's "Modules" panel, `_surface.md` § Modules panel) is live-confirmed NOT to close on `Escape`; this case's own dropdown was not independently isolated for `Escape` specifically, but the architecture is identical, so use the confirmed-reliable outside-click close, not `Escape`.

## Expected Results
- Typing `/` with zero toolkit/MCP participants shows a dropdown titled "Mention Toolkit or MCP" containing only "No matching results".
- No toolkits/MCPs are listed (there are none to list).
- Clicking outside the dropdown closes it.
- No console errors during the sequence (confirmed live — none observed, `page.on("console")` listener attached for the whole exploration session).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create a new conversation with no toolkits or MCPs added | Conversation open; PARTICIPANTS has no TOOLKITS or MCPS | AFS step 1 | `is_participants_badge_visible(section="toolkits"/"mcp") == False` | asserted |
| 2 Click into the message input field and type '/' | Dropdown appears with heading 'MENTION TOOLKIT OR MCP' | AFS step 2 | dropdown container `.text_content()` contains "Mention Toolkit or MCP" | asserted |
| 3 Verify dropdown shows 'No matching results' or empty list | No toolkits or MCPs listed | AFS step 3 | dropdown container `.text_content()` contains "No matching results"; zero item-testid matches inside it | asserted |
| 4 Press elsewhere to close dropdown | Dropdown closes | AFS step 4 | dropdown-container testid `to_have_count(0)` after outside click (absence assertion) | asserted |

### Axis 2 — Analyst additions
- Step 1 asserts the PARTICIPANTS-panel precondition explicitly via the pre-existing badge-visibility helper (reused, not new) rather than trusting the fixture silently — *added: makes the case's own stated precondition ("PARTICIPANTS has no TOOLKITS or MCPS") a real assertion instead of an assumption.*
- No console errors during the whole `/`-type → verify → close sequence — *added: standard side-channel check per the skill's "check the side channels even when the UI looks fine" rule; none observed.*

## Cleanup
- Conversation deleted by the `conversation_id` fixture's teardown (`ConversationAPI.delete_conversation`).

## Concrete Handles (discovered during exploration)

`SlashSuggestionList.jsx` (`EliteaUI/src/[fsd]/features/chat/ui/slash-suggestion-list/`) renders `NewParticipantList` (`EliteaUI/src/pages/NewChat/Recommendations/NewParticipantList.jsx`) for its `'toolkit'` phase — **that shared component (and its child `NewParticipantCard`) carry ZERO testids anywhere** (confirmed via full-file read AND `git grep -c "data-testid\|testId"` returning empty for both files against `origin/main` and `origin/automation/testids`). `NewParticipantList` is also reused by `RecommendationList.jsx` and `SearchResultList.jsx` — per `.agents/testing.md` § Locator policy ("shared components never hardcode feature-scoped testids"), new testids must be threaded as caller-supplied props from `SlashSuggestionList`'s call site, not hardcoded inside `NewParticipantList`/`NewParticipantCard` themselves.

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Message input (trigger for `/`) | `[data-testid="chat-message-input"]` | **on-main ✓** | pre-existing `ChatPage.message_input` field — reuse directly, no new work |
| Slash-mention dropdown container | `testid needed: slash-mention-list` | needs-adding | `NewParticipantList.jsx:54`'s outer `Box` (the `ClickAwayListener`'s child). Add via a new optional prop, e.g. `containerTestId`, defaulted to `undefined` (existing callers `RecommendationList`/`SearchResultList` unaffected); `SlashSuggestionList.jsx`'s `<NewParticipantList ... containerTestId="slash-mention-list" .../>` call (line ~140) is the ONLY call site that sets it — this case only touches the toolkit-mention surface. Scope: title text + "No matching results" text are both read via this ONE container's `.text_content()` — no separate testid needed for the `Typography` sub-elements (avoids over-testid'ing elements this case never targets individually). |

## Network Behavior
- No network request fires for the `/`-dropdown itself in the empty-participants case — `filteredParticipants` is computed client-side from `activeConversation.participants` (already loaded); nothing to fetch when the list is empty.

## Known Defects Found During Exploration
- None. Feature matches the case's Objective and Pass/Fail criteria exactly.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- Page object: extend `automation/pages/chat_page.py`'s `ChatPage` with:
  - `slash_mention_list = LocatorDescriptor(testid="slash-mention-list")` (once added — see § Concrete Handles).
  - `open_slash_mention_dropdown()` — `message_input.click()` then `message_input.press_sequentially("/")`, then wait for `slash_mention_list` to become visible.
  - `close_slash_mention_dropdown()` — click a neutral page coordinate (outside-click; do **not** use `Escape`, see AFS step 4 note) then wait for `slash_mention_list` to detach.
- `conversation_id` fixture (`automation/fixtures/data_fixtures.py:38`) gives a fresh, isolated, participant-less conversation — exactly what this case's precondition needs; no extra setup.
- This AFS's proposed testids (`slash-mention-list` + the item/tool testids proposed in ELITEA-2203's and ELITEA-2204's AFS) are all on the SAME shared component tree — implement them together in one `add-data-testid` pass so all three cases build against the identical, already-verified handle set rather than three separate partial passes.
