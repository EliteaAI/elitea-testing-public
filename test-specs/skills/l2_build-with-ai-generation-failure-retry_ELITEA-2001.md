# Test Case: Build with AI — generation failure shows error and allows retry (Skill)

## Metadata
- **TMS ID**: ELITEA-2001
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: `.agents/testing.md` has no `TMS case-gate` section defining
  excluded statuses for this project (confirmed again this run — same gap
  ELITEA-1915's AFS flagged). The case file's own frontmatter carries
  `status: draft` / `execution_type: manual` — per the skill's default
  ("if absent, default to fetching all and flag the gap"), this run proceeded
  and fetched/executed the case.
- **Relationship to ELITEA-1915 (Agent "Build with AI" failure/retry)**:
  investigated live before executing this case, per dispatch instructions.
  The two cases share the `GenerateEntityModal.jsx` / `GenerateEntityButton.jsx`
  presentation component (via the `entityLabel="skill"` prop and the
  `generate-entity-with-ai` directory), but the **skill** flow has its own
  distinct entry point (`GenerateSkillButton.jsx`), wrapper
  (`GenerateSkillModal.jsx`), API endpoint
  (`/elitea_core/generate_skill_draft/prompt_lib/{projectId}`, source:
  `generateSkillDraftApi.js:7`), and review form
  (`GenerateSkillReviewForm.jsx`) — a fully separate business object (Skill,
  not Agent) is created on approval. This is genuine Rule-6 **non**-overlap
  at the entity level (different creation mutation, different review-form
  fields, different downstream navigation target `/skills/{id}`) even though
  the shared modal shell behavior (loading → error → retry → review) is
  identical. Classified **`ready-for-automation`** as a fresh spec, not
  `extend-existing` — the existing `test_agent_build_with_ai.py` file
  automates `GenerateAgentModal`-specific selectors/API mocks that do not
  apply to the Skill entry point (different route, different button, and —
  confirmed live, see Concrete Handles — the skill flow currently carries
  **zero** wired testids, whereas the agent flow's testids landed after
  ELITEA-1915 shipped). A shared **page-object base class** for
  `GenerateEntityModal` common controls (Generate/Cancel/error-alert/loading)
  would be a reasonable implementer refactor, but that's an implementation
  choice, not a reason to defer this case to `extend-existing`.

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips login
  via `VITE_DEV_TOKEN`) with editor/admin role sufficient to create skills
  (confirmed live: the "Build with AI" entry point is gated behind
  `PERMISSIONS.applications.update` via `GenerateEntityButton.jsx` — same
  gate as the agent flow; `GenerateSkillButton.jsx:12` passes the same
  permission constant. Button renders `null` if the check fails, not a
  disabled state — matches the ELITEA-1915 finding exactly, same shared
  component).
- A project is selected/accessible (`Private`, id `399` in this run).
- **Corrected precondition (case-text drift, not a defect) — same pattern as
  ELITEA-1915:** the case's stated precondition "The Build with AI modal is
  open with a natural-language description entered" actually describes the
  end state of Step 1/2, not a setup precondition. Live entry point is the
  **Skill create form** (`${BASE_URL}/skills/create`), General accordion
  section, "Build with AI" button (`GenerateSkillButton.jsx`, rendered via
  `GenerateEntityButton` as a `summaryAction` inside `CreateSkillForm.jsx:154`,
  in the "General" accordion header — confirmed live, same pattern as
  `CreateAgentForm.jsx:106` for the agent case). This AFS's Step 1 covers
  navigating there and opening the modal.
- "A method to simulate or trigger a generation failure is available" —
  confirmed achievable live via Playwright route interception on the exact
  skill-draft endpoint (see Step 2).

## Test Data

### reuse-existing (no fixture creation/teardown needed)
- Natural-language prompt (any valid description text, per case): `"Create a
  skill that summarizes long customer support transcripts into a 3-bullet
  action list for the assigned agent."` — live-verified: any non-empty,
  non-whitespace string enables the Generate button
  (`disabled={!description.trim()}` in `GenerateEntityModal.jsx:215`, shared
  code path with the agent case); content is not otherwise asserted by this
  case.
- Simulated failure response body: `{"error":"Simulated generation failure
  for ELITEA-2001"}`, HTTP 500. Chosen for the same reason as ELITEA-1915:
  the shared error-display code (`GenerateEntityModal.jsx:161-163`) reads
  `generateError?.data?.error || generateError?.data?.detail || 'Failed to
  generate. Please try again.'` — a custom, case-ID-tagged message live-
  proves the actual backend error surfaces verbatim, not just the generic
  fallback.

No test data is created or persisted in the product (no skill is ever
submitted in this AFS's steps — the "Create Skill" button on the review
form is never clicked). See Cleanup.

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`. In the "General" accordion
   section, click the **"Build with AI"** button (no testid, confirmed live
   — see Concrete Handles) to open the `GenerateSkillModal`. Fill the prompt
   textarea (no testid — accessible name `"Describe what your skill should
   do, its inputs, and expected output format."`) with the test-data prompt.
   - **Verify**: the textarea contains exactly the entered text; the
     **"Generate"** button (no testid, disabled while the field is
     empty/whitespace-only) becomes enabled once non-empty text is present.
     Confirmed live via snapshot before/after fill — button snapshot showed
     `[disabled]` pre-fill, `[cursor=pointer]` (enabled) post-fill.

2. Before clicking Generate, install a Playwright route interception on
   `POST **/elitea_core/generate_skill_draft/**` (the exact endpoint the
   mutation calls — confirmed via source, `generateSkillDraftApi.js:7`:
   `/elitea_core/generate_skill_draft/prompt_lib/{projectId}`) that fulfills
   with **HTTP 500** and body `{"error":"Simulated generation failure for
   ELITEA-2001"}`. Click **"Generate"**.
   - **Verify**: the modal transitions to a loading state
     (`"Generating skill draft..."` + spinner, confirmed live in a snapshot
     immediately after click), then the mocked request resolves 500 and the
     UI reverts to the input step. Network panel confirms `POST
     /api/v2/elitea_core/generate_skill_draft/prompt_lib/399 => [500]`
     (live-observed, request #1485 in this run's network log). This is the
     case's "trigger or simulate a generation failure" step — route
     interception, not a real backend outage.

3. With the mocked 500 still resolved, observe the modal without further
   interaction.
   - **Verify**: a MUI `Alert severity="error"` (`role="alert"`, confirmed
     via accessibility snapshot) renders inside the modal body, directly
     below the prompt textarea, containing the exact injected message:
     `"Simulated generation failure for ELITEA-2001"`. This confirms the
     live component surfaces the backend's `error` field verbatim rather
     than only the generic fallback — same code path as the agent case
     (`GenerateEntityModal.jsx:161`, entity-agnostic). Screenshot:
     `test-results/screenshots/ELITEA-2001-step-3-error-state.png`. Console:
     exactly one `[ERROR] Failed to load resource: … 500 …` entry for the
     mocked endpoint (`generate_skill_draft/prompt_lib/399`) — no unrelated
     app-level console errors accompanying the failure (side-channel check
     passed; total console log at this point: 8 messages, 1 error, 0
     warnings).

4. Inspect the prompt textarea state in the same (still-open) modal.
   - **Verify**: the textarea still contains the exact prompt text entered
     in Step 1, unmodified — confirmed live via accessibility snapshot
     immediately after the failure (same view as Step 3's screenshot shows
     both the alert AND the intact prompt text together). Source-confirmed
     why: `GenerateEntityModal.jsx`'s `handleGenerate` catch block
     (`GenerateEntityModal.jsx:79-82`) only resets `step` back to
     `STEPS.INPUT` — it does not clear the `description` state, which is
     independent local component state untouched by the failed mutation
     (identical mechanism to the agent case, same shared component).

5. Remove the route interception (letting the endpoint hit the real DEV
   backend) and click **"Generate"** again (the same button — the modal has
   no separate "Retry" control, matching ELITEA-1915's finding; the case's
   "retry/Generate button" step 6 language maps directly onto re-clicking
   the one **Generate** button already used in Step 2 — see Known
   Defects/Clarification #1).
   - **Verify**: `resetGenerate()` fires before the retry request
     (`GenerateEntityModal.jsx:68`), clearing the prior `generateError`
     state immediately — the modal shows the loading state again
     (`"Generating skill draft..."`), not a stale copy of the Step 3 error
     alongside the new attempt. Confirmed live: the error alert is gone as
     soon as the retry request is in flight (snapshot immediately after
     click showed only the `progressbar` + `"Generating skill draft..."`
     text, no alert node).

6. Wait for the retried (real, unmocked) request to resolve.
   - **Verify**: the live DEV backend recovered and returned a real draft
     (confirmed live in this run — resolved within ~90s, polled via
     `wait_for` on the "Back to prompt" text appearing). The modal
     transitions from the loading state directly to the **review form**
     (`GenerateSkillReviewForm`), populated with a generated Name
     (`support-transcript-summarizer`), Description, and Instructions (all
     non-empty, contextually relevant to the prompt — e.g. Instructions
     produced a structured "3 action items" spec matching the prompt's
     intent). Actions row shows **"Back to prompt"** and **"Create Skill"**.
     Screenshot:
     `test-results/screenshots/ELITEA-2001-step-6-review-form.png`. Network
     confirms both legs: request #1485
     `POST .../generate_skill_draft/prompt_lib/399 => [500]` (Step 2's mock)
     followed by request #1486 `POST .../generate_skill_draft/prompt_lib/399
     => [200]` (Step 6's real retry). Console: zero new errors during the
     successful retry/transition (only the earlier, expected Step 2 mocked-
     500 entry remains in the log — same count, 1 error total, confirmed
     before and after the retry). This is the case's "if service recovers,
     a draft is returned / review form displayed" outcome — live-verified
     end-to-end against the real backend, not asserted only against a
     second mock.
   - Note (unlike the Agent review form, which has Name/Description/
     Instructions/Welcome Message/4 conversation starters), the Skill
     review form (`GenerateSkillReviewForm.jsx`) only surfaces
     **Name/Description/Instructions** — no Welcome Message, no
     conversation starters. This is expected per the Skill entity's data
     model (skills have no chat welcome/starters concept in this product),
     not a defect or omission relative to the case.

Modal was closed via the **"Close"** (X) button after Step 6 (not itself a
case step) rather than clicking "Create Skill" — see Cleanup.

## Expected Results
Matches the case's stated Pass criteria exactly, live-verified end-to-end:
error message displayed on failure (Step 3), prompt preserved after failure
(Step 4), retry available and functional (Step 5), and — when the service
recovers — the retry successfully produces a new draft and transitions to
the review form (Step 6). No step produced an unexpected result; no
clarification changes the case's pass/fail semantics (only the entry-point
precondition wording, per Known Defects #1, is a text-level correction,
mirroring the same drift already documented for the sibling Agent case).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: "The Build with AI modal is open with a natural-language description entered" | — | step 1 | step 1 folds this into itself (navigate + open + fill), since live this is an outcome of Step 1, not a standalone precondition | clarification *(case-text drift — see Known Defects #1; not a product defect)* |
| Precondition: "A method to simulate or trigger a generation failure is available" | achievable | step 2 | step 2: Playwright route interception on the exact generate-skill-draft endpoint | asserted |
| 1 Open modal, enter prompt | input field accepts and displays the prompt | step 1 | step 1: snapshot shows textarea value == entered text, Generate button enabled | asserted |
| 2 Enter natural-language prompt | field accepts and displays prompt | step 1 | same as above (case splits this into two steps 1/2; live behavior is a single fill-and-verify action) | asserted |
| 3 Simulate/trigger generation failure | generation request fails | step 2 | step 2: mocked 500, network panel + loading→input transition confirmed | asserted |
| 4 Verify clear error message displayed | error message visible in modal | step 3 | step 3: `role="alert"` with exact injected message text, screenshot | asserted |
| 5 Verify prompt still present after failure | original prompt text preserved | step 4 | step 4: textarea value unchanged, source-confirmed why (`description` state untouched by failed mutation) | asserted |
| 6 Click retry/Generate button again | generation is retried | step 5 | step 5: re-click the same Generate button (no separate retry control exists), error cleared, loading state re-entered | asserted *(see Known Defects #1 — case implies a distinct "retry" affordance; live product reuses the single Generate button, fully satisfying the case's functional intent)* |
| 7 Verify generation retried and (if service recovers) draft returned | skill draft generated, review form displayed | step 6 | step 6: real (unmocked) backend call succeeds, review form populated with Name/Description/Instructions, screenshot | asserted |

### Axis 2 — Analyst additions

- step 1 documents the same permission-gating behavior found in ELITEA-1915:
  `GenerateEntityButton` returns `null` for a user lacking
  `PERMISSIONS.applications.update` — *added: relevant context for a future
  permission-denied variant of this case, not itself required by
  ELITEA-2001's Pass/Fail criteria, so not asserted here.*
- step 2 documents the exact intercepted endpoint (distinct from the agent
  case's endpoint) and both HTTP-level and UI-level confirmation of the
  failure — *added: gives the implementer two independent, stable signals
  to wait on/assert against instead of only the alert text.*
- step 5 documents the `resetGenerate()` ordering (old error cleared before
  the retry request is even sent) — *added: source-confirmed detail
  (`GenerateEntityModal.jsx:68`) matters for a flake-free automated
  assertion, identical mechanism to the agent case since both flows share
  this component.*
- step 6 documents that the Skill review form's field set
  (Name/Description/Instructions only) differs from the Agent review form
  (which also has Welcome Message + conversation starters) — *added:
  prevents an implementer from copy-pasting the agent review-form
  assertions verbatim onto the skill flow and getting spurious failures for
  fields that don't exist on this entity.*
- observed but out of this case's scope: clicking **"Back to prompt"** from
  the review form was not exercised in this run (unlike ELITEA-1915, which
  did exercise it) — *flagged as an assumption carried over from the
  sibling case, not independently re-verified here; a future case or the
  implementer should confirm the Skill flow's Back-to-prompt behavior
  matches the Agent flow's (same shared `handleBack` in
  `GenerateEntityModal.jsx:85-89`, so behaviorally expected to match, but
  not this AFS's own live observation).*

## Cleanup
1. No product state is created by Steps 1-6. Step 6 only populates the
   review form in local component state — the draft is **not** approved/
   "Create Skill"-clicked in this AFS, so no skill, version, or backend
   record is created. Closing the modal (via "Close" — exercised live after
   Step 6 to leave a clean state) fully resets all local state (`step`,
   `description`, `draftData`, `isApproving`) and calls `resetGenerate()`,
   per source `handleClose` in `GenerateEntityModal.jsx:51-62` (identical
   mechanism to the agent case).
2. For automated runs: no API/DB cleanup fixture is needed for this case.
   If the implementer chooses to also click through to "Create Skill" as an
   extended assertion (out of this case's scope), that WOULD require a
   skill-delete cleanup pattern (existing `SkillAPI`/UI delete-skill helper,
   per this project's skill test suite conventions) — not needed for
   ELITEA-2001 as scoped.
3. Playwright route interception is automatically scoped to the test's own
   browser context/page and needs no explicit teardown beyond the normal
   fixture-per-test browser context lifecycle already used across this
   suite; `page.unroute(...)` was used mid-run here only because Step 5
   needed the mock removed to let the real backend recover — an automated
   test can instead register a **second** route handler (mock 500 once,
   then real/second mock success) rather than literally unrouting to hit
   the live DEV backend, if determinism is preferred over "real recovery"
   fidelity — see Automation Hints (same recommendation as ELITEA-1915).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Skills list/create entry → `/skills/create` | direct navigation used in this exploration; page has an existing "Skill" create button in the sidebar create-menu (`button` labeled "Skill", no testid inspected this run — out of this case's scope) | n/a |
| "Build with AI" button (`GenerateEntityButton.jsx:19-27`, rendered via `GenerateSkillButton.jsx`) | **testid needed** — confirmed live via DOM inspection: **zero** `data-testid` attributes anywhere in the open dialog except the MUI icon's own default `ErrorOutlineIcon` testid (not a real handle). Source-confirmed why: `GenerateSkillButton.jsx` never passes a `buttonTestId` prop to `GenerateEntityButton`, unlike `GenerateAgentButton.jsx:14` which passes `buttonTestId="generate-agent-open-button"`. **This is the key finding of this AFS**: the shared `GenerateEntityModal`/`GenerateEntityButton` components gained full testid wiring support since ELITEA-1915 was written (all `*TestId` props now exist and are consumed — confirmed via source read of `GenerateEntityModal.jsx:30-38` and `GenerateEntityButton.jsx:11`), but the **Skill** entity's wrapper components were never updated to pass them, while the **Agent** wrapper was. Request via `add-data-testid`, suggested name `generate-skill-open-button` (mirroring the agent naming convention exactly) | `page.get_by_role("button", { name: "Build with AI" })` — used only for this exploration; not for automated tests per locator policy |
| Modal container (`Modal.BaseModal` inside `GenerateEntityModal.jsx:227-237`) | **testid needed** — `modalTestId` prop exists and is wired to `data-testid={modalTestId}` (`GenerateEntityModal.jsx:235`) but `GenerateSkillModal.jsx` never passes it. Suggested name: `generate-skill-modal` (mirrors `generate-agent-modal`) | `page.get_by_role("dialog")` (single dialog open at a time in this flow) |
| Modal "Close" (X) button | **testid needed** — `closeButtonTestId` prop exists (`GenerateEntityModal.jsx:236`, wired to `BaseModal`'s `closeButtonDataTestId`) but unwired for Skill. Suggested name: `generate-skill-close-button` | `page.get_by_role("button", { name: "Close" })` scoped to the dialog |
| Prompt textarea (`GenerateEntityModal.jsx:140-154`) | **testid needed** — `promptInputTestId` prop exists (`inputProps={{'data-testid': promptInputTestId}}`) but unwired for Skill. Suggested name: `generate-skill-prompt-input` | `page.get_by_role("textbox", { name: "Describe what your skill should do, its inputs, and expected output format." })` — brittle: tied to exact placeholder copy |
| Error `Alert` (`GenerateEntityModal.jsx:155-165`) | **testid needed** — `errorAlertTestId` prop exists but unwired for Skill. Suggested name: `generate-skill-error-alert` | `page.get_by_role("alert")` scoped to the dialog (only one alert renders at a time) |
| "Generate" button (doubles as the case's "retry" button, `GenerateEntityModal.jsx:212-221`) | **testid needed** — `generateButtonTestId` prop exists but unwired for Skill. Suggested name: `generate-skill-submit-button` | `page.get_by_role("button", { name: "Generate" })` scoped to the dialog |
| "Cancel" button (input step) | **testid needed** — `cancelButtonTestId` prop exists but unwired for Skill. Suggested name: `generate-skill-cancel-button` | `page.get_by_role("button", { name: "Cancel" })` scoped to the dialog |
| Loading state text/spinner | **testid needed** — `loadingIndicatorTestId` prop exists but unwired for Skill. Suggested name: `generate-skill-loading-indicator` | `page.get_by_text("Generating skill draft...")` |
| Review form fields (Name/Description/Instructions, `GenerateSkillReviewForm.jsx`) | **testid needed** — not inspected field-by-field in this AFS (out of this case's scope; case only requires confirming a draft WAS returned, step 6), but flagged since a future "edit/approve generated draft" case will need them | n/a — out of scope for ELITEA-2001 |
| "Back to prompt" / "Create Skill" buttons (review step actions, `GenerateEntityModal.jsx:173-198`) | **testid needed** — `backButtonTestId`/`approveButtonTestId` props exist but unwired for Skill. Suggested names `generate-skill-back-button` / `generate-skill-approve-button` | `page.get_by_role("button", { name: "Back to prompt" })` / `page.get_by_role("button", { name: "Create Skill" })` |

**Summary for the implementer / `add-data-testid`:** unlike the Agent flow
(where `GenerateAgentButton.jsx`/`GenerateAgentModal.jsx` were fixed to pass
all nine `*TestId` props after ELITEA-1915 — confirmed live, exact names
`generate-agent-open-button`, `generate-agent-modal`,
`generate-agent-close-button`, `generate-agent-prompt-input`,
`generate-agent-error-alert`, `generate-agent-loading-indicator`,
`generate-agent-submit-button`, `generate-agent-cancel-button`,
`generate-agent-back-button`, `generate-agent-approve-button`), the **Skill**
flow's `GenerateSkillButton.jsx`/`GenerateSkillModal.jsx` still pass **none**
of these props through to the shared components, even though
`GenerateEntityModal.jsx`/`GenerateEntityButton.jsx` fully support them. This
is now a one-line-per-prop wiring gap only in the Skill wrapper components
(the underlying capability already exists and is proven working for Agent) —
`add-data-testid` should mirror the exact agent naming convention with
`generate-skill-*` in place of `generate-agent-*`, adding the props to
`GenerateSkillButton.jsx` (1 prop: `buttonTestId`) and `GenerateSkillModal.jsx`
(9 props passed through to its `<GenerateEntityModal ...>` call).

## Network Behavior
- `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/{project_id}` —
  the sole endpoint the modal calls to generate a skill draft. Body:
  `{"user_description": "<prompt text>"}` inferred from
  `GenerateSkillModal.jsx:25` (`generateDraft({ projectId, user_description:
  description })`, same body shape convention as
  `GenerateAgentModal.jsx:101-104`). Mocked response (Step 2): `500` +
  `{"error":"Simulated generation failure for ELITEA-2001"}`. Real response
  (Step 6, live DEV backend, ~90s in this run): `200` with a JSON draft
  payload consumed directly by `GenerateSkillReviewForm` (`name`,
  `description`, `instructions` — confirmed live via the populated review
  form; no other fields observed, unlike the Agent draft's additional
  `welcome_message`/`conversation_starters`/`suggested_*` arrays).
- No other network calls are specific to the failure/retry flow itself; the
  surrounding page's usual `support_assistant`, `project_info`,
  `configurations`, `permissions`, `tags`, `default_icons`,
  `upload_skill_icon`, `notifications`, etc. GETs (visible in the full
  request log for this run) are unrelated page-load traffic, not part of
  this case's assertions.

## Known Defects Found During Exploration

1. **Case-text drift (CLARIFICATION, not a product defect) — case
   Preconditions describe Step 1/2's end state, and Step 6 implies a
   distinct "retry" control that doesn't exist as a separate element.**
   Same pattern as ELITEA-1915: the case's Preconditions line ("The Build
   with AI modal is open with a natural-language description entered") is
   really the outcome of Steps 1-2, not a setup requirement. Separately,
   Step 6's wording ("Click the retry/Generate button again") reads as if a
   dedicated retry affordance might appear after a failure; live-verified
   there is exactly **one** Generate button throughout the input step,
   before and after a failed attempt. This fully satisfies the case's
   functional intent, so **not filed as a GitHub issue** — a case-authoring
   precision gap, not a product defect (identical disposition to
   ELITEA-1915's finding #1).

2. **[Non-blocking, informational — not filed] `data-testid` coverage gap
   specific to the Skill entry point of the shared "Build with AI" flow.**
   See Concrete Handles above for the full inventory and the exact
   comparison against the now-fixed Agent flow. Not filed as a GitHub issue
   per this project's bug filing policy (`.agents/profile.md` § Bug filing
   is for product defects; a missing testid routes to `add-data-testid`
   directly per `.agents/testing.md` § Locator policy) — flagging here is
   the correct channel. Distinct from ELITEA-1915's equivalent finding
   in that the underlying capability (the nine `*TestId` props on
   `GenerateEntityModal`/`GenerateEntityButton`) now exists and works for
   Agent; only the Skill wrapper's prop-passing was never done. This is a
   smaller, more mechanical fix than ELITEA-1915 originally faced (no new
   plumbing needed in the shared component, just wiring in
   `GenerateSkillButton.jsx`/`GenerateSkillModal.jsx`).

No functional product defect was found. The live product's behavior across
all 6 case steps matches the case's Pass criteria exactly once the
case-text-drift point above is accounted for.

## Blocked Steps
None. All case steps were executed end-to-end live, including a full real
(unmocked) retry-recovery round-trip against the live DEV backend in Step 6
(not merely asserted against a second mock) — this AFS is
`ready-for-automation` for all steps.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/skills/test_skill_build_with_ai.py` (new file — grep
  of `automation/tests/ui/skills/` and `automation/pages/` found no
  `GenerateSkillModal`/"Build with AI" references prior to this AFS,
  mirroring the equivalent gap ELITEA-1915 found for agents).
- New page object suggested: `automation/pages/generate_skill_modal_page.py`
  (or a `GenerateSkillModalPage` class alongside the existing skill page
  objects), holding `LocatorDescriptor` fields for every handle in the
  Concrete Handles table above **once the corresponding testids land** via
  `add-data-testid`. Until then, per this project's strict testid-only
  locator policy (`.agents/testing.md` § Locator policy), this case should
  **not** be automated with the role/text fallbacks used during this
  exploration — route the testid additions through `add-data-testid` first
  (dual-target flow: commit on `automation/testids`, draft PR to `main`),
  then implement.
- **Reuse opportunity for the implementer** (not a spec requirement, an
  efficiency note): since `GenerateEntityModal`/`GenerateEntityButton` are
  the same shared component for both Agent and Skill, a common base
  page-object (e.g. `GenerateEntityModalPageBase` with `prompt_input`,
  `generate_button`, `error_alert`, `loading_indicator`, `cancel_button`,
  `close_button`, `back_button`, `approve_button` fields keyed off the
  `generate-{entity}-*` naming convention) would let
  `GenerateSkillModalPage`/`GenerateAgentModalPage` each subclass it and
  only override entity-specific bits (review-form fields, approve-button
  label). This mirrors the `add-data-testid` naming convention already
  established by the Agent flow (`generate-agent-*` → `generate-skill-*`),
  so the two page objects would be near-identical modulo the prefix and the
  review-form field set — worth a shared base class to avoid duplicating
  the failure/retry interaction logic across two page-object files.
- For Step 2's failure simulation, use Playwright's `page.route()` /
  `page.unroute()` (or a context-level route) scoped to
  `**/elitea_core/generate_skill_draft/**` — matching this exploration's
  mechanism exactly, same technique as ELITEA-1915, different endpoint.
- For Step 5/6's retry, the implementer has two options, both valid (same
  trade-off ELITEA-1915 documented):
  (a) **as explored here**: `unroute()` after the mocked failure and let the
  retry hit the real DEV backend — higher fidelity, but the real generation
  call took ~90s in this run (longer than the agent case's ~30s; both are
  subject to live LLM service latency) and depends on live service
  availability, making CI timing/flakiness a real risk; or
  (b) **more deterministic**: register a second route handler for the retry
  that fulfills with a synthetic 200 + minimal valid draft JSON shape
  (`name`, `description`, `instructions` at minimum, per the real response
  shape partially observed in this run — no `welcome_message`/
  `conversation_starters` needed, unlike the Agent draft shape). Recommend
  **(b)** for CI stability, with the real-backend path (a) reserved for a
  manual/occasional smoke check.
- Wait strategy: wait on the `generate_skill_draft` network response
  (`page.wait_for_response(...)`) for both the failed and retried requests,
  and on the loading-state text disappearing, rather than fixed sleeps —
  this exploration used `wait_for(text="Back to prompt")` interactively; an
  automated test should await the network response directly for
  determinism.
