# Test Case: Build with AI — "Back to prompt" returns to input step and preserves prompt text

> ⚠️ **UNDER REVIEW — 2026-08-14 fidelity audit. Do NOT reuse this AFS as a pattern.**
>
> This spec directs the implementer to **substitute the system under test** (mocking
> the `generate_application_draft` response) for a TMS case whose text never asks for
> simulation. Classification: **TRANSIT** — as 1918 — the mock is transit to the review step; the back-to-prompt observable is real.
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
- **TMS ID**: ELITEA-1919
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/agents/build_with_ai/ELITEA-1919_build-with-ai-back-to-prompt-returns-to-input-step-preserves-text.md`
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project `UI Testing` / id `400` (browser session's last-selected project — the case's own steps are project-agnostic)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via `VITE_DEV_TOKEN`; admin-equivalent role, per `.agents/profile.md` § Roles & sample users)
- **Analyst**: qa-engineer (Sage), analyst slot, batch #1298 — last case in the batch
- **Status**: ready-for-automation
- **Tracking issue**: EliteaAI/elitea-testing-public#1298 (batch tracking issue — no per-case board card)
- **Case-gate note**: source case frontmatter carries `status: draft` / `execution_type: manual` — consistent with the batch's other Build-with-AI cases; no exclusion per `.agents/testing.md` § TMS case-gate, so this run proceeded normally.
- **Reuse check (before executing)**: `grep -rn "back_button\|generate-agent-back-button" automation/tests automation/pages` shows `back_button` is a pre-existing `LocatorDescriptor` on `GenerateAgentModalPage` (`generate-agent-back-button`), but is only ever `.is_visible()`-checked in the suite (`TestAgentBuildWithAICreationFailureRecovery`, asserting the review step's action buttons are still present after a creation failure) — **never `.click()`ed anywhere**. ELITEA-1918's AFS explicitly disclaimed covering it ("this AFS does **not** cover Back-to-prompt... This is ELITEA-1919's separate case"). Confirms this case is genuinely unexercised — `ready-for-automation`, not `already-covered`/`extend-existing`.

## Triangulation — what "Back to prompt" actually does (source-level confirmation)

Read `GenerateEntityModal.jsx` (`../EliteaUI/src/[fsd]/entities/generate-entity-with-ai/ui/GenerateEntityModal.jsx`), the shared shell both the Agent and Skill Build-with-AI modals render through:

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

**This is the mechanism the case's Pass criteria depend on.** `handleBack()` (wired to `back_button` via `onClick={handleBack}` in `renderActions()`) resets `step` back to `STEPS.INPUT` and clears `draftData` (so the review form's fields are gone, `renderContent()`'s `step === STEPS.REVIEW && draftData` branch no longer matches) — but it never calls `setDescription('')`. `handleClose()` (wired to both the INPUT-step Cancel button and the review-step X icon, per ELITEA-1917/1918's triangulation) is the sibling function that DOES clear `description`. The prompt-preservation behavior this case asserts is a deliberate asymmetry between these two exit paths, not an accident — confirmed by reading both functions side by side, not inferred from behavior alone.

## Preconditions
- `${TEST_USER}` is authenticated via the `auth_state` fixture (localhost `VITE_DEV_TOKEN` bypass — no Keycloak login form on localhost).
- The New Agent creation page (`${BASE_URL}/agents/create?viewMode=owner`) is reachable, with the "General" accordion section expanded by default.
- **A draft has been generated and the review/edit form is displayed** — this case's own precondition, same shape as ELITEA-1918. Reached live this run via a real (unmocked) `generate_application_draft` call — no `mock_generate_success()` needed; the real endpoint responded within the existing `REVIEW_FORM_TIMEOUT`/`GENERATE_RESPONSE_TIMEOUT` constants this file already defines. Mocking (`GenerateAgentModalPage.mock_generate_success()`) remains available if the implementer prefers a deterministic draft payload — this case's Pass criteria don't depend on the draft's specific content, only on what "Back to prompt" does to the modal's step/prompt state afterward.

## Test Data
### reuse-existing (no fixture creation/teardown needed)
- `${TEST_USER_EMAIL}` / `${TEST_USER_PASSWORD}` via `auth_state`.
- `${ELITEA_PROJECT_ID}` (whichever project is active — the flow is project-agnostic).
- Prompt text: any non-empty natural-language string, confirmed live with:
  `"An agent that helps summarize customer support tickets for ELITEA-1919 back-to-prompt verification."`
  A dedicated `BACK_TO_PROMPT_PROMPT_TEXT` constant is recommended (mirrors this file's existing `CANCEL_PROMPT_TEXT` / `CANCEL_FROM_REVIEW_PROMPT_TEXT` naming) since this case's own assertion (Step 4) depends on reading the EXACT text back — reusing another case's constant is fine as long as it stays a literal string this test owns the identity of.
- If the implementer mocks the draft instead of using the real endpoint, a small dedicated `BACK_TO_PROMPT_DRAFT_PAYLOAD` (same shape as `CANCEL_FROM_REVIEW_DRAFT_PAYLOAD`) is sufficient — this case never asserts on the draft's specific field values, only on its absence after Back is clicked.

No new test data is created or persisted in the product by this case's steps — a draft IS generated (precondition), but it is discarded when "Back to prompt" is clicked and no `Create Agent` call ever fires. See Cleanup.

## Test Steps

1. Navigate to `${BASE_URL}/agents/create?viewMode=owner`, open the Build with AI modal (`generate-agent-open-button`), enter a natural-language description into the prompt textarea (`generate-agent-prompt-input`), and click "Generate Draft" (`generate-agent-submit-button`) to reach the review step.
   - **Verify**: the review form is displayed with the generated draft's data — confirmed live via `wait_for_review_form()`'s existing pattern (waits for `back_button` + `approve_button` visible) and an accessibility snapshot showing populated Name/Description/Instructions/Welcome Message/4 Chat-starter fields (this run generated "Ticket Summary Verifier" from the ticket-summarization prompt — real, unmocked AI output).
2. Click "Back to prompt" (`generate-agent-back-button`).
   - **Verify**: the click is accepted, no confirmation/"discard changes?" interstitial appears — confirmed live, same finding class as ELITEA-1917/1918's Close/Cancel controls.
3. Verify the modal returns to the prompt input step.
   - **Verify**: confirmed live via accessibility snapshot immediately after the click — the dialog now shows only the prompt textarea (`generate-agent-prompt-input`) + `Cancel`/`Generate Draft` (`generate-agent-submit-button`) action buttons; `generate-agent-back-button` and `generate-agent-approve-button` are no longer present in the DOM (the review-step action row is gone entirely, not merely hidden — `renderContent()` re-renders the INPUT branch).
4. Verify the previously entered natural-language description is still present in the input field.
   - **Verify**: confirmed live — the prompt textarea's value read immediately after the Back click is
     `"An agent that helps summarize customer support tickets for ELITEA-1919 back-to-prompt verification."`,
     an **exact, character-for-character match** to what was typed in Step 1 (no truncation, no whitespace drift, no residual draft text appended).
5. Verify no draft data leaks into the prompt step UI.
   - **Verify**: confirmed live — none of the review-form's field testids (`generate-agent-review-name-input` and siblings) are present in the DOM after Back; the visible surface is exactly the input step's own elements (prompt textarea + Cancel/Generate Draft), matching the identical DOM shape the modal has on its very first open (Step 1, before ever generating).

## Expected Results
Clicking "Back to prompt" (`generate-agent-back-button`) on the GenerateAgentModal's review step returns the modal to the INPUT step (review-step action buttons and all review-form fields removed from the DOM, not merely hidden), preserves the exact previously-typed prompt text in `generate-agent-prompt-input`, and shows only the input step's own elements — no review-form field, no generated-draft content, no confirmation interstitial. No new network request fires from the Back click itself (pure client-side state transition — `handleBack()` never calls the generate-draft or create-agent endpoints; confirmed via `browser_network_requests` filtered to both routes: still exactly 1 `generate_application_draft` call total, from Step 1's own Generate, and 0 `applications/prompt_lib` CREATE calls, both counts unchanged by the Back click). No console errors beyond the pre-existing, unrelated `disableUnderline` React DOM-attribute warning that fires on every Build-with-AI run regardless of outcome (documented baseline noise — see ELITEA-1906/1913/1916/1918's AFS Known Defects; confirmed present, unchanged, this run too — `browser_console_messages` level=error → exactly 1 result, that warning, no others, before AND after the Back click).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Generate an agent draft and enter the review/edit form | The review/edit form is displayed | AFS Step 1 | `modal.wait_for_review_form()` (existing helper); accessibility snapshot confirms populated fields | ready-for-automation (new test) |
| 2 Click "Back to prompt" (or equivalent back control) | The modal navigates back | AFS Step 2 | `modal.back_button.click()` — first assertion-backed `.click()` of this control anywhere in the suite (previously `.is_visible()`-only) | ready-for-automation (new test) |
| 3 Verify the modal returns to the prompt input step | The prompt input step is displayed | AFS Step 3 | `modal.wait_for_input_step()` (existing helper — waits for `generate_button` visible) + explicit absence check on `back_button`/`approve_button` | ready-for-automation (new test) |
| 4 Verify the previously entered natural-language description is still present in the input field | The original prompt text is present and unchanged | AFS Step 4 | `modal.get_prompt_value() == BACK_TO_PROMPT_PROMPT_TEXT` (existing helper — exact-string equality) | ready-for-automation (new test) |
| 5 Verify no draft data leaks into the prompt step UI | Only the input field and action buttons are visible — no review form fields or generated content | AFS Step 5 | Absence assertion on review-form field testids (e.g. `modal.review_name_input.count() == 0`) — reference by absence per canon ruling #511 extension | ready-for-automation (new test) |

### Axis 2 — Analyst additions

- Confirmed **zero new network requests** fire from the Back click itself — `browser_network_requests` filtered to `generate_application_draft`/`applications/prompt_lib` showed the same 1-vs-0 split before and after clicking Back — *added: guards against a future regression where "Back to prompt" accidentally re-triggers a generate or create call (it is meant to be a pure client-side state reset per `handleBack()`'s source).*
- Confirmed **zero new console errors** beyond the pre-existing, cross-case `disableUnderline` warning (`browser_console_messages`, level=error → 1 result, that warning only, unchanged by the Back click) — *added: side-channel check, standard practice per this skill's methodology.*
- **Source-level confirmation of the preservation mechanism** (`handleBack()` resets `step`/`draftData` but never calls `setDescription('')`, unlike the sibling `handleClose()`) — *added: this is the actual reason the behavior holds, not merely an observed correlation; documents the asymmetry for future maintainers so a refactor that "cleans up" `handleBack()` to also reset `description` is caught as the regression it would be.*
- Confirmed the review-step action row (`back_button`/`approve_button`) is fully removed from the DOM after Back, not merely hidden/inert — *added: same DOM-removal-vs-hidden distinction ELITEA-1917/1918 established for the modal-close case; here it distinguishes a real state transition from a CSS-only toggle that could leave stale review-form data reachable via direct DOM query even if visually hidden.*
- Confirmed all testids needed already exist as `LocatorDescriptor` fields on `GenerateAgentModalPage` — no `add-data-testid` work needed for this case.

## Cleanup
No product state persists from this case's own steps — the generated draft is discarded when "Back to prompt" is clicked (`draftData` reset to `null`), and the create-agent call never fires. No `agent_api.delete_agent(...)` teardown is needed. (If the implementer chooses to mock the draft via `mock_generate_success()` instead of using the real generate endpoint, no cleanup changes — mocking is purely client-side route interception, nothing persists either way.)

## Concrete Handles (discovered during exploration — all pre-existing)

| Element | Recommended Locator | Provenance |
|---|---|---|
| "Build with AI" open button | `generate-agent-open-button` (`GenerateAgentModalPage.open_button`) | on-main ✓ |
| Modal container | `generate-agent-modal` (`GenerateAgentModalPage.modal`) | on-main ✓ |
| Prompt textarea | `generate-agent-prompt-input` (`GenerateAgentModalPage.prompt_input`) — read via `modal.get_prompt_value()` (existing helper) | on-main ✓ |
| Generate Draft button (also the input-step re-appearance marker) | `generate-agent-submit-button` (`GenerateAgentModalPage.generate_button`) — `modal.wait_for_input_step()` waits on this | on-main ✓ |
| **"Back to prompt" button — this case's core control** | `generate-agent-back-button` (`GenerateAgentModalPage.back_button`) — pre-existing field; previously `.is_visible()`-checked only, never `.click()`ed | on-main ✓ |
| "Create Agent" / approve button (NOT this case — disambiguation only) | `generate-agent-approve-button` (`GenerateAgentModalPage.approve_button`) — used only to assert its absence after Back, per AFS Step 3 | on-main ✓ |
| Review-form Name field (used for absence assertion only) | `generate-agent-review-name-input` (`GenerateAgentModalPage.review_name_input`) — `count() == 0` after Back proves no draft-data leak | on-main ✓ |
| Base-agent CREATE route | `**/elitea_core/applications/prompt_lib/**` (`GenerateAgentModalPage.CREATE_APPLICATION_ROUTE`) | on-main ✓ — used only for a **negative** (no-call) network assertion |
| Generate-draft route | `**/elitea_core/generate_application_draft/**` (`GenerateAgentModalPage.GENERATE_DRAFT_ROUTE`) | on-main ✓ — expected to fire exactly ONCE total (Step 1's own Generate), unchanged by the Back click |

No new testids required. No new page-object locators required. Every handle needed already exists in `GenerateAgentModalPage`.

## Network Behavior
Confirmed live: across the entire open → type-prompt → generate → back sequence, exactly **one** request matched `**/elitea_core/generate_application_draft/**` (`POST`, `200 OK` — Step 1's own Generate, reaching the review step this case's precondition needs), and **zero** requests matched `**/elitea_core/applications/prompt_lib/**` (`POST`, the CREATE route) at any point — filtering `browser_network_requests` to both route substrings before and immediately after clicking "Back to prompt" showed the identical 1-vs-0 split, confirming the Back click itself is a pure client-side state transition with no network side effect. Only the page's normal load-time GETs (`support_assistant`, `project_info`, `configurations`, `permissions`, `tags`, `default_icons`, socket.io polling, etc.) appeared otherwise, consistent with ELITEA-1905/1917/1918's own Network Behavior notes for this same modal family.

## Known Defects Found During Exploration
None found. "Back to prompt" behaves exactly per the case's Pass criteria: returns to the input step, preserves the prompt text verbatim, and shows no leaked draft data — all confirmed live and further confirmed at the source level (`handleBack()` in `GenerateEntityModal.jsx`).

## Blocked Steps
None. All case elements were executed live this run against the real local system (`http://localhost:5173`), including a real (unmocked) `generate_application_draft` call that produced a genuine AI-generated draft ("Ticket Summary Verifier").

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Add a new, standalone test class to `automation/tests/ui/agents/test_agent_build_with_ai.py` — e.g. `TestAgentBuildWithAIBackToPromptFromReviewStep` (mirrors `TestAgentBuildWithAICancelFromReviewStep`'s naming/shape, ELITEA-1918, since both operate from the review step, but this one's exit control is `back_button` not `close_button`).
- **Reaching the review step**: either (a) a real, unmocked `generate_button.click()` + `wait_for_review_form()` (confirmed reliable this run, real AI response), or (b) `mock_generate_success(draft)` + `expect_generate_response()` (the pattern ELITEA-1916/1918 use) for a deterministic, faster draft. Either is sound — this case's Pass criteria don't depend on the draft's specific content.
- **Do not target `close_button` or `approve_button`** — this case's own control is `back_button` exclusively. Reuse `BasePage.capture_requests_matching()` / `capture_console_errors()` (existing infrastructure, same as ELITEA-1917/1918) to back the Network Behavior / console-error assertions with real evidence rather than a bare "looked fine."
- **Absence assertions after Back** (`back_button`, `approve_button`, `review_name_input` all `count() == 0`) are first-class per `.agents/testing.md`'s canon ruling #511 extension — they count as "referencing" the testid, no different from a positive assertion.
- Suggested flow (illustrative, not prescriptive):
  ```python
  with allure.step("Step 1 — Generate a draft and reach the review form"):
      list_page.navigate_to_create()
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

  with allure.step("Step 6 — Verify no new network requests and zero unexpected console errors"):
      assert len(draft_requests) == 1  # unchanged from Step 1 — Back fires no new call
      assert not create_requests
      unexpected_errors = [m.text for m in console_capture if "disableUnderline" not in m.text]
      assert not unexpected_errors
  ```
- Timeout constants: reuse this file's existing `NAVIGATION_TIMEOUT` (15000), `GENERATE_RESPONSE_TIMEOUT`, `REVIEW_FORM_TIMEOUT` — all already defined, no new constants needed.
- Marker: `@pytest.mark.p2` + `@pytest.mark.regression`, consistent with this file's other Build-with-AI cases and this case's own `l2`/`medium` priority.
