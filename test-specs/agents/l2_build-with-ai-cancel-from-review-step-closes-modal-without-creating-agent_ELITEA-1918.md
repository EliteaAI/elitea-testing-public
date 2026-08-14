# Test Case: Build with AI — Cancel from review step closes modal without creating an agent

> ⚠️ **UNDER REVIEW — 2026-08-14 fidelity audit. Do NOT reuse this AFS as a pattern.**
>
> This spec directs the implementer to **substitute the system under test** (mocking
> the `generate_application_draft` response) for a TMS case whose text never asks for
> simulation. Classification: **TRANSIT** — the mock only reaches the review step; the case's own observable (cancel closes the modal) is still produced by the system — re-check and declare it, or drop the mock for a live generate.
>
> Its justifications ("the same sanctioned-mocking technique this file already uses",
> "not a good use of fixture-creation effort") are **not valid authorities**: nothing
> sanctions response mocking, and cost is never a reason to substitute. See
> `.agents/testing.md` § Fidelity policy and `.agents/role-overrides.md` § Every role —
> precedent is not authority.
>
> **`extend-existing` must not inherit this design.** Rework is tracked on
> [#1298](https://github.com/EliteaAI/elitea-testing-public/issues/1298); the full chain
> is in `sdlc-skills/bundles/test-automation/incidents/2026-08-14-response-mocking-drift.md`.

## Metadata
- **TMS ID**: ELITEA-1918
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/agents/build_with_ai/ELITEA-1918_build-with-ai-cancel-from-review-step-closes-modal.md`
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project `UI Testing` / id `400` (browser session's last-selected project — the case's own steps are project-agnostic)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via `VITE_DEV_TOKEN`; admin-equivalent role, per `.agents/profile.md` § Roles & sample users)
- **Analyst**: qa-engineer (Sage), analyst slot, batch #1298
- **Status**: ready-for-automation
- **Tracking issue**: EliteaAI/elitea-testing-public#1298 (batch tracking issue — no per-case board card)
- **Case-gate note**: source case frontmatter carries `status: draft` / `execution_type: manual` — consistent with the batch's other cases; no exclusion per `.agents/testing.md` § TMS case-gate, so this run proceeded normally.
- **Case-text drift filed**: [EliteaAI/elitea-testing-public#1318](https://github.com/EliteaAI/elitea-testing-public/issues/1318) — see § Known Defects Found and § Triangulation below. **The case's literal "Cancel" button does not exist on the review step** — this AFS asserts the live, correct control instead (reverse-masking guard).

## Triangulation — what actually closes the modal from the REVIEW step

**Read `GenerateEntityModal.jsx` (`../EliteaUI/src/[fsd]/entities/generate-entity-with-ai/ui/GenerateEntityModal.jsx`) before writing anything** — `renderActions()` (lines 170-224) renders a **different button set per step**, not a fixed "Cancel + Generate/Approve" pair:

```js
if (step === STEPS.REVIEW) {
  return (
    <>
      <BaseBtn onClick={handleBack} data-testid={backButtonTestId}>Back to prompt</BaseBtn>
      <BaseBtn onClick={handleApprove} data-testid={approveButtonTestId}>{...}</BaseBtn>
    </>
  );
}
// else (INPUT step):
return (
  <>
    <BaseBtn onClick={handleClose} data-testid={cancelButtonTestId}>Cancel</BaseBtn>
    <BaseBtn onClick={handleGenerate} data-testid={generateButtonTestId}>Generate Draft</BaseBtn>
  </>
);
```

**There is no "Cancel" button at the REVIEW step at all.** Only two controls render there:
- **"Back to prompt"** (`generate-agent-back-button`) → `handleBack()` — returns to the INPUT step, `draftData` reset to `null`, **modal stays open**. This is ELITEA-1919's separate case
  (`onetest-ai-tm-Elitea/.../ELITEA-1919_build-with-ai-back-to-prompt-returns-to-input-step-preserves-text.md`)
  — confirmed a distinct case exists for it, so this AFS does **not** cover Back-to-prompt.
- **"Create Agent"** (`generate-agent-approve-button`) → `handleApprove()` — the approval path (ELITEA-1909/1911/1912/1914's territory), not this case's concern.

The only way to close the modal from the review step **without creating an agent** is the modal header's **X ("Close") icon** (`generate-agent-close-button`, wired via `Modal.BaseModal`'s
`closeButtonTestId`/`onClose` prop — confirmed in `.../shared/ui/modal/BaseModal.jsx:154`,
`onClick={onClose}`). Tracing `onClose` back to `GenerateEntityModal.jsx`'s own `<Modal.BaseModal onClose={handleClose} .../>` (line 230) confirms the X icon calls **the exact same
`handleClose()`** function the INPUT-step "Cancel" button calls (lines 51-62): abort any in-flight
generate promise, reset `step`/`description`/`draftData`/`isApproving`, `resetGenerate()`, then
`onClose()` (the parent's close callback, which also resets the parent's `selected*Ids` sets via
`handleDraftGenerated()`). Same semantics as ELITEA-1917's prompt-step Cancel — closing discards
everything, unconditionally, with no confirmation interstitial — just a different visible
affordance because the review step's action row is occupied by Back/Create.

**This is why the AFS routes to `ready-for-automation`, not `already-covered`/`extend-existing`
against ELITEA-1913's test:** `TestAgentBuildWithAIReviewFormNameValidation` (ELITEA-1913,
`test_agent_build_with_ai.py`) DOES call `modal.close_button.click()` from the review step —
but only as end-of-test **cleanup** ("No product state to clean up ... close the modal to leave a
clean state", line ~1838), with **zero assertions before or after it**. Confirmed via
`grep -n "close_button" tests/ui/agents/test_agent_build_with_ai.py` → exactly one hit, that
cleanup line. No test asserts what clicking the X icon from the review step actually DOES (modal
removed from DOM, form untouched, no create call, no agent in the list) — that is this case's
entire, previously-unexercised gap. Same triangulation shape ELITEA-1917 used for `cancel_button`
(visible-but-never-`.click()`ed-with-assertions before ELITEA-1917) — here `close_button` has been
`.click()`ed once, but never verified.

## Preconditions
- `${TEST_USER}` is authenticated via the `auth_state` fixture (localhost
  `VITE_DEV_TOKEN` bypass — no Keycloak login form on localhost).
- The New Agent creation page (`${BASE_URL}/agents/create?viewMode=owner`)
  is reachable, with the "General" accordion section expanded by default.
- **A draft has been generated and the review/edit form is displayed** — this
  case's own precondition (distinct from ELITEA-1917, which cancels BEFORE
  generating). Reached live this run via a real (unmocked)
  `generate_application_draft` call — no `mock_generate_success()` needed;
  the real endpoint responds reliably within the existing
  `REVIEW_FORM_TIMEOUT`/`GENERATE_RESPONSE_TIMEOUT` constants this file
  already defines (used by ELITEA-1916's test). Mocking remains available
  (`GenerateAgentModalPage.mock_generate_success()`) if the implementer
  prefers a deterministic draft payload — either is sound; this AFS does not
  assert on the draft's specific content, only on the close behavior.

## Test Data
### reuse-existing (no fixture creation/teardown needed)
- `${TEST_USER_EMAIL}` / `${TEST_USER_PASSWORD}` via `auth_state`.
- `${ELITEA_PROJECT_ID}` (whichever project is active — the flow is
  project-agnostic).
- Prompt text: any non-empty natural-language string. Confirmed live with:
  `"A customer support agent that answers billing questions and escalates
  refund requests."` — reused this file's existing `CANCEL_PROMPT_TEXT`
  constant is also fine (case's own prompt text doesn't matter to this
  case's Pass criteria); if the implementer mocks the draft instead, this
  file's existing `CREATE_FAILURE_DRAFT_PAYLOAD`-shaped fixture pattern
  (ELITEA-1916) can be reused/adapted, or a small dedicated
  `CANCEL_FROM_REVIEW_DRAFT_PAYLOAD` if a case-specific draft is preferred.

No new test data is created or persisted in the product by this case's
steps — the draft IS generated (this case's precondition), but the
create-agent call never fires because the X icon is clicked instead of
"Create Agent". See Cleanup.

## Test Steps

1. Navigate to `${BASE_URL}/agents/create?viewMode=owner`, open the Build
   with AI modal (`generate-agent-open-button`), enter a natural-language
   description into the prompt textarea (`generate-agent-prompt-input`),
   and click "Generate Draft" (`generate-agent-submit-button`) to reach the
   review step.
   - **Verify**: the review form is displayed with the generated draft's
     data — confirmed live via `wait_for_review_form()`'s existing pattern
     (waits for `back_button` + `approve_button` visible) and an
     accessibility snapshot showing populated Name/Description/
     Instructions/Welcome Message/Chat-starter fields (this run generated
     "Billing Support Agent" from a billing-support prompt, with 4 chat
     starters — real, unmocked AI output, confirmed live).
2. Click the modal's Close (X) icon (`generate-agent-close-button`) —
   **the review step has no separate "Cancel" button**; see § Triangulation
   above for why this is the correct control, not case-text drift left
   unaddressed. ("Back to prompt", `generate-agent-back-button`, is a
   visually-adjacent but functionally distinct control — ELITEA-1919's
   separate case — that returns to the INPUT step rather than closing.)
   - **Verify**: the close action is triggered — confirmed live, resolves
     synchronously with no confirmation dialog / "discard changes?" prompt
     — none appeared, identical to ELITEA-1917's prompt-step Cancel.
3. Verify the modal closes.
   - **Verify**: `generate-agent-modal` is no longer present in the DOM —
     confirmed live via accessibility snapshot immediately after the click:
     the `dialog` element is gone entirely (not merely hidden/inert), the
     page returns to the plain "New Agent" tab view.
4. Verify the New Agent form is still shown with empty/untouched fields.
   - **Verify**: `agent-name-input` and `agent-description-input` are both
     empty (`input_value() == ""`) — confirmed live via
     `page.evaluate()` reading both inputs' `.value` directly immediately
     after the close: both `""`. The review-step draft's generated Name
     ("Billing Support Agent") never bled into the outer New Agent form's
     own Name field — the two are entirely separate inputs, same finding
     class as ELITEA-1917 documented for the prompt-step flow.
5. Verify no new Agent was created in the Agents list.
   - **Verify (primary, deterministic)**: no `POST
     .../elitea_core/applications/prompt_lib/**` (the base-agent CREATE
     call — same route `GenerateAgentModalPage.CREATE_APPLICATION_ROUTE`
     targets) fired at any point during this flow — confirmed live via
     `browser_network_requests` filtered to that route: **zero matches**,
     across the entire open→type→generate→close sequence (the
     `generate_application_draft` call DID fire once, as expected — that's
     this case's own precondition, not a Pass-criteria violation; only the
     CREATE call must be absent).
   - **Verify (secondary, case-literal)**: navigating to
     `${BASE_URL}/agents/all` and reading the visible agent card names
     (`entity-card-name`) shows the generated draft's name
     ("Billing Support Agent" this run) is **absent** — confirmed live via
     `page.evaluate()` reading all `entity-card-name` text content: 2
     pre-existing agents only ("Bullet Summary Agent", "Agent UI Testing"),
     no "Billing Support Agent". Unlike ELITEA-1917 (where no draft is ever
     generated, so there's no name to search for), this case's precondition
     DOES generate a real draft with a real name — so the list-search here
     is a genuine, name-specific secondary confirmation, not merely an
     unchanged-set echo.

## Expected Results
Clicking the modal's Close (X) icon on the GenerateAgentModal's review step
(after a draft has been generated) closes the modal (dialog removed from
the DOM, not merely hidden), leaves the New Agent creation form in its
original empty/untouched state, and creates no agent — the base-agent
CREATE call never fires, and the generated draft's name never appears in
the Agents list. No console errors beyond the pre-existing, unrelated
`disableUnderline` React DOM-attribute warning that fires on every
Build-with-AI run regardless of outcome (documented baseline noise — see
ELITEA-1906/1913/1916's AFS Known Defects; confirmed present, unchanged,
this run too — `browser_console_messages` level=error → exactly 1 result,
that warning, no others).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Generate an agent draft and reach the review/edit form | The review/edit form is displayed with draft data | AFS Step 1 | `modal.wait_for_review_form()` (existing helper); accessibility snapshot confirms populated fields | ready-for-automation (new test) |
| 2 Click "Cancel" | The Cancel action is triggered | AFS Step 2 | **Case-text drift** (filed [#1318](https://github.com/EliteaAI/elitea-testing-public/issues/1318)) — no "Cancel" button exists on the review step; asserted against the live, correct control instead: `modal.close_button.click()` (the modal's X icon, same `handleClose()` semantics as the INPUT-step Cancel button ELITEA-1917 covers) | ready-for-automation (new test) — first assertion-backed `.click()` of `close_button` from the review step; previously only an unasserted cleanup call (ELITEA-1913) |
| 3 Verify the modal closes | GenerateAgentModal is closed and no longer visible | AFS Step 3 | `modal.modal.wait_for(state="hidden", ...)` + `modal.modal.count() == 0` (DOM-absence, same pattern as ELITEA-1917) — confirmed live: dialog fully removed | ready-for-automation (new test) |
| 4 Verify no Agent was created in the Agents list | Navigating to the Agents list shows no new agent was added | AFS Steps 4-5 | Primary: assert no POST fired to `CREATE_APPLICATION_ROUTE` (network-request-log inspection, via `BasePage.capture_requests_matching()` — existing helper, already used by ELITEA-1917's test). Secondary: `AgentsListPage.get_agent_card_names()` does not contain the generated draft's name | ready-for-automation (new test) — network-absence is the deterministic proof; the name-specific list-search is the case-literal echo (stronger than ELITEA-1917's unchanged-set check, because a real name exists here to search for) |

### Axis 2 — Analyst additions

- **Filed case-text drift** ([#1318](https://github.com/EliteaAI/elitea-testing-public/issues/1318)):
  the review step has no "Cancel" button at all — only "Back to prompt" and
  "Create Agent" — *added: this is the load-bearing finding of this
  analysis; without it, an implementer would search the DOM for a
  nonexistent "Cancel"-labelled control on the review step and either fail
  or mis-click "Back to prompt" (which does NOT close the modal — see
  below), silently testing the wrong thing.*
- **Confirmed "Back to prompt" is NOT a substitute for this case** — clicking
  it (not exercised by this AFS's own test, but confirmed via source read
  of `handleBack()`) returns to the INPUT step with the modal still open,
  `draftData` cleared; it does not close the modal and does not create an
  agent either, but it is categorically a different outcome than "modal
  closed" — *added: disambiguates the three review-step outcomes (Back,
  Create, Close-via-X) so no future case conflates them.*
- Confirmed zero console errors beyond the pre-existing, cross-case
  `disableUnderline` warning (`browser_console_messages`, level=error → 1
  result, that warning only) across the full
  open→type→generate→close sequence — *added: side-channel check, standard
  practice per this skill's methodology; the warning itself is documented
  baseline noise (ELITEA-1906/1913/1916), not a regression caused by this
  case's own steps.*
- Confirmed clicking the X icon produces no confirmation/"discard changes?"
  interstitial, even though a full draft (with 5 populated fields + 4 chat
  starters) is discarded — *added: a plausible UX pattern the case text
  doesn't rule out ("are you sure you want to lose this draft?"), ruled out
  live, consistent with ELITEA-1917's identical finding for the
  lighter-weight prompt-step case.*
- Confirmed all testids needed already exist as `LocatorDescriptor` fields
  on `GenerateAgentModalPage`/`AgentFormPage`/`AgentsListPage` (see §
  Concrete Handles) — no `add-data-testid` work needed for this case.

## Cleanup
No product state persists from this case's own steps — the generated draft
is discarded on close, and the create-agent call never fires. No
`agent_api.delete_agent(...)` teardown is needed. (If the implementer
chooses to mock the draft via `mock_generate_success()` instead of using
the real generate endpoint, no cleanup changes — mocking is purely
client-side route interception, nothing persists either way.)

## Concrete Handles (discovered during exploration — all pre-existing)

| Element | Recommended Locator | Provenance |
|---|---|---|
| "Build with AI" open button | `generate-agent-open-button` (`GenerateAgentModalPage.open_button`) | on-main ✓ |
| Modal container | `generate-agent-modal` (`GenerateAgentModalPage.modal`) | on-main ✓ |
| Prompt textarea | `generate-agent-prompt-input` (`GenerateAgentModalPage.prompt_input`) | on-main ✓ |
| Generate Draft button | `generate-agent-submit-button` (`GenerateAgentModalPage.generate_button`) | on-main ✓ |
| **Modal Close (X) icon — this case's core control** | `generate-agent-close-button` (`GenerateAgentModalPage.close_button`) — pre-existing field; previously `.click()`ed only as unasserted test cleanup (ELITEA-1913) | on-main ✓ |
| "Back to prompt" button (NOT this case — disambiguation only) | `generate-agent-back-button` (`GenerateAgentModalPage.back_button`) | on-main ✓ |
| "Create Agent" / approve button (NOT this case — disambiguation only) | `generate-agent-approve-button` (`GenerateAgentModalPage.approve_button`) | on-main ✓ |
| New Agent form Name field | `agent-name-input` (`AgentFormPage.name_input`) | on-main ✓ (confirmed empty after close) |
| New Agent form Description field | `agent-description-input` (`AgentFormPage.description_input`) | on-main ✓ (confirmed empty after close) |
| Agents list card name | `entity-card-name` (`AgentsListPage.entity_card_name`, via `get_agent_card_names()`) | on-main ✓ |
| Base-agent CREATE route | `**/elitea_core/applications/prompt_lib/**` (`GenerateAgentModalPage.CREATE_APPLICATION_ROUTE`) | on-main ✓ — used here only for a **negative** (no-call) network assertion |
| Generate-draft route | `**/elitea_core/generate_application_draft/**` (`GenerateAgentModalPage.GENERATE_DRAFT_ROUTE`) | on-main ✓ — expected to fire ONCE (this case's precondition), unlike ELITEA-1917 where it must never fire |

No new testids required. No new page-object locators required. Every
handle needed already exists in `GenerateAgentModalPage`, `AgentFormPage`,
and `AgentsListPage`.

## Network Behavior
Confirmed live: across the entire open → type-prompt → generate → click-X
sequence, exactly **one** request matched
`**/elitea_core/generate_application_draft/**` (`POST`, `200 OK` — this
case's own precondition, generating the review-step draft), and **zero**
requests matched `**/elitea_core/applications/prompt_lib/**` (`POST`, the
CREATE call) — filtering `browser_network_requests` to both route
substrings confirmed this exact 1-vs-0 split. Only the page's normal
load-time GETs (`support_assistant`, `project_info`, `configurations`,
`permissions`, `tags`, `default_icons`, socket.io polling, etc.) appeared
otherwise, consistent with ELITEA-1905/1917's own Network Behavior notes
for this same modal family.

## Known Defects Found During Exploration
**Case-text drift (not a product defect)** — filed as CLARIFICATION
[#1318](https://github.com/EliteaAI/elitea-testing-public/issues/1318): the
review step has no "Cancel" button; the case's Step 2 ("Click 'Cancel'")
must be reinterpreted as "click the modal's Close (X) icon" per the
reverse-masking guard (live product behavior is correct; the case text's
control name is stale for this step). See § Triangulation for the full
source-level proof.

No functional product defect found — the modal correctly closes via the X
icon from the review step, discards the generated draft, and creates no
agent, exactly matching the case's underlying intent (Pass criteria: "Modal
closes and no agent is created" — satisfied by the live, correctly-named
control).

## Blocked Steps
None. All case elements were executed live this run against the real local
system (`http://localhost:5173`), including a real (unmocked)
`generate_application_draft` call that produced a genuine AI-generated
draft ("Billing Support Agent").

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Add a new,
  standalone test class to
  `automation/tests/ui/agents/test_agent_build_with_ai.py` — e.g.
  `TestAgentBuildWithAICancelFromReviewStep` (mirrors
  `TestAgentBuildWithAICancelFromPromptStep`'s naming, ELITEA-1917). Same
  file, same imports, same fixtures the file's other tests already use
  (`AgentsListPage`, `GenerateAgentModalPage`, `AgentFormPage` if the
  implementer wants the belt-and-suspenders empty-field check).
- **Reuse `BasePage.capture_requests_matching()` / `capture_console_errors()`**
  — the exact infrastructure ELITEA-1917's implementation built and this
  file's `TestAgentBuildWithAICancelFromPromptStep` already uses (see that
  class, `test_cancel_from_prompt_step_closes_modal_without_creating_agent`,
  for the full `try/finally` capture-then-assert-then-`.stop()` pattern).
  No new capture helper needed — only the route filter changes (this case
  doesn't need to assert `generate_application_draft` is ABSENT; it fires
  once, expected, as the precondition).
- **Reaching the review step**: either (a) a real, unmocked
  `generate_button.click()` + `wait_for_review_form()` (confirmed reliable
  this run, real AI response), or (b) `mock_generate_success(draft)` +
  `expect_generate_response()` (the pattern ELITEA-1916's
  `test_creation_failure_stays_on_review_step_and_retry_succeeds` uses) for
  a deterministic, faster draft. Either is sound — this case's Pass
  criteria don't depend on the draft's specific content, only on what
  happens when the X icon is clicked afterward. Mocking is the faster,
  more deterministic choice if the implementer wants to avoid real-AI
  latency/non-determinism in CI.
- **Do not target "Cancel"** — there is no `cancel_button` interaction in
  this test; `close_button` is the control. Do not confuse with
  `back_button` (a distinct, non-closing control — assert its ABSENCE from
  this test's flow only if the implementer wants an extra disambiguation
  assertion; not required by the case's own Pass criteria).
- Suggested flow (illustrative, not prescriptive):
  ```python
  with allure.step("Step 1 — Generate a draft and reach the review form"):
      list_page.navigate_to_create()
      modal.open_modal()
      modal.fill_prompt(CANCEL_FROM_REVIEW_PROMPT_TEXT)
      modal.mock_generate_success(CANCEL_FROM_REVIEW_DRAFT_PAYLOAD)  # or real click, see hint above
      with modal.expect_generate_response(timeout=GENERATE_RESPONSE_TIMEOUT) as response_info:
          modal.generate_button.click()
      assert response_info.value.status == 200
      modal.wait_for_review_form(timeout=REVIEW_FORM_TIMEOUT)

  with allure.step("Step 2 — Click the modal's Close (X) icon (no 'Cancel' button exists on this step)"):
      modal.close_button.click()

  with allure.step("Step 3 — Verify the modal closes"):
      modal.modal.wait_for(state="hidden", timeout=NAVIGATION_TIMEOUT)
      assert modal.modal.count() == 0

  with allure.step("Step 4 — Verify the New Agent form is untouched"):
      assert form_page.name_input.input_value() == ""
      assert form_page.description_input.input_value() == ""

  with allure.step("Step 5 — Verify no agent was created"):
      assert not create_requests, f"got: {list(create_requests)}"
      list_page.navigate()
      assert CANCEL_FROM_REVIEW_DRAFT_PAYLOAD["name"] not in list_page.get_agent_card_names()
  ```
- Timeout constants: reuse this file's existing `NAVIGATION_TIMEOUT`
  (15000), `GENERATE_RESPONSE_TIMEOUT`, `REVIEW_FORM_TIMEOUT` — all already
  defined (ELITEA-1915/1916 introduced them), no new constants needed.
- Marker: `@pytest.mark.p2` + `@pytest.mark.regression`, consistent with
  this file's other Build-with-AI cases and this case's own `l2`/`medium`
  priority.
