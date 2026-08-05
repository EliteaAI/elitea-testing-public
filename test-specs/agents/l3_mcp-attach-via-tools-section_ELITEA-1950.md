# Test Case: MCP Integration in Agent — Attach MCP via Tools Section

## Metadata
- **TMS ID**: ELITEA-1950
- **Linked Story**: none
- **Priority**: l3 (medium, per case metadata)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — executed end-to-end live (attach → persist
  across reload → remove), no blockers. One new testid added (`agent-add-mcp-button`,
  draft PR EliteaAI/EliteaUI#565) and one case-text-drift CLARIFICATION filed
  ([EliteaAI/elitea-testing-public#530](https://github.com/EliteaAI/elitea-testing-public/issues/530),
  "Found while working #70") — see § Known Defects / Coverage Map for detail.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- An existing agent is available in the project — used the seeded "Test Agent"
  (agent id `3` in this run, `/agents/all/3`).
- A Remote MCP is available in the project — **case-text drift**: the case's
  example ("Web Search") does not exist as project data (project `399`, verified
  live via the MCP add-popper's item list). Substituted an existing project MCP,
  `autotest_remote_mcp_full`, to execute the flow — sufficient for the observable
  under test (attach / persist / remove), not a data gap worth filing on its own.

## Test Data

### reuse-existing
- Agent: "Test Agent" (id `3`), any existing agent in the project works — the
  flow is agent-agnostic.
- MCP: `autotest_remote_mcp_full` (an existing Remote MCP toolkit in project `399`,
  created by the ELITEA-1922 AFS's `test_create_remote_mcp_all_fields_populated`).
  Any project MCP not already attached to the target agent works equally.

No `generate-per-test` data is needed — this flow doesn't create/destroy any
persistent entity of its own; it only associates/disassociates an existing MCP
toolkit with an existing agent (cleanup = leave the agent in its pre-test state,
see § Cleanup).

## Test Steps

1. Navigate to `${BASE_URL}/agents/all/3?viewMode=owner`. Agent detail page loads.
   - **Verify — PASSES.** Page loads; Information section shows Agent ID `3`.
2. Scroll to the "Tools" accordion section (`agent-toolkits-section` testid,
   already expanded by default) and verify it is expanded.
   - **Verify — PASSES.**
3. Verify the four tool-type add controls are visible in the Tools section.
   - **Verify — PASSES, with case-text drift (CLARIFICATION filed, see § Known
     Defects).** The case describes these as "tool type tabs" with a persistent
     "active tab" state and a shared "MCP selection area" that appears after
     clicking. The live product instead renders **four independent "+ &lt;Type&gt;"
     buttons** — Toolkit / MCP / Agent / Pipeline — each of which opens its own
     `UnifiedDropdown` popper directly on click. There is no tab control and no
     "active" state to assert; asserting "4 buttons are visible, each labelled
     Toolkit/MCP/Agent/Pipeline" is the live-accurate equivalent of case steps 3–5.
4. Click the "MCP" add button (`agent-add-mcp-button` — **testid added this run**,
   draft PR EliteaAI/EliteaUI#565; the sibling Toolkit button already carried
   `agent-add-toolkit-button`).
   - **Verify — PASSES.** A `UnifiedDropdown` popper opens directly (no
     intermediate "tab becomes active" state — see step 3 drift note) with a
     "Search mcps..." input and a list of project MCPs plus a "Create new" entry.
5. Select the target MCP from the popper by its rendered name (`autotest_remote_mcp_full`
   in this run; menu items render as `role="menuitem"` with the MCP's name as
   accessible text — no per-item testid, matching the existing Toolkit/Skill
   popper pattern in this codebase).
   - **Verify — PASSES.** Popper closes; a toast/alert confirms attachment; the MCP
     immediately appears as a card in the Tools section (see step 6).
6. Verify the selected MCP appears in the tools list under the Tools section.
   - **Verify — PASSES.** A card renders with the MCP's name (`autotest_remote_mcp_full`)
     and description ("Full configuration test MCP"), plus a connection-status
     banner ("The autotest_remote_mcp_full mcp server is disconnected. Reconnect
     it to use.") and a "Log in" button — this MCP requires OAuth; connection
     status is a separate concern from attachment and not asserted further here.
     Card DOM: `[data-testid="agent-toolkit-card"]` (existing testid, shared
     between Toolkit and MCP cards — see § Concrete Handles).
7. Click Save on the agent.
   - **Verify — PASSES, with case-text drift (CLARIFICATION filed).** Attaching
     the MCP fires an immediate `PATCH /api/v2/elitea_core/tool/prompt_lib/399/{tool_id}`
     (→ `201 Created`) — the association is auto-saved the instant the popper item
     is selected, mirroring this codebase's existing skill-attach
     (`AgentDetailPage.attach_skill()`) and toolkit-attach (`add_toolkit()`) flows.
     The agent-level "Save" button stays **disabled** throughout (nothing on the
     Formik form itself changed), so there is nothing to click here — the
     live-accurate equivalent is asserting the PATCH response status, not a Save
     click.
8. Reload the page; verify the MCP is still attached under the Tools section.
   - **Verify — PASSES.** After a full `page.goto()` reload of `/agents/all/3`,
     `autotest_remote_mcp_full` is still rendered as a Tools-section card
     (confirmed via `document.body.innerText` containing the MCP name).
9. Remove the MCP attachment; verify it's gone.
   - **Verify — PASSES.** Hover the card to reveal the delete icon
     (`agent-toolkit-delete-button`, scoped within `agent-toolkit-card` — same
     shared testids the Toolkit-removal flow already uses, confirmed live to work
     unchanged for MCP cards), click it, confirm the "Remove MCP?" dialog ("Are you
     sure to remove the {name} from agent?", Cancel/Remove buttons) via "Remove".
     Card disappears immediately (no reload needed) and stays gone after a fresh
     reload.

## Expected Results
- MCP attaches to the agent immediately on selection (`PATCH .../tool/prompt_lib/{project}/{id}` → 201).
- Attached MCP persists across a full page reload.
- MCP can be removed via its card's delete icon + "Remove MCP?" confirmation; removal
  persists across a fresh reload.
- No console errors attributable to the attach/detach flow (see § Network Behavior
  for the one unrelated console error observed).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agents section, open agent detail page | Agent detail page loads | step 1 | `step 1`: Information section + Agent ID visible | asserted |
| 2 Scroll to Tools section, verify expanded | Tools section visible/expanded | step 2 | `step 2`: `agent-toolkits-section` visible | asserted |
| 3 Verify tool type tabs visible: Toolkit, MCP, Agent, Pipeline | All 4 tabs shown | step 3 | `step 3`: 4 add-buttons visible, labelled Toolkit/MCP/Agent/Pipeline | clarification *(no "tabs" exist — 4 independent buttons; see § Known Defects)* |
| 4 Click "MCP" tab button | MCP tab is active | step 4 | `step 4`: MCP popper opens on click | clarification *(no "active tab" state exists to assert — button click opens a popper directly)* |
| 5 Verify MCP selection area appears | Selection UI displayed | step 4 | `step 4`: popper with search + menu items visible | asserted *(decomposed into step 4, same UI event as case step 4)* |
| 6 Select Remote MCP from dropdown (e.g. "Web Search") | MCP is selected | step 5 | `step 5`: popper closes, toast confirms | asserted, with data substitution *(project has no "Web Search" MCP; used `autotest_remote_mcp_full` — see § Preconditions)* |
| 7 Verify selected MCP appears in tools list | MCP appears in list | step 6 | `step 6`: card with MCP name/description visible | asserted |
| 8 Click Save on agent | Operation completes successfully | step 7 | `step 7`: PATCH .../tool/... returns 201 (already fired at step 5's selection) | clarification *(attach is auto-save; there is no separate agent-level Save step to click — Save button stays disabled)* |
| 9 Reload page, verify MCP still attached | MCP persists after reload | step 8 | `step 8`: MCP name present in DOM after `page.goto()` reload | asserted |
| 10 Remove MCP attachment, save, verify gone | MCP no longer listed | step 9 | `step 9`: card removed after confirm dialog, gone after reload | asserted |
| Expected Final State: MCP attachment removed after saving | — | step 9 | `step 9` | asserted |

### Axis 2 — Analyst additions

- `step 6` asserts the exact connection-status banner text ("...mcp server is
  disconnected. Reconnect it to use.") and the presence of a "Log in" button on
  the attached card — *added: this MCP requires OAuth; worth guarding that the
  attach flow doesn't silently swallow/hide the disconnected state, though
  connecting it is out of scope for this case.*
- `step 7` asserts the underlying `PATCH .../tool/prompt_lib/{project}/{tool_id}`
  response status (201) directly, rather than only a UI-visible "success" signal —
  *added: this is the actual persistence signal; a toast alone doesn't prove the
  server-side association succeeded.*
- `step 9` asserts removal survives an explicit fresh-reload check (not just
  DOM-disappearance right after the confirm click) — *added: mirrors the existing
  `remove_toolkit()` page-object pattern's care about async React state updates;
  a card that vanishes optimistically but reappears after refetch would be a real
  regression this case's literal text wouldn't catch.*

## Cleanup
1. If the target agent didn't have the MCP attached before the test, remove it
   again at teardown (the flow in step 9 is itself the removal — for automation,
   wrap attach/detach in a `try/finally` so a failed assertion mid-test still
   leaves the agent in its original state).
2. No other entities are created by this flow — nothing else to tear down.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Tools accordion section | `LocatorDescriptor(testid="agent-toolkits-section")` (existing, `AgentDetailPage.toolkits_section`) | none — testid-only policy |
| "+ MCP" add button | `LocatorDescriptor(testid="agent-add-mcp-button")` — **added this run**, EliteaUI draft PR#565 | none |
| "+ Toolkit" add button (for contrast/reuse) | `LocatorDescriptor(testid="agent-add-toolkit-button")` (existing) | none |
| MCP add popper | `components.mui.Popper` (existing shared helper — same `MuiPopper-root` component as Toolkit/Skill/Agent/Pipeline dropdowns) | none |
| MCP popper search input | scoped inside popper: `[data-testid="toolkit-search-input"]`? **not confirmed for the MCP popper specifically in this run** — the MCP popper's search placeholder is "Search mcps..."; existing `add_toolkit()` looks up `[data-testid="toolkit-search-input"]` inside the popper for the Toolkit flow. Automation engineer: verify whether the MCP popper's search input carries the same testid or needs its own before reusing `add_toolkit()`'s pattern verbatim. |
| MCP popper menu item (select by name) | `Popper.select_menuitem(popper, mcp_name, page)` (existing shared helper, already used by `add_toolkit()` — confirmed working for MCP items in this run: menu items render `role="menuitem"` with the MCP name as text, no name-stripping quirk like the Toolkit popper's space-stripping) | none |
| Attached MCP card | `LocatorDescriptor(testid="agent-toolkit-card")` filtered `.filter(has_text=mcp_name)` (existing, shared with Toolkit cards — confirmed same component `ToolCard.jsx` renders both) | none |
| MCP card delete (hover-revealed) icon | scoped inside card: `[data-testid="agent-toolkit-delete-button"]` (existing, shared with Toolkit cards — confirmed working unchanged for MCP in this run) | none |
| "Remove MCP?" confirm dialog | `components.mui.Dialog.wait_for(page)` + `Dialog.click_first_button(dialog, "Remove", "Confirm", "Delete")` (existing shared helper — dialog title is "Remove MCP?" for MCP cards vs "Remove toolkit?" for Toolkit cards, but the shared helper matches on button text, not title, so it works unchanged) | none |

**Recommendation for the implementer:** `AgentDetailPage`'s existing `add_toolkit()`
/ `remove_toolkit()` / `is_toolkit_attached()` methods are built around the shared
`ToolCard`/`agent-toolkit-card`/`agent-toolkit-delete-button` handles and should
work for MCP cards with **no new page-object methods** beyond adding an
`add_mcp()` counterpart that clicks `agent-add-mcp-button` instead of
`agent-add-toolkit-button` (everything downstream — popper, search, select,
card lookup, removal — reuses the existing toolkit-flavored methods/helpers,
since MCP cards use the exact same `data-testid`s as Toolkit cards).

## Network Behavior
- `PATCH /api/v2/elitea_core/tool/prompt_lib/399/{tool_id}` — fires on MCP
  selection from the popper, `201 Created` on success. This is the real
  persistence signal (see step 7 clarification — there is no separate
  agent-level Save request for this flow).
- No additional GET refetch was observed to be required before the card renders
  (unlike the Skills section's RTK-Query-refetch timing caveat documented in
  `AgentDetailPage.attach_skill()`) — the card appeared synchronously with the
  PATCH response in this run. Automation engineer: still prefer `wait_for_network()`
  over a fixed timeout, per `.claude/rules/ui-tests.md`.

## Implementer Amendment (Phase 2/3, ELITEA-1950)

- **§ Concrete Handles gap confirmed and resolved**: the MCP popper's search
  input (`toolkit-search-input`) and menu items (`toolkit-menu-item`) are
  rendered unconditionally by the shared `UnifiedDropdown.jsx` component
  regardless of entity type (toolkit/mcp/agent/pipeline) — confirmed via
  source read, not just live observation. `add_toolkit()`'s pattern is safe
  to mirror verbatim for `add_mcp()`. Unlike the Toolkit popper, MCP names are
  **not** space-stripped in the popper — `add_mcp()` matches the exact name.
- **Step 3 scoped down**: only the two testid-backed add buttons (`+ Toolkit`
  / `+ MCP`) are asserted. `ToolMenu.jsx`'s Agent and Pipeline add buttons
  carry no `data-testid` at all (confirmed via source read) — asserting them
  would require a text-based locator, forbidden by the testid-only/no-fallback
  policy, and adding new testids is out of scope for this dispatch (the
  `automation/testids` integration branch is sealed to the already-merged
  `agent-add-mcp-button` commit backing draft PR #565). Follow-up: add
  testids to the Agent/Pipeline buttons in a future `add-data-testid` pass if
  full 4-button coverage is wanted.
- **Axis 2 addition (connection-status banner + "Log in" button) dropped**:
  `ToolCard.jsx` renders the disconnected-status text only inside a MUI
  `Tooltip` `title` (no `data-testid`, not in the DOM until hover) and the
  "Log in" button (`McpLogInButton.jsx`) also carries no `data-testid`.
  Neither can be asserted under the testid-only/no-fallback policy without
  adding new testids, which is out of scope here for the same reason as
  above. The other two Axis-2 additions (PATCH 201 assertion, reload-verified
  removal) are implemented as specified.

## Known Defects Found During Exploration
- None (no product defect). One case-text-drift **CLARIFICATION** filed:
  [EliteaAI/elitea-testing-public#530](https://github.com/EliteaAI/elitea-testing-public/issues/530)
  ("Found while working #70") — the case describes a "tabs" UI paradigm (steps
  3–6) and an explicit agent-level Save step (step 8) that don't match the live
  product's 4-independent-buttons + auto-save behavior. Per the reverse-masking
  guard, the live product is correct and the case text is stale — this AFS
  asserts the live contract (§ Test Steps 3, 4, 7) rather than the stale case
  text.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`), following the
  existing `automation/pages/agent_detail_page.py` toolkit-attach pattern.
- Reuse `components.mui.Popper` / `components.mui.Dialog` shared helpers — do
  not write new popper/dialog handling for MCP, it's the identical component.
- New page-object method needed: `AgentDetailPage.add_mcp(mcp_name)` (mirrors
  `add_toolkit()`, swapping the button testid) — everything else (`is_toolkit_attached()`,
  `remove_toolkit()`) already generalizes to MCP cards since they share
  `agent-toolkit-card` / `agent-toolkit-delete-button`. Naming: consider whether
  the implementer wants `is_toolkit_attached()`/`remove_toolkit()` renamed/aliased
  to a shared `is_tool_attached()`/`remove_tool()` given they're now confirmed to
  serve both entity types, or left as-is with a docstring note — implementer's call.
- Toolkit fixture available for setup/cleanup if a dedicated (non-shared) MCP is
  preferred over reusing `autotest_remote_mcp_full`: `toolkit_api` fixture +
  `ToolkitAPI` client (see `automation/tests/ui/toolkits/test_mcp_create_remote.py`
  for the create-MCP-via-API pattern, if the implementer wants full test isolation
  rather than reusing a shared project MCP).
