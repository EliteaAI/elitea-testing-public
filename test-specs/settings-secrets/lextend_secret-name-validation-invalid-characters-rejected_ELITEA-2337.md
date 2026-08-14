# Test Case: Secret name validation — only letters, numbers, and underscores are allowed (hyphens NOT permitted)

## Metadata
- **TMS ID**: ELITEA-2337
- **Source case**: `.agents/automation/elitea-2337-secret-name-validation/cases/ELITEA-2337.md`
  (snapshot; TMS module `settings-secrets`)
- **Linked Story**: none
- **Priority**: l2 (high, per case frontmatter `priority: high`). **This does NOT
  inherit the covering test's module-level `p2`** (correct for ELITEA-2336, which
  is `priority: medium`) — per
  `.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`
  (module-level `pytestmark` is a trap once a second, differently-prioritized
  case lands in the same file — identical mechanism to ELITEA-2284/ELITEA-2286 on
  the sibling Personal Tokens file), the new sibling test method needs its own
  per-function `@pytest.mark.p1` decorator — see § Gap assertions.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: extend-existing

## Extension target

**Covering spec**: `automation/tests/ui/admin/test_secret_create_inline_checkmark_x_cancel.py`
(class `TestSecretCreateInlineCheckmarkXCancel`, method
`test_create_secret_inline_checkmark_saves_x_cancels`), merged to
`origin/automation/base` in PR #1205 (ELITEA-2336, commit `722278ae`).

**Behavioural-overlap argument**: this case's steps 1-2 ("Navigate to Settings →
Secrets and click '+'"; "verify a new inline editable row appears") are
**already asserted, verbatim in substance**, by the covering spec's own Steps
1-3 (page title + existing rows visible; add button click + disabled; row is
an inline `secret-row`, not a modal). The covering spec's Step 4 also proves
the name input **accepts and displays typed text** for a well-formed, generated
name (`f"autotest_secret_{uuid4().hex[:8]}"` — itself alphanumeric+underscore
only, so it never exercises the invalid branch of `SECRET_NAME_PATTERN`). No
new assertion is needed for that half of this case's steps.

**Gap**: this case's steps 3-8 (hyphenated name is entered but rejected by
validation; special-characters/space name is entered but rejected; a
conforming name clears the error and enables the save/checkmark icon) have
**zero existing coverage anywhere** in the merged suite (grepped
`SECRET_NAME_PATTERN|secret-name-error|validation.*error|invalid.*name` across
`automation/tests` and `test-specs/settings-secrets/` — no hit besides this
AFS). The covering spec's own happy path never types an invalid character
into `secret-name-input`, so:
- the error-message/disabled-checkmark code path (`hasRowValidationErrors`,
  `SecretsTable.jsx:355-359`) is never exercised anywhere in the merged suite;
- the invalid→valid recovery transition (error clearing, checkmark
  re-enabling after a prior invalid attempt) is also new — the covering
  spec's Step 4/5 only ever sees a pristine, always-valid input, never a
  recovery from an error state.

This is structurally the same partial-overlap shape as
`test-specs/settings-personal-tokens/lextend_token-name-validation-invalid-characters-rejected_ELITEA-2286.md`
(sibling surface, same "name-only client-side regex validation, never
submitted" pattern) — same extension shape applies here.

## Preconditions
- User is logged in to the Elitea platform (localhost dev-token auth).
- Active project is `${ELITEA_PROJECT_ID}` (399, "Private") — same project used
  by ELITEA-2336; not load-bearing for this case (name validation is pure
  client-side `useMemo` regex logic, no server round-trip is ever reached
  since the save/checkmark button stays disabled for every invalid input
  tried here).
- No precondition on existing secret data — this case is **fully read-only
  against the create-secret ROW** and never clicks the checkmark/save icon,
  so it never creates a secret and needs no API cleanup (unlike ELITEA-2336's
  own save-flow half). The pending row itself is discarded via the existing
  Cancel (✗) icon at the end (client-side only, zero network calls — same
  proof as the covering spec's own Step 8).

## Test Data
### literal (from case text, verbatim — no run-uniqueness needed since
### nothing is submitted/persisted)
- Invalid, hyphenated: `"my-secret"` (case step 3's own example) — confirmed
  live this fails `SECRET_NAME_PATTERN = /^[A-Za-z0-9_]*$/`
  (`EditSecretInputGridTable.jsx:6`) — hyphens are the one character this
  surface's regex excludes that the **sibling** Personal Tokens surface's own
  regex (`/^[a-zA-Z0-9_-]*$/`) explicitly **allows**. Do not assume the two
  "name validation" surfaces share a character class — confirmed live they
  differ by exactly this one character.
- Invalid, space + special characters: `"my secret!"` (case step 5's own
  example — contains both a space and `!`; confirmed live this fails the
  same regex branch as the hyphen case, same error text, same disabled
  mechanism — i.e. the case's two negative examples are not behaviourally
  distinct from each other, see § Case-Text Note).
- Valid: `"my_secret_123"` (case step 7's own example) — confirmed live this
  passes `SECRET_NAME_PATTERN` and clears the error/enables the checkmark;
  used here to close the invalid→valid recovery transition (§ Extension
  target Gap).

## Test Steps
1. From `${BASE_URL}/settings/secrets`, click the "+" (add) button
   (`secrets_page.navigate()` + `secrets_page.click_add_button()`, both
   pre-existing) and wait for the new row's inputs to be visible
   (`expect(secrets_page.name_input).to_be_visible()`).
   - **Verify**: light-touch presence check only (the full page-title +
     existing-rows assertion is the covering spec's own Step 1, not repeated
     here) — the name input is present and empty (auto-focused for a new
     row), and the save (checkmark) button starts enabled (no validation
     error yet, per `hasRowValidationErrors` defaulting `undefined`/falsy for
     a freshly-added row before any input).
2. Type `"my-secret"` into the name input (character-by-character —
   `press_sequentially`, same mechanism `fill_new_row()` uses; a bulk
   `.fill()` risks not triggering React's controlled-input `onChange`, per
   `.claude/rules/mui-patterns.md`).
   - **Verify**: the name input's value is `"my-secret"` (input is accepted
     verbatim, not blocked character-by-character — confirmed live).
   - **Verify**: the validation-error text (testid needed —
     `secret-name-error`) is visible with exact text `"Only alphanumeric
     characters and underscore are allowed"` — confirmed live via the
     `helperText`/`error` props threaded to `Input.StyledInputEnhancer`
     (`EditSecretInputGridTable.jsx:22-23,91-92`). **No explicit blur/Tab
     step needed** — the error renders on every keystroke via the
     component's own `useMemo(validationError, [field, inputValue])`, unlike
     the sibling Personal Tokens surface which gates on Formik's
     `touched.name` after an auto-blur cycle (do not port that
     blur-dependency assumption here — confirmed live the error appears
     immediately, no blur/refocus cycle observed or required on this
     surface).
   - **Verify**: the save/checkmark button (testid `secret-row-save-button`,
     pre-existing) is disabled — confirmed live: `hasRowValidationErrors(id)`
     is `true` because `handleValidationChange` recorded
     `validationErrors[{id}-name] = true` via `EditSecretInputGridTable`'s
     `onValidationChange` callback (`SecretsTable.jsx:348-359,450,456-461`).
3. Clear the name input (`press("Home")` then `press("Shift+End")` to
   keyboard-select the full line, then type over the selection — **do not
   use `Control+a`**, confirmed unreliable live on this exact input
   component during this session's own exploration: a `Control+a` press
   immediately after typing left the field showing `"my secret!my-secret"`
   instead of replacing the prior content, i.e. the select-all silently
   failed to select anything before the next keystroke landed) and type
   `"my secret!"` (space + special character, no hyphen).
   - **Verify**: the name input's value is `"my secret!"`.
   - **Verify**: the same validation-error text (`secret-name-error`) is
     visible with the same exact text — confirmed live: a space+`!` also
     fails the same `SECRET_NAME_PATTERN` regex, same branch as step 2 (see
     § Case-Text Note — the case's two negative examples are not
     behaviourally distinguishable, only cosmetically different strings).
   - **Verify**: the save/checkmark button is disabled — same mechanism as
     step 2.
4. Clear the name input (same Home+Shift+End technique) and type
   `"my_secret_123"` (allowed characters only — letters, numbers,
   underscores).
   - **Verify**: the name input's value is `"my_secret_123"`.
   - **Verify**: the validation-error text (`secret-name-error`) is **no
     longer present** (`to_have_count(0)` — the component only renders
     `helperText` when `validationError` is truthy;
     `SECRET_NAME_PATTERN.test("my_secret_123")` is `true`, so
     `validationError` is `null` and `helperText` resolves to `null`) —
     confirmed live. This is the invalid→valid recovery transition the
     covering spec never exercises (its own happy path only ever sees a
     pristine, never-invalid input) — see § Extension target Gap.
   - **Verify**: the save/checkmark button is enabled — confirmed live:
     `hasRowValidationErrors(id)` flips back to falsy once
     `onValidationChange(id, 'name', false)` fires for the conforming value.
5. **Verify no console error** was raised across steps 1-4 (side-channel
   check — confirmed live this exploration session: 0 console errors, 0
   warnings across this full negative-validation flow; no occurrence of the
   known `#1203` "Maximum update depth exceeded" warning was observed during
   this run, unlike the covering spec's own automated run which hit it
   deterministically 3/3 — see § Known Defects for how the implementer
   should handle either outcome).

(This case never clicks the save/checkmark icon — every invalid-name attempt
leaves it disabled by design, and the one valid name reached in step 4 is
only entered to prove the error clears and the button re-enables, not
submitted. Discard the pending row via the existing Cancel (✗) icon
(`secrets_page.click_cancel_button()`) as unwrapped cleanup — zero network
calls, same proof as the covering spec's own Step 8 — so no secret is ever
created and no API cleanup is needed.)

## Expected Results
- Typing a name containing a hyphen, or containing a space/special
  character, is accepted into the field's displayed value but triggers a
  visible validation error with the exact text "Only alphanumeric characters
  and underscore are allowed", and disables the save/checkmark icon —
  immediately on each keystroke, no blur/Tab action needed.
- Replacing an invalid name with one using only letters/numbers/underscores
  clears the validation error and re-enables the save/checkmark icon.
- No console errors at any point (modulo the known, OPEN, deterministic
  `#1203` mount-time warning — see § Known Defects).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Secrets and click "+" | Target page/section loads successfully | — | covering spec `test_create_secret_inline_checkmark_saves_x_cancels` Steps 1-2 | already-covered |
| 2 Verify a new inline editable row appears in the table | Condition holds as described | — | covering spec Step 3 | already-covered |
| 3 Enter a name with a hyphen (e.g., "my-secret") | Field accepts the input and displays the entered value | AFS step 2 | name input value assertion | asserted |
| 4 Verify a validation error is shown or the hyphen is rejected | Condition holds as described | AFS step 2 | `secret-name-error` exact text + save button disabled | asserted *(the "shown" branch — confirmed live, not the "rejected" branch; input is accepted into the field, not blocked character-by-character)* |
| 5 Enter a name with spaces or special characters (e.g., "my secret!") | Field accepts the input and displays the entered value | AFS step 3 | name input value assertion | asserted |
| 6 Verify these are also rejected | Condition holds as described | AFS step 3 | `secret-name-error` exact text + save button disabled | asserted *(same "shown" branch as row 4 — same regex, same error, see § Case-Text Note)* |
| 7 Enter a valid name "my_secret_123" | Field accepts the input and displays the entered value | AFS step 4 | name input value + invalid→valid transition | asserted *(the isolated "valid name accepted" half is arguably touched by the covering spec's own generated-name flow, but the covering spec never types an invalid character first, so the RECOVERY transition — error clearing, button re-enabling after being disabled — is new here, see § Extension target Gap)* |
| 8 Verify no validation error is shown and the checkmark/save icon is enabled | Condition holds as described | AFS step 4 | `secret-name-error` `to_have_count(0)` + save button enabled | asserted |

### Axis 2 — Analyst additions
- **Step 1 adds a light-touch "row present" check** instead of repeating the
  covering spec's full page-title/existing-rows assertion — *added: avoids
  duplicating an already-merged, already-passing assertion; per Rule-6 dedup
  spirit, this AFS asserts only what's new.*
- **Step 2 documents that no blur/Tab action is required, and explicitly
  that this surface's mechanism DIFFERS from the sibling Personal Tokens
  surface's Formik-`touched`+auto-blur mechanism** — *added: this needed
  real investigation (reading `EditSecretInputGridTable.jsx`'s `useMemo`
  after confirming live that the error appeared with no blur action of my
  own) — the implementer should not port the Personal Tokens page's
  auto-blur assumption or add a defensive `.press("Tab")` here; this
  component's validation is unconditional on every render, not gated on a
  Formik `touched` flag.*
- **Step 3 explicitly forbids `Control+a`** for the same reason confirmed on
  the sibling Personal Tokens surface (`ELITEA-2286`'s AFS) — *added:
  reconfirmed live on THIS surface's own input, not assumed by analogy: a
  `Control+a` press directly after typing left the field showing the old and
  new text concatenated, i.e. the selection silently failed. See §
  Automation Hints for the exact reliable sequence.*
- **A `to_have_count(0)` absence assertion on the `secret-name-error`
  testid** — *added: per `.agents/testing.md` § Locator policy, an absence
  assertion on a testid the test's own earlier steps use positively is
  itself a "reference" — no new/different handle needed for the
  "error is gone" check.*
- **Step 5's console-error check documents that `#1203` was NOT observed
  live during this analysis session** — *added: contrasts directly with the
  covering spec's own implementation-time run, which hit `#1203`
  deterministically 3/3 (React "Maximum update depth exceeded" on every
  `/settings/secrets` mount). Flagged explicitly rather than silently
  assuming either outcome — see § Known Defects for the implementer's
  decision tree.*

## Case-Text Note (clarification-worthy, not filed as a bug)
The case's steps 3-4 (hyphenated, `"my-secret"`) and steps 5-6 (space +
special character, `"my secret!"`) exercise the **identical code branch** —
`SECRET_NAME_PATTERN = /^[A-Za-z0-9_]*$/` rejects a hyphen exactly the same
way it rejects a space or `!` (both are "any character outside the allowed
set"). Confirmed live: both produce byte-identical error text
("Only alphanumeric characters and underscore are allowed") and the
identical `hasRowValidationErrors`/disabled-checkmark mechanism. This is not
a defect (the case's two examples are still both valid demonstrations of the
rule, and the analysis executes both faithfully per the case's own step
numbering) — flagged here only so the implementer doesn't waste time hunting
for a behavioral difference between the two negative cases that doesn't
exist. This is the identical case-text pattern already flagged on the
sibling Personal Tokens surface (`ELITEA-2286`'s own Case-Text Note) — same
observation, independently reconfirmed here rather than assumed by analogy.

**Cross-surface divergence worth flagging forward**: the case's own title
says "letters, numbers, and underscores — hyphens not permitted", i.e. this
surface's rule is objectively **stricter** than the sibling Personal Tokens
surface, which explicitly **allows** hyphens
(`TOKEN_NAME_PATTERN = /^[a-zA-Z0-9_-]*$/`, confirmed in
`CreatePersonalToken.jsx:18` per ELITEA-2286's AFS). Both are correct
per their own case text and their own source regex — not a defect on
either surface, just a genuine cross-feature inconsistency in the product's
naming rules that a future case author might want to reconcile (or not) —
noted here for visibility, no action taken.

## Known Defects Found During Exploration
None newly found during this analysis pass. `#1203` (OPEN,
`EliteaAI/elitea-testing-public#1203` — React "Maximum update depth
exceeded" console warning on every `/settings/secrets` mount, filed during
ELITEA-2336's implementation) is a **pre-existing, already-tracked** defect
on this exact surface; **not re-filed here** (dedup: same object, same
trigger, same OPEN issue). It was **not observed** during this analysis
session's own live exploration (0 console errors/warnings across the full
negative-validation flow, confirmed via `browser_console_messages` before
and after each typed value) — contrast with the covering spec's own
automated run, which hit it deterministically 3/3. Two honest possibilities
for the implementer to resolve at automation time (this AFS does not
prejudge which):
1. The new test's own automated run also hits `#1203` on mount (most
   likely, since it mounts the same `/settings/secrets` route) — in that
   case, reuse the **exact same** `_is_known_defect_1203()` matcher +
   `soft_failures`/`pytest.fail()` idiom already established in
   `test_secret_create_inline_checkmark_x_cancel.py` (same file, same
   class) rather than re-deriving it, per the sanctioned-RED merge-gate
   exception (`.agents/testing.md` § Merge gate) — the defect is the same
   object, same trigger, already open and linked.
2. The new test's run does NOT hit it (possible — my own exploration
   session didn't) — in that case assert a plain `assert not
   console_errors` with no special-casing; do not manufacture an expected
   failure that doesn't reproduce.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`), same as the
  covering spec — append the new test to the same file/class
  (`TestSecretCreateInlineCheckmarkXCancel`).
- Page object: extend `automation/pages/secrets_page.py` (existing, from
  ELITEA-2336) with:
  - A new `name_error` `LocatorDescriptor(testid="secret-name-error")`
    (testid needed — see § Concrete Handles).
  - A new method `type_name(name: str)` — types into `name_input` via
    `press_sequentially` **without** any postcondition assertion on the
    save button's state (unlike a hypothetical happy-path fill helper —
    this case needs to observe the DISABLED state along the way, so the
    method must not assert "enabled" internally).
  - A new method `clear_and_type_name(name: str)` — `press("Home")` then
    `press("Shift+End")` (keyboard-only line-select) immediately followed by
    `press_sequentially(new_text)`, mirroring
    `create_personal_token_page.py`'s `clear_and_type_name()` — confirmed
    unreliable with `Control+a` on this exact input too (see § Axis 2).
  - `fill_new_row(name, value)` (existing, from ELITEA-2336) stays untouched
    — reused as-is by the covering test; not reused here since this case
    only ever types into the name field, never the value field.
- Wait strategy: no `page.wait_for_timeout` anywhere. Every assertion above
  is expressed as a Playwright auto-waiting `expect(...)` on a testid/state,
  never a fixed sleep — the validation error renders synchronously with
  React's own re-render on every keystroke (confirmed live: no debounce
  observed on this component, unlike some other MUI form fields per
  `.claude/rules/mui-patterns.md`'s general debounce guidance — this
  specific component's `useMemo` has no timer).
- **This surface's error mechanism does NOT depend on blur/touched state**
  (contrast with the sibling Personal Tokens surface's Formik
  `touched.name` + `useAutoBlur` mechanism, `create_personal_token_page.py`'s
  own Automation Hints) — do not add an unneeded blur/Tab step by analogy
  with that sibling page; confirmed live here the error/disabled-button pair
  appears on the very next render after `onChange`, no blur event involved.

## Gap assertions (implementer: append to the covering spec)

Add a **new, independent `test()` method** to
`automation/tests/ui/admin/test_secret_create_inline_checkmark_x_cancel.py`'s
`TestSecretCreateInlineCheckmarkXCancel` class — purely additive, the
existing `test_create_secret_inline_checkmark_saves_x_cancels` body stays
byte-identical. The module currently carries `pytestmark = [pytest.mark.ui,
pytest.mark.admin, pytest.mark.p2, pytest.mark.regression]` (correct for
ELITEA-2336, `priority: medium`), but this case's own priority is `high`
(§ Metadata → `l2`/`p1`), **not** the module's `p2` — per
`.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`
(identical trap already hit twice on the sibling
`test_personal_token_create_and_verify.py` file, ELITEA-2284/ELITEA-2286),
the new test needs its own per-function `@pytest.mark.p1` decorator —
otherwise a `pytest -m "p0 or p1"` high-priority gate run silently excludes
this case. The original test's module-level `p2` stays untouched.

```python
@pytest.mark.p1
def test_secret_name_rejects_hyphen_and_special_chars_valid_name_clears_error(
    self, page
):
    """ELITEA-2337 — a secret name containing a hyphen, or a space/special
    character, shows the validation error "Only alphanumeric characters and
    underscore are allowed" and disables the save (checkmark) icon;
    replacing it with a conforming name (letters/numbers/underscores only)
    clears the error and re-enables the checkmark. Read-only against the
    pending row: never clicks the checkmark, creates no secret, needs no
    API cleanup — discards the pending row via the existing Cancel (X) icon.
    (The empty-row-starts-enabled and fresh-valid-name-enables-checkmark
    observables are already touched by
    test_create_secret_inline_checkmark_saves_x_cancels's own Steps 1-4 —
    not repeated here; this test's own new ground is the INVALID states and
    the invalid->valid recovery transition.)"""
    secrets_page = SecretsPage(page)
    console_errors = secrets_page.capture_console_errors()

    try:
        with allure.step(
            "Step 1 — Navigate to Settings -> Secrets; click '+' and wait "
            "for the new row's name input"
        ):
            secrets_page.navigate()
            secrets_page.click_add_button()
            expect(secrets_page.name_input).to_be_visible(timeout=ROW_WAIT_TIMEOUT)

        with allure.step(
            "Step 2 — Enter a hyphenated name; verify the validation error "
            "is shown and the checkmark stays disabled"
        ):
            secrets_page.type_name("my-secret")
            assert secrets_page.name_input.input_value() == "my-secret", (
                f"Expected name input to show 'my-secret', got "
                f"{secrets_page.name_input.input_value()!r}"
            )
            expect(secrets_page.name_error).to_have_text(
                "Only alphanumeric characters and underscore are allowed"
            )
            expect(secrets_page.save_button).to_be_disabled(timeout=ROW_WAIT_TIMEOUT)

        with allure.step(
            "Step 3 — Replace with a name containing a space and a special "
            "character; verify the same validation error and disabled "
            "checkmark"
        ):
            secrets_page.clear_and_type_name("my secret!")
            assert secrets_page.name_input.input_value() == "my secret!", (
                f"Expected name input to show 'my secret!', got "
                f"{secrets_page.name_input.input_value()!r}"
            )
            expect(secrets_page.name_error).to_have_text(
                "Only alphanumeric characters and underscore are allowed"
            )
            expect(secrets_page.save_button).to_be_disabled(timeout=ROW_WAIT_TIMEOUT)

        with allure.step(
            "Step 4 — Replace with a conforming name; verify the "
            "validation error clears and the checkmark becomes enabled"
        ):
            secrets_page.clear_and_type_name("my_secret_123")
            expect(secrets_page.name_error).to_have_count(0)
            expect(secrets_page.save_button).to_be_enabled(timeout=ROW_WAIT_TIMEOUT)

        with allure.step("Step 5 — Verify no console errors across the flow"):
            unexpected_errors = [m.text for m in console_errors]
            assert not unexpected_errors, (
                f"Unexpected console errors: {unexpected_errors}"
            )
    finally:
        console_errors.stop()
        # Cleanup (not an AFS case step) — the pending row is never saved
        # (checkmark is never clicked in this test), so discard it via the
        # existing Cancel (X) icon: zero network calls, no secret ever
        # created, no API cleanup needed. Guard with a bare try since the
        # row may already be gone if an earlier assertion failed mid-flow.
        try:
            secrets_page.click_cancel_button()
        except Exception:
            logger.warning(
                "Cleanup: could not click cancel button (row may already "
                "be gone or page navigated away)"
            )
```

**Note on step 5's console-error handling**: the code block above asserts a
plain `assert not unexpected_errors`. If the implementer's own automated
run reproduces `#1203` (as the covering test's did, 3/3), replace this with
the identical `_is_known_defect_1203()` filter + `soft_failures`/
`pytest.fail()` pattern already in this same file (see § Known Defects,
option 1) rather than writing a second, divergent matcher.

New page-object methods needed on `SecretsPage`
(`automation/pages/secrets_page.py`):

```python
def type_name(self, name: str) -> None:
    """Type *name* into the currently-editing row's name input without
    asserting the save button's resulting enabled/disabled state (unlike
    fill_new_row(), which fills both name+value and is meant for the
    happy path — not valid for negative/invalid-name cases where the save
    button is EXPECTED to be disabled)."""
    self.name_input.click()
    self.name_input.press_sequentially(name, delay=20)

def clear_and_type_name(self, name: str) -> None:
    """Replace the name input's current content with *name*.

    Uses Home + Shift+End to select the full line, then types over the
    selection — Control+a is unreliable here (confirmed live during
    ELITEA-2337 AFS exploration: a Control+a press directly after typing
    left the field showing the old and new text concatenated instead of
    replacing it), same technique and same root cause already documented
    on the sibling Personal Tokens page's own
    clear_and_type_name() (ELITEA-2286).
    """
    self.name_input.click()
    self.page.keyboard.press("Home")
    self.page.keyboard.press("Shift+End")
    self.name_input.press_sequentially(name, delay=20)
```

New `LocatorDescriptor` needed on `SecretsPage`:

```python
name_error = LocatorDescriptor(
    testid="secret-name-error",
    description="Name-field validation error text, visible only while "
    "the currently-editing row's name fails SECRET_NAME_PATTERN",
)
```

No new imports needed in the test file (`SecretsPage`, `allure`, `pytest`,
`expect`, `logger` are all already imported/defined).

## Concrete Handles (discovered during exploration)

| Element | File | Recommended testid | How to add |
|---|---|---|---|
| Name-field validation error | `EditSecretInputGridTable.jsx:22-23` (`helperText` value) → `92` (`helperText={helperText}` prop on `Input.StyledInputEnhancer`) | `secret-name-error` (**testid needed**) | `Input.StyledInputEnhancer`'s `helperText` prop is spread through to a plain MUI `TextField` (confirmed by tracing `StyledInputEnhancer.jsx`'s `<Input.InputBase {...leftProps} .../>` → `InputBase.jsx`'s `<MuiTextField {...leftProps} .../>` — `helperText` travels via the `leftProps` spread all the way to MUI's own `FormHelperText`, same mechanism as the sibling Personal Tokens page's `create-personal-token-name-error`), so wrap the call site's existing `helperText` value in a plain element carrying the testid at the `EditSecretInputGridTable.jsx` call site, e.g. `helperText={helperText ? <span data-testid="secret-name-error">{helperText}</span> : null}` — call-site-only change, zero `StyledInputEnhancer.jsx`/`InputBase.jsx` edit needed (same "wire an existing generic prop" pattern already used for every other handle added to this surface by ELITEA-2336). Uniqueness confirmed via `grep -rn "secret-name-error" src/` (EliteaUI, fetched `automation/testids`) → no hits. |
| Name input (reused, pre-existing) | `EditSecretInputGridTable.jsx:95` | `secret-name-input` | Already exists (ELITEA-2336, `EliteaAI/EliteaUI@c2a5b4c7`, on `automation/testids` only) — zero new work, reused via `secrets_page.name_input`. |
| Save/checkmark button (reused, pre-existing) | `SecretsTable.jsx:456` | `secret-row-save-button` | Already exists (ELITEA-2336, same commit) — zero new work, reused via `secrets_page.save_button`. Its `disabled` prop (`SecretsTable.jsx:460`, `disabled={hasValidationErrors}`) is the state this case's own steps 2-4 assert. |

Source confirmation (`EliteaUI/src/[fsd]/features/settings/ui/secrets/`):
`EditSecretInputGridTable.jsx:6` — `SECRET_NAME_PATTERN = /^[A-Za-z0-9_]*$/`;
`:13-17` — `validationError` `useMemo`, message `'Only alphanumeric
characters and underscore are allowed'`; `:22-23` — `helperText` resolution;
`:25-27` — `onValidationChange?.(id, field, Boolean(validationError))`
effect. `SecretsTable.jsx:348-351` — `handleValidationChange` records
`validationErrors[{rowId}-{field}]`; `:355-359` — `hasRowValidationErrors`;
`:450,456,460` — `renderActions`'s save `IconButton`,
`disabled={hasValidationErrors}`.

## Network Behavior
None — every scenario in this case leaves the save/checkmark button disabled
before it could ever be clicked (or, for the one valid name reached, is
simply never clicked because the case only tests the field-level
transition), so `POST /api/v2/secrets/secrets/default/${ELITEA_PROJECT_ID}`
never fires. Pure client-side `useMemo`-based regex validation, confirmed
live (no network requests observed beyond the initial page-load/list-fetch
calls already covered by the ELITEA-2336 AFS's own Network Behavior
section) — verified via `browser_network_requests` across this entire
exploration session.
