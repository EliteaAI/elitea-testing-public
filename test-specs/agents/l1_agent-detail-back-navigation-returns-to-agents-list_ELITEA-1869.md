# Test Case: Agent listing — back navigation from agent detail returns to Agents list

## Metadata
- **TMS ID**: ELITEA-1869
- **Linked Story**: none
- **Priority**: l1 (critical, per case frontmatter; case body header line says
  "high" — frontmatter is authoritative, noted here as a minor case-text
  inconsistency, not filed as a defect, same pattern as ELITEA-1872)
- **Environment Explored**: **`https://dev.elitea.ai` (`APP_PREFIX=/app`)**,
  project `Private` / `${ELITEA_PROJECT_ID}`=399. *(2026-09-10 adjustment pass.
  The original 2026-07 pass explored `http://localhost:5173`.)*
- **User set**: `${TEST_USER}` (Keycloak; storage state obtained via
  `api_auth.get_playwright_storage_state`, the same path `auth_state` uses on
  deployed envs)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — **ADJUSTMENT** of an already-merged test
  (`tests.ui.agents.test_agent_back_navigation.test_back_button_from_agent_detail_returns_to_intact_agents_list`)
  that went red on DEV. **Triage class A — UI drift (intentional product
  change).** No product defect. All 5 case steps re-executed end-to-end against
  DEV, twice consecutively, both clean. Repair is fully specified below; nothing
  blocks it and no new testid is required.
- **Tracking card**: EliteaAI/elitea-testing-public#2145 (`[FIX][ELITEA-1869]`)
- **Failing CI run**: 34331579791 (DEV Stable #114), 3/3 retries identical —
  `playwright._impl._errors.TimeoutError: Locator.click: Timeout 10000ms
  exceeded … waiting for get_by_test_id("back-button")` at Step 3.

---

## Adjustment (2026-09-10) — what changed in the product and what the repair does

### Triage class: **A — UI drift (intentional product change)**

**Root cause, confirmed live.** EliteaUI `origin/main` commit
`f1d4ea47` (2026-09-01, *feat: [EL-6460] Add Breadcrumb Navigation to Agent,
Pipeline, and Skill Details Pages (#884)*) introduced
`src/[fsd]/shared/ui/breadcrumbs/BreadcrumbsOrTitle.jsx`, whose entire body is a
binary switch:

```jsx
// BreadcrumbsOrTitle.jsx:16-29
{hasBreadcrumbTrail ? (
  <Breadcrumbs />
) : (
  <>
    <BackButton />                                {/* data-testid="back-button" */}
    <Typography ... data-testid={testId}>{title}</Typography>
  </>
)}
```

`src/pages/Applications/EditApplication.jsx:133` renders the agent detail header
through it (`leftPart={<BreadcrumbsOrTitle title={…} />}`).
`useHasBreadcrumbTrail()` (`useBreadcrumbTrail.hooks.js:55-59`) is purely
pathname-based, and `BREADCRUMB_REGISTRY` (`breadcrumb.constants.js:60-65`)
declares `ApplicationsDetail` with `parent: ApplicationsWithTab`, so on
`/agents/:tab/:agentId` the trail is **always** non-empty (2 crumbs) no matter
how the user arrived. ⇒ the `BackButton` branch is **unreachable** on the agent
detail route, and `data-testid="back-button"` never mounts there.

That fully and deterministically explains the 3/3-identical CI failure. It is
**not** the run-34331579791 gateway-500 outage: the `agents` job selected 30
tests and only 4 failed, and this failure reproduces on a healthy DEV today.

**Not a promotion gap (class F ruled out).** Fresh `git -C ../EliteaUI fetch
origin`, then the closure-record grep — every testid this case touches is on
**both** refs:

```
back-button              main:YES  testids:YES
breadcrumbs              main:YES  testids:YES
breadcrumb-item          main:YES  testids:YES
breadcrumb-current       main:YES  testids:YES
agent-detail-title       main:YES  testids:YES
agents-page-header       main:YES  testids:YES
entity-card-name         main:YES  testids:YES
```

`back-button` is *present in source, unreachable at runtime on this route* —
the opposite of a promotion gap.

**Not a product bug (class B/C ruled out).** The intended affordance per `src/`
is the breadcrumb trail, and it works: the ancestor crumb navigates to the
Agents dashboard with the list intact and zero console errors. Per
`.agents/role-overrides.md` § interaction-discovery ladder, the source is the
decisive step and it states the intended mode as fact.

**Not data pollution / flake (class D ruled out).** Deterministic across 3
independent DEV sessions; the element count is 0, not intermittently 0.

### The replacement control

| | Before (≤ f1d4ea47) | After (current) |
|---|---|---|
| Header markup | `<BackButton/>` + title | `<nav data-testid="breadcrumbs">` |
| Go-back affordance | arrow button, `data-testid="back-button"` | ancestor crumb link **"Agents"**, `data-testid="breadcrumb-item"` |
| Navigation mechanism | history back | react-router `<Link to>` (client-side, no reload) |
| Landing URL | `/agents/all?viewMode=owner` | `/agents/all?viewMode=owner&name=<agent name>` |

Observed markup on DEV (verbatim, `/app/agents/all/9433`):

```html
<ol><li><a data-testid="breadcrumb-item"
           href="/app/agents/all?viewMode=owner&name=Echo%20Agent">Agents</a></li>
    <li><span aria-hidden="true">/</span>
        <span aria-current="page" data-testid="agent-detail-title">Echo Agent</span></li></ol>
```

### Expected-result changes (declared — this is the section the rail requires)

Exactly **one** assertion changes, and it is an Axis-2 observable the analyst
added, not a case-text expected result:

| | Old | New | Why this is not a weakening |
|---|---|---|---|
| Landing-URL assertion | `page.url.rstrip("/").endswith("/agents/all?viewMode=owner")` | `urlparse(url).path` ends with `/agents/all` **AND** `parse_qs(url)["viewMode"] == ["owner"]` **AND** `"/chat" not in url` | Both facts the old assertion proved (list route, owner viewMode) are still proven, each explicitly. The only thing dropped is the incidental requirement that the query string contain *nothing else* — and the new control legitimately carries `name=<agent name>` through (`Breadcrumbs.jsx:46` passes the current location's `search` into the crumb's `to`). A `/chat` negative is added, matching the case's own Fail criterion. |

**Every case-level expected result is preserved verbatim.** No step deleted, no
comparison weakened, no count lowered, no check made conditional. Two
assertions are *added* (§ Axis 2), one of which is the absence assertion that
makes this very drift test-enforced.

### Robustness fixes (class-D discipline — assertions untouched)

1. **Explicit card-render wait after the crumb click.** Observed live: awaiting
   the `applications/prompt_lib/…agents_type=classic` 200 **plus**
   `wait_for_load_state("networkidle")` still returned an empty card list once
   (`count after: 0`) — networkidle races the persistent `/socket.io/` polling
   transport (`.agents/testing.md` § `networkidle` flake / #1847). Adding
   `entity_card_name.first.wait_for(state="visible")` before reading the names
   made two consecutive runs exact-match. **Wait on what the caller needs, not
   on network silence.**
2. **`AgentDetailPage.click_back_button(timeout=…)` never passes `timeout` to
   `.click()`** — only to the trailing `wait_for_network()`
   (`agent_detail_page.py:4924-4932`). That is why a `NAVIGATION_TIMEOUT=15000`
   argument produced the CI signature's `Timeout 10000ms` (the context default
   from `conftest.py:326`). The new breadcrumb method must propagate
   `timeout` to the click. See § Automation Hints for the disposition of the
   existing method.

### Precedent this repair follows (convention, not deviation)

The identical drift was already analysed and repaired on the **MCP** surface —
`McpFormPage` (ELITEA-1961, CLARIFICATION #1731) declares `breadcrumbs_nav` +
`breadcrumb_parent_link` and keeps `back_button` bound **for an absence
assertion only** (`mcp_form_page.py:325-352`,
`tests/ui/toolkits/test_mcp_back_navigation.py:158-192`). The pipelines surface
uses the same `BREADCRUMB_ITEM_SELECTOR` class constant with a
**count-then-index** guard (`pipeline_detail_page.py:90`, `close_run_history`).
This AFS mirrors both shapes rather than inventing one.

---

## Preconditions
- User is logged in. On DEV: Keycloak / `${TEST_USER}` via the `auth_state`
  fixture; on localhost `auth_state` skips login via `VITE_DEV_TOKEN`.
- At least one agent exists in the current project. **Confirmed live on DEV**:
  project 399 renders a full first page of 20 agent cards; no agent needs to be
  created. Reuse an existing agent — **do not** use the `agent_id` fixture
  (`fixtures/data_fixtures.py`), which unconditionally calls
  `agent_api.create_agent(...)` and walks into open defect
  [#524](https://github.com/EliteaAI/elitea-testing-public/issues/524).
  *(The currently-merged test takes `agent_id`; the repair should drop it —
  see § Automation Hints.)*
- A deployment banner (`Release 2.0.5 — Deployment`, z-index 2400) intercepts
  card clicks on DEV. The autouse `dismiss_banner_after_navigation` fixture
  (`conftest.py:414`) already handles this for tests using the standard `page`
  fixture; no spec-level action needed.

## Test Data
### reuse-existing, read-only
- Any existing agent in the project's Agents list — the **first card** is
  sufficient and is what the merged test already uses. This run used
  `Echo Agent` (agent id `9433`, project 399), a pre-existing agent. Nothing
  created, edited, or deleted; nothing to clean up.

---

## Test Steps

1. **Navigate to `${BASE_URL}/agents/all`.**
   - **Verify — PASSES.** Agents dashboard loads; `agents-page-header` visible;
     the list renders a full page of agent cards. Capture the card-name list
     (`entity-card-name`) as `agents_before`. Observed on DEV: 20 names, backed
     by `GET …/applications/prompt_lib/399?…agents_type=classic&limit=20&offset=0`
     → `200`.
   - Evidence: ![Step 1 — Agents dashboard on DEV](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-1869-step-01-agents-list.png)

2. **Click into an existing agent card to open its detail page** — an **in-app
   click on the card**, never a `page.goto()` deep link.
   - **Verify — PASSES.** URL becomes
     `/agents/all/9433?viewMode=owner&name=Echo%20Agent`;
     `agent-information-section` renders.
   - ⚠️ **The in-app arrival path is load-bearing and must be preserved** —
     `.agents/testing.md` § "A sanctioned RED is only sanctioned if the CASE
     asks…" (ELITEA-2022/#2139): for a back-navigation family, the arrival path
     can be the *producer* of the observable. Substituting a `goto` deep link
     "to reach the precondition faster" is a wrong-interface precondition under
     § Fidelity policy. The case says *click into any agent card*; the test does
     that.

3. **Click the "Agents" breadcrumb — the go-back control in the agent detail
   page header** *(was: "Click the Back button"; see § Adjustment)*.

   3a. **Absence of the legacy control (NEW assertion).**
   - **Verify — PASSES.** `back-button` count = **0** on DEV, live-confirmed in
     3 independent sessions. This absence assertion is first-class and
     deliberate: if the UI team restores the arrow, the test goes red and the
     case text gets revisited, instead of the drift rotting in a docstring
     (`.agents/testing.md` § Locator policy, #511 absence-assertion extension;
     same shape as `test_mcp_back_navigation.py:177`).

   3b. **The breadcrumb trail is the replacement affordance.**
   - **Verify — PASSES.** `breadcrumbs` nav visible; trail text reads
     `Agents/Echo Agent`; `breadcrumb-item` count = **exactly 1**;
     its text is `"Agents"`; the current crumb is `agent-detail-title` with
     `aria-current="page"` and the agent's name.
   - **Count-then-text, never `.first` on an unguarded collection.**
     `applyBreadcrumbLabels` (`breadcrumb.helpers.js:65-68`) DROPS any
     non-current ancestor whose label is empty. Here the ancestor's label is the
     static `PathSessionMap[Applications]` so it can never be dropped — but
     asserting the count makes that an *enforced invariant* instead of a silent
     assumption, exactly as `pipeline_detail_page.close_run_history` documents.
   - Evidence: ![Step 3 — agent detail header: breadcrumbs, no back arrow](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-1869-step-02-detail-breadcrumbs.png)

   3c. **Click the ancestor crumb, awaiting the list re-fetch.**
   - **Verify — PASSES.** Wrapping the click in
     `page.expect_response(lambda r: "applications/prompt_lib/" in r.url and
     "agents_type=classic" in r.url)` resolved `200
     …/applications/prompt_lib/399?tags=&sort_by=created_at&sort_order=desc&query=&agents_type=classic&limit=20&offset=0`
     on every run. **This wait signal survives the drift unchanged** — keep the
     currently-merged `expect_response` verbatim.

   3d. **Landing route.**
   - **Verify — PASSES, with the declared change.** Actual URL:
     `https://dev.elitea.ai/app/agents/all?viewMode=owner&name=Echo%20Agent`
     → `path=/app/agents/all`, `query={'viewMode': ['owner'], 'name': ['Echo Agent']}`.
     Assert path + `viewMode=owner` + `"/chat" not in url` (see § Adjustment
     § Expected-result changes).
   - The trailing `name` param is **carried through by design**
     (`Breadcrumbs.jsx:46` — `to={{pathname: crumb.to, search}}`) and is
     **inert**: the list request fired with `query=` empty and rendered the
     full unfiltered 20-card page. Recorded as an observation, not a defect.

4. **Verify the Agents dashboard is shown.**
   - **Verify — PASSES.** `agents-page-header` visible (count 1); same DOM shape
     as the Step-1 load — not Chat, not a blank page.

5. **Verify the list is intact (not blank, not redirected).**
   - **Verify — PASSES.** After waiting for the first `entity-card-name` to be
     visible, `agents_after == agents_before` — exact equality of names **and**
     order **and** count (20 == 20), on two consecutive DEV runs.
   - ⚠️ **The wait is mandatory** — without it the read returned `[]` while the
     header was already visible (see § Adjustment § Robustness fixes 1).
   - Evidence: ![Step 5 — back on the Agents dashboard, list intact](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-1869-step-05-back-on-list.png)

**Side channel (all steps):** zero console errors across the whole
navigate → detail → breadcrumb-back flow, on every DEV run.

---

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture | n/a (fixture-level) | asserted |
| Precondition: at least one agent exists | Agents list non-empty | pre-existing project state (20 cards) | Step 1 `assert agents_before` | asserted (existing data reused; `agent_id`/#524 avoided) |
| Step 1: navigate to Agents page | Dashboard loads, list displays | Step 1 | `agents-page-header` visible + non-empty `entity-card-name` list | asserted |
| Step 2: click into any agent card | Detail page opens | Step 2 | URL matches `/agents/all/<id>`, `agent-information-section` visible | asserted |
| Step 3: click the go-back control in the detail page header | Navigation is triggered back to the previous page | Steps 3a–3d | `back-button` count 0; `breadcrumb-item` count 1 + text "Agents"; click awaits the list re-fetch `200` | asserted — **control changed, observable unchanged** (case text needs the wording update in § Proposed TMS case-text change) |
| Step 4: verify Agents dashboard is shown | Dashboard visible | Step 4 | `agents-page-header` visible | asserted |
| Step 5: verify list is intact (not blank, not redirected) | List fully rendered with all previously visible agents | Step 5 | `agents_after == agents_before` (names + order + count) | asserted |
| Expected Final State: on Agents dashboard, list intact, not redirected to Chat/other | — | Steps 3d–5 | path + `viewMode` + `"/chat" not in url` + list equality | asserted |
| Pass/Fail: "all steps complete without errors" | No errors | Steps 1–5 | console-error side channel (0 observed) | asserted |
| Pass/Fail: "redirected elsewhere OR list blank = FAIL" | n/a | Steps 3d, 5 | explicit `/chat` negative + exact list equality (not `count > 0`) | asserted |

### Axis 2 — observables asserted beyond the case text

- **`back-button` absence on the detail route** (`to_have_count(0)`) — *added
  this pass: the case's original control no longer exists. An absence assertion
  keeps the finding test-enforced, so a UI-team restoration of the arrow turns
  the test red and forces the case text to be revisited, rather than leaving the
  drift as a comment. Mirrors `test_mcp_back_navigation.py:177` (#1731).*
- **Breadcrumb-trail shape**: `breadcrumbs` visible, `breadcrumb-item` count
  **exactly 1** with text `"Agents"`, current crumb `agent-detail-title` —
  *added this pass: `breadcrumb-item` is a generic shared testid, so the count
  guard is what makes `.first` honest; and asserting the label proves the crumb
  clicked is the Agents ancestor, not some other trail member.*
- **Landing route asserted as path + `viewMode`** rather than a whole-query
  string match — *see § Expected-result changes; strictly the same two facts,
  stated explicitly.*
- **Exact agent-name-list equality (order + count)** rather than "list
  non-empty" — *carried over from the original pass: `count > 0` would pass even
  if the round trip silently dropped or reordered an agent.*
- **Network-level re-fetch confirmation** (`applications/prompt_lib/…
  agents_type=classic` → `200`) — *carried over: distinguishes "intact because
  correctly re-fetched" from "intact because the DOM was never unmounted".*
- **Zero console errors across all steps** — *project convention; clean on every
  DEV run this pass.*

---

## Cleanup
None required. Read-only against a pre-existing agent; no test data generated.

---

## Concrete Handles (re-verified live on DEV, 2026-09-10)

**PROVENANCE verified after `cd ../EliteaUI && git fetch origin`, with the
two-stage closure-record grep (`.agents/workflow.md` § Closure record).
No new testid is required for this repair.**

| Element | Locator (testid-only) | Source | PROVENANCE |
|---|---|---|---|
| Breadcrumb `<nav>` on agent detail | `LocatorDescriptor(testid="breadcrumbs")` | `src/[fsd]/shared/ui/breadcrumbs/Breadcrumbs.jsx:23` | **on-main ✓** (also on `automation/testids`) |
| Ancestor crumb link **"Agents"** — *the replacement go-back control* | `LocatorDescriptor(testid="breadcrumb-item")` | `src/[fsd]/shared/ui/breadcrumbs/BreadcrumbItem.jsx:30` | **on-main ✓** |
| Current crumb (agent name, `aria-current="page"`) | `LocatorDescriptor(testid="agent-detail-title")` | registry `breadcrumb.constants.js:64` → `BreadcrumbItem.jsx:17` | **on-main ✓** |
| Legacy back arrow — **bound for the absence assertion only** | existing `AgentDetailPage.back_button = LocatorDescriptor(testid="back-button")` (`agent_detail_page.py:680`) | `src/components/BackButton.jsx:120` | **on-main ✓** (present in source, unreachable on this route) |
| Agents dashboard header | existing `AgentsListPage.page_header` (`testid="agents-page-header"`) | — | **on-main ✓** |
| Agent card name (collection) | existing `AgentsListPage.entity_card_name` (`testid="entity-card-name"`) | shared `Card.jsx` | **on-main ✓** |
| Agent detail loaded marker | existing `AgentDetailPage.information_section` (`testid="agent-information-section"`) | — | **on-main ✓** |
| Agent card click (Step 2) | existing `AgentsListPage.open_first_agent()` — drives `entity_card_name.first` (testid-compliant) | `agents_list_page.py:369-391` | **on-main ✓** |

**Locator-policy notes.**
- `breadcrumb-item` is a **generic testid on a shared component**, which is the
  policy-compliant shape for `src/[fsd]/shared/` (`.agents/testing.md`
  § "Shared components never hardcode feature-scoped testids" — *either* a
  generic testid *or* a caller-supplied `testId` prop). It is already used this
  way, as a `LocatorDescriptor`, by `McpFormPage.breadcrumb_parent_link` and as
  an UPPER_CASE class constant by `PipelineDetailPage.BREADCRUMB_ITEM_SELECTOR`.
  **No new testid is warranted** — the escalation test is "missing testid ⇒ add
  it", and nothing is missing.
- ⚠️ **Do NOT use `select_agent(name)`** (`agents_list_page.py:356-366`) — it
  builds a raw `page.locator(f'text="{name}"')` inside the method body
  (pre-policy tech debt #25/#42) and the project's first card is `Echo Agent`,
  a name that appears three times in the list. `open_first_agent()` is the
  testid-compliant counterpart and returns the agent id.

### Optional UI improvement — **human decision, not required for this repair**

The ancestor crumb's testid is hardcoded in the shared component
(`BreadcrumbItem.jsx:30`), while `BREADCRUMB_REGISTRY` already supplies a
`testId` that only the *current* crumb consumes (`BreadcrumbItem.jsx:17`). A
one-attribute change — `data-testid={testId ?? 'breadcrumb-item'}` on the link
branch, plus `testId: 'agents-breadcrumb-link'` on the `ApplicationsWithTab`
registry entry — would give every ancestor crumb a semantic handle across all
surfaces. It is zero-functional-impact and policy-clean, but it is **suite-wide
scope** (it changes the ancestor testid for toolkits/MCPs/skills/pipelines
too, and `McpFormPage`/`PipelineDetailPage` already bind the generic one).
**Recommendation: do not do it under this card.** Raise it as a `question` card
if the team wants it.

---

## Network Behavior
- `GET /api/v2/elitea_core/applications/prompt_lib/399?tags=&sort_by=created_at&sort_order=desc&query=&agents_type=classic&limit=20&offset=0`
  → `200`. Fires on the Step-1 navigate **and again after the Step-3 crumb
  click**. Unchanged by the drift — this remains the implementer's wait signal
  for "the list has re-loaded". *(A `limit=1&offset=0` probe of the same
  endpoint also fires on first load; the `expect_response` predicate matches
  either, and the awaited one observed was always the `limit=20` list fetch.
  If that ever matters, tighten the predicate with `"limit=20"`.)*
- `GET /api/v2/elitea_core/application/prompt_lib/399/{id}` — fires on Step 2.
- The crumb click is **client-side** (react-router `<Link>`); no document
  `load` event. The MCP sibling asserts this explicitly
  (`test_mcp_back_navigation.py` Step 4); optional here.

---

## Known Defects Found During Exploration
**None.** The drift is an intentional product change (EL-6460 / `f1d4ea47`),
and the replacement affordance works correctly end to end. Per
`.agents/role-overrides.md` § interaction-discovery ladder, the intended mode
per source is the breadcrumb, and the intended mode works — so this is a
**case-text CLARIFICATION**, not a `bug` (the #1731 disposition, and the
reverse-masking guard's exact scenario: the case text is what is stale).

**Observation, not a defect:** the ancestor crumb carries the detail page's
`?name=<agent name>` search param onto the list route. Live-verified inert —
the list request goes out with `query=` empty and renders the full unfiltered
page. Cosmetic only.

**Blast radius — report only, out of scope for this card:**
- `tests/ui/skills/test_skill_back_navigation.py` (ELITEA-2429) +
  `pages/skill_detail_page.py:41` use the same `back-button` testid, and
  `SkillsDetail` is in `BREADCRUMB_REGISTRY` (`breadcrumb.constants.js:93-98`)
  with `EditSkill.jsx:207` rendering `BreadcrumbsOrTitle` — **same drift, same
  root commit.** Needs its own `[FIX]` card.
- `pages/mcp_form_page.py:348` also declares `back-button`, but that surface was
  **already repaired** (ELITEA-1961 / #1731) — it is bound for an absence
  assertion and needs nothing.

---

## Blocked Steps
None.

---

## Automation Hints

- Framework: Playwright + pytest. Branch `tests/adjust-ELITEA-1869-<slug>` cut
  from fresh `origin/automation/base`. **Update the existing test file only** —
  no new test file, no new test class.
- **Page-object changes** (`automation/pages/agent_detail_page.py`), mirroring
  `McpFormPage` (`mcp_form_page.py:325-352`) verbatim in shape:
  ```python
  # class level, next to the existing back_button field
  breadcrumbs_nav = LocatorDescriptor(
      testid="breadcrumbs",
      description="Breadcrumb <nav> on the agent detail page "
                  "(absent on the agents list page)",
  )
  breadcrumb_parent_link = LocatorDescriptor(
      testid="breadcrumb-item",
      description="Parent crumb link ('Agents') in the breadcrumb trail — "
                  "exactly one renders on /agents/:tab/:agentId",
  )
  ```
  Keep the existing `back_button` field — it is now **referenced by an absence
  assertion on the executed path**, which is a first-class reference under
  `.agents/testing.md` § Locator policy (#511 extension).
- **New method** `click_breadcrumb_parent(timeout: int = 10000)` on
  `AgentDetailPage`, wrapped in `@action(...)`:
  count-guard (`expect(self.breadcrumb_parent_link).to_have_count(1, timeout=timeout)`),
  then `.first.wait_for(state="visible", timeout=timeout)`, then
  `.first.click(timeout=timeout)`. **Propagate `timeout` to the click** — the
  bug that produced this card's misleading `10000ms` signature.
- **Disposition of `AgentDetailPage.click_back_button()` / the
  `AgentPage.click_back_button()` facade** — after this repair, nothing calls
  either (grep: the only caller is this test). Recommended:
  fix the one-line timeout propagation (`self.back_button.click(timeout=timeout)`)
  so it can never mislead a future triage the way it misled this one, and
  **leave the methods in place**; deleting them is a separate cleanup decision
  for the lead, and `SkillDetailPage` still mirrors the same shape pending its
  own `[FIX]` card.
- **Test-file changes** (`tests/ui/agents/test_agent_back_navigation.py`):
  - **Drop the `agent_id` fixture parameter.** It is unused by the test body
    (the test clicks the first card, not `agent_id`) and every invocation pays
    an `agent_api.create_agent(...)` that walks into open defect #524. Removing
    it is a precondition/robustness change, not an assertion change.
  - Step 2: prefer `AgentsListPage.open_first_agent()` over
    `select_agent(agents_before[0])` — testid-compliant, and immune to the
    duplicate-name hazard (`Echo Agent` ×3 in project 399).
  - Step 3: add the two new sub-assertions (3a absence, 3b trail shape), keep
    the `expect_response` wrapper verbatim, swap `click_back_button` for
    `click_breadcrumb_parent`, and replace the URL assertion per
    § Expected-result changes (`urlparse`/`parse_qs`, already imported
    elsewhere in the suite).
  - Step 5: add
    `list_page.entity_card_name.first.wait_for(state="visible", timeout=NAVIGATION_TIMEOUT)`
    before reading `agents_after`.
  - Preserve every `allure.step("Step N — …")` wrapper, the markers
    (`ui`, `agents`, `p0`, `regression`), and the docstring's AFS link;
    update the docstring to name the breadcrumb control and cite this AFS's
    § Adjustment.
- **Gate on DEV, not localhost** (`.agents/testing.md` § Merge gate + the
  `.env.test`-is-a-symlink trap): resolve the symlink with `os.path.realpath`,
  rewrite `ELITEA_URL=https://dev.elitea.ai` / `APP_PREFIX=/app` with Python
  (BSD `sed -i ''` refuses symlinks and fails silently-by-omission), assert
  `settings.app_base_url == "https://dev.elitea.ai/app"` before running, and
  restore from a backup in a shell `trap … EXIT INT TERM`. Localhost serves
  identical code (all three long-lived branches are 0 behind their mains) so a
  localhost run is a valid smoke check, but the card scopes DEV.
- ⚠️ **Expect `#2124`/`#2156` `Page.goto` noise on DEV** — measured at up to
  7-of-9 attempts in a burst. Those are raw uncaught errors at a
  *precondition* (allure status `broken`), never a member of a sanctioned-RED
  set: **re-gate, never accept 2-of-3.** Classify by
  `statusDetails.message` in `reports/allure-results/*-result.json`, not by the
  pytest tail.

---

## Implementation notes — shipped truth (implementer, 2026-09-10)

Amended per `test-automation-implementation` Rule 11 after the repair was built
and gated green on DEV. Three points where the shipped code is more specific
than § Automation Hints — none changes what is asserted:

1. **A third `LocatorDescriptor` was added**, not just the two in the Hints
   snippet: `AgentDetailPage.detail_title = LocatorDescriptor(
   testid="agent-detail-title")`. It is the current-crumb handle the § Concrete
   Handles table already lists, and Step 3b asserts its text + its
   `aria-current="page"` through it. Locator-policy compliant (class-level
   field, testid on `main`).
2. **The "trail reads `Agents/<name>`" assertion is a web-first `expect` on the
   nav field**, not a `get_breadcrumb_text()` getter as on `McpFormPage`:
   `expect(detail_page.breadcrumbs_nav).to_have_text(re.compile(rf"^Agents\s*/\s*{re.escape(name)}$"))`.
   Auto-retrying (so it cannot read a half-mounted trail) and tolerant of MUI's
   separator whitespace, while still a full-string match. No new page-object
   method was needed.
3. **The console side-channel was migrated to
   `utils.console_errors.collect_console_errors(page)`** from the spec's
   hand-rolled URL-less `page.on("console", …)` listener. Not requested by this
   AFS — it is the standing opportunistic-migration ask in `.agents/testing.md`
   § Unconfirmed ("only migrated specs can produce this evidence"), and this
   spec was being touched anyway. Capture-only: nothing is filtered, no
   `exclude_known_defect_urls` call is made, so the assertion is strictly the
   same one, now carrying the failing resource's URL when it fires.

Also applied verbatim from § Robustness fixes 2: `click_back_button()` now
passes `timeout` to `.click()` as well as to `wait_for_network()`. The method
and the `AgentPage` facade are **kept** (no caller remains after this repair,
but `back_button` stays bound for Step 3a's absence assertion, and
`SkillDetailPage` still mirrors the shape pending its own `[FIX]` card).

**DEV gate observed:** 3 invocations, 3 green (63.88 s / 46.13 s / 49.42 s).
2 of those 3 carried one `--reruns` attempt each, both the documented
`#2124`/`#2156` DEV hazard — `Page.goto: Timeout 15000ms exceeded … navigating
to "https://dev.elitea.ai/"`, allure status `broken`, 0.0 s, in session setup,
upstream of every assertion. The spec's own signature never appeared.

---

## Proposed TMS case-text change (do NOT apply here — orchestrator applies at back-write)

The case text is what is stale, not the product (reverse-masking guard). The
change updates the *control* while leaving every expected result intact.

**Objective** — replace:
> Verify that clicking the Back button on an agent detail page returns the user to the Agents dashboard with the list intact, without redirecting to an unrelated page.

with:
> Verify that using the agent detail page's header navigation — the "Agents" breadcrumb — returns the user to the Agents dashboard with the list intact, without redirecting to an unrelated page.

**Step 3** — replace the row:

| # | Action | Expected Result |
|---|--------|-----------------|
| 3 | Click the Back button in the agent detail page header | Navigation is triggered back to the previous page |

with:

| # | Action | Expected Result |
|---|--------|-----------------|
| 3 | In the agent detail page header, verify the breadcrumb trail reads "Agents / \<agent name\>" (the standalone back-arrow button is no longer rendered on this route), then click the "Agents" breadcrumb | Navigation is triggered from the agent detail page back to the Agents list route |

**Pass criteria** — replace:
> - The Back button returns the user to the Agents dashboard with the list intact.

with:
> - The "Agents" breadcrumb returns the user to the Agents dashboard with the list intact.

**Frontmatter:** `automation_test_id` stays **unchanged** (same test, same
dotted Form C path). `automation_pr` should be updated to the adjustment PR.

**Rationale to record with the change:** EliteaAI/EliteaUI@f1d4ea47
(*feat: [EL-6460] Add Breadcrumb Navigation to Agent, Pipeline, and Skill Details
Pages*, #884) replaced the back-arrow header control with a breadcrumb trail on
every agent/pipeline/skill detail route. Same disposition as the MCP surface's
CLARIFICATION #1731.
