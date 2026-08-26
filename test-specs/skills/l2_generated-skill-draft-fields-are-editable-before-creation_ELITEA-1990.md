# Test Case: Generated skill draft fields are editable before creation

> ⚠️ **UNDER REVIEW — 2026-08-14 fidelity audit. Do NOT reuse this AFS as a pattern.**
>
> This spec directs the implementer to **substitute the system under test** (mocking
> the generate-draft response) for a TMS case whose text never asks for simulation.
> Classification: **MIXED** — editability is a real observable; the assertions that the fields are pre-populated with the *generated* values are tautologies against the test's own payload.
>
> **Rework by class:** `TERMINAL` → rewrite against the live flow (the test currently
> proves nothing about the case's subject). `MIXED` → drop the tautological assertions
> and prefer a live draft; the rest of the coverage is sound. `TRANSIT` → cheapest —
> swap the mock for a live generate, or keep it and declare it per
> `.agents/testing.md` § Fidelity policy.
>
> Justifications of the form "the same sanctioned-mocking technique this file already
> uses" or "not a good use of fixture-creation effort" are **not valid authorities**:
> nothing sanctions response mocking, and cost is never a reason to substitute. See
> `.agents/role-overrides.md` § Every role — precedent is not authority.
>
> **`extend-existing` must not inherit this design.** Rework tracked on
> [#1298](https://github.com/EliteaAI/elitea-testing-public/issues/1298) (agents) and
> [#1399](https://github.com/EliteaAI/elitea-testing-public/issues/1399) (skills); full
> chain in `sdlc-skills/bundles/test-automation/incidents/2026-08-14-response-mocking-drift.md`.

## Metadata
- **TMS ID**: ELITEA-1990
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/skills/build_with_ai/ELITEA-1990_generated-skill-draft-fields-are-editable-before-creation.md`
- **Priority**: l2 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: source case frontmatter carries `status: draft` /
  `execution_type: manual`. `.agents/testing.md` has no `TMS case-gate`
  section defining excluded statuses for this project (same recurring gap
  ELITEA-1915/ELITEA-2001's AFS flagged) — per the skill's default, this run
  proceeded and fetched/executed the case.
- **Relationship to ELITEA-2001 (Skill "Build with AI" failure/retry)**:
  that AFS explicitly scoped the review-form's Name/Description/Instructions
  fields as **out of scope** ("case only requires confirming a draft WAS
  returned... not inspected field-by-field... out of scope for ELITEA-2001")
  and flagged them as a future gap. This case (ELITEA-1990) is exactly that
  follow-up — it inspects and exercises those three fields directly, plus
  the full create-skill approval flow through to the detail page. No
  Rule-6 overlap: ELITEA-2001 never edits or approves the review form;
  this case's entire assertion surface (field editability + created-skill
  fidelity) is untouched by it. Classified fresh `ready-for-automation`,
  not `extend-existing`/`already-covered`.
- **Relationship to the open bug #524 (agent creation 400,
  temperature/reasoning_effort conflict)**: investigated per dispatch
  instructions. **Not reproduced or applicable here.** Skill creation goes
  through a different endpoint (`POST
  /elitea_core/skills/prompt_lib/{projectId}`, distinct from the Agent
  entity's `/applications/prompt_lib/{projectId}`) and a different payload
  shape (`GenerateSkillModal.jsx handleApprove`: `name`, `description`,
  `versions: [{ name, instructions }]` — no `temperature` /
  `reasoning_effort` fields at all in the Skill create payload). Both live
  runs in this session (see Steps 6-7) returned `201 Created` with no
  network or console errors. This case is unaffected by #524; not a
  duplicate.

## Preconditions
- User is logged in to Elitea (localhost `auth_state`/`VITE_DEV_TOKEN`) with
  editor/admin role sufficient to create skills — confirmed live, the
  "Build with AI" button rendered and worked without a permission gate
  hitting in this run.
- A skill draft has been generated via the Build with AI modal — covered by
  this AFS's own Step 1-2 (case's stated precondition is actually the
  outcome of those steps, same case-text-drift pattern documented in the
  ELITEA-1915/ELITEA-2001 AFS lineage — **not** filed separately, see Known
  Defects #1).
- A project is selected/accessible (`Private`, id `399` in this run).

## Test Data

### reuse-existing
None — this case has no dependency on any pre-existing environment fixture
(no shared MCP/toolkit/credential/agent is read or attached). The only
precondition is project selection (`Private`, id `399`), already covered
under § Preconditions.

### generate-per-test
All test data below is created live by the test itself and deleted in this
AFS's own Cleanup section — none of it is shared across tests or left
behind for a later case to reuse:
- Natural-language prompt used to generate the draft:
  `"Create a skill that reviews pull request diffs and flags missing test
  coverage."` — any valid non-empty prompt satisfies the case; content
  itself isn't asserted.
- Live-generated draft (real DEV backend, not mocked — this case explicitly
  tests real user editing + real creation, so mocking the draft would
  weaken the assertion): `name: "pr-test-coverage-review"`, plus a
  generated `description` and `instructions` (full text logged in the raw
  exploration; not reproduced verbatim here since only the *edited* values
  matter to the case).
- Edited values written into the three review-form fields (Run 2, the
  authoritative testid-verified run — see Concrete Handles):
  - Name: `edited-pr-coverage-skill-v2`
  - Description: `Testid-verified edited description for ELITEA-1990.`
  - Instructions: `Testid-verified edited instructions for ELITEA-1990.`
- The resulting created Skill itself (ids 574/575 across this AFS's two
  exploration runs) is also generate-per-test data — deleted via the UI
  delete-menu flow as part of Cleanup (see § Cleanup).

### generate-shared-with-cleanup
None — nothing created by this case is intended for reuse by other tests;
every artifact is scoped to, and torn down within, this case's own run.

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`. In the "General" accordion
   section, click **"Build with AI"** (`generate-skill-open-button`) to open
   `GenerateSkillModal`. Fill the prompt textarea
   (`generate-skill-prompt-input`) with the test-data prompt.
   - **Verify**: Generate button (`generate-skill-submit-button`) is
     disabled while the prompt textarea is empty, becomes enabled once
     filled — confirmed live via snapshot before/after fill.

2. Click **Generate** and wait for the real (unmocked) DEV backend to
   return a draft (network: `POST
   /api/v2/elitea_core/generate_skill_draft/prompt_lib/399 => [200]`,
   resolved in both runs in this session).
   - **Verify**: the modal transitions to the review-form step, showing
     non-empty generated Name/Description/Instructions and the
     **"Back to prompt"** / **"Create Skill"** action buttons
     (`generate-skill-back-button` / `generate-skill-approve-button`) —
     matches ELITEA-1990's Step 1 expected result exactly. This is the
     precondition the case describes, folded into Steps 1-2 (see Known
     Defects #1).

3. Overwrite the generated **Name** field
   (`generate-skill-review-name-input`, newly added — see Concrete Handles)
   with a different valid value (`edited-pr-coverage-skill-v2`).
   - **Verify**: the field accepts and displays the new value — confirmed
     live via accessibility snapshot (`textbox: edited-pr-coverage-skill-v2`)
     immediately after the edit, and via the field's own live character
     counter (`24/64` in the first run, confirming the underlying React
     state — not just the DOM value — updated on edit).

4. Overwrite the generated **Description** field
   (`generate-skill-review-description-input`, newly added) with custom
   text (`Testid-verified edited description for ELITEA-1990.`).
   - **Verify**: the field accepts and displays the new value — confirmed
     live via snapshot.

5. Overwrite the generated **Instructions** field
   (`generate-skill-review-instructions-input`, newly added) with custom
   text (`Testid-verified edited instructions for ELITEA-1990.`).
   - **Verify**: the field accepts and displays the new value, including
     its own live character counter (`64/2500` observed) confirming
     controlled-component state — confirmed live via snapshot. Steps 3-5
     together satisfy the case's Step 5 ("Verify all three fields accept
     the edits") — all three fields retained their user-entered values
     simultaneously in the same snapshot (see raw exploration for the
     combined post-edit snapshot).

6. Click **"Create Skill"** (`generate-skill-approve-button`).
   - **Verify**: network shows `POST
   /api/v2/elitea_core/skills/prompt_lib/399 => [201] Created` (confirmed
     live, two independent runs — skill IDs 574 and 575, both since
     deleted as part of this AFS's cleanup). Zero console errors/warnings
     across the whole flow (confirmed via `browser_console_messages`,
     level=warning, 0 results both runs).

7. Observe the resulting navigation and the created skill's field values.
   - **Verify**: the browser is redirected to `/skills/all/{new_skill_id}`
     (confirmed live: `/skills/all/574` then `/skills/all/575` across the
     two runs) — the Skill details page, satisfying the case's Step 8. The
     detail page's General section shows **Name**, **Description**, and
     **Instructions** fields populated with the *edited* Run-2 values
     (`edited-pr-coverage-skill-v2` /
     `Testid-verified edited description for ELITEA-1990.` /
     `Testid-verified edited instructions for ELITEA-1990.`) — **not** the
     originally-generated draft values (`pr-test-coverage-review` / the
     AI-generated description / the AI-generated instructions) — confirmed
     live via a full accessibility snapshot of the detail page's `Name *`,
     `Description *`, and Instructions editor textboxes immediately after
     redirect. This directly satisfies the case's core assertion (Step 7):
     the skill is created with the user-edited values, not the original
     generated ones.

## Expected Results
Matches the case's stated Pass criteria exactly, live-verified end-to-end
across two independent runs (Run 1 via accessibility-tree refs before the
review-form testids existed; Run 2 via the newly-added
`generate-skill-review-*-input` testids after they landed): all three
review-form fields (Name, Description, Instructions) accept and retain
user edits over the AI-generated draft values; clicking "Create Skill"
creates the skill with the edited values (confirmed on the resulting detail
page, not just inferred from the request payload); the user is redirected
to the new skill's details page. No step produced an unexpected result.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: "A skill draft has been generated via the Build with AI modal" | draft exists | steps 1-2 | step 2: review form populated after a real (unmocked) generate call | clarification *(case-text drift — the case states this as setup, live it's the outcome of Steps 1-2; not a product defect — see Known Defects #1)* |
| 1 Generate a skill draft via Build with AI modal | review/edit form displayed with generated Name/Description/Instructions | steps 1-2 | step 2: review form step reached, all three fields non-empty | asserted |
| 2 Modify the generated Name to a different valid value | Name field accepts the edit and displays the new value | step 3 | step 3: snapshot shows edited value + live character counter update | asserted |
| 3 Modify the generated Description | Description field accepts the edit and displays the new value | step 4 | step 4: snapshot shows edited value | asserted |
| 4 Modify the generated Instructions | Instructions field accepts the edit and displays the new value | step 5 | step 5: snapshot shows edited value + live character counter | asserted |
| 5 Verify all three fields accept the edits | all three fields reflect user-entered values | steps 3-5 | combined post-edit snapshot shows all three edits present simultaneously | asserted |
| 6 Click "Create Skill" | skill creation initiated | step 6 | step 6: `POST .../skills/prompt_lib/399 => 201` | asserted |
| 7 Verify the Skill is created with the edited (not original generated) values | created Skill shows user-modified Name/Description/Instructions | step 7 | step 7: detail-page snapshot shows edited values, contrasted explicitly against the original generated values | asserted |
| 8 Verify the user is redirected to the created Skill details page | Skill details page of the new Skill displayed | step 7 | step 7: URL `/skills/all/{id}`, confirmed twice (574, 575) | asserted |

### Axis 2 — Analyst additions

- step 3 documents the field's own live `{len}/{max}` character-count
  helper text as a second, independent signal (beyond the raw input value)
  that the underlying React/MUI controlled-component state actually
  updated on edit, not just the DOM — *added: gives the implementer a
  flake-resistant secondary assertion.*
- Metadata documents the explicit non-relationship to the open bug #524
  (different endpoint, different payload shape, no `temperature`/
  `reasoning_effort` fields in the Skill create call) — *added: closes out
  the dispatch instruction's open question so no future analyst re-checks
  this.*
- Concrete Handles documents that this case is what motivated adding
  `generate-skill-review-{name,description,instructions}-input` testids,
  which did not exist before this run — *added: gives the implementer the
  exact provenance and PR link for the new selectors.*
- Run 1 (pre-testid, ref-based) vs Run 2 (post-testid) is documented as two
  independent full passes of the same flow, both producing an identically
  successful outcome — *added: strengthens confidence this isn't a
  one-off; not itself required by the case's Pass/Fail criteria.*

## Cleanup
1. Both skills created during this AFS's exploration (id 574 from Run 1,
   id 575 from Run 2) were deleted live via the UI overflow-menu delete
   flow (`skill-controls-menu-button` → `skill-delete-menu-item` →
   type-to-confirm dialog → `Delete`), confirmed by redirect back to
   `/skills/all` both times. No skill records from this case remain on the
   shared local DEV backend.
2. A raw `fetch(..., {method:'DELETE'})` from the page's own JS context was
   attempted first and failed — see Known Defects #2 (environment note, not
   a product defect) — the UI delete flow was used instead and succeeded
   cleanly.
3. For automated runs: use the existing `SkillAPI.delete_skill(skill_id)`
   helper (`automation/api/client.py:1270`, cookie-based auth) in a
   fixture/teardown, matching this project's established skill-test cleanup
   convention (`SkillAPI` already exists and is proven working via cookie
   auth from other skill test fixtures) — do **not** rely on the raw
   `fetch()`-from-page-context approach that failed during this
   exploration (see Known Defects #2).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| "Build with AI" open button | `generate-skill-open-button` (pre-existing, confirmed live) | n/a — testid-only policy |
| Prompt textarea | `generate-skill-prompt-input` (pre-existing) | n/a |
| Generate button | `generate-skill-submit-button` (pre-existing) | n/a |
| Review-form **Name** field | **`generate-skill-review-name-input`** — newly added this run. Applied via `TextField slotProps.htmlInput['data-testid']` on the native `<input>` in `GenerateSkillReviewForm.jsx` (was previously **zero** testid coverage on all three review-form fields — confirmed by source read before the fix). Landed on `automation/testids` (commit `383c11c`) and as draft PR [EliteaAI/EliteaUI#566](https://github.com/EliteaAI/EliteaUI/pull/566) against `main`. | n/a — testid-only policy; do not use accessible-name/role fallback in the implementation |
| Review-form **Description** field | **`generate-skill-review-description-input`** — newly added this run, same PR/commit as above | n/a |
| Review-form **Instructions** field | **`generate-skill-review-instructions-input`** — newly added this run, same PR/commit as above | n/a |
| "Back to prompt" button | `generate-skill-back-button` (pre-existing) | n/a |
| "Create Skill" button | `generate-skill-approve-button` (pre-existing) | n/a |
| Skill detail page Name field | `skill-name-input-field` (pre-existing, per `skill_form_page.py`/`skill_detail_page.py`) — confirmed live post-redirect shows edited value | n/a |
| Skill detail page Description field | `skill-description-input-field` (pre-existing) — confirmed live | n/a |
| Skill detail page Instructions editor | `skill-instructions-editor-content` (pre-existing) — confirmed live | n/a |
| Skill delete flow (cleanup) | `skill-controls-menu-button` → `skill-delete-menu-item` → `Dialog.type_to_confirm` + `Delete` (all pre-existing, per `skill_detail_page.py:delete_skill_via_menu`) | n/a |

**Testid provenance for this AFS**: `automation/testids` commit `383c11c`
("test: [EL-1990] add data-testid for skill build-with-ai review form
fields"); review PR `testids/ELITEA-1990-skill-review-form-fields` →
`EliteaAI/EliteaUI` `main`, opened as **draft**:
https://github.com/EliteaAI/EliteaUI/pull/566. Diff is attribute-only
(verified: only `data-testid` lines differ from `main`, modulo prettier's
multi-line reformatting of the same `slotProps` object literal — no
behavioral change).

## Network Behavior
- `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/399` — draft
  generation, `200` both runs.
- `POST /api/v2/elitea_core/skills/prompt_lib/399` — skill creation on
  approval, `201 Created` both runs. Payload (from
  `GenerateSkillModal.jsx handleApprove`): `{name, description, versions:
  [{name: "base", instructions}]}` — confirmed this shape carries **no**
  `temperature`/`reasoning_effort` fields, unlike the Agent-creation
  endpoint implicated in bug #524.
- `GET /api/v2/elitea_core/skill/prompt_lib/399/{id}` — detail-page load
  after redirect, `200` both runs.
- No console errors or warnings observed at any point in either full run
  (`browser_console_messages`, level=warning, 0 results).

## Known Defects Found During Exploration

1. **Case-text drift (CLARIFICATION, not a product defect).** The case's
   Preconditions line ("A skill draft has been generated via the Build with
   AI modal") describes the outcome of this AFS's own Steps 1-2, not an
   independent setup requirement — identical pattern to the one already
   documented in the ELITEA-1915/ELITEA-2001 AFS lineage for the sibling
   Agent/Skill "Build with AI" cases. Not filed as a GitHub issue — a
   case-authoring precision gap, not a live product defect.

2. **[Non-blocking, informational — not filed] Raw `fetch()` DELETE from
   page JS context fails for this app's API.** Attempting
   `fetch('/api/v2/.../skill/...', {method:'DELETE'})` directly from the
   page's JS console context (via `browser_evaluate`) failed with a CORS
   error — the request got redirected through
   `dev.elitea.ai/forward-auth/auth_oidc/login` (missing an
   `Access-Control-Allow-Origin` header on that redirect target), unlike
   the app's own `axios`-based calls which succeed from the same origin.
   This is an **environment/tooling** observation about ad-hoc
   `fetch()`-from-console cleanup, not a product defect (the real app never
   makes bare unauthenticated `fetch()` calls this way — it uses its own
   configured HTTP client with proper headers). Worked around by using the
   UI's own delete flow instead (see Cleanup #1). Not filed — routes to
   this AFS's Automation Hints (use `SkillAPI.delete_skill()`, not raw
   `fetch()`, for automated cleanup).

No functional product defect was found. The live product's behavior across
all 8 case steps matches the case's Pass criteria exactly, across two
independent live runs.

## Blocked Steps
None. All case steps were executed end-to-end live, twice — once via
accessibility-tree refs before the review-form testids existed (Run 1,
skill 574), and once via the newly-added `generate-skill-review-*-input`
testids after `add-data-testid` landed them (Run 2, skill 575). Both runs
produced an identical, fully successful outcome. This AFS is
`ready-for-automation` for all steps using the Run 2 (testid-based) handles.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Home:
  `automation/tests/ui/skills/test_skill_build_with_ai.py` (existing file —
  add a new test class/method alongside
  `TestSkillBuildWithAIGenerationFailureRetry`; do not duplicate the
  existing generate-mock helpers, reuse `GenerateSkillModalPage`).
- Page object: extend `automation/pages/generate_skill_modal_page.py`
  (`GenerateSkillModalPage`) with three new `LocatorDescriptor` fields for
  the review-form testids added by this case:
  ```python
  review_name_input = LocatorDescriptor(
      testid="generate-skill-review-name-input",
      description="Review-form Name field (editable before creation)",
  )
  review_description_input = LocatorDescriptor(
      testid="generate-skill-review-description-input",
      description="Review-form Description field (editable before creation)",
  )
  review_instructions_input = LocatorDescriptor(
      testid="generate-skill-review-instructions-input",
      description="Review-form Instructions field (editable before creation)",
  )
  ```
  These fields did **not** exist before this AFS — do not confuse them
  with the pre-existing `skill-name-input`/`skill-description-input`/
  `skill-instructions-editor` testids, which belong to the separate main
  create-skill form, not this modal's review step.
- Recommend mocking the `generate_skill_draft` response (via the existing
  `mock_generate_success()` helper on `GenerateEntityModalPageBase`) for
  determinism, rather than waiting ~20s+ for a real LLM generation each
  run — this case's assertions are about field editability and the
  create-skill payload, not about generation quality, so a synthetic draft
  is sufficient and faster. Both this AFS's live runs used the *real*
  backend to also validate the full happy path end-to-end at least once;
  the implementer can decide whether to keep one un-mocked smoke variant.
- Cleanup: use `SkillAPI.delete_skill(skill_id)` (cookie-auth, existing
  helper) in a `try/finally` or pytest fixture teardown — get `skill_id`
  either from the URL after redirect (`page.url` regex
  `/skills/all/(\d+)$`) or from the `Skill ID:` field on the detail page
  (`skill-id`-adjacent copy button, not yet a `LocatorDescriptor` — reuse
  the URL-regex approach instead, it's simpler and already proven in this
  exploration).
- Assertion for Step 7 (edited-not-generated values) should compare against
  the actual generated draft values captured earlier in the same test (via
  the review-form fields' `input_value()` immediately before editing), not
  hardcoded constants — this makes the test robust to LLM output variance
  if the un-mocked variant is kept, and trivial if the draft is mocked.
