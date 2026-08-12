# Test Case: Edit with AI — Skill Happy Path

## Metadata
- **TMS ID**: ELITEA-2611
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (skills-remaining-w4)
- **Status**: ready-for-automation

## Preconditions
- User is logged in (Admin/Editor role — `PERMISSIONS.skills.update`).
- A project is selected (`${PROJECT_ID}` — Private project, id `399` on this env).
- A skill exists that the test can edit. **Recommendation: create a throwaway
  skill per-test** (see § Test Data) rather than reusing a shared fixture skill
  — the flow mutates name/description/instructions, and other suites' skills
  in this project pool (e.g. `test-publish-skill-*`, `el-2599-lc-*`) must not
  be touched.

## Test Data
### generate-per-test (in test setup, deleted in teardown)
- Skill name: `edit-ai-test-skill-${timestamp}` (must satisfy the create-form's
  name regex `/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/`, max 64 chars — see
  `_surface.md` § Build with AI for the validator)
- Description: `Basic description for testing`
- Instructions: `Simple instructions to be enhanced`
- Edit prompt: `Make this skill more detailed and professional. Add better
  structure to the instructions.` — **confirmed live to reliably change the
  Description AND Instructions text** (LLM output is non-deterministic in
  exact wording, but always produces a materially different Description and
  a much longer, markdown-structured Instructions block for this prompt against
  this skill's tiny seed content — safe basis for a "did it change" assertion).
  It typically leaves Name unchanged (the AI has no reason to rename), which is
  why this AFS treats "Name suggested == Name current" as expected, not a bug.

## Test Steps
1. Navigate to `${BASE_URL}/skills/all/{skill_id}` for the pre-created skill.
   - **Verify**: skill detail page loads with Name/Description/Instructions
     fields populated with the seeded values.
2. Verify the "Edit with AI" button is visible in the General section header
   (next to Name/Description), with the sparkle icon.
   - **Verify**: `edit-skill-with-ai-button` visible.
3. Click "Edit with AI".
   - **Verify**: `ai-edit-skill-modal` dialog opens, titled "Edit with AI".
   - **Verify**: `ai-edit-skill-prompt-input` textarea is visible and empty.
4. Type the edit prompt into the prompt textarea.
5. Click "Generate Draft" (`ai-edit-skill-generate-button`; case text says
   "Generate" — live label is **"Generate Draft"**, same control).
   - **Verify**: `ai-edit-skill-loading-indicator` appears with the exact text
     **"Generating skill draft..."** (confirmed live, matches case's expected
     text modulo the ellipsis character).
6. Wait for generation to finish (`ai-edit-skill-loading-indicator` gone /
   wizard content visible — no fixed sleep; poll on the loading indicator or
   on the `generate_skill_draft` response per § Network Behavior).
   - **Verify**: wizard's first step is **"1. General"** (testid needed —
     see § Concrete Handles).
   - **Verify**: General step shows Name and Description, each with a CURRENT
     (read-only) column and a SUGGESTED (editable) column.
   - **Verify**: each field's SUGGESTED column has an "Apply changes" checkbox,
     **checked by default** (confirmed live: both Name and Description
     checkboxes are `checked` immediately after generation).
   - **Verify**: SUGGESTED Description text differs from CURRENT Description
     text (the diff-highlighting observable, asserted at the data level — see
     § Automation Hints for why this AFS prefers a text-differs assertion over
     a CSS-highlight assertion).
7. Click "Next" (testid needed) to advance to the Instructions step.
   - **Verify**: step indicator now reads **"2. Instructions"**.
   - **Verify**: Instructions step shows CURRENT (read-only, original
     instructions) vs SUGGESTED (editable, AI-generated instructions) with an
     "Apply changes" checkbox, checked by default.
   - **Verify**: SUGGESTED instructions text differs from CURRENT.
8. Click "Previous" (testid needed) to return to the General step, then
   **uncheck** the Description "Apply changes" checkbox (case step 16's intent
   — "keep original description"). Leave Name and Instructions checked.
   - **Verify**: Description checkbox is now unchecked; Name checkbox remains
     checked (per-field state persists across step navigation — confirmed
     live).
9. Click "Next" twice (General → Instructions → Summary).
   - **Verify**: step indicator reads **"3. Summary"**.
   - **Verify**: the Summary step's **Description** field shows the ORIGINAL
     value (`Basic description for testing`) because it was unchecked.
   - **Verify**: the Summary step's **Instructions** field shows the
     AI-SUGGESTED value (because it stayed checked).
   - **Verify**: the Summary step's **Name** field shows the AI-suggested name
     (identical to current in this run, since the AI didn't rename it) because
     it stayed checked.
   - (Note on case-text nuance: the case describes the Summary step as
     "listing which changes will be applied." The live implementation instead
     renders ONE merged, directly-editable form per field — the per-field
     value is either the current or the suggested one depending on that
     field's checkbox state from the prior steps, with no separate itemized
     change list. This is a wording-only mismatch, not a behavioral defect:
     the underlying guarantee the case cares about — "only checked
     suggestions carry through" — holds exactly. Not filed as a
     clarification; noted here so the implementer doesn't go looking for a
     literal bullet-point change list.)
10. Click "Save" (testid needed; NOT "Save as Version" — that path creates a
    new skill version and is out of scope for this happy-path case).
    - **Verify**: a `toast-message` toast reading **"Skill saved"** appears.
    - **Verify**: `PUT /api/v2/elitea_core/skill/prompt_lib/{projectId}/{skillId}`
      fires and returns `200`.
    - **Verify**: the modal closes.
    - **Verify**: on the skill detail page, Description still reads
      `Basic description for testing` (unchecked → NOT applied) and
      Instructions now reads the AI-generated content (checked → applied).
11. Reload the skill detail page (`${BASE_URL}/skills/all/{skill_id}`).
    - **Verify**: Description is still `Basic description for testing` and
      Instructions is still the AI-generated content — i.e. the partial apply
      persisted server-side, not just in local Formik state.

## Expected Results
- "Edit with AI" wizard completes end-to-end: prompt → loading → 3-step
  wizard (General → Instructions → Summary) → save.
- Only the CHECKED suggestion (Instructions) is applied; the UNCHECKED one
  (Description) keeps its original value; the untouched one (Name, which the
  AI didn't change) is a no-op either way.
- Changes persist across a full page reload.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to skill detail/edit page | page loads | step 1 | `step 1` | asserted |
| 2 "Edit with AI" CTA visible | button with magic-wand icon present | step 2 | `step 2`: `edit-skill-with-ai-button` visible | asserted |
| 3 Click "Edit with AI" | modal/wizard opens | step 3 | `step 3`: `ai-edit-skill-modal` visible | asserted |
| 4 Prompt input field displayed | textarea visible | step 3 | `step 3`: `ai-edit-skill-prompt-input` | asserted |
| 5 Enter edit prompt | text entered | step 4 | `step 4` | asserted |
| 6 Click "Generate"/equivalent | generation starts | step 5 | `step 5`: `ai-edit-skill-generate-button` click | asserted *(label is "Generate Draft" live — case said "or equivalent")* |
| 7 Loading state "Generating skill draft…" | indicator+message shown | step 5 | `step 5`: `ai-edit-skill-loading-indicator` text | asserted |
| 8 Wait for generation to complete | suggestions generated | step 6 | `step 6` | asserted |
| 9 Wizard first step General (Name, Description) | Step 1 displayed | step 6 | `step 6`: step-indicator text + Name/Description fields | asserted |
| 10 "Current" value read-only | original shown non-editable | step 6 | `step 6`: `ai-edit-skill-general-description-current` text == SEED_DESCRIPTION + no `contenteditable` attribute | asserted |
| 11 "Suggested" value editable | AI suggestion shown editable | step 6 | `step 6`: `ai-edit-skill-general-description-suggested` `contenteditable="true"` | asserted |
| 12 Diff highlighting shows changes | visual diff current vs suggested | step 6 | `step 6`: suggested text differs from current text | asserted *(data-level, not CSS — see Automation Hints)* |
| 13 Checkboxes present, default checked | checked by default | step 6 | `step 6`: Name + Description checkboxes checked | asserted |
| 14 Navigate to Instructions step | Step 2 loads | step 7 | `step 7`: Next click + step-indicator text | asserted |
| 15 Current vs Suggested for Instructions | both shown, diff highlighted | step 7 | `step 7` | asserted |
| 16 Uncheck one suggestion (keep original description) | checkbox unchecked | step 8 | `step 8`: Description checkbox unchecked | asserted |
| 17 Navigate to Summary step | summary displayed | step 9 | `step 9`: step-indicator text | asserted |
| 18 Summary shows which changes will be applied | only checked items listed | step 9 | `step 9`: Description=original, Instructions=suggested | asserted *(implemented as a merged per-field form, not an itemized list — see step-9 note; same guarantee)* |
| 19 Click "Apply"/"Finalize" | changes applied | step 10 | `step 10`: `Save` click + `PUT .../skill/...` 200 | asserted *(button is "Save" live)* |
| 20 Only CHECKED suggestions applied | unchecked fields retain original | step 10 | `step 10`: post-save field read | asserted |
| 21 Skill saved with applied changes | skill shows updated values | step 10 | `step 10`: toast + field read | asserted |
| 22 Reopen skill, verify persisted changes | changes saved correctly | step 11 | `step 11`: reload + field read | asserted |

**Axis 2 — Analyst additions:**
- `step 5` asserts the `generate_skill_draft` request body carries `skill_id`
  and `version_id` — *added: this is the mechanism that distinguishes
  Edit-with-AI (existing skill) from Build-with-AI/skill-creation (no
  `skill_id`), confirmed live via network capture; worth guarding so a future
  regression doesn't silently collapse the two flows onto the same payload
  shape.*
- `step 10` asserts the exact endpoint/method (`PUT
  .../skill/prompt_lib/{projectId}/{skillId}`) — *added: traced from
  `useSaveSkill.hooks.js` → `skillUpdate` mutation in `skillsApi.js:187-200`;
  confirms Save (not Save-as-Version) mutates the current version in place.*
- No new console errors attributable to this flow — *added: standard
  side-channel check; the only console errors observed during the whole run
  were a pre-existing benign dev-env WebSocket `ERR_NAME_NOT_RESOLVED` (dev
  backend Socket.IO trying to reach `wss://dev.elitea.ai` from localhost —
  unrelated, seen on every localhost session) and a stray 404 for an unrelated
  skill/version id combination left over from page-transition timing — neither
  reproduces if isolated to a single skill's Edit-with-AI flow start-to-finish.*

## Cleanup
1. Delete the generated skill via the UI delete flow (Skill overflow menu →
   "Delete skill" → type name to confirm) or `SkillAPI.delete_skill(skill_id)`
   in a `try/finally` (cookie-auth client, `automation/api/client.py:1478`) —
   **do not** use a raw `fetch()` DELETE from page JS context (CORS-fails on
   this backend's Keycloak forward-auth path, per `_surface.md` § Build with
   AI cleanup note).

## Concrete Handles (discovered during exploration)

**PROVENANCE:** all pre-existing testids below verified live 2026-08-12 against
`origin/main` and `origin/automation/testids` (post `git fetch origin`) — all
`YES`/`YES`, i.e. already on `main`, nothing pending human promotion.

| Element | Locator | PROVENANCE |
|---|---|---|
| "Edit with AI" button (skill detail, General section) | `LocatorDescriptor(testid="edit-skill-with-ai-button")` | on-main ✓ |
| Edit-with-AI modal | `LocatorDescriptor(testid="ai-edit-skill-modal")` | on-main ✓ |
| Modal close (X) button | `LocatorDescriptor(testid="ai-edit-skill-close-button")` | on-main ✓ |
| Prompt textarea | `LocatorDescriptor(testid="ai-edit-skill-prompt-input")` | on-main ✓ |
| Generate error alert | `LocatorDescriptor(testid="ai-edit-skill-error-alert")` | on-main ✓ |
| Loading indicator ("Generating skill draft...") | `LocatorDescriptor(testid="ai-edit-skill-loading-indicator")` | on-main ✓ |
| "Generate Draft" button | `LocatorDescriptor(testid="ai-edit-skill-generate-button")` | on-main ✓ |
| "Cancel" button (prompt phase) | `LocatorDescriptor(testid="ai-edit-skill-cancel-button")` | on-main ✓ |
| "Save as Version" name dialog — name input | `LocatorDescriptor(testid="ai-edit-skill-version-dialog-name-input")` | on-main ✓ *(not exercised by this happy-path case — Save, not Save as Version)* |
| "Save as Version" dialog save/cancel/close | `ai-edit-skill-version-dialog-save-button` / `-cancel-button` / `-close-button` | on-main ✓ *(same — out of scope here)* |
| Skill overflow menu → Delete skill (cleanup) | `LocatorDescriptor(testid="skill-delete-menu-item")` | on-main ✓ |
| Skill create/edit form: name/description/instructions inputs | `skill-name-input-field` / `skill-description-input-field` / `skill-instructions-editor-content` | on-main ✓ |
| Skill save button (form-level, not wizard) | `LocatorDescriptor(testid="skill-save-button")` | on-main ✓ |

**Genuinely no testid — `testid needed:` (component + wiring guidance, so the
implementer doesn't have to re-trace this).** The wizard PHASE of
`EditEntityModal` (shared by Skill/Agent/Project-Context Edit-with-AI) and its
step components (`GeneralStep`/`InstructionsStep`/`SummaryStep`,
`EditEntityStepIndicator`) carry **zero** `data-testid` wiring — confirmed by
reading every file under
`../EliteaUI/src/[fsd]/entities/edit-entity-with-ai/ui/` and
`../EliteaUI/src/[fsd]/features/skill/ui/ai-edit-skill-modal/`. Only the
PROMPT-phase controls (table above) are wired. All new testids below follow
the existing `xxxTestId` prop-threading pattern already used for the prompt
phase (`modalTestId`, `promptInputTestId`, …) — same shared-component
discipline, just extended to the wizard phase:

| Element | Component (file) | New prop to add | testid needed |
|---|---|---|---|
| Step indicator ("1. General" / "2. Instructions" / "3. Summary") | `entities/edit-entity-with-ai/ui/EditEntityStepIndicator.jsx` (shared) | `stepIndicatorTestId` (threaded via `EditEntityModal` → `EditEntityStepIndicator`) | `ai-edit-skill-step-indicator` |
| "Refine Prompt" button | `entities/edit-entity-with-ai/ui/EditEntityModal.jsx` `renderWizardFooter()` (shared) | `refinePromptButtonTestId` | `ai-edit-skill-wizard-refine-prompt-button` |
| "Previous" button | same, `renderWizardFooter()` | `previousButtonTestId` | `ai-edit-skill-wizard-previous-button` |
| "Next" button | same, `renderWizardFooter()` | `nextButtonTestId` | `ai-edit-skill-wizard-next-button` |
| "Save" button (wizard, last step) | same, `renderWizardFooter()` | `wizardSaveButtonTestId` (distinct from the unrelated prompt-phase — there is none there) | `ai-edit-skill-wizard-save-button` |
| "Save as Version" button (wizard, last step) | same, `renderWizardFooter()` | `saveAsVersionButtonTestId` | `ai-edit-skill-wizard-save-as-version-button` |
| Name "Apply changes" checkbox (General step) | `entities/edit-entity-with-ai/ui/GeneralStep.jsx` (shared) | `nameCheckboxTestId` | `ai-edit-skill-general-name-checkbox` |
| Description "Apply changes" checkbox (General step) | same | `descriptionCheckboxTestId` | `ai-edit-skill-general-description-checkbox` |
| Instructions "Apply changes" checkbox | `entities/edit-entity-with-ai/ui/InstructionsStep.jsx` (shared) | `instructionsCheckboxTestId` | `ai-edit-skill-instructions-checkbox` |
| Summary step — Name input | `features/skill/ui/ai-edit-skill-modal/steps/SummaryStep.jsx` (skill-specific) | `nameInputTestId` | `ai-edit-skill-summary-name-input` |
| Summary step — Description input | same | `descriptionInputTestId` | `ai-edit-skill-summary-description-input` |
| Summary step — Instructions input | same | `instructionsInputTestId` | `ai-edit-skill-summary-instructions-input` |
| General step — Description CURRENT column (read-only) | `entities/edit-entity-with-ai/ui/GeneralStep.jsx` (shared, via `TextDiffHighlight.jsx`'s new `testId` prop) | `descriptionCurrentTestId` | `ai-edit-skill-general-description-current` |
| General step — Description SUGGESTED column (editable) | same | `descriptionSuggestedTestId` | `ai-edit-skill-general-description-suggested` |

**Added during ELITEA-2611 fix round 1 (implementer):** the two rows above were
missing from the original Concrete Handles table even though Coverage Map rows
10/11 required them — `TextDiffHighlight.jsx` now accepts a generic `testId`
prop (threaded through `GeneralStep.jsx` → `AIEditSkillModal.jsx`), landed on
`automation/testids` at `EliteaAI/EliteaUI@3e1e5c73`. Only the Description
field's Current/Suggested columns are wired (not Name's) — the test only
asserts on Description, so per canon #511 no orphan testid is introduced for
Name's pair.

**Minimum viable testid set for THIS case** (if the implementer wants to trim
scope): step indicator + the 3 checkboxes + the 4 wizard-footer navigation/save
buttons are load-bearing (steps 6/7/8/9/10 assert on them directly). The
Summary-step input testids are used only for the step-9 read — reading via
`page.locator(parent_testid).locator('textarea, input')` scoped under a real
testid parent is NOT compliant here (this is first-party app code, not a #579
third-party exception), so these three do need real testids too, not a scoped
raw handle.

## Network Behavior
- `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/{projectId}` —
  fires on "Generate Draft" click, `200 OK`. Body: `{user_description,
  skill_id, version_id}` (confirmed live via `browser_network_requests`) — the
  presence of `skill_id`/`version_id` is what makes this the EDIT flow, as
  opposed to the skill-creation "Build with AI" flow's `generate_skill_draft`
  call, which omits both (see `_surface.md` § Build with AI).
- `PUT /api/v2/elitea_core/skill/prompt_lib/{projectId}/{skillId}` — fires on
  "Save" (wizard), `200 OK` per `skillsApi.js:187-200` (`skillUpdate`
  mutation). Body: `{name, description, version: {id, instructions, tags}}`.
  Wait on this response (or the `toast-message` "Skill saved" text), never a
  fixed sleep.
- "Save as Version" (not exercised by this case) instead calls
  `PUT /api/v2/elitea_core/skill/prompt_lib/{projectId}/{skillId}` (name/
  description only, when applicable) followed by the existing
  create-new-version flow (`useSaveSkillVersion`) — out of scope here, noted
  for the sibling case that would cover it.

## Known Defects Found During Exploration
None found. The flow is functionally correct end-to-end: partial-apply
(checked vs unchecked fields) merges correctly at the Summary step and
persists correctly through Save + reload.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only locators (`.agents/testing.md`).
- New page object: `automation/pages/ai_edit_skill_modal_page.py` (none exists
  yet — this is the first case to touch Edit-with-AI for skills). Model on
  `automation/pages/generate_skill_modal_page.py`'s
  `GenerateSkillModalPage`/`GenerateEntityModalPageBase` split, since
  `EditEntityModal` is the analogous shared shell for the edit flow (mirrors
  `GenerateEntityModalPageBase` for creation) — but note the wizard-phase
  testids don't exist yet (see above), so this page object is *blocked on*
  `add-data-testid` landing them first, unlike the create-flow's page object
  which had full coverage from ELITEA-1990's era.
- **Diff-highlighting assertion — deliberately data-level, not CSS.** The case
  wants "diff highlighting shows changes." `TextDiffHighlight.jsx` renders
  added/removed word segments as inline-styled `<span>`s with no testid
  (first-party shared component, not a #579 exception) — asserting the exact
  background-color would need yet another new testid on every diff segment.
  This AFS instead asserts the OBSERVABLE OUTCOME (suggested text differs from
  current text) rather than the CSS mechanism, which is both stable and
  faithful to what a user actually verifies. If a future case wants pixel-level
  diff-color verification, it should add generic (non-feature-scoped, shared
  component) testids to `TextDiffHighlight.jsx`'s added/removed spans — e.g.
  `diff-highlight-added-segment` / `diff-highlight-removed-segment` — and is a
  separate scope decision, not bundled into this AFS's minimum testid set.
- **Prompt is LLM-driven — assert content changed, not exact wording.** The
  edit prompt's LLM output is inherently non-deterministic in phrasing. Assert
  `suggested != current` (or `suggested != ''`), never a fixed expected string
  for the AI-generated Description/Instructions text.
- Wait strategy: `wait_for_response` matching `generate_skill_draft` before
  asserting the wizard appears (loading→wizard transition, ~5–20s observed
  live for a real LLM call — no fixed sleep); `wait_for_response` matching the
  `PUT .../skill/...` before asserting the "Skill saved" toast / reload check.
- Skill-creation reuse: `automation/pages/skill_form_page.py`'s
  `set_name`/`set_description`/`fill_instructions`/`save_and_wait_for_navigation`
  cover the § Preconditions throwaway-skill setup — no new page object needed
  for that part.
