# Test Case: Max Context Tokens does not accept non-numeric or negative values

## Metadata
- **TMS ID**: ELITEA-2391
- **Linked Story**: EliteaAI/elitea-testing-public#899
- **Priority**: l3
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (analyst slot), batch `elitea-2391-max-context-tokens`
- **Status**: extend-existing

## Extension target

- **Covering spec**: `automation/tests/ui/settings/test_context_management_toggle.py`
  (`class TestContextManagementToggle`, merged to `automation/base`, commit `3ea450cc`).
  New test method appended to this class, mirroring the additive mechanic already
  used twice in this class (`test_automatic_summarization_toggle_enables_disables_own_fields`
  for ELITEA-2377, `test_target_summary_tokens_range_validation` for ELITEA-2378).
- **Covering AFS**: `test-specs/settings-user-profile/l3_context-management-toggle-enables-disables-fields_ELITEA-2374.md`.
- **Behavioural overlap**: the covering ELITEA-2374 spec already reaches
  `/settings/memory`, drives `UserProfileSettingsPage`, enables Context
  Management, and reads/round-trips the Max Context Tokens value (as a
  precondition side effect of testing the toggle's mount/unmount behaviour).
  What it does **not** cover is this case's actual observable: Max Context
  Tokens' own **client-side rejection of non-numeric and negative input**.
  Confirmed via `grep -n "abc\|non.numeric\|negative\|aria-invalid" automation/tests/ui/settings/test_context_management_toggle.py`
  → no hits outside the new ELITEA-2378 method (which tests a different
  field, Target Summary Tokens). No existing spec exercises Max Context
  Tokens' own validation.
- **Extension mechanic**: additive — a new `test_max_context_tokens_rejects_non_numeric_and_negative_input`
  method appended to the same `TestContextManagementToggle` class, sharing
  the same module-level `_is_autosave_put_response` / `_is_autosave_get_response`
  helpers, `AUTOSAVE_PUT_PATH`/`UI_ELEMENT_TIMEOUT`/`AUTOSAVE_TIMEOUT` constants,
  and the negative-wait pattern already established by
  `test_target_summary_tokens_range_validation` (steps 5/6). The three
  existing test methods are byte-identical after this change.

## Preconditions
- User is logged in to the Elitea platform (`auth_state` fixture).
- No project-level precondition — this is a per-user profile setting.
- Context Management (parent toggle) must be ON for Max Context Tokens to be
  visible/mounted at all (conditional-unmount mechanism, see the covering
  ELITEA-2374 spec's class docstring and `_surface.md`).

## Test Data
### reuse-existing
- No fixed test data required — the test types transient invalid/valid
  values into the field and restores the original value at the end. The
  shared `${TEST_USER}` account currently has Max Context Tokens = `10000`
  (confirmed live this session, restored to this value after exploration) —
  **do not hard-assert this as a platform default**; read-and-restore.
- Case step values used verbatim (matches the case text, no invented
  boundary values): `"abc"` (non-numeric), `"-100"` (negative), `64000`
  (valid — the case's own example, and coincidentally the platform default
  per `DEFAULT_CONTEXT_STRATEGY.MAX_CONTEXT_TOKENS`).

## Test Steps
1. Navigate to `${BASE_URL}/settings/memory` (Settings → Memory tab).
   - **Verify**: the "Context Management" accordion section
     (`context-management-section`) is visible and expanded by default.
2. Ensure Context Management is enabled (precondition). If OFF, turn it ON
   via `context-management-toggle` and wait for the autosave round-trip
   (`PUT /api/v2/social/author/` → 200).
3. Verify Max Context Tokens (`max-context-tokens-input`) is visible and
   enabled. Read its current value and store as `original_max_tokens` for
   the restore step at the end.
4. Type `"abc"` into Max Context Tokens (select-all + type, character by
   character — see Automation Hints) and blur (Tab).
   - **Verify**: the field ends up **empty** — confirmed live: the field's
     onChange handler (`handleConvertToNumberChange`, shared with the
     sibling Target Summary Tokens field) strips every non-digit character
     as typed, so `"abc"` (zero digits) reduces to an empty string.
   - **Verify**: the input is invalid (`aria-invalid="true"` on
     `max_context_tokens_input`) and the helper text reads **"This field is
     required"** (confirmed live — the field is `required` when
     `context_enabled` is true).
   - **Verify**: no autosave `PUT /api/v2/social/author/` fires within a
     short bounded wait (validation blocks the submit — same
     `useFormikAutoSaveOnBlur` mechanism as the covering ELITEA-2378 test).
5. Type `"-100"` into Max Context Tokens (select-all + type) and blur (Tab).
   - **Verify**: the field ends up showing **`"100"`, not `"-100"`** —
     confirmed live: the same digit-only filter strips the minus-sign
     keystroke before it ever reaches Formik state; the remaining digits
     (`"100"`) are what the field actually holds.
   - **Verify**: the input is invalid (`aria-invalid="true"`) and the helper
     text reads **"Max tokens must be at least 1,000"** — confirmed live:
     `100` is evaluated against `VALIDATION_LIMITS.MAX_CONTEXT_TOKENS.MIN = 1000`
     and fails the minimum, not a "negative rejected" message (there is no
     such message in the schema — the app structurally prevents a literal
     negative number from ever reaching the field, so it is always the
     min-boundary error that fires for a typed negative).
   - **Verify**: no autosave PUT fires (same mechanism as step 4).
6. Type `64000` into Max Context Tokens (select-all + type) and blur (Tab).
   - **Verify**: the input is valid (`aria-invalid` absent/`"false"`).
   - **Verify**: autosave PUT `/api/v2/social/author/` fires → 200, and the
     response body's `default_context_management.max_context_tokens` equals
     `64000` (confirms the value actually persisted, not just that a
     request fired).
7. Restore Max Context Tokens to `original_max_tokens` (step 3) and blur;
   verify the autosave PUT fires → 200 (cleanup — leaves the shared
   `${TEST_USER}` account as found).

## Expected Results
- Non-numeric input (`"abc"`) never reaches the field as typed — the
  onChange handler filters every non-digit keystroke, so the field ends up
  empty and shows the `required` validation error. No autosave PUT fires.
- Negative input (`"-100"`) is likewise never literally entered — the
  minus-sign keystroke is stripped before Formik ever sees it, so the field
  ends up holding the unsigned digits (`"100"`), which then fails the
  schema's `min(1000)` boundary. No autosave PUT fires.
- Both outcomes satisfy the case's Title/Objective ("does not accept
  non-numeric or negative values") and steps 3/5 ("verify the input is
  rejected") — see Coverage Map for the literal step 2/4 text mismatch,
  which is case-text drift, not a product defect.
- A valid value (`64000`) is accepted: no invalid state, and the value
  autosaves via `PUT /api/v2/social/author/` → 200, confirmed by the
  response body echoing the new value back.
- No console errors during the flow beyond the one pre-existing, unrelated
  `disableUnderline`/`disableunderline` MUI DOM-attribute warning already
  noted in the covering ELITEA-2377/ELITEA-2378 AFS's exploration (confirmed
  present again this session, same component tree, not new).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Personalization → DEFAULT CONTEXT MANAGEMENT | Target page/section loads | AFS step 1 | step 1: `context-management-section` visible (reused pattern from covering spec) | clarification *(route is Settings → Memory, not Personalization — same stale case-text pattern as ELITEA-2374/2377/2378, already covered by EliteaAI/elitea-testing-public#1238, no new ticket needed)* |
| 2 Clear Max Context Tokens and enter "abc" | "Action completes without error and produces the expected UI state" | AFS step 4 (part 1) | step 4: field typed with "abc", blurred | clarification *(text implies "abc" is accepted/entered as typed; live behaviour is that non-digit keystrokes are filtered client-side before they reach the field at all, so the field ends up empty, not showing "abc". Filed EliteaAI/elitea-testing-public#1247.)* |
| 3 Verify the input is rejected | Condition holds | AFS step 4 (part 2) | step 4: `aria-invalid="true"` + "This field is required" + no autosave PUT | asserted |
| 4 Enter "-100" | "Field accepts the input and displays the entered value" | AFS step 5 (part 1) | step 5: field typed with "-100", blurred | clarification *(text implies "-100" is accepted and displayed as entered; live behaviour is that the minus-sign keystroke is filtered client-side, so the field displays "100", not "-100" — a literal negative value can never reach this field. Filed EliteaAI/elitea-testing-public#1247, same issue as row above.)* |
| 5 Verify the input is rejected | Condition holds | AFS step 5 (part 2) | step 5: `aria-invalid="true"` + "Max tokens must be at least 1,000" + no autosave PUT | asserted |
| 6 Enter a valid value (e.g., 64000) | Field accepts the input and displays the entered value | AFS step 6 (part 1) | step 6: field set to `64000`, blurred | asserted |
| 7 Verify no validation error is shown | Condition holds | AFS step 6 (part 2) | step 6: `aria-invalid` absent + autosave PUT 200 with value echoed back | asserted |

### Axis 2 — Analyst additions
- AFS step 3 stores the pre-test value and AFS step 7 restores it —
  *added: the case has no explicit cleanup step, but this test mutates a
  shared account field; leaving it at `64000` would pollute `${TEST_USER}`
  for later sessions/tests if its pre-test value differed (it happened to
  already be `10000` this session). Same "leave as found" discipline as
  the covering ELITEA-2378 spec's restore step.*
- AFS steps 4/5 assert the field's ACTUAL DISPLAYED VALUE after the invalid
  keystrokes (empty / "100"), not just the error state — *added: this is
  the concrete, checkable form of the case Title's claim ("does not accept
  non-numeric or negative values") — it proves the app doesn't merely
  reject on submit, it structurally prevents the invalid characters from
  ever landing in the field, which is a stronger and more specific
  guarantee than "shows an error".*
- AFS step 6's response-body echo check — *added: same rationale as
  ELITEA-2378 step 7 — a bare 200 doesn't prove `64000` was the field that
  changed, since the endpoint returns the full author object regardless.*

## Cleanup
- AFS step 7 restores Max Context Tokens to the value read in step 3.
  Context Management is left ON (same as it started, per the precondition
  step) — no toggle state to restore.
- **Analyst session note**: during live exploration the field was
  temporarily set to `""` (via "abc"), `"100"` (via "-100"), then `64000`
  (autosaved, response confirmed `max_context_tokens: 64000`), then
  explicitly restored to `10000` (the pre-session value, confirmed via a
  final autosave PUT echoing `"max_context_tokens": 10000`) before ending
  the session — the shared `${TEST_USER}` account is not left polluted by
  this analysis pass.

## Concrete Handles (discovered during exploration)

| Element | Testid | PROVENANCE | Notes |
|---|---|---|---|
| Max Context Tokens input | `max-context-tokens-input` | on-main ✓ (per `_surface.md`'s testid provenance table, unchanged this session) | Pre-existing. Declared on the page object (`user_profile_settings_page.py:74`) with a getter (`get_max_context_tokens()`) and a setter (`set_max_context_tokens(value: int)`, line 303) — **the existing setter is not directly reusable for this case** (see Automation Hints: it types `str(int)` only, so it cannot type `"abc"`; and it unconditionally calls `wait_for_autosave()` internally, which the invalid-value steps must NOT rely on for their no-PUT assertion). |
| Context Management toggle, Context Management section | `context-management-toggle`, `context-management-section` | on-main ✓ | Reused precondition helpers, no change. |
| Max Context Tokens validation state | **N/A — no new testid.** Assert via the standard `aria-invalid` ARIA attribute on the already-testid'd `max_context_tokens_input` (`expect(...).to_have_attribute("aria-invalid", "true")` / not present when valid). | n/a | Confirmed live: MUI sets `aria-invalid` on the `<input>` when the `TextField`'s `error` prop is true (`MemoryContextManagement.jsx`: `error={!!errors.max_context_tokens}`). State via a standard attribute on a stable testid'd element — compliant with `.agents/testing.md` § Locator policy, same pattern as the covering ELITEA-2378 spec used for Target Summary Tokens. |
| Max Context Tokens error message text (helper text `<p>`, e.g. "This field is required" / "Max tokens must be at least 1,000") | **testid needed: `max-context-tokens-error-text`** | needs-adding | **Optional strengthening, not required for the case's pass/fail contract** (same call as ELITEA-2378's equivalent row). The required assertions (Coverage Map rows 3/5) are satisfiable via `aria-invalid` + the field's actual displayed value alone. If the implementer wants to additionally assert the exact message text, add `FormHelperTextProps={{ 'data-testid': 'max-context-tokens-error-text' }}` to the `Input.StyledInputEnhancer` for Max Context Tokens in `MemoryContextManagement.jsx` (same prop-plumbing mechanism already confirmed to exist for Target Summary Tokens). If skipped, the AFS's required assertions still hold via `aria-invalid` + displayed value — not a blocker. |

## Network Behavior
- `PUT /api/v2/social/author/` — fires on blur (Tab) of the Max Context
  Tokens field **only when the resulting value passes Yup validation**
  (`useFormikAutoSaveOnBlur` calls `validateForm()` before `submitForm()`).
  Confirmed live:
  - `"abc"` → field ends up empty → blur: **no PUT** (required-error
    blocked it).
  - `"-100"` → field ends up `"100"` → blur: **no PUT** (min-error blocked
    it).
  - `64000` → blur: `PUT` → `200`, response body:
    `"default_context_management": {..., "max_context_tokens": 64000}`.
- `GET /api/v2/social/author/` — refetches after a successful PUT, same
  pattern as the covering specs.
- Validation limits confirmed at the source (`EliteaAI/EliteaUI`
  `automation/testids`,
  `src/[fsd]/widgets/context-budget/lib/constants.js`):
  `VALIDATION_LIMITS.MAX_CONTEXT_TOKENS = { MIN: 1000, MAX: 10000000 }`,
  consumed by the Yup schema in
  `src/[fsd]/features/settings/lib/helpers/profile.helpers.js`
  (`profileValidationSchema.max_context_tokens.min(1000).max(10000000)`,
  `.typeError('Please enter a valid number')`, `.integer('Must be a whole
  number')`, `.required('This field is required')` when
  `context_enabled: true`).
- **Onchange character filter is the actual mechanism behind "rejects
  non-numeric/negative" — confirmed at the source**:
  `handleConvertToNumberChange` (`src/[fsd]/widgets/context-budget/lib/validation.js:169-173`)
  runs `value.replace(/[^0-9]/g, '')` on every keystroke before
  `setFieldValue` — this is the SAME handler used by the sibling Target
  Summary Tokens field (confirmed: `MemorySummarization.jsx:34` calls the
  identical function). It strips letters AND the minus sign identically;
  there is no separate "reject negative" code path — a negative number
  structurally cannot exist in Formik state for either field, only its
  unsigned digits can, which then get evaluated against `min()`.

## Known Defects Found During Exploration
- None. The product's behaviour is stricter/more defensive than a naive
  reading of the case text suggests (it prevents invalid characters from
  ever being entered, rather than merely rejecting on submit) — this is
  correct, intentional behaviour, not a bug.
- **New clarification filed**:
  [EliteaAI/elitea-testing-public#1247] — case steps 2/4's literal Expected
  Result text implies the raw invalid string is accepted/displayed as
  typed; live product filters it client-side before it's ever entered. See
  Coverage Map rows 2/4.
- The existing clarification **[EliteaAI/elitea-testing-public#1238]**
  already covers this case's route drift (Personalization → DEFAULT
  CONTEXT MANAGEMENT doesn't exist; live route is Settings → Memory) — no
  new ticket needed, same root cause as ELITEA-2374/2377/2378.

## Blocked Steps
- None. All case elements are covered (see Coverage Map — the three
  "clarification" dispositions are case-text drift, not blockers; all are
  fully automatable against the live/correct behavior).

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- Page object: `automation/pages/user_profile_settings_page.py` — **extend,
  don't duplicate**. Additions needed this implementation:
  1. New method `type_max_context_tokens_raw(text: str) -> None`, mirroring
     `set_target_summary_tokens()`'s "no wait baked in" shape rather than
     `set_max_context_tokens()`'s (click + `fill("")` + `type(text, delay=50)`
     + `press("Tab")` — no `wait_for_autosave()` call, no `int` coercion of
     the input). This is necessary because:
     - the existing `set_max_context_tokens(value: int)` cannot type a
       literal non-numeric string like `"abc"` (its signature forces
       `str(int)`);
     - it unconditionally calls `wait_for_autosave()` after every set,
       which does not reliably distinguish "PUT fired" from "PUT did not
       fire" (see its docstring — best-effort networkidle wait, silently
       falls back to a fixed 1s sleep on timeout) — the test needs an
       explicit `page.on("response", ...)` listener (or
       `page.expect_response(...)`) around the call instead, exactly the
       pattern already used by `test_target_summary_tokens_range_validation`.
     Do NOT modify `set_max_context_tokens()` itself — it is used unchanged
     by the existing `test_context_management_toggle_enables_disables_fields`
     test (ELITEA-2374); this case needs a sibling method, not a
     behavioural change to the shared one. This mirrors exactly the
     `set_target_summary_tokens()` precedent added for ELITEA-2378 (see
     that method's docstring for the same reasoning, applied here to the
     sibling field).
  2. No new getter needed — `get_max_context_tokens()` already exists and
     is directly reusable for reading `original_max_tokens` in step 3 and
     the restore value in step 7 (note: it raises `ValueError` if the field
     is non-numeric per its docstring — only call it when the field is
     expected to hold a valid integer, i.e. NOT immediately after typing
     `"abc"`/`"-100"`; read the field's raw displayed value via
     `max_context_tokens_input.input_value()` directly for steps 4/5's
     "field shows X" assertions instead, matching how the case's Coverage
     Map frames those checks).
- Test file: `automation/tests/ui/settings/test_context_management_toggle.py`
  — append `test_max_context_tokens_rejects_non_numeric_and_negative_input`
  to the existing `TestContextManagementToggle` class (same file, same
  class, same module-level `_is_autosave_put_response` /
  `_is_autosave_get_response` helpers and `AUTOSAVE_PUT_PATH`/
  `UI_ELEMENT_TIMEOUT`/`AUTOSAVE_TIMEOUT` constants). Do NOT create a new
  file or class. Verify with
  `git diff <base>... -- automation/tests/ui/settings/test_context_management_toggle.py | grep -E '^-[^-]'`
  → empty (no modification to any of the three existing test methods).
- For steps 4/5 (asserting NO autosave PUT fires), reuse the exact
  bounded-negative-wait pattern from
  `test_target_summary_tokens_range_validation` steps 5/6: register a
  `page.on("response", _capture_put)` listener before the blur, blur
  (inside `type_max_context_tokens_raw`), wait a fixed 2s bound, then
  assert the listener never saw a PUT to `AUTOSAVE_PUT_PATH`, and
  `page.remove_listener(...)` in a `finally`. Same reasoning as that
  test's docstring: `validateForm()` gates `submitForm()` synchronously on
  blur, so 2s comfortably exceeds any debounce/validation cycle observed
  live without inflating runtime.
- Step 6's value-echo assertion: read the PUT response JSON body via
  `page.expect_response(...).value.json()["default_context_management"]["max_context_tokens"]`
  and compare to `64000`. Follow the existing `expect_response` +
  `put_info.value` pattern already used throughout
  `test_context_management_toggle.py` (see
  `test_target_summary_tokens_range_validation` step 7 for the closest
  analogue, adjusted for the `default_context_management` response key
  instead of `default_summarization`).
- Steps 4/5's "field shows empty" / "field shows 100" assertions: use
  `expect(profile.max_context_tokens_input).to_have_value("")` and
  `expect(profile.max_context_tokens_input).to_have_value("100")`
  respectively (Playwright's `to_have_value` on the input element — no new
  testid needed, reuses the existing `max-context-tokens-input` field).
