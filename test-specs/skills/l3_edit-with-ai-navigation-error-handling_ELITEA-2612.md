# Test Case: Edit with AI — Skill Navigation and Error Handling

## Metadata
- **TMS ID**: ELITEA-2612
- **Linked Story**: none
- **Priority**: l3 (case `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (skills-remaining-w4)
- **Status**: ready-for-automation

## Preconditions
- User is logged in (Admin/Editor role — `PERMISSIONS.skills.update`).
- A project is selected (`${PROJECT_ID}` — Private project, id `399` on this env).
- A skill exists that the test can edit. **Recommendation: create a throwaway
  skill per-test** (same rationale as ELITEA-2611 — the flow's `handleClose`/
  `handleRefinePrompt` paths never mutate the underlying skill since neither
  case ever clicks Save, but a shared fixture skill still risks collision with
  other suites reading its Name/Description while this test's modal is open).

## Test Data
### generate-per-test (in test setup, deleted in teardown)
- Skill name: `nav-error-test-skill-${timestamp}` (regex
  `/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/`, max 64 chars)
- Description: `Original description that should be preserved`
- Instructions: `Original instructions that should be preserved`
- Valid prompt: `Improve this skill with better structure`
- Empty prompt: `""`
- Whitespace prompt: `"   "` (3 spaces)

## Test Steps

### Part A — "Refine Prompt" (the case's "Back") preserves the prompt text
1. Navigate to `${BASE_URL}/skills/all/{skill_id}` for the pre-created skill,
   open "Edit with AI" (`edit-skill-with-ai-button`).
   - **Verify**: `ai-edit-skill-modal` opens on the prompt-input step, empty.
2. Type the valid prompt into `ai-edit-skill-prompt-input`.
3. Click `ai-edit-skill-generate-button` ("Generate Draft") and wait for the
   wizard.
   - **Verify**: wizard opens on `ai-edit-skill-step-indicator` == `"1. General"`.
4. Click "Refine Prompt" — this IS the case's "Back to Enter request step or
   equivalent" (case text names no exact label; the live control is
   "Refine Prompt", confirmed via source read of `EditEntityModal.jsx`'s
   `renderWizardFooter()` — there is no separate "Back" button anywhere in the
   wizard footer).
   - **Verify**: the modal returns to the prompt-input step (wizard content
     gone, `ai-edit-skill-prompt-input` visible again).
5. Read `ai-edit-skill-prompt-input`'s value.
   - **Verify**: it still equals the exact prompt typed in step 2 — confirmed
     live via source: `EditEntityModal.jsx`'s `handleRefinePrompt` resets
     `phase`/`draftData`/`activeStepIndex`/`isDraftValid` but **does NOT reset
     `description`** (the prompt state), unlike `handleClose`/the `!open`
     effect, which reset all five including `description`. This asymmetry is
     the mechanism the case is really testing.
6. Verify the field is still editable and "Generate Draft" is enabled again
   (`is_enabled()` on `ai-edit-skill-generate-button`); click it once more.
   - **Verify**: generation succeeds a second time — wizard reopens on
     `"1. General"` (confirmed live: re-clicking Generate Draft with the
     preserved prompt regenerates cleanly, no stale-state issue).

### Part B — Cancel (Close) preserves the original skill configuration
7. With the wizard open again (reuse the state from step 6, or regenerate),
   read the CURRENT column values as a baseline
   (`ai-edit-skill-general-description-current` text, and the skill detail
   page's Description/Instructions via `SkillDetailPage.get_description()`/
   `get_instructions()` before any of this Part ran).
8. Click "Next" (`ai-edit-skill-wizard-next-button`) at least once — advance
   past the first step without applying anything.
   - **Verify**: `ai-edit-skill-step-indicator` no longer reads `"1. General"`.
9. Click the modal's Close (X) button — **`ai-edit-skill-close-button`, NOT a
   "Cancel" button**. Source-confirmed gotcha: `EditEntityModal.jsx`'s
   `renderActions()` (which renders the `ai-edit-skill-cancel-button` labelled
   "Cancel") returns `null` whenever `phase !== PHASES.PROMPT` — i.e. **the
   "Cancel" button only exists in the prompt-input phase**. Once the wizard
   phase is reached, the only dismissal control is the modal-level Close (X).
   The case's "Click 'Cancel' or close the wizard" step is written generically
   enough to cover this — the AFS makes the mechanism explicit so the
   implementer doesn't go looking for a wizard-phase Cancel button that does
   not exist.
   - **Verify**: `ai-edit-skill-modal` becomes hidden.
10. Verify the skill detail page (still mounted underneath) shows the ORIGINAL
    Name/Description/Instructions — unchanged (`SkillDetailPage.get_name()`/
    `get_description()`/`get_instructions()`).
11. Reload the skill detail page (`${BASE_URL}/skills/all/{skill_id}`).
    - **Verify**: Name/Description/Instructions are still the original seeded
      values — confirms nothing was persisted server-side (no `PUT` to
      `.../skill/prompt_lib/...` ever fired, since Save was never clicked).
12. (Case step 11 "Reopen the skill" / step 12 "no changes saved") — covered
    by step 11 above; reopening via reload is the strongest form of this
    check (proves server state, not just React state that a soft
    re-navigation might not have cleared).

### Part C — Generation failure shows an error, and "Generate Draft" doubles as Retry
13. Open "Edit with AI" again (fresh: close/reopen, or navigate fresh).
    - **Verify**: wizard opens on the prompt-input step.
14. Type the valid prompt.
15. **Simulate a generation failure via network interception** (case step 15
    explicitly allows "if possible via network/API error" — no backend lever
    exists to force a real 500, so this AFS uses `page.route()` to intercept
    exactly ONE `POST **/elitea_core/generate_skill_draft/**` and fulfil it
    with `500` + a JSON body `{"error": "<message>"}`, then `route.continue()`
    on any subsequent call — same class of interception technique already
    established in this codebase, see `ai_edit_skill_modal_page.py`'s
    `click_generate_and_wait_for_response()` docstring's "declared
    improvisation" precedent for reading POST bodies via `page.route()`).
    Click `ai-edit-skill-generate-button`.
16. Wait for `ai-edit-skill-error-alert` to become visible.
    - **Verify**: the alert IS shown, and its text equals exactly the
      simulated `error` field from the mocked 500 body — confirmed live this
      round-trips through `generateError?.data?.error ||
      generateError?.data?.detail || 'Failed to generate. Please try again.'`
      in `EditEntityModal.jsx`. (A real, unmocked backend failure would render
      whichever of `data.error`/`data.detail` the API actually returns, or the
      hardcoded fallback string if neither is present — this AFS only
      controls the mocked case, so assert on the exact string the mock sent,
      not a hardcoded expectation about a real backend error shape.)
17. Verify "Retry" is available. **There is no separate "Retry" button/testid
    — confirmed via source read: on a `handleGenerate` catch, `phase` is set
    back to (already is) `PHASES.PROMPT`, so the prompt phase's own
    `ai-edit-skill-generate-button` ("Generate Draft") remains visible AND
    enabled and IS the retry mechanism.** Assert
    `generate_button.is_visible()` and `.is_enabled()` after the failure — this
    satisfies the case's "Retry button or option is present" (an "equivalent"
    control, same shape already sanctioned by ELITEA-2611's "Generate"/
    "Generate Draft" label reconciliation).
18. Remove the route interception (or let it fall through to `route.continue()`
    on the 2nd call) and click `ai-edit-skill-generate-button` again.
19. Wait for `ai-edit-skill-step-indicator`.
    - **Verify**: the retry succeeds — wizard reaches `"1. General"`, and
      `ai-edit-skill-error-alert`'s count is 0 (error cleared).

### Part D — Empty/whitespace prompt validation is disable-only (case-text drift — see Known Defects/Clarification)
20. Open "Edit with AI" fresh (empty prompt by default).
    - **Verify**: `ai-edit-skill-prompt-input` value is `""`.
21. Read `ai-edit-skill-generate-button`'s enabled state with an empty prompt.
    - **Verify**: `is_enabled() == False` (disabled). Confirmed live via
      source: `EditEntityModal.jsx`'s Generate Draft button carries
      `disabled={!description.trim()}`.
22. **No separate validation error message is rendered for an empty prompt** —
    confirmed live (`ai-edit-skill-error-alert`'s count stays `0`). This
    diverges from the case's step 22 ("verify error message indicates prompt
    is required") — see the filed clarification below. The AFS asserts the
    disable-only mechanism, which is what step 23 ("Generate button is
    disabled or blocked") already anticipates and what the live product
    actually implements.
23. (Same assertion as step 21, restated by the case as its own step —
    covered.)
24. Fill the prompt with whitespace only (`"   "`).
25. Read `ai-edit-skill-generate-button`'s enabled state.
    - **Verify**: still `False` — `.trim()` on a whitespace-only string is
      empty/falsy, so the SAME disabled condition as the empty-prompt case
      fires. Confirmed live: filling `"   "` does not enable the button.
26. Attempt a click anyway (`force=True`, since Playwright's own actionability
    check would otherwise refuse to click a disabled element — this is a
    deliberate defense-in-depth check, not a normal click).
    - **Verify**: no generation is triggered — `ai-edit-skill-loading-indicator`
      never appears, the modal stays on the prompt-input step. This proves
      the disabled attribute isn't merely cosmetic (a stale/decorative
      `disabled` class that a forced click could bypass) — the `onClick`
      handler itself is gated (MUI `disabled` buttons don't fire `onClick`
      even under a forced Playwright click, since the DOM-level `disabled`
      attribute suppresses the click event before React's handler runs).

## Expected Results
- "Refine Prompt" returns to the prompt-input step with the SAME prompt text
  the user typed — not cleared. Regeneration from there works.
- Closing the wizard (via the modal's X — the only dismissal control once past
  the prompt phase) never applies any change; the skill's Name/Description/
  Instructions are unchanged even after a full page reload.
- A generation failure renders `ai-edit-skill-error-alert` with the backend's
  error text; "Generate Draft" itself (no separate "Retry" control) retries
  successfully once the failure condition is removed.
- Empty AND whitespace-only prompts both keep "Generate Draft" disabled — no
  generation is ever triggered — but (case-text drift) no explicit "Prompt is
  required" validation message is rendered; the disable-only mechanism is the
  entire guard.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open skill, click "Edit with AI" | wizard opens on prompt step | step 1 | `step 1` | asserted |
| 2 Enter valid prompt | prompt text entered | step 2 | `step 2` | asserted |
| 3 Click "Generate" and wait | suggestions generated, wizard advances | step 3 | `step 3`: step-indicator == "1. General" | asserted |
| 4 Click "Back to Enter request step" or equivalent | wizard returns to prompt step | step 4 | `step 4`: "Refine Prompt" click + prompt-input visible | asserted *(live control is "Refine Prompt" — no separate "Back" button; AFS documents the mapping)* |
| 5 Verify original prompt preserved | prompt field contains previously entered text | step 5 | `step 5`: `get_prompt_value() == valid_prompt` | asserted |
| 6 Verify user can modify and regenerate | can edit + generate again | step 6 | `step 6`: re-click Generate Draft succeeds | asserted |
| 7 Generate suggestions again | suggestions displayed | step 7 (reuse step-6 state) | `step 7` | asserted |
| 8 Navigate wizard steps without applying | user on a later step | step 8 | `step 8`: step-indicator != "1. General" | asserted |
| 9 Click "Cancel" or close the wizard | wizard closes | step 9 | `step 9`: `ai-edit-skill-close-button` click, modal hidden | asserted *(no wizard-phase "Cancel" button exists — AFS documents why Close/X is the correct control)* |
| 10 Verify skill's original values unchanged | Description/Instructions original | step 10 | `step 10`: detail-page field reads | asserted |
| 11 Reopen the skill | skill loads with original values | step 11 | `step 11`: reload + field reads | asserted |
| 12 Verify no changes were saved | all fields match original | step 12 (= step 11's reload proof) | `step 11` | asserted |
| 13 Open "Edit with AI" wizard | wizard opens | step 13 | `step 13` | asserted |
| 14 Enter a valid prompt | prompt entered | step 14 | `step 14` | asserted |
| 15 Trigger/simulate generation failure | generation fails | step 15 | `step 15`: `page.route()` 500 mock | asserted *(case explicitly allows "if possible via network/API error" — no product-side failure lever exists)* |
| 16 Verify error message displayed | clear error message shown | step 16 | `step 16`: `ai-edit-skill-error-alert` text == mocked message | asserted |
| 17 Verify "Retry" option available | retry button/option present | step 17 | `step 17`: `ai-edit-skill-generate-button` visible+enabled | asserted *(no separate Retry control — Generate Draft itself is it, same "equivalent control" reconciliation as ELITEA-2611)* |
| 18 Click Retry | generation attempted again | step 18 | `step 18`: re-click Generate Draft | asserted |
| 19 Verify retry can succeed | successful generation after retry | step 19 | `step 19`: step-indicator == "1. General", error-alert count 0 | asserted |
| 20 Open wizard | wizard opens | step 20 | `step 20` | asserted |
| 21 Leave prompt empty, try to generate | validation error shown | step 21 | `step 21`: generate button disabled | asserted *(disable-only — see step 22 note + Known Defects)* |
| 22 Verify error message "prompt is required" | message indicates requirement | step 22 | `step 22`: NOT PRESENT LIVE | **clarification filed, not asserted as case-literal** |
| 23 Verify Generate button disabled/blocked | cannot proceed | step 23 | `step 21`/`step 23` (same assertion) | asserted |
| 24 Enter whitespace-only prompt | whitespace entered | step 24 | `step 24` | asserted |
| 25 Try to generate | validation error shown | step 25 | `step 25`: generate button still disabled | asserted *(same disable-only mechanism)* |
| 26 Verify whitespace treated as empty | same validation as empty | step 26 | `step 26`: forced click triggers no generation | asserted |

**Axis 2 — Analyst additions:**
- `step 4/5` asserts the specific React-state asymmetry between
  `handleRefinePrompt` (preserves `description`) and `handleClose`/the `!open`
  effect (clears `description`) — *added: this is the actual mechanism under
  test; a naive "click Back, check prompt" test could pass by accident if it
  didn't also confirm Close/Cancel behaves oppositely (Part B), so both parts
  together prove the asymmetry is intentional, not incidental.*
- `step 9` documents the wizard-phase-only-has-Close, no-Cancel gotcha —
  *added: source-confirmed via `EditEntityModal.jsx`'s `renderActions()`
  returning `null` outside `PHASES.PROMPT`; worth flagging so the implementer
  doesn't write a test that looks for a nonexistent `ai-edit-skill-cancel-button`
  once past the prompt step.*
- `step 26` asserts the forced-click-on-disabled-button proves the guard is a
  real `onClick` gate, not just a decorative CSS/attribute — *added: a
  stronger proof than "the button LOOKS disabled."*
- No new console errors attributable to this flow — *added: standard
  side-channel check. Observed during this run: the pre-existing benign
  dev-env WebSocket `ERR_NAME_NOT_RESOLVED` (documented in ELITEA-2611's AFS,
  every localhost session), a handful of stray 404s for OTHER skills'
  `skill/prompt_lib/{project}/{id}[/{version}]` (leftover ids from other
  suites' data in this project pool, not this test's own skill/actions), and
  the ONE simulated 500 for `generate_skill_draft` this test itself causes in
  Part C (expected, not a defect).*

## Cleanup
1. Delete the generated skill via the UI delete flow (Skill overflow menu →
   "Delete skill" → type name to confirm, `skill-controls-menu-button` →
   `skill-delete-menu-item` → `delete-confirm-name-input` (scoped `#name`
   sub-input) → `delete-confirm-button`) or `SkillAPI.delete_skill(skill_id)`
   in a `try/finally` — same convention as ELITEA-2611's AFS.

## Concrete Handles (discovered during exploration)

**PROVENANCE:** all pre-existing testids below verified live 2026-08-12
against `origin/main` and `origin/automation/testids` (post `git fetch
origin`) — all `YES`/`YES`, already on `main`. The ONE new handle this case
needs (`ai-edit-skill-wizard-refine-prompt-button`) does not exist yet on
either ref — it is `needs-adding`.

| Element | Locator | PROVENANCE |
|---|---|---|
| "Edit with AI" button | `LocatorDescriptor(testid="edit-skill-with-ai-button")` | on-main ✓ (reused from `AIEditSkillModalPage.open_button`) |
| Edit-with-AI modal | `LocatorDescriptor(testid="ai-edit-skill-modal")` | on-main ✓ (reused: `.modal`) |
| Modal close (X) button | `LocatorDescriptor(testid="ai-edit-skill-close-button")` | on-main ✓ (reused: `.close_button`) — **the ONLY dismissal control once the wizard phase is reached (Part B)** |
| Prompt textarea | `LocatorDescriptor(testid="ai-edit-skill-prompt-input")` | on-main ✓ (reused: `.prompt_input`) |
| Generate error alert | `LocatorDescriptor(testid="ai-edit-skill-error-alert")` | on-main ✓ (reused: `.error_alert`) |
| Loading indicator | `LocatorDescriptor(testid="ai-edit-skill-loading-indicator")` | on-main ✓ (reused: `.loading_indicator`) |
| "Generate Draft" button | `LocatorDescriptor(testid="ai-edit-skill-generate-button")` | on-main ✓ (reused: `.generate_button`) — **doubles as the Retry control (Part C) and carries the `disabled` state asserted in Part D** |
| "Cancel" button (prompt phase ONLY) | `LocatorDescriptor(testid="ai-edit-skill-cancel-button")` | on-main ✓ (reused: `.cancel_button`) — NOT exercised by this case (Part B uses Close instead, since it dismisses from the WIZARD phase where Cancel doesn't render) |
| Wizard step indicator | `LocatorDescriptor(testid="ai-edit-skill-step-indicator")` | on-main ✓ (reused: `.step_indicator`) |
| Wizard "Next" button | `LocatorDescriptor(testid="ai-edit-skill-wizard-next-button")` | on-main ✓ (reused: `.next_button`) |
| Skill overflow menu → Delete (cleanup) | `LocatorDescriptor(testid="skill-delete-menu-item")` | on-main ✓ (reused, ELITEA-2611 precedent) |
| Skill controls menu button (cleanup) | `LocatorDescriptor(testid="skill-controls-menu-button")` | on-main ✓ (`_surface.md` § Pin/unpin) |

**Genuinely no testid — `testid needed:` (this case is the first to exercise
it — canon #511 executed-code-path rule now applies).**

| Element | Component (file) | New prop to add | testid needed |
|---|---|---|---|
| "Refine Prompt" button (wizard footer) | `entities/edit-entity-with-ai/ui/EditEntityModal.jsx` `renderWizardFooter()` (shared); wire the value at `features/skill/ui/ai-edit-skill-modal/AIEditSkillModal.jsx`'s `<EditEntityModal>` call site | `refinePromptButtonTestId` (prop channel already exists on `EditEntityModal`, deliberately left unwired per ELITEA-2611's AFS since that case never clicked it — THIS case does) | `ai-edit-skill-wizard-refine-prompt-button` (matches the sibling `ai-edit-skill-wizard-{previous,next,save}-button` naming already landed for ELITEA-2611) |

No other new testids needed — Parts B/C/D reuse entirely pre-existing
prompt-phase and modal-level handles; Part D's validation is asserted via the
existing `ai-edit-skill-generate-button`'s `disabled` state, not a new
validation-message testid (none is rendered — see Known Defects below).

## Network Behavior
- `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/{projectId}` —
  same endpoint as ELITEA-2611. Part C mocks exactly ONE call to `500` via
  `page.route()`, then lets subsequent calls through to the real backend for
  the retry. Real backend responses for `generate_skill_draft` were also
  observed during Parts A/B (unmocked, `200 OK`).
- No `PUT .../skill/prompt_lib/...` should EVER fire in this case — Parts A-D
  never click Save/Save-as-Version. Worth a network-request-count assertion
  (`page.expect_request` should never match a `PUT` to that path across the
  whole test) as a stronger proof than just re-reading the detail page.

## Known Defects Found During Exploration
None — the underlying navigation/error/validation guarantees all hold
correctly live:
- "Refine Prompt" genuinely preserves the prompt (asymmetric-but-correct
  state reset).
- Close genuinely never applies partial/uncommitted wizard state.
- A generation failure genuinely surfaces an error and genuinely allows a
  working retry via the same control.
- Empty/whitespace prompts genuinely cannot trigger generation.

**Case-text clarification filed (not a product defect — reverse-masking
guard):** [elitea-testing-public#1478](https://github.com/EliteaAI/elitea-testing-public/issues/1478)
— case steps 21-26 (Part D) describe an explicit "Prompt is required"
validation error message; the live product implements disable-only
validation (`disabled={!description.trim()}` on the Generate Draft button)
with NO separate error text ever rendered, for either an empty or a
whitespace-only prompt. The case's own step 23 already anticipates this
("Generate button is disabled or blocked"), so this AFS asserts the
disable-only mechanism as the correct/expected live behavior rather than
treating the missing message as a bug.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only locators (`.agents/testing.md`).
- **Reuse `automation/pages/ai_edit_skill_modal_page.py` as-is** for every
  handle except the new `refinePromptButtonTestId` wiring — add one new
  `LocatorDescriptor` (`refine_prompt_button`, once the implementer wires the
  testid via `add-data-testid`) and one new method,
  `click_refine_prompt(self, timeout=5000)`, mirroring the existing
  `click_previous()`/`click_next()` condition-wait-on-phase-change pattern
  (wait for `prompt_input` to become visible again, not the step indicator,
  since Refine Prompt returns to a DIFFERENT phase entirely rather than a
  different wizard step).
- **Part C's failure simulation is a DECLARED IMPROVISATION** — no product
  lever exists to force a real backend `generate_skill_draft` failure
  on-demand (unlike, say, a toolkit-credential failure scenario elsewhere in
  the suite that has a real invalid-credential path). `page.route()`
  interception matching exactly once (an `interceptCount`-gated handler, or
  Playwright's `page.route(url, handler, { times: 1 })` option) then falling
  through to the real network for the retry is the correct, minimal-fakery
  shape — it exercises the REAL `generateError` RTK-Query error state (the
  mutation genuinely rejects with a 500), not a hand-rolled DOM error
  injection. Same class of technique the codebase already uses for reading
  POST bodies via route interception (`ai_edit_skill_modal_page.py`'s
  `click_generate_and_wait_for_response()` docstring).
- **Part D's forced-click-on-disabled-button check (step 26) is a
  defense-in-depth assertion, not the primary proof.** The primary proof is
  simply reading `.is_enabled()` on `ai-edit-skill-generate-button` (steps
  21/25) — cheaper and equally conclusive given MUI's `disabled` prop
  genuinely disables the underlying `<button disabled>` element (confirmed:
  `force=True` click still triggers no `onClick`, since the browser itself
  suppresses the click event on a disabled native button before it reaches
  React). Keep both, but don't over-invest debugging time in the forced-click
  path if it ever proves flaky — the enabled-state assertion alone already
  fully covers the case's Pass/Fail criteria.
- Skill-creation reuse: `automation/pages/skill_form_page.py`'s
  `set_name`/`set_description`/`fill_instructions`/`save_and_wait_for_navigation`
  cover the § Preconditions throwaway-skill setup (same as ELITEA-2611).
- Test can share ONE seeded skill across Parts A-D (no state mutates it) —
  no need to re-seed between parts, unlike ELITEA-2611 which mutates via
  Save.
