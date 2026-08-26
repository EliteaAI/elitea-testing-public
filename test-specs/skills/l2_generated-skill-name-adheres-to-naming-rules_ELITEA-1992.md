# Test Case: Build with AI — generated Skill name adheres to naming rules

## Metadata
- **TMS ID**: ELITEA-1992
- **Source case**: `.agents/automation/skills-remaining-w5/cases/ELITEA-1992.md` (intake snapshot)
- **Priority**: l2 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: source case frontmatter carries `status: draft` /
  `execution_type: manual`. `.agents/testing.md` has no `TMS case-gate`
  section defining excluded statuses for this project (same recurring gap
  flagged by the whole ELITEA-1988/1989/1990/1991/1993/2001 AFS lineage) —
  per the skill's default, this run proceeded and executed the case.
- **Relationship to sibling Build-with-AI Skill specs (Rule-6 check)**:
  every existing Skill "Build with AI" test in
  `automation/tests/ui/skills/test_skill_build_with_ai.py`
  (`TestSkillBuildWithAIGenerationFailureRetry`,
  `TestSkillBuildWithAIReviewFormEditableFields`, covering ELITEA-2001,
  1990, 1989, 1988, 1991) **mocks** `generate_skill_draft` with an
  analyst-authored payload whose `name` value (`support-transcript-summarizer`,
  `pr-test-coverage-review`, `changelog-editor`) is pre-chosen to already be
  naming-rule-compliant — those tests only assert the review form
  *displays* whatever `name` the mock returns; none of them assert that a
  **real, unmocked** AI-generated name is itself well-formed. ELITEA-1993
  (`l2_build-with-ai-name-field-validation_ELITEA-1993.md`) asserts the
  Name field's client-side validation, but only on **manually-typed**
  invalid values — it never inspects an AI-generated name. This case
  (ELITEA-1992) is the one gap in the family that actually exercises the
  real generation endpoint and asserts the naming-rule compliance of its
  *own* output — no overlap with any merged spec's assertions.
  Classified fresh `ready-for-automation`, not `extend-existing`/
  `already-covered`.
- **Why this test must NOT mock the generate-draft response**: mocking
  `generate_skill_draft` with a pre-chosen compliant name (as every sibling
  test does) would make this assertion tautological — it would prove the
  analyst's own fixture string matches a regex, not that the platform's AI
  generation produces compliant output. The case's actual intent is to
  verify the **real AI/backend naming behavior**, so this AFS specifies an
  **unmocked** live call to `generate_skill_draft` (confirmed live this
  run — see below), matching the same technique the ELITEA-1989 AFS used
  for its (also-unmockable-by-nature) loading-text assertion.
- **Source-code confirmation**: the review form's Name field is validated
  client-side by `validateSkillDraft()`
  (`../EliteaUI/src/[fsd]/features/skill/lib/helpers/skillDraftValidation.helpers.js`),
  regex `/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/` (lowercase letters/digits/
  hyphens only, cannot start or end with a hyphen), plus the Name
  `<input>`'s native HTML `maxlength="64"`. This case's own live
  generation (below) shows the value the **API itself returns** already
  satisfies the regex — i.e., compliance is enforced upstream of the
  client-side validator, not merely by it.

## Preconditions
- User is logged in to Elitea (localhost `auth_state`/`VITE_DEV_TOKEN`)
  with admin/editor role — confirmed live, the "Build with AI" button
  rendered and worked without a permission gate hitting in this run.
- The Build with AI modal is reachable from `/skills/create`'s General
  accordion section header (`generate-skill-open-button`) — confirmed live.
- A project is selected/accessible (`Private`, id `399` in this run).

## Test Data

### reuse-existing
None.

### generate-per-test
- Natural-language prompt used this run (any valid non-empty prompt
  satisfies the case's Test Data requirement — content isn't asserted,
  only the resulting Name's format): `"A skill that translates English
  customer feedback into concise Spanish summaries for the support
  team."`.
- **Confirmed live this run**, real (unmocked) DEV backend response
  (`POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/399` →
  `200`): `name: "english-to-spanish-feedback"` — verified byte-identical
  between the raw API response body and the review form's Name field
  (`generate-skill-review-name-input`) `input_value()`, i.e. no client-side
  transform/sanitization runs between the two; the API already returns a
  naming-rule-compliant value.
- No skill is created/persisted by this case — the case's Expected Final
  State stops at inspecting the generated Name; the modal was closed via
  `generate-skill-close-button` without clicking "Create Skill." No
  cleanup is required.

### generate-shared-with-cleanup
None.

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`, click **"Build with AI"**
   (`generate-skill-open-button`), fill the prompt
   (`generate-skill-prompt-input`) with any valid non-empty description,
   and click **Generate Draft** (`generate-skill-submit-button`) against
   the **real, unmocked** backend.
   - **Verify** (confirmed live): the request resolves `200`, and the
     modal transitions to the review-form step (`generate-skill-back-button`
     / `generate-skill-approve-button` both become visible).

2. Inspect the generated Name in the review form
   (`generate-skill-review-name-input`).
   - **Verify** (confirmed live): the field is visible and populated
     (non-empty) — this run's value: `"english-to-spanish-feedback"`.

3. Verify the name contains only lowercase letters, digits, and hyphens.
   - **Verify** (confirmed live): `"english-to-spanish-feedback"` matches
     `^[a-z0-9-]+$` — every character is a lowercase letter or a hyphen.

4. Verify the name does not contain spaces, underscores, or special
   characters.
   - **Verify** (confirmed live): no ` `, `_`, or any character outside
     `[a-z0-9-]` present.

5. Verify the name does not start or end with a hyphen.
   - **Verify** (confirmed live): first char `e`, last char `k` — neither
     is `-`.

6. Verify the name does not exceed 64 characters.
   - **Verify** (confirmed live): `len("english-to-spanish-feedback") == 27`,
     well under 64.

All six checks reduce, mechanically, to one regex + one length assertion
against the single generated-name string (the same regex the digest/1993
AFS already confirmed against source:
`^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`, `len <= 64`) — the AFS keeps them
enumerated per-step (rather than collapsing to one assertion) so a future
failure pinpoints exactly which naming sub-rule broke, mirroring the
case's own step granularity.

## Expected Results
Matches the case's stated Pass criteria exactly: the AI-generated Name is
visible, populated, and its value is confirmed live to satisfy every
naming-rule sub-check (lowercase/digit/hyphen-only charset, no leading/
trailing hyphen, ≤ 64 chars) — with the API response itself (not just the
DOM field) carrying the compliant value, confirmed this run via
`browser_network_request` on the `generate_skill_draft` response body.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open modal, submit prompt | generation initiated and completes | step 1 | step 1: `200` response + review-form transition, confirmed live against real backend | asserted |
| 2 Inspect generated Name in review form | Name field visible and populated | step 2 | step 2: `get_review_name()` non-empty, confirmed live (`"english-to-spanish-feedback"`) | asserted |
| 3 Only lowercase letters, digits, hyphens | charset restricted | step 3 | step 3: regex/charset check against the confirmed live value | asserted |
| 4 No spaces/underscores/special chars | absence confirmed | step 4 | step 4: same regex check (charset restriction implies this) | asserted |
| 5 No leading/trailing hyphen | first/last char not `-` | step 5 | step 5: string boundary check against the confirmed live value | asserted |
| 6 Name ≤ 64 characters | length constraint | step 6 | step 6: `len()` check against the confirmed live value (27 chars this run) | asserted |

### Axis 2 — Analyst additions

- **API-response-vs-DOM-field parity check** — *added: confirmed live
  that the raw `generate_skill_draft` response body's `name` field is
  byte-identical to the review form's displayed value, proving the
  platform's generation output is compliant at the source (not merely
  passed through an invisible client-side sanitizer before display). This
  strengthens the case's intent — "the generated Skill name adheres to
  naming rules" is a claim about the AI/backend's output, and this
  confirms the DOM assertion is not masking a client-side fixup.*
- **Explicit no-mock declaration** — *added: documented and justified why
  this AFS deliberately diverges from every sibling Build-with-AI test's
  mocking convention (see Metadata) — without this note an implementer
  might "normalize" the test to use `mock_generate_success()`, which would
  silently defeat the case's actual purpose.*

## Cleanup
None required. No Skill is created — the modal is closed via
`generate-skill-close-button` immediately after inspecting the generated
Name (confirmed live: closing here does not fire any additional network
request).

## Concrete Handles (discovered during exploration — all pre-existing)

| Element | Recommended Locator | Fallback |
|---|---|---|
| "Build with AI" open button | `generate-skill-open-button` (pre-existing, confirmed live) | n/a — testid-only policy |
| Prompt textarea | `generate-skill-prompt-input` (pre-existing, confirmed live) | n/a |
| Generate button | `generate-skill-submit-button` (pre-existing, confirmed live) | n/a |
| Review-form Name field | `generate-skill-review-name-input` (pre-existing, added for ELITEA-1990) — `GenerateSkillModalPage.get_review_name()` already returns `.input_value()` | n/a |
| Close button (dialog) | `generate-skill-close-button` (pre-existing, confirmed live this run) | n/a |
| "Create Skill" button | `generate-skill-approve-button` (pre-existing) — not clicked in this case | n/a |

No new testids are required for this case — every handle needed already
exists in `GenerateSkillModalPage`/`GenerateEntityModalPageBase`.

## Network Behavior
- `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/399` — draft
  generation, **unmocked**, confirmed live `200` this run. Response body
  (confirmed via `browser_network_request`): `{"name":
  "english-to-spanish-feedback", "description": "...", "instructions":
  "..."}` — the `name` field is the assertion target.
- No `POST .../skills/prompt_lib/399` (create) fires — the case never
  clicks "Create Skill."
- No console errors observed (`browser_console_messages`, level=error →
  0 of 7 total messages).

## Known Defects Found During Exploration
None. Live product behavior matches the case's Pass criteria exactly: the
real, unmocked AI-generated Skill name (`english-to-spanish-feedback`,
this run) satisfies every naming-rule sub-check the case enumerates.

## Blocked Steps
None. All case steps were executed live this run, end-to-end, against the
real (unmocked) DEV backend.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Home:
  `automation/tests/ui/skills/test_skill_build_with_ai.py` (existing file)
  — add a new, narrowly-scoped test class (e.g.
  `TestSkillBuildWithAIGeneratedNameNamingRules`) reusing
  `GenerateSkillModalPage`; do not create a new file.
- **Do not mock `generate_skill_draft` for this test** (see Metadata
  § "Why this test must NOT mock…") — call
  `modal.click_generate_and_wait_for_response(timeout=...)` against the
  real backend. Recommend a more generous timeout than the existing
  mocked-path `GENERATE_RESPONSE_TIMEOUT = 15000` constant — this run's
  real generation resolved within ~25s; **30000ms** is a safer floor for
  an LLM-backed, unmocked call. If CI stability against a live LLM call
  proves an issue, note it in the Run Report rather than silently
  reverting to a mock (that would defeat the case).
- Assertion helper (suggested, mirrors the case's per-rule granularity):
  ```python
  import re

  SKILL_NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")

  def assert_generated_name_is_compliant(name: str) -> None:
      assert name, "Generated Name should be non-empty"
      assert SKILL_NAME_RE.match(name), (
          f"Generated Name {name!r} must contain only lowercase letters, "
          "digits and hyphens, and must not start or end with a hyphen"
      )
      assert not name.startswith("-") and not name.endswith("-"), (
          f"Generated Name {name!r} must not start or end with a hyphen"
      )
      assert len(name) <= 64, (
          f"Generated Name {name!r} must not exceed 64 characters (got {len(name)})"
      )
  ```
  (The `SKILL_NAME_RE` match already implies the no-leading/trailing-hyphen
  check; the explicit `startswith`/`endswith` assertion is kept anyway so
  a regex failure and a hyphen-boundary failure produce distinguishable
  messages, matching the case's Step 3 vs Step 5 split.)
- Also assert the API response's `name` field (from
  `click_generate_and_wait_for_response()`'s returned `response.json()`)
  equals `modal.get_review_name()` — the parity check documented in Axis 2,
  confirming the DOM value isn't silently transformed from the API value.
- No cleanup/fixture needed — this test never creates a Skill; close the
  modal via `modal.close_button.click()` (or equivalent) once assertions
  pass.
- Consider running this test with `@pytest.mark.flaky(reruns=1)` if CI
  shows real-LLM-call latency/instability — per `.agents/testing.md`,
  per-test reruns are allowed when justified; document the justification
  in the test's docstring if added.
