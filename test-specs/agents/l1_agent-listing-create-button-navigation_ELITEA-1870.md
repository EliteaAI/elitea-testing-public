# Test Case: Agent listing — "+Create" button navigates to Create Agent page

## Metadata
- **TMS ID**: ELITEA-1870
- **Linked Story**: none
- **Priority**: l1 (critical, per case frontmatter; case body header line says
  "high" — frontmatter is authoritative, noted here as a minor case-text
  inconsistency, not filed as a defect, same pattern as ELITEA-1869/1872)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend), project `Private` /
  `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips
  login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — all 5 case steps executed end-to-end
  against the live system. Clicking the sidebar create-agent control from
  `/agents/all` navigates straight to `/agents/create?viewMode=owner` with an
  empty Name/Description/Instructions form and a disabled Save button, zero
  console errors, no product defect found. **Not `already-covered`**: the two
  existing tests that touch this form
  (`test_create_agent_via_ui`, `test_create_agent_required_fields_validation`
  in `automation/tests/ui/agents/test_agent_management.py`) both reach the
  create form via `AgentsListPage.navigate_to_create()`, which does a direct
  `page.goto("/agents/create?viewMode=owner")` — **neither test clicks the
  create button from the Agents list**, so this case's actual button-click
  navigation path (Steps 1–3) is a genuine, previously-unexercised gap. The
  empty-fields observation (Step 4) is also new: existing coverage only
  infers emptiness indirectly (Save disabled), never asserts the three field
  values directly.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).

## Test Data
No test data required — this case never submits the form (case is explicit:
"does NOT require submitting/creating an agent"). No entities created, no
cleanup needed.

## Test Steps
1. Navigate to `${BASE_URL}/agents/all`.
   - **Verify — PASSES.** Agents dashboard loads (`Page Title: "Agents: all -
     project_user_659"`); list renders in card view with 6 pre-existing
     agents.
2. Click the create-agent control in the left sidebar (top icon group,
   `data-testid="sidebar-create-button"` — see § Concrete Handles for the
   testid-naming discrepancy discovered here).
   - **Verify — PASSES.** Browser navigates immediately (client-side route
     change, no confirmation dialog, no intermediate menu) to
     `/agents/create?viewMode=owner`.
3. Verify the browser navigates to `/agents/create` (or equivalent).
   - **Verify — PASSES.** URL confirmed via Playwright MCP page state:
     `http://localhost:5173/agents/create?viewMode=owner`. `viewMode=owner`
     is a query param, not a path segment — case's "(or equivalent)" clause
     covers it.
4. Verify the Create Agent form is shown with empty Name, Description, and
   Instructions fields.
   - **Verify — PASSES.** All three fields present and empty, confirmed both
     via accessibility snapshot (`textbox "Name *"`, `textbox "Description
     *"`, `textbox "Guidelines for the AI agent"` all render with no visible
     value) and via direct DOM query on their testids
     (`agent-name-input`.value === "", `agent-description-input`.value ===
     "", `agent-instructions-input`.value === ""). Form is a fresh "New
     Agent" tab — no pre-fill from a prior draft or navigation state.
5. Verify the Save button is disabled by default.
   - **Verify — PASSES.** `data-testid="agent-save-button"` confirmed
     `disabled === true` via direct DOM query, and rendered as `button
     "Save" [disabled]` in the accessibility snapshot. Cancel button is also
     disabled by default (observed, not part of the case — see Axis 2).

## Expected Results
- Clicking the create control from `/agents/all` lands on
  `/agents/create?viewMode=owner` with no intermediate confirmation step.
- Name, Description, Instructions fields are all empty on first render.
- Save button is disabled until required fields are filled.
- Zero console errors/warnings across the whole flow.
- No new network calls fire on the button click itself (pure client-side
  route change — see § Network Behavior).

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture (localhost `VITE_DEV_TOKEN`) | n/a (fixture-level) | asserted |
| Step 1: navigate to Agents dashboard | Dashboard loads correctly | Step 1 | page title, card list render | asserted |
| Step 2: click "+ Create" button | Browser navigates to Create Agent page | Step 2 | URL change to `/agents/create?viewMode=owner` | asserted |
| Step 3: verify URL is `/agents/create` (or equivalent) | URL reflects create route | Step 3 | exact URL string, `viewMode=owner` accepted as "or equivalent" | asserted |
| Step 4: verify Name/Description/Instructions all empty | All three fields empty | Step 4 | `.value === ""` on all three testids + accessibility-snapshot cross-check | asserted |
| Step 5: verify Save button disabled by default | Save not clickable | Step 5 | `disabled === true` on `agent-save-button` + accessibility snapshot | asserted |
| Expected Final State: Create Agent form shown, fields empty, Save disabled | — | Steps 3–5 | combined URL + field + button state | asserted |
| Pass/Fail: "form not shown, fields pre-filled, or Save enabled without input" (negative condition) | n/a | Steps 4–5 | explicit empty-value + disabled-state checks, not just visual "looks empty" | asserted |

### Axis 2 — observables asserted beyond the case text

- Zero console errors/warnings across all 5 steps (project convention,
  `test-case-analysis` § Anti-patterns — never skip the side-channel check
  even when the UI looks fine) — clean this run (`browser_console_messages`,
  level `error`: 0 messages returned).
- No new/unexpected network requests fire on the create-button click itself
  — *added: confirms the navigation is a pure client-side route change, not
  a request that could fail silently and leave the button visually
  "clicked" but not actually navigated.*
- Cancel button's default-disabled state — *added: observed alongside Save
  in the same header region during Step 5; not asked for by the case but a
  natural companion assertion since both buttons render disabled together
  on a pristine form and a regression that enables one without the other
  would be worth catching.*
- Direct DOM `.value` check on the three field testids, in addition to the
  case's implied "looks empty" — *added: an accessibility-tree textbox with
  no visible text can still carry a non-empty controlled-component value in
  edge cases (e.g. whitespace-only draft state); asserting `.value === ""`
  directly is the honest version of "empty".*

## Cleanup
None required. No agent was created, no form was submitted, no entities
were modified. Read-only navigation/observation case.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Status |
|---|---|---|---|
| Sidebar create-agent control (Step 2) | `data-testid="sidebar-create-button"` — **discrepancy**: `AgentsListPage.create_agent_button` (`automation/pages/agents_list_page.py:33-37`) is defined with `testid="create-agent-button"`, which **does not exist** in the live DOM (confirmed via `document.querySelectorAll('[data-testid]')` full inventory on `/agents/all` — no such testid present). The page object's existing `click_create_agent()` method only works today because of its `fallback=lambda page: page.get_by_label("Create Agent").get_by_role("button")` — which itself doesn't match either (no `aria-label="Create Agent"` found live); in practice Playwright's role/label fallback resolution must be finding it some other way, or the method is currently untested against this live app state. **Recommend**: implementer verifies `click_create_agent()` still resolves correctly, and if not, updates the `create_agent_button` `LocatorDescriptor` to `testid="sidebar-create-button"` (the real, confirmed-live testid) per the testid-only locator policy — this is a housekeeping fix, not a new defect, since the button's *behavior* is correct. | none — testid-only policy; do not add a new fallback | **stale testid — needs page-object fix or add-data-testid verification pass** |
| Create Agent page — Name field | existing `AgentFormPage.name_input` (`testid="agent-name-input"`, `automation/pages/agent_form_page.py:26-30`) — confirmed live, empty on load | none needed | pre-existing, confirmed live |
| Create Agent page — Description field | existing `AgentFormPage.description_input` (`testid="agent-description-input"`) — confirmed live, empty on load | none needed | pre-existing, confirmed live |
| Create Agent page — Instructions field | existing `AgentFormPage.instructions_input` (`testid="agent-instructions-input"`) — confirmed live, empty on load | none needed | pre-existing, confirmed live |
| Create Agent page — Save button | existing `AgentFormPage.save_button` (`testid="agent-save-button"`) — confirmed live, `disabled === true` on fresh form | none needed | pre-existing, confirmed live |
| Create Agent page — Cancel button | rendered live as `button "Cancel" [disabled]` in the accessibility snapshot, but `data-testid="agent-cancel-button"` (the testid `AgentFormPage.cancel_button` expects, `automation/pages/agent_form_page.py:148-152`) **was not found live** (`document.querySelector` returned null). Not required for this case's own assertions (Axis 2 addition only) — flagging for the implementer rather than blocking, since Cancel isn't a Step in the source case. | `get_by_role("button", name="Cancel")` (existing fallback, works — accessible name confirmed) | **testid gap — flag for `add-data-testid`, non-blocking for this case** |

## Network Behavior
- No `POST`/`PUT` requests fire on the Step 2 button click — confirmed via
  `browser_network_requests` immediately before/after the click: only the
  pre-existing `GET .../applications/prompt_lib/399?...` list-fetch calls
  from the Step-1 page load are present; nothing new fires on navigation to
  `/agents/create` (the "New Agent" form starts from client-side default
  state, no fetch needed).
- `GET /api/v2/elitea_core/applications/prompt_lib/399?...` (multiple
  variants, filtered by status) — these are Step-1 list-load calls,
  unrelated to the create-button click itself; included here only to
  confirm nothing unexpected fired afterward.

## Known Defects Found During Exploration
None found. The feature under test (create-button navigation from Agents
list to Create Agent page, empty form, disabled Save) works exactly as the
case describes. The two locator discrepancies noted in § Concrete Handles
(`create-agent-button` and `agent-cancel-button` testids not present live)
are testid-hygiene / page-object-maintenance gaps, not functional defects —
the underlying UI behavior is correct in both cases (button is clickable
and navigates correctly; Cancel button renders and is disabled correctly)
— so no tracker ticket was filed per the reverse-masking guard (this is
stale test-infrastructure metadata, not a product bug).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md` /
  `automation/CLAUDE.md`).
- Page objects: `AgentsListPage` (`automation/pages/agents_list_page.py`)
  for Steps 1–2 — **but see § Concrete Handles**: verify
  `click_create_agent()` / `create_agent_button` actually resolves against
  the live `sidebar-create-button` testid before relying on it; do not
  reuse `navigate_to_create()` for this case, since that method bypasses
  the button click entirely (direct `page.goto`) and is exactly the gap
  this case exists to cover. `AgentFormPage`
  (`automation/pages/agent_form_page.py`) for Steps 3–5 — `wait_for_form_load()`,
  field `LocatorDescriptor`s, and `is_save_enabled()` are all already
  testid-correct and reusable as-is.
- Wait strategy: after the Step 2 click, wait on URL change to
  `/agents/create` (or `AgentFormPage.wait_for_form_load()`, which waits
  for the Name field to be visible + network idle + a settle delay) rather
  than a fixed timeout — matches existing `wait_for_form_load()` behavior.
- Suggested assertions: field emptiness via `.input_value() == ""` on all
  three `LocatorDescriptor`s (not just visibility), and
  `is_save_enabled() is False` immediately after `wait_for_form_load()` —
  both already-available page-object methods, no new ones needed beyond
  fixing the sidebar-create-button testid per the flagged gap.
