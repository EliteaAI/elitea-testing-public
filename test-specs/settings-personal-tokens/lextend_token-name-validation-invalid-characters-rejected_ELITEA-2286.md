# Test Case: Token name validation — only alphanumeric characters, underscores, and hyphens are allowed

## Metadata
- **TMS ID**: ELITEA-2286
- **Source case**: `.agents/automation/elitea-2286-token-name-validation/cases/ELITEA-2286.md`
  (snapshot; TMS module `settings-personal-tokens`)
- **Linked Story**: none
- **Priority**: l2 (high, per case frontmatter `priority: high`, mapped
  directly — `l2`/`p1` per this repo's `l<n>` convention, e.g.
  `l2_publish-draft-version-status-changes-unpublish-available_ELITEA-1892.md`.
  Sibling ELITEA-2280 on the same module/file is `l3`/`p2` (`priority:
  medium`) — this case's frontmatter genuinely says `high`, one notch above
  it, so it does **not** inherit the covering spec's module-level `p2`; see
  § Gap assertions for how the new test carries its own `p1` marker instead
  — identical trap and identical fix to the one already hit once on this
  exact file by ELITEA-2284, see
  `.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`
  § Recurrence variant).
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: extend-existing

## Extension target

**Covering spec**: `automation/tests/ui/admin/test_personal_token_create_and_verify.py`
(class `TestPersonalTokenCreateAndVerify`, method
`test_create_personal_token_and_verify_in_table`), merged to
`origin/automation/base` in PR #1174 (ELITEA-2280, commit `4ae8fdf0`).

**Behavioural-overlap argument**: this case's steps 7–8 ("leave the token
name field empty; verify the Generate button is disabled or an inline
validation error is shown") and steps 9–11 ("enter a valid name using only
allowed characters; verify no validation error is shown; verify Generate
becomes enabled") are **already asserted, verbatim in substance**, by the
covering spec's own **Step 3** (lines 92–104):

```python
assert create_page.generate_button.is_disabled(), (
    "Expected Generate disabled while the Name field is empty"
)
create_page.fill_name(token_name)
...
assert create_page.generate_button.is_enabled(), (
    "Expected Generate enabled once a valid name is entered"
)
```

`token_name` there is `f"autotest-token-{uuid.uuid4().hex[:8]}"` — a
run-unique value that is itself alphanumeric-plus-hyphen, i.e. it exercises
the exact same `[a-zA-Z0-9_-]` character class as this case's literal
example `"my_token-123"`. The observable ("empty name ⇒ Generate disabled";
"conforming name ⇒ no error, Generate enabled") is proven by the covering
spec against a fresh, never-touched form — no new assertion is needed for
that half of steps 7–11.

**Gap**: this case's steps 2–6 ("enter a name with special characters /
a space; verify a validation error is shown; verify Generate stays
disabled") have **zero existing coverage anywhere** in the merged suite
(grepped `TOKEN_NAME_PATTERN|name_error|validation.*error|invalid.*name`
across `automation/tests` and `test-specs/settings-personal-tokens/` — no
hit besides this AFS). Additionally, the case's own step 5 phrasing ("Clear
the name and enter a valid name") implies the valid-name-enables-Generate
transition happens **after** a prior invalid attempt, not from a pristine
empty form — the covering spec's Step 3 only proves the fresh-load
transition (empty → valid), never the invalid → valid recovery transition
(error message actually clearing, `nameHasError` flipping back to `false`).
That specific transition is also new and is folded into this AFS's Gap test
as its closing step (see § Test Steps step 4 / § Axis 2).

## Preconditions
- User is logged in to the Elitea platform (localhost dev-token auth).
- Active project is `${ELITEA_PROJECT_ID}` (399, "Private") — same project
  used by ELITEA-2277/2280/2284; not load-bearing for this case (name
  validation is pure client-side Formik/yup logic, no server round-trip is
  ever reached since Generate stays disabled for every invalid input tried
  here).
- No precondition on existing token data — this case is **fully read-only
  against the create-token FORM** and never clicks Generate, so it never
  creates a token and needs no cleanup (unlike ELITEA-2280).

## Test Data
### literal (from case text, verbatim — no run-uniqueness needed since
### nothing is submitted/persisted)
- Invalid, special-characters: `"my token!@#"` (case step 2's own example —
  contains both a space and `!@#`; confirmed live this fails the same
  regex branch as a bare space, see § Case-Text Note for why this makes
  case steps 2–4 and 5–6 redundant with each other but not with anything
  already covered).
- Invalid, space only: `"my token"` (case step 5's own example).
- Valid: `"my_token-123"` (case step 9's own example) — used here only to
  close the invalid→valid transition (§ Extension target Gap); the
  isolated "valid name ⇒ enabled, no error" observable is already covered
  by the merged spec's own generated name.

## Test Steps
1. From `${BASE_URL}/settings/tokens`, click the add-token button
   (`tokens_page.navigate()` + `tokens_page.click_add_button()`, both
   pre-existing) and wait for the New Token form to load
   (`create_page.wait_for_loaded()`).
   - **Verify**: the Name input is present and empty, and Generate starts
     disabled (light-touch presence check only — the full page-title/
     defaults assertion is the covering spec's Step 2, not repeated here).
2. Type `"my token!@#"` into the Name input (character-by-character, same
   `press_sequentially` mechanism the covering spec's `fill_name()` uses —
   required to trigger React's controlled-input `onChange`; a bulk `.fill()`
   would not, per `.claude/rules/mui-patterns.md`).
   - **Verify**: the Name input's value is `"my token!@#"` (input is
     accepted verbatim, not blocked character-by-character — confirmed
     live, see Known Defects / Case-Text Note).
   - **Verify**: the validation-error paragraph (testid needed —
     `create-personal-token-name-error`) is visible with exact text
     `"Only alphanumeric characters, underscore and hyphen are allowed"` —
     confirmed live via `yup.matches(TOKEN_NAME_PATTERN, ...)`'s message
     (`CreatePersonalToken.jsx:23`). **No explicit blur/Tab interaction is
     needed** — `Input.InputBase`'s `enableAutoBlur` default fires a real
     DOM blur+refocus ~10ms after every keystroke (`useAutoBlur.js`), which
     sets Formik's `touched.name` to `true` as a side effect of that real
     blur event — confirmed live, see § Automation Hints.
   - **Verify**: the Generate button (testid
     `create-personal-token-generate-button`, pre-existing) is disabled —
     confirmed live: `isGenerateDisabled` is `true` because
     `nameHasError` (`touched.name && Boolean(errors.name)`) is `true`
     (`CreatePersonalToken.jsx:88,91`), even though `formik.values.name` is
     non-empty — a **materially different disable mechanism** than the
     already-covered empty-name case (`!formik.values.name`).
3. Clear the Name input (select the full line — `Home` then `Shift+End` —
   and type over the selection; **do not use `Control+a`**, see § Automation
   Hints for why it's unreliable here) and type `"my token"` (space only,
   no other special characters).
   - **Verify**: the Name input's value is `"my token"`.
   - **Verify**: the same validation-error paragraph
     (`create-personal-token-name-error`) is visible with the same exact
     text — confirmed live: a bare space also fails `TOKEN_NAME_PATTERN =
     /^[a-zA-Z0-9_-]*$/` (same regex, same branch as step 2).
   - **Verify**: Generate is disabled — same mechanism as step 2.
4. Clear the Name input (same technique as step 3) and type `"my_token-123"`
   (allowed characters only).
   - **Verify**: the validation-error paragraph
     (`create-personal-token-name-error`) is **no longer present**
     (`to_have_count(0)` — MUI only renders `FormHelperText` when
     `helperText` is truthy; `getNameHelperText()` returns `undefined` once
     `formik.errors.name` clears, `CreatePersonalToken.jsx:93-101`) —
     confirmed live. This is the invalid→valid recovery transition the
     covering spec never exercises (its own happy path only ever sees a
     pristine empty→valid transition); see § Extension target Gap.
   - **Verify**: Generate is enabled — confirmed live.
5. **Verify no console error** was raised across steps 1–4 (side-channel
   check — confirmed live: 0 console errors, 0 warnings across this full
   negative-validation flow).

(This case never clicks Generate — every attempt with an invalid name
leaves the button disabled by design, and the one valid name reached in
step 4 is only entered to prove the error clears, not submitted. No token
is created; no cleanup is needed.)

## Expected Results
- Typing a name containing any character outside `[a-zA-Z0-9_-]` (special
  characters, spaces, or both) is accepted into the field's displayed value
  but triggers a visible validation error with the exact text "Only
  alphanumeric characters, underscore and hyphen are allowed", and disables
  the Generate button — without requiring any explicit blur/Tab action (an
  automatic blur+refocus cycle fires ~10ms after each keystroke and is
  sufficient).
- An empty name also disables Generate (already covered by the merged
  ELITEA-2280 spec).
- Replacing an invalid name with one using only allowed characters clears
  the validation error and re-enables Generate.
- No console errors at any point.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Personal Tokens and click "+" | Target page/section loads successfully | AFS step 1 | reuses `PersonalTokensPage.navigate()` + `click_add_button()` | asserted |
| 2 Enter a token name with special characters (e.g., "my token!@#") | Field accepts the input and displays the entered value | AFS step 2 | name input value assertion | asserted |
| 3 Verify a validation error is shown or invalid characters are rejected | Condition holds as described | AFS step 2 | `create-personal-token-name-error` exact text | asserted *(the "shown" branch — confirmed live, not the "rejected" branch; input is accepted into the field, not blocked)* |
| 4 Verify the "Generate" button is disabled | Condition holds as described | AFS step 2 | `generate_button.is_disabled()` | asserted |
| 5 Clear the name and enter a name with a space (e.g., "my token") | Action completes without error and produces the expected UI state | AFS step 3 | name input value assertion | asserted |
| 6 Verify the space is rejected or a validation error is shown | Condition holds as described | AFS step 3 | `create-personal-token-name-error` exact text | asserted *(same "shown" branch as row 3)* |
| 7 Leave the token name field empty | Action completes without error and produces the expected UI state | — | covering spec `test_create_personal_token_and_verify_in_table` Step 2 (asserts Name input starts empty) | already-covered |
| 8 Verify the "Generate" button is disabled or an inline validation error is shown | Condition holds as described | — | covering spec Step 3, line 95: `assert create_page.generate_button.is_disabled()` | already-covered |
| 9 Clear the name and enter a valid name using only allowed characters: "my_token-123" | Action completes without error and produces the expected UI state | AFS step 4 | name input value + the invalid→valid transition | asserted *(isolated "valid name accepted" half already-covered by the merged spec's own generated name; the transition-from-invalid half is new, see § Extension target Gap)* |
| 10 Verify no validation error is shown | Condition holds as described | AFS step 4 | `create-personal-token-name-error` `to_have_count(0)` | asserted |
| 11 Verify the "Generate" button becomes enabled | Condition holds as described | AFS step 4 | `generate_button.is_enabled()` | asserted *(isolated observable already-covered by covering spec line 103; the recovery-transition angle is new here)* |

### Axis 2 — Analyst additions
- **Step 1 adds a light-touch "form loaded" check** instead of repeating the
  covering spec's full page-title/defaults assertion — *added: avoids
  duplicating an already-merged, already-passing assertion; per Rule-6 dedup
  spirit, this AFS asserts only what's new.*
- **Step 2 adds an explicit note that no blur/Tab action is required** —
  *added: this needed real investigation (reading `useAutoBlur.js` after the
  live snapshot showed the error appearing without any blur click of my
  own) — the implementer should not add a defensive-but-unnecessary
  `.press("Tab")` after typing; the auto-blur already does the touching. See
  § Automation Hints.*
- **Step 4 is reframed as an invalid→valid transition, not a fresh-state
  check** — *added: the case's own step 5 wording ("Clear the name and
  enter a valid name") already implies this continuity; the covering spec's
  happy path never enters an invalid state first, so the error-clearing
  code path (`getNameHelperText()` returning `undefined` again) was never
  actually exercised anywhere in the merged suite until this AFS.*
- **A `to_have_count(0)` absence assertion on the error testid** — *added:
  per `.agents/testing.md` § Locator policy, an absence assertion on a
  testid the test's own earlier steps use positively is itself a
  "reference" — no new/different handle needed for the "error is gone"
  check, same `create-personal-token-name-error` testid.*

## Case-Text Note (clarification-worthy, not filed as a bug)
The case's steps 2–4 (special characters, e.g. `"my token!@#"`) and steps
5–6 (space only, `"my token"`) exercise the **identical code branch** —
`TOKEN_NAME_PATTERN = /^[a-zA-Z0-9_-]*$/` rejects a space exactly the same
way it rejects `!@#` (both are "any character outside the allowed set").
Confirmed live: both produce byte-identical error text and the identical
`isGenerateDisabled` mechanism. This is not a defect (the case's two
examples are still both valid demonstrations of the rule, and the analysis
executes both faithfully per the case's own step numbering) — flagged here
only so the implementer doesn't waste time hunting for a behavioral
difference between the two negative cases that doesn't exist, and so a
future case-text revision could consider collapsing steps 2–6 into one
"any disallowed character" example if the author wants a leaner case.

## Known Defects Found During Exploration
None. All case steps reproduce as authored on this build.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`), same as the
  covering spec — append the new test to the same file/class.
- Page object: extend `automation/pages/create_personal_token_page.py`
  (existing, from ELITEA-2280) with:
  - A new `name_error` `LocatorDescriptor(testid="create-personal-token-name-error")`.
  - A new method to type a name **without** the existing `fill_name()`'s
    `expect(generate_button).to_be_enabled()` postcondition (that
    postcondition is correct for the happy path but would make every
    invalid-name assertion in this case fail before it's even reached) —
    e.g. `type_name(name: str)` doing just the click + `press_sequentially`
    half, and a separate `clear_and_type_name(name: str)` for steps 3–4
    (see next bullet for the clearing technique). `fill_name()` itself
    stays untouched — reused as-is by the covering spec.
- **Clearing technique — do NOT use `Control+a` (confirmed unreliable
  live).** `Input.InputBase`'s `enableAutoBlur` (see below) fires a
  `blur()` + `focus()` cycle ~10ms after every change; if a `Control+a`
  select-all keypress lands while/after that refocus cycle, the selection
  is lost (confirmed live: a `Control+a` + `Backspace` sequence removed
  only a single leading character instead of the whole field, because the
  refocus had silently reset the cursor to position 0 before the shortcut
  landed). The reliable sequence, confirmed live: `press("Home")` then
  `press("Shift+End")` (keyboard-only line-select, not reliant on a
  modifier race) immediately followed by `press_sequentially(new_text)` —
  typing over an active selection replaces it in one step, same as a real
  user would.
- **No blur/Tab step needed to observe validation state.**
  `Input.InputBase` (`src/[fsd]/shared/ui/input/InputBase.jsx`,
  `enableAutoBlur` defaults `true`) wraps `onChange` so that ~10ms after
  every keystroke, `useAutoBlur.js` calls
  `document.activeElement.blur(); document.activeElement.focus()` on the
  currently-focused element — a **real** DOM blur event, which is what
  actually sets Formik's `touched.name` to `true` (Formik's default
  `handleChange` alone does not touch a field; only a real/synthetic blur
  does). This is why the error paragraph and the disabled Generate button
  both appear live within roughly one render tick of typing an invalid
  character, with no separate interaction — confirmed by reading
  `useAutoBlur.js` after observing the behavior live. Automation should
  simply wait on the error testid / button `disabled` state via Playwright's
  auto-waiting (`expect(...).to_be_visible()` / `.to_be_disabled()`), not
  add an unnecessary explicit blur step.
- **Navigating away with unsaved form state triggers a real
  `beforeunload` dialog** — confirmed live (hit this directly while
  re-navigating between manual exploration attempts): `useNavBlocker`
  (`CreatePersonalToken.jsx:84-86`) blocks `page.goto()`/reload once
  `hasChanged` is true. Not relevant to this AFS's own steps (nothing here
  navigates away mid-form), but worth flagging forward for any future case
  on this page that does — `page.on("dialog")` or
  `page.once("dialog", lambda d: d.accept())` would be needed before such a
  navigation, or navigate via `onCancel`'s own back-button/close-icon flow
  instead of a raw `goto()`.
- Wait strategy: no `page.wait_for_timeout` anywhere, per
  `.agents/conventions.md` — every assertion above is expressed as a
  Playwright auto-waiting `expect(...)` on a testid/attribute, never a
  fixed sleep. The ~10ms auto-blur delay is well within Playwright's
  default `expect` polling.

## Gap assertions (implementer: append to the covering spec)

Add a **new, independent `test()` method** to
`automation/tests/ui/admin/test_personal_token_create_and_verify.py`'s
`TestPersonalTokenCreateAndVerify` class — purely additive, the existing
`test_create_personal_token_and_verify_in_table` body stays byte-identical.
The module already carries `pytestmark = [pytest.mark.ui, pytest.mark.admin,
pytest.mark.p2, pytest.mark.regression]` (correct for ELITEA-2280,
`medium`/`p2`) — reuse it as-is for `ui`/`admin`/`regression`, but this
case's own priority is `high` (§ Metadata → `l2`/`p1`), **not** the module's
`p2`, so the new test needs its own per-function `@pytest.mark.p1` decorator
— otherwise a `pytest -m "p0 or p1"` high-priority gate run silently
excludes this case (identical trap to the one already hit and fixed once on
this exact file, ELITEA-2284 — see § Metadata). The original test's
module-level `p2` stays untouched.

```python
@pytest.mark.p1
def test_invalid_token_name_shows_error_and_keeps_generate_disabled(self, page):
    """ELITEA-2286 — a token name containing any character outside
    [a-zA-Z0-9_-] (special characters or a space) shows the validation
    error and keeps Generate disabled; replacing it with a conforming name
    clears the error and re-enables Generate. Read-only against the
    create-token FORM: never clicks Generate, creates no token, needs no
    cleanup. (The empty-name-disables-Generate and
    fresh-valid-name-enables-Generate observables are already asserted by
    test_create_personal_token_and_verify_in_table's Step 2/Step 3 — not
    repeated here.)"""
    tokens_page = PersonalTokensPage(page)
    create_page = CreatePersonalTokenPage(page)
    console_errors = tokens_page.capture_console_errors()

    with allure.step(
        "Step 1 — Navigate to the New Token form via the add-token button"
    ):
        tokens_page.navigate()
        tokens_page.click_add_button()
        create_page.wait_for_loaded()

    with allure.step(
        "Step 2 — Enter a name with special characters; verify the "
        "validation error is shown and Generate stays disabled"
    ):
        create_page.type_name("my token!@#")
        assert create_page.name_input.input_value() == "my token!@#", (
            f"Expected Name input to show 'my token!@#', "
            f"got {create_page.name_input.input_value()!r}"
        )
        expect(create_page.name_error).to_have_text(
            "Only alphanumeric characters, underscore and hyphen are allowed"
        )
        assert create_page.generate_button.is_disabled(), (
            "Expected Generate disabled for a name with special characters"
        )

    with allure.step(
        "Step 3 — Replace with a name containing only a space; verify the "
        "same validation error and Generate stays disabled"
    ):
        create_page.clear_and_type_name("my token")
        assert create_page.name_input.input_value() == "my token", (
            f"Expected Name input to show 'my token', "
            f"got {create_page.name_input.input_value()!r}"
        )
        expect(create_page.name_error).to_have_text(
            "Only alphanumeric characters, underscore and hyphen are allowed"
        )
        assert create_page.generate_button.is_disabled(), (
            "Expected Generate disabled for a name containing a space"
        )

    with allure.step(
        "Step 4 — Replace with a conforming name; verify the validation "
        "error clears and Generate becomes enabled"
    ):
        create_page.clear_and_type_name("my_token-123")
        expect(create_page.name_error).to_have_count(0)
        assert create_page.generate_button.is_enabled(), (
            "Expected Generate enabled once the name only uses allowed characters"
        )

    with allure.step("Step 5 — Verify no console errors across the flow"):
        assert not console_errors, f"Unexpected console errors: {console_errors}"
```

New page-object methods needed on `CreatePersonalTokenPage`
(`automation/pages/create_personal_token_page.py`):

```python
def type_name(self, name: str) -> None:
    """Type *name* into the Name field without asserting Generate's
    resulting enabled/disabled state (unlike fill_name(), which asserts
    enabled — not valid for negative/invalid-name cases)."""
    self.name_input.click()
    self.name_input.press_sequentially(name, delay=20)

def clear_and_type_name(self, name: str) -> None:
    """Replace the Name field's current content with *name*.

    Uses Home + Shift+End to select the full line, then types over the
    selection — Control+a is unreliable here because Input.InputBase's
    enableAutoBlur fires a real blur()+focus() cycle ~10ms after every
    change, which can race a Control+a keypress and silently reset the
    cursor before the shortcut lands (confirmed live during AFS
    exploration).
    """
    self.name_input.click()
    self.page.keyboard.press("Home")
    self.page.keyboard.press("Shift+End")
    self.name_input.press_sequentially(name, delay=20)
```

No new imports needed in the test file (`PersonalTokensPage`,
`CreatePersonalTokenPage`, `allure`, `pytest`, `expect` are all already
imported).

## Concrete Handles (discovered during exploration)

| Element | File | Recommended testid | How to add |
|---|---|---|---|
| Name-field validation error | `CreatePersonalToken.jsx:161` → `<Input.InputBase ... helperText={getNameHelperText()} ... />` | `create-personal-token-name-error` (**testid needed**) | `Input.InputBase`'s `helperText` prop accepts any `ReactNode` (confirmed in `InputBase.jsx` — passed straight through to MUI `TextField`'s `helperText`), so wrap the call site's existing `getNameHelperText()` output in a plain element carrying the testid, e.g. `helperText={getNameHelperText() ? <span data-testid="create-personal-token-name-error">{getNameHelperText()}</span> : undefined}` — call-site-only change in `CreatePersonalToken.jsx`, zero `InputBase.jsx` edit needed (same "wire an existing generic prop" pattern as every other handle already added on this page per the ELITEA-2280 AFS). Uniqueness confirmed via `grep -rn "create-personal-token-name-error" src/` (EliteaUI, `automation/testids`) → no hits. |
| Name input (reused, pre-existing) | `CreatePersonalToken.jsx:162-165` | `create-personal-token-name-input` | Already exists (ELITEA-2280) — zero new work, reused via `create_page.name_input`. |
| Generate button (reused, pre-existing) | `CreatePersonalToken.jsx:120-121` | `create-personal-token-generate-button` | Already exists (ELITEA-2280) — zero new work, reused via `create_page.generate_button`. |

Source confirmation (`EliteaUI/src/[fsd]/pages/settings/CreatePersonalToken.jsx`):
`TOKEN_NAME_PATTERN = /^[a-zA-Z0-9_-]*$/` (line 18), `yup.matches(...,
'Only alphanumeric characters, underscore and hyphen are allowed')` (line
23), `nameHasError = formik.touched.name && Boolean(formik.errors.name)`
(line 88), `isGenerateDisabled = !formik.values.name || nameHasError ||
isGenerating || !!data.uuid` (line 91).

## Network Behavior
None — every scenario in this case leaves the Generate button disabled
before it could ever be clicked, so `POST /api/v2/auth/token/` never fires.
Pure client-side Formik/yup validation, confirmed live (no network requests
observed beyond the initial page-load calls already covered by the ELITEA-2280
AFS's Network Behavior section).
