# Test Case: Chat – Slash Commands – Typing '/' Shows Only the Added Toolkit and MCP Participants

## Metadata
- **TMS ID**: ELITEA-2203
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (analyst slot), batch `approved-next50`, cluster with ELITEA-2202/2204
- **Status**: **ready-for-automation** — executed live end-to-end (one Artifact-type toolkit + one Remote-MCP toolkit added as participants via the real "+ > Toolkits" / "+ > MCPs" UI flow, then `/` typed). Matches the case's Objective and Pass/Fail criteria exactly (screenshot: both cards shown, labelled "Toolkit"/"MCP" respectively, distinct icons, nothing else listed). The item cards carry **zero testids today** — `add-data-testid` work is required (see § Concrete Handles).
- **Cluster note**: analysed together with ELITEA-2202 (empty state) and ELITEA-2204 (toolkit→tool selection) in one live session — three **separate AFS files**, see ELITEA-2202's AFS Cluster note for the full rationale. This case is the one that actually exercises the "+ > Toolkits" and "+ > MCPs" add-participant flows the other two only assume as a precondition.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation (fresh `conversation_id` fixture conversation).
- One Toolkit-type and one MCP-type toolkit exist and are addable via the plus-menu search (see § Test Data).

## Test Data

### Case's literal names are cosmetic — not required verbatim
The case's Test Data table names a toolkit `banana` and an MCP `delete`. Live exploration used **auto-generated unique names** (`banana-745480` / `delete-745480` pattern, timestamp-suffixed per the suite's existing `artifact_toolkit`/`mcp_toolkit_with_tools` fixture convention) — the case's exact strings are illustrative, not literal requirements; the case's own Pass/Fail criteria only require "the specifically added toolkit and MCP" to appear, which is name-agnostic. Assertions below are written against **whatever name the test's own fixture generates**, read back from the fixture's return value — never hardcoded.

### generate-per-test (reuse existing suite fixtures — no new fixture needed)
- **Toolkit participant**: an Artifact-type toolkit, created the same way the existing `artifact_toolkit` fixture does (`automation/fixtures/data_fixtures.py:493-534`) — `ToolkitAPI.create_toolkit(toolkit_type="artifact", ...)`. Any Artifact toolkit works for THIS case (2203 only asserts labeling, not tool contents — contrast with ELITEA-2204, which needs a specific 4-tool `selected_tools` list).
- **MCP participant**: reuse the existing `mcp_toolkit_with_tools` fixture as-is (`automation/fixtures/data_fixtures.py:726-761`) — public `mcp.deepwiki.com` endpoint, 3 tools (`ask_question`, `read_wiki_contents`, `read_wiki_structure`). Confirmed live: this MCP renders correctly in the slash-mention dropdown labelled "MCP".
- Both toolkits must be added to the conversation as **participants** before typing `/` — the dropdown's `filteredParticipants` (in `SlashSuggestionList.jsx`) is a client-side filter over `activeConversation.participants`, so a toolkit that exists in the project but is NOT a conversation participant never appears here (this is the feature's whole point — contrast with the project-wide toolkit list elsewhere in the UI).

## Test Steps

1. Add the Toolkit as a chat participant: open the plus menu (`plus-menu-button`), click **"Toolkits"** (`toolkits-menuitem`), type the toolkit's name into the search field (`toolkits-search-input`), click the matching item (`toolkits-menu-item-toolkit-{project_id}-{toolkit_id}` — dynamic, confirmed live format below).
   - **Note (mechanism)**: unlike the AGENT add flow (single click selects-and-closes), the Toolkits/MCPs entries in this plus-menu render as **toggle switches** (`showToggle: true` in `PlusChatSubmenu.jsx`) — clicking the row toggles participant membership ON without closing the submenu. This is a genuinely different interaction shape from the existing `ChatPage.add_toolkit_participant()` method (which assumes select-and-close, legacy text-based locators) — do not reuse that method for this case; see § Automation Hints for the new method this case needs.
2. WITHOUT closing the outer plus-menu popper, add the MCP as a chat participant: click **"MCPs"** (`mcps-menuitem` — same open `Popper`, switches which submenu is shown), type the MCP's name into `mcps-search-input`, click the matching item (`mcps-menu-item-mcp-{project_id}-{toolkit_id}` — dynamic, confirmed live format below).
   - **Quirk, confirmed live**: closing the popper (`Escape`) and re-clicking `plus-menu-button` between steps 1 and 2 **toggles the whole popper CLOSED** instead of reopening it (same "second click on an already-open popper closes it" quirk already documented for the Attach-Files popper, `_surface.md` § File attachments) — because `Escape` does not reliably close this `Popper`+`ClickAwayListener` shape either (see ELITEA-2202's AFS step 4 note). Do NOT close between steps 1 and 2 — go directly from the Toolkits submenu to the MCPs submenu within the same open popper.
   - Close the popper afterward with an outside click (not `Escape`).
   - **Verify**: both participants now show — `is_participants_badge_visible(section="toolkits") == True` and `is_participants_badge_visible(section="mcp") == True` (pre-existing helper, reused).
3. Click into the message input and type `/`.
   - **Verify**: the dropdown shows **exactly two** items — confirmed live via screenshot: a card labelled **"banana-745480" / "Toolkit"** (folder-style icon) and a card labelled **"delete-745480" / "MCP"** (wrench/plug-style icon), side by side, nothing else.
4. Verify the Toolkit item's type label reads exactly **"Toolkit"** (lowercase in source — `NewParticipantCard.jsx`'s type `Typography` renders `participant.type?.toLowerCase().endsWith('mcp') ? 'MCP' : participant.participantType`, CSS `text-transform: capitalize` renders it "Toolkit" on screen; the underlying DOM text is lowercase `"toolkits"`/`"Toolkits"` per `ChatParticipantType` — assert via the item's own `.text_content()` substring match, not a separate raw text locator).
5. Verify the MCP item's type label reads exactly **"MCP"** (same mechanism — `NewParticipantCard.jsx`'s ternary explicitly special-cases MCP toolkit types to literal `'MCP'`, confirmed live in the screenshot).
6. Verify no other toolkits or MCPs appear — confirmed live: exactly 2 item-testid matches inside the dropdown container (see § Concrete Handles for the dynamic item testid this needs).

## Expected Results
- After adding one Toolkit-type and one MCP-type toolkit as participants, typing `/` shows a dropdown with exactly those two items.
- Each item is correctly labelled ("Toolkit" / "MCP") with a distinct icon.
- No other toolkits/MCPs — including ones that exist in the project but are NOT conversation participants — ever appear.
- No console errors during the sequence (confirmed live — none observed).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Add toolkit 'banana' via + > Toolkits; add MCP 'delete' via + > MCPs | Both in PARTICIPANTS panel | AFS steps 1–2 | `is_participants_badge_visible(section="toolkits"/"mcp") == True` | asserted *(names generated per-test, not literal "banana"/"delete" — see § Test Data)* |
| 2 Type '/' in message input | 'MENTION TOOLKIT OR MCP' dropdown shows exactly 'banana' (Toolkit) and 'delete' (MCP) | AFS step 3 | dropdown container: exactly 2 item-testid matches, names read from fixture | asserted |
| 3 Verify 'banana' labeled 'Toolkit' with toolkit icon | Toolkit label and icon correct | AFS step 4 | toolkit item's `.text_content()` contains "Toolkit"; icon presence checked (see § Concrete Handles icon note — label text is the PRIMARY signal, icon distinctness is a declared secondary check) | asserted |
| 4 Verify 'delete' labeled 'MCP' with MCP icon | MCP label and icon correct | AFS step 5 | MCP item's `.text_content()` contains "MCP"; icon presence checked (same declared-improvisation note as row above) | asserted |
| 5 Verify no other toolkits or MCPs appear | Only the two added items shown | AFS step 6 | dropdown container: item-testid count == 2 | asserted |

### Axis 2 — Analyst additions
- **Declared improvisation (icon assertion scope)**: `EntityIcon.jsx` (`EliteaUI/src/components/EntityIcon.jsx`) already renders a genuinely different SVG component per participant type (`ApplicationsIcon`/`FlowIcon`/toolkit icon/`MCPIcon`) — confirmed via source read — but NONE of these icon components carry a testid or any other stable per-type attribute today, and they're shared across many other call sites (agent cards, pipeline cards, etc.) well outside this case's scope. Per `.agents/testing.md` § Locator policy ("shared components never hardcode feature-scoped testids") and the "scope is exactly what this test touches" rule, adding a distinguishing testid to `EntityIcon` itself is out of scope for this case. Chose instead: assert icon PRESENCE (an icon element renders inside the item, via the item's own testid scope) as the automatable signal, with the adjacent TYPE-LABEL TEXT ("Toolkit"/"MCP") carrying the actual type-correctness assertion — this is what the case's Pass/Fail criteria substantively need ("Toolkit label and icon correct"), and it doesn't touch a shared component's internals. Reasoning declared here per `.agents/role-overrides.md` § Declared-improvisation protocol — reviewer should verify this scoping call, not treat it as an unfulfilled testid request.
- No console errors during the whole add-participants → `/` → verify sequence — *added: standard side-channel check, none observed.*

## Cleanup
- Conversation deleted by the `conversation_id` fixture's teardown.
- Toolkit + MCP toolkit deleted by their respective fixtures' teardown (`toolkit_api.delete_toolkit`).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Plus menu button | `[data-testid="plus-menu-button"]` | **on-main ✓** | pre-existing |
| "Toolkits" plus-menu item | `[data-testid="toolkits-menuitem"]` | **on-main ✓** (`PlusChatButton.jsx:46`) | pre-existing; hover-triggered (`onMouseEnter`), not click — Playwright's `.click()` moves the mouse first, which fires the hover handler naturally; confirmed live to work via plain `.click()` |
| "MCPs" plus-menu item | `[data-testid="mcps-menuitem"]` | **on-main ✓** (`PlusChatButton.jsx:47`) | pre-existing; same hover-triggered mechanism. Gated by `useIsMcpVisible()` (platform settings `mcp_exposure_enabled`/`mcp_in_menu_enabled`) — confirmed live via `GET /elitea_core/platform_settings/prompt_lib`: both `true` in this environment, so the item is visible. |
| Toolkits search input | `[data-testid="toolkits-search-input"]` | **on-`automation/testids` only** — commit `73595e8d` ("add data-testid for plus-menu entity items/rows (ELITEA-2094)"), NOT yet on `main` | `PlusChatSubmenu.jsx:89`, `` `${sectionKey}-search-input` `` template, `sectionKey="toolkits"` |
| MCPs search input | `[data-testid="mcps-search-input"]` | **on-`automation/testids` only** — same commit `73595e8d` | same template, `sectionKey="mcps"` |
| Toolkit item row (dynamic) | `testid needed pattern (confirmed live): [data-testid="toolkits-menu-item-toolkit-{project_id}-{toolkit_id}"]` | **on-`automation/testids` only** — same commit `73595e8d` | `PlusChatSubmenu.jsx:131`, `` `${sectionKey}-menu-item-${item.key}` ``. Live-confirmed concrete value for a toolkit with `project_id=399, id=2298`: `toolkits-menu-item-toolkit-399-2298`. Template constant for the page object: `TOOLKIT_PARTICIPANT_MENU_ITEM = '[data-testid="toolkits-menu-item-toolkit-{}-{}"]'` (format with `project_id, toolkit_id`, both known from the fixture's return dict — no name-based filtering needed). |
| MCP item row (dynamic) | `testid needed pattern (confirmed live): [data-testid="mcps-menu-item-mcp-{project_id}-{toolkit_id}"]` | **on-`automation/testids` only** — same commit `73595e8d` | Live-confirmed concrete value for `project_id=399, id=2299`: `mcps-menu-item-mcp-399-2299`. Template: `MCP_PARTICIPANT_MENU_ITEM = '[data-testid="mcps-menu-item-mcp-{}-{}"]'`. |
| Slash-mention dropdown container | `testid needed: slash-mention-list` | needs-adding (see ELITEA-2202's AFS — same handle, implement once) | Used here to scope the exactly-2-items count and both items' `.text_content()` reads |
| Per-item card in the slash-mention dropdown (dynamic) | `testid needed: slash-mention-item-{project_id}_{toolkit_id}` | needs-adding | `NewParticipantCard.jsx` — zero testids today (see ELITEA-2202's AFS § Concrete Handles for the full shared-component threading requirement: `SlashSuggestionList.jsx` must pass a `getItemTestId(participant)` callback or per-item `testId` prop down through `NewParticipantList` → `NewParticipantCard`, since both are shared with `RecommendationList`/`SearchResultList`). Naming choice (`{project_id}_{toolkit_id}`) mirrors the live-confirmed plus-menu item key shape above for consistency, though the exact separator is the implementer's call. |

## Network Behavior
- Adding a participant: the toggle fires the same participant-update mutation the rest of the suite already exercises for agents (`useConversationEditMutation`/participant-add endpoint family) — not independently re-verified this pass, out of scope (case doesn't ask for network-level assertions).
- The `/`-dropdown itself: purely client-side (`activeConversation.participants` already in Redux state) — no new network request on typing `/`.

## Known Defects Found During Exploration
- None. Feature matches the case's Objective and Pass/Fail criteria exactly.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- **New page-object method needed** — `ChatPage.add_toolkit_participant_via_slash_menu(project_id, toolkit_id)` / `add_mcp_participant_via_slash_menu(project_id, toolkit_id)` — do NOT reuse the existing `add_toolkit_participant(toolkit_name)` (`chat_page.py:3910-3952`): that method assumes select-and-close semantics (agents' flow) and legacy `get_by_placeholder`/`li[role="menuitem"]:has-text(...)` locators, neither of which match the toggle-switch, testid'd flow this case actually exercises. New methods should:
  1. Click `plus_menu_button`.
  2. Click `toolkits_menuitem` (new `LocatorDescriptor`) or `mcps_menuitem` (new `LocatorDescriptor`).
  3. Type into `toolkits_search_input`/`mcps_search_input` (new `LocatorDescriptor`s).
  4. Click the dynamic `TOOLKIT_PARTICIPANT_MENU_ITEM`/`MCP_PARTICIPANT_MENU_ITEM` template, formatted with `(project_id, toolkit_id)` from the fixture's return dict.
  5. For the two-in-one-popper case (this test needs both), do steps 2–4 for Toolkits, then repeat steps 2–4 for MCPs WITHOUT closing in between (see AFS step 2's quirk note), then close via outside click.
- `conversation_id` + the reused `artifact_toolkit`-style / `mcp_toolkit_with_tools` fixtures give fully isolated, auto-cleaned test data — no new fixture required.
- Close the plus-menu popper via an outside click (e.g. `page.mouse.click(x, y)` at a neutral chat-area coordinate, or a dedicated page-object method) — never `Escape` (see AFS step 2 quirk note).
