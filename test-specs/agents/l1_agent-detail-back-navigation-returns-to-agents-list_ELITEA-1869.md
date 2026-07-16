# Test Case: Agent listing — back navigation from agent detail returns to Agents list

## Metadata
- **TMS ID**: ELITEA-1869
- **Linked Story**: none
- **Priority**: l1 (critical, per case frontmatter; case body header line says
  "high" — frontmatter is authoritative, noted here as a minor case-text
  inconsistency, not filed as a defect, same pattern as ELITEA-1872)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend), project `Private` /
  `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips
  login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — all 5 case steps executed end-to-end
  against the live system, back navigation works exactly as the case
  describes, list is fully intact post-navigation, zero console errors,
  no product defect found. Precondition ("at least one agent exists")
  satisfied via an **existing** agent already present in the project (6
  agents pre-existed) — per dispatch instructions, the broken
  `AgentAPI.create_agent()` / agent-creation pipeline (open defect
  [#524](https://github.com/EliteaAI/elitea-testing-public/issues/524)) was
  **not** exercised and was not needed; the Agents list was not empty, so
  no blocker applies.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- At least one agent exists in the current project. **Confirmed live**: the
  `Private` / project 399 Agents dashboard already contains 6 agents
  (`guardrails_test_agent` ×3, `at_ctx_budget_test_10k`, `Test Agent`,
  `uililulu`) — no new agent needed to be created. The implementer should
  reuse any pre-existing agent (e.g. via the `agent_id` fixture, if it
  resolves to an existing/reusable agent in the target project) rather than
  routing through the broken create-agent helpers.

## Test Data
### reuse-existing
- Any existing agent in the project's Agents list. This run used
  **`Test Agent`** (agent id `3`) — a pre-existing fixture-seeded agent, not
  created or deleted by this analysis run. No disposable test data was
  generated; nothing to clean up (see § Cleanup).

## Test Steps
1. Navigate to `${BASE_URL}/agents/all`.
   - **Verify — PASSES.** Agents dashboard loads (`Page Title: "Agents: all
     - project_user_659"`); the Agents list renders in card view with all 6
     pre-existing agents visible, plus the "Agents: 6 / Published: 0" tag
     panel counter on the right.
2. Click into an existing agent card (`Test Agent`) to open its detail page.
   - **Verify — PASSES.** Navigates to
     `/agents/all/3?viewMode=owner&name=Test%20Agent`; agent detail page
     renders (`Page Title: "Agent: Test Agent - project_user_659"`), General
     / Instructions / Welcome message / Tools / Skills / Advanced /
     Editor Notes / Information sections all populate correctly for agent
     id `3`.
3. Click the Back button (`data-testid="back-button"`, top-left of the
   detail page header, confirmed present and visible via
   `document.querySelector('[data-testid="back-button"]')` before
   clicking) — equivalent to the existing page-object method
   `AgentDetailPage.click_back_button()` / `AgentPage.click_back_button()`.
   - **Verify — PASSES.** Browser navigates to
     `/agents/all?viewMode=owner` (URL confirmed via Playwright MCP page
     state).
4. Verify the Agents dashboard is shown.
   - **Verify — PASSES.** `Page Title: "Agents: all - project_user_659"`;
     the "Agents" header and Import / view-toggle toolbar are present —
     same DOM shape as the initial Step-1 load, not the Chat page or any
     other unrelated route.
5. Verify the list is intact (not blank, not redirected to Chat or another
   page).
   - **Verify — PASSES.** All 6 agents from Step 1 are present, in the same
     order (`guardrails_test_agent` ×3, `at_ctx_budget_test_10k`,
     `Test Agent`, `uililulu`); the "Agents: 6" tag-panel counter matches
     the pre-navigation count exactly. Confirmed via network log: `GET
     /api/v2/elitea_core/applications/prompt_lib/399?agents_type=classic&…`
     → `200 OK` — the list is freshly re-fetched, not a stale cached blank
     state. Zero console errors or warnings at any point across Steps 1–5
     (`browser_console_messages` — Errors: 0, Warnings: 0 throughout).

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture (localhost `VITE_DEV_TOKEN`) | n/a (fixture-level) | asserted |
| Precondition: at least one agent exists in project | Agents list non-empty | pre-existing project state (6 agents) | Step 1 list render | asserted (existing data reused, no create-agent workaround needed) |
| Step 1: navigate to Agents page | Dashboard loads, list displays | Step 1 | page title, card list render, "Agents: 6" counter | asserted |
| Step 2: click into any agent card | Detail page opens | Step 2 | URL `/agents/all/3?...`, page title, section render | asserted |
| Step 3: click Back button in detail page header | Navigation triggered to previous page | Step 3 | URL becomes `/agents/all?viewMode=owner` | asserted |
| Step 4: verify Agents dashboard is shown | Dashboard visible | Step 4 | page title, header/toolbar DOM shape matches Step 1 | asserted |
| Step 5: verify list is intact (not blank, not redirected elsewhere) | List fully rendered with all previously visible agents | Step 5 | agent names + count match Step 1 exactly; re-fetch `GET .../applications/...` → `200` | asserted |
| Expected Final State: user on Agents dashboard, list intact, not redirected to Chat/other page | — | Steps 4–5 | URL + list content + counter | asserted |
| Pass/Fail: "all steps complete without errors" | No errors | Steps 1–5 | console error/warning check at each step (0 throughout) | asserted |
| Pass/Fail: "redirected elsewhere OR list blank = FAIL" (negative condition) | n/a | Step 5 | exact agent-name-list comparison, not just "list non-empty" | asserted |

### Axis 2 — observables asserted beyond the case text

- URL assertion (`/agents/all?viewMode=owner` post-back, vs. `/agents/all/3?viewMode=owner&name=...` pre-back) — *added: the case's expected results are UI-visual ("Agents dashboard is shown"); the URL is a stronger, less-flaky signal that this app's actual back-navigation target is the list route and not e.g. a client-side-only view swap that leaves a stale detail URL.*
- Exact agent-name-list equality (order + count) between pre-navigate and post-back states, not just "list is non-empty" — *added: the case's Step 5 says "not blank" which a weak `count > 0` check would satisfy even if the back button silently dropped an agent or reordered the list; comparing the full name list is the honest version of "list intact".*
- Network-level re-fetch confirmation (`GET /api/v2/elitea_core/applications/prompt_lib/399?agents_type=classic...` → `200`) after Back — *added: distinguishes "list is intact because it was correctly re-fetched" from "list looks intact because the DOM was never unmounted" (a subtly different, less robust implementation the case text can't distinguish from the outside).*
- Zero console errors/warnings check across all 5 steps (project convention, `test-case-analysis` § Anti-patterns — never skip the side-channel check even when the UI looks fine) — clean this run.

## Cleanup
None required. This run used a pre-existing project agent (`Test Agent`, id
`3`) read-only — no agent was created, edited, or deleted. No test data was
generated and nothing needs teardown.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Status |
|---|---|---|---|
| Back button (agent detail page header) | `data-testid="back-button"` — confirmed present/visible via DOM query before click; already wired to `AgentDetailPage.back_button` / `AgentDetailPage.click_back_button()` (`automation/pages/agent_detail_page.py:187,2130-2138`), also exposed via the `AgentPage` facade (`automation/pages/agent_page.py:254-256`) | none needed — testid pre-exists project-wide (also used by `BackButton.jsx`, a shared component reused across multiple entity-detail pages) | pre-existing |
| Agents dashboard header | existing `AgentsListPage.page_header` (`testid="agents-page-header"`) | none | pre-existing |
| Agent card (click into detail) | existing `AgentsListPage.select_agent(name)` — **note:** this pre-existing method uses a raw `page.locator(f'text="{name}"')`, not a `data-testid` (`automation/pages/agents_list_page.py:209-220`); it predates the current testid-only locator policy (`.claude/rules/page-objects.md`). Not a new gap introduced by this case — flagging for the implementer/lead rather than blocking this AFS, since the case only needs to *reuse* the existing method, not add a new locator. | none currently | pre-existing (policy-noncompliant, informational only) |
| Agent list card names (post-back verification) | existing `AgentsListPage.get_agent_card_names()` (`automation/pages/agents_list_page.py:171-188`) — same testid caveat as above (uses `[class*="CardContent"]` CSS selector, not testid) | none currently | pre-existing (policy-noncompliant, informational only) |

No new testids were required for this case — the Back button, dashboard
header, and list-reading helpers all already exist and were exercised live.
The two "policy-noncompliant" notes above are pre-existing technical debt
in `AgentsListPage`, out of scope for this AFS to fix (this case doesn't
touch new UI surface), but worth the implementer/lead knowing about if a
future `add-data-testid` pass targets agent cards.

## Network Behavior
- `GET /api/v2/elitea_core/applications/prompt_lib/399?agents_type=classic&sort_by=created_at&sort_order=desc&query=&limit=20&offset=0` — fires on both the initial Step 1 navigate AND again after the Step 3 Back click; `200 OK` both times. This is the implementer's strongest wait signal for "list has re-loaded" post-back (wait for this response, or for `networkidle`, before asserting list contents — don't assert immediately on URL change).
- `GET /api/v2/elitea_core/application/prompt_lib/399/{id}` — fires once on Step 2 (agent detail fetch), confirming detail page loaded real data before Back is clicked.

## Known Defects Found During Exploration
None found. The feature under test (Back-button navigation from agent
detail to Agents dashboard, list intact) works exactly as the case
describes — no reverse-masking, no functional defect, no clarification
needed. (Unrelated to this case: the project-wide agent-creation defect
[#524](https://github.com/EliteaAI/elitea-testing-public/issues/524) was
not encountered because this case's precondition was satisfied by an
existing agent, per dispatch instructions — not re-triggered, not
re-confirmed, not applicable to this AFS.)

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md` / `automation/CLAUDE.md`).
- Page objects: `AgentsListPage` (`automation/pages/agents_list_page.py`) for
  Steps 1, 4, 5; `AgentDetailPage` / `AgentPage` facade
  (`automation/pages/agent_detail_page.py`, `automation/pages/agent_page.py`)
  for Steps 2–3. `AgentPage.click_back_button()` already delegates to
  `AgentDetailPage.click_back_button()` — use the facade if the test also
  needs list-page methods, or `AgentDetailPage` directly if only detail-page
  methods are needed (see `.claude/rules/ui-tests.md` § Which Page Object to
  Import).
- Suggested test-data approach: do **not** use the `agent_id` fixture — it
  unconditionally calls `agent_api.create_agent(...)`
  (`automation/fixtures/data_fixtures.py:77-103`) and always creates a
  fresh agent; it does not reuse an existing one, so it walks straight
  into the broken create-agent path (open defect #524 — 400 error,
  temperature/reasoning_effort conflict). Instead, resolve an existing
  agent id directly — e.g. query the agents list API/page for any
  pre-existing agent in the target project (the same approach this
  analysis run used: `Test Agent`, id `3`, project 399) — this case's
  precondition only requires an *existing* agent, not a *fresh* one, so
  the #524 create-agent defect does not block this case as long as the
  fixture is avoided.
- Wait strategy: after clicking Back, wait for the
  `applications/prompt_lib/399?agents_type=classic...` response (or
  `wait_for_network()` / networkidle) before asserting on
  `get_agent_card_names()` — asserting immediately on URL change risks a
  race against the re-fetch.
- Suggested assertion: capture `get_agent_card_names()` (or equivalent) once
  before Step 2's navigation and once after Step 3's Back click; assert list
  equality (not just non-empty) per Axis 2 above.
