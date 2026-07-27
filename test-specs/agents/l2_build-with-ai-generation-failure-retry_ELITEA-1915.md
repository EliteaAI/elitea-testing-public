# Test Case: Build with AI — generation failure shows error and allows retry (Agent)

## Metadata
- **TMS ID**: ELITEA-1915
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: `.agents/testing.md` has no `TMS case-gate` section defining
  excluded statuses for this project. The case file's own frontmatter carries
  `status: draft` / `execution_type: manual` — per the skill's default
  ("if absent, default to fetching all and flag the gap"), this run proceeded
  and fetched/executed the case; flagging the gap here for scout to fill
  `.agents/testing.md` § TMS case-gate (which statuses, if any, should actually
  skip fetch — `draft` here reads as "not yet automated", not "author says
  skip", but that's an inference, not a documented policy).

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips login
  via `VITE_DEV_TOKEN`) with editor/admin role sufficient to create agents
  (confirmed live: the "Build with AI" entry point is gated behind
  `PERMISSIONS.applications.update` — `GenerateEntityButton.jsx` returns `null`
  if the permission check fails, i.e. the button silently doesn't render for
  an unpermitted user rather than showing a disabled state or message. Not a
  defect — matches this project's existing family of `useCheckPermission`
  gates elsewhere — but worth naming since it means a permission-denied
  scenario for this case is "button absent", not "button disabled/error").
- A project is selected/accessible (`Private`, id `399` in this run).
- **Corrected precondition (case-text drift, not a defect):** the case's
  stated precondition "The GenerateAgentModal is open with a prompt entered"
  actually describes the *end state of Step 1*, not a precondition — the live
  entry point is the **Agent create form** (`${BASE_URL}/agents/create`),
  General section header, "Build with AI" button (`GenerateAgentButton.jsx`,
  rendered as a `summaryAction` on the "General" accordion in
  `CreateAgentForm.jsx:106`). This AFS's Step 1 covers navigating there and
  opening the modal; the case's own precondition line is folded into Step 1
  below rather than treated as a separate setup requirement.
- "A network or service failure condition can be triggered or simulated" —
  confirmed achievable live via Playwright route interception (see Step 2).

## Test Data

### reuse-existing (no fixture creation/teardown needed)
- Natural-language prompt (any valid description text, per case): `"Create a
  customer support triage agent that categorizes incoming tickets by urgency
  and routes them to the correct team."` — live-verified: any non-empty,
  non-whitespace string enables the Generate button
  (`disabled={!description.trim()}` in `GenerateEntityModal.jsx:198`); content
  is not otherwise asserted by this case.
- Simulated failure response body: `{"error":"Simulated generation failure for
  ELITEA-1915"}`, HTTP 500. Chosen because the live error-display code
  (`GenerateEntityModal.jsx:147-149`) reads `generateError?.data?.error ||
  generateError?.data?.detail || 'Failed to generate. Please try again.'` —
  using a custom, case-ID-tagged message live-proves the *actual* backend
  error surfaces verbatim (not just the generic fallback), which is a
  stronger assertion than only checking "some alert is shown".

No test data is created or persisted in the product (no agent, skill,
toolkit, etc. is left behind by Steps 1-5). Step 6, if it completes to a real
generated draft, produces draft *review-form* data only — the draft is never
submitted/approved in this AFS, so nothing needs deletion. See Cleanup.

## Test Steps

1. Navigate to `${BASE_URL}/agents/create?viewMode=owner` (via the Agents
   list "Agent" create button, `data-testid="sidebar-create-button"` —
   confirmed live). In the "General" accordion section header, click the
   **"Build with AI"** button (no testid — see Concrete Handles) to open the
   `GenerateAgentModal`. Fill the prompt textarea (no testid — accessible
   name `"Describe your agent's goal, key tasks, and preferred tone or
   behavior."`) with the test-data prompt.
   - **Verify**: the textarea contains exactly the entered text; the
     **"Generate"** button (no testid, disabled while the field is
     empty/whitespace-only) becomes enabled once non-empty text is present.
     Confirmed live via snapshot before/after fill.

2. Before clicking Generate, install a Playwright route interception on
   `POST **/elitea_core/generate_application_draft/**` (the exact endpoint
   the mutation calls — confirmed via source,
   `generateAgentDraftApi.js:7`: `/elitea_core/generate_application_draft/prompt_lib/{projectId}`)
   that fulfills with **HTTP 500** and body
   `{"error":"Simulated generation failure for ELITEA-1915"}`. Click
   **"Generate"**.
   - **Verify**: the modal transitions to a brief loading state
     (`"Generating agent draft..."` + spinner, confirmed live in a poll
     immediately after click), then the mocked request resolves 500 and the
     UI reverts to the input step. Network panel confirms
     `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/399 =>
     [500]`. This is the case's "trigger or simulate a generation failure"
     step — route interception, not a real backend outage, per the
     standard technique for this class of assertion (no dependency on an
     actual flaky/unavailable service).

3. With the mocked 500 still resolved, observe the modal without further
   interaction.
   - **Verify**: a MUI `Alert severity="error"` (`role="alert"`, confirmed
     via accessibility snapshot) renders inside the modal body, directly
     below the prompt textarea, containing the exact injected message:
     `"Simulated generation failure for ELITEA-1915"`. This confirms the live
     component surfaces the backend's `error` field verbatim
     (`generateError?.data?.error`, `GenerateEntityModal.jsx:147`) rather
     than only ever showing the generic `"Failed to generate. Please try
     again."` fallback. Screenshot:
     `test-results/screenshots/ELITEA-1915-step-3-error-state.png`. Console:
     exactly one `[ERROR] Failed to load resource: … 500 …` entry for the
     mocked endpoint — no unrelated app-level console errors accompanying
     the failure (side-channel check passed).

4. Inspect the prompt textarea state in the same (still-open) modal.
   - **Verify**: the textarea still contains the exact prompt text entered
     in Step 1, unmodified — confirmed live via accessibility snapshot
     immediately after the failure (Step 3's screenshot shows both the alert
     AND the intact prompt text in the same view). Source-confirmed why:
     `GenerateEntityModal.jsx`'s `handleGenerate` catch block
     (`GenerateEntityModal.jsx:70-73`) only resets `step` back to
     `STEPS.INPUT` — it does **not** clear the `description` state, which is
     independent local component state untouched by the failed mutation.

5. Remove the route interception (letting the endpoint hit the real DEV
   backend) and click **"Generate"** again (the same button — the modal has
   no separate "Retry" control; the case's "retry / Generate agent button"
   step 5 language maps directly onto re-clicking the one **Generate**
   button already used in Step 2 — see Known Defects/Clarification #1).
   - **Verify**: `resetGenerate()` fires before the retry request
     (`GenerateEntityModal.jsx:59`), clearing the prior `generateError` state
     immediately — the modal shows the loading state again
     (`"Generating agent draft..."`), NOT a stale copy of the Step 3 error
     alongside the new attempt. Confirmed live: the error alert is gone as
     soon as the retry request is in flight.

6. Wait for the retried (real, unmocked) request to resolve.
   - **Verify**: the live DEV backend recovered and returned a real draft
     (confirmed live in this run — polled every 5s, resolved within ~30s).
     The modal transitions from the loading state directly to the **review
     form** (`GenerateAgentReviewForm`), populated with a generated Name,
     Description, Instructions, Welcome Message, and 4 conversation
     starters (all non-empty, contextually relevant to the prompt — e.g.
     Name: `"Support Ticket Triage Agent"`). Actions row shows **"Back to
     prompt"** and **"Create Agent"**. Screenshot:
     `test-results/screenshots/ELITEA-1915-step-6-review-form.png`. Console:
     zero new errors during the successful retry/transition (only the
     earlier, expected Step 2 mocked-500 entry remains in the log).
     This is the case's "if service recovers, the modal transitions to the
     review form with a generated draft" outcome — live-verified end-to-end
     against the real backend, not asserted only against a second mock.

## Expected Results
Matches the case's stated Pass criteria exactly, live-verified end-to-end:
error message displayed on failure (Step 3), prompt preserved after failure
(Step 4), retry available and functional (Step 5), and — when the service
recovers — the retry successfully produces a new draft and transitions to
the review form (Step 6). No step produced an unexpected result; no
clarification changes the case's pass/fail semantics (only the entry-point
precondition wording, per Known Defects #1, is a text-level correction).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: "The GenerateAgentModal is open with a prompt entered" | — | step 1 | step 1 folds this into itself (navigate + open + fill), since live this is an outcome of Step 1, not a standalone precondition | clarification *(case-text drift — see Known Defects #1; not a product defect)* |
| Precondition: "A network or service failure condition can be triggered or simulated" | achievable | step 2 | step 2: Playwright route interception on the exact generate-draft endpoint | asserted |
| 1 Open modal, enter description | input field contains entered description | step 1 | step 1: snapshot shows textarea value == entered text | asserted |
| 2 Trigger/simulate generation failure | generation attempt fails | step 2 | step 2: mocked 500, network panel + loading→input transition confirmed | asserted |
| 3 Verify clear error message displayed | error message shown in modal | step 3 | step 3: `role="alert"` with exact injected message text, screenshot | asserted |
| 4 Verify prompt still present after failure | prompt text still visible | step 4 | step 4: textarea value unchanged, source-confirmed why (`description` state untouched by failed mutation) | asserted |
| 5 Click retry / "Generate agent" button | generation is retried | step 5 | step 5: re-click the same Generate button (no separate retry control exists), error cleared, loading state re-entered | asserted *(see Known Defects #1 — the case implies a distinct "retry" affordance; live product reuses the single Generate button, which fully satisfies the case's functional intent)* |
| 6 Verify retry succeeds and (if service recovers) draft returned | modal transitions to review form with generated draft | step 6 | step 6: real (unmocked) backend call succeeds, review form populated with Name/Description/Instructions/Welcome Message/starters, screenshot | asserted |

### Axis 2 — Analyst additions

- step 1 documents a permission-gating behavior beyond the case's own scope:
  `GenerateEntityButton` returns `null` (button doesn't render at all) for a
  user lacking `PERMISSIONS.applications.update`, rather than a
  disabled/tooltip state — *added: relevant context for anyone later writing
  a permission-denied variant of this case, not itself required by
  ELITEA-1915's Pass/Fail criteria, so not asserted here.*
- step 2 documents the exact intercepted endpoint and both HTTP-level and
  UI-level confirmation of the failure (network panel status code AND the
  loading→input step transition) — *added: gives the implementer two
  independent, stable signals to wait on/assert against instead of only the
  toast/alert text.*
- step 5 documents the `resetGenerate()` ordering (old error cleared before
  the retry request is even sent, not just after it resolves) — *added:
  source-confirmed detail (`GenerateEntityModal.jsx:59`) that matters for a
  flake-free automated assertion — an implementer polling for "alert element
  gone" immediately after the retry click will see it gone as soon as
  loading starts, not only once the new request settles.*
- observed but out of this case's scope: clicking **"Back to prompt"** from
  the review form (not itself a case step) also preserves the original
  prompt text in the textarea (confirmed live, re-entered the input step
  with the same description intact) — *added: consistent with the Step 4
  behavior and useful precedent if a future case covers the Back-to-prompt
  flow, but not asserted here since ELITEA-1915 doesn't exercise it.*

## Cleanup
1. No product state is created by Steps 1-5 (no agent is ever submitted).
   Step 6 only populates the review form in local component state — the
   draft is **not** approved/"Create Agent"-clicked in this AFS, so no
   agent, toolkit association, or backend record is created. Closing the
   modal (via "Close"/Cancel, not exercised as a case step but confirmed via
   source `handleClose` in `GenerateEntityModal.jsx:42-53`) fully resets all
   local state (`step`, `description`, `draftData`, `isApproving`) and calls
   `resetGenerate()`.
2. For automated runs: no API/DB cleanup fixture is needed for this case.
   If the implementer chooses to also click through to "Create Agent" as an
   extended assertion (out of this case's scope), that WOULD require the
   existing `AgentAPI`/UI delete-agent cleanup pattern used elsewhere in
   `automation/pages/agent_detail_page.py` — not needed for ELITEA-1915 as
   scoped.
3. Playwright route interception is automatically scoped to the test's own
   browser context/page and needs no explicit teardown beyond the normal
   fixture-per-test browser context lifecycle already used across this
   suite; `page.unroute(...)` was used mid-run here only because Step 5
   needed the mock removed to let the real backend recover — an automated
   test can instead register a **second** route handler (mock 500 once,
   then real/second mock success) rather than literally unrouting to hit
   the live DEV backend, if determinism is preferred over "real recovery"
   fidelity — see Automation Hints.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Agents list → Create button (entry to `/agents/create`) | `page.get_by_test_id("sidebar-create-button")` — confirmed live, existing testid | n/a — already present |
| "Build with AI" button (`GenerateEntityButton.jsx:19-27`) | **testid needed** — no `data-testid` on the `BaseBtn` (source-confirmed: zero testid props anywhere in `GenerateEntityButton.jsx`). Request via `add-data-testid`, suggested name `generate-agent-open-button` (or a more generic `generate-entity-open-button` if the team wants one name reused across agent/skill/pipeline "Build with AI" entry points — this component is already shared, see Known Defects #2) | `page.get_by_role("button", { name: "Build with AI" })` — used only for this exploration; not for automated tests per locator policy |
| Modal container (`Modal.BaseModal` inside `GenerateEntityModal.jsx:209-217`) | **testid needed** — `BaseModal.jsx` itself supports a `dataTestId` prop (`data-testid={dataTestId}` at `BaseModal.jsx:122`) but `GenerateEntityModal` never passes one through. This is a one-line wiring gap, not a missing capability — `add-data-testid` (or a small implementer PR) just needs to add `dataTestId="generate-agent-modal"` to the `<Modal.BaseModal ...>` call in `GenerateEntityModal.jsx:209` | `page.get_by_role("dialog")` (single dialog open at a time in this flow — acceptable only for exploration) |
| Modal "Close" (X) button | **testid needed** — same gap as above: `BaseModal` supports `closeButtonDataTestId` (`BaseModal.jsx:144`) but it isn't passed | `page.get_by_role("button", { name: "Close" })` scoped to the dialog |
| Prompt textarea (`GenerateEntityModal.jsx:128-141`) | **testid needed** — plain MUI `TextField`, zero testid props. Suggested name: `generate-agent-prompt-input` | `page.get_by_role("textbox", { name: "Describe your agent's goal, key tasks, and preferred tone or behavior." })` — brittle: tied to the exact placeholder copy |
| Error `Alert` (`GenerateEntityModal.jsx:142-151`) | **testid needed** — plain MUI `Alert`, zero testid props. Suggested name: `generate-agent-error-alert` | `page.get_by_role("alert")` scoped to the dialog (only one alert renders at a time in this flow) |
| "Generate" button (doubles as the case's "retry" button — `GenerateEntityModal.jsx:195-203`) | **testid needed** — zero testid props. Suggested name: `generate-agent-submit-button` | `page.get_by_role("button", { name: "Generate" })` scoped to the dialog |
| "Cancel" button (input step) | **testid needed** — suggested name: `generate-agent-cancel-button` | `page.get_by_role("button", { name: "Cancel" })` scoped to the dialog |
| Loading state text/spinner | **testid needed** — suggested name: `generate-agent-loading-indicator` | `page.get_by_text("Generating agent draft...")` |
| Review form fields (Name/Description/Instructions/Welcome Message/starters, `GenerateAgentReviewForm.jsx`) | **testid needed** — not inspected field-by-field in this AFS (out of this case's scope; case only requires confirming a draft WAS returned, step 6), but flagged since a future "edit/approve generated draft" case will need them | n/a — out of scope for ELITEA-1915 |
| "Back to prompt" / "Create Agent" buttons (review step actions, `GenerateEntityModal.jsx:162-181`) | **testid needed** — suggested names `generate-agent-back-button` / `generate-agent-approve-button` | `page.get_by_role("button", { name: "Back to prompt" })` / `page.get_by_role("button", { name: "Create Agent" })` |

**Summary for the implementer / `add-data-testid`:** this entire flow
(`GenerateEntityModal.jsx`, `GenerateEntityButton.jsx`,
`GenerateAgentButton.jsx`) has **zero** `data-testid` attributes anywhere in
the component tree it renders directly, despite the shared `BaseModal`
already supporting `dataTestId` / `closeButtonDataTestId` /
`confirmButtonDataTestId` props that are simply never wired through. This
is a single shared component used for both the Agent and (per the
`entityLabel` prop / directory name `generate-entity-with-ai`) presumably
other entity types' "Build with AI" flows — fixing it once in
`GenerateEntityModal.jsx` (+ passing entity-specific names from
`GenerateAgentModal.jsx` where needed) benefits every case that touches any
"Build with AI" modal, not just this one.

## Network Behavior
- `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/{project_id}`
  — the sole endpoint the modal calls to generate a draft. Body:
  `{"user_description": "<prompt text>"}` per
  `GenerateAgentModal.jsx:101-104`. Mocked response (Step 2):
  `500` + `{"error":"Simulated generation failure for ELITEA-1915"}`.
  Real response (Step 6, live DEV backend, ~30s in this run): `200` with a
  JSON draft payload consumed directly by `GenerateAgentReviewForm`
  (`name`, `description`, `instructions`, `welcome_message`,
  `conversation_starters`, plus `suggested_toolkits` / `suggested_mcp` /
  `suggested_agents` / `suggested_pipelines` / `suggested_skills` arrays
  per `GenerateAgentModal.jsx:253-259` — not inspected in detail, out of
  this case's scope).
- No other network calls are specific to the failure/retry flow itself;
  the surrounding page's usual `applications`, `tags`, `models`,
  `permissions`, etc. GETs (visible in the full request log for this run)
  are unrelated page-load traffic, not part of this case's assertions.

## Known Defects Found During Exploration

1. **Case-text drift (CLARIFICATION, not a product defect) — case
   Preconditions describe Step 1's end state, and Step 5 implies a distinct
   "retry" control that doesn't exist as a separate element.** The case's
   Preconditions line ("The GenerateAgentModal is open with a prompt
   entered") is really the *outcome* of Step 1, not a setup requirement —
   this AFS folds it into Step 1 rather than treating it as a precondition
   met before the case begins. Separately, Step 5's wording ("Click the
   retry / \"Generate agent\" button") reads as if a dedicated retry
   affordance might appear after a failure; live-verified there is exactly
   **one** Generate button throughout the input step, before and after a
   failed attempt — clicking it again after a failure IS the retry
   mechanism (confirmed via source: the button has no separate "retry"
   variant/label, and `handleGenerate` is reused unconditionally). This
   fully satisfies the case's functional intent (a working retry exists and
   works), so **not filed as a GitHub issue** — this is a case-authoring
   precision gap, not a product defect. Recommend the TMS case wording be
   tightened upstream (Preconditions → fold into Step 1; Step 5 → "click
   Generate again to retry") but that's a documentation nit, not blocking.

2. **[Non-blocking, informational — not filed] `data-testid` coverage gap
   across the entire "Build with AI" flow.** See Concrete Handles above for
   the full inventory. Not filed as a GitHub issue per this project's bug
   filing policy (`.agents/profile.md` § Bug filing is for *product
   defects*; a missing testid is exactly the class of gap
   `.agents/testing.md` § Locator policy routes to `add-data-testid`
   directly, not to the tracker) — flagging here is the correct channel per
   this AFS's own instructions ("you are NOT expected to add testids
   yourself, that's the implementer's job via the `add-data-testid`
   skill").

No functional product defect was found. The live product's behavior across
all 6 steps matches the case's Pass criteria exactly once the two
case-text-drift points above are accounted for.

## Blocked Steps
None. All 6 steps were executed end-to-end live, including a full real
(unmocked) retry-recovery round-trip against the live DEV backend in Step 6
(not merely asserted against a second mock) — this AFS is
`ready-for-automation` for all 6 steps.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/agents/test_agent_build_with_ai.py` (new file — no
  existing test file covers the Generate-Agent-with-AI flow; grep of
  `automation/tests/ui/agents/` and `automation/pages/` found no
  `GenerateAgentModal`/"Build with AI" references prior to this AFS).
- New page object suggested: `automation/pages/generate_agent_modal_page.py`
  (or a `GenerateAgentModalPage` class alongside the existing
  `agent_form_page.py`/`agent_page.py` in that directory), holding
  `LocatorDescriptor` fields for every handle in the Concrete Handles table
  above **once the corresponding testids land** via `add-data-testid`. Until
  then, per this project's strict testid-only locator policy
  (`.agents/testing.md` § Locator policy), this case should **not** be
  automated with the role/text fallbacks used during this exploration —
  route the testid additions through `add-data-testid` first (dual-target
  flow: commit on `automation/testids`, draft PR to `main`), then implement.
- For Step 2's failure simulation, use Playwright's `page.route()` /
  `page.unroute()` (or a context-level route) scoped to
  `**/elitea_core/generate_application_draft/**`, matching this
  exploration's mechanism exactly — this is the standard technique per the
  skill's own guidance and requires no backend cooperation.
- For Step 5/6's retry, the implementer has two options, both valid:
  (a) **as explored here**: `unroute()` after the mocked failure and let the
  retry hit the real DEV backend — higher fidelity, but the real generation
  call took ~30s in this run and depends on live LLM service availability,
  making CI timing/flakiness a real risk; or
  (b) **more deterministic**: register a *second* route handler for the
  retry that fulfills with a synthetic 200 + minimal valid draft JSON shape
  (`name`, `description`, `instructions`, `welcome_message`,
  `conversation_starters: []` at minimum, based on the real response shape
  partially observed in this run), fully mocking both legs of the flow.
  Recommend **(b)** for CI stability, with the real-backend path (a)
  reserved for a manual/occasional smoke check if the team wants one — this
  AFS itself used (a) to prove the real contract exists at all, which
  option (b)'s synthetic payload should mirror.
- Wait strategy: wait on the `generate_application_draft` network response
  (`page.wait_for_response(...)`) for both the failed and retried requests,
  and on the loading-state text disappearing, rather than fixed sleeps —
  this exploration used a 5s-interval poll only because it was
  interactively investigating the real backend's actual latency; an
  automated test should await the network response directly.
