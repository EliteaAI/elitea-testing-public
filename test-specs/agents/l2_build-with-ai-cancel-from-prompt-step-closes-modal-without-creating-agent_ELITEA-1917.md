# Test Case: Build with AI — Cancel from prompt step closes modal without creating an agent

## Metadata
- **TMS ID**: ELITEA-1917
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/agents/build_with_ai/ELITEA-1917_build-with-ai-cancel-from-prompt-step-closes-modal.md`
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project `UI Testing` / id `400` (browser session's last-selected project — the case's own steps are project-agnostic; other cases in this batch use `${ELITEA_PROJECT_ID}`=399, no behavioral dependency on which project is active)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via `VITE_DEV_TOKEN`; admin-equivalent role, per `.agents/profile.md` § Roles & sample users)
- **Analyst**: qa-engineer (Sage), analyst slot, batch #1298
- **Status**: ready-for-automation
- **Tracking issue**: EliteaAI/elitea-testing-public#1298 (batch tracking issue — no per-case board card)
- **Case-gate note**: source case frontmatter carries `status: draft` / `execution_type: manual` — consistent with the batch's other cases; no exclusion per `.agents/testing.md` § TMS case-gate (no excluded-status list defined for this project), so this run proceeded normally.

## Triangulation vs ELITEA-1905 (why this is `ready-for-automation`, not `extend-existing`)

`test-specs/agents/lextend_build-with-ai-modal-contains-prompt-generate-cancel-controls_ELITEA-1905.md`
is merged onto this batch's trunk and its gap assertions are live in
`automation/tests/ui/agents/test_agent_build_with_ai.py`,
`TestAgentBuildWithAIGenerationFailureRetry.test_generation_failure_shows_error_and_allows_retry`,
Step 1 block (lines 384–392 on this trunk):

```python
assert modal.cancel_button.is_visible(), (
    "Cancel button should be visible in the Build with AI modal"
)
```

Grep confirms this is the **only** occurrence of `cancel_button` anywhere in
the suite (`grep -rn "cancel_button" automation/tests/ automation/pages/`) —
it is read for `.is_visible()` and never `.click()`ed. ELITEA-1905 proved the
Cancel button **exists**; it never exercised what clicking it **does**, which
is this case's entire objective.

**Why this can't be spliced into the same covering test (extend-existing
doesn't fit):** `test_generation_failure_shows_error_and_allows_retry`'s
Step 1 block is immediately followed by `modal.fill_prompt(...)` →
`modal.mock_generate_failure(...)` → `click_generate_and_wait_for_response()`
→ asserts on the review/error flow. Clicking Cancel closes the modal
permanently (confirmed live this run — see § Test Steps below) — inserting
a cancel-click there would terminate that test's own flow before it ever
reaches its Step 2. The skill's own boundary call applies: an "extension"
that would break the covering test's control flow is not a small gap-fill,
so this routes to `ready-for-automation` as a new, standalone test —
reusing the existing `GenerateAgentModalPage`/`AgentsListPage`/`AgentFormPage`
handles (no new page object, no new locators; see § Concrete Handles).

No other existing test in this file or elsewhere in `tests/ui/agents/`
references `cancel_button` at all (confirmed via the same grep), so there is
no partial-overlap target to extend against for the click-and-verify
behavior either.

## Preconditions
- `${TEST_USER}` is authenticated via the `auth_state` fixture (localhost
  `VITE_DEV_TOKEN` bypass — no Keycloak login form on localhost).
- The New Agent creation page (`${BASE_URL}/agents/create?viewMode=owner`)
  is reachable, with the "General" accordion section expanded by default
  and the Name/Description fields empty — confirmed live (initial
  page-load snapshot showed both fields with no value).

## Test Data
### reuse-existing (no fixture creation/teardown needed)
- `${TEST_USER_EMAIL}` / `${TEST_USER_PASSWORD}` via `auth_state`.
- `${ELITEA_PROJECT_ID}` (whichever project is active — the flow is
  project-agnostic).
- Prompt text: any non-empty natural-language string (case's Test Data
  says "Any description text (not submitted)"). Confirmed live with:
  `"A customer support agent that answers billing questions."`

No new test data is created or persisted in the product by this case's
steps — Cancel is clicked before Generate, so no draft is ever requested
and no agent is ever created. See Cleanup.

## Test Steps

1. Navigate to `${BASE_URL}/agents/create?viewMode=owner`, click the Magic
   Wand ("Build with AI") button (`data-testid="generate-agent-open-button"`,
   rendered as the `summaryAction` of the "General" accordion header, per
   `CreateAgentForm.jsx` — **not** adjacent to the Name field; the icon next
   to Name is a distinct element, `agent-form-icon-button`, the agent's
   avatar/icon picker, confirmed live this run when an initial click on it
   produced no modal).
   - **Verify**: the `generate-agent-modal` dialog opens, showing heading
     "Build with AI", a prompt textarea, a "Cancel" button, and a disabled
     "Generate Draft" button — confirmed live via accessibility snapshot.
2. Enter a natural-language description into the prompt textarea
   (`data-testid="generate-agent-prompt-input"`) **without clicking
   Generate**.
   - **Verify**: the textarea contains the entered text — confirmed live
     (`"A customer support agent that answers billing questions."`); the
     "Generate Draft" button transitions from disabled to enabled
     (confirmed live, consistent with ELITEA-1915's existing
     `is_generate_enabled()` coverage of this same transition — not
     re-asserted here, this AFS's own gap is the Cancel click).
3. Click "Cancel" (`data-testid="generate-agent-cancel-button"`)
   **without generating**.
   - **Verify**: the Cancel action is triggered — confirmed live, the
     click resolves synchronously with no confirmation dialog / prompt
     ("are you sure you want to discard?") — none appeared.
4. Verify the modal closes.
   - **Verify**: `generate-agent-modal` is no longer present in the DOM —
     confirmed live via accessibility snapshot immediately after the
     Cancel click: the `dialog` element is gone entirely (not merely
     hidden/inert), the page returns to the plain "New Agent" tab view.
5. Verify the New Agent form is still shown with empty/untouched fields.
   - **Verify**: `agent-name-input` and `agent-description-input` are both
     empty (`input_value() == ""`) — confirmed live (both were empty
     before opening the modal and remained empty after Cancel; the modal's
     prompt text was never written into the New Agent form's own fields —
     they are entirely separate inputs). The outer form's own "Save"/
     "Cancel" buttons remain disabled, consistent with an untouched empty
     form (secondary confirmation, not itself a case criterion).
6. Verify no new Agent was created in the Agents list.
   - **Verify (primary, deterministic)**: no `POST
     .../elitea_core/applications/prompt_lib/**` (the base-agent CREATE
     call — same route `GenerateAgentModalPage.CREATE_APPLICATION_ROUTE`
     targets) and no `POST .../elitea_core/generate_application_draft/**`
     (the generate-draft call) fired at any point during this flow —
     confirmed live via `browser_network_requests` filtered to both
     routes: **zero matches**, across the entire open→type→cancel
     sequence. Since Cancel is clicked before Generate, no draft is ever
     requested, so there is no generated name to search the Agents list
     for — the network-absence check is the only sound way to prove
     "no agent was created" (a list-search would need a name that was
     never generated).
   - **Verify (secondary, case-literal)**: navigating to `${BASE_URL}/agents/all`
     and reading the visible agent card names before this test's Step 1
     and again after Step 4 shows an unchanged set/count — a redundant,
     case-literal confirmation of the same fact the network check already
     proves deterministically.

## Expected Results
Clicking Cancel on the GenerateAgentModal's prompt-input step closes the
modal (dialog removed from the DOM, not merely hidden), leaves the New Agent
creation form in its original empty/untouched state, and creates no agent —
neither the generate-draft call nor the create-agent call ever fires. No
console errors observed (`browser_console_messages`, level=error → 0 results,
across open → type → cancel).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open the GenerateAgentModal and enter a natural-language description | Input field contains the entered text | AFS Steps 1–2 | `prompt_input.input_value() == PROMPT_TEXT`; modal dialog present via `modal.wait_for(state="visible")` (reuses `GenerateEntityModalPageBase.open_modal()`/`fill_prompt()`) | ready-for-automation (new test) |
| 2 Click "Cancel" without generating | The Cancel action is triggered | AFS Step 3 | `modal.cancel_button.click()` — **the case's core, previously-unexercised gap**; confirmed live (no confirmation dialog intervenes) | ready-for-automation (new test) — first ever `.click()` on `cancel_button` in the suite |
| 3 Verify the modal closes | GenerateAgentModal is closed and no longer visible | AFS Step 4 | `modal.modal.wait_for(state="hidden", timeout=...)` (or equivalent DOM-absence check) — confirmed live: the dialog element is fully removed | ready-for-automation (new test) |
| 4 Verify the New Agent form is still shown with empty/untouched fields | Form displayed with fields in original empty/untouched state | AFS Step 5 | `agent_form.name_input.input_value() == ""` and `agent_form.description_input.input_value() == ""` (existing `AgentFormPage` locators, confirmed live both before-open and after-cancel) | ready-for-automation (new test) |
| 5 Verify no new Agent was created in the Agents list | Navigating to the Agents list shows no new agent was added | AFS Step 6 | Primary: assert no POST fired to `CREATE_APPLICATION_ROUTE` / `GENERATE_DRAFT_ROUTE` during the flow (network-request-log inspection). Secondary: `AgentsListPage.get_agent_card_names()` count/set unchanged before vs after | ready-for-automation (new test) — network-absence is the deterministic proof; the list-navigation is the case-literal echo |

### Axis 2 — Analyst additions

- Confirmed the Magic Wand ("Build with AI") button lives in the "General"
  accordion header's `summaryAction` slot (`CreateAgentForm.jsx:106`), NOT
  adjacent to the Name field — *added: disambiguates it from
  `agent-form-icon-button` (the agent avatar/icon picker), a distinct
  element that sits directly beside Name and produces no modal when
  clicked (confirmed live this run — an initial mis-click on it did
  nothing).* Neither ELITEA-1905's nor this AFS's own exploration notes
  this distinction explicitly before now; worth flagging for any future
  case touching this button.
- Confirmed zero console errors across the full open→type→cancel sequence
  (`browser_console_messages`, level=error → 0 results) — *added:
  side-channel check, standard practice per this skill's methodology, not
  itself required by the case's Pass criteria.*
- Confirmed clicking Cancel produces no confirmation/"discard changes?"
  interstitial — the modal closes on the first click — *added: a plausible
  UX pattern the case text doesn't rule out, ruled out live.*
- Confirmed all three testids needed (`generate-agent-open-button`,
  `generate-agent-prompt-input`, `generate-agent-cancel-button`) plus the
  New Agent form's own `agent-name-input`/`agent-description-input` and
  the Agents-list `entity-card-name` collection locator already exist as
  `LocatorDescriptor` fields on `GenerateAgentModalPage`/`AgentFormPage`/
  `AgentsListPage` and were live-confirmed present in the DOM this run —
  *added: no `add-data-testid` work needed for this case.*

## Cleanup
No product state is created by this case's own steps — Cancel is clicked
before Generate, so no draft is requested and no agent is created. No
`agent_api.delete_agent(...)` teardown is needed (unlike the create-flow
tests in this same file, which own a `try/finally` cleanup for the agent
they DO create).

## Concrete Handles (discovered during exploration — all pre-existing)

| Element | Recommended Locator | Provenance |
|---|---|---|
| "Build with AI" open button | `generate-agent-open-button` (pre-existing on `GenerateAgentModalPage.open_button`) | on-main ✓ (confirmed via ELITEA-1903's merged test + live click this run) |
| Modal container | `generate-agent-modal` (pre-existing on `GenerateAgentModalPage.modal`) | on-main ✓ |
| Prompt textarea | `generate-agent-prompt-input` (pre-existing on `GenerateAgentModalPage.prompt_input`) | on-main ✓ |
| Cancel button | `generate-agent-cancel-button` (pre-existing on `GenerateAgentModalPage.cancel_button`) — **this case is the first to `.click()` it; ELITEA-1905 only asserted `.is_visible()`** | on-main ✓ |
| New Agent form Name field | `agent-name-input` (pre-existing on `AgentFormPage.name_input`) | on-main ✓ (confirmed empty both before-open and after-cancel) |
| New Agent form Description field | `agent-description-input` (pre-existing on `AgentFormPage.description_input`) | on-main ✓ (confirmed empty both before-open and after-cancel) |
| Agents list card name | `entity-card-name` (pre-existing on `AgentsListPage.entity_card_name`, via `get_agent_card_names()`) | on-main ✓ |
| Base-agent CREATE route | `**/elitea_core/applications/prompt_lib/**` (pre-existing constant `GenerateAgentModalPage.CREATE_APPLICATION_ROUTE`) | on-main ✓ — used here only for a **negative** (no-call) network assertion, not a mock |
| Generate-draft route | `**/elitea_core/generate_application_draft/**` (pre-existing constant `GenerateAgentModalPage.GENERATE_DRAFT_ROUTE`) | on-main ✓ — same negative-assertion use |

No new testids required. No new page-object locators required. Every
handle needed already exists in `GenerateAgentModalPage`, `AgentFormPage`,
and `AgentsListPage`.

## Network Behavior
Confirmed live: across the entire open → type-prompt → click-Cancel
sequence, **zero** requests matched either
`**/elitea_core/generate_application_draft/**` or
`**/elitea_core/applications/prompt_lib/**` (POST) — filtering
`browser_network_requests` to both route substrings returned no rows. Only
the page's normal load-time GETs (`support_assistant`, `project_info`,
`configurations`, `permissions`, `tags`, `default_icons`, `upload_icon`,
socket.io polling, etc.) appeared, identical in shape to ELITEA-1905's own
Network Behavior notes for the same screen.

## Known Defects Found During Exploration
None. Product behavior matches the case's stated intent exactly: Cancel
closes the modal, the New Agent form is unaffected, and no agent is
created. No case-text drift found either — unlike ELITEA-1905 (button
label/enabled-state drift, filed as #1315), this case's wording matches
the live product precisely.

## Blocked Steps
None. All 6 case elements were executed live this run against the real
local system (`http://localhost:5173`).

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Add a new,
  standalone test — do not attempt to insert a cancel-click into
  `test_generation_failure_shows_error_and_allows_retry` (see §
  Triangulation above for why that breaks the covering test's flow). A new
  test method in `automation/tests/ui/agents/test_agent_build_with_ai.py`
  (new class, e.g. `TestAgentBuildWithAICancelFromPromptStep`, or appended
  to an existing class if the implementer judges the grouping fits) is the
  natural home — same file, same imports, same fixtures already used by
  the file's other tests (`AgentsListPage`, `GenerateAgentModalPage`), no
  new page object needed.
- No new `LocatorDescriptor` fields needed — `cancel_button` already
  exists; this case is simply its first real `.click()`.
- Suggested flow (illustrative, not prescriptive — the implementer owns
  exact structure/step numbering per this file's `allure.step` convention):
  ```python
  with allure.step("Step 1 — Open modal, enter description"):
      list_page.navigate_to_create()
      modal.open_modal()
      modal.fill_prompt(CANCEL_PROMPT_TEXT)
      assert modal.get_prompt_value() == CANCEL_PROMPT_TEXT

  with allure.step("Step 2 — Click Cancel without generating"):
      modal.cancel_button.click()

  with allure.step("Step 3 — Verify the modal closes"):
      modal.modal.wait_for(state="hidden", timeout=NAVIGATION_TIMEOUT)

  with allure.step("Step 4 — Verify the New Agent form is untouched"):
      form_page = AgentFormPage(page)
      assert form_page.name_input.input_value() == "", (
          "New Agent form's Name field should remain empty after cancelling Build with AI"
      )
      assert form_page.description_input.input_value() == "", (
          "New Agent form's Description field should remain empty after cancelling Build with AI"
      )

  with allure.step("Step 5 — Verify no agent was created"):
      create_calls = [
          r for r in captured_requests
          if "/elitea_core/applications/prompt_lib/" in r.url and r.method == "POST"
      ]
      assert not create_calls, "No base-agent CREATE call should ever fire after Cancel"
      draft_calls = [
          r for r in captured_requests
          if "/elitea_core/generate_application_draft/" in r.url
      ]
      assert not draft_calls, "No generate-draft call should ever fire after Cancel"
  ```
  Capturing `captured_requests` needs a `page.on("request", ...)` collector
  installed before Step 1 (or `page.request` history via a small local
  helper) — the file has no existing "assert a route was never called"
  helper; a minimal local list-append handler is sufficient and does not
  require a new page-object method (network mocking helpers already on
  `GenerateAgentModalPage` are for *mocking* generate/create, not for
  negative-call assertions — a distinct, smaller need).
- Timeout constants: reuse the file's existing `NAVIGATION_TIMEOUT` (15000)
  for the modal-hidden wait; no new constant needed.
- No mocking/route interception needed — every assertion in this case is
  against the real, unmocked flow (no draft is ever requested, so there is
  nothing to mock).
- Marker: `@pytest.mark.p2` + `@pytest.mark.regression`, consistent with
  this file's other Build-with-AI cases and this case's own `l2`/`medium`
  priority.
