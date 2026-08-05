# Test Case: Skill draft is generated from a natural-language description

## Metadata
- **TMS ID**: ELITEA-1989
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/skills/build_with_ai/ELITEA-1989_skill-draft-generated-from-natural-language-description.md`
- **Priority**: l1 (case priority: `high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (analyst slot)
- **Status**: extend-existing
- **Case-gate note**: source case frontmatter carries `status: draft` /
  `execution_type: manual`. `.agents/testing.md` has no `TMS case-gate`
  section defining excluded statuses for this project (same recurring gap
  the ELITEA-1915/ELITEA-2001/ELITEA-1990 AFS lineage already flagged) —
  per the skill's default, this run proceeded and fetched/executed the
  case.

## Extension target

**Covering spec/test file**:
`automation/tests/ui/skills/test_skill_build_with_ai.py` —
`TestSkillBuildWithAIReviewFormEditableFields.test_review_form_fields_are_editable_before_creation`
(covers ELITEA-1990, spec `test-specs/skills/l2_generated-skill-draft-fields-are-editable-before-creation_ELITEA-1990.md`),
with a secondary contribution from
`TestSkillBuildWithAIGenerationFailureRetry.test_generation_failure_shows_error_and_allows_retry`
(covers ELITEA-2001, spec
`test-specs/skills/l2_build-with-ai-generation-failure-retry_ELITEA-2001.md`).

Page object: `automation/pages/generate_skill_modal_page.py`
(`GenerateSkillModalPage`) + its shared base
`automation/pages/generate_entity_modal_page_base.py`
(`GenerateEntityModalPageBase`).

### Behavioural-overlap argument (what's already proven)

ELITEA-1989's happy-path generation flow is, structurally, the same flow
ELITEA-1990's test already drives end-to-end:

1. **Open modal / enter prompt / Generate button enablement**
   (case steps 1-2) — proven live by ELITEA-1990's Step 1
   (`modal.open_modal()`, `modal.fill_prompt(...)`,
   `is_generate_enabled()` assertions before/after fill).
2. **Click Generate; generation completes; modal transitions to a
   review/edit form with generated Name, Description, Instructions**
   (case steps 3, 5, 6) — proven live by ELITEA-1990's Step 2
   (`click_generate_and_wait_for_response()` asserts `200`,
   `wait_for_review_form()`, then `get_review_name()` /
   `get_review_description()` / `get_review_instructions()` asserted
   against the generated draft payload).
3. **A loading state is shown during generation** (case step 4, partial)
   — the *presence/visibility* of the loading state is already exercised
   by ELITEA-2001's Step 5/6 (`modal.wait_for_loading_visible(...)` on the
   retry path) and implicitly by `GenerateEntityModalPageBase`'s
   `mock_generate_success()`/`mock_generate_failure()` helpers, which
   both insert an artificial `delay_ms` specifically so the loading state
   is reliably observable mid-flight.

This is enough overlap that a fresh `.spec.ts`/`test_*` reimplementing the
whole open→fill→generate→review-form flow would just duplicate
ELITEA-1990's Step 1-2 almost verbatim. Per Rule-6, that overlap routes to
`extend-existing`, not a new file.

### Gap assertions (what the covering spec does NOT cover — confirmed live this run)

Two assertions from the case are **not** covered by either existing test,
and were confirmed live in this session as genuine product behavior worth
locking in:

1. **Loading-state exact text.** Neither ELITEA-1990's nor ELITEA-2001's
   test asserts the loading indicator's *text content* — only its
   visibility (`wait_for_loading_visible()`/`wait_for_input_step()` wait
   on the `generate-skill-loading-indicator` / `generate-skill-submit-button`
   testids' visible/hidden state, never read `.text_content()`). Case step
   4 requires the specific string `"Generating skill draft..."`.
   **Confirmed live this run**: clicking Generate against the real
   (unmocked) DEV backend rendered exactly `Generating skill draft...`
   inside the `generate-skill-loading-indicator`-testid element (visible
   in the interim snapshot between the click and the review-form
   transition — see raw exploration notes below) before the modal
   transitioned to the review form once
   `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/399` resolved
   `200`.
2. **Absence of suggested tools/agents/pipelines/toolkits/MCPs/resources
   sections on the review form.** Neither existing test asserts a
   *negative* — that no such section renders. Case step 7 requires this
   explicitly. **Confirmed live this run**: the post-generation review
   form (see raw exploration snapshot) contains exactly three fields —
   `Name` (textbox `github-pr-review`), `Description` (textbox, generated
   text), `Instructions` (textbox, generated text) — plus the
   `Back to prompt` / `Create Skill` action buttons. No additional
   section, heading, list, chip-group, or control referencing tools,
   agents, pipelines, toolkits, MCPs, or resources appeared anywhere in
   the dialog at any point in the flow (input step or review step). Zero
   console errors/warnings were observed across the whole interaction
   (`browser_console_messages`, onlyErrors=true → 0 results).

## Preconditions
- User is logged in to Elitea (localhost `auth_state`/`VITE_DEV_TOKEN`)
  with admin/editor role — confirmed live, the "Build with AI" button
  rendered and worked without a permission gate hitting in this run.
- The Build with AI modal is reachable from `/skills/create`'s General
  accordion section header — confirmed live (`generate-skill-open-button`).

## Test Data

### reuse-existing
None — no pre-existing environment fixture (MCP/toolkit/credential/agent)
is read or attached by this case. Only precondition is project selection
(`Private`, id `399`), already covered under § Preconditions.

### generate-per-test
- Natural-language prompt (per case Test Data table): `"A skill that helps
  write concise GitHub PR review comments"`. Confirmed live this run to
  produce a real generated draft (name `github-pr-review`, a generated
  description and Markdown-formatted instructions) via the real DEV
  backend — any valid non-empty prompt satisfies the case; content itself
  isn't asserted beyond "the three fields are populated."
- No skill is created/persisted by this case — the case's Expected Final
  State stops at the review form being shown correctly; it does not click
  "Create Skill." No cleanup is required for the gap assertions this
  extension adds (nothing is created).

### generate-shared-with-cleanup
None.

## Gap Assertions To Append (implementer-facing)

Add these as new assertions inside
`TestSkillBuildWithAIReviewFormEditableFields.test_review_form_fields_are_editable_before_creation`
(ELITEA-1990's test), immediately around its existing Step 2 (generate →
`wait_for_review_form()`), OR as a small new test method in the same class
if the implementer prefers not to grow the existing method further — either
is acceptable; the assertions themselves are what's missing, not a specific
method boundary:

1. **Loading-state text assertion** — right after
   `click_generate_and_wait_for_response()` is invoked (or, if the mock's
   `delay_ms` resolves too fast to observe reliably in the same request/
   response context-manager pattern ELITEA-1990 uses, capture it the way
   ELITEA-2001's retry step does: assert visibility via
   `modal.wait_for_loading_visible()` *before* awaiting the response, then
   read `modal.loading_indicator.text_content()` and assert it equals
   `"Generating skill draft..."`. `GenerateEntityModalPageBase` already
   exposes `wait_for_loading_visible()`/`wait_for_loading_hidden()` and the
   `loading_indicator` `LocatorDescriptor` (`generate-skill-loading-indicator`)
   — no new locator or helper needed, just a new
   `.text_content()`/`==` assertion. Keep `mock_generate_success()`'s
   `delay_ms` (default 300ms, already used by both existing tests) so the
   loading state is reliably observable — this is exactly why that
   artificial delay exists in the shared base.

2. **Absence-of-extra-sections assertion** — once `wait_for_review_form()`
   resolves, add a negative assertion that only the three known review-form
   fields exist and no tools/agents/pipelines/toolkits/MCPs/resources
   section is present. Recommended approach: take an accessibility
   snapshot scope to the dialog (`page.get_by_role("dialog")` /
   equivalent) and assert none of the following case-forbidden substrings
   appear in its text content: `"tool"`, `"agent"`, `"pipeline"`,
   `"toolkit"`, `"MCP"`, `"resource"` (case-insensitive, word-boundary
   match to avoid false positives against "Instructions" etc. — none of
   the three real field labels contain these substrings, so a naive
   substring check is safe here). Simpler alternative matching this
   project's existing style (see ELITEA-1990's page object pattern):
   assert the review-form's field-holding container has exactly the three
   known `LocatorDescriptor`s (`review_name_input`,
   `review_description_input`, `review_instructions_input`) and count the
   dialog's direct field-group children equals 3 — whichever the
   implementer finds less brittle against future MUI DOM churn.

3. These two gap assertions require no new testids and no new page-object
   locators — `generate-skill-loading-indicator` and the three
   `review_*_input` fields already exist in `GenerateSkillModalPage`/
   `GenerateEntityModalPageBase` (see § Extension target).

## Expected Results
Matches the case's stated Pass criteria: the loading state displays the
exact text "Generating skill draft..." during generation, and the
resulting review form shows only Name, Description, and Instructions —
no additional tools/agents/pipelines/toolkits/MCPs/resources section.
Both confirmed live this run against the real (unmocked) DEV backend, with
zero console errors.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open the Build with AI modal | modal opens with prompt input visible | ELITEA-1990 test Step 1 (existing) | `modal.open_modal()` waits for `generate-skill-modal` visible | asserted (existing) |
| 2 Enter natural-language description | input field accepts/displays it | ELITEA-1990 test Step 1 (existing) | `modal.fill_prompt(...)` + `get_prompt_value()` equality (existing pattern; ELITEA-1990 doesn't currently read back the value but the helper supports it) | asserted (existing, via equivalent helper) |
| 3 Click "Generate" | generation initiated | ELITEA-1990 test Step 2 (existing) | `click_generate_and_wait_for_response()` | asserted (existing) |
| 4 Verify loading state shows "Generating skill draft..." | modal displays that exact text | **gap** | confirmed live this run (raw exploration); not yet a test assertion | **gap — new assertion needed (§ Gap Assertions To Append #1)** |
| 5 Wait for generation to complete | generation completes, modal transitions | ELITEA-1990 test Step 2 (existing) | `wait_for_review_form()` | asserted (existing) |
| 6 Verify review/edit form shows generated Name, Description, Instructions | review form shown, fields populated | ELITEA-1990 test Step 2 (existing) | `get_review_name/description/instructions()` equality asserts | asserted (existing) |
| 7 Verify no suggested tools/agents/pipelines/toolkits/MCPs/resources section shown | no such section displayed | **gap** | confirmed live this run (raw exploration snapshot: only 3 fields + 2 action buttons in dialog) | **gap — new assertion needed (§ Gap Assertions To Append #2)** |

### Axis 2 — Analyst additions

- Documented the exact testid already wired for the loading indicator
  (`generate-skill-loading-indicator`, per `GenerateSkillModalPage`) so the
  implementer doesn't need to re-discover it — *added: saves a
  `add-data-testid` round-trip, the locator already exists and just isn't
  asserted on for its text content.*
- Documented that this case creates no persisted skill (unlike ELITEA-1990,
  which clicks "Create Skill" and cleans up via `SkillAPI.delete_skill()`)
  — *added: implementer should not add unnecessary cleanup for the gap
  assertions; the case's own Expected Final State stops at the review-form
  step.*
- Noted the real (unmocked) DEV backend resolved in well under a second in
  this run, so the artificial `delay_ms` in `mock_generate_success()` (used
  by the *existing* ELITEA-1990 test, which does mock) remains necessary
  for the loading-state assertion to be reliably observable in CI — *added:
  flags a flake risk if the gap assertion is added without a mock/delay.*

## Cleanup
None required — no skill is created or persisted; the case (and this
extension) stop at the review-form step.

## Concrete Handles (discovered during exploration — all pre-existing)

| Element | Recommended Locator | Fallback |
|---|---|---|
| "Build with AI" open button | `generate-skill-open-button` (pre-existing, confirmed live) | n/a — testid-only policy |
| Prompt textarea | `generate-skill-prompt-input` (pre-existing, confirmed live) | n/a |
| Generate button | `generate-skill-submit-button` (pre-existing, confirmed live) | n/a |
| Loading state ("Generating skill draft...") | `generate-skill-loading-indicator` (pre-existing, confirmed live — text content verified this run) | n/a |
| Review-form Name field | `generate-skill-review-name-input` (pre-existing, added for ELITEA-1990) | n/a |
| Review-form Description field | `generate-skill-review-description-input` (pre-existing, added for ELITEA-1990) | n/a |
| Review-form Instructions field | `generate-skill-review-instructions-input` (pre-existing, added for ELITEA-1990) | n/a |
| "Back to prompt" button | `generate-skill-back-button` (pre-existing, confirmed live) | n/a |
| "Create Skill" button | `generate-skill-approve-button` (pre-existing, confirmed live, not clicked in this run) | n/a |

No new testids were required for this extension — every handle needed for
the two gap assertions already exists in `GenerateSkillModalPage`.

## Network Behavior
- `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/399` — draft
  generation, `200` (confirmed live this run, real DEV backend, real
  generation — prompt: "A skill that helps write concise GitHub PR review
  comments", generated name: `github-pr-review`).
- No console errors or warnings observed at any point in the flow
  (`browser_console_messages`, onlyErrors=true, 0 results).

## Known Defects Found During Exploration
None. Live product behavior matches the case's Pass criteria exactly:
the loading state text is exactly `"Generating skill draft..."`, and the
review form shows only Name/Description/Instructions with no
tools/agents/pipelines/toolkits/MCPs/resources section.

## Blocked Steps
None. All case steps were executed live this run, end-to-end, against the
real (unmocked) DEV backend.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Extend the
  existing `TestSkillBuildWithAIReviewFormEditableFields` test (or add a
  narrowly-scoped sibling test method in the same file) in
  `automation/tests/ui/skills/test_skill_build_with_ai.py` — do not create
  a new file; do not duplicate `GenerateSkillModalPage`/
  `GenerateEntityModalPageBase` helpers.
- Both gap assertions (§ Gap Assertions To Append) require zero new
  testids and zero new `LocatorDescriptor` fields — purely new
  `assert` statements against handles that already exist.
- Recommend keeping `mock_generate_success()`'s existing `delay_ms`
  (already used by ELITEA-1990's test) when adding the loading-text
  assertion, for the same reason the shared base's docstring already
  states: "a 0-delay mock can resolve before the next assertion runs."
- If the implementer chooses to also keep one un-mocked smoke pass (as
  ELITEA-1990's AFS suggested for its own case), the loading-state text
  assertion is still safe against the real backend — confirmed observable
  live in this run even without an artificial delay, though the mocked
  path is the more deterministic choice for CI.
