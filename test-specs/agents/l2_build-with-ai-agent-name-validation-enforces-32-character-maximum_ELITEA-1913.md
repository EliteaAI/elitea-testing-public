# Test Case: Build with AI — agent name validation enforces 32-character maximum

## Metadata
- **TMS ID**: ELITEA-1913
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/agents/build_with_ai/ELITEA-1913_build-with-ai-agent-name-validation-enforces-32-character-maximum.md`
- **Linked Story**: none
- **Priority**: l2 (case priority: `medium`)
- **Status**: `ready-for-automation`
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project "UI Testing" (id `400`)
- **User set**: `${TEST_USER}` (localhost `auth_state`/dev-token bypass skips login)
- **Analyst**: qa-engineer (Sage), analyst slot, batch #1298
- **Tracking issue**: EliteaAI/elitea-testing-public#1298 (batch tracking issue — no per-case board card)
- **Case-gate note**: same recurring gap as every prior "Build with AI" AFS in this family: `.agents/testing.md` has no `TMS case-gate` section defining excluded statuses. Case frontmatter carries `status: draft` / `execution_type: manual`; per the skill's default this run proceeded and fetched/executed the case. Flagging again for scout.

## Triangulation — why this is `ready-for-automation`, not a duplicate of ELITEA-1900 or covered by ELITEA-1912

Both prior "32-char Name field" artifacts on this trunk/suite were read and
confirmed **genuinely distinct** from this case's target, by reading source,
not by name:

1. **ELITEA-1900** (`automation/tests/ui/agents/test_agent_name_character_limit.py::test_agent_name_truncated_at_32_characters`)
   tests the **regular Create Agent form's** Name field — testid
   `agent-name-input`, component `CreateAgentForm.jsx`
   (`inputProps={{ maxLength: MAX_NAME_LENGTH, 'data-testid': 'agent-name-input' }}`).
   Source-confirmed: this field wires `maxLength` through the older MUI
   `inputProps` API, and it DOES render as a native `maxlength="32"` HTML
   attribute — live-confirmed by that test's own assertions (bulk `.fill()`
   of 80 chars truncates to exactly 32; `press_sequentially()` past 32
   silently rejects extra keystrokes; **no error state, no validation
   message** — the limit is enforced by the browser's native input clamp).
2. **ELITEA-1912** (`TestAgentBuildWithAIDraftFieldPopulation.test_edited_fields_persist_after_approve`,
   same file) edits the Build-with-AI review form's Name field
   (`generate-agent-review-name-input`) — but **deliberately avoids the
   32-char boundary**: its own AFS/code comment states the `"<generated
   name> [edited]"` suffix convention "rejects the draft… once the
   generated 30-char name gains any suffix", so the implementation
   switched to a short, under-limit literal (`"Edited Agent Name [1912]"`,
   25 chars) specifically **to keep the Approve button enabled**. It never
   types an over-limit name, never reads the validation error, and never
   asserts the button's disabled state. It proves the "stays under the
   limit → Approve works" path; it does not touch this case's target
   contract (over-limit → error shown + Approve disabled → trim to exactly
   32 → error clears + Approve re-enables).

**Source read confirms these are functionally different mechanisms, not
just different tests of the same thing** — this is the crux of the
triangulation and also this run's own live finding (see § Known Defects):
`GenerateAgentReviewForm.jsx`'s Name field wires `maxLength` through the
*newer* MUI `slotProps={{ htmlInput: { maxLength: MAX_NAME_LENGTH } }}` API,
and — **live-confirmed this run** — that prop does **not** propagate to a
native `maxlength` attribute on the rendered `<input>`
(`el.maxLength === -1`, `el.getAttribute('maxlength') === null`, checked via
`browser_evaluate` after typing 40 real keystrokes past the limit, all 40
landed in the DOM value). So real typing is **not** clamped the way
`agent-name-input`'s is; instead, `validateAgentDraft()`
(`agentDraftValidation.helpers.js`) computes `errors.name` client-side and
the review form renders it as `helperText`/`error` on the MUI field, while
`isDraftValid` gates `generate-agent-approve-button`'s `disabled` prop. This
is a genuinely different validation mechanism from ELITEA-1900's field, and
this case's Pass criteria (error message shown + Approve disabled + both
clear at exactly 32) is exactly what exercises it. Neither prior test
proves this. Not a duplicate; not an extension target — fresh coverage.

**Root cause confirmed by source read (explains WHY, not just THAT), and
reconciles an apparent contradiction with the Skill Build-with-AI sibling
case (ELITEA-1993, `daily/2026-08-02.md`), which found the SKILL review
form's Name field DOES get native `maxlength` truncation via the same
`slotProps.htmlInput.maxLength` API.** These are not inconsistent findings
about the same mechanism — they're two different components:
`GenerateSkillReviewForm.jsx` calls MUI's raw `<TextField slotProps={{htmlInput:{maxLength}}}>`
directly, which honors it natively. `GenerateAgentReviewForm.jsx` (this
case's target) instead calls the project's own wrapper,
`Input.InputBase` (`EliteaUI/src/[fsd]/shared/ui/input/InputBase.jsx`),
which has a genuine prop-plumbing bug: it destructures only an `inputProps`
prop from its own `props` (line 85), builds its OWN internal `slotProps`
object mapping `htmlInput: inputProps` (line 267), and spreads that
internal `slotProps` onto `<MuiTextField>` (line 260) **after** spreading
`{...leftProps}` (line 257) — and since `leftProps` is everything NOT
explicitly destructured, including any `slotProps` the CALLER passed, JSX's
later-prop-wins semantics mean the caller's `slotProps` (containing
`htmlInput.maxLength`) is silently and completely overwritten by
`InputBase`'s own internally-built one, which has no `maxLength` in it.
This is why `GenerateAgentReviewForm.jsx`'s `slotProps={{ htmlInput: {
maxLength: MAX_NAME_LENGTH } }}` has zero effect — it never reaches the
DOM. Out of scope to fix as part of this case (doesn't affect this case's
own Pass criteria — the JS validation path works correctly independent of
native maxlength), but worth recording precisely since it also shapes the
CORRECT way to add the error-message testid this AFS asks for (see
Concrete Handles) — a caller passing raw `slotProps.formHelperText` would
suffer the identical silent-drop bug; the fix must thread a NEW explicitly-
destructured prop through `InputBase`'s OWN internal `slotProps`
construction, the same pattern already used for `tooltipTestId`/
`tooltipContentTestId` in that same file.

## Preconditions
- User is logged in to Elitea (localhost `auth_state`/dev-token bypass) with
  admin/editor role sufficient to create agents — confirmed live (same
  permission finding as every prior case in this family).
- A project is selected/accessible ("UI Testing", id `400`, this run).
- **Corrected precondition (case-text drift, not a defect — same
  clarification recorded by every prior case in this family, e.g.
  ELITEA-1906/1912):** "An agent draft has been generated and the
  review/edit form is displayed" is accurate; the modal is reached via
  `${BASE_URL}/agents/create` → "Build with AI" (`generate-agent-open-button`)
  → fill prompt → **"Generate Draft"** (`generate-agent-submit-button`) — not
  "Generate agent", the case-text/live-label mismatch this AFS family
  repeatedly notes (`_surface.md`).

## Test Data

### reuse-existing (no fixture creation/teardown needed — read-only case)
- Natural-language prompt (same as ELITEA-1906/1912's, reused deliberately
  so this case's validation behaviour is isolated from any prompt-content
  variable): `"An agent that helps write concise JIRA ticket descriptions"`.
- Live-generated draft's Name this run: `"JIRA Ticket Writer"` (19 chars,
  under the limit) — the starting value the test edits away from. The exact
  generated name doesn't matter for this case (unlike ELITEA-1912's
  approve-and-persist case) since the test only edits the Name field and
  never clicks Approve to completion — draft generation may be mocked or
  live at the implementer's discretion.
- Over-limit name used this run: 40 `'A'` characters typed via real
  keystrokes (`press_sequentially`-equivalent), confirmed to land as a
  40-char DOM value (no native truncation on this field — see Triangulation).
  Implementer may reuse literally (`"A" * 40`) or any string > 32 chars.
- Exactly-32-char name used this run: `"Edited Agent Name Exactly32Char!"`
  (confirmed live via `input_value()` length == 32 after typing). The
  implementer should construct this programmatically
  (`base_string[:32]` from any base string ≥ 32 chars, or
  `"A" * 32`) rather than hand-count a literal — this run typed the literal
  incrementally and verified the length via `input_value()` after each
  keystroke specifically to avoid an off-by-one, which is the safer pattern
  for automation too.

No agent is created (the test never clicks a still-enabled Approve to
completion) — no cleanup needed beyond closing the modal.

## Test Steps

1. Navigate to `${BASE_URL}/agents/create`, click **"Build with AI"**
   (`generate-agent-open-button`), enter the case's prompt, click
   **"Generate Draft"** (`generate-agent-submit-button`), wait for the
   review form (`wait_for_review_form()`).
   - **Verify**: review form renders with the Name field populated
     (`generate-agent-review-name-input`) — confirmed live this run, draft
     name `"JIRA Ticket Writer"`. (Draft population itself is already
     proven by ELITEA-1906 — not re-asserted here beyond confirming the
     field is present and interactable, the precondition for this case's
     own steps.)

2. Select all existing text in the Name field and type 40 characters via
   real keystrokes (`press_sequentially`/`type(..., slowly=True)`, NOT
   `.fill()` — see Automation Hints for why the distinction matters here).
   - **Verify**: the Name field's DOM value is exactly 40 characters — live
     confirmed this run via `input.value.length === 40` (no native
     `maxlength` clamp on this field, unlike `agent-name-input`). This
     itself is worth asserting explicitly (see Axis 2) because it is the
     opposite of what a reader familiar with ELITEA-1900's field would
     assume.

3. Verify a validation message is shown for the Name field.
   - **Verify**: live-confirmed this run —
     `review_name_input` carries `aria-invalid="true"` (readable via
     `get_attribute("aria-invalid")` on the EXISTING `review_name_input`
     `LocatorDescriptor`, no new testid needed for this half), AND a
     helper-text paragraph reading exactly **"Name must be 32 characters or
     less"** renders as a sibling of the input (MUI `FormHelperText`,
     `error` variant — red text in the live UI). Reading the exact message
     text needs a NEW testid (see Concrete Handles — `needs-adding`); the
     `aria-invalid` half needs none.

4. Verify the "Approve" / "Create Agent" button is inactive/disabled.
   - **Verify**: live-confirmed this run — `generate-agent-approve-button`
     (existing `LocatorDescriptor`, label "Create Agent") is `disabled`;
     `is_enabled()` returns `False`. Attempting `.click()` on it while
     disabled would time out (Playwright's actionability check), exactly
     the failure-mode footgun ELITEA-1912's own memory entry documents —
     implementer should assert `is_enabled() is False`, never attempt the
     click.

5. Trim the name to exactly 32 characters.
   - **Verify**: live-confirmed this run — Name field's DOM value length ==
     32 after trimming (build the 32-char string programmatically, don't
     hand-count a literal — see Test Data).

6. Verify the validation error clears and the button becomes active.
   - **Verify**: live-confirmed this run — at exactly 32 characters,
     `aria-invalid` flips to `"false"`, the "Name must be 32 characters or
     less" helper text disappears (the character-counter widget
     independently confirms this too: it read "0 characters left" at
     exactly 32, vs. "-8 characters left" at 40 — a second, UI-visible
     confirmation channel beyond the field's own validation state, see
     Axis 2), AND `generate-agent-approve-button` becomes `is_enabled() ==
     True` again.

## Expected Results
Matches the case's stated Pass criteria and Expected Final State exactly:
the Build-with-AI review form's Name field enforces `MAX_NAME_LENGTH = 32`
via client-side JS validation (NOT a native `maxlength` clamp — that
distinction is itself part of what this case newly proves): typing beyond
32 characters is accepted into the DOM value (no truncation), which
triggers `aria-invalid="true"` + a visible "Name must be 32 characters or
less" error message + a disabled Create Agent button; trimming back to
exactly 32 characters clears the error and re-enables the button. Live
end-to-end this run, no functional defect.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: draft generated, review form displayed | review form displayed | step 1 | already covered — ELITEA-1906 Steps 1-4; re-confirmed here as this case's own entry point | asserted |
| 1 Generate draft, enter review form | review form displayed | step 1 | field present + interactable | asserted |
| 2 Edit Name to >32 chars | field shows over-limit text | step 2 | DOM value length == 40 | asserted |
| 3 Validation message shown | error message displayed near Name field | step 3 | `aria-invalid="true"` + helper-text == "Name must be 32 characters or less" | asserted — **genuinely new, not proven by ELITEA-1900 or ELITEA-1912** |
| 4 Approve/Create Agent button disabled | button inactive | step 4 | `generate-agent-approve-button.is_enabled() == False` | asserted — **genuinely new** |
| 5 Trim to exactly 32 chars | field shows trimmed 32-char name | step 5 | DOM value length == 32 | asserted |
| 6 Validation error clears, button active | error disappears, button enabled | step 6 | `aria-invalid="false"`, helper-text gone, `is_enabled() == True` | asserted — **genuinely new** |

### Axis 2 — Analyst additions

- Step 2 asserts the **absence of native truncation** on this field (DOM
  value reaches the full 40 chars typed, no clamp) — *added: this is the
  opposite of `agent-name-input`'s behavior (ELITEA-1900) and is exactly
  the mechanism difference that makes this case non-duplicate; asserting it
  explicitly documents the contract for future readers who might otherwise
  assume the two Name fields behave identically.*
- Step 6 documents the character-counter widget ("N characters left" /
  "-N characters left") as a **second, independent confirmation channel**
  for the validation boundary — *added: gives the implementer an optional
  extra-confidence assertion beyond `aria-invalid`/helper-text/button-state,
  not required to satisfy the case's own Pass criteria.*
- **Console side-channel finding, not filed as a new issue — already
  tracked.** The same `"does not recognize the disableUnderline prop"`
  React warning already tracked as
  [EliteaAI/elitea-testing-public#1050](https://github.com/EliteaAI/elitea-testing-public/issues/1050)
  (and already noted from this exact entry point by ELITEA-1906/1912's own
  AFS files) fired again this run. Not re-filed, not re-commented — noted
  here only so the implementer isn't surprised by it.
- **Design-note, not a defect (deliberately NOT filed as a bug or
  clarification):** the review form's Name field lacks the native
  `maxlength` clamp its sibling `agent-name-input` field has (see
  Triangulation). This is an inconsistency between two Name fields in the
  same app, but it does not fail this case's own Pass/Fail criteria (which
  only asks about the error-message + button-disable + clear-at-32
  contract, not about truncation) — showing an inline validation error is
  an equally valid UX pattern to silent truncation, arguably a stronger
  one. Recorded here for the implementer's awareness only, so nobody
  mistakes it for a regression this test should assert differently.

## Cleanup
1. No product state left behind — the test never clicks Approve to
   completion (it stays disabled through the over-limit assertion, and
   even once re-enabled at exactly 32 chars, no click is required by this
   case's own Pass criteria). Close the modal via
   `generate-agent-close-button` (or navigate away) to leave a clean state.
   Confirmed live this run: closing the modal after these steps left no
   draft/agent behind (no `POST .../applications/...` ever fired — only
   `POST .../generate_application_draft/...` did, confirmed via network
   request log).
2. No API cleanup fixture needed.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| "Build with AI" open button | `generate-agent-open-button` | on-`automation/testids` ✓ (pre-existing) | n/a — already present |
| Prompt input | `generate-agent-prompt-input` | on-`automation/testids` ✓ | n/a — already present |
| Generate button | `generate-agent-submit-button` | on-`automation/testids` ✓ | n/a — already present |
| Review-form Name input | `generate-agent-review-name-input` — existing `LocatorDescriptor` on `GenerateAgentModalPage` (`automation/pages/generate_agent_modal_page.py:103`) | on-`automation/testids` ✓ | n/a — already present |
| Review-form Name field's `aria-invalid` state | read via `.get_attribute("aria-invalid")` on the EXISTING `review_name_input` locator — no new testid, this is an attribute check on an already-testid'd element | on-`automation/testids` ✓ (uses existing handle) | n/a |
| Review-form Name field's validation error TEXT (MUI `FormHelperText`, "Name must be X characters or less") | **testid needed: `generate-agent-review-name-helper-text`** (naming matches the established sibling precedent — the Skill Build-with-AI review form already added `generate-skill-review-name-helper-text` for the identical element, `daily/2026-08-02.md`/EliteaUI commit `8e78723b`). `Input.InputBase` (`EliteaUI/src/[fsd]/shared/ui/input/InputBase.jsx`) currently threads NO testid prop for its `helperText`/`FormHelperText` element (source-confirmed, grepped the file — none found). Per role-overrides.md "shared components never hardcode feature-scoped testids": add a NEW explicitly-destructured `helperTextTestId` prop to `Input.InputBase` (same pattern as the file's existing `tooltipTestId`/`tooltipContentTestId` props), and wire it into the component's OWN internally-built `slotProps` object at `formHelperText: { 'data-testid': helperTextTestId }` (that object is constructed at `InputBase.jsx:260-277` — add the key there). **Do NOT have the caller pass a raw `slotProps.formHelperText` prop instead** — confirmed via source read (see Triangulation's root-cause note) that any `slotProps` the caller passes is silently dropped by this same component, which is exactly why the Name field's `maxLength` never reaches the DOM either; only a prop `InputBase` itself explicitly destructures and threads through survives. Then set `helperTextTestId="generate-agent-review-name-helper-text"` at the ONE call site this case touches — `GenerateAgentReviewForm.jsx`'s Name field (`~line 94-108`) only, not the other 4 fields (scope discipline — this case's test never asserts their error text). | **needs-adding** | n/a — the `aria-invalid` half of Step 3/4 is testable without this; only the exact-message-text assertion needs it |
| "Create Agent" approve button | `generate-agent-approve-button` — existing `LocatorDescriptor` (`automation/pages/generate_agent_modal_page.py:88`), read via `.is_enabled()` | on-`automation/testids` ✓ | n/a — already present |
| Modal close button | `generate-agent-close-button` | on-`automation/testids` ✓ | n/a — already present |

**Summary for the implementer:** one small `add-data-testid` job — thread a
`helperTextTestId` prop through the shared `Input.InputBase` component and
wire it at the Name field's call site in `GenerateAgentReviewForm.jsx`
only. Everything else (the field itself, `aria-invalid` reads, the approve
button, open/close/generate controls) already has a testid and is reused
as-is. If the implementer judges the `aria-invalid` + button-disabled pair
already satisfies the case's Step 3/4 intent strongly enough without the
exact message text, that is a legitimate lighter-weight option — but per
role-overrides.md this AFS does not soften the testid request itself; it's
offered as implementer discretion on ASSERTION STRENGTH, not as license to
skip the testid work if the message text ends up asserted.

## Network Behavior
- `POST /api/v2/elitea_core/generate_application_draft/prompt_lib/400` →
  `200` — generates the draft (mocked or live, implementer's discretion).
- No other `elitea_core` network call fires during Steps 2-6 — confirmed
  live via the full network request log after the typing/validation
  sequence: only the one `generate_application_draft` POST is present,
  everything else is static assets. The validation itself is 100%
  client-side (`validateAgentDraft()`), consistent with `agentDraftValidation.helpers.js`
  being a pure function with no API calls.

## Known Defects Found During Exploration
None. All 6 case steps executed live end-to-end against the real DEV
backend with no functional defect — the field correctly enforces the
32-char limit via its validation-message + button-disable mechanism, and
correctly clears at exactly 32. The lack of a native `maxlength` clamp on
this specific field (vs. its sibling `agent-name-input`) is recorded as a
design-note/Axis-2 observation, not a defect — see Coverage Map § Axis 2
for why it doesn't fail this case's own Pass/Fail criteria.

## Blocked Steps
None. All case steps executed live.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Home:
  `automation/tests/ui/agents/test_agent_build_with_ai.py` — same file as
  ELITEA-1906/1909/1911/1912/1914, reusing `GenerateAgentModalPage` and the
  existing draft-generation setup helper. A new test method (this case
  doesn't extend an existing one — no existing method reaches the
  over-limit boundary) in either the existing
  `TestAgentBuildWithAIDraftFieldPopulation` class or a new sibling class,
  implementer's call.
- **Use real keystroke typing (`press_sequentially()` / Playwright's
  `type(slowly=True)`), NOT `.fill()`, for Step 2's over-limit input.**
  `.fill()` also works for this field (confirmed by ELITEA-1912's own
  finding that `.fill()` bypasses the limit too, since — unlike
  `agent-name-input` — this field has no native `maxlength` at all), but
  real keystrokes are the more faithful simulation of the case's own
  "Edit the Name field" step and match what a real user does, and this run
  used keystroke typing throughout to get the cleanest live signal.
- Wait strategy: `wait_for_review_form()` (existing) after Generate Draft;
  no waits needed for the validation state changes themselves — they're
  synchronous client-side React state updates (confirmed by the network
  log showing zero requests during Steps 2-6), so a direct
  `input_value()`/`get_attribute()`/`is_enabled()` read immediately after
  the type action is sufficient, no polling or `wait_for_timeout` needed.
- No cleanup fixture needed — read-only case, confirmed live (see Cleanup).
