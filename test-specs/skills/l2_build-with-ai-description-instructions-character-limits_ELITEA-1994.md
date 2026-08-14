# Test Case: Build with AI — review-form Description/Instructions character limits are enforced (Family)

> ⚠️ **UNDER REVIEW — 2026-08-14 fidelity audit. Do NOT reuse this AFS as a pattern.**
>
> This spec directs the implementer to **substitute the system under test** (mocking
> the generate-draft response) for a TMS case whose text never asks for simulation.
> Classification: **TRANSIT** — covers ELITEA-1994 + ELITEA-1995; the mock only reaches the review form — the character-limit truncation the case checks is produced by the real UI on typed input.
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
- **TMS ID (family)**: ELITEA-1994, ELITEA-1995 — `family_afs: true`, this file
  is the single AFS for both cases (parameter table below has one row per
  case).
- **Linked Story**: none
- **Priority**: l2 (both source cases declare `priority: medium` in
  frontmatter; maps to `l2` per this folder's established convention for the
  sibling Build-with-AI cases, e.g. ELITEA-1993/1996/1997/1998)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` / id `399`)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot (cluster dispatch, one live
  session for both cases)
- **Status**: **ready-for-automation** — both cases executed end-to-end live
  against a REAL (unmocked) generated draft. No blocking defect; two
  case-text-drift clarifications filed/referenced (see Known Defects). No
  new testid needed — every assertion resolves through already-testid'd
  elements.

## Family classification rationale

Per `test-case-analysis` § 3 "differ only in DATA vs. differ in STEPS": both
cases drive the **identical** flow (generate a draft → reach the review form
→ overwrite one field with an over-limit string → observe the field's
resulting value/validity/button state → confirm the field is at-limit and
valid) against the **same** underlying mechanism
(`GenerateSkillReviewForm.jsx`'s `slotProps.htmlInput.maxLength`, sourced
from `EliteaUI/src/common/constants.js`). ELITEA-1994 targets the
**Description** field (`MAX_DESCRIPTION_LENGTH`); ELITEA-1995 targets the
**Instructions** field (`MAX_INSTRUCTIONS_LENGTH`) — same steps, same
assertions, different target field/constant/limit value. One parameterized
spec, 2 data rows.

## Source-code confirmation (read before/alongside live execution)

`GenerateSkillReviewForm.jsx` (`EliteaUI/src/[fsd]/features/skill/ui/
generate-skill-modal/GenerateSkillReviewForm.jsx`) wires the SAME pattern
already documented for the Name field (`test-specs/skills/
l2_build-with-ai-name-field-validation_ELITEA-1993.md`) onto Description and
Instructions:

```js
import { MAX_DESCRIPTION_LENGTH, MAX_INSTRUCTIONS_LENGTH } from '@/common/constants.js';
// Description <TextField multiline>:
slotProps: { htmlInput: { maxLength: MAX_DESCRIPTION_LENGTH, 'data-testid': 'generate-skill-review-description-input' } }
// Instructions <TextField multiline>:
slotProps: { htmlInput: { maxLength: MAX_INSTRUCTIONS_LENGTH, 'data-testid': 'generate-skill-review-instructions-input' } }
```

`EliteaUI/src/common/constants.js:67-68`:
```js
export const MAX_DESCRIPTION_LENGTH = 2304;
export const MAX_INSTRUCTIONS_LENGTH = 5000;
```

`validateSkillDraft()` (`skillDraftValidation.helpers.js`) independently
carries the SAME two constants and would set `errors.description`/
`errors.instructions` (disabling "Create Skill" via `isDraftValid`) if a
draft object ever contained an over-length value — but see Known Defect #1:
the native `maxLength` on both fields' `<textarea>` makes that branch
unreachable via manual UI editing (typed, pasted, or `.fill()`'d), exactly
like the Name field's already-documented `maxlength=64` gap.

## Preconditions
- User is logged in to Elitea (localhost `auth_state`/`VITE_DEV_TOKEN`) with
  editor/admin role sufficient to create skills.
- A skill draft has been generated via the Build with AI modal — covered by
  this AFS's own Step 1 (case-text-drift pattern already established by the
  ELITEA-1990/1993/2001 AFS lineage; not filed separately here).
- A project is selected/accessible (`Private`, id `399` in this run).

## Test Data

### Parameter table (one row per source TMS case)

| # | Source case | Target field | Field testid | Constant | Case-stated limit | **Live-confirmed limit** |
|---|---|---|---|---|---|---|
| 1 | ELITEA-1994 | Description | `generate-skill-review-description-input` | `MAX_DESCRIPTION_LENGTH` | 2,304 | **2,304 (case text is correct)** |
| 2 | ELITEA-1995 | Instructions | `generate-skill-review-instructions-input` | `MAX_INSTRUCTIONS_LENGTH` | 2,500 | **5,000 (case text is stale — clarification filed, see Known Defects #2)** |

### generate-per-test
- Prompt used to generate the draft (REAL, unmocked call — see
  § Automation Hints for why mocking is preferred for the automated version):
  live exploration used `"A skill that reviews pull request diffs and flags
  missing test coverage for ELITEA-1994/1995 char-limit analysis."` and
  received a valid generated draft (`name: "pr-test-coverage-review"`, a
  ~260-char description, a multi-paragraph instructions body) in ~20s.
- Over-limit synthetic value per row: a same-character string 100 chars
  longer than the row's live-confirmed limit (`"y" * 2404` for Description,
  `"z" * 5100` for Instructions in this exploration) — any over-limit value
  works identically since truncation is length-based, not content-based.

### generate-shared-with-cleanup
None. This case never reaches the create-skill network call — the review
form is closed via the "Close" (X) icon (`generate-skill-close-button`)
after both rows are exercised, discarding the draft. Confirmed live: zero
`POST .../skills/prompt_lib/399` requests fired across the whole run.

## Test Steps

Run once per Test Data row (`${FIELD_INPUT}` / `${FIELD_HELPER_GETTER}` /
`${LIMIT}` = the row's values):

1. Navigate to `${BASE_URL}/skills/create`, click **"Build with AI"**
   (`generate-skill-open-button`), fill the prompt
   (`generate-skill-prompt-input`), click **Generate**
   (`generate-skill-submit-button`), and wait for the review-form step
   (`generate-skill-back-button` / `generate-skill-approve-button` both
   visible).
   - **Verify** (confirmed live): review form is displayed with the three
     fields pre-populated from the draft, and "Create Skill"
     (`generate-skill-approve-button`) starts **enabled** (the unmodified
     generated draft is itself valid — both Description and Instructions
     are well within their limits).

2. Overwrite `${FIELD_INPUT}` (the row's field —
   `generate-skill-review-description-input` for row 1,
   `generate-skill-review-instructions-input` for row 2) via `.fill()` with
   a string **longer than** `${LIMIT}` characters (row 1: 2,404 chars vs.
   the 2,304 limit; row 2: 5,100 chars vs. the 5,000 limit — see Known
   Defect #2 for why row 2 does not use the case's literal "over 2,500"
   value).
   - **Verify** (confirmed live, via a real user-input-equivalent paste —
     `document.execCommand('insertText', ...)` on the focused field,
     confirmed to reproduce the identical truncation `.fill()`/keystroke
     typing already established for the Name field in ELITEA-1993): the
     field's own native `maxlength` HTML attribute
     (`slotProps.htmlInput.maxLength`, `MAX_DESCRIPTION_LENGTH`/
     `MAX_INSTRUCTIONS_LENGTH` from `EliteaUI/src/common/constants.js`)
     truncates the pasted value to **exactly `${LIMIT}` characters** before
     any React validation ever runs. Live-measured: row 1's
     `generate-skill-review-description-input.input_value()` length ==
     **2304**; row 2's `generate-skill-review-instructions-input
     .input_value()` length == **5000**. This combines and corrects the
     case's Steps 2-4 ("enter an over-limit string → validation error is
     shown → Create Skill is disabled") — that sequence is unreachable via
     manual UI editing for the same reason ELITEA-1993's Step 6 documents
     for the Name field; see Known Defect #1.

3. (Combines and satisfies the case's Steps 5-6 — "trim the field to
   exactly `${LIMIT}` characters" is a no-op after Step 2, since the native
   truncation already left the field at exactly the limit.)
   - **Verify** (confirmed live): no validation error is shown for the
     row's field — the helper text under the field reads the plain
     character-count counter (`"2304/2304"` for Description,
     `"5000/5000"` for Instructions), not an error message; "Create Skill"
     (`generate-skill-approve-button`) **remains enabled**
     (`is_enabled() == True`). Confirmed live via direct DOM inspection of
     the review form's `MuiFormHelperText-root` node and the approve
     button's `disabled` property.

4. Repeat Steps 1-3 for the other row (Description then Instructions, or
   vice versa — independent, no shared state between rows beyond the
   modal's own open/close per row).

5. Close the modal via the "Close" (X) icon (`generate-skill-close-button`)
   without ever creating a skill.
   - **Verify** (confirmed live across the whole run): zero
     `POST .../elitea_core/skills/prompt_lib/399` (create) requests fired;
     zero console errors (`browser_console_messages(level="error")` returned
     0 across both rows).

## Expected Results
For both rows: an over-limit paste into the target field is truncated by the
field's native `maxlength` to exactly the row's live-confirmed limit before
React validation ever sees an over-length value; the truncated value is
valid (character-count helper text, no error), and "Create Skill" stays
enabled throughout. No Skill is ever created during this case. Matches the
case's Pass criteria for the exact-limit behavior (Steps 5-6) exactly; the
over-limit-rejection behavior (Steps 2-4) is corrected per Known Defect #1
to reflect that state's unreachability via manual editing — the same
class of finding ELITEA-1993 already established for the Name field.
Row 2 (ELITEA-1995) additionally corrects the case's stated numeric limit
(2,500 → 5,000) per Known Defect #2.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: "A skill draft has been generated" (both cases) | draft/review form exists | step 1 | step 1: review form reached via a real generate call | clarification *(case-text drift — same established pattern as ELITEA-1990/1993; not filed separately)* |
| 1 Generate a skill draft, enter review form (both cases) | review/edit form displayed | step 1 | step 1: back/approve buttons visible, approve starts enabled | asserted |
| 2 Clear field, paste over-limit string (ELITEA-1994 Description / ELITEA-1995 Instructions) | text entered in the field | step 2 | step 2: field value inspected post-paste | asserted, **corrected** — see disposition below |
| 3 Validation message shown for the field | validation error displayed | step 2 | step 2: **corrected** — field truncates to exactly the limit via native `maxlength`; no error is ever reachable this way | clarification *(case-text drift — see Known Defect #1)* |
| 4 "Create Skill" button inactive/disabled | button disabled | step 2 | step 2: **corrected** — button stays enabled (truncated value is valid) | clarification *(case-text drift — see Known Defect #1, same root cause as #3)* |
| 5 Trim field to exactly the limit | field contains exactly N chars | step 3 (no-op after step 2) | step 3: field length == limit, confirmed already true post-truncation | asserted, **folded** into step 2's truncation |
| 6 Validation error clears, "Create Skill" becomes active | error clears, button active | step 3 | step 3: helper text is the plain counter (not error), approve button enabled | asserted |

### Axis 2 — Analyst additions

- Step 5's zero-network-calls + zero-console-errors whole-run confirmation —
  *added: a single, cheap, whole-run guarantee that no invalid variant ever
  reaches the backend, mirroring ELITEA-1993's identical addition for the
  Name field.*
- Row 2's live-measured limit (5,000, not the case's stated 2,500) — *added:
  without re-deriving the actual constant, an implementer would either
  hard-code a wrong expected value (silently passing the wrong assertion, or
  worse, an over-limit string that is actually still valid) or discover the
  drift mid-implementation with no citation trail. Filed as a clarification
  (Known Defect #2) rather than guessed past.*
- Confirmation that `.fill()`-based `set_review_description()`/
  `set_review_instructions()` (pre-existing `GenerateSkillModalPage`
  methods) correctly trigger React's `onChange` for these two fields — *
  added: same due-diligence already documented for `set_review_name()` in
  the page object's docstring, now independently confirmed live for these
  two fields via the `execCommand('insertText', ...)` probe (which
  dispatches the same native `input` event `.fill()` relies on).*

## Cleanup
None required. No Skill is ever created by this case (the modal is closed
via the X icon after both rows are exercised) — confirmed live, zero
`POST .../skills/prompt_lib/399` requests across the whole run.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| "Build with AI" open button | `generate-skill-open-button` (pre-existing) | on-main ✓ (pre-existing per ELITEA-1990 lineage) | `GenerateSkillModalPage` field |
| Prompt textarea | `generate-skill-prompt-input` (pre-existing) | on-main ✓ | |
| Generate button | `generate-skill-submit-button` (pre-existing) | on-main ✓ | |
| Review-form **Description** field | `generate-skill-review-description-input` (pre-existing) | on-main ✓ | `review_description_input` / `set_review_description()` / `get_review_description()` — all already on `GenerateSkillModalPage` |
| Review-form **Instructions** field | `generate-skill-review-instructions-input` (pre-existing) | on-main ✓ | `review_instructions_input` / `set_review_instructions()` / `get_review_instructions()` — all already on `GenerateSkillModalPage` |
| "Create Skill" button | `generate-skill-approve-button` (pre-existing) — its `disabled` state (via `is_enabled()`) is this case's primary assertion target | on-main ✓ | |
| Close (X) button | `generate-skill-close-button` (pre-existing) | on-main ✓ | used for cleanup — review step has no "Cancel" |

**No new testid needed for this case.** The Description/Instructions
helper-text elements remain untested (no `data-testid`, unlike
`generate-skill-review-name-helper-text` added for ELITEA-1993) — every
assertion this case needs resolves through the already-testid'd field
inputs (`.input_value()` length) and the approve button's `disabled`
property, so no new element is touched and none is requested. (Per canon
ruling #511: a testid is only "referenced" — and thus only worth adding —
when the test's own executed path calls it; this case's path never needs to
read the helper text's exact string, only whether the field's value length
equals the limit and whether the button is enabled.)

## Network Behavior
- `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/399` — draft
  generation. Live exploration used a REAL (unmocked) call; the automated
  version should mock it via `mock_generate_success(GENERATED_DRAFT_PAYLOAD)`
  (already defined in `test_skill_build_with_ai.py`) for determinism/speed,
  per the same reasoning ELITEA-1993 documents (this case's assertions are
  entirely about client-side field validation, not generation quality).
- **No other network call fires at any point in this case.** Description/
  Instructions length validation (`validateSkillDraft`) is pure, synchronous
  client-side JavaScript — confirmed live: zero requests to
  `.../elitea_core/skills/prompt_lib/399` (create) across both rows, because
  "Create Skill" is never clicked in this case (the modal is closed instead).
- Zero console errors observed during both rows' edits (`browser_console_
  messages(level="error")` returned 0 messages for the whole session).

## Known Defects Found During Exploration

1. **Case-text drift (CLARIFICATION, not a product defect) — the
   "over-limit → validation error + disabled button" state is unreachable
   via manual UI editing, for BOTH Description and Instructions.** Both
   cases' Steps 2-4 describe pasting an over-limit string and then observing
   a validation error and a disabled "Create Skill" button. Live exploration
   (confirmed via a real paste-equivalent `document.execCommand('insertText',
   ...)` on the focused field, the same mechanism the Name field's
   `.fill()`/`press_sequentially()` precedent used in ELITEA-1993) shows both
   fields carry a native HTML `maxlength` attribute
   (`GenerateSkillReviewForm.jsx`'s `slotProps.htmlInput.maxLength`, sourced
   from `MAX_DESCRIPTION_LENGTH`/`MAX_INSTRUCTIONS_LENGTH`) that caps **any**
   input — typed, pasted, or `.fill()`'d — at exactly the limit before
   React's `onChange`/`validateSkillDraft()` ever sees a longer value. The
   over-limit branches of `validateSkillDraft()` (`Description must be 2304
   characters or less` / `Instructions must be 5000 characters or less`) are
   real code that does exist, but — exactly as ELITEA-1993's Known Defect #2
   already established for the Name field — they are dead from the
   manual-editing surface these cases describe. Not filed as a separate
   GitHub issue, following that same local precedent (documented here as an
   AFS clarification instead). The corrected, automatable equivalent
   (truncation to the exact limit, value remains valid) is what Step 2/3 of
   this AFS asserts.

2. **Case-text drift (CLARIFICATION, filed) — ELITEA-1995's stated
   Instructions limit (2,500) does not match the live product (5,000).**
   Filed: [elitea-testing-public#1489](https://github.com/EliteaAI/elitea-testing-public/issues/1489)
   (sibling of [#1480](https://github.com/EliteaAI/elitea-testing-public/issues/1480),
   which documents the identical `MAX_INSTRUCTIONS_LENGTH = 5000` drift for
   the sibling "Edit with AI" flow, ELITEA-2613). Live/source-confirmed:
   `EliteaUI/src/common/constants.js:68` — `export const
   MAX_INSTRUCTIONS_LENGTH = 5000;` — imported into
   `GenerateSkillReviewForm.jsx` and applied identically to the Instructions
   field. Live-measured: pasting a 5,100-character string truncates to
   exactly 5,000 characters, not 2,500. ELITEA-1994's Description limit
   (2,304) is, by contrast, **exactly correct** per the case text — only
   ELITEA-1995's number is stale. Recommendation (per the filed issue):
   update the TMS case's "2,500 characters" references to "5,000
   characters".

No functional product defect was found in either case. The live product's
actual behavior for both fields either matches the cases' Pass criteria
exactly (Steps 5-6, once the correct limit is used for row 2) or exceeds it
via a stronger mechanism the cases did not anticipate (Steps 2-4, per Known
Defect #1) — the product prevents an invalid state from ever being entered,
rather than accepting then rejecting it.

## Blocked Steps
None. Both cases' steps were executed end-to-end live against the real DEV
backend (draft generation used a real, unmocked call in this exploration;
the field-length validation under test is itself pure client-side and was
exercised directly against the shipped `GenerateSkillReviewForm.jsx` /
`validateSkillDraft()` logic).

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Home:
  `automation/tests/ui/skills/test_skill_build_with_ai.py` (existing file —
  add a new test class, e.g. `TestSkillBuildWithAIReviewFormCharacterLimits`,
  parameterized over the two rows via `@pytest.mark.parametrize` or two
  discrete test methods sharing a helper; reuse `GENERATED_DRAFT_PAYLOAD`
  and `GenerateSkillModalPage` rather than duplicating the mock draft).
- Page object: **no changes needed.** `review_description_input` /
  `review_instructions_input` / `set_review_description()` /
  `set_review_instructions()` / `get_review_description()` /
  `get_review_instructions()` / `approve_button` are all pre-existing
  `GenerateSkillModalPage` fields/methods (added for ELITEA-1990/1991).
- Recommend mocking `generate_skill_draft` (via
  `mock_generate_success(GENERATED_DRAFT_PAYLOAD)`, already used by the
  sibling ELITEA-1990/1991/1993 tests) for determinism/speed — this case's
  assertions are entirely about client-side field-length validation, not
  generation quality or network behavior.
- For both rows, use `set_review_description("y" * 2404)` /
  `set_review_instructions("z" * 5100)` — `.fill()` is already confirmed
  (both live, this run, and by precedent in the page object's own
  `set_review_name()` docstring) to respect the native `maxlength` the same
  as real typing/pasting — then assert:
  ```python
  assert len(modal.get_review_description()) == 2304
  assert modal.approve_button.is_enabled() is True
  ```
  and symmetrically for Instructions with `5000`. Do **not** assert a
  validation-error helper text for either field — no testid exists for
  Description/Instructions helper text (only Name's does, per ELITEA-1993),
  and per Known Defect #1 above, no error state is reachable to assert
  regardless.
- Live-confirmed exact limits to hard-code as test constants (do not
  re-derive from case text): `MAX_DESCRIPTION_LENGTH = 2304`,
  `MAX_INSTRUCTIONS_LENGTH = 5000`.
- No cleanup/fixture needed — this test never creates a Skill (close the
  modal via `modal.close_button.click()` at the end, mirroring ELITEA-1992's
  cleanup pattern).
