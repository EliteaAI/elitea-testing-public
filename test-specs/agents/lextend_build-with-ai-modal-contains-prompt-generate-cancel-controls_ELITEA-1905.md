# Test Case: Build with AI opens GenerateAgentModal (prompt input, Generate, Cancel controls present)

> ⚠️ **UNDER REVIEW — 2026-08-14 fidelity audit. Do NOT reuse this AFS as a pattern.**
>
> This spec directs the implementer to **substitute the system under test** (mocking
> the generate-draft response) for a TMS case whose text never asks for simulation.
> Classification: **UNDER REVIEW** — mocked, and its TMS `automation_test_id` points at ELITEA-1915's failure-retry test — the mapping looks wrong; both need a human decision.
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
- **TMS ID**: ELITEA-1905
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/agents/build_with_ai/ELITEA-1905_build-with-ai-opens-generateagentmodal.md`
- **Linked Story**: none
- **Priority**: l2 (case priority: `high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project `Private` / `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via `VITE_DEV_TOKEN`; admin-equivalent role, per `.agents/profile.md` § Roles & sample users)
- **Analyst**: qa-engineer (Sage), analyst slot, batch #1298
- **Status**: extend-existing
- **Tracking issue**: EliteaAI/elitea-testing-public#1298 (batch tracking issue — no per-case board card)
- **Case-gate note**: source case frontmatter carries `status: draft` / `execution_type: manual` — consistent with the batch's other cases; no exclusion per `.agents/testing.md` § TMS case-gate (no excluded-status list defined for this project), so this run proceeded normally.

## Extension target

**Covering specs (both merged onto this batch's trunk, `tests/batch-1298-agents-build-with-ai`)**:

1. `automation/tests/ui/agents/test_agent_build_with_ai_role_visibility.py` —
   `TestAgentBuildWithAIButtonRoleVisibility.test_build_with_ai_button_visible_for_admin_role`
   (merged: commit `fe067f77`, covers ELITEA-1903). Its Step 3 explicitly
   asserts `modal.open_button.is_visible()`, the button's accessible text
   (`"Build with AI"`), calls `modal.open_modal()`, and explicitly asserts
   `modal.modal.is_visible()` with a message — this is a **first-class,
   standalone** assertion that clicking the button opens the
   `generate-agent-modal` dialog.
2. `automation/tests/ui/agents/test_agent_build_with_ai.py` —
   `TestAgentBuildWithAIGenerationFailureRetry.test_generation_failure_shows_error_and_allows_retry`
   (covers ELITEA-1915). Its Step 1 block opens the modal, then:
   - `assert not modal.is_generate_enabled()` while the prompt is empty
     (`generate_button.is_enabled()` — requires the button to be present
     and actionable)
   - `modal.fill_prompt(PROMPT_TEXT)` (`prompt_input.click()` +
     `.fill()` — Playwright auto-waits for visibility/actionability
     before either call, so this incidentally proves the prompt textarea
     is visible and accepts text)
   - `assert modal.get_prompt_value() == PROMPT_TEXT`
   - `assert modal.is_generate_enabled()` once non-empty (proves the
     Generate button transitions disabled → enabled in response to the
     prompt)
   - later (Step 5 of that test): `modal.generate_button.click()` — a
     real click, requiring visibility/actionability

Page object: `automation/pages/generate_agent_modal_page.py`
(`GenerateAgentModalPage`) + its shared base
`automation/pages/generate_entity_modal_page_base.py`
(`GenerateEntityModalPageBase`).

### Behavioural-overlap argument (what's already proven)

Between the two covering tests, ELITEA-1905's steps 1–4 are already
proven, live, on this batch's trunk:

- **Step 1** (New Agent creation page displayed, tab bar visible) —
  ELITEA-1903's Step 2 (`"/agents/create" in page.url and "viewMode=owner"
  in page.url` + `form_page.name_input.is_visible()`).
- **Step 2** (clicking the Magic Wand opens the modal) — ELITEA-1903's
  Step 3, a first-class, message-carrying `assert modal.modal.is_visible()`.
  This is a stronger proof than the ELITEA-1988 Skill sibling had
  available at analysis time (that case's covering tests only proved the
  open incidentally, via `open_modal()`'s internal wait) — for Agents, the
  explicit assertion already exists and needs no extension.
- **Step 3** (prompt input field present) — incidentally but functionally
  proven by ELITEA-1915's `fill_prompt()` + `get_prompt_value()`
  round-trip, which requires the textarea to be visible and interactable.
- **Step 4** (Generate button visible **and** — per the case's literal
  wording — enabled) — ELITEA-1915's `is_generate_enabled()` pair proves
  both states: disabled while empty, enabled once filled. This is a
  *stronger* proof than the case's own wording asks for (the case doesn't
  mention the empty→enabled transition at all — see § Known Defects /
  Case-Text Drift below for the exact mismatch).

This is enough overlap on **steps 1–4** that a fresh `test_*`
reimplementing "open modal → prompt input exists → Generate button
exists/enabled" would substantially duplicate the two existing tests'
own Step-1/Step-3 setup and assertions. Per Rule-6, that overlap routes
to `extend-existing`, not a new file.

### Gap assertion (what the covering specs do NOT cover — confirmed live this run)

**Cancel button presence/visibility (case step 5) is a genuine, complete
gap.** Grep of both `test_agent_build_with_ai.py` and
`test_agent_build_with_ai_role_visibility.py` confirms **zero**
occurrences of `cancel_button` anywhere in either file — the modal is
always closed via `close_button` (the X icon), never via Cancel.
`GenerateAgentModalPage.cancel_button` (`generate-agent-cancel-button`)
exists as a `LocatorDescriptor` but is never referenced from any test's
executed code path.

**Confirmed live this run**: navigating to `/agents/create?viewMode=owner`,
clicking the Magic Wand button (`data-testid="generate-agent-open-button"`,
confirmed via the resolved locator `page.getByTestId('generate-agent-open-button')`)
opened a `dialog [active]` with heading "Build with AI", containing:
- a `textbox` with accessible name "Describe your agent's goal, key tasks,
  and preferred tone or behavior." (the prompt input)
- a `button "Cancel"` — **the gap** — visible and clickable, never
  asserted by any existing test
- a `button "Generate Draft" [disabled]` (see § Known Defects / Case-Text
  Drift for the label + disabled-by-default mismatch vs the case's
  literal wording)

Additionally, while prompt-input and Generate-button visibility are both
*incidentally* exercised via real interactions (per the overlap argument
above), neither existing test contains a **standalone, message-carrying
assertion that they are visible** as this case's own Pass criterion
(steps 3–4) — they're proven only as a side effect of `fill_prompt()`'s
auto-wait and `is_generate_enabled()`'s state read. This AFS's gap
assertions make all three elements (prompt input, Generate button,
Cancel button) explicit, first-class assertions in one place.

## Preconditions
- `${TEST_USER}` is authenticated via the `auth_state` fixture (localhost
  `VITE_DEV_TOKEN` bypass — no Keycloak login form on localhost).
- Acting project: `${ELITEA_PROJECT_ID}` (Private, id `399`).
- The New Agent creation page (`${BASE_URL}/agents/create?viewMode=owner`)
  is reachable, with the "General" accordion section expanded by default
  — confirmed live.

## Test Data
### reuse-existing (no fixture creation/teardown needed)
- `${TEST_USER_EMAIL}` / `${TEST_USER_PASSWORD}` via `auth_state`.
- `${ELITEA_PROJECT_ID}` = `399` (Private).

No new test data is created or persisted in the product by this case's
own steps — no prompt is submitted by the gap assertions (they run before
any prompt text is entered, so `generate_button` is asserted `disabled`
per the confirmed-live default). See Cleanup.

## Test Steps

1. Log in as `${TEST_USER}` and navigate to `${BASE_URL}/agents/create?viewMode=owner`.
   - **Verify**: New Agent creation page displayed, tab bar visible —
     already asserted by ELITEA-1903's Step 2 (existing, covering).
2. Click the Magic Wand ("Build with AI") button in the tab bar
   (`data-testid="generate-agent-open-button"`).
   - **Verify**: the `generate-agent-modal` dialog opens — already
     asserted by ELITEA-1903's Step 3, a first-class
     `assert modal.modal.is_visible()` (existing, covering).
3. Inspect the opened dialog.
   - **Verify**: a natural-language prompt input (textarea) is visible —
     confirmed live, `data-testid="generate-agent-prompt-input"` present,
     accessible-named "Describe your agent's goal, key tasks, and
     preferred tone or behavior." **Gap — needs an explicit,
     standalone assertion** (currently only incidentally proven via
     ELITEA-1915's `fill_prompt()`/`get_prompt_value()`).
4. Inspect the opened dialog.
   - **Verify**: a Generate button is visible — confirmed live,
     `data-testid="generate-agent-submit-button"`, rendered `[disabled]`
     while the prompt field is empty (expected, confirmed via source —
     see § Known Defects / Case-Text Drift). **Gap — needs an explicit,
     standalone visibility assertion** (the enabled/disabled *transition*
     is already covered by ELITEA-1915's `is_generate_enabled()` pair;
     this AFS only adds the visibility check, consistent with what the
     modal renders before any prompt is typed).
5. Inspect the opened dialog.
   - **Verify**: a Cancel button is visible — confirmed live,
     `data-testid="generate-agent-cancel-button"` present and clickable.
     **This is the case's fully uncovered gap** — see § Extension target
     above.

## Expected Results
The GenerateAgentModal opens on click and displays: a prompt input field,
a Generate button (real label "Generate Draft" — see Case-Text Drift),
and a Cancel button. All three confirmed present and visible live via
accessibility snapshot. No console errors observed
(`browser_console_messages`, level=error → 0 results, both before and
after opening the modal).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Log in as admin/editor, navigate to New Agent creation | Page displayed, tab bar visible | ELITEA-1903's Step 2 (existing, merged to trunk) | `"/agents/create" in page.url and "viewMode=owner" in page.url` + `form_page.name_input.is_visible()` | already-covered (existing) |
| 2 Click Magic Wand button | GenerateAgentModal opens | ELITEA-1903's Step 3 (existing, merged to trunk) | first-class `assert modal.modal.is_visible()` with message | already-covered (existing) |
| 3 Verify prompt input field present | textarea visible | ELITEA-1915's `fill_prompt()`/`get_prompt_value()` (existing, incidental) | value round-trip proves interactability, but visibility is never independently asserted as this case's own criterion | **gap — new explicit assertion needed (§ Gap Assertions To Append #1)** |
| 4 Verify "Generate agent" button visible + enabled | button visible; case text says "enabled" | ELITEA-1915's `is_generate_enabled()` pair (existing, proves both disabled-then-enabled transition — stronger than case asks) | enabled/disabled *state transition* is asserted; visibility as a standalone check, and the case's real default (disabled while empty) are not | **gap — new explicit visibility assertion needed (§ Gap Assertions To Append #2); case-text drift on label + default-enabled claim, filed as #1315** |
| 5 Verify Cancel button present | button visible in modal | **gap — no existing test references `cancel_button` at all** | confirmed live this run (accessibility snapshot of the opened dialog) | **gap — new assertion needed (§ Gap Assertions To Append #3)** |

### Axis 2 — Analyst additions

- Confirmed the Generate button's real accessible text is "Generate
  Draft", not "Generate agent" as the case names it, and that it is
  `[disabled]` by default (`disabled={!description.trim()}` in
  `GenerateEntityModal.jsx:213`) rather than "enabled" as the case's
  Step 4 expected result states — *added: case-text drift, filed as
  EliteaAI/elitea-testing-public#1315 per the reverse-masking guard
  (live product behavior is correct/intentional; the case text is
  stale/imprecise).*
- Confirmed zero console errors/warnings across the whole open-modal
  interaction (`browser_console_messages`, level=error → 0 results) —
  *added: side-channel check, standard practice per this skill's
  methodology, not itself required by the case's Pass criteria.*
- Confirmed all three testids needed for the gap assertions
  (`generate-agent-prompt-input`, `generate-agent-submit-button`,
  `generate-agent-cancel-button`) already exist as
  `LocatorDescriptor` fields on `GenerateAgentModalPage` and were
  live-confirmed present in the DOM this run — *added: no
  `add-data-testid` work needed for this extension.*

## Gap Assertions To Append (implementer-facing)

Extend the **existing** Step 1 block of
`TestAgentBuildWithAIGenerationFailureRetry.test_generation_failure_shows_error_and_allows_retry`
in `automation/tests/ui/agents/test_agent_build_with_ai.py` — do **not**
create a new test file or a new page object; every locator already
exists on `GenerateAgentModalPage`. This is a small, surgical addition
(3 assertion lines), not a rewrite — insert immediately after the
existing `modal.open_modal()` call and *before* the existing
`assert not modal.is_generate_enabled()` line, so the gap assertions run
against the true pre-fill state (prompt empty, Generate disabled):

```python
with allure.step("Step 1 — Open modal, enter description"):
    list_page.navigate_to_create()
    modal.open_modal()

    # --- ELITEA-1905 gap fill: modal-contents assertions -------------
    # (modal-open itself is already covered by ELITEA-1903's dedicated
    # test — see test_agent_build_with_ai_role_visibility.py)
    assert modal.prompt_input.is_visible(), (
        "Natural-language prompt input should be visible in the Build with AI modal"
    )
    assert modal.generate_button.is_visible(), (
        "Generate button should be visible in the Build with AI modal"
    )
    assert modal.cancel_button.is_visible(), (
        "Cancel button should be visible in the Build with AI modal"
    )
    # -------------------------------------------------------------------

    assert not modal.is_generate_enabled(), (
        "Generate button should be disabled while the prompt is empty"
    )
    modal.fill_prompt(PROMPT_TEXT)
    ...
```

1. **Prompt-input visibility assertion** — `modal.prompt_input.is_visible()`.
   No new locator needed (`generate-agent-prompt-input` already exists).
2. **Generate-button visibility assertion** — `modal.generate_button.is_visible()`.
   No new locator needed (`generate-agent-submit-button` already exists).
   Do not assert enabled/disabled state here — the existing
   `is_generate_enabled()` pair immediately below already covers that
   transition for ELITEA-1915's purposes, and this is asserted while the
   button is still disabled (before any prompt is typed).
3. **Cancel-button visibility assertion** — `modal.cancel_button.is_visible()`.
   No new locator needed (`generate-agent-cancel-button` already exists)
   — this is the one handle **zero** existing tests reference at all.

Update the module docstring's "Covers" list to add ELITEA-1905 alongside
the existing ELITEA-1915/1907/1909/1911 entries, per this file's
established multi-case-coverage convention.

All three gap assertions require no new testids and no new page-object
locators — every handle already exists on `GenerateAgentModalPage`/
`GenerateEntityModalPageBase`.

## Cleanup
No product state is created by the gap assertions themselves — they run
before any prompt is entered or draft generated. The enclosing test
(`test_generation_failure_shows_error_and_allows_retry`) already owns its
own cleanup (mock teardown, no agent persisted since the create form is
never submitted to completion in that flow's failure/retry path — see
that test's own Cleanup for specifics; unchanged by this extension).

## Concrete Handles (discovered during exploration — all pre-existing)

| Element | Recommended Locator | Provenance |
|---|---|---|
| "Build with AI" open button | `generate-agent-open-button` (pre-existing on `GenerateAgentModalPage.open_button`) | on-main ✓ (confirmed via ELITEA-1903's merged test + live click this run) |
| Modal container | `generate-agent-modal` (pre-existing on `GenerateAgentModalPage.modal`) | on-main ✓ |
| Prompt textarea | `generate-agent-prompt-input` (pre-existing on `GenerateAgentModalPage.prompt_input`, confirmed live in the dialog's accessibility snapshot) | on-main ✓ |
| Generate button | `generate-agent-submit-button` (pre-existing on `GenerateAgentModalPage.generate_button`, confirmed live, `[disabled]` while prompt empty, label "Generate Draft") | on-main ✓ |
| Cancel button | `generate-agent-cancel-button` (pre-existing on `GenerateAgentModalPage.cancel_button`, confirmed live via accessibility snapshot — the case's uncovered gap) | on-main ✓ |
| Modal "Close" (X) button | `generate-agent-close-button` (pre-existing on `GenerateAgentModalPage.close_button`, used this run to close the modal cleanly) | on-main ✓ |

No new testids required for this extension — every handle needed for
the gap assertions already exists in `GenerateAgentModalPage` and its
base class, and all are confirmed present on `main` (this page object
and its testids predate this batch — verified via
`GenerateAgentModal.jsx` source, not merely the AFS's claim).

## Network Behavior
None specific to the gap assertions — opening the modal and inspecting
its static elements (prompt input, Generate, Cancel) triggers no network
call; the `generate_application_draft` endpoint only fires on clicking
Generate with a non-empty prompt, which the gap assertions never do
(they run before any prompt is typed). Confirmed live: only the page's
normal load-time GETs (`support_assistant`, `project_info`,
`configurations`, `permissions`, `tags`, `default_icons`, etc.) appeared
before and after opening the modal.

## Known Defects Found During Exploration
None — no product defect. **Case-text drift only**, filed as
EliteaAI/elitea-testing-public#1315: the case's Step 4 names the button
"Generate agent" (actual label: "Generate Draft") and states it is
"visible and enabled" (actual default: visible and **disabled** until a
non-empty prompt is entered — `disabled={!description.trim()}` in
`GenerateEntityModal.jsx:213`, an intentional guard against submitting
an empty prompt). Per the reverse-masking guard, the live product's
gating is correct; the case text is what needs updating.

## Blocked Steps
None. All 5 case steps were executed live this run against the real
local system (`http://localhost:5173`), either directly (steps 3–5) or
via triangulation against the two merged covering tests (steps 1–2).

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Extend the
  existing `test_generation_failure_shows_error_and_allows_retry` method
  in `automation/tests/ui/agents/test_agent_build_with_ai.py` — do not
  create a new file, do not duplicate `GenerateAgentModalPage`/
  `GenerateEntityModalPageBase` helpers, do not add new
  `LocatorDescriptor` fields (all three needed already exist).
- Suggested diff shape is given verbatim in § Gap Assertions To Append.
- No mocking/route interception needed for the gap assertions themselves
  — they run before any network call in that test's flow.
- No new marker needed; the extended test already carries
  `@pytest.mark.p2` + `@pytest.mark.regression` (case ELITEA-1915's own
  markers) — ELITEA-1905's own priority is `l2`/`high`, consistent with
  not needing an upgrade to `p1`.
