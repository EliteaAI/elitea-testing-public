# Test Case: Build with AI (Skills) — "Back to prompt" returns to input step without losing the prompt

> ⚠️ **UNDER REVIEW — 2026-08-14 fidelity audit. Do NOT reuse this AFS as a pattern.**
>
> This spec directs the implementer to **substitute the system under test** (mocking
> the generate-draft response) for a TMS case whose text never asks for simulation.
> Classification: **TRANSIT** — the mock only reaches the review step; the back-to-prompt observable is real (mirror of agents ELITEA-1919).
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
- **TMS ID**: ELITEA-1996
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/skills/build_with_ai/ELITEA-1996_build-with-ai-back-to-prompt-returns-to-input-step-without-losing-the-prompt.md`
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project `Private` / id `399`
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via `VITE_DEV_TOKEN`; admin-equivalent role, per `.agents/profile.md` § Roles & sample users)
- **Analyst**: qa-engineer (Sage), analyst slot, batch `skills-remaining-w5`
- **Status**: ready-for-automation
- **Tracking issue**: EliteaAI/elitea-testing-public#1399 (batch tracking issue — no per-case board card)
- **Case-gate note**: source case frontmatter carries `status: draft` / `execution_type: manual`, tag `automated:UI:regression` — consistent with the batch's other Build-with-AI (skills) cases; no exclusion per `.agents/testing.md` § TMS case-gate, so this run proceeded normally.
- **Reuse check (before executing)**: `grep -n "back_button" automation/tests/ui/skills/*.py` returns 0 hits — `back_button` is a pre-existing `LocatorDescriptor` on `GenerateSkillModalPage` (`generate-skill-back-button`, `generate_skill_modal_page.py:75`) but is **never referenced anywhere in the skills test suite** (`test_skill_build_with_ai.py`'s existing classes cover generation failure/retry, review-field edits, name validation, modal-elements — none exercise Back). This is the skills-entity sibling of ELITEA-1919 (`test-specs/agents/l2_build-with-ai-back-to-prompt-returns-to-input-step-preserves-text_ELITEA-1919.md`), which covers the identical control on the Agent entity. Confirms this case is genuinely unexercised on the Skills entity — `ready-for-automation`, not `already-covered`/`extend-existing` (the agents AFS is a different entity's spec, not a valid `extend-existing`/`already-covered` target for a skills case per the merged-target rule's behavioural-equivalence bar — same control, different entity, different page object, different test file).

## Triangulation — what "Back to prompt" actually does (source-level confirmation)

Read `GenerateEntityModal.jsx` (`../EliteaUI/src/[fsd]/entities/generate-entity-with-ai/ui/GenerateEntityModal.jsx`), the shared shell BOTH the Agent and Skill Build-with-AI modals render through (entity-agnostic — takes `entityLabel`/`*TestId` props, no skill-vs-agent branching in the component body itself):

```js
const [step, setStep] = useState(STEPS.INPUT);
const [description, setDescription] = useState('');   // the prompt textarea's value
const [draftData, setDraftData] = useState(null);

const handleClose = useCallback(() => {
  ...
  setStep(STEPS.INPUT);
  setDescription('');      // <-- Close/Cancel DOES clear the prompt text
  setDraftData(null);
  ...
}, [onClose, resetGenerate]);

const handleBack = useCallback(() => {
  setStep(STEPS.INPUT);
  setDraftData(null);      // <-- discards the generated draft
  resetGenerate();
  // note: description is NOT touched — the prompt text state survives
}, [resetGenerate]);
```

`handleBack()` is wired to `back_button` via `onClick={handleBack}` in `renderActions()` (line 179), passed down as `backButtonTestId` → renders as `data-testid={backButtonTestId}` — `generate-skill-back-button` for the Skill entity, `generate-agent-back-button` for the Agent entity, same component. `handleBack()` resets `step` to `STEPS.INPUT` and clears `draftData` (so `renderContent()`'s `step === STEPS.REVIEW && draftData` branch stops matching), but never calls `setDescription('')` — the same deliberate asymmetry vs `handleClose()` that ELITEA-1919 documented for the Agent entity. Since this is the exact same component instance type (not a per-entity fork), the mechanism is proven identical by source inspection; the live run below confirms it holds for the Skill entity's actual DOM/testids too.

## Preconditions
- `${TEST_USER}` is authenticated via the `auth_state` fixture (localhost `VITE_DEV_TOKEN` bypass — no Keycloak login form on localhost).
- The New Skill creation page (`${BASE_URL}/skills/create`) is reachable, with the "General" accordion section expanded by default.
- **A draft has been generated and the review/edit form is displayed** — this case's own precondition. Reached live this run via a real (unmocked) `generate_skill_draft` call — no `mock_generate_success()` needed; the real endpoint responded well within `GenerateEntityModalPageBase`'s `wait_for_review_form()` default timeout. Mocking (`GenerateSkillModalPage.mock_generate_success()`) remains available if the implementer prefers a deterministic draft payload — this case's Pass criteria don't depend on the draft's specific content, only on what "Back to prompt" does to the modal's step/prompt state afterward.

## Test Data
### reuse-existing (no fixture creation/teardown needed)
- `${TEST_USER_EMAIL}` / `${TEST_USER_PASSWORD}` via `auth_state`.
- `${ELITEA_PROJECT_ID}` (whichever project is active — the flow is project-agnostic).
- Prompt text: any non-empty natural-language string, confirmed live with:
  `"A skill that translates English feedback into Spanish for ELITEA-1996 back-to-prompt verification."`
  A dedicated `BACK_TO_PROMPT_PROMPT_TEXT` constant is recommended (mirrors this file's existing prompt-text constants, e.g. those used by the generation-failure/retry and name-validation classes) since this case's own assertion (Step 4) depends on reading the EXACT text back.
- If the implementer mocks the draft instead of using the real endpoint, a small dedicated `BACK_TO_PROMPT_DRAFT_PAYLOAD` (shape: `{name, description, versions: [{name: "base", instructions}]}` per the skill create payload documented in `test-specs/skills/_surface.md`) is sufficient — this case never asserts on the draft's specific field values, only on its absence after Back is clicked.

No new test data is created or persisted in the product by this case's steps — a draft IS generated (precondition), but it is discarded when "Back to prompt" is clicked and no `Create Skill` call ever fires. See Cleanup.

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`, open the Build with AI modal (`generate-skill-open-button`), enter a natural-language description into the prompt textarea (`generate-skill-prompt-input`), and click "Generate Draft" (`generate-skill-submit-button`) to reach the review step.
   - **Verify**: the review form is displayed with the generated draft's data — confirmed live via a `browser_snapshot` immediately after the click showing populated Name/Description/Instructions fields (this run generated `name: "english-to-spanish-feedback"`, real unmocked AI output from `POST generate_skill_draft/prompt_lib/399` → `200`). Note: the Skill review form has only these 3 fields — no Welcome Message/conversation starters, unlike the Agent review form (documented difference, `test-specs/skills/_surface.md` § Build with AI).
2. Click "Back to prompt" (`generate-skill-back-button`).
   - **Verify**: the click is accepted, no confirmation/"discard changes?" interstitial appears — confirmed live.
3. Verify the modal returns to the prompt input step.
   - **Verify**: confirmed live via `browser_snapshot` immediately after the click — the dialog now shows only the prompt textarea (`generate-skill-prompt-input`) + `Cancel`/`Generate Draft` (`generate-skill-submit-button`) action buttons; `generate-skill-back-button` and `generate-skill-approve-button` are no longer present in the DOM (the review-step action row is gone entirely, not merely hidden — `renderContent()` re-renders the INPUT branch).
4. Verify the previously entered natural-language description is still present in the input field.
   - **Verify**: confirmed live — the prompt textarea's value read immediately after the Back click is
     `"A skill that translates English feedback into Spanish for ELITEA-1996 back-to-prompt verification."`,
     an **exact, character-for-character match** to what was typed in Step 1 (no truncation, no whitespace drift, no residual draft text appended).
5. Verify no draft data leaks into the prompt step UI.
   - **Verify**: confirmed live — none of the review-form's field testids (`generate-skill-review-name-input`, `generate-skill-review-description-input`, `generate-skill-review-instructions-input`) are present in the DOM after Back; the visible surface is exactly the input step's own elements (prompt textarea + Cancel/Generate Draft), matching the identical DOM shape the modal has on its very first open (Step 1, before ever generating).

## Expected Results
Clicking "Back to prompt" (`generate-skill-back-button`) on the GenerateSkillModal's review step returns the modal to the INPUT step (review-step action buttons and all review-form fields removed from the DOM, not merely hidden), preserves the exact previously-typed prompt text in `generate-skill-prompt-input`, and shows only the input step's own elements — no review-form field, no generated-draft content, no confirmation interstitial. No new network request fires from the Back click itself (pure client-side state transition — `handleBack()` never calls the generate-draft or create-skill endpoints; confirmed via `browser_network_requests` filtered to `generate_skill_draft`/`skills/prompt_lib`: still exactly 1 `generate_skill_draft` call total, from Step 1's own Generate, both before AND after clicking Back — 0 `skills/prompt_lib` CREATE (`POST`) calls at any point). No console errors: `browser_console_messages` level=error → 0 results, both before and after the Back click.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Generate a skill draft and enter the review/edit form | The review/edit form is displayed with generated values | AFS Step 1 | `modal.wait_for_review_form()` (existing helper); `browser_snapshot` confirms populated Name/Description/Instructions fields | ready-for-automation (new test) |
| 2 Click "Back to prompt" | The modal returns to the prompt input step | AFS Step 2 | `modal.back_button.click()` — first assertion-backed `.click()` of this control anywhere in the skills suite (previously never referenced) | ready-for-automation (new test) |
| 3 Verify the modal returns to the prompt input state | The prompt input field and Generate button are visible | AFS Step 3 | `modal.wait_for_input_step()` (existing helper — waits for `generate_button` visible) + explicit absence check on `back_button`/`approve_button` | ready-for-automation (new test) |
| 4 Verify the previously entered natural-language description is still present in the input field | The original prompt text is preserved in the input field | AFS Step 4 | `modal.get_prompt_value() == BACK_TO_PROMPT_PROMPT_TEXT` (existing helper — exact-string equality) | ready-for-automation (new test) |
| 5 Verify no partial draft data leaks into the prompt step UI | No generated Name, Description, or Instructions data is shown in the prompt step | AFS Step 5 | Absence assertions on `review_name_input`/`review_description_input`/`review_instructions_input` `.count() == 0` — reference by absence per canon ruling #511 extension | ready-for-automation (new test) |

### Axis 2 — Analyst additions

- Confirmed **zero new network requests** fire from the Back click itself — `browser_network_requests` filtered to `generate_skill_draft`/`skills/prompt_lib` showed the same 1-vs-0 split before and after clicking Back — *added: guards against a future regression where "Back to prompt" accidentally re-triggers a generate or create call (it is meant to be a pure client-side state reset per `handleBack()`'s source, entity-agnostic).*
- Confirmed **zero console errors** at any point in the flow (`browser_console_messages` level=error → 0 results before AND after the Back click) — *added: side-channel check, standard practice per this skill's methodology. Note this run did not surface the `disableUnderline` warning some Agent Build-with-AI AFS files document as baseline noise — that is a `warning`-level message (not checked here since only `error` level is asserted), consistent with those AFS's own framing of it as non-blocking noise, not evidence it's absent from this flow.*
- **Source-level confirmation of the preservation mechanism** (`handleBack()` resets `step`/`draftData` but never calls `setDescription('')`, unlike the sibling `handleClose()`) is entity-agnostic — the SAME `GenerateEntityModal.jsx` component instance renders both the Agent and Skill modals via `entityLabel`/`*TestId` props, with no skill-vs-agent branching in `handleBack()` itself — *added: documents that this case and its Agent sibling (ELITEA-1919) share one mechanism, so a future regression here would also regress ELITEA-1919's test and vice versa; a maintainer "fixing" one should check both.*
- Confirmed the review-step action row (`back_button`/`approve_button`) is fully removed from the DOM after Back, not merely hidden/inert — *added: distinguishes a real state transition from a CSS-only toggle that could leave stale review-form data reachable via direct DOM query even if visually hidden.*
- Confirmed all testids needed already exist as `LocatorDescriptor` fields on `GenerateSkillModalPage` — no `add-data-testid` work needed for this case.

## Cleanup
No product state persists from this case's own steps — the generated draft is discarded when "Back to prompt" is clicked (`draftData` reset to `null`), and the create-skill call never fires. No `SkillAPI.delete_skill(...)` teardown is needed. (If the implementer chooses to mock the draft via `mock_generate_success()` instead of using the real generate endpoint, no cleanup changes — mocking is purely client-side route interception, nothing persists either way.)

## Concrete Handles (discovered during exploration — all pre-existing)

| Element | Recommended Locator | Provenance |
|---|---|---|
| "Build with AI" open button | `generate-skill-open-button` (`GenerateSkillModalPage.open_button`) | on-main ✓ |
| Modal container | `generate-skill-modal` (`GenerateSkillModalPage.modal`) | on-main ✓ |
| Prompt textarea | `generate-skill-prompt-input` (`GenerateSkillModalPage.prompt_input`) — read via `modal.get_prompt_value()` (existing helper) | on-main ✓ |
| Generate Draft button (also the input-step re-appearance marker) | `generate-skill-submit-button` (`GenerateSkillModalPage.generate_button`) — `modal.wait_for_input_step()` waits on this | on-main ✓ |
| **"Back to prompt" button — this case's core control** | `generate-skill-back-button` (`GenerateSkillModalPage.back_button`) — pre-existing field; never referenced anywhere in the skills test suite before this case | on-main ✓ |
| "Create Skill" / approve button (NOT this case — disambiguation only) | `generate-skill-approve-button` (`GenerateSkillModalPage.approve_button`) — used only to assert its absence after Back, per AFS Step 3 | on-main ✓ |
| Review-form Name field (used for absence assertion only) | `generate-skill-review-name-input` (`GenerateSkillModalPage.review_name_input`) — `count() == 0` after Back proves no draft-data leak | on-main ✓ |
| Review-form Description field (used for absence assertion only) | `generate-skill-review-description-input` (`GenerateSkillModalPage.review_description_input`) — `count() == 0` after Back | on-main ✓ |
| Review-form Instructions field (used for absence assertion only) | `generate-skill-review-instructions-input` (`GenerateSkillModalPage.review_instructions_input`) — `count() == 0` after Back | on-main ✓ |
| Skill CREATE route (negative network assertion only) | `**/elitea_core/skills/prompt_lib/**` (glob string, used ad hoc elsewhere e.g. `skill_form_page.py:784`; no dedicated constant on `GenerateSkillModalPage` — implementer may add one, e.g. `CREATE_SKILL_ROUTE`, mirroring the Agent page object's `CREATE_APPLICATION_ROUTE`) | on-main ✓ — used only for a **negative** (no-call) network assertion |
| Generate-draft route | `**/elitea_core/generate_skill_draft/**` (`GenerateSkillModalPage.GENERATE_DRAFT_ROUTE`) | on-main ✓ — expected to fire exactly ONCE total (Step 1's own Generate), unchanged by the Back click |

No new testids required. No new page-object locators required. Every handle needed already exists in `GenerateSkillModalPage`. (Optional implementer nicety: add a `CREATE_SKILL_ROUTE` class constant on `GenerateSkillModalPage` mirroring `GenerateAgentModalPage.CREATE_APPLICATION_ROUTE`, since the create-route glob is currently only inlined ad hoc in other files — not required for this case to pass, just consistency with the Agent page object's shape.)

## Network Behavior
Confirmed live: across the entire open → type-prompt → generate → back sequence, exactly **one** request matched `**/elitea_core/generate_skill_draft/**` (`POST`, `200 OK` — Step 1's own Generate, reaching the review step this case's precondition needs), and **zero** requests matched `**/elitea_core/skills/prompt_lib/**` (`POST`, the CREATE route) at any point — filtering `browser_network_requests` to both route substrings before and immediately after clicking "Back to prompt" showed the identical 1-vs-0 split, confirming the Back click itself is a pure client-side state transition with no network side effect.

## Known Defects Found During Exploration
None found. "Back to prompt" behaves exactly per the case's Pass criteria: returns to the input step, preserves the prompt text verbatim, and shows no leaked draft data — all confirmed live and further confirmed at the source level (`handleBack()` in `GenerateEntityModal.jsx`, shared with the Agent entity's identical, already-verified ELITEA-1919 behavior).

## Blocked Steps
None. All case elements were executed live this run against the real local system (`http://localhost:5173`), including a real (unmocked) `generate_skill_draft` call that produced a genuine AI-generated draft (`name: "english-to-spanish-feedback"`).

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Add a new, standalone test class to `automation/tests/ui/skills/test_skill_build_with_ai.py` — e.g. `TestSkillBuildWithAIBackToPromptFromReviewStep` (mirrors the naming shape of `TestAgentBuildWithAIBackToPromptFromReviewStep` recommended for ELITEA-1919, and this file's existing `TestSkillBuildWithAI*` classes).
- **Reaching the review step**: either (a) a real, unmocked `generate_button.click()` + `wait_for_review_form()` (confirmed reliable this run, real AI response), or (b) `mock_generate_success(draft)` + `expect_generate_response()` (the pattern this file's `TestSkillBuildWithAIGenerationFailureRetry`/review-field-editing classes use) for a deterministic, faster draft. Either is sound — this case's Pass criteria don't depend on the draft's specific content.
- **Do not target `close_button` or `approve_button`** — this case's own control is `back_button` exclusively.
- **Absence assertions after Back** (`back_button`, `approve_button`, `review_name_input`, `review_description_input`, `review_instructions_input` all `count() == 0`) are first-class per `.agents/testing.md`'s canon ruling #511 extension — they count as "referencing" the testid, no different from a positive assertion.
- Suggested flow (illustrative, not prescriptive):
  ```python
  with allure.step("Step 1 — Generate a draft and reach the review form"):
      skill_form_page.navigate_to_create()
      modal.open_modal()
      modal.fill_prompt(BACK_TO_PROMPT_PROMPT_TEXT)
      with modal.expect_generate_response(timeout=GENERATE_RESPONSE_TIMEOUT) as response_info:
          modal.generate_button.click()
      assert response_info.value.status == 200
      modal.wait_for_review_form(timeout=REVIEW_FORM_TIMEOUT)

  with allure.step("Step 2 — Click 'Back to prompt'"):
      modal.back_button.click()

  with allure.step("Step 3 — Verify the modal returns to the prompt input step"):
      modal.wait_for_input_step(timeout=NAVIGATION_TIMEOUT)
      assert modal.back_button.count() == 0
      assert modal.approve_button.count() == 0

  with allure.step("Step 4 — Verify the previously entered prompt text is preserved"):
      assert modal.get_prompt_value() == BACK_TO_PROMPT_PROMPT_TEXT

  with allure.step("Step 5 — Verify no draft data leaks into the prompt step UI"):
      assert modal.review_name_input.count() == 0
      assert modal.review_description_input.count() == 0
      assert modal.review_instructions_input.count() == 0

  with allure.step("Step 6 — Verify no new network requests and zero console errors"):
      assert len(draft_requests) == 1  # unchanged from Step 1 — Back fires no new call
      assert not create_requests
      assert not console_capture  # 0 error-level messages, both before and after Back
  ```
- Timeout constants: reuse this file's existing timeout constants (`NAVIGATION_TIMEOUT`, `GENERATE_RESPONSE_TIMEOUT`, `REVIEW_FORM_TIMEOUT`) if already defined in `test_skill_build_with_ai.py`; otherwise mirror the Agent test file's values.
- Marker: `@pytest.mark.p2` + `@pytest.mark.regression` + `@pytest.mark.skills`, consistent with this file's other Build-with-AI cases and this case's own `l2`/`medium` priority.
