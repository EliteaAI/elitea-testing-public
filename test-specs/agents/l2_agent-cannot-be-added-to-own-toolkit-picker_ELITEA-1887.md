# Test Case: Agent Cannot Be Added to Its Own Toolkit Picker (Self-Attachment Blocked)

## Metadata
- **TMS ID**: ELITEA-1887
- **Linked Story**: none
- **Priority**: l2 (medium, per case metadata)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — executed end-to-end live, self-exclusion
  confirmed both by observed UI behavior and by reading the source filter
  (`ToolMenu.jsx:401`). One new testid added (`agent-add-agent-button`, pushed
  straight to `automation/testids`, commit `ce74cd40`) — no defect found.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- An existing agent is available in the project — used the seeded "Test Agent"
  (agent id `3` in this run, `/agents/all/3`), same agent reused by the
  ELITEA-1950 AFS.

## Test Data

### reuse-existing
- Agent under test: "Test Agent" (id `3`), any existing, already-saved agent in
  the project works — the flow is agent-agnostic (case-text confirms "an
  existing agent"). The agent must be saved (not a new/unsaved draft) — the
  Tools-section add buttons are disabled until the entity has an id
  (`isEntityUnsaved` guard in `ToolMenu.jsx`).

No `generate-per-test` data is needed — this is a pure read/search flow; it
creates no persistent entity and requires no cleanup.

## Test Steps

1. Navigate to `${BASE_URL}/agents/all/3?viewMode=owner`. Agent detail page loads.
   - **Verify — PASSES.** Page loads; Information section shows Agent ID `3`,
     General section shows Name `Test Agent`.
2. Scroll to the "Tools" accordion section (`agent-toolkits-section` testid,
   already expanded by default) and click the "+ Agent" add button
   (`agent-add-agent-button` — **testid added this run**, pushed to
   `automation/testids`, commit `ce74cd40`; previously text/role-only,
   matching ELITEA-1950's finding that the Agent/Pipeline buttons lacked
   testids at that time).
   - **Note on case-text interpretation**: the case's literal step 2 says
     'Click "+ Toolkit" to open the toolkit picker' and its step 3 says
     'Search for the current agent's own name'. The live product's Tools
     section has **four independent add buttons** — Toolkit / MCP / Agent /
     Pipeline (confirmed, same 4-button layout as ELITEA-1950) — and only the
     **"+ Agent"** button's popper lists other agents (searchable by agent
     name) that could be attached as a sub-agent tool. The "+ Toolkit"
     button's popper lists Toolkit-type entities only (confirmed live: with
     zero toolkits in this project, it showed "No toolkits available",
     disabled, unrelated to agents at all — searching an agent's name there
     is not a meaningful test of self-attachment). This AFS asserts the
     live-accurate equivalent of the case's intent — self-attachment via the
     **Agent** picker — not the literal "Toolkit" label. See
     § Known Defects for the CLARIFICATION filed on this case-text drift.
   - **Verify — PASSES.** A `UnifiedDropdown`-style popper opens directly with
     a "Search agents..." input and a list of other project agents (observed:
     `at_ctx_budget_test_10k`, `autotest GH Issue Bot 601356`, `el-1893-agent-*`,
     `guardrails_test_agent` ×3, `uililulu`, etc. — the current agent, "Test
     Agent", is **not** in this initial unfiltered list either).
3. Type the current agent's own name ("Test Agent") into the popper's search
   input.
   - **Verify — PASSES.** Debounced (`useDebounceValue`, 200ms) server-side
     search fires `GET /api/v2/elitea_core/applications/prompt_lib/399?agents_type=classic&sort_by=created_at&sort_order=desc&query=Test+Agent&limit=20&offset=0`
     → `200 OK`.
4. Verify the current agent ("Test Agent") does NOT appear in the popper's
   result list.
   - **Verify — PASSES, with a load-bearing technical detail worth asserting
     explicitly in automation.** The backend response for the query above
     actually **does** include the self-agent (`{"total": 1, "rows": [{"id": 3,
     "name": "Test Agent", ...}]}` — confirmed via
     `browser_network_request` on the exact call). The UI nonetheless renders
     **"No agents found"** (a disabled `role="menuitem"` item, no
     `data-testid`). This is because self-exclusion is applied **client-side**,
     not server-side: `EliteaUI/src/pages/Applications/Components/Tools/ToolMenu.jsx`
     line 401, `agentMenuItems` — `agentsData.rows.filter(agent => agent.id !==
     applicationId)` (also line 402 excludes swarm agents). This means the
     absence-assertion is NOT equivalent to "the search API returned zero
     rows" — an automation test that only checks the API response would give
     a false negative (or worse, false positive if the filter regresses) for
     this behavior. The DOM-level check (no menuitem with accessible name ==
     the agent's own name) is the correct assertion target, not the network
     response.

## Expected Results
- The "+ Agent" toolkit picker never lists the currently-open agent among its
  search results, regardless of search term (confirmed both unfiltered and
  filtered by the agent's exact own name).
- Self-exclusion is enforced entirely client-side (`ToolMenu.jsx:401`); the
  backend `GET .../applications` endpoint does NOT exclude the requesting
  agent from its own search results — this is a UI-layer guard, not an API
  contract. (Informational for the implementer; not something to assert on
  the network layer, since asserting DOM absence is the correct/available
  handle and doesn't depend on knowing implementation internals.)
- No console errors attributable to the search/popper flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to an agent detail page | Agent detail page loads | step 1 | `step 1`: Information section shows Agent ID `3`, General section shows Name | asserted |
| 2 Click "+ Toolkit" to open the toolkit picker | Toolkit picker dialog opens | step 2 | `step 2`: popper opens with "Search agents..." input | clarification *(case says "+ Toolkit"; live-accurate target is the "+ Agent" button — the "+ Toolkit" popper lists Toolkit-type entities, unrelated to agent self-attachment. See § Known Defects for the filed CLARIFICATION.)* |
| 3 Search for the current agent's own name in the search field | Search results are returned | step 3 | `step 3`: debounced `GET .../applications?...query=Test+Agent...` fires, `200 OK` | asserted |
| 4 Verify the agent itself does NOT appear in the toolkit picker list | Current agent absent from search results | step 4 | `step 4`: no `role="menuitem"` with accessible name == agent's own name; "No agents found" disabled item shown | asserted |
| Expected Final State: current agent does not appear in its own toolkit picker, preventing self-attachment | — | step 4 | `step 4` | asserted |

### Axis 2 — Analyst additions

- `step 2` asserts the current agent is absent from the **unfiltered** popper
  list too (before any search term is typed) — *added: proves the exclusion
  isn't an artifact of the search/debounce path specifically; it holds for
  the base list render.*
- `step 4` asserts the DOM-level menu-item absence rather than only the
  network response emptiness — *added: source read
  (`ToolMenu.jsx:401`) proved the backend actually returns the self-agent row
  and the UI filters it client-side. An assertion coupled to the API response
  being empty would be asserting the wrong contract and would pass/fail for
  the wrong reason if either layer changes independently.* See § Test Steps
  step 4 for the full technical detail.

## Cleanup
None. This flow creates no persistent entity and mutates no state — pure
read/search against an existing agent.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Tools accordion section | `LocatorDescriptor(testid="agent-toolkits-section")` (existing, `AgentDetailPage.toolkits_section`) | none — testid-only policy |
| "+ Agent" add button | `LocatorDescriptor(testid="agent-add-agent-button")` — **added this run**, pushed to `automation/testids` commit `ce74cd40` | none |
| Agent add popper | `components.mui.Popper` (existing shared helper — same component family as Toolkit/MCP/Skill poppers) | none |
| Agent popper search input | scoped inside popper: `[data-testid="toolkit-search-input"]` (existing, shared `UnifiedDropdown` wrapper — confirmed live via DOM ancestor walk: the "Search agents..." `<input>` sits inside a `MuiFormControl` carrying this testid, same as the Toolkit/MCP poppers per ELITEA-1950) | none |
| Agent popper menu item (select by name) | `Popper.select_menuitem(popper, agent_name, page)` (existing shared helper, already used by `add_toolkit()`/MCP flow — menu items render `role="menuitem"` with the agent's name as accessible text, no per-item testid, same established pattern as Toolkit/MCP/Skill poppers) | none |
| Agent popper empty-state item ("No agents found") | `page.get_by_role("menuitem", name="No agents found")` scoped inside the popper — no `data-testid` on this disabled item (confirmed via DOM query, `role="menuitem"` `aria-disabled="true"`, no `data-testid` attribute) | none — **primary assertion should be item-absence by name, not empty-state-text presence** (see § Automation Hints); this handle is a secondary/defensive check only |

**Recommendation for the implementer:** the primary assertion for step 4 is
**absence** of a menu item whose accessible name equals the agent's own name
(`page.get_by_role("menuitem", name=agent_name)` inside the popper scope,
assert count == 0 / not visible) — this doesn't depend on the "No agents
found" empty-state text existing or being stable copy. Use the empty-state
text as a secondary/defensive assertion only, since it has no testid and its
exact copy could change independently of the self-exclusion behavior under
test.

## Network Behavior
- `GET /api/v2/elitea_core/applications/prompt_lib/399?agents_type=classic&sort_by=created_at&sort_order=desc&query=Test+Agent&limit=20&offset=0`
  — fires (debounced 200ms) when the popper search input changes, `200 OK`.
  **Response body includes the self-agent row** (`{"total": 1, "rows":
  [{"id": 3, "name": "Test Agent", ...}]}` in this run) — the backend does
  NOT filter self out. This is the key finding: automation must NOT assert
  against this response being empty; it must assert the DOM after the
  client-side filter (`ToolMenu.jsx:401`) has run. See § Test Steps step 4.
- No console errors observed attributable to this flow (7 total console
  messages this session, 0 errors, 0 warnings).

## Known Defects Found During Exploration
- None (no product defect — self-attachment IS correctly blocked, confirmed
  both live and via source). One case-text-drift **CLARIFICATION** posted as
  a work-log comment on the tracking issue
  ([EliteaAI/elitea-testing-public#133](https://github.com/EliteaAI/elitea-testing-public/issues/133)):
  the case's steps 2–3 say '"+ Toolkit"' as the button to click and picker to
  search, but the live product's Toolkit-type add button opens a picker
  scoped to Toolkit entities only (not agents) — the picker that actually
  lists other agents (and could theoretically allow self-attachment) is the
  separate "+ Agent" add button. Per the reverse-masking guard, the live
  product's 4-independent-add-button design is correct and the case text is
  stale/imprecise about which button; this AFS asserts the live-accurate
  target (the Agent picker) rather than the literal "Toolkit" label.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`), following the
  existing `automation/pages/agent_detail_page.py` toolkit/MCP-attach pattern
  (`add_toolkit()` / `add_mcp()`).
- New page-object method needed: `AgentDetailPage.search_agent_picker(query)`
  (or similar) — clicks `agent-add-agent-button`, types into the
  `toolkit-search-input`-scoped input inside the resulting popper, and
  returns/exposes the popper for the caller to assert on
  (`is_agent_in_picker(agent_name) -> bool`, implemented as a
  `get_by_role("menuitem", name=agent_name)` visibility check, per
  § Concrete Handles).
- Reuse `components.mui.Popper` shared helper — same popper component as
  Toolkit/MCP/Skill.
- Test does NOT need to attach anything or reload — it's a pure
  search-and-assert-absence flow, no state mutation, no cleanup.
- Recommended assertion shape:
  1. Open the Agent picker (unfiltered) → assert the current agent's name is
     absent from the initial list.
  2. Type the agent's exact own name into the search input → wait for the
     debounced network response (`wait_for_response` matching
     `/applications/prompt_lib/.*query=<encoded-name>/`) → assert the current
     agent's name is still absent from the rendered menu items (DOM-level,
     not network-level — see § Network Behavior).
- Optional stretch (not required by the case, out of scope for this AFS):
  the same `ToolMenu.jsx:401`-style self-exclusion pattern likely exists for
  Pipelines too (pipelines are also `type: 'application'` entities per
  `useFilterAddedItems.js`) — not verified in this run since the case only
  covers Agent self-attachment; a follow-up case could target Pipeline
  self-attachment if that's ever authored.
