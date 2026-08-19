# Test Case: Chat – Slash Commands – Selecting an MCP From '/' Shows Its Available Tools (or Correctly Doesn't)

## Metadata
- **TMS IDs**: ELITEA-2205 ("Chat – Slash Commands – Verify Selecting MCP from / Dropdown", priority medium), ELITEA-2468 ("Chat – Select MCP from / dropdown", priority high) — **family AFS**, `family_afs: true`, both cases share this `afs_path`
- **Linked Story**: none (both cases `requirements: []`)
- **Priority**: l2 (taking the higher of the two case priorities — ELITEA-2468 is `high`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (analyst slot), batch `chat-remaining-w14`, cluster dispatch (ELITEA-2205 + ELITEA-2468, one live session)
- **Status**: **ready-for-automation** — executed live end-to-end for BOTH the has-tools and no-tools MCP states. Matches the cases' Objective and most Pass/Fail criteria, with **one live product defect found and filed** — [#1596](https://github.com/EliteaAI/elitea-testing-public/issues/1596) — see § Known Defects. The defect is deterministic, single-cause, and isolable to one tail assertion (the "no tools ⇒ no list" branch); per `.agents/testing.md` § Merge gate "Analysis-time entry" this stays `ready-for-automation` with that one assertion written as `expect.soft()` + `# Known defect: #1596` (sanctioned-RED once implemented).
- **Family note (why one spec, not two)**: both cases test the exact same flow — type `/`, click the MCP card, verify composer + tools-list behavior — with the SAME steps in the SAME order; ELITEA-2468 merely spells the same 2 assertions ELITEA-2205 states tersely into 4 explicit steps and both use the same "delete" MCP test-data example. They differ only in wording/granularity, not in steps — textbook "merge cases that differ only in data" per `test-case-analysis` § Execute. One parameterized spec covers both; a fresh spec per case would just duplicate assertions.
- **Cluster note**: analysed together in one live session (shared login/navigation, MCP fixtures created once, both cases executed against the same live states). Reused all of `pages/chat_page.py`'s existing `ChatPage` slash-mention surface added for ELITEA-2202/2203/2204 (merged to `automation/base`, see § Concrete Handles Provenance) — no page-object changes needed, this case is a pure consumer of that surface.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation.
- An MCP-type toolkit exists and is addable via the plus-menu "+ > MCPs" toggle flow, and is added as a conversation participant BEFORE typing `/` (same participant-filtering mechanism as ELITEA-2203 — a toolkit that exists in the project but is NOT a conversation participant never appears in the `/` dropdown).

## Test Data

### Parameter table — one row per TMS case

| # | TMS ID | MCP state | MCP name (fixture-generated, illustrative here) | Expected tools-list behavior (per case text) |
|---|---|---|---|---|
| 1 | ELITEA-2205 | has tools (3: `ask_question`, `read_wiki_contents`, `read_wiki_structure`) | `autotest_mcp_<test>_hastools` | "Tools shown" |
| 2 | ELITEA-2468 | has tools (same as row 1 — case only names "delete" as an example, doesn't require a specific tool set) | `autotest_mcp_<test>_hastools` | "tools list appears" |
| — | both (Axis-2 enrichment, not case-required) | **no tools** (`settings.available_mcp_tools: []`) | `autotest_mcp_<test>_notools` | "no tools list appears" — **live product does NOT satisfy this, see § Known Defects** |

Both cases' Test Data table names the MCP `delete` — cosmetic, not literal (same convention as ELITEA-2203's AFS): assertions are written against the fixture-generated name, read back from the fixture's return value, never hardcoded `"delete"`.

### generate-per-test (reuse existing suite fixtures — no new fixture needed for the has-tools state)
- **MCP with tools**: reuse the existing `mcp_toolkit_with_tools` fixture as-is (`automation/fixtures/data_fixtures.py:2085-2127`) — public `mcp.deepwiki.com` endpoint, 3 real tools. Confirmed live this pass (again, same as ELITEA-2203/2204's prior confirmation): renders correctly, labelled "MCP".
- **MCP with NO tools** (new fixture needed — none exists today): a Remote MCP toolkit created via `ToolkitAPI.create_remote_mcp_toolkit(name=..., url=<any valid MCP URL — the sync-and-populate value is what matters, not connectivity>, tools=[])`. Confirmed live: `create_remote_mcp_toolkit` with an empty `tools` list produces a toolkit whose `settings.available_mcp_tools == []` / `settings.selected_tools == []` — this is an **honest API-level precondition** (a real toolkit resource with zero configured tools), not a UI-observable substitution; the slash-dropdown behavior under test is still driven live against this real toolkit. This also stands in for the case's "or disconnected" wording — confirmed via source read (see § Known Defects) that the UI-level code path for "toolkit has zero tools" and "toolkit's `available_mcp_tools` came back empty because it's disconnected" are IDENTICAL (both read `settings.available_mcp_tools`/`selected_tools`, empty either way) — no separate "genuinely disconnected" test is needed to cover the case's "or disconnected" branch.
- Both MCPs must be added to the conversation as **participants** before typing `/` (same toggle-switch `+ > MCPs` flow as ELITEA-2203, reusing `ChatPage.add_mcp_participant_via_slash_menu()`).

## Test Steps

_Steps are the same flow for both the has-tools and no-tools MCP states — only the tools-list outcome (step 3) differs, per the parameter table._

1. Add the MCP as a chat participant: open the plus menu (`plus-menu-button`), click **"MCPs"** (`mcps-menuitem`), click the matching toggle row (`mcps-menu-item-mcp-{project_id}-{toolkit_id}` — confirmed live, same dynamic-testid pattern as ELITEA-2203/2204). Close the popper via outside click.
2. Click into the message input and type `/`.
   - **Verify**: the slash-mention dropdown (`slash-mention-list`) shows the MCP's card, labelled **"MCP"** (confirmed live, exact case-match, same as ELITEA-2203's finding — literal string `'MCP'`, no CSS-transform caveat needed here unlike the Toolkit branch).
3. Click the MCP's card in the dropdown.
   - **Verify**: the message field shows exactly `/{mcp_name}` (confirmed live via the input's DOM text, no trailing space at this point — `onSlashSelectToolkit`'s replacement is exactly `'/' + toolkit.name`, source-confirmed generic across Toolkit/MCP, `EliteaUI/src/[fsd]/features/chat/lib/hooks/useSlashMention.hooks.js:80-113`).
   - **Verify (has-tools state, row 1/2)**: a NEW panel appears titled **`{mcp_name} available tools`**, listing exactly the MCP's 3 tools (`ask_question`, `read_wiki_contents`, `read_wiki_structure`), each row individually clickable — confirmed live, same `ToolList`/`ToolItem` component and testid scheme as ELITEA-2204's Toolkit-selection phase (`slash-mention-tool-list` container, `slash-mention-tool-item-{tool_name}` per-row — **already added to EliteaUI, ELITEA-2204's commit, on-`automation/testids`**, no new testid work needed for this case).
   - **Verify (no-tools state, Axis-2)**: **per the case's OWN stated expected result, no tools panel should appear at all.** Live product does NOT satisfy this — see § Known Defects. Write this as `expect.soft(slash_mention_tool_list not visible or has 0 rows) + # Known defect: #1596` — this assertion currently FAILS deterministically (the panel DOES render, header-only, zero rows) and should merge RED under the sanctioned-RED exception until the product fix ships.
4. (has-tools state only) Click one tool (e.g. `ask_question`) from the tools list.
   - **Verify**: the message field updates to `/{mcp_name}/{tool_name} ` (trailing space) — confirmed via source read: `onSlashCommitMention` (`useSlashMention.hooks.js:122-145`) is fully generic across participant type, `replacement = mentionToken + ' '` unconditionally; same mechanism ELITEA-2204 already live-confirmed for the Toolkit path.

## Expected Results
- Adding an MCP as a participant makes it selectable from the `/` dropdown, labelled "MCP".
- Selecting it replaces the composer fragment with `/{mcp_name}`.
- If the MCP has tools, they render in a titled tools list, each individually selectable, and selecting one appends `/{tool_name} ` (trailing space) to the composer.
- If the MCP has no tools (or is disconnected), the case expects no tools list to appear — **live product instead shows a header-only, zero-row panel; filed as a known defect, #1596, not blocking automation of the rest of this case.**
- No console errors during the whole sequence (confirmed live for both states — none observed).

## Coverage Map

### Axis 1 — Case coverage

**ELITEA-2205**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Type '/' and click 'delete' in dropdown | Message field shows '/delete' | AFS steps 2–3 | `message_input.input_value() == f"/{mcp_name}"` | asserted |
| 2 Verify if MCP has tools, they are displayed; if no tools/disconnected, no tools list | Tools shown or no tools depending on MCP state | AFS step 3 (both branches) | has-tools: `slash_mention_tool_list` visible, exactly 3 tool-item testids; no-tools: `expect.soft()` (see § Known Defects) | asserted (has-tools branch); **clarification/known-defect** (no-tools branch — live product diverges, filed #1596, soft-asserted not blocking) |

**ELITEA-2468**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Chats section with MCP participant | Target page loads | Precondition + Setup | conversation navigation, page loaded | asserted |
| 2 Type "/" and verify dropdown shows the MCP | Field accepts input, dropdown shows MCP | AFS step 2 | `slash_mention_list` visible, MCP card present, labelled "MCP" | asserted |
| 3 Click "delete" in dropdown, verify message shows "/delete" | Control responds; expected next state shown | AFS step 3 | `message_input.input_value() == f"/{mcp_name}"` | asserted |
| 4 Verify if MCP has available tools they are displayed; if no tools/disconnected, no tools list | Condition holds as described | AFS step 3 (both branches) | same as ELITEA-2205 row 2 above | asserted (has-tools branch); **clarification/known-defect** (no-tools branch, #1596) |

### Axis 2 — Analyst additions
- **No-tools MCP state** (both cases' Test Data table only mentions ONE MCP, "delete" — implied to have tools since the case's own Pass criteria distinguish "has tools" vs "no tools/disconnected" as two possible outcomes for the SAME MCP under test, but neither case's Test Data actually supplies a zero-tools MCP to exercise the second branch) — *added: without exercising this branch, half of the case's own stated Expected Result ("if no tools or disconnected, no tools list appears") would never be verified at all. Constructing a real zero-tools MCP via the toolkit API (§ Test Data) closes this gap and is what surfaced the #1596 defect.*
- **Tool-selection composer trailing space** (AFS step 4) — *added: same rationale as ELITEA-2204's AFS — the case's Pass/Fail criteria imply the exact composer string matters ("message field not updated" is a FAIL condition), and the trailing space is a real, source-confirmed part of the mechanism that a substring-only check would silently swallow.*
- No console errors during the whole add-participant → `/` → select → verify sequence, for BOTH MCP states — *added: standard side-channel check, none observed either state.*

## Cleanup
- Conversation deleted by the `conversation_id` fixture's teardown.
- Both MCP toolkits (has-tools + no-tools) deleted by their fixtures' teardown (`toolkit_api.delete_toolkit`).
- (Analyst's scratch exploration data — conversation 9113, toolkits 2919/2920 — already deleted via the API during this analysis pass; not left behind.)

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Plus menu button | `[data-testid="plus-menu-button"]` | **on-main ✓** | pre-existing, `ChatPage.plus_menu_button` |
| "MCPs" plus-menu item | `[data-testid="mcps-menuitem"]` | **on-main ✓** (`PlusChatButton.jsx:47`) | pre-existing, `ChatPage.mcps_menuitem` |
| MCP participant toggle row (dynamic) | `[data-testid="mcps-menu-item-mcp-{project_id}-{toolkit_id}"]` | **on-`automation/testids` only** — commit `73595e8d` (ELITEA-2094), confirmed still not on `main` as of this pass (see `_surface.md` update below) | `ChatPage.MCP_PARTICIPANT_MENU_ITEM` template + `add_mcp_participant_via_slash_menu()` — REUSE AS-IS, live-confirmed working for both MCP fixtures this pass (`mcps-menu-item-mcp-399-2919`, `mcps-menu-item-mcp-399-2920`) |
| Slash-mention dropdown container | `[data-testid="slash-mention-list"]` | **on-`automation/testids` only** — commit `34319b30` (ELITEA-2202/2203/2204 implementation) | `ChatPage.slash_mention_list` — REUSE AS-IS |
| Per-item card in slash-mention dropdown (dynamic) | `[data-testid="slash-mention-item-{project_id}_{toolkit_id}"]` | same commit `34319b30` | `ChatPage.SLASH_MENTION_ITEM` template + `get_slash_mention_item()` / `select_slash_mention_toolkit()` — REUSE AS-IS. `select_slash_mention_toolkit()` name is generic despite the name — confirmed live this pass it works identically for an MCP card (its docstring already says "Click a toolkit/MCP card") |
| Available-tools list container | `[data-testid="slash-mention-tool-list"]` | same commit `34319b30` | `ChatPage.slash_mention_tool_list` — REUSE AS-IS. Confirmed live this pass: renders for MCP participants via the exact same `ToolList` component as Toolkit participants (`SlashSuggestionList.jsx`'s `availableTools` memo branches on `isMcpToolkit()` to read `settings.available_mcp_tools` vs `settings.selected_tools`, but both map into the same `{name, description}` shape `ToolList` consumes — no separate MCP-specific container) |
| Per-tool item (dynamic) | `[data-testid="slash-mention-tool-item-{tool_name}"]` | same commit `34319b30` | `ChatPage.SLASH_MENTION_TOOL_ITEM` template + `select_slash_mention_tool()` / `get_slash_mention_tool_testids()` — REUSE AS-IS. Confirmed live this pass with MCP tool names (`slash-mention-tool-item-ask_question` clicked successfully) |
| Message input | `[data-testid="chat-message-input"]` | **on-main ✓** | `ChatPage.message_input`, read via `.input_value()` |

**⚠️ Caution for the implementer — `select_slash_mention_toolkit()` waits for a tool-item row to attach.** Its docstring (`chat_page.py:6406-6424`) says it "waits for the first tool-item row to attach instead" of just container visibility, to dodge the `isToolsFetching` race (ELITEA-2204's fix). **This wait will TIMEOUT for the no-tools MCP state** (zero rows ever attach) — do NOT reuse `select_slash_mention_toolkit()` unmodified for the no-tools branch. Either: (a) inline the click + container-visibility wait without the "first row" wait for that one test, or (b) add a `wait_for_first_tool: bool = True` parameter to `select_slash_mention_toolkit()` (additive, doesn't break ELITEA-2204's existing call). Implementer's call which is cleaner; either is in-contract (no locator/fidelity policy involved, pure wait-strategy adjustment).

**No new testids needed for this case** — every handle above was already added to EliteaUI by the ELITEA-2202/2203/2204 implementation (all on `automation/testids`, none yet on `main` per that AFS's provenance notes — unchanged this pass, re-verify at implementation time with a fresh `git fetch origin`).

## Network Behavior
- Adding a participant: same participant-update mutation as ELITEA-2203, not independently re-verified this pass.
- Selecting an MCP: `GET` toolkit-details (`useToolkitsDetailsQuery`) resolves `settings.available_mcp_tools` — confirmed live via the brief loading state before either 3 tools (has-tools) or the empty panel (no-tools) renders.
- Selecting a tool: no network call — pure client-side composer text replacement (`onSlashCommitMention`).

## Known Defects Found During Exploration
- **[MINOR] MCP/Toolkit with zero available tools still opens an empty "available tools" panel — filed [#1596](https://github.com/EliteaAI/elitea-testing-public/issues/1596).** Root-caused via source read: `SlashSuggestionList.jsx`'s early-return (`if (!isToolsFetching && toolQuery && filteredTools.length === 0) return null;`) only hides the tools panel when the user has typed a **tool-name filter that matches nothing** — it does NOT cover "the toolkit/MCP genuinely has zero tools and no filter is typed", so `<ToolList>` always renders in that case, and `ToolList.jsx` unconditionally renders its `"{name} available tools"` header Box regardless of whether `tools` is empty (no "no tools" empty-state message either — just a header with nothing under it). Confirmed live twice (immediately and after a 2s settle, ruling out an `isToolsFetching` race) against a real zero-tools MCP toolkit, no console errors. Applies identically to a zero-tool Toolkit participant (same shared component, same missing guard) — not MCP-specific, though filed from this MCP case's explicit acceptance criterion. Per `.agents/testing.md` § Merge gate "Analysis-time entry", this is deterministic + single-cause + tail-isolable — automate the rest of the case normally and write ONLY the no-tools-panel assertion as `expect.soft()` + `# Known defect: #1596`.
- No other defects. Both cases' remaining Objective/Pass-Fail criteria match live product behavior exactly.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- **New fixture needed**: an MCP toolkit with zero tools — `toolkit_api.create_remote_mcp_toolkit(name=..., description=..., url=<reuse the same deepwiki URL constant>, tools=[])`. Suggest naming it `mcp_toolkit_no_tools` in `fixtures/data_fixtures.py`, mirroring `mcp_toolkit_with_tools`'s shape (`{"id", "name", "toolkit_name", "tools": [], "project_id"}`) and cleanup pattern.
- Reuse `ChatPage.add_mcp_participant_via_slash_menu()`, `open_slash_mention_dropdown()`, `get_slash_mention_item()`/`select_slash_mention_toolkit()` (with the wait-strategy caveat above for the no-tools branch), `select_slash_mention_tool()`, `close_plus_menu_popper()` — all pre-existing, no page-object changes needed except the optional `wait_for_first_tool` parameter noted above.
- Two tests recommended (one per parameter-table state), sharing the same conversation-setup pattern as `test_slash_mention_toolkit_and_mcp_participants.py` / `test_slash_mention_toolkit_tool_selection.py`:
  - `test_select_mcp_from_slash_mention_shows_its_tools` (has-tools state; covers both ELITEA-2205 and ELITEA-2468's has-tools assertions — `@allure.issue` both TMS links)
  - `test_select_mcp_from_slash_mention_no_tools_shows_empty_panel` (no-tools state; covers both cases' "no tools/disconnected" branch; carries the `# Known defect: #1596` soft assertion, sanctioned-RED once merged)
- `conversation_id` + `mcp_toolkit_with_tools` + the new `mcp_toolkit_no_tools` fixtures give fully isolated, auto-cleaned test data.
