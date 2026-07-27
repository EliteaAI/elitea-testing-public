# Test Case: Clicking Build with AI opens the generation modal

## Metadata
- **TMS ID**: ELITEA-1988
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/skills/build_with_ai/ELITEA-1988_clicking-build-with-ai-opens-the-generation-modal.md`
- **Linked Story**: none
- **Priority**: l1 (case priority: `high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI dev server, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via `VITE_DEV_TOKEN`; admin/editor role, per `.agents/profile.md` § Roles & sample users)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: extend-existing
- **Case-gate note**: source case frontmatter carries `status: draft` /
  `execution_type: manual`. `.agents/testing.md` has no `TMS case-gate`
  section defining excluded statuses for this project (same recurring gap
  the ELITEA-1915/ELITEA-2001/ELITEA-1990/ELITEA-1989 AFS lineage already
  flagged) — per the skill's default, this run proceeded and
  fetched/executed the case.

## Extension target

**Covering spec/test file**:
`automation/tests/ui/skills/test_skill_build_with_ai.py` — all three
existing test methods exercise Step 1 of this case (open the modal, enter
a prompt) as their own setup:
- `TestSkillBuildWithAIGenerationFailureRetry.test_generation_failure_shows_error_and_allows_retry`
  (covers ELITEA-2001)
- `TestSkillBuildWithAIReviewFormEditableFields.test_review_form_fields_are_editable_before_creation`
  (covers ELITEA-1990)
- `TestSkillBuildWithAIReviewFormEditableFields.test_loading_state_shows_exact_text_and_review_form_has_no_extra_sections`
  (covers ELITEA-1989, extend-existing gap fill)

Page object: `automation/pages/generate_skill_modal_page.py`
(`GenerateSkillModalPage`) + its shared base
`automation/pages/generate_entity_modal_page_base.py`
(`GenerateEntityModalPageBase`).

### Behavioural-overlap argument (what's already proven)

All three existing tests call `list_page.navigate_to_create()` then
`modal.open_modal()` (which clicks the "Build with AI" button and does
`self.modal.wait_for(state="visible")`), then `modal.fill_prompt(...)`.
Two of the three also assert `is_generate_enabled()` transitions
false→true around the fill. This proves, incidentally:

1. The modal opens on click (via the `wait_for(state="visible")` inside
   `open_modal()` — a real wait, so it would fail loudly if the modal
   never appeared, but it is never asserted as its own explicit,
   message-carrying check).
2. The prompt input exists and accepts text (`fill_prompt()` +, in
   `test_review_form_fields_are_editable_before_creation`, an
   `is_generate_enabled()` read that depends on the textarea's value).
3. The Generate button exists and its enabled/disabled state responds to
   the prompt field (`is_generate_enabled()` assertions in two of the
   three tests).

This is enough overlap on **steps 3-5** of ELITEA-1988 that a fresh
`test_*` reimplementing "open modal → prompt input exists → Generate
button exists" would just duplicate the existing tests' Step 1 setup
almost verbatim. Per Rule-6, that overlap routes to `extend-existing`,
not a new file — confirmed live this run: opening the modal via
`page.getByTestId('generate-skill-open-button')` (identical selector
`GenerateSkillModalPage.open_button` already uses) reproduced the exact
dialog these tests already drive through, with the same three testids
(`generate-skill-prompt-input`, `generate-skill-submit-button`,
`generate-skill-cancel-button`) confirmed present in the DOM this run
(see § Concrete Handles).

### Gap assertion (what the covering spec does NOT cover — confirmed live this run)

One assertion from the case is **not** covered by any existing test, and
was confirmed live in this session as genuine, currently-untested product
behavior worth locking in:

**Cancel button presence/visibility (case step 6).** None of the three
existing tests ever reference, assert on, or click
`modal.cancel_button` — grep of
`automation/tests/ui/skills/test_skill_build_with_ai.py` confirms zero
occurrences of `cancel_button`. The `LocatorDescriptor` already exists on
`GenerateSkillModalPage` (`generate-skill-cancel-button`), but nothing in
the suite ever exercises or asserts its visibility. **Confirmed live this
run**: clicking `generate-skill-open-button` on `/skills/create` opened
the dialog, and `page.evaluate(...)` querying `[data-testid]` inside the
`[role="dialog"]` element returned exactly
`["generate-skill-close-button", "generate-skill-prompt-input",
"generate-skill-cancel-button", "generate-skill-submit-button"]` — the
Cancel button is present and visible in the DOM, but no test asserts it.

Additionally, while the modal-open, prompt-input, and Generate-button
existence are all *incidentally* exercised (per the overlap argument
above), none of the three existing tests contains a standalone,
message-carrying assertion that explicitly states "the modal is open"
or "the prompt input / Generate button are visible" as this case's own
Pass criterion (steps 3-5) — they're only implicit side effects of
`open_modal()`'s wait and `is_generate_enabled()`'s value-dependent
read. This AFS's gap assertions make all four elements (modal open,
prompt input, Generate button, Cancel button) explicit, first-class
assertions in one place, satisfying ELITEA-1988's stated intent as a
standalone smoke check rather than relying on it being "proven along the
way" by unrelated tests targeting different case IDs.

## Preconditions
- User is logged in to Elitea (localhost `auth_state`/`VITE_DEV_TOKEN`)
  with admin/editor role — confirmed live, the "Build with AI" button
  rendered and worked without a permission gate hitting in this run
  (same permission gate as ELITEA-1915/ELITEA-2001:
  `PERMISSIONS.applications.update` via `GenerateEntityButton.jsx`).
- The New Skill creation screen (`${BASE_URL}/skills/create`) is
  reachable, with the "General" accordion section expanded by default —
  confirmed live.

## Test Data

### reuse-existing (no fixture creation/teardown needed)
None — no prompt text is entered by this case (unlike ELITEA-1989/1990/2001).
The case only requires the modal to open and its three static elements
(prompt input, Generate button, Cancel button) to be visible; the Generate
button is expected to render `[disabled]` while the prompt is empty, which
is itself confirmed (not a blocker).

No test data is created or persisted in the product — no skill is ever
created, no prompt is submitted. See Cleanup.

## Test Steps

1. Log in as admin/editor and navigate to `${BASE_URL}/skills/create`.
   - **Verify**: the New Skill creation screen is displayed with the
     "General" accordion section expanded (confirmed live via snapshot —
     `tabpanel "New Skill"` visible with Name/Description/Tags fields and
     a "Build with AI" button in the General accordion header).
2. Click the **"Build with AI"** button
   (`data-testid="generate-skill-open-button"`, confirmed live — unlike
   the ELITEA-2001 AFS's earlier finding of zero testids, this button now
   carries the testid).
   - **Verify**: a `dialog` element becomes visible (confirmed live:
     `dialog [active]` with heading "Build with AI Close" appeared in the
     snapshot immediately after the click).
3. Inspect the opened dialog.
   - **Verify**: a natural-language prompt input (textarea) is visible —
     confirmed live, `data-testid="generate-skill-prompt-input"` present
     and accessible-named `"Describe what your skill should do, its
     inputs, and expected output format."`.
4. Inspect the opened dialog.
   - **Verify**: a **"Generate"** button is visible — confirmed live,
     `data-testid="generate-skill-submit-button"` present, rendered
     `[disabled]` while the prompt field is empty (expected — this case
     only requires visibility, not enabled state; enabled-state
     transition is already covered by ELITEA-1990/2001's tests).
5. Inspect the opened dialog.
   - **Verify**: a **"Cancel"** button is visible — confirmed live,
     `data-testid="generate-skill-cancel-button"` present and clickable.
     **This is the case's uncovered gap** — see § Extension target above.

## Expected Results
Matches the case's stated Pass criteria exactly, live-verified: clicking
"Build with AI" opens the modal, and the modal displays all three
required elements — a natural-language prompt input, a "Generate"
button, and a "Cancel" button. No step produced an unexpected result; no
console errors were observed (`browser_console_messages`,
level=error → 0 results, confirmed both before and after opening the
modal).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Log in as admin or editor | login successful, on platform home | fixture (`auth_state`) | localhost `auth_state` fixture skips login via `VITE_DEV_TOKEN` — pre-existing project convention | asserted (existing, via fixture) |
| 2 Navigate to New Skill creation screen | screen displayed | ELITEA-1990/2001/1989 tests' `list_page.navigate_to_create()` (existing) | existing tests already navigate there as Step-1 setup | already-covered (existing) |
| 3 Click "Build with AI" / Magic Wand button | modal opens | ELITEA-1990/2001/1989 tests' `modal.open_modal()` (existing, incidental) | `open_modal()`'s internal `wait_for(state="visible")` — a real wait but never a standalone, message-carrying assertion | **gap — new explicit assertion needed (§ Gap Assertions To Append #1)** |
| 4 Verify modal contains prompt input field | textarea visible | ELITEA-1990/2001/1989 tests' `fill_prompt()`/`get_prompt_value()` (existing, incidental) | value is read/written but visibility itself is never independently asserted as this case's own criterion | **gap — new explicit assertion needed (§ Gap Assertions To Append #2)** |
| 5 Verify modal contains "Generate" button | button visible | ELITEA-1990/2001/1989 tests' `is_generate_enabled()` (existing, incidental) | enabled/disabled *state* is asserted, but visibility as a standalone check is not | **gap — new explicit assertion needed (§ Gap Assertions To Append #3)** |
| 6 Verify modal contains "Cancel" button | button visible | **gap — no existing test references `cancel_button` at all** | confirmed live this run (`page.evaluate` testid inventory of the dialog) | **gap — new assertion needed (§ Gap Assertions To Append #4)** |

### Axis 2 — Analyst additions

- Documented that the "Build with AI" open button now carries a testid
  (`generate-skill-open-button`) live, contradicting the earlier
  ELITEA-2001 AFS's finding of zero testids on the Skill entry point —
  *added: the testid gap ELITEA-2001 flagged for `add-data-testid` has
  since been resolved; useful context so a future analyst doesn't
  re-file the same gap.*
- Confirmed zero console errors/warnings across the whole open-modal
  interaction (`browser_console_messages`, level=error → 0 results) —
  *added: side-channel check, not itself required by the case's Pass
  criteria, but standard practice per this skill's methodology.*
- Confirmed the Generate button's `[disabled]` state while the prompt is
  empty, matching the shared `GenerateEntityModal.jsx:215` behavior
  already documented by the ELITEA-2001/1990 AFS lineage — *added: not
  itself required by ELITEA-1988 (which only asks for visibility), but
  worth noting so the implementer doesn't mistake `[disabled]` for
  "not visible."*

## Gap Assertions To Append (implementer-facing)

Add these as a new, standalone test method in
`automation/tests/ui/skills/test_skill_build_with_ai.py` (not folded into
an existing method — unlike ELITEA-1989's gap fill, this case's gaps form
a coherent, independent smoke check rather than additions to another
case's flow). See § Automation Hints for the suggested method body.

1. **Modal-open assertion** — after `modal.open_modal()`, assert
   `modal.modal.is_visible()` explicitly, with a message. `open_modal()`
   already waits for this internally, but no test states it as its own
   Pass criterion.
2. **Prompt-input visibility assertion** — assert
   `modal.prompt_input.is_visible()`. No new locator needed
   (`generate-skill-prompt-input` already exists).
3. **Generate-button visibility assertion** — assert
   `modal.generate_button.is_visible()`. No new locator needed
   (`generate-skill-submit-button` already exists). Do not assert
   enabled/disabled state here — that's ELITEA-1990/2001's concern, not
   this case's (case step 5 only asks for visibility).
4. **Cancel-button visibility assertion** — assert
   `modal.cancel_button.is_visible()`. No new locator needed
   (`generate-skill-cancel-button` already exists) — this is the one
   handle **zero** existing tests reference at all.

All four gap assertions require no new testids and no new page-object
locators — every handle already exists on `GenerateSkillModalPage`/
`GenerateEntityModalPageBase`.

## Cleanup
1. No product state is created by this case's steps — no prompt is
   entered, no draft is generated, no skill is created. Closing the
   modal (via "Cancel", exercised live this run to leave a clean state)
   fully resets all local state (`step`, `description`, `draftData`,
   `isApproving`) and calls `resetGenerate()`, per source `handleClose`/
   `handleCancel` in `GenerateEntityModal.jsx` (identical mechanism to
   the ELITEA-2001/1990 AFS lineage).
2. For automated runs: no API/DB cleanup fixture is needed for this case
   — it never reaches a network call.

## Concrete Handles (discovered during exploration — all pre-existing)

| Element | Recommended Locator | Fallback |
|---|---|---|
| "Build with AI" open button | `generate-skill-open-button` (pre-existing on `GenerateSkillModalPage.open_button`, confirmed live via click + evaluate) | n/a — testid-only policy |
| Modal container | `generate-skill-modal` (pre-existing on `GenerateSkillModalPage.modal`, confirmed live: `document.querySelector('[data-testid="generate-skill-modal"]')` resolved to a `DIV` wrapping the dialog) | n/a |
| Prompt textarea | `generate-skill-prompt-input` (pre-existing on `GenerateSkillModalPage.prompt_input`, confirmed live in the dialog's testid inventory) | n/a |
| "Generate" button | `generate-skill-submit-button` (pre-existing on `GenerateSkillModalPage.generate_button`, confirmed live, `[disabled]` while prompt empty) | n/a |
| "Cancel" button | `generate-skill-cancel-button` (pre-existing on `GenerateSkillModalPage.cancel_button`, confirmed live — clicked to close the modal cleanly at the end of this run) | n/a |
| Modal "Close" (X) button | `generate-skill-close-button` (pre-existing on `GenerateSkillModalPage.close_button`, confirmed live in the dialog's testid inventory, not exercised this run) | n/a |

No new testids were required for this extension — every handle needed
for the gap assertions already exists in `GenerateSkillModalPage` and its
base class.

## Network Behavior
None specific to this case — opening the modal and inspecting its static
elements triggers no network call (the `generate_skill_draft` endpoint is
only called on clicking "Generate" with a non-empty prompt, which this
case never does). Confirmed live: only the page's normal load-time GETs
(`support_assistant`, `project_info`, `configurations`, `permissions`,
`tags`, `default_icons`, etc.) appeared in the console/network activity
before and after opening the modal — no additional request fired on the
click itself.

## Known Defects Found During Exploration
None. Live product behavior matches the case's Pass criteria exactly:
clicking "Build with AI" opens the modal, and the modal displays a
natural-language prompt input, a "Generate" button, and a "Cancel"
button — all three confirmed present and visible via both accessibility
snapshot and DOM testid inventory.

## Blocked Steps
None. All 6 case steps were executed live this run against the real
local system (`http://localhost:5173`).

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Add a new,
  narrowly-scoped test method to the existing
  `automation/tests/ui/skills/test_skill_build_with_ai.py` (do not create
  a new file, do not duplicate `GenerateSkillModalPage`/
  `GenerateEntityModalPageBase` helpers) — e.g.
  `test_build_with_ai_opens_modal_with_expected_elements`, a standalone
  P1 smoke-style test distinct from the P2 flows already in the file.
- Suggested new test body (all locators/methods already exist, zero new
  `LocatorDescriptor` fields needed):
  ```python
  def test_build_with_ai_opens_modal_with_expected_elements(self, page):
      list_page = SkillsListPage(page)
      modal = GenerateSkillModalPage(page)

      with allure.step("Step 1-2 — Navigate to New Skill screen, click Build with AI"):
          list_page.navigate_to_create()
          modal.open_modal()
          assert modal.modal.is_visible(), (
              "Build with AI modal should be open after clicking the button"
          )

      with allure.step("Step 3 — Verify prompt input is visible"):
          assert modal.prompt_input.is_visible(), (
              "Natural-language prompt input should be visible in the modal"
          )

      with allure.step("Step 4 — Verify Generate button is visible"):
          assert modal.generate_button.is_visible(), (
              "Generate button should be visible in the modal"
          )

      with allure.step("Step 5 — Verify Cancel button is visible"):
          assert modal.cancel_button.is_visible(), (
              "Cancel button should be visible in the modal"
          )
  ```
- No mocking/route interception needed — this case never reaches the
  network layer, unlike its ELITEA-2001/1990/1989 siblings in the same
  file.
- Mark `@pytest.mark.p1` (case priority: high) and
  `@pytest.mark.smoke` in addition to `@pytest.mark.regression`, since
  this is exactly the kind of fast, no-network smoke assertion the
  `smoke` marker exists for, per `.agents/testing.md` § Markers.
