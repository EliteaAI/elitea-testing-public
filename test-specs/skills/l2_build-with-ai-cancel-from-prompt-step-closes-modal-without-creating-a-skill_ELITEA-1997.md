# Test Case: Build with AI — Cancel from prompt step closes modal without creating a Skill

## Metadata
- **TMS ID**: ELITEA-1997
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/skills/ELITEA-1997_build-with-ai-cancel-closes-the-modal-without-creating-a-skill.md`
  (path inferred from the intake snapshot at
  `.agents/automation/skills-remaining-w5/cases/ELITEA-1997.md`; module `skills`, tags `[automated:UI:regression, feat:skills]`)
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project `Private` / id `399`
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via `VITE_DEV_TOKEN`; admin-equivalent role, per `.agents/profile.md` § Roles & sample users)
- **Analyst**: qa-engineer (Sage), analyst slot, batch skills-remaining-w5, cluster dispatch with ELITEA-1998
- **Status**: ready-for-automation
- **Tracking issue**: batch tracking issue for skills-remaining-w5 (no per-case board card)
- **Case-gate note**: source case frontmatter carries `status: draft` / `execution_type: manual` — no exclusion per `.agents/testing.md` § TMS case-gate, so this run proceeded normally.

## Triangulation vs the Skill entity's existing Build-with-AI coverage (why this is `ready-for-automation`, not `extend-existing`)

`GenerateSkillModalPage.cancel_button` (`generate-skill-cancel-button`) is referenced exactly once
elsewhere in the suite — `automation/tests/ui/skills/test_skill_build_with_ai.py`,
`TestSkillBuildWithAIModalElements`, line ~738:

```python
assert modal.cancel_button.is_visible(), (
    "Cancel button should be visible in the Build with AI modal"
)
```

(confirmed via `grep -n "cancel_button" automation/tests/ui/skills/test_skill_build_with_ai.py`
— exactly this one hit, `.is_visible()` only, never `.click()`ed anywhere in the file). That case
(ELITEA-1988's gap-fill) proved the Cancel button **exists**; it never exercised what clicking it
**does**, which is this case's entire objective. Identical triangulation shape to the Agent-entity
sibling ELITEA-1917 (`test-specs/agents/l2_build-with-ai-cancel-from-prompt-step-closes-modal-without-creating-agent_ELITEA-1917.md`)
against the Agent's own `TestAgentBuildWithAIGenerationFailureRetry` visibility-only assertion.

**Why this can't be spliced into `TestSkillBuildWithAIModalElements` (extend-existing doesn't
fit):** that test's Cancel-visibility assertion sits inline with several other static-elements
checks (prompt input, Generate button, etc.) in one test method; clicking Cancel would close the
modal and terminate any assertions that method makes afterward about the modal's other elements.
This routes to `ready-for-automation` as a new, standalone test class — reusing the existing
`SkillsListPage`/`GenerateSkillModalPage`/`SkillFormPage` handles (no new page object, no new
locators; see § Concrete Handles).

## Preconditions
- `${TEST_USER}` is authenticated via the `auth_state` fixture (localhost `VITE_DEV_TOKEN`
  bypass — no Keycloak login form on localhost).
- The New Skill creation page (`${BASE_URL}/skills/create`) is reachable, with the "General"
  accordion section expanded by default and the Name/Description fields empty — confirmed live
  (initial page-load snapshot showed both fields with no value, via `skill-name-input-field` /
  `skill-description-input-field`).

## Test Data
### reuse-existing (no fixture creation/teardown needed)
- `${TEST_USER_EMAIL}` / `${TEST_USER_PASSWORD}` via `auth_state`.
- `${ELITEA_PROJECT_ID}` (whichever project is active — the flow is project-agnostic; this run
  used project `Private`/`399`).
- Prompt text: any non-empty natural-language string (case's Test Data says "Any valid prompt
  text"). Confirmed live with: `"A skill that converts markdown tables into CSV for ELITEA-1997
  cancel-from-prompt verification."`

No new test data is created or persisted in the product by this case's steps — Cancel is clicked
before Generate, so no draft is ever requested and no skill is ever created. See Cleanup.

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`, click the "Build with AI" button
   (`data-testid="generate-skill-open-button"`, rendered as the accordion-header action next to
   "General" in `CreateSkillForm`'s equivalent — confirmed live: the button sits directly after
   the Name/Description/Tags fields inside the General accordion region, before the Instructions
   accordion).
   - **Verify**: the `generate-skill-modal` dialog opens, showing heading "Build with AI", a
     prompt textarea, a "Cancel" button, and a disabled "Generate Draft" button — confirmed live
     via accessibility snapshot.
2. Enter a natural-language description into the prompt textarea
   (`data-testid="generate-skill-prompt-input"`) **without clicking Generate**.
   - **Verify**: the textarea contains the entered text — confirmed live; the "Generate Draft"
     button transitions from disabled to enabled (confirmed live via a second snapshot of the
     dialog after typing).
3. Click "Cancel" (`data-testid="generate-skill-cancel-button"`) **without generating**.
   - **Verify**: the Cancel action is triggered — confirmed live, the click resolves
     synchronously with no confirmation dialog / "discard changes?" prompt — none appeared.
4. Verify the modal closes.
   - **Verify**: the dialog (`generate-skill-modal`) is no longer present in the DOM — confirmed
     live via accessibility snapshot immediately after the Cancel click: the `dialog` element is
     gone entirely (not merely hidden/inert), the page returns to the plain "New Skill" tab view.
5. Verify the New Skill form is still shown with empty fields (no auto-population from the
   cancelled draft).
   - **Verify**: `skill-name-input-field` and `skill-description-input-field` are both empty
     (`.value === ""`, confirmed live via `page.evaluate()` reading both inputs directly
     immediately after Cancel) — both were empty before opening the modal and remained empty
     after Cancel; the modal's prompt text was never written into the New Skill form's own
     fields — they are entirely separate inputs (same finding class as the Agent-entity sibling
     ELITEA-1917).
6. Navigate to the Skills list and verify no new Skill was created.
   - **Verify (primary, deterministic)**: no `POST .../elitea_core/skills/prompt_lib/**` (the
     skill CREATE call) and no `POST .../elitea_core/generate_skill_draft/**` (the generate-draft
     call) fired at any point during this flow — confirmed live via `browser_network_requests`
     filtered to `skill`: the only skill-related request across the entire
     open→type→cancel sequence was a benign, pre-existing `GET
     .../elitea_core/upload_skill_icon/prompt_lib/399` (icon-picker list, unrelated to this
     flow). **Zero** matches for either the create or generate-draft routes.
   - **Verify (secondary, case-literal)**: navigating to `${BASE_URL}/skills/all` and reading the
     20 visible `entity-card-name` skill-card names shows no card corresponding to this case's
     prompt text — confirmed live (`page.evaluate()` reading all `entity-card-name` text
     content). Since Cancel is clicked before Generate, no draft is ever requested, so there is
     no generated name to search the Skills list for by name — the network-absence check is the
     only sound way to prove "no skill was created"; the list-read is a redundant, case-literal
     echo of an unchanged set.

## Expected Results
Clicking Cancel on the GenerateSkillModal's prompt-input step closes the modal (dialog removed
from the DOM, not merely hidden), leaves the New Skill creation form in its original
empty/untouched state, and creates no skill — neither the generate-draft call nor the
create-skill call ever fires. No console errors observed (`browser_console_messages`, level=error
→ 0 results, across open → type → cancel).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open the Build with AI modal | The modal opens with the prompt input field | AFS Step 1 | `modal.open_modal()` (existing `GenerateEntityModalPageBase` helper); accessibility snapshot confirms dialog + prompt textarea + Cancel + disabled Generate Draft | ready-for-automation (new test) |
| 2 Enter a natural-language description | The input field accepts and displays the description | AFS Step 2 | `modal.fill_prompt(...)` / `modal.get_prompt_value() == PROMPT_TEXT` (existing helpers); Generate Draft transitions disabled→enabled, confirmed live | ready-for-automation (new test) |
| 3 Click "Cancel" | The modal closes | AFS Step 3 | `modal.cancel_button.click()` — **the case's core, previously-unexercised gap**; confirmed live (no confirmation dialog intervenes) | ready-for-automation (new test) — first ever `.click()` on `cancel_button` in `tests/ui/skills/` |
| 4 Verify the modal closes | The modal is no longer visible | AFS Step 4 | `modal.modal.wait_for(state="hidden", timeout=...)` (DOM-absence check) — confirmed live: dialog fully removed | ready-for-automation (new test) |
| 5 Verify the New Skill form is still shown with empty fields | The New Skill creation form is displayed with empty fields | AFS Step 5 | `SkillFormPage.name_input_field.input_value() == ""` and `.description_input_field.input_value() == ""` (existing `SkillFormPage` locators, confirmed live both before-open and after-cancel) | ready-for-automation (new test) |
| 6 Navigate to the Skills list and verify no new Skill was created | No new Skill entry appears in the Skills list | AFS Step 6 | Primary: assert no POST fired to the skill CREATE route (`/elitea_core/skills/prompt_lib/`) or generate-draft route (`/elitea_core/generate_skill_draft/`) — via `capture_requests_matching()`. Secondary: `SkillsListPage.get_skill_card_names()` set unchanged before vs after | ready-for-automation (new test) — network-absence is the deterministic proof; the list-navigation is the case-literal echo |

### Axis 2 — Analyst additions

- Confirmed the "Build with AI" button lives inside the "General" accordion region, positioned
  after the Name/Description/Tags fields and before the Instructions accordion — *added:
  disambiguates its DOM position for this entity, mirroring the Agent-entity disambiguation
  ELITEA-1917's AFS already documented for `agent-form-icon-button` (no equivalent adjacent
  icon-picker distraction exists on the Skill create form, so no analogous mis-click risk here).*
- Confirmed zero console errors across the full open→type→cancel sequence
  (`browser_console_messages`, level=error → 0 results) — *added: side-channel check, standard
  practice per this skill's methodology, not itself required by the case's Pass criteria.*
- Confirmed clicking Cancel produces no confirmation/"discard changes?" interstitial — the modal
  closes on the first click — *added: a plausible UX pattern the case text doesn't rule out,
  ruled out live, consistent with the Agent-entity sibling's identical finding.*
- Confirmed all testids needed (`generate-skill-open-button`, `generate-skill-prompt-input`,
  `generate-skill-cancel-button`) plus the New Skill form's own `skill-name-input-field` /
  `skill-description-input-field` and the Skills-list `entity-card-name` collection locator
  already exist as `LocatorDescriptor` fields on `GenerateSkillModalPage`/`SkillFormPage`/
  `SkillsListPage` and were live-confirmed present in the DOM this run — *added: no
  `add-data-testid` work needed for this case.*
- **Note on `SkillFormPage` field-name overlap**: `SkillFormPage` also exposes a plain
  `name_input`/`description_input` pair (`skill-name-input`/`skill-description-input`, the MUI
  wrapper elements) distinct from `name_input_field`/`description_input_field` (the real
  `<input>`/`<textarea>` elements, testid'd for ELITEA-1990's edit-flow needs) — this case reads
  the `_field` variants directly (matching the pattern `SkillFormPage.get_review_name()`'s
  siblings already use for the modal's own review fields), since those resolve to the actual DOM
  nodes whose `.value` this case's Pass criteria depend on.

## Cleanup
No product state is created by this case's own steps — Cancel is clicked before Generate, so no
draft is requested and no skill is created. No `SkillAPI.delete_skill(...)` teardown is needed.

## Concrete Handles (discovered during exploration — all pre-existing)

| Element | Recommended Locator | Provenance |
|---|---|---|
| "Build with AI" open button | `generate-skill-open-button` (pre-existing on `GenerateSkillModalPage.open_button`) | on-main ✓ (confirmed via live click this run) |
| Modal container | `generate-skill-modal` (pre-existing on `GenerateSkillModalPage.modal`) | on-main ✓ |
| Prompt textarea | `generate-skill-prompt-input` (pre-existing on `GenerateSkillModalPage.prompt_input`) | on-main ✓ |
| Cancel button | `generate-skill-cancel-button` (pre-existing on `GenerateSkillModalPage.cancel_button`) — **this case is the first to `.click()` it; ELITEA-1988 only asserted `.is_visible()`** | on-main ✓ |
| New Skill form Name field (real `<input>`) | `skill-name-input-field` (pre-existing on `SkillFormPage.name_input_field`) | on-main ✓ (confirmed empty both before-open and after-cancel) |
| New Skill form Description field (real `<textarea>`) | `skill-description-input-field` (pre-existing on `SkillFormPage.description_input_field`) | on-main ✓ (confirmed empty both before-open and after-cancel) |
| Skills list card name | `entity-card-name` (pre-existing on `SkillsListPage`, via `get_skill_card_names()`) | on-main ✓ |
| Skill CREATE route (substring for negative assertion) | `/elitea_core/skills/prompt_lib/` (POST) — used directly with `capture_requests_matching()`, no named constant on `GenerateSkillModalPage` (unlike the Agent page object's `CREATE_APPLICATION_ROUTE`) | on-main ✓ — used here only for a **negative** (no-call) network assertion |
| Generate-draft route | `**/elitea_core/generate_skill_draft/**` (pre-existing constant `GenerateSkillModalPage.GENERATE_DRAFT_ROUTE`; substring form `/elitea_core/generate_skill_draft/` for `capture_requests_matching()`) | on-main ✓ — same negative-assertion use |

No new testids required. No new page-object locators required. Every handle needed already
exists in `GenerateSkillModalPage`, `SkillFormPage`, and `SkillsListPage`.

## Network Behavior
Confirmed live: across the entire open → type-prompt → click-Cancel sequence, **zero** requests
matched either `/elitea_core/generate_skill_draft/` or `/elitea_core/skills/prompt_lib/` (POST).
Filtering `browser_network_requests` to `skill` returned exactly one match — a benign, pre-existing
`GET /elitea_core/upload_skill_icon/prompt_lib/399?limit=20&skip=0 => 200` (icon-picker list,
fires on every visit to the create-skill page regardless of Build-with-AI interaction, confirmed
unrelated). Only the page's normal load-time GETs otherwise, consistent with the Agent-entity
sibling ELITEA-1917's Network Behavior notes for the equivalent screen.

## Known Defects Found During Exploration
None. Product behavior matches the case's stated intent exactly: Cancel closes the modal, the
New Skill form is unaffected, and no skill is created. No case-text drift found for THIS case
(contrast with its cluster sibling ELITEA-1998, which does have case-text drift — see that AFS).

## Blocked Steps
None. All 6 case elements were executed live this run against the real local system
(`http://localhost:5173`).

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Add a new, standalone test class to
  `automation/tests/ui/skills/test_skill_build_with_ai.py` — e.g.
  `TestSkillBuildWithAICancelFromPromptStep` (mirrors the Agent-entity sibling's
  `TestAgentBuildWithAICancelFromPromptStep` naming, ELITEA-1917). Same file, same imports, same
  fixtures already used by the file's other tests (`SkillsListPage`, `GenerateSkillModalPage`,
  `SkillFormPage`), no new page object needed.
- No new `LocatorDescriptor` fields needed — `cancel_button` already exists; this case is simply
  its first real `.click()`.
- Reuse `BasePage.capture_requests_matching()` / `capture_console_errors()` (existing
  infrastructure, already used elsewhere in this file's `TestSkillBuildWithAIBackToPromptFromReviewStep`
  class) for the negative network-call assertions and the console-error check.
- Suggested flow (illustrative, not prescriptive — the implementer owns exact structure/step
  numbering per this file's `allure.step` convention):
  ```python
  with allure.step("Step 1 — Open modal, enter description"):
      skills_list_page.navigate_to_create()
      modal.open_modal()
      modal.fill_prompt(CANCEL_PROMPT_TEXT)
      assert modal.get_prompt_value() == CANCEL_PROMPT_TEXT
      assert modal.is_generate_enabled()

  with allure.step("Step 2 — Click Cancel without generating"):
      create_requests = form_page.capture_requests_matching(
          "/elitea_core/skills/prompt_lib/", method="POST"
      )
      draft_requests = form_page.capture_requests_matching(
          "/elitea_core/generate_skill_draft/"
      )
      console_capture = form_page.capture_console_errors()
      modal.cancel_button.click()

  with allure.step("Step 3 — Verify the modal closes"):
      modal.modal.wait_for(state="hidden", timeout=NAVIGATION_TIMEOUT)

  with allure.step("Step 4 — Verify the New Skill form is untouched"):
      assert form_page.name_input_field.input_value() == "", (
          "New Skill form's Name field should remain empty after cancelling Build with AI"
      )
      assert form_page.description_input_field.input_value() == "", (
          "New Skill form's Description field should remain empty after cancelling Build with AI"
      )

  with allure.step("Step 5 — Verify no Skill was created"):
      assert not create_requests, f"got: {list(create_requests)}"
      assert not draft_requests, f"got: {list(draft_requests)}"
      assert not console_capture, f"got: {list(console_capture)}"
      create_requests.stop()
      draft_requests.stop()
      console_capture.stop()

  with allure.step("Step 6 — Verify the Skills list is unchanged"):
      skills_list_page.navigate()
      names_after = skills_list_page.get_skill_card_names()
      # compare against a names-before snapshot captured prior to Step 1
  ```
- Timeout constants: reuse the file's existing `NAVIGATION_TIMEOUT` (15000) for the modal-hidden
  wait; no new constant needed.
- No mocking/route interception needed — every assertion in this case is against the real,
  unmocked flow (no draft is ever requested, so there is nothing to mock).
- Marker: `@pytest.mark.p2` + `@pytest.mark.regression`, consistent with this file's other
  Build-with-AI cases and this case's own `l2`/`medium` priority.
