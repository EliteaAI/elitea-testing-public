# Test Case: Target Summary Tokens range is 100–4096

## Metadata
- **TMS ID**: ELITEA-2378
- **Linked Story**: EliteaAI/elitea-testing-public#886
- **Priority**: l3
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (analyst slot), batch `target-summary-tokens-range-2378`
- **Status**: extend-existing

## Extension target

- **Covering spec**: `automation/tests/ui/settings/test_context_management_toggle.py`
  (`class TestContextManagementToggle`, merged to `automation/base`). New test
  method appended to this class, mirroring the additive mechanic already used
  by `test_automatic_summarization_toggle_enables_disables_own_fields`
  (ELITEA-2377, `lextend_automatic-summarization-toggle-enables-disables-fields_ELITEA-2377.md`).
- **Covering AFS**: `test-specs/settings-user-profile/l3_context-management-toggle-enables-disables-fields_ELITEA-2374.md`
  + `test-specs/settings-user-profile/lextend_automatic-summarization-toggle-enables-disables-fields_ELITEA-2377.md`.
- **Behavioural overlap**: the covering specs already reach `/settings/memory`,
  drive `UserProfileSettingsPage`, and enable Context Management + Automatic
  Summarization so the Target Summary Tokens field is visible/enabled. What
  they do **not** cover is this case's actual observable: the field's own
  **client-side min/max validation** (100–4096) — neither ELITEA-2374 nor
  ELITEA-2377 types an out-of-range value into it or reads its error state;
  ELITEA-2377 only reads the field's value and clicks the parent toggle.
  Grepped `automation/tests/ui/settings/` and `test-specs/` first — confirmed
  no existing spec exercises this boundary (see Intake notes on the case
  snapshot for the same conclusion, reached independently here by re-reading
  the merged test file directly: `grep -n "100\|4096\|4097\|validation"
  automation/tests/ui/settings/test_context_management_toggle.py` → no hits).
- **Extension mechanic**: additive — a new
  `test_target_summary_tokens_range_validation` method appended to the same
  `TestContextManagementToggle` class, sharing the same module-level
  autosave-wait helpers and the same `UserProfileSettingsPage` page object.
  The two existing test methods are byte-identical after this change.

## Preconditions
- User is logged in to the Elitea platform (`auth_state` fixture).
- No project-level precondition — this is a per-user profile setting.
- Context Management (parent toggle) AND Automatic Summarization (its own
  toggle) must both be ON for Target Summary Tokens to be visible AND
  enabled — confirmed live and in source
  (`isSummarizationDisabled = !values.context_enabled || !values.enable_summarization`,
  `MemorySummarization.jsx`). Same precondition chain as ELITEA-2377.

## Test Data
### reuse-existing
- No fixed test data required — the test types transient invalid/valid
  values into the field and restores the original value at the end. The
  shared `${TEST_USER}` account currently has Target Summary Tokens = `4096`
  (confirmed live this session) — **do not hard-assert this as a platform
  default**, same caveat as the sibling cases; read-and-restore instead.
- Case step values used verbatim (matches the case text exactly, so no
  invented boundary values): `99` (below min), `4097` (above max), `200`
  (in-range).

## Test Steps
1. Navigate to `${BASE_URL}/settings/memory` (Settings → Memory tab).
   - **Verify**: the "Context Management" accordion section
     (`context-management-section`) is visible and expanded by default.
2. Ensure Context Management is enabled (precondition). If OFF, turn it ON
   via `context-management-toggle` and wait for the autosave round-trip
   (`PUT /api/v2/social/author/` → 200).
3. Ensure Automatic Summarization is enabled (precondition — Target Summary
   Tokens is disabled while it's OFF, per the ELITEA-2377 mechanism). If
   OFF, turn it ON via `automatic-summarization-toggle` and wait for the
   autosave round-trip.
4. Verify Target Summary Tokens (`target-summary-tokens-input`) is visible
   and enabled. Read its current value and store as `original_target_tokens`
   for the restore step at the end.
5. Set Target Summary Tokens to `99` (below the minimum) and blur (Tab).
   - **Verify**: the input is invalid (`aria-invalid="true"` —
     `to_have_attribute("aria-invalid", "true")` on `target_summary_tokens_input`;
     no new testid needed, this is a standard ARIA attribute on the
     already-testid'd field).
   - **Verify**: no autosave `PUT /api/v2/social/author/` fires within a
     short bounded wait (validation blocks the submit — confirmed via
     `useFormikAutoSaveOnBlur.hooks.js`: `attemptSubmit()` calls
     `validateForm()` first and returns early without calling
     `submitForm()` when errors are non-empty).
6. Set Target Summary Tokens to `4097` (above the maximum) and blur (Tab).
   - **Verify**: same invalid-state assertion as step 5.
   - **Verify**: no autosave PUT fires (same mechanism).
7. Set Target Summary Tokens to `200` (in range) and blur (Tab).
   - **Verify**: the input is valid (`aria-invalid` absent/`"false"`).
   - **Verify**: autosave PUT `/api/v2/social/author/` fires → 200, and the
     response body's `default_summarization.target_summary_tokens` equals
     `200` (confirms the value actually persisted, not just that a request
     fired).
8. Restore Target Summary Tokens to `original_target_tokens` (step 4) and
   blur; verify the autosave PUT fires → 200 (cleanup — leaves the shared
   `${TEST_USER}` account as found).

## Expected Results
- Values below 100 or above 4096 are rejected client-side: the field enters
  an invalid ARIA state and the autosave submit is blocked (Formik
  `validateForm()` gates `submitForm()` in `useFormikAutoSaveOnBlur`).
- A value inside `[100, 4096]` is accepted: no invalid state, and the value
  autosaves via `PUT /api/v2/social/author/` → 200, confirmed by the
  response body echoing the new value back.
- No console errors during the flow beyond the one pre-existing, unrelated
  `disableUnderline`/`disableunderline` MUI DOM-attribute warning already
  noted in the covering ELITEA-2377 AFS's exploration (confirmed present
  again this session, same component tree, not new).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Personalization → DEFAULT SUMMARIZATION | Target page/section loads | AFS step 1 | step 1: `context-management-section` visible (reused pattern from covering spec) | clarification *(route is Settings → Memory, not Personalization; "DEFAULT SUMMARIZATION" is the "Automatic Summarization" sub-section — same stale case-text pattern as ELITEA-2374/2377, already covered by EliteaAI/elitea-testing-public#1238, no new ticket needed)* |
| 2 Set Target Summary Tokens to 99 | Action completes | AFS step 5 (part 1) | step 5: field set to `99`, blurred | asserted |
| 3 Verify a validation error is shown (below minimum of 100) | Condition holds | AFS step 5 (part 2) | step 5: `aria-invalid="true"` + no autosave PUT | asserted *(confirmed live: helper text reads "Target tokens must be at least 100")* |
| 4 Set Target Summary Tokens to 4097 | Action completes | AFS step 6 (part 1) | step 6: field set to `4097`, blurred | asserted |
| 5 Verify a validation error is shown (above maximum of 4096) | Condition holds | AFS step 6 (part 2) | step 6: `aria-invalid="true"` + no autosave PUT | asserted *(confirmed live: helper text reads "Target tokens cannot exceed 4,096")* |
| 6 Set Target Summary Tokens to 200 | Action completes | AFS step 7 (part 1) | step 7: field set to `200`, blurred | asserted |
| 7 Verify no validation error is shown and Save is enabled | Condition holds | AFS step 7 (part 2) | step 7: `aria-invalid` absent + autosave PUT 200 with value echoed back | clarification *(there is no "Save" button anywhere on `/settings/memory` — the page autosaves on blur; "Save is enabled" has no live analog. Filed EliteaAI/elitea-testing-public#1244. The correct automated equivalent — "no error, and the value persists via autosave" — is what AFS step 7 actually asserts.)* |

### Axis 2 — Analyst additions
- AFS step 4 stores the pre-test value and AFS step 8 restores it —
  *added: the case has no explicit cleanup step, but this test mutates a
  shared account field (unlike ELITEA-2374/2377, which only read the value
  or round-tripped a toggle); leaving it at `200` would pollute
  `${TEST_USER}` for later sessions/tests. Same "leave as found" discipline
  as the covering specs' `finally` blocks.*
- AFS step 7 asserts the autosave response body's echoed field value, not
  just a 200 status — *added: a bare 200 doesn't prove `200` (the value)
  was the one persisted, since the endpoint returns the full author object
  regardless of which field changed; the value-echo check is what actually
  proves the boundary case saved correctly.*
- AFS steps 5/6 assert the ABSENCE of an autosave PUT within a bounded wait
  — *added: this is the concrete, checkable form of "a validation error is
  shown" blocking persistence; the case text only says "verify a validation
  error is shown," this makes the causal link (error → no save) explicit
  and testable, which is the actual point of a min/max *range* case.*

## Cleanup
- AFS step 8 restores Target Summary Tokens to the value read in step 4.
  Context Management and Automatic Summarization are left ON (same as they
  started, per the precondition steps) — no toggle state to restore.
- **Analyst session note**: during live exploration the field was
  temporarily set to `99`, `4097`, then `200` (autosaved), then explicitly
  restored to `4096` (the pre-session value, confirmed via a final autosave
  PUT #1698 echoing `"target_summary_tokens": 4096`) before ending the
  session — the shared `${TEST_USER}` account is not left polluted by this
  analysis pass.

## Concrete Handles (discovered during exploration)

| Element | Testid | PROVENANCE | Notes |
|---|---|---|---|
| Target Summary Tokens input | `target-summary-tokens-input` | on-automation/testids only (awaiting human promotion to main) | Pre-existing — added in the ELITEA-2377 session, `EliteaAI/EliteaUI@be73caea`. Already declared on the page object (`user_profile_settings_page.py:111`) with a getter (`get_target_summary_tokens()`); **no setter exists yet** — implementer must add one (see Automation Hints). |
| Context Management toggle, Automatic Summarization toggle, Context Management section | `context-management-toggle`, `automatic-summarization-toggle`, `context-management-section` | on-automation/testids only / on-main (see prior AFS provenance tables — unchanged this session) | Reused precondition helpers, no change. |
| Target Summary Tokens validation state | **N/A — no new testid.** Assert via the standard `aria-invalid` ARIA attribute on the already-testid'd `target_summary_tokens_input` (`expect(...).to_have_attribute("aria-invalid", "true")` / not present when valid). | n/a | Confirmed live: MUI sets `aria-invalid` on the `<input>` when the `TextField`'s `error` prop is true (`MemorySummarization.jsx`: `error={!!errors.summary_llm_settings?.max_tokens}`). This is state via a standard attribute on a stable testid'd element, not a state-switched testid — compliant with `.agents/testing.md` § Locator policy. |
| Target Summary Tokens error message text (`helper text` paragraph, e.g. "Target tokens must be at least 100") | **testid needed: `target-summary-tokens-error-text`** | needs-adding | **Optional strengthening, not required for the case's pass/fail contract.** The required assertion (Coverage Map rows 3/5) is satisfiable via `aria-invalid` alone. If the implementer wants to additionally assert the exact boundary message text (recommended — it is the strongest proof the min/max values are literally 100/4096, not just "some invalid state"), add `FormHelperTextProps={{ 'data-testid': 'target-summary-tokens-error-text' }}` to the `Input.StyledInputEnhancer` for Target Summary Tokens in `MemorySummarization.jsx` (MUI `TextField` forwards `FormHelperTextProps` to the underlying `FormHelperText` `<p>`; confirmed the prop plumbing exists via `InputBase.jsx`'s `{...leftProps}` spread onto `MuiTextField`). If the implementer skips this, the AFS's required assertions still hold via `aria-invalid` — do not treat the missing testid as a blocker. |

## Network Behavior
- `PUT /api/v2/social/author/` — fires on blur (Tab) of the Target Summary
  Tokens field **only when the typed value passes Yup validation**
  (`useFormikAutoSaveOnBlur` calls `validateForm()` before `submitForm()`).
  Confirmed live:
  - `99` → blur: **no PUT** (validation blocked it).
  - `4097` → blur: **no PUT**.
  - `200` → blur: `PUT` → `200`, response body:
    `"default_summarization": {..., "target_summary_tokens": 200}`.
- `GET /api/v2/social/author/` — refetches after a successful PUT, same
  pattern as the covering specs.
- Validation limits confirmed at the source (`EliteaAI/EliteaUI`
  `automation/testids`,
  `src/[fsd]/widgets/context-budget/lib/constants.js`):
  `VALIDATION_LIMITS.MAX_TOKENS = { MIN: 100, MAX: 4096 }`, consumed by the
  Yup schema in `src/[fsd]/features/settings/lib/helpers/profile.helpers.js`
  (`profileValidationSchema.summary_llm_settings.max_tokens.min(100).max(4096)`)
  — exactly matches the case's title and boundary values.

## Known Defects Found During Exploration
- None that block this case.
- **Contradicting evidence for the existing OPEN bug
  [EliteaAI/elitea-testing-public#1129]** ("numeric fields don't autosave
  when typed into directly"): this session's step 7 (`200` → blur) DID
  autosave successfully via `PUT` → 200 with the value echoed back in the
  response. Commented on #1129 with the reproduction details rather than
  closing it (agents don't close issues) — it's possible the defect is
  field-specific (only reproduces on Max Context Tokens / Preserve Recent
  Messages, not Target Summary Tokens) or was partially fixed since filing.
  Flagging for the implementer: if step 7's autosave assertion is
  unexpectedly flaky in CI, that's this bug's territory — soft-assert
  and link #1129 rather than treating it as a new defect.
- **New clarification filed**:
  [EliteaAI/elitea-testing-public#1244] — case text implies a "Save" button
  exists and becomes "enabled" (step 7 / Expected Final State); no such
  button exists anywhere on `/settings/memory` (autosave-only page). See
  Coverage Map row 7.
- The existing clarification **[EliteaAI/elitea-testing-public#1238]**
  already covers this case's route drift (Personalization → DEFAULT
  SUMMARIZATION doesn't exist; live route is Settings → Memory) — no new
  ticket needed, same root cause as ELITEA-2374/2377.

## Blocked Steps
- None. All case elements are covered (see Coverage Map — the two
  "clarification" dispositions are case-text drift, not blockers; both are
  fully automatable against the live/correct behavior).

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- Page object: `automation/pages/user_profile_settings_page.py` — **extend,
  don't duplicate**. Additions needed this implementation:
  1. New method `set_target_summary_tokens(value: int) -> None`, mirroring
     `set_max_context_tokens()` (click + `fill("")` + `type(str(value),
     delay=50)` + `press("Tab")` — MUI/React `onChange` requires keyboard
     events, not `fill()` alone, per `.claude/rules/mui-patterns.md`). Do
     **not** reuse `set_max_context_tokens()` by parameterizing the field —
     it currently waits for `wait_for_autosave()` unconditionally after
     every set, which is wrong here: an out-of-range value must NOT wait
     for/expect a PUT. Give the new method a `wait_for_autosave: bool =
     True` parameter (or let the test itself own the
     `page.expect_response(...)` context managers, matching the
     ELITEA-2377 test's pattern of wrapping the page-object call rather
     than baking the network wait into the page object) so the test can
     assert PUT/no-PUT explicitly per value.
  2. New method `is_target_summary_tokens_invalid() -> bool` (or use
     Playwright's `expect(...).to_have_attribute("aria-invalid", ...)`
     directly in the test, matching the existing `to_be_disabled()` /
     `to_be_enabled()` direct-expect style already used in the
     ELITEA-2377 test method — no getter needed for a boolean ARIA check).
- Test file: `automation/tests/ui/settings/test_context_management_toggle.py`
  — append `test_target_summary_tokens_range_validation` to the existing
  `TestContextManagementToggle` class (same file, same class, same
  module-level `_is_autosave_put_response` / `_is_autosave_get_response`
  helpers). Do NOT create a new file or class. Verify with
  `git diff <base>... -- automation/tests/ui/settings/test_context_management_toggle.py | grep -E '^-[^-]'`
  → empty (no modification to either existing test method).
- For steps 5/6 (asserting NO autosave PUT fires), use a short bounded
  negative wait — e.g. `page.wait_for_timeout` is normally forbidden per
  `.agents/testing.md`, but a bounded "assert this does NOT happen" check
  has no positive condition to wait on; the existing
  `test_context_management_toggle_enables_disables_fields` codebase has no
  established negative-wait helper. Recommended shape: register a
  `page.on("response", ...)` listener before the blur, blur, wait a fixed
  short bound (e.g. 2s — long enough to exceed the debounce/validation
  cycle observed live, short enough not to bloat runtime), then assert the
  listener never saw a PUT to `AUTOSAVE_PUT_PATH`. This is a legitimate use
  of a bounded wait for a negative assertion, not an arbitrary
  "hope it's enough" sleep — document the reasoning in the test's docstring
  if using this shape (there's no better proof-of-absence mechanism than
  bounding a wait, since `page.expect_response` only proves a positive).
- Value-echo assertion (step 7): read the PUT response JSON body via
  `page.expect_response(...).value.json()["default_summarization"]["target_summary_tokens"]`
  and compare to `200`. Follow the existing `expect_response` + `put_info.value`
  pattern already used throughout `test_context_management_toggle.py`.
