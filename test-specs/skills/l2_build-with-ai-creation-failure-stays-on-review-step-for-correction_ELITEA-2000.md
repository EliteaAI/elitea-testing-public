# Test Case: Build with AI — Skill creation failure stays on review step for correction

## Metadata
- **TMS ID**: ELITEA-2000
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (default `auth_state` session)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: same gap every prior Skills-surface AFS has recorded —
  `.agents/testing.md` has no `TMS case-gate` section for this project. Case
  frontmatter carries `status: draft` / `execution_type: manual`; per the
  skill's default this run proceeded and fetched/executed the case from the
  intake snapshot `.agents/automation/skills-remaining-w5/cases/ELITEA-2000.md`.
- **Sibling-entity precedent (source-confirmed BEFORE execution, not
  inferred):** ELITEA-1916 is the byte-for-byte identical case for the
  **Agent** entity
  (`test-specs/agents/l2_build-with-ai-creation-failure-stays-on-review-step-for-correction_ELITEA-1916.md`),
  already `ready-for-automation` and already implemented
  (`generate_agent_modal_page.py` ships `mock_create_failure()`,
  `toast_alert`/`toast_message`/`TOAST_ALERT_SEVERITY`,
  `expect_create_response()`, `click_approve_and_wait_for_creation()` —
  confirmed by reading the file directly). Read the Skill entity's own
  source before assuming the same mechanism holds:
  `GenerateSkillModal.jsx`'s `handleApprove` calls `createSkill({...}).unwrap()`
  and, on success, either calls `onSkillCreated` or navigates to the new
  Skill's detail page — it never itself catches an error. The actual
  try/catch lives one level up, in the **shared**
  `GenerateEntityModal.jsx` (`entities/generate-entity-with-ai/ui/`) that
  both `GenerateSkillModal.jsx` and `GenerateAgentModal.jsx` render into via
  `onApprove={handleApprove}` — confirmed identical for both entities by
  reading `GenerateEntityModal.jsx` directly: `handleApprove` (lines ~91-102)
  wraps `await onApprove(draftData)` in a `try`, and its `catch` block calls
  `toastError(buildErrorMessage(err))` only — no `setStep`, no
  `resetDraftData`, no `handleClose()` (`handleClose()` only runs inside the
  `try`, after success). **This is the exact same catch block ELITEA-1916
  already proved live for the Agent entity** — same component, same code
  path, entity-agnostic. Conclusion: this case is a genuine coverage gap for
  the **Skill** entity specifically (no existing spec clicks
  `generate-skill-approve-button` and asserts a create-time failure — grepped
  `automation/tests/ui/skills/test_skill_build_with_ai.py` in full; every
  existing test in that file either never reaches the review step or, where
  it does reach Approve, only asserts the SUCCESS path), classified
  `ready-for-automation`, not `extend-existing`/`already-covered` (no merged
  spec proves this Skill-specific observable).
- **Create endpoint confirmed at source** (not inferred from the Agent
  case): `GenerateSkillModal.jsx` → `useSkillCreateMutation()` →
  `skillsApi.js`'s `skillCreate` mutation → `POST
  ${apiSlicePath}/skills/${mode}/${projectId}` where `apiSlicePath =
  '/elitea_core'` and `mode = 'prompt_lib'` (both literal constants, no
  entity/viewMode branching) → **`POST
  /api/v2/elitea_core/skills/prompt_lib/{projectId}`**. Same URL the
  `skillList`/`totalSkills` GET queries use — any test mock MUST scope to
  `method === 'POST'` only (mirrors the Agent case's
  `mock_create_failure()` note about the Agents-list GET sharing the same
  URL).

## Preconditions
- User is logged in to Elitea (on localhost, `auth_state` fixture skips
  login via `VITE_DEV_TOKEN`) with editor/admin role sufficient to create
  skills (the "Build with AI" button visibility gate is covered separately
  by ELITEA-1986/1987 — not re-verified here, this run's session already
  has it visible).
- A project is selected/accessible (`Private`, id `399` in this run — the
  case does not require any particular project, project identity is not
  asserted).
- **Corrected precondition (case-text drift, not a defect — same class of
  correction ELITEA-1915/1916's AFSs already made for the Agent entity's
  identical precondition wording):** "A skill draft has been generated and
  the review/edit form is displayed" describes the *end state of Step 1*,
  not a standalone precondition. This AFS's Step 1 covers reaching that
  state (navigate → open modal → fill prompt → generate → review form).
- "A method to simulate or trigger a creation API failure is available" —
  confirmed achievable live via Playwright route interception on the exact
  create-skill POST (see Step 2), same technique ELITEA-1916 uses for the
  Agent's create-application endpoint.

## Test Data

### reuse-existing (no fixture creation/teardown needed for the mocked path)
- Natural-language prompt: any valid, non-empty description — content is
  not asserted by this case, only that a draft is reached. This run used:
  `"Create a simple test skill for ELITEA-2000 creation-failure recovery."`
  (first attempt) and `"Create a simple test skill for ELITEA-2000 attempt
  2."` (second, cleaner attempt — see Automation Hints for why two attempts
  were needed).
- **Mocked draft payload** (fulfills `generate_skill_draft`, live-run
  values, mirrors the existing skills-file draft-mocking shape already used
  by `TestSkillBuildWithAIGenerationFailureRetry`/
  `TestSkillBuildWithAIReviewFormEditableFields` in
  `test_skill_build_with_ai.py`):
  ```json
  {
    "name": "elitea-2000-draft-skill-2",
    "description": "A draft used to test create-failure recovery (attempt 2).",
    "instructions": "You are a test skill for ELITEA-2000 attempt 2."
  }
  ```
  Unlike the Agent draft, the Skill draft has no `welcome_message`/
  `conversation_starters`/`suggested_*` fields at all (confirmed by
  `GenerateSkillModal.jsx`'s `renderReview` → `GenerateSkillReviewForm`,
  Name/Description/Instructions only — matches every other Skill
  Build-with-AI AFS's Axis 2 note).
- **Simulated creation-failure response body**: `{"error":"Simulated
  creation failure for ELITEA-2000"}`, HTTP 500 — same message-carrying-
  verbatim technique ELITEA-1915/1916 use, chosen because it live-proves
  the backend's `error` field reaches the user (via `buildErrorMessage(err)`
  → `err?.data?.error`, `common/utils.jsx:161`, entity-agnostic), not just a
  generic fallback.

No test data is created or persisted by Steps 1-5 (mocked failure path).
Step 6's retry, if it completes to a real skill, DOES create a real backend
record — see Cleanup.

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`. In the "General" accordion
   section header, click **"Build with AI"** (`generate-skill-open-button`,
   confirmed live) to open the `GenerateSkillModal`. Fill the prompt
   textarea (`generate-skill-prompt-input`) with the test-data prompt, then
   click **"Generate Draft"** (`generate-skill-submit-button`).
   - **Verify**: the modal transitions through the loading state
     (`generate-skill-loading-indicator`) to the **review form**, populated
     with the draft's Name/Description/Instructions
     (`generate-skill-review-name-input` etc., confirmed live via
     snapshot — read back verbatim: Name
     `"elitea-2000-draft-skill-2"`, Description `"A draft used to test
     create-failure recovery (attempt 2)."`, Instructions `"You are a test
     skill for ELITEA-2000 attempt 2."`). This maps the case's "a skill
     draft has been generated and the review/edit form is displayed"
     precondition onto an executed step, same correction ELITEA-1915/1916's
     AFSs already made.

2. Before clicking "Create Skill", install a Playwright route interception
   on `POST **/elitea_core/skills/prompt_lib/**` (the exact endpoint the
   create mutation calls — confirmed via source,
   `skillsApi.js`'s `skillCreate` mutation, which resolves to `POST
   /elitea_core/skills/prompt_lib/{projectId}`; scope to `method ===
   'POST'` only — the same URL also serves the `skillList`/`totalSkills`
   GET queries) that fulfills the **first** matching request with **HTTP
   500** and body `{"error":"Simulated creation failure for ELITEA-2000"}`,
   then click **"Create Skill"** (`generate-skill-approve-button`).
   - **Verify**: the mocked request resolves with the injected 500. Live
     this run: exactly ONE `POST .../elitea_core/skills/prompt_lib/399`
     fired per click (confirmed via a request-logging fetch wrapper), and
     it carried the mocked failure body. This is the case's "creation
     request is submitted" (step 1) + "creation API call fails" (step 2).

3. With the mocked 500 resolved, observe the page (not just the modal —
   important, see Known Defects #1 below) without further interaction.
   - **Verify**: an app-wide **toast** notification (MUI `Snackbar` +
     `Alert`, `Toast.jsx`, existing testids `toast-alert`/`toast-message`/
     `toast-dismiss-button` — the SAME shared component `AgentDetailPage`/
     `ChatPage`/`PipelineDetailPage`/etc. already use elsewhere in this
     suite, and the SAME one ELITEA-1916 already wired onto
     `GenerateAgentModalPage`) renders, `data-severity="error"`, containing
     the exact injected message `"Simulated creation failure for
     ELITEA-2000"`. Confirmed live via direct DOM query immediately after
     the mocked 500 resolved:
     `document.querySelector('[data-testid="toast-alert"]')` →
     `data-testid="toast-alert"`, `data-severity="error"`, and
     `[data-testid="toast-message"]` → exact text `"Simulated creation
     failure for ELITEA-2000"`. Console: zero errors across the whole
     round trip (checked via `browser_console_messages` at `error` level
     immediately after the failure — 0 errors). **This diverges from the
     case's stated Step 3 expectation "Verify form-level error messages are
     displayed using the standard Skill creation error handling" — see
     Known Defects #1, a clarification not a defect (identical divergence,
     identical resolution, to ELITEA-1916's Known Defect #1 for the Agent
     entity).**

4. With the toast visible/dismissing, inspect the modal (still open).
   - **Verify**: the modal (`generate-skill-modal`) is still present in the
     DOM and still shows the **review form** (not the input/prompt step,
     not closed) — confirmed live via
     `document.querySelector('[data-testid="generate-skill-modal"]')`
     truthy immediately after the failure. Source-confirmed why:
     `GenerateEntityModal.jsx`'s `handleApprove` catch block only calls
     `setIsApproving(false)` and `toastError(...)` — it never calls
     `handleClose()` (that only happens inside the `try` block, after
     `onApprove` succeeds), so `step` stays `STEPS.REVIEW` and `draftData`
     is untouched — identical mechanism to ELITEA-1916's Step 4, same
     shared component. This is the case's "the review/edit form is still
     displayed" (step 4), live-verified, not merely inferred from source.

5. With the modal still open on the review step, inspect all draft fields.
   - **Verify**: Name, Description, and Instructions still read the exact
     generated-draft values (confirmed live via direct DOM read
     immediately after the failure — see step 1's verbatim values,
     unchanged after the failed create). This is the case's "the draft
     data (Name, Description, Instructions) is still present and editable"
     (step 5) — because `draftData` is component state independent of the
     failed `createSkill` mutation, same underlying reason ELITEA-1916's
     AFS documents for the Agent entity's analogous fields.

6. With the review form still populated and the failure toast gone, click
   **"Create Skill"** again (`generate-skill-approve-button`) — the SAME
   button; there is no separate retry control (mirrors ELITEA-1915/1916's
   finding for the Generate/Create buttons in this shared modal). This time
   the route mock is cleared/not re-installed, letting the request reach
   the real DEV backend.
   - **Verify**: the button is genuinely re-enabled and clickable
     (`isApproving` was reset to `false` in the catch block, and
     `isDraftValid` was never touched by the failure — confirmed live:
     `approve_button.disabled === false` immediately after the toast).
     Clicking it resolves `201`, the modal closes, and the app
     auto-navigates to the created skill's detail page — confirmed live
     this run: navigated to `/skills/all/1960`, with the detail page
     showing Name `"elitea-2000-draft-skill-2"`, Description, and
     Instructions all matching the draft exactly (Skill ID `1960`, Version
     ID `2142`, version name `base`). This is the case's "the Skill is
     created and the user is redirected to the Skill details page" (step
     6), live-verified end-to-end against the real backend, not merely
     mocked twice. Skill `1960` (and an earlier throwaway attempt, Skill
     `1959`, created during this same exploration — see Automation Hints)
     were both deleted via the Skill detail page's "SKILL" menu → "Delete
     skill" → typed exact name → "Delete", confirmed removed from
     `/skills/all`.

## Expected Results
Matches the case's stated Pass criteria on every FUNCTIONAL point — user
stays on the review step (step 4), draft data is preserved (step 5), retry
creates the Skill and redirects to its details page (step 6) — live-verified
end-to-end including a real create call against DEV (deleted afterward, see
Cleanup). The one divergence is the *mechanism* of the error surface in step
3: a toast, not an inline/embedded form message — see Known Defects #1,
classified as case-text drift (clarification), not a functional failure;
the user genuinely IS informed of the failure by an equally standard
app-wide UI pattern (the same one ELITEA-1916 already documented for the
sibling Agent entity).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: "A skill draft has been generated and the review/edit form is displayed" | — | step 1 | step 1 folds this into itself (navigate + open + fill + generate), since live this is an outcome of Step 1, not a standalone precondition | clarification *(case-text drift, same class as ELITEA-1915/1916's AFSs — not a product defect)* |
| Precondition: "A method to simulate or trigger a creation API failure is available" | achievable | step 2 | step 2: Playwright route interception on the exact create-skill POST endpoint | asserted |
| 1 Generate a skill draft, review it, and click "Create Skill" | Skill creation is initiated | steps 1-2 | step 2: mocked request observed resolving with the injected 500 | asserted |
| 2 Simulate or trigger a creation API failure | The API call fails | step 2 | step 2: mocked 500, confirmed via the resolved mocked response body | asserted |
| 3 Verify form-level error messages are displayed using the standard Skill creation error handling | Error messages are visible on the review/edit form | step 3 | step 3: app-wide toast (`toast-alert`/`toast-message`), `data-severity="error"`, exact injected message | asserted *(mechanism diverges from "form-level" — see Known Defects #1; the user-facing outcome, "informed of the failure," is fully satisfied)* |
| 4 Verify the user remains on the review/edit step (not redirected or kicked back to prompt) | The review/edit form is still displayed | step 4 | step 4: modal + review form still present in DOM immediately after failure, source-confirmed why (`handleClose()` never called on the catch path, shared `GenerateEntityModal.jsx`) | asserted |
| 5 Verify the draft data (Name, Description, Instructions) is still present and editable | All draft fields retain their values and are editable | step 5 | step 5: all fields read back verbatim against the mocked draft immediately after failure | asserted |
| 6 Correct the issue and click "Create Skill" again — verify the Skill is created successfully | The Skill is created and the user is redirected to the Skill details page | step 6 | step 6: real (unmocked) backend call resolves 201, modal closes, auto-navigation to the created skill's detail page, all fields verified against the draft | asserted |

### Axis 2 — Analyst additions

- step 2 documents the exact scoping requirement (POST-only) needed to
  avoid accidentally intercepting the `skillList`/`totalSkills` GET queries
  that share the same URL — *added: an implementer who scopes the mock to
  URL-only (no method check) will break every OTHER test/page load that
  fires a Skills-list GET on the same route while the mock is active.*
- step 3 documents the exact source location and mechanism proving WHY the
  toast (not an inline alert) is the correct signal for THIS failure path,
  distinct from the generation-failure path's inline `error_alert` — *added:
  gives the implementer a stable code anchor
  (`GenerateEntityModal.jsx`'s `handleApprove` catch block) instead of only
  a live observation.*
- step 6 documents the exact re-enable condition (`isApproving`/
  `isDraftValid` both false after a failed attempt) — *added: an
  implementer might otherwise assume a failed create leaves the form
  invalid/locked; source + live-verified DOM read confirm it does not.*
- **Exploration note, not asserted by this case:** the first live attempt
  in this run used a naive `window.fetch` monkey-patch with a
  call-counting guard (`if (count === 1) return mocked500; else fall
  through`) via `browser_evaluate` (the only network-mocking technique
  available to this session's tooling — no direct `page.route()` call).
  That first attempt's Create-Skill click unexpectedly reached the REAL
  backend and created a genuine skill (id `1959`) instead of hitting the
  mocked failure — most likely because the click fired while the count-based
  branch logic interacted badly with this ad hoc technique (root cause not
  fully isolated; not worth further diagnosis since it is a property of the
  EXPLORATION workaround only). The SECOND attempt, which always returns
  the mocked 500 for every matching POST (no counter) and explicitly clears
  the mock before retrying, worked correctly and is what steps 2-6 above
  document. **This is a property of the ad hoc `browser_evaluate` fetch-patch
  technique, not of the product** — the automated test MUST use Playwright's
  native `page.route()`/`page.unroute()` (exactly as `mock_generate_failure`/
  `mock_generate_success`/the Agent entity's `mock_create_failure` already
  do), which intercepts at the browser/protocol level and does not share
  this fragility. Flagged here so the implementer doesn't waste time trying
  to reproduce the naive monkey-patch's behavior — go straight to
  `page.route()`.

## Cleanup
1. Steps 1-5 create no product state — the mocked failure never reaches the
   real backend (route interception fulfills locally). Steps 3-5's toast and
   review-form assertions require no teardown beyond the mock's own
   page-scoped lifecycle.
2. **Step 6's retry, once its route mock/interception is cleared (or a
   second mock resolving 201 is used — see Automation Hints), creates a
   REAL skill** on the DEV backend. This run created and then deleted skill
   id `1960` ("elitea-2000-draft-skill-2") via the Skill detail page's
   "SKILL" menu → "Delete skill" → typed the exact name into the
   confirmation dialog → "Delete" (and separately cleaned up the id `1959`
   throwaway from the first, misbehaving exploration attempt the same way).
   An automated test MUST clean this up the same way every other
   Approve-clicking test in `test_skill_build_with_ai.py` does (e.g.
   `test_create_skill_from_unmodified_draft_persists_generated_values`):
   capture `created_skill_id` from the create response and delete it via
   `skill_api.delete_skill(...)` in a `finally` block.
3. Playwright route interception is scoped to the test's own page/context
   and needs no explicit teardown beyond normal fixture-per-test lifecycle,
   consistent with ELITEA-1915/1916's Cleanup notes.

## Concrete Handles (discovered during exploration)

All handles below are **pre-existing testids**, already declared as
`LocatorDescriptor` fields on `GenerateSkillModalPage`
(`automation/pages/generate_skill_modal_page.py`) — this case needs **zero**
new EliteaUI testid additions, except the app-wide toast fields which need
a page-object wiring (not a testid) — see Implementer note below.

| Element | Recommended Locator | Provenance |
|---|---|---|
| "Build with AI" open button | `generate-skill-open-button` | on-main ✓ — already used by every other Skill Build-with-AI test in this file |
| Modal container | `generate-skill-modal` | on-main ✓ — same |
| Prompt textarea | `generate-skill-prompt-input` | on-main ✓ — same |
| "Generate Draft" / retry button | `generate-skill-submit-button` | on-main ✓ — same |
| Loading indicator | `generate-skill-loading-indicator` | on-main ✓ — same |
| Review-form Name input | `generate-skill-review-name-input` | on-main ✓ — used by ELITEA-1990/1991/1993 |
| Review-form Description input | `generate-skill-review-description-input` | on-main ✓ — same |
| Review-form Instructions input | `generate-skill-review-instructions-input` | on-main ✓ — same |
| "Create Skill" / Approve button | `generate-skill-approve-button` | on-main ✓ — used by ELITEA-1990/1991/1993 (never yet clicked in a create-failure context) |
| **App-wide toast alert** | `toast-alert` (+ `[data-testid="toast-alert"][data-severity="{}"]` state filter, mirroring the existing `TOAST_ALERT_SEVERITY` class-constant pattern ELITEA-1916 already added to `GenerateAgentModalPage`) | on-main ✓ — pre-existing shared component (`src/components/Toast.jsx`), **not yet declared on `GenerateSkillModalPage`** — this is the first Skill Build-with-AI-flow case to need it |
| App-wide toast message text | `toast-message` | on-main ✓ — same component, same "not yet on this page object" note |
| App-wide toast dismiss button | `toast-dismiss-button` | on-main ✓ — same (not needed by this case's own assertions, listed for completeness) |

**Implementer note:** add `toast_alert`/`toast_message`/`TOAST_ALERT_SEVERITY`
as class-level `LocatorDescriptor` fields on `GenerateSkillModalPage` (or
hoist them onto the shared `GenerateEntityModalPageBase` if the reviewer
prefers, since both entity page objects need the identical fields — copy
the existing pattern verbatim from `generate_agent_modal_page.py:111-122`
(ELITEA-1916's addition) or `agent_detail_page.py:388-399`. This is wiring
a **page-object field** to an **existing, unchanged EliteaUI testid** — no
`add-data-testid` run is needed, no EliteaUI source changes at all.

## Network Behavior
- `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/{project_id}`
  — unrelated to this case's own assertions beyond reaching the review
  form; mocked per Step 1's Test Data (see ELITEA-2001's AFS for the full
  contract).
- `POST /api/v2/elitea_core/skills/prompt_lib/{project_id}` — **the
  endpoint this case is actually about.** Confirmed via source
  (`skillsApi.js`'s `skillCreate` mutation). Mocked response (Step 2):
  `500` + `{"error":"Simulated creation failure for ELITEA-2000"}`. Real
  response (Step 6, live DEV backend, this run): `201`-equivalent (the app
  navigated on success) with the created skill's full JSON (`id: 1960`,
  `name`, version `id: 2142`, etc.).
- No `associateToolkits`/similar follow-up call fires on a Skill create at
  all (unlike the Agent flow's optional Toolkit/Skill association calls) —
  the Skill draft carries no suggested-resources concept whatsoever
  (`GenerateSkillReviewForm` renders only Name/Description/Instructions),
  so there is nothing analogous to guard against here.

## Known Defects Found During Exploration

1. **Case-text mismatch (CLARIFICATION, not a product defect) — Step 3's
   "form-level error message... using the standard Skill creation error
   handling" expectation does not match the live mechanism, which is an
   app-wide TOAST, not an inline/embedded alert inside the modal.**
   Live-verified and source-confirmed
   (`GenerateEntityModal.jsx`'s `handleApprove` catch block calls
   `toastError(buildErrorMessage(err))`, never renders an `Alert` inside the
   modal body the way the *generation*-failure path does). This is the
   EXACT SAME deterministic UX inconsistency ELITEA-1916 already documented
   for the Agent entity (generation failure → inline `Alert`; create
   failure → toast only) — confirmed here to be entity-agnostic, since both
   entities render through the identical shared `GenerateEntityModal.jsx`.
   Not classified as a functional product defect for THIS case, for the
   same three reasons ELITEA-1916's AFS already gives: (a) the user
   genuinely IS informed via a standard, widely-reused app pattern; (b) the
   case's other, more load-bearing requirements (stay on review step, data
   preserved, retry works) all pass cleanly; (c) the REGULAR (non-AI)
   Skill create form has no stronger "standard" to hold this flow to
   either. **Not filed as a new GitHub issue** — this is the identical
   case-authoring precision gap ELITEA-1916 already flagged
   (recommend the TMS case wording be loosened the same way ELITEA-1916's
   AFS recommended for its Agent sibling; a single documentation nit
   covering both would be ideal, not duplicated per-entity tickets).
   Asserted here against the LIVE toast-based contract per the
   reverse-masking guard.

No functional product defect was found. The live product's behavior across
all 6 case steps matches the case's Pass criteria once Known Defect #1's
mechanism-level correction is accounted for — and matches ELITEA-1916's
Agent-entity finding byte-for-byte, confirming the shared component's
behavior is consistent across both entities.

## Blocked Steps
None. All 6 steps were executed end-to-end live (across two exploration
attempts — see Axis 2's exploration note for why a second, cleaner attempt
was needed), including a full real (unmocked) retry-recovery round-trip
against the live DEV backend in Step 6 (skill id `1960`, created then
deleted as part of this exploration's cleanup, plus the id `1959`
throwaway from the first attempt) — this AFS is `ready-for-automation` for
all 6 steps.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Home:
  `automation/tests/ui/skills/test_skill_build_with_ai.py` (existing file —
  add a new test class, e.g.
  `TestSkillBuildWithAICreationFailureRecovery`, alongside the existing
  `TestSkillBuildWithAIGenerationFailureRetry` class; reuses the same
  `GenerateSkillModalPage` page object and `skill_api` fixture already used
  throughout this file).
- **New page-object method needed** on `GenerateSkillModalPage`
  (`automation/pages/generate_skill_modal_page.py`): a
  `mock_create_failure()` sibling to the base class's existing
  `mock_generate_failure()`/`mock_generate_success()`
  (`generate_entity_modal_page_base.py:100-146`), targeting
  `**/elitea_core/skills/prompt_lib/**` (POST) instead of the generate-draft
  route — **copy `GenerateAgentModalPage.mock_create_failure()`
  (`generate_agent_modal_page.py:488-511`, ELITEA-1916) verbatim, adjusting
  only the route constant and testids.** That method already handles the
  POST-only scoping (route.continue_() for non-POST) this case's Step 2
  requires. Also add `expect_create_response()` and
  `click_approve_and_wait_for_creation()`/similar wait helpers mirroring
  `generate_agent_modal_page.py:340-467` — the Skill entity's create
  response wait is simpler than the Agent's (no toolkit/skill-association
  follow-up calls to also await, per this AFS's Network Behavior section),
  so a single-response wait analogous to
  `click_approve_and_wait_for_agent_created()` (not the multi-response
  Toolkit/Skill variants) is the correct pattern to copy.
- **Use Playwright's native `page.route()`/`page.unroute()`, NOT a
  `browser_evaluate` fetch monkey-patch** — see Axis 2's exploration note
  for why the ad hoc technique misbehaved on its first attempt during this
  live exploration. The existing `mock_generate_failure`/
  `mock_generate_success` in `generate_entity_modal_page_base.py` already
  establish the correct native-route pattern; mirror it exactly.
- For Step 6's retry, recommend registering a **second, call-counted**
  route handler on the same create endpoint (mock 500 on the 1st POST,
  200/201 with a synthetic created-skill JSON on the 2nd) for CI
  determinism — same rationale ELITEA-1915/1916's AFSs give for preferring
  this over hitting the real DEV backend twice. This exploration used the
  real DEV backend for the retry leg specifically to prove the end-to-end
  contract once; the synthetic-second-mock approach is what should ship in
  the automated test.
- Wait strategy: wait on the create-skill POST's response
  (`page.expect_response(...)`) for BOTH the failed and retried requests —
  do not poll/sleep. For the toast assertion (Step 3), assert immediately
  after the mocked response resolves, before any other wait — the toast is
  transient (MUI `Snackbar` `autoHideDuration`, same mechanism ELITEA-1916
  documents) and a delayed assertion will flake.
- Cleanup: this test creates a real skill on its Step 6 retry (unlike
  ELITEA-2001, which never reaches Approve) — wrap Steps in `try`/`finally`
  and call `skill_api.delete_skill(created_skill_id)` in `finally`, exactly
  matching this file's other Approve-clicking test's pattern
  (`test_create_skill_from_unmodified_draft_persists_generated_values`).
