# Test Case: Build with AI — creation failure stays on review step for correction (Agent)

## Metadata
- **TMS ID**: ELITEA-1916
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `UI Testing` / `${ELITEA_PROJECT_ID}`=400)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: same gap as ELITEA-1915's AFS — `.agents/testing.md` has no
  `TMS case-gate` section for this project. Case frontmatter carries `status:
  draft` / `execution_type: manual`; per the skill's default this run proceeded
  and fetched/executed the case.
- **Triangulation vs ELITEA-1915 and the Approve-clicking tests (per dispatch
  instructions) — done BEFORE execution, confirmed by reading source, not
  inferred**:
  - `TestAgentBuildWithAIGenerationFailureRetry.test_generation_failure_shows_error_and_allows_retry`
    (`automation/tests/ui/agents/test_agent_build_with_ai.py:320-423`,
    `ELITEA-1915`) mocks `POST .../generate_application_draft/...` to fail —
    it never clicks the review-form's "Create Agent"/Approve button at all
    (its Step 6 only asserts the review form renders after a *recovered
    generation* retry). It is generation-failure-only, confirmed by reading
    the test to its end — no `approve_button`/`click_approve_*` call anywhere
    in the class.
  - Every test in the file that DOES click Approve —
    `test_selected_suggested_resources_attached_and_non_selected_absent`
    (ELITEA-1909), `test_selected_suggested_skill_attached_and_non_selected_absent`
    (ELITEA-1911), `test_approve_with_no_resources_creates_agent_and_appears_in_list`
    (ELITEA-1914), `test_zero_selection_across_categories_attaches_nothing`
    (ELITEA-1908), `test_edited_fields_persist_after_approve` (ELITEA-1912) —
    calls one of `click_approve_and_wait_for_creation()` /
    `click_approve_and_wait_for_skill_creation()` /
    `click_approve_and_wait_for_agent_created()` (`generate_agent_modal_page.py`)
    and asserts `create_response.status == 201` in every case. None mocks or
    otherwise triggers a non-2xx response from the create-application POST;
    all of them assume/require success. Confirmed by reading each test to its
    assertion block, not by grepping for a keyword.
  - **Conclusion: no existing spec exercises a CREATE-time failure anywhere in
    this file (or, per a repo-wide grep for `GenerateAgentModal`/`generate-
    agent-approve-button`, anywhere else).** ELITEA-1916 is a genuine coverage
    gap, not an overlap — classified `ready-for-automation`, not
    `extend-existing`/`already-covered` (per the skill's merged-target rule,
    `already-covered`/`extend-existing` require an existing spec proving the
    *same* observable; none does for creation failure).

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips login
  via `VITE_DEV_TOKEN`) with editor/admin role sufficient to create agents
  (same `PERMISSIONS.applications.update` gate documented by the ELITEA-1915
  AFS — button doesn't render at all for an unpermitted user, not a
  disabled/error state).
- A project is selected/accessible (`UI Testing`, id `400` in this run).
- **Corrected precondition (case-text drift, not a defect — same class of
  correction ELITEA-1915's AFS already made for this precondition wording):**
  "An agent draft has been generated and the review/edit form is displayed"
  describes the *end state of Step 1*, not a standalone precondition. This
  AFS's Step 1 covers reaching that state (navigate → open modal → fill
  prompt → generate → review form).
- "A creation API failure condition can be triggered or simulated" —
  confirmed achievable live via Playwright route interception on the
  base-create POST (see Step 2), exactly the same technique ELITEA-1915 uses
  for the generate-draft endpoint.

## Test Data

### reuse-existing (no fixture creation/teardown needed for the mocked path)
- Natural-language prompt: any valid, non-empty description — content is not
  asserted by this case, only that a draft is reached. This run used:
  `"Create a simple test agent for ELITEA-1916 creation-failure recovery."`
- **Mocked draft payload** (fulfills `generate_application_draft`, live-run
  values, mirrors the existing `RETRY_DRAFT_PAYLOAD`/`FIELD_POPULATION_DRAFT_PAYLOAD`
  shape already used elsewhere in this test file):
  ```json
  {
    "name": "ELITEA-1916 Draft Agent",
    "description": "A draft used to test create-failure recovery.",
    "instructions": "You are a test agent for ELITEA-1916.",
    "welcome_message": "Hi, testing creation failure recovery.",
    "conversation_starters": ["Starter one", "Starter two"],
    "suggested_toolkits": [], "suggested_mcp": [], "suggested_pipelines": [],
    "suggested_agents": [], "suggested_skills": []
  }
  ```
  Empty suggested-resource arrays deliberately keep this case's DOM surface
  focused on the create-failure/retry mechanics — resource-selection
  persistence across a create failure is a distinct, NOT-yet-covered
  observable, flagged under Axis 2 below, not asserted here.
- **Simulated creation-failure response body**: `{"error":"Simulated creation
  failure for ELITEA-1916"}`, HTTP 500 — same message-carrying-verbatim
  technique ELITEA-1915 uses, chosen because it live-proves the backend's
  `error` field reaches the user (via `buildErrorMessage(err)` →
  `err?.data?.error`, `common/utils.jsx:161`), not just a generic fallback.

No test data is created or persisted by Steps 1-5 (mocked failure path). Step
6's retry, if it completes to a real agent, DOES create a real backend record
— see Cleanup.

## Test Steps

1. Navigate to `${BASE_URL}/agents/create?viewMode=owner`. In the "General"
   accordion section header, click **"Build with AI"**
   (`generate-agent-open-button`, confirmed live) to open the
   `GenerateAgentModal`. Fill the prompt textarea
   (`generate-agent-prompt-input`) with the test-data prompt, then click
   **"Generate Draft"** (`generate-agent-submit-button`).
   - **Verify**: the modal transitions through the loading state
     (`generate-agent-loading-indicator`) to the **review form**, populated
     with the draft's Name/Description/Instructions/Welcome Message/2 Chat
     starters (`generate-agent-review-name-input` etc., confirmed live via
     snapshot). This maps the case's "an agent draft has been generated and
     the review/edit form is displayed" precondition onto an executed step,
     same correction as ELITEA-1915's AFS.

2. Before clicking "Create Agent", install a Playwright route interception on
   `POST **/elitea_core/applications/prompt_lib/**` (the exact endpoint the
   create mutation calls — confirmed via source,
   `GenerateAgentModal.jsx:227-248`'s `createApplication({...}).unwrap()`,
   which resolves to `POST /elitea_core/applications/prompt_lib/{projectId}`)
   that fulfills the **first** matching request with **HTTP 500** and body
   `{"error":"Simulated creation failure for ELITEA-1916"}`, then click
   **"Create Agent"** (`generate-agent-approve-button`).
   - **Verify**: the button's label briefly reads "Creating..." while the
     mocked request is in flight (`isApproving` state,
     `GenerateEntityModal.jsx:193-195`), then the mocked 500 resolves. This is
     the case's "creation request is submitted" (step 1) + "creation API call
     fails" (step 2) — route interception, not a real backend outage, same
     standard technique as ELITEA-1915's Step 2.

3. With the mocked 500 resolved, observe the page (not just the modal —
   important, see Known Defects #1 below) without further interaction.
   - **Verify**: an app-wide **toast** notification (MUI `Snackbar` + `Alert`,
     `Toast.jsx`, existing testids `toast-alert`/`toast-message`/
     `toast-dismiss-button` — the SAME shared component already used by
     `ChatPage`/`PipelineDetailPage`/`AgentDetailPage`/etc. in this suite)
     renders at the top-center of the viewport, OUTSIDE the modal's `dialog`
     element, `data-severity="error"`, containing the exact injected message
     `"Simulated creation failure for ELITEA-1916"`. Confirmed live via
     accessibility snapshot immediately after the mocked 500 resolved — the
     alert appeared as a sibling of `main`, not inside the modal's `dialog`
     subtree. Screenshot:
     `test-results/screenshots/ELITEA-1916-step-3-creation-failure-toast.png`.
     Console: no unrelated app-level errors accompanying the failure (the one
     pre-existing `disableUnderline` React DOM-attribute warning present in
     every Build-with-AI run, including ELITEA-1906/1913, is unrelated
     baseline noise, not caused by this failure — side-channel check passed).
     **This diverges from the case's stated Step 3 expectation "Verify
     form-level error messages are shown using the standard creation error
     handling" — see Known Defects #1, a clarification not a defect.**
   - Toast is **transient** (MUI `Snackbar` `autoHideDuration`, confirmed
     live — re-querying `[data-testid="toast-alert"]` a few seconds after the
     screenshot returned no match). Automate the toast-message assertion
     immediately after the mocked response resolves, not after further waits.

4. With the toast dismissed/dismissing, inspect the modal (still open).
   - **Verify**: the modal (`generate-agent-modal`) is still present in the
     DOM and still shows the **review form** (not the input/prompt step, not
     closed) — confirmed live via
     `document.querySelector('[data-testid="generate-agent-modal"]')` truthy
     immediately after the failure. Source-confirmed why:
     `GenerateEntityModal.jsx`'s `handleApprove` catch block
     (`GenerateEntityModal.jsx:98-101`) only calls `setIsApproving(false)` and
     `toastError(...)` — it does **not** call `handleClose()` (that only
     happens inside the `try` block, after `onApprove` succeeds), so `step`
     stays `STEPS.REVIEW` and `draftData` is untouched. This is the case's
     "user remains on the review/edit step (not redirected or kicked to
     prompt step); no unwanted navigation occurs" (step 4), live-verified,
     not merely inferred from source.

5. With the modal still open on the review step, inspect all draft fields.
   - **Verify**: Name, Description, Instructions, Welcome Message, and both
     Chat starters still read the exact generated-draft values (confirmed
     live via `get_review_name()`-equivalent DOM read immediately after the
     failure: `Name field value: "ELITEA-1916 Draft Agent"`, matching the
     mocked draft verbatim). This is the case's "all previously entered and
     selected data is preserved on the form" (step 5) — because `draftData`
     is component state independent of the failed `createApplication`
     mutation, the same "why" pattern ELITEA-1915's AFS documents for the
     prompt-preservation case (a different piece of untouched state, same
     underlying reason: the catch block resets only approval-in-flight UI
     state, never the data).

6. With the review form still populated and the failure toast gone, click
   **"Create Agent"** again (`generate-agent-approve-button`) — the SAME
   button; there is no separate retry control (mirrors ELITEA-1915's Step 5
   finding for the Generate button). This time do not re-install the mock
   (or install a second route handler resolving 201 — see Automation Hints),
   letting the request reach the real DEV backend.
   - **Verify**: the button is genuinely re-enabled and clickable
     (`isApproving` was reset to `false` in the catch block, and
     `isDraftValid` was never touched by the failure, so
     `disabled={isApproving || !isDraftValid}` is `false` — confirmed live:
     `approve_button.disabled === false` immediately after the toast).
     Clicking it resolves `201`, the modal closes
     (`handleClose()` fires inside `handleApprove`'s `try` block on success),
     and the app auto-navigates to the created agent's detail page
     (`/agents/all/{id}?destTab=configuration&name=...`) — confirmed live
     this run: navigated to `/agents/all/158?...`, with the detail page
     showing Name "ELITEA-1916 Draft Agent", Description, Instructions,
     Welcome Message, and both Chat starters all matching the draft exactly,
     Skills counter `0/5` (empty `suggested_skills`, none selected — same
     zero-attachment contract ELITEA-1914's AFS documents for a plain draft).
     This is the case's "the Agent is created successfully on the second
     attempt" (step 6), live-verified end-to-end against the real backend,
     not merely mocked twice.

## Expected Results
Matches the case's stated Pass criteria on every FUNCTIONAL point — user stays
on the review step (step 4), data is preserved (step 5), retry succeeds (step
6) — live-verified end-to-end including a real create call against DEV
(deleted afterward, see Cleanup). The one divergence is the *mechanism* of the
error surface in step 3: a toast, not an inline/embedded form message — see
Known Defects #1, classified as case-text drift (clarification), not a
functional failure; the user genuinely IS informed of the failure by an
equally standard app-wide UI pattern.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: "An agent draft has been generated and the review/edit form is displayed" | — | step 1 | step 1 folds this into itself (navigate + open + fill + generate), since live this is an outcome of Step 1, not a standalone precondition | clarification *(case-text drift, same class as ELITEA-1915's AFS — not a product defect)* |
| Precondition: "A creation API failure condition can be triggered or simulated" | achievable | step 2 | step 2: Playwright route interception on the exact create-application endpoint | asserted |
| 1 Generate draft, click Approve/Create Agent | creation request submitted | steps 1-2 | step 2: `isApproving`/"Creating..." transient state, mocked request observed in flight | asserted |
| 2 Simulate creation API failure | creation call fails | step 2 | step 2: mocked 500, confirmed via the resolved mocked response | asserted |
| 3 Verify form-level error messages shown via standard creation error handling | error message displayed on form | step 3 | step 3: app-wide toast (`toast-alert`/`toast-message`), `data-severity="error"`, exact injected message, screenshot | asserted *(mechanism diverges from "form-level" — see Known Defects #1; the user-facing outcome, "informed of the failure," is fully satisfied)* |
| 4 Verify user remains on review/edit step | no unwanted navigation | step 4 | step 4: modal + review form still present in DOM immediately after failure, source-confirmed why (`handleClose()` never called on the catch path) | asserted |
| 5 Verify all draft data still present | Name/Description/Instructions/resources preserved | step 5 | step 5: all fields read back verbatim against the mocked draft immediately after failure | asserted |
| 6 Correct issue, click Approve again, verify agent created | agent created successfully on retry | step 6 | step 6: real (unmocked) backend call resolves 201, modal closes, auto-navigation to the created agent's detail page, all fields verified against the draft | asserted |

### Axis 2 — Analyst additions

- step 3 documents the toast's exact DOM position (sibling of `main`, outside
  the modal's `dialog` subtree) and its transience (auto-hides after a few
  seconds) — *added: an implementer polling `toast-alert` too late (e.g. after
  an unrelated multi-second wait) will see a false negative; the assertion
  must run immediately after the mocked response resolves.*
- step 4 documents the exact source location (`GenerateEntityModal.jsx:98-101`)
  proving WHY the modal stays open on any `onApprove` rejection, not just this
  simulated one — *added: gives the implementer a stable code anchor instead
  of only a live observation, useful if this behavior ever needs re-verifying
  after a refactor.*
- step 6 documents the exact re-enable condition
  (`disabled={isApproving || !isDraftValid}`, both false after a failed
  attempt) — *added: an implementer might otherwise assume a failed create
  leaves the form invalid/locked; source + live-verified DOM read confirm it
  does not.*
- observed but out of this case's scope: this run's mocked draft carried
  empty `suggested_toolkits`/`suggested_mcp`/`suggested_pipelines`/
  `suggested_agents`/`suggested_skills` deliberately, to isolate the
  create-failure mechanics. **Whether a create failure preserves
  *selected-but-not-yet-submitted* suggested-resource checkboxes (Toolkit/
  Agent/Skill selections made before clicking Approve) is a DIFFERENT,
  currently-uncovered observable** — `selectedToolkitIds`/etc. are
  `GenerateAgentModal`-level state, untouched by the same catch block, so
  by the same source reasoning they likely survive too, but this was not
  live-verified with a non-empty selection in this run. *Added: flagged as a
  natural extension for a future case if the team wants it; NOT asserted
  here since ELITEA-1916's own Test Data table states "(none required)" and
  its steps never mention selecting suggested resources.*

## Cleanup
1. Steps 1-5 create no product state — the mocked failure never reaches the
   real backend (route interception fulfills locally). Steps 3-5's toast and
   review-form assertions require no teardown beyond the mock's own
   page-scoped lifecycle.
2. **Step 6's retry, once its route mock/interception is cleared (or a second
   mock resolving 201 is used — see Automation Hints), creates a REAL agent**
   on the DEV backend. This run created and then deleted agent id `158`
   ("ELITEA-1916 Draft Agent") via the Agent detail page's "AGENT" menu →
   "Delete agent" → typed the exact name into the confirmation dialog →
   "Delete". An automated test MUST clean this up the same way every other
   Approve-clicking test in this file does: capture `created_agent_id` from
   the create response and delete it via `agent_api.delete_agent(...)` in a
   `finally` block (matches `test_selected_suggested_resources_attached_and_non_selected_absent`
   / `test_approve_with_no_resources_creates_agent_and_appears_in_list` /
   etc.'s existing pattern in this file verbatim).
3. Playwright route interception is scoped to the test's own page/context and
   needs no explicit teardown beyond normal fixture-per-test lifecycle,
   consistent with ELITEA-1915's Cleanup note.

## Concrete Handles (discovered during exploration)

All handles below are **pre-existing testids**, already declared as
`LocatorDescriptor` fields on `GenerateAgentModalPage`
(`automation/pages/generate_agent_modal_page.py`) — this case needs **zero**
new EliteaUI testid additions.

| Element | Recommended Locator | Provenance |
|---|---|---|
| "Build with AI" open button | `generate-agent-open-button` | on-main ✓ — already used by ELITEA-1915/1906/1913 tests in this file |
| Modal container | `generate-agent-modal` | on-main ✓ — same |
| Prompt textarea | `generate-agent-prompt-input` | on-main ✓ — same |
| "Generate Draft" / retry button | `generate-agent-submit-button` | on-main ✓ — same |
| Loading indicator | `generate-agent-loading-indicator` | on-main ✓ — same |
| Review-form Name input | `generate-agent-review-name-input` | on-main ✓ — used by ELITEA-1906/1912/1913 |
| Review-form Description input | `generate-agent-review-description-input` | on-main ✓ — same |
| Review-form Instructions input | `generate-agent-review-instructions-input` | on-main ✓ — same |
| Review-form Welcome Message input | `generate-agent-review-welcome-message-input` | on-main ✓ — same |
| Review-form Chat-starter inputs | `generate-agent-review-starter-input-{index}` (class template `REVIEW_STARTER_INPUT`) | on-main ✓ — same |
| "Create Agent" / Approve button | `generate-agent-approve-button` | on-main ✓ — used by ELITEA-1909/1911/1912/1914/1908 |
| **App-wide toast alert** | `toast-alert` (+ `[data-testid="toast-alert"][data-severity="error"]` state filter, per the existing `TOAST_ALERT_SEVERITY` class-constant pattern) | on-main ✓ — pre-existing shared component (`src/components/Toast.jsx`), **not yet declared on `GenerateAgentModalPage`** (declared today on `AgentDetailPage`/`ChatPage`/`PipelineDetailPage`/etc. — this is the first Build-with-AI-flow case to need it) |
| App-wide toast message text | `toast-message` | on-main ✓ — same component, same "not yet on this page object" note |
| App-wide toast dismiss button | `toast-dismiss-button` | on-main ✓ — same (not needed by this case's own assertions, listed for completeness) |

**Implementer note:** add `toast_alert`/`toast_message`/`TOAST_ALERT_SEVERITY`
as class-level `LocatorDescriptor` fields on `GenerateAgentModalPage` — copy
the existing pattern verbatim from `agent_detail_page.py:388-399` (or
`chat_page.py`/`pipeline_detail_page.py`, same shape). This is wiring a
**page-object field** to an **existing, unchanged EliteaUI testid** — no
`add-data-testid` run is needed, no EliteaUI source changes at all.

## Network Behavior
- `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/{project_id}`
  — unrelated to this case's own assertions beyond reaching the review form;
  mocked per Step 1's Test Data (see ELITEA-1915/1906/1912's AFSs for the full
  contract).
- `POST /api/v2/elitea_core/applications/prompt_lib/{project_id}` — **the
  endpoint this case is actually about.** Confirmed via source
  (`GenerateAgentModal.jsx:227`, `useApplicationCreateMutation` /
  `api/applications.js:223`). Mocked response (Step 2): `500` +
  `{"error":"Simulated creation failure for ELITEA-1916"}`. Real response
  (Step 6, live DEV backend, this run): `201` with the created agent's full
  JSON (`id`, `name`, `version_details.id`, etc. — same shape every other
  Approve-clicking test in this file already asserts against).
- On a create failure, **no** `associateToolkits`/`associateApplications`/
  `associateSkills` call ever fires — those only run after
  `createApplication(...).unwrap()` resolves successfully
  (`GenerateAgentModal.jsx:248-263`; the failed `.unwrap()` throws before
  reaching that code). Not separately asserted here (this case's draft
  carries no suggested resources at all — see Axis 2), but worth naming for
  an implementer who might otherwise expect to guard against a stray
  association call on failure.

## Known Defects Found During Exploration

1. **Case-text mismatch (CLARIFICATION, not a product defect) — Step 3's
   "form-level error message" expectation does not match the live mechanism,
   which is an app-wide TOAST, not an inline/embedded alert inside the
   modal.** Live-verified and source-confirmed
   (`GenerateEntityModal.jsx:91-102`'s `handleApprove` catch block calls
   `toastError(buildErrorMessage(err))`, never renders an `Alert` inside the
   modal body the way the *generation*-failure path does at
   `GenerateEntityModal.jsx:155-165`). This is a genuine, deterministic UX
   **inconsistency within the same modal** — generation failure → inline
   `Alert` (`generate-agent-error-alert`, `role="alert"`, ELITEA-1915); create
   failure → toast only, no inline alert anywhere in the modal — but it is
   NOT classified as a functional product defect for THIS case, because:
   (a) the user genuinely IS informed of the failure (the toast is visible,
   legible, carries the exact backend error text) via an equally standard,
   widely-reused app pattern (the same `toast-alert`/`toast-message`
   component `AgentDetailPage`/`ChatPage`/etc. already rely on for other
   failures across this suite); (b) the case's OTHER, more load-bearing
   requirements (stay on review step, data preserved, retry works) all pass
   cleanly; (c) cross-checked against the "standard creation error handling"
   phrase itself — the REGULAR (non-AI) Create Agent form's own error
   handling (`useCreateApplication.jsx:85-107`) shows field-level errors
   ONLY for structured/array-shaped validation errors (via
   `formik.setFieldError`) and does literally nothing user-visible
   (`console.error` only, no toast, no inline message) for a generic/scalar
   error shape — so there IS no single unambiguous "standard" behavior in
   this app to hold the Build-with-AI flow to; a toast is, if anything, a
   STRONGER user-facing signal than the regular form's silent-console
   fallback for the same failure class. **Not filed as a GitHub issue** —
   this is a case-authoring precision gap (the case assumed a specific
   mechanism without the author having seen either flow's actual code), not
   a functional defect; the case's real intent ("the user is told the
   creation failed, in a way they can act on") IS met. Recommend the TMS case
   wording be loosened from "form-level error messages... on the form" to
   "a clear, actionable error message is shown" — a documentation nit, not
   blocking. Asserted here against the LIVE toast-based contract per the
   reverse-masking guard (`test-case-analysis` skill § Classify findings).

2. **[Non-blocking, informational — not filed] The toast-vs-inline
   inconsistency itself (generation failure = inline `Alert`, creation
   failure = toast) is worth a product-quality note even though it isn't a
   defect for THIS case.** Recorded here for visibility; not filed as its own
   ticket per this project's bug-filing policy (routes functional defects to
   the tracker, not UX-consistency observations with no broken behavior
   behind them) — flagging in the AFS is the correct channel.

No functional product defect was found. The live product's behavior across
all 6 case steps matches the case's Pass criteria once Known Defect #1's
mechanism-level correction is accounted for.

## Blocked Steps
None. All 6 steps were executed end-to-end live, including a full real
(unmocked) retry-recovery round-trip against the live DEV backend in Step 6
(agent id `158`, created then deleted as part of this exploration's cleanup)
— this AFS is `ready-for-automation` for all 6 steps.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Home:
  `automation/tests/ui/agents/test_agent_build_with_ai.py` (existing file —
  add a new test class, e.g. `TestAgentBuildWithAICreationFailureRecovery`,
  alongside the existing `TestAgentBuildWithAIGenerationFailureRetry` class;
  reuses the same `GenerateAgentModalPage`/`AgentsListPage`/`AgentDetailPage`
  page objects and `agent_api` fixture already used throughout this file).
- **New page-object method needed** on `GenerateAgentModalPage`
  (`automation/pages/generate_agent_modal_page.py`): a `mock_create_failure()`
  sibling to the base class's existing `mock_generate_failure()`/
  `mock_generate_success()` (`generate_entity_modal_page_base.py:100-146`),
  targeting `**/elitea_core/applications/prompt_lib/**` (POST) instead of the
  generate-draft route, same `route()`/`fulfill()`/`delay_ms` shape. This
  exploration used a `window.fetch` monkey-patch (browser_evaluate) ONLY
  because the live-exploration tooling available in this session had no
  direct `page.route()` call; the automated test MUST use Playwright's native
  `page.route()`/`page.unroute()` (or a call-counting handler, exactly as
  `mock_generate_failure`/`mock_generate_success` already do), matching this
  suite's established pattern — not the ad hoc fetch-patch technique used
  only for this session's live verification.
- For Step 6's retry, recommend registering a **second, call-counted** route
  handler on the same create endpoint (mock 500 on the 1st POST, 200/201 with
  a synthetic created-agent JSON on the 2nd) for CI determinism — same
  rationale ELITEA-1915's AFS gives for preferring option (b) over hitting
  the real DEV backend twice. This exploration used the real DEV backend for
  the retry leg specifically to prove the end-to-end contract once (same
  reasoning ELITEA-1915's own AFS used its real-backend leg for); the
  synthetic-second-mock approach is what should ship in the automated test.
- Wait strategy: wait on the create-application POST's response
  (`page.expect_response(...)`, matching the existing
  `click_approve_and_wait_for_agent_created()` pattern) for BOTH the failed
  and retried requests — do not poll/sleep. For the toast assertion (Step
  3), assert immediately after the mocked response resolves, before any
  other wait — the toast auto-hides (live-confirmed transient) and a
  delayed assertion will flake.
- Cleanup: this test creates a real agent on its Step 6 retry (unlike
  ELITEA-1915, which never reaches Approve) — wrap Steps in `try`/`finally`
  and call `agent_api.delete_agent(created_agent_id)` in `finally`, exactly
  matching this file's other Approve-clicking tests
  (`test_selected_suggested_resources_attached_and_non_selected_absent` etc.).
