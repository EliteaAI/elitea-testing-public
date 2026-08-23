# Test Case: Bucket Name Field Does Not Accept More Than 56 Characters

## Metadata
- **TMS ID**: ELITEA-1819
- **Case snapshot**: `.agents/automation/artifacts-w04/cases/ELITEA-1819.md`
- **Priority**: l3 (source case `priority: medium`, mapped per this folder's convention)
- **Environment explored**: local `http://localhost:5173` (EliteaUI `automation/testids` → DEV
  backend), project `Private` / id `399`.
- **User set**: `${TEST_USER}` (on localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot · **Date**: 2026-08-23
- **Status**: **ready-for-automation** — case executed end-to-end live, every step passed as
  authored, **no product defect on this path**. Two CLARIFICATIONs filed for case-text/case-data
  drift ([#1682](https://github.com/EliteaAI/elitea-testing-public/issues/1682) — indicator text,
  [#1683](https://github.com/EliteaAI/elitea-testing-public/issues/1683) — 57-char test data).
  One `testid needed:` (`artifacts-bucket-name-character-counter`). 0 console errors.
- **Sibling case analysed in the same session**: ELITEA-1818
  (`l3_create-bucket-56-char-name-limit-warning-and-delete-cancel_ELITEA-1818.md`). Separate AFS:
  the two share steps 1-5 but **diverge in steps** — 1818 saves the bucket and drives the
  delete-confirmation Cancel; this case never clicks Save and is therefore **unaffected by
  defect [#1080](https://github.com/EliteaAI/elitea-testing-public/issues/1080)**, which blocks
  1818's Save step. Merging them would drag this clean case into a sanctioned-RED spec.

## Fidelity declaration

**No substitution.** The extra character is delivered as a real keystroke
(`Locator.type("z")` / `press("z")`) into the focused field — the browser's own `maxLength`
enforcement is the subject, so it must be exercised through real key events. A `fill()` would
set the value through the DOM value setter and **bypass `maxLength` entirely**, proving nothing —
that shape is forbidden for this case.

## Overlap check vs existing automation

Read before executing: `automation/pages/artifacts_page.py` and every
`automation/tests/ui/artifacts/test_artifacts_bucket_*.py` + their AFS files.

- `test_artifacts_bucket_name_validation_invalid_formats.py` (ELITEA-1811) covers the **regex**
  rule (leading digit, `$`, `_`, space) and the shared helper-text message — never length.
- `test_artifacts_bucket_empty_name_validation.py` (ELITEA-1813) covers the empty-name /
  disabled-Save boundary — the *lower* bound, not the upper one.
- `test_artifacts_create_bucket_55char_name_and_delete.py` (ELITEA-1817, merged) fills a 56-char
  name but **never attempts a 57th character** and never asserts `maxLength` enforcement or the
  counter.
- `grep -rn "maxlength\|characters left\|character.limit" tests/ui/artifacts/ pages/artifacts_page.py -i`
  → prose only, no assertions.

Verdict: **fresh implementation**, `ready-for-automation`. Nothing merged asserts that the field
rejects a 57th character.

## Preconditions
- User logged in (localhost: `auth_state` skips login).
- A project is selected (`Private`, id 399 in this run).
- **No bucket is created and nothing is persisted** — the case never clicks Save. No fixture, no
  teardown, no test data leak.

## Test Data

- **56-character name — generate per run or use a fixed valid 56-char literal.** Do **not** use
  the case's own literal verbatim: it is **57** characters (CLARIFICATION
  [#1683](https://github.com/EliteaAI/elitea-testing-public/issues/1683)), so typing it *already*
  performs step 6's rejection and collapses steps 4 and 6 into one action, destroying the case's
  own structure. Enter a genuine 56-character name first, then attempt the 57th character as a
  separate, observable act.
  - Shape used live: `("afs1819" + <6-digit stamp> + "a1b2c3…")[:56]`; must satisfy
    `^[a-zA-Z][a-zA-Z0-9-]*$` and be **exactly 56** characters (assert the length as a data
    sanity check — the case is meaningless at any other length).
  - A fixed literal is also acceptable here (nothing is persisted, so there is no duplicate-name
    hazard), but it must not equal ELITEA-1817's or ELITEA-1818's name.
- **Extra character**: `z` (as the case specifies).
- **Character indicator expected text**: `0 characters left`, **not** the case's
  `0 of 56 remaining` (CLARIFICATION
  [#1682](https://github.com/EliteaAI/elitea-testing-public/issues/1682)). Source:
  `src/[fsd]/shared/ui/text/CharacterCounter.jsx` → `` `${remaining} characters left` ``.
- **Enforcement mechanism** (live-confirmed): `CreateBucket.jsx:239-241` sets
  `inputProps={{ maxLength: 56 }}` — a native browser input constraint, so the 57th keystroke
  never reaches React. There is no error state, no helper text and no toast: the character is
  simply dropped.

## Test Steps

1. **Navigate to Artifacts** (case step 1) — `ArtifactsPage.navigate_to_artifacts()`.
   - Verify `artifacts-buckets-heading` visible.
2. **Click the create-bucket icon** (case step 2) — `click_create_bucket_button()`.
   - Verify URL contains `/artifacts/create-bucket`.
3. **Verify the "New Bucket" form** (case step 3).
   - `artifacts-bucket-form-heading` text == `"New Bucket"`; `artifacts-bucket-name-input`
     visible with `input_value() == "new-bucket"`.
   - Verify the field advertises its own limit: `artifacts-bucket-name-input`'s `maxlength`
     attribute == `"56"` (live-confirmed) — the contract this case exists to enforce.
4. **Enter the 56-character name** (case step 4) — `fill_bucket_name(NAME_56)`
   (click + `select_text()` + `type()`; a bare `fill()` bypasses both formik and `maxLength`).
   - Verify `input_value() == NAME_56` and `len(...) == 56`.
   - **Leave the field focused** — step 5 depends on it.
5. **Verify the character indicator** (case step 5).
   - Counter visible, text exactly `"0 characters left"` (**testid needed**, see § Concrete
     Handles).
   - **Focus gotcha (live-confirmed):** the counter renders only while
     `isFocused('name') && length === 56`; a blur removes the element from the DOM entirely.
     Keep focus in the field for steps 5-8.
6. **Attempt one additional character** (case step 6) — move the caret to the end
   (`press("End")`) and `type("z")` as a real keystroke.
   - No assertion here; this is the action.
7. **Verify the character was rejected** (case step 7).
   - `input_value() == NAME_56` (unchanged) and `len(...) == 56`.
   - `input_value().endswith("z")` is `False` (guards against a same-length substitution).
   - Live-confirmed for **both** delivery shapes (`type("z")` and `press("z")`) — the
     implementation may assert either; asserting both is cheap and stronger.
8. **Verify the indicator still reads "0 characters left"** (case step 8).
   - Same counter, same text — it must not flip to a negative or an error state.
   - Also verify no error state appeared: `is_bucket_name_invalid()` is `False`
     (`aria-invalid == "false"` live) and `artifacts-bucket-name-helper-text` has count 0 —
     rejection is silent, by design.
9. **Verify the name is unchanged** (case step 9).
   - Re-assert `input_value() == NAME_56` (the case asserts the field content twice, in steps 7
     and 9, around the indicator check — keep both, they bracket step 8).

**No Save click. No teardown.** Leaving the form (or the test ending) discards everything; do not
add a cleanup step that creates state this case never created.

## Concrete Handles

| Element | Handle | Provenance (fetched 2026-08-23) | Notes |
|---|---|---|---|
| Buckets page heading | `artifacts-buckets-heading` | on-main ✓ | `wait_for_page_load()` |
| Create-bucket icon | `artifacts-create-bucket-button` | on-main ✓ | `click_create_bucket_button()` |
| Form heading | `artifacts-bucket-form-heading` | on-`automation/testids` only (awaiting human promotion to main) | text `"New Bucket"` |
| Name input | `artifacts-bucket-name-input` | on-main ✓ | `maxlength="56"` readable off the same testid'd node — no new handle needed |
| **Character counter** | **testid needed: `artifacts-bucket-name-character-counter`** | needs-adding | `CreateBucket.jsx:248` `<Text.CharacterCounter>`; the component already accepts a `data-testid` prop (`CharacterCounter.jsx:11,20`) — prop-only wiring at the call site, zero functional impact. No wrapper element may be added. Shared with ELITEA-1818 — whichever case is implemented first adds it. |
| Name helper text | `artifacts-bucket-name-helper-text` | on-main ✓ | asserted **absent** (`to_have_count(0)`) — the rejection is silent |
| Save button | `artifacts-bucket-save-button` | on-main ✓ | present but **never clicked** by this case |

Existing page-object methods reused as-is: `navigate_to_artifacts()`,
`click_create_bucket_button()`, `fill_bucket_name()`, `is_bucket_name_invalid()`.
New page-object work: the character-counter `LocatorDescriptor` + text reader, and a small
"type one more character at the end" helper (caret to `End`, then `type`) — the existing
`fill_bucket_name()` replaces the whole value and cannot express an append.

## Network Behavior

**None.** The entire case is client-side: `maxLength` is a native input constraint and no
request is made at any step. A useful negative assertion: zero `/artifacts/buckets` requests
across the test.

## Coverage Map

### Axis 1 — every element of the source case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` (localhost bypass) | fixture | covered |
| Step 1 — navigate to Artifacts | page loads | Step 1 | `artifacts-buckets-heading` | covered |
| Step 2 — click create-bucket icon | New Bucket form opens | Step 2 | URL `/artifacts/create-bucket` | covered |
| Step 3 — verify form opens | form visible | Step 3 | heading + name field + `maxlength` | covered |
| Step 4 — enter 56-char name | all 56 accepted | Step 4 | `input_value()` + length 56 | covered (test data corrected — CLARIFICATION #1683) |
| Step 5 — indicator "0 of 56 remaining" | warning shown | Step 5 | counter text `"0 characters left"` | covered, **text corrected** — CLARIFICATION #1682 (reverse-masking guard) |
| Step 6 — type an extra "z" | attempt made | Step 6 | action (real keystroke) | covered |
| Step 7 — char not accepted, still 56 | field unchanged | Step 7 | value equality + length + no trailing `z` | covered |
| Step 8 — indicator still "0 …" | unchanged | Step 8 | counter text re-read | covered, text corrected |
| Step 9 — name unchanged | unchanged | Step 9 | value equality | covered |
| Expected final state | hard 56-char maximum enforced | Steps 7-9 | — | covered |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why |
|---|---|
| `maxlength` attribute == `"56"` (step 3) | names the enforcement mechanism; if the attribute is ever dropped the test fails at the cause rather than at a downstream symptom |
| `aria-invalid == "false"` + helper text count 0 after the rejected keystroke | the case says only "not accepted"; proving the rejection is **silent** (no error state) is what distinguishes correct `maxLength` behaviour from a validation failure |
| `endswith("z")` is False | length equality alone would pass if the field silently swapped a character; this pins *which* character was dropped |
| Both `type()` and `press()` delivery shapes | guards against a future implementation that filters only one event path |
| Zero network requests across the test | proves the whole boundary is enforced client-side, as designed |
| Console-error side channel | project convention; 0 errors observed live |

## Known Defects Found

**None on this path.** Every step behaved exactly as the case expects.

Recorded for the implementer's awareness only (does **not** affect this case, which never clicks
Save): [#1080](https://github.com/EliteaAI/elitea-testing-public/issues/1080) — Save silently
does nothing on a single click at exactly 56 characters (root-caused during this session; see
ELITEA-1818's AFS).

Clarifications (case-text drift, NOT defects — reverse-masking guard):
[#1682](https://github.com/EliteaAI/elitea-testing-public/issues/1682),
[#1683](https://github.com/EliteaAI/elitea-testing-public/issues/1683).

## Blocked Steps

None.

## Automation Hints

- **Markers**: `ui`, `regression`, `p2`, `artifacts`.
- Wrap every step in `with allure.step("Step N — …"):`.
- Locators: testid-only `LocatorDescriptor` class fields; the counter needs a new testid via
  `add-data-testid` (prop already supported — no new DOM node).
- **Never use `fill()` for the extra character** — it bypasses `maxLength` and would make the
  test pass for the wrong reason (see § Fidelity declaration).
- Keep focus in the Name field for steps 5-8; a stray blur removes the counter from the DOM and
  the assertion fails for an unrelated reason.
- Timeouts: 10 s UI elements, 15-20 s navigation. Fast test — no network waits at all.

## Cleanup

None required — nothing is created or persisted.

## Evidence

- `test-results/screenshots/ELITEA-1819-step-05-counter.png`
- `test-results/screenshots/ELITEA-1819-step-07-rejected.png`
