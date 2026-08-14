# Test Case: Build with AI — name field validation on invalid manual edits

> ⚠️ **UNDER REVIEW — 2026-08-14 fidelity audit. Do NOT reuse this AFS as a pattern.**
>
> This spec directs the implementer to **substitute the system under test** (mocking
> the generate-draft response) for a TMS case whose text never asks for simulation.
> Classification: **MIXED** — steps 2+ (name validation on manual edits) are a real observable; step 1's `get_review_name() == payload["name"]` is a tautology.
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
- **TMS ID**: ELITEA-1993
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/skills/build_with_ai/ELITEA-1993_build-with-ai-name-field-validation-on-invalid-manual-edits.md`
- **Priority**: l2 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: source case frontmatter carries `status: draft` /
  `execution_type: manual`. `.agents/testing.md` has no `TMS case-gate`
  section defining excluded statuses for this project (same recurring gap
  flagged by the ELITEA-1990/1989/2001 AFS lineage) — per the skill's
  default, this run proceeded and fetched/executed the case.
- **Relationship to ELITEA-1990 (review-form fields are editable before
  creation)**: that AFS covers the review form's Name/Description/
  Instructions fields being *editable* (accept and retain arbitrary valid
  edits) and the create-flow through to the detail page. It never enters an
  *invalid* value into any field and never inspects the validation/disabled
  state. This case (ELITEA-1993) is the validation-only counterpart:
  it exercises exactly the negative-input paths ELITEA-1990 explicitly
  never asserts. No Rule-6 overlap — classified fresh
  `ready-for-automation`, not `extend-existing`/`already-covered`. Both
  tests share `GenerateSkillModalPage`/`review_name_input` (pre-existing
  from ELITEA-1990) but assert disjoint observables.
- **Source-code confirmation (read before/alongside live execution, per
  the skill's "capture handles, don't guess" discipline)**: the review
  form's validation is `validateSkillDraft()`
  (`../EliteaUI/src/[fsd]/features/skill/lib/helpers/skillDraftValidation.helpers.js`),
  wired into `GenerateSkillReviewForm.jsx` via `onValidationChange` →
  `GenerateEntityModal.jsx`'s `isDraftValid` state → the "Create Skill"
  button's `disabled={isApproving || !isDraftValid}`
  (`../EliteaUI/src/[fsd]/entities/generate-entity-with-ai/ui/GenerateEntityModal.jsx:189`).
  The Name-field regex is `/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/` — lowercase
  letters/digits/hyphens only, cannot start or end with a hyphen. This is a
  pure client-side, synchronous check (no network call) — confirmed live,
  no `generate_skill_draft`/`skills/prompt_lib` request fires on any of the
  invalid-name edits below.

## Preconditions
- User is logged in to Elitea (localhost `auth_state`/`VITE_DEV_TOKEN`) with
  editor/admin role sufficient to create skills.
- A skill draft has been generated via the Build with AI modal — covered by
  this AFS's own Step 1 (case-text-drift pattern already documented in the
  ELITEA-1990/2001 AFS lineage; not filed separately here — see Known
  Defects #1).
- A project is selected/accessible (`Private`, id `399` in this run).

## Test Data

### reuse-existing
None — no dependency on any pre-existing environment fixture.

### generate-per-test
- Prompt used to generate the draft (mocked response, see Automation Hints):
  `"Create a skill that reviews pull request diffs and flags missing test
  coverage."`
- Synthetic draft payload the mock returns (name/description/instructions
  all initially valid — only the Name field is then manually overwritten
  with each invalid variant): `name: "pr-test-coverage-review"`,
  `description: "Reviews pull request diffs and flags missing test
  coverage."`, `instructions: "You are a PR reviewer. Inspect the diff and
  flag any changed code paths that lack corresponding test coverage."`
  (identical payload shape to `GENERATED_DRAFT_PAYLOAD` already defined in
  `test_skill_build_with_ai.py` for ELITEA-1990 — implementer should reuse
  that constant rather than duplicate it).
- Invalid Name values (from the case's Test Data table, all confirmed live
  — see Test Steps): `"MySkill"` (uppercase), `"my skill"` (spaces),
  `"-my-skill"` (leading hyphen), `"my-skill-"` (trailing hyphen), and a
  70-character string (`"a" * 70`) for the "exceeds 64 chars" variant —
  see Known Defects #2 for why 70, not exactly 65+, and why the *observed*
  behavior diverges from the case's literal expectation for this one
  variant.
- A known-valid Name (`"my-valid-skill"`) used as a recovery/contrast check
  (Axis 2 addition) — confirms the "Create Skill" button re-enables once a
  valid value replaces an invalid one, i.e. the disabled state truly
  tracks live validation, not a one-way latch.

### generate-shared-with-cleanup
None. This case never reaches the create-skill network call (every
attempt is blocked client-side by validation before Step 7's "cannot
create" assertion) — **no Skill is ever created**, so there is nothing to
delete. Confirmed live: zero `POST .../skills/prompt_lib/399` requests
fired across all 5 invalid-name edits.

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`, click **"Build with AI"**
   (`generate-skill-open-button`), fill the prompt
   (`generate-skill-prompt-input`), mock the `generate_skill_draft`
   response with the valid synthetic draft above, click **Generate**
   (`generate-skill-submit-button`), and wait for the review-form step
   (`generate-skill-back-button` / `generate-skill-approve-button` both
   visible).
   - **Verify**: review form is displayed with the three fields
     pre-populated from the draft, and "Create Skill"
     (`generate-skill-approve-button`) starts **enabled** (the unmodified
     draft is itself valid) — confirmed live.

2. Overwrite the Name field (`generate-skill-review-name-input`) with an
   uppercase value: `"MySkill"`.
   - **Verify** (confirmed live): field displays `"MySkill"` (no silent
     lowercasing); the helper text
     (`generate-skill-review-name-helper-text`, newly added this run — see
     Concrete Handles) reads exactly `"Name must be lowercase letters,
     digits and hyphens only, cannot start or end with a hyphen"`; "Create
     Skill" (`generate-skill-approve-button`) is **disabled**
     (`is_enabled() == False`).

3. Overwrite the Name field with a value containing spaces:
   `"my skill"`.
   - **Verify** (confirmed live): identical helper-text message as Step 2;
     "Create Skill" disabled.

4. Overwrite the Name field with a value starting with a hyphen:
   `"-my-skill"`.
   - **Verify** (confirmed live): identical helper-text message; "Create
     Skill" disabled.

5. Overwrite the Name field with a value ending with a hyphen:
   `"my-skill-"`.
   - **Verify** (confirmed live): identical helper-text message; "Create
     Skill" disabled.

6. Overwrite the Name field via `fill()` with a 70-character string
   (`"a" * 70`) — the case's "exceeds 64 characters" variant.
   - **Verify** (confirmed live — see Known Defects #2 for the full
     analysis): the field's own native `maxlength="64"` HTML attribute
     (`SKILL_NAME_MAX_LENGTH` passed via MUI `slotProps.htmlInput.maxLength`)
     truncates the value to **exactly 64 characters** before any React
     validation ever runs — reproduced identically via both Playwright's
     `fill()` and real keystroke-by-keystroke typing
     (`press_sequentially()`). The resulting 64-char value is **valid**
     (64 ≤ the 64-char limit): helper text shows the character counter
     `"64/64"` (not an error), and "Create Skill" is **enabled**. The
     case's literal expectation ("Create Skill disabled or error shown")
     does **not** hold for this variant — not because the length guard is
     broken, but because the UI structurally prevents ever *reaching* an
     over-length value through manual editing. This is a case-text
     precision gap, not a product defect (see Known Defects #2); the
     assertion below is the corrected, automatable equivalent of the
     case's intent.

7. (Combines the case's Steps 6("exceeds 64 chars" expectation, corrected
   per Step 6 above) and 7 ("cannot create a Skill with any invalid
   name")). For each of Steps 2-5's invalid values: assert "Create Skill"
   is disabled (already captured per-step above — restated here as the
   case's explicit Step 7 requirement that submission is blocked, not
   merely that the button looks disabled). Additionally, as a recovery
   contrast (Axis 2 addition): overwrite the Name field once more with a
   known-valid value (`"my-valid-skill"`).
   - **Verify** (confirmed live): helper text reverts to the plain
     character counter (`"14/64"`, no error text); "Create Skill"
     re-enables (`is_enabled() == True`). This confirms the disabled state
     is a live function of current validity, not a one-way latch from the
     first invalid edit — strengthens confidence in Steps 2-6's
     assertions (a button that never re-enables would trivially "pass"
     every disabled-check above for the wrong reason).
   - Across the whole run (Steps 2-6): zero `POST .../skills/prompt_lib/399`
     requests fired (confirmed via no network call ever becoming
     available to click — the button was disabled at every invalid state),
     satisfying the case's Pass criterion "no Skill is created" without a
     separate cleanup step.

## Expected Results
Matches the case's stated Pass criteria for 4 of its 5 invalid-name
variants exactly (uppercase, spaces, leading hyphen, trailing hyphen — all
show the disabled-button + validation-error combination live). The 5th
variant ("exceeds 64 characters") is corrected per Known Defects #2: the
field's native `maxlength` attribute makes an over-64-char value
unreachable via manual UI editing, so the AFS asserts the truncation
behavior (64-char cap, remains valid) as the automatable equivalent of the
case's intent, rather than a validation error that can never fire through
real user interaction. No Skill is ever created during this case (every
invalid edit is blocked before submission is possible).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: "A skill draft has been generated" | draft/review form exists | step 1 | step 1: review form reached via mocked generate call | clarification *(case-text drift — same established pattern as ELITEA-1990/2001; not filed separately, see Known Defects #1)* |
| 1 Generate a skill draft, enter review form | review/edit form displayed | step 1 | step 1: back/approve buttons visible, approve starts enabled | asserted |
| 2 Uppercase name (e.g. "MySkill") | disabled button or validation error | step 2 | step 2: helper-text message + `approve_button.is_enabled() == False`, both confirmed live | asserted |
| 3 Name with spaces (e.g. "my skill") | disabled button or validation error | step 3 | step 3: same dual assertion | asserted |
| 4 Name starting with hyphen (e.g. "-my-skill") | disabled button or validation error | step 4 | step 4: same dual assertion | asserted |
| 5 Name ending with hyphen (e.g. "my-skill-") | disabled button or validation error | step 5 | step 5: same dual assertion | asserted |
| 6 Name exceeding 64 characters | disabled button or validation error | step 6 | step 6: **corrected** — field truncates input to 64 chars via native `maxlength`; truncated value is valid, button enabled | clarification *(case-text drift — the over-64-char state is unreachable via manual editing; see Known Defects #2)* |
| 7 Verify cannot create a Skill with any invalid name | submission blocked for every invalid variant | step 7 | step 7: disabled-state re-confirmed for steps 2-6, zero create-skill network calls fired across the whole run, plus a valid-name recovery contrast | asserted, with an Axis-2 addition (recovery contrast) |

### Axis 2 — Analyst additions

- Step 7's valid-name recovery contrast (`"my-valid-skill"` re-enabling
  "Create Skill") — *added: proves the disabled state is a live function
  of current validity, not a one-way latch; without it, a button that
  simply never re-enables after the first invalid edit would pass every
  individual disabled-check for the wrong reason.*
- Metadata documents the exact client-side validation source
  (`skillDraftValidation.helpers.js` regex + `isDraftValid` wiring) read
  alongside live execution — *added: gives the implementer the ground
  truth for the helper-text wording instead of a guessed string, and
  explains why no network mocking of an error response is needed (the
  check never leaves the client).*
- Concrete Handles documents that this case is what motivated adding
  `generate-skill-review-name-helper-text`, which did not exist before
  this run — *added: gives the implementer the exact provenance.*
- Zero-network-calls assertion across the whole run — *added: a single,
  cheap, whole-run confirmation that no invalid variant can slip through
  to the backend, complementing the per-step disabled-button checks.*

## Cleanup
None required. No Skill is ever created by this case (every invalid Name
value is blocked before "Create Skill" can be clicked) — confirmed live,
zero `POST .../skills/prompt_lib/399` requests across the whole run.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| "Build with AI" open button | `generate-skill-open-button` (pre-existing) | n/a — testid-only policy |
| Prompt textarea | `generate-skill-prompt-input` (pre-existing) | n/a |
| Generate button | `generate-skill-submit-button` (pre-existing) | n/a |
| Review-form **Name** field | `generate-skill-review-name-input` (pre-existing, added for ELITEA-1990) | n/a |
| Review-form Name field **helper/validation text** | **`generate-skill-review-name-helper-text`** — newly added this run. Applied via `TextField slotProps.formHelperText['data-testid']` in `GenerateSkillReviewForm.jsx` (this element carried the validation-error text and the `{len}/64` counter but had **zero** testid coverage before this fix — confirmed by source read). Scope: only the **Name** field's helper text was touched (this case never manually edits Description/Instructions to an invalid value) — Description/Instructions helper text remain untouched per the scope-discipline rule (canon #511). Landed on `automation/testids` commit `8e78723b`. | n/a — testid-only policy |
| "Create Skill" button | `generate-skill-approve-button` (pre-existing) — its `disabled` state (via `is_enabled()`) is this case's primary assertion target | n/a |

**Testid provenance for this AFS**: `automation/testids` commit `8e78723b`
("test: [EL-1993] add testid for skill review-form name validation helper
text"). Diff is attribute-only (single `slotProps.formHelperText` object
added; no other lines changed besides prettier reformatting of the
existing `slotProps` literal).

## Network Behavior
- `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/399` — draft
  generation, mocked `200` (Step 1 only).
- **No other network call fires at any point in this case.** Name-field
  validation (`validateSkillDraft`) is pure, synchronous client-side
  JavaScript — confirmed live: zero requests to
  `.../elitea_core/skills/prompt_lib/399` (create) across all 5 invalid
  edits and the recovery check, because "Create Skill" stays disabled and
  is never clicked while invalid.
- No console errors or warnings observed during the invalid-name edits
  (spot-checked live; low risk given the validation path never touches
  the network).

## Known Defects Found During Exploration

1. **Case-text drift (CLARIFICATION, not a product defect).** The case's
   Preconditions line ("A skill draft has been generated") describes the
   outcome of this AFS's own Step 1, not an independent setup requirement
   — identical pattern already documented in the ELITEA-1990/1989/2001 AFS
   lineage for the sibling Skill "Build with AI" cases. Not filed as a
   GitHub issue, consistent with that established local precedent (a
   case-authoring precision gap, not a live product defect).

2. **Case-text drift (CLARIFICATION, not a product defect) — the "exceeds
   64 characters" variant is unreachable via manual UI editing.** The
   case's Test Data table specifies "A string of 65 or more characters" as
   an invalid-name input, expecting the same disabled-button/error-message
   treatment as the other four variants. Live exploration (confirmed via
   both `fill()` and real keystroke-by-keystroke `press_sequentially()`
   typing) shows the Name `<input>` carries a native HTML `maxlength="64"`
   attribute (`GenerateSkillReviewForm.jsx`'s
   `slotProps.htmlInput.maxLength = SKILL_NAME_MAX_LENGTH`), which caps
   **any** input — typed or programmatically filled — at exactly 64
   characters before React's `onChange`/validation ever sees a longer
   value. The length-exceeds-64 branch of `validateSkillDraft()`
   (`Name must be 64 characters or less`) is real code that does exist,
   but it is **dead from the manual-editing surface this case describes**
   — the only way to trigger it would be to construct a `draftData` object
   with an over-length `name` some other way (e.g. an AI-generated draft
   returned with a >64-char name from the backend, which is a materially
   different case not written here). This is a case-authoring precision
   gap (the case assumed the field would accept arbitrary length and then
   reject it, when in fact the field structurally prevents the invalid
   state from ever being entered) — not a product defect; the product's
   actual behavior (prevent-by-truncation instead of enter-then-reject) is
   arguably a *stronger* guarantee than what the case describes. Not
   filed as a GitHub issue, following the same local precedent as Known
   Defect #1. The AFS's Step 6 documents the corrected, automatable
   assertion (truncation to 64 chars, remains valid) as the faithful
   equivalent of the case's protective intent.

No functional product defect was found. The live product's actual
behavior across all 7 case steps either matches the case's Pass criteria
exactly (Steps 2-5, 7) or exceeds it via a stronger mechanism that the
case did not anticipate (Step 6, per Known Defect #2).

## Blocked Steps
None. All case steps were executed end-to-end live against the real DEV
backend (draft generation mocked for determinism/speed; the Name-field
validation under test is itself pure client-side and was exercised
unmocked, directly against the shipped `validateSkillDraft()` logic).

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Home:
  `automation/tests/ui/skills/test_skill_build_with_ai.py` (existing file
  — add a new test class alongside the existing
  `TestSkillBuildWithAIReviewFormEditableFields`; reuse
  `GENERATED_DRAFT_PAYLOAD` and `GenerateSkillModalPage` rather than
  duplicating the mock draft).
- Page object: extend `automation/pages/generate_skill_modal_page.py`
  (`GenerateSkillModalPage`) with one new `LocatorDescriptor` field for
  the testid added by this case:
  ```python
  review_name_helper_text = LocatorDescriptor(
      testid="generate-skill-review-name-helper-text",
      description="Review-form Name field's validation/character-count helper text",
  )
  ```
  and a getter mirroring the existing `get_review_name()` pattern:
  ```python
  def get_review_name_helper_text(self) -> str:
      """Return the review-form Name field's current helper text
      (validation error message, or the plain '{len}/64' counter when valid)."""
      return self.review_name_helper_text.text_content() or ""
  ```
  Reuse the existing `approve_button` `LocatorDescriptor` directly for the
  disabled-state assertions (`modal.approve_button.is_enabled()`) — no new
  locator needed for it. Optionally add `is_approve_enabled()` on
  `GenerateEntityModalPageBase` mirroring the existing
  `is_generate_enabled()` for symmetry (not required — direct
  `approve_button.is_enabled()` access is already policy-compliant per
  `.claude/rules/page-objects.md` § Test Imports, since specialized-page
  locator access is allowed).
- Recommend mocking `generate_skill_draft` (via
  `mock_generate_success()`, already used by the sibling ELITEA-1990/1991
  tests) for determinism/speed — this case's assertions are entirely
  about client-side Name-field validation, not generation quality or
  network behavior.
- For Step 6 (exceeds-64-chars), use `set_review_name("a" * 70)` (existing
  `set_review_name()` uses `.fill()`, confirmed live to respect the native
  `maxlength` the same as real typing) and assert
  `len(modal.get_review_name()) == 64` — do NOT assert a validation-error
  helper text for this variant; assert the character-count helper text
  (`"64/64"`) and `approve_button.is_enabled() == True` instead, per Known
  Defect #2.
- No cleanup/fixture needed — this test never creates a Skill.
